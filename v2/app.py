from __future__ import annotations

import os
import secrets
import sqlite3
from datetime import date, datetime
from pathlib import Path
from functools import wraps

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data_v2"
UPLOAD_DIR = DATA_DIR / "uploads"
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "central_v2.db"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_IMAGES_PER_PRODUCT = 10
STATUSES = ["Ideia", "Preparando", "Pronto", "Publicado", "Pausado"]
FORMATS = ["Story", "Feed", "Reel", "Outro"]

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.update(
    SECRET_KEY=os.environ.get("CENTRAL_SECRET_KEY") or secrets.token_hex(32),
    MAX_CONTENT_LENGTH=20 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS products (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          category TEXT NOT NULL DEFAULT '',
          price TEXT NOT NULL DEFAULT '',
          affiliate_link TEXT NOT NULL DEFAULT '',
          commission TEXT NOT NULL DEFAULT '',
          notes TEXT NOT NULL DEFAULT '',
          image_filename TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS product_images (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          product_id INTEGER NOT NULL,
          filename TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS posts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          product_id INTEGER,
          planned_date TEXT NOT NULL DEFAULT '',
          format TEXT NOT NULL DEFAULT 'Story',
          status TEXT NOT NULL DEFAULT 'Ideia',
          caption TEXT NOT NULL DEFAULT '',
          hashtags TEXT NOT NULL DEFAULT '',
          cta TEXT NOT NULL DEFAULT '',
          image_filename TEXT NOT NULL DEFAULT '',
          notes TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS metrics (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          product_id INTEGER,
          report_date TEXT NOT NULL DEFAULT '',
          clicks INTEGER NOT NULL DEFAULT 0,
          orders INTEGER NOT NULL DEFAULT 0,
          commission_value TEXT NOT NULL DEFAULT '',
          notes TEXT NOT NULL DEFAULT '',
          FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_posts_date ON posts(planned_date);
        CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);
        CREATE INDEX IF NOT EXISTS idx_images_product ON product_images(product_id);
        """)

init_db()

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login", next=request.full_path.rstrip("?")))
        return fn(*args, **kwargs)
    return wrapped

def valid_upload(file):
    return bool(file and file.filename and "." in file.filename and file.filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS)

def save_upload(file):
    if not valid_upload(file):
        return ""
    ext = file.filename.rsplit(".", 1)[1].lower()
    name = secure_filename(Path(file.filename).stem)[:40] or "imagem"
    filename = f"{secrets.token_hex(8)}_{name}.{ext}"
    file.save(UPLOAD_DIR / filename)
    return filename

def get_product(product_id):
    with connect() as con:
        row = con.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        if not row:
            return None
        images = con.execute("SELECT * FROM product_images WHERE product_id=? ORDER BY id", (product_id,)).fetchall()
    return {"row": row, "images": images}

@app.template_filter("brdate")
def brdate(value):
    if not value:
        return "Sem data"
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return value

@app.context_processor
def common_context():
    return {"today": date.today().isoformat(), "statuses": STATUSES, "formats": FORMATS}

@app.errorhandler(413)
def too_large(_error):
    flash("O arquivo ultrapassa o limite de 20 MB. Escolha imagens menores.", "error")
    return redirect(request.referrer or url_for("products"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("authenticated"):
        return redirect(url_for("dashboard"))
    error = ""
    if request.method == "POST":
        expected_user = os.environ.get("CENTRAL_USERNAME", "1")
        expected_password = os.environ.get("CENTRAL_PASSWORD", "1")
        if request.form.get("username", "") == expected_user and request.form.get("password", "") == expected_password:
            session.clear()
            session["authenticated"] = True
            session["csrf"] = secrets.token_urlsafe(24)
            target = request.args.get("next", "")
            if not target.startswith("/") or target.startswith("//"):
                target = url_for("dashboard")
            return redirect(target)
        error = "Usuário ou senha incorretos."
    return render_template("login.html", error=error)

@app.before_request
def csrf_protect():
    if request.method == "POST" and request.endpoint != "login":
        token = session.get("csrf", "")
        if not token or request.form.get("csrf_token", "") != token:
            abort(400, "Sessão expirada ou formulário inválido. Atualize a página e tente novamente.")

@app.context_processor
def csrf_context():
    return {"csrf_token": session.get("csrf", "")}

@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    with connect() as con:
        counts = {
            "products": con.execute("SELECT COUNT(*) FROM products").fetchone()[0],
            "posts": con.execute("SELECT COUNT(*) FROM posts").fetchone()[0],
            "ready": con.execute("SELECT COUNT(*) FROM posts WHERE status='Pronto'").fetchone()[0],
            "published": con.execute("SELECT COUNT(*) FROM posts WHERE status='Publicado'").fetchone()[0],
        }
        upcoming = con.execute("""SELECT posts.*, products.name AS product_name FROM posts
          LEFT JOIN products ON products.id=posts.product_id WHERE posts.status!='Publicado'
          ORDER BY CASE WHEN planned_date='' THEN 1 ELSE 0 END, planned_date, posts.id DESC LIMIT 6""").fetchall()
        metrics = con.execute("SELECT COALESCE(SUM(clicks),0), COALESCE(SUM(orders),0) FROM metrics").fetchone()
    return render_template("dashboard.html", counts=counts, upcoming=upcoming, clicks=metrics[0], orders=metrics[1])

@app.route("/produtos")
@login_required
def products():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sql = "SELECT * FROM products WHERE 1=1"
    params = []
    if q:
        sql += " AND (name LIKE ? OR notes LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    if category:
        sql += " AND category=?"
        params.append(category)
    sql += " ORDER BY id DESC"
    with connect() as con:
        rows = con.execute(sql, params).fetchall()
        categories = [r[0] for r in con.execute("SELECT DISTINCT category FROM products WHERE category!='' ORDER BY category").fetchall()]
        images = con.execute("SELECT product_id, filename FROM product_images ORDER BY id").fetchall()
    gallery = {}
    for image in images:
        gallery.setdefault(image["product_id"], []).append(image["filename"])
    return render_template("products.html", rows=rows, gallery=gallery, q=q, category=category, categories=categories)

@app.route("/produto/novo", methods=["GET", "POST"])
@login_required
def new_product():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("O nome do produto é obrigatório.", "error")
            return redirect(url_for("new_product"))
        primary = save_upload(request.files.get("image"))
        with connect() as con:
            cur = con.execute("""INSERT INTO products(name,category,price,affiliate_link,commission,notes,image_filename)
              VALUES(?,?,?,?,?,?,?)""", (name, request.form.get("category","").strip(), request.form.get("price","").strip(),
              request.form.get("affiliate_link","").strip(), request.form.get("commission","").strip(),
              request.form.get("notes","").strip(), primary))
            product_id = cur.lastrowid
            used = 1 if primary else 0
            for file in request.files.getlist("images"):
                if used >= MAX_IMAGES_PER_PRODUCT:
                    break
                filename = save_upload(file)
                if filename:
                    con.execute("INSERT INTO product_images(product_id,filename) VALUES(?,?)", (product_id, filename))
                    used += 1
        flash("Produto salvo com sucesso.")
        return redirect(url_for("products"))
    return render_template("product_form.html", p=None, heading="Cadastrar produto", images_count=0)

@app.route("/produto/<int:product_id>/editar", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product = get_product(product_id)
    if not product:
        abort(404)
    p, images = product["row"], product["images"]
    if request.method == "POST":
        primary = save_upload(request.files.get("image")) or p["image_filename"]
        with connect() as con:
            con.execute("""UPDATE products SET name=?,category=?,price=?,affiliate_link=?,commission=?,notes=?,image_filename=? WHERE id=?""",
                (request.form.get("name","").strip(), request.form.get("category","").strip(), request.form.get("price","").strip(),
                 request.form.get("affiliate_link","").strip(), request.form.get("commission","").strip(),
                 request.form.get("notes","").strip(), primary, product_id))
            used = con.execute("SELECT COUNT(*) FROM product_images WHERE product_id=?", (product_id,)).fetchone()[0] + (1 if primary else 0)
            for file in request.files.getlist("images"):
                if used >= MAX_IMAGES_PER_PRODUCT:
                    break
                filename = save_upload(file)
                if filename:
                    con.execute("INSERT INTO product_images(product_id,filename) VALUES(?,?)", (product_id, filename))
                    used += 1
        flash("Produto atualizado. As fotos existentes foram preservadas.")
        return redirect(url_for("products"))
    return render_template("product_form.html", p=p, heading="Editar produto", images_count=len(images))

@app.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(UPLOAD_DIR, filename)

@app.route("/calendario")
@login_required
def posts():
    month = request.args.get("month", date.today().strftime("%Y-%m"))
    with connect() as con:
        rows = con.execute("""SELECT posts.*, products.name AS product_name FROM posts
          LEFT JOIN products ON products.id=posts.product_id ORDER BY CASE WHEN planned_date='' THEN 1 ELSE 0 END, planned_date, posts.id DESC""").fetchall()
        products = con.execute("SELECT id,name FROM products ORDER BY name COLLATE NOCASE").fetchall()
    return render_template("posts.html", rows=rows, products=products, month=month)

@app.route("/publicacao/nova", methods=["GET", "POST"])
@login_required
def new_post():
    with connect() as con:
        products = con.execute("SELECT id,name FROM products ORDER BY name COLLATE NOCASE").fetchall()
    product_id = request.args.get("product_id", type=int)
    if request.method == "POST":
        with connect() as con:
            con.execute("""INSERT INTO posts(product_id,planned_date,format,status,caption,hashtags,cta,notes)
              VALUES(?,?,?,?,?,?,?,?)""", (request.form.get("product_id") or None, request.form.get("planned_date",""),
              request.form.get("format","Story"), request.form.get("status","Ideia"), request.form.get("caption","").strip(),
              request.form.get("hashtags","").strip(), request.form.get("cta","").strip(), request.form.get("notes","").strip()))
        flash("Publicação planejada.")
        return redirect(url_for("posts"))
    return render_template("post_form.html", p=None, products=products, heading="Planejar publicação", default_product=product_id)

@app.route("/publicacao/<int:post_id>/editar", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    with connect() as con:
        p = con.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
        products = con.execute("SELECT id,name FROM products ORDER BY name COLLATE NOCASE").fetchall()
    if not p:
        abort(404)
    if request.method == "POST":
        with connect() as con:
            con.execute("""UPDATE posts SET product_id=?,planned_date=?,format=?,status=?,caption=?,hashtags=?,cta=?,notes=? WHERE id=?""",
              (request.form.get("product_id") or None, request.form.get("planned_date",""), request.form.get("format","Story"),
               request.form.get("status","Ideia"), request.form.get("caption","").strip(), request.form.get("hashtags","").strip(),
               request.form.get("cta","").strip(), request.form.get("notes","").strip(), post_id))
        flash("Publicação atualizada.")
        return redirect(url_for("posts"))
    return render_template("post_form.html", p=p, products=products, heading="Editar publicação", default_product=p["product_id"])

@app.route("/publicacao/<int:post_id>/publicada", methods=["POST"])
@login_required
def mark_published(post_id):
    with connect() as con:
        cur = con.execute("UPDATE posts SET status='Publicado' WHERE id=?", (post_id,))
        if cur.rowcount == 0:
            abort(404)
    flash("Publicação marcada como publicada.")
    return redirect(request.referrer or url_for("posts"))

@app.route("/resultados", methods=["GET", "POST"])
@login_required
def metrics():
    with connect() as con:
        products = con.execute("SELECT id,name FROM products ORDER BY name COLLATE NOCASE").fetchall()
        if request.method == "POST":
            clicks = max(0, min(10**9, int(request.form.get("clicks", "0") or 0)))
            orders = max(0, min(10**9, int(request.form.get("orders", "0") or 0)))
            con.execute("""INSERT INTO metrics(product_id,report_date,clicks,orders,commission_value,notes)
              VALUES(?,?,?,?,?,?)""", (request.form.get("product_id") or None, request.form.get("report_date") or date.today().isoformat(),
              clicks, orders, request.form.get("commission_value","").strip(), request.form.get("notes","").strip()))
            flash("Resultado registrado. Os dados são lançados manualmente.")
            return redirect(url_for("metrics"))
        rows = con.execute("""SELECT metrics.*, products.name AS product_name FROM metrics
          LEFT JOIN products ON products.id=metrics.product_id ORDER BY report_date DESC, metrics.id DESC LIMIT 100""").fetchall()
        totals = con.execute("SELECT COALESCE(SUM(clicks),0),COALESCE(SUM(orders),0) FROM metrics").fetchone()
    return render_template("metrics.html", products=products, rows=rows, totals=totals)

@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, message="Essa página não existe."), 404

@app.errorhandler(400)
def bad_request(error):
    return render_template("error.html", code=400, message=getattr(error, "description", "Pedido inválido.")), 400

if __name__ == "__main__":
    print("Central de Afiliados V2")
    print(f"Banco novo e separado: {DB_PATH}")
    print("Acesse no Chrome do mesmo celular: http://127.0.0.1:5001")
    app.run(host="127.0.0.1", port=5001, debug=False)
