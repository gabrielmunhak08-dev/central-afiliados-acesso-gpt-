from flask import session
from flask import Flask, request, redirect, url_for, render_template_string, flash
import sqlite3
import os
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "central.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("CENTRAL_SECRET_KEY", "troque-esta-chave-local")

@app.before_request
def require_login():
    if request.endpoint in ("login", "logout"):
        return None
    if not session.get("logged_in"):
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    erro = ""
    if request.method == "POST":
        usuario = request.form.get("username", "").strip()
        senha = request.form.get("password", "")
        usuario_correto = os.environ.get("CENTRAL_USERNAME", "1")
        senha_correta = os.environ.get("CENTRAL_PASSWORD", "1")

        if usuario == usuario_correto and senha == senha_correta:
            session.clear()
            session["logged_in"] = True
            return redirect(url_for("index"))
        erro = "Usuário ou senha incorretos."

    return render_template_string("""
    <!doctype html>
    <html lang="pt-br">
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <meta charset="utf-8">
      <title>Login - Central de Afiliados</title>
      <style>
        * { box-sizing: border-box; }
        body {
          margin: 0; min-height: 100vh; display: grid;
          place-items: center; padding: 20px;
          background: #0b0d10; color: #f5f5f5;
          font-family: Arial, sans-serif;
        }
        .card {
          width: 100%; max-width: 380px; padding: 28px;
          background: #15181d; border: 1px solid #30343b;
          border-radius: 18px;
        }
        h1 { font-size: 24px; margin-top: 0; }
        p { color: #aaa; }
        label { display: block; margin: 18px 0 7px; }
        input {
          width: 100%; padding: 13px; border-radius: 9px;
          border: 1px solid #3a3f47; background: #0b0d10;
          color: white; font-size: 16px;
        }
        button {
          width: 100%; margin-top: 22px; padding: 14px;
          border: 0; border-radius: 9px; background: #ff6b00;
          color: white; font-size: 16px; font-weight: bold;
        }
        .erro { color: #ff8585; }
      </style>
    </head>
    <body>
      <main class="card">
        <h1>Central de Afiliados</h1>
        <p>Entre para acessar seu painel.</p>
        {% if erro %}<p class="erro">{{ erro }}</p>{% endif %}
        <form method="post">
          <label for="username">Usuário</label>
          <input id="username" name="username" autocomplete="username"
                 required>
          <label for="password">Senha</label>
          <input id="password" name="password" type="password"
                 autocomplete="current-password" required>
          <button type="submit">Entrar</button>
        </form>
      </main>
    </body>
    </html>
    """, erro=erro)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


STATUSES = ["Ideia", "Preparando", "Pronto", "Publicado", "Pausado"]
FORMATS = ["Story", "Feed", "Reel", "Outro"]

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT DEFAULT '',
                price TEXT DEFAULT '',
                affiliate_link TEXT DEFAULT '',
                commission TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                image_filename TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                planned_date TEXT DEFAULT '',
                format TEXT DEFAULT 'Story',
                status TEXT DEFAULT 'Ideia',
                caption TEXT DEFAULT '',
                hashtags TEXT DEFAULT '',
                cta TEXT DEFAULT '',
                image_filename TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                report_date TEXT DEFAULT '',
                clicks INTEGER DEFAULT 0,
                orders INTEGER DEFAULT 0,
                commission_value TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL
            )
        """)

def get_products():
    with db() as conn:
        return conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()

def get_post(post_id):
    with db() as conn:
        return conn.execute("""
            SELECT posts.*, products.name AS product_name, products.affiliate_link AS affiliate_link
            FROM posts LEFT JOIN products ON products.id = posts.product_id
            WHERE posts.id = ?
        """, (post_id,)).fetchone()

@app.template_filter("brdate")
def brdate(value):
    if not value:
        return "Sem data"
    try:
        y, m, d = value.split("-")
        return f"{d}/{m}/{y}"
    except Exception:
        return value

STYLE = """
:root{--bg:#f5f6fa;--card:#fff;--ink:#1d2433;--muted:#667085;--line:#e4e7ec;--accent:#e65a22;--accent2:#fff0e9}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
header{background:#202635;color:#fff;padding:18px 16px 14px}header .brand{font-size:21px;font-weight:800;letter-spacing:.2px}header p{margin:5px 0 0;color:#cbd0db;font-size:13px}
nav{display:flex;gap:8px;overflow-x:auto;padding:11px 12px;background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:2}
nav a{white-space:nowrap;text-decoration:none;color:var(--ink);background:#f2f4f7;padding:9px 12px;border-radius:999px;font-size:13px;font-weight:650}
main{max-width:960px;margin:0 auto;padding:16px 12px 36px}.pagehead{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin:6px 0 16px}.pagehead h1{font-size:23px;margin:0}.sub{color:var(--muted);font-size:13px;margin-top:5px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:10px}.stat,.card,.formcard{background:var(--card);border:1px solid var(--line);border-radius:15px;padding:14px;margin-bottom:12px}.stat small{color:var(--muted);display:block}.stat strong{font-size:27px;display:block;margin-top:5px}.stat span{font-size:12px;color:var(--muted)}
.btn,button{border:0;background:var(--accent);color:white;padding:11px 14px;border-radius:10px;font-weight:750;font-size:14px;text-decoration:none;display:inline-block;cursor:pointer}.btn.secondary,button.secondary{background:#eef0f4;color:#283142}.btn.danger,button.danger{background:#b42318}.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
label{display:block;font-size:13px;font-weight:700;margin:12px 0 5px}input,select,textarea{font:inherit;font-size:16px;width:100%;border:1px solid #cfd4dc;border-radius:10px;padding:11px;background:#fff;color:var(--ink)}textarea{min-height:86px;resize:vertical}.formgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:0 12px}
.itemtitle{font-size:17px;font-weight:800;margin:0 0 5px}.muted{color:var(--muted);font-size:13px}.pill{display:inline-block;border-radius:999px;padding:5px 8px;font-size:11px;font-weight:800;background:#f2f4f7;color:#344054}.pill.orange{background:var(--accent2);color:#b54708}.itemrow{display:flex;gap:12px;align-items:flex-start}.thumb{width:72px;height:72px;object-fit:cover;border-radius:10px;background:#f2f4f7;flex-shrink:0}.itembody{min-width:0;flex:1}.itembody a{overflow-wrap:anywhere}.empty{padding:25px;text-align:center;color:var(--muted);background:#fff;border:1px dashed #cfd4dc;border-radius:15px}.flash{padding:11px 13px;background:#ecfdf3;border:1px solid #abefc6;color:#067647;border-radius:10px;margin-bottom:12px}.tinyform{display:inline}.tinyform button{padding:8px 10px;font-size:12px}.sectiontitle{font-size:16px;margin:20px 0 10px}.kit{white-space:pre-wrap;background:#f8fafc;border:1px solid var(--line);padding:12px;border-radius:10px;font-size:14px;overflow-wrap:anywhere}
footer{text-align:center;color:var(--muted);font-size:12px;padding:18px}
@media(min-width:700px){header{padding-left:max(18px,calc((100% - 936px)/2));padding-right:max(18px,calc((100% - 936px)/2))}nav{justify-content:center}}
"""

LAYOUT = """
<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#202635"><title>{{ title }} · Central Afiliado</title><style>""" + STYLE + """</style>
<style>
:root {
  color-scheme: dark;
  --bg: #0b0d10;
  --panel: #15191f;
  --panel2: #1c222b;
  --text: #f1f5f9;
  --muted: #a1aab8;
  --accent: #ff6b00;
  --border: #2b323d;
}
html, body {
  background: var(--bg) !important;
  color: var(--text) !important;
}
body {
  margin: 0;
}
header, nav, main, section, article, aside, form,
.card, .panel, .container, .content, .stat, .metric,
table, tr, td, th {
  color: var(--text);
}
.card, .panel, .stat, .metric, section, article,
form, .container, .content {
  background-color: var(--panel) !important;
  border-color: var(--border) !important;
}
input, textarea, select {
  background: var(--panel2) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}
button, .btn, input[type="submit"] {
  background: var(--accent) !important;
  color: white !important;
  border: 0 !important;
}
a {
  color: #ff9b52 !important;
}
p, small, label, .muted {
  color: var(--muted);
}
table th, table td {
  border-color: var(--border) !important;
}
</style>

</head><body>
<header><div class="brand">🛍️ Central de Afiliado</div><p>Organize produtos, prepare conteúdos e planeje suas publicações.</p></header>
<nav><a href="{{ url_for('index') }}">Painel</a><a href="{{ url_for('products') }}">Produtos</a><a href="{{ url_for('new_product') }}">+ Produto</a><a href="{{ url_for('posts') }}">Calendário</a><a href="{{ url_for('new_post') }}">+ Publicação</a><a href="{{ url_for('metrics') }}">Resultados</a><a href="{{ url_for('logout') }}">Sair</a></nav>
<main>{% with messages = get_flashed_messages() %}{% for message in messages %}<div class="flash">{{ message }}</div>{% endfor %}{% endwith %}{{ content|safe }}</main><footer>Central pessoal · V1 · Os dados ficam neste dispositivo até você fazer backup.</footer></body></html>
"""

def page(title, template, **context):
    content = render_template_string(template, **context)
    return render_template_string(LAYOUT, title=title, content=content)

@app.route("/")
def index():
    with db() as conn:
        product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        post_count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        ready_count = conn.execute("SELECT COUNT(*) FROM posts WHERE status='Pronto'").fetchone()[0]
        published_count = conn.execute("SELECT COUNT(*) FROM posts WHERE status='Publicado'").fetchone()[0]
        upcoming = conn.execute("""
          SELECT posts.*, products.name AS product_name FROM posts
          LEFT JOIN products ON products.id=posts.product_id
          WHERE posts.status != 'Publicado' ORDER BY
          CASE WHEN planned_date='' THEN 1 ELSE 0 END, planned_date ASC, posts.id DESC LIMIT 6
        """).fetchall()
    template = """
    <div class="pagehead"><div><h1>Painel principal</h1><div class="sub">Seu espaço de organização, sem complicação.</div></div><a class="btn" href="{{ url_for('new_post') }}">+ Planejar</a></div>
    <div class="grid">
      <div class="stat"><small>Produtos</small><strong>{{ product_count }}</strong><span>No catálogo</span></div>
      <div class="stat"><small>Publicações</small><strong>{{ post_count }}</strong><span>Planejadas ou registradas</span></div>
      <div class="stat"><small>Prontas</small><strong>{{ ready_count }}</strong><span>Preparadas para postar</span></div>
      <div class="stat"><small>Publicadas</small><strong>{{ published_count }}</strong><span>Marcadas manualmente</span></div>
    </div>
    <h2 class="sectiontitle">Próximas tarefas</h2>
    {% if upcoming %}{% for p in upcoming %}
      <div class="card"><div class="itemrow"><div class="itembody"><div class="itemtitle">{{ p['product_name'] or 'Produto não selecionado' }}</div><div class="muted">{{ p['planned_date']|brdate }} · {{ p['format'] }} · <span class="pill {{ 'orange' if p['status']=='Pronto' else '' }}">{{ p['status'] }}</span></div></div><a class="btn secondary" href="{{ url_for('edit_post', post_id=p['id']) }}">Abrir</a></div></div>
    {% endfor %}{% else %}<div class="empty">Ainda não há publicações planejadas.<br><br><a class="btn" href="{{ url_for('new_post') }}">Criar primeira publicação</a></div>{% endif %}
    <div class="actions"><a class="btn secondary" href="{{ url_for('new_product') }}">Cadastrar produto</a><a class="btn secondary" href="{{ url_for('metrics') }}">Registrar resultados</a></div>
    """
    return page("Painel", template, product_count=product_count, post_count=post_count, ready_count=ready_count, published_count=published_count, upcoming=upcoming)

PRODUCT_FORM = """
<div class="pagehead"><div><h1>{{ heading }}</h1><div class="sub">Cadastre os dados que você quer ter à mão ao criar uma divulgação.</div></div></div>
<form class="formcard" method="post" enctype="multipart/form-data">
  <label>Nome do produto *</label><input name="name" required value="{{ p['name'] if p else '' }}" placeholder="Ex.: Relógio esportivo">
  <div class="formgrid"><div><label>Categoria</label><input name="category" value="{{ p['category'] if p else '' }}" placeholder="Casa, beleza, tecnologia..."></div><div><label>Preço exibido (R$)</label><input name="price" value="{{ p['price'] if p else '' }}" placeholder="Ex.: 49,90"></div></div>
  <label>Link de afiliado</label><input name="affiliate_link" type="url" value="{{ p['affiliate_link'] if p else '' }}" placeholder="Cole o link gerado pela Shopee">
  <label>Comissão estimada (opcional)</label><input name="commission" value="{{ p['commission'] if p else '' }}" placeholder="Ex.: 5% ou R$ 2,50">
  <label>Foto principal (opcional)</label><input name="image" type="file" accept="image/*">
  <label>Fotos adicionais (até 9, total máximo de 10)</label>
  <input name="images" type="file" accept="image/*" multiple>
  <div class="muted">Você poderá usar essas imagens nas publicações futuras.</div>
  <label>Observações</label><textarea name="notes" placeholder="Pontos fortes, público, cuidados com preço...">{{ p['notes'] if p else '' }}</textarea>
  <div class="actions"><button type="submit">Salvar produto</button><a class="btn secondary" href="{{ url_for('products') }}">Cancelar</a></div>
</form>
"""

@app.route("/produtos")
def products():
    with db() as conn:
        rows = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    with db() as conn:
        gallery_rows = conn.execute(
            "SELECT product_id, filename FROM product_images ORDER BY id"
        ).fetchall()
    gallery_by_product = {}
    for image in gallery_rows:
        gallery_by_product.setdefault(image["product_id"], []).append(image["filename"])
    template = """
    <div class="pagehead">
      <div>
        <h1>Catálogo de produtos</h1>
        <div class="sub">Guarde links e informações para reutilizar nas publicações.</div>
      </div>
      <a class="btn" href="{{ url_for('new_product') }}">+ Produto</a>
    </div>
    {% if rows %}
      {% for p in rows %}
      <div class="card" style="margin-bottom:16px;overflow:hidden">
        <div style="display:flex;align-items:flex-start;gap:16px;flex-wrap:wrap">
          {% if p['image_filename'] %}
          <img class="thumb" style="width:100px;height:100px;object-fit:contain;flex-shrink:0"
               src="{{ url_for('uploaded_file', filename=p['image_filename']) }}" alt="Produto">
          {% endif %}
          <div class="itembody" style="flex:1;min-width:180px">
            <div class="itemtitle">{{ p['name'] }}</div>
            <div class="muted">{{ p['category'] or 'Sem categoria' }}{% if p['price'] %} · R$ {{ p['price'] }}{% endif %}</div>
            {% if p['commission'] %}<p class="muted">Comissão estimada: {{ p['commission'] }}</p>{% endif %}
            {% if p['affiliate_link'] %}
              <p><a href="{{ p['affiliate_link'] }}" target="_blank" rel="noopener">Abrir link de afiliado</a></p>
            {% else %}
              <p class="muted">Link ainda não cadastrado</p>
            {% endif %}
            <div class="actions">
              <a class="btn secondary" href="{{ url_for('edit_product', product_id=p['id']) }}">Editar</a>
              <a class="btn secondary" href="{{ url_for('new_post', product_id=p['id']) }}">Planejar publicação</a>
            </div>
          </div>
        </div>
        {% set gallery = gallery_by_product.get(p['id'], []) %}
        {% if gallery %}
        <div style="margin-top:14px">
          <div class="muted" style="margin-bottom:8px">Fotos adicionais ({{ gallery|length }})</div>
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            {% for filename in gallery %}
            <img src="{{ url_for('uploaded_file', filename=filename) }}"
                 alt="Foto adicional de {{ p['name'] }}"
                 style="width:64px;height:64px;object-fit:cover;border-radius:8px">
            {% endfor %}
          </div>
        </div>
        {% endif %}
      </div>
      {% endfor %}
    {% else %}
      <div class="empty">Seu catálogo está vazio.<br><br>
        <a class="btn" href="{{ url_for('new_product') }}">Cadastrar primeiro produto</a>
      </div>
    {% endif %}
    """
    return page("Produtos", template, rows=rows, gallery_by_product=gallery_by_product)

@app.route("/produto/novo", methods=["GET", "POST"])
def new_product():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("O nome do produto é obrigatório.")
            return redirect(url_for("new_product"))
        filename = save_upload(request.files.get("image"))
        with db() as conn:
            cur = conn.execute("INSERT INTO products (name,category,price,affiliate_link,commission,notes,image_filename) VALUES (?,?,?,?,?,?,?)",
                (name, request.form.get("category","").strip(), request.form.get("price","").strip(),
                 request.form.get("affiliate_link","").strip(), request.form.get("commission","").strip(),
                 request.form.get("notes","").strip(), filename))
            product_id = cur.lastrowid
            saved = 0
            for image in request.files.getlist("images"):
                if saved >= 9:
                    break
                extra = save_upload(image)
                if extra:
                    conn.execute("INSERT INTO product_images (product_id,filename) VALUES (?,?)", (product_id, extra))
                    saved += 1
        flash("Produto cadastrado com galeria de fotos.")
        flash("Produto cadastrado.")
        return redirect(url_for("products"))
    return page("Novo produto", PRODUCT_FORM, heading="Cadastrar produto", p=None)

@app.route("/produto/<int:product_id>/editar", methods=["GET", "POST"])
def edit_product(product_id):
    with db() as conn:
        p = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    if not p:
        flash("Produto não encontrado.")
        return redirect(url_for("products"))
    if request.method == "POST":
        filename = save_upload(request.files.get("image")) or p["image_filename"]
        with db() as conn:
            conn.execute("""UPDATE products SET name=?,category=?,price=?,affiliate_link=?,commission=?,notes=?,image_filename=? WHERE id=?""",
                (request.form.get("name","").strip(), request.form.get("category","").strip(), request.form.get("price","").strip(),
                 request.form.get("affiliate_link","").strip(), request.form.get("commission","").strip(),
                 request.form.get("notes","").strip(), filename, product_id))
            count = conn.execute("SELECT COUNT(*) FROM product_images WHERE product_id=?", (product_id,)).fetchone()[0]
            for image in request.files.getlist("images"):
                if count >= 9:
                    break
                extra = save_upload(image)
                if extra:
                    conn.execute("INSERT INTO product_images (product_id,filename) VALUES (?,?)", (product_id, extra))
                    count += 1
        flash("Produto atualizado.")
        return redirect(url_for("products"))
    return page("Editar produto", PRODUCT_FORM, heading="Editar produto", p=p)

@app.route("/calendario")
def posts():
    with db() as conn:
        rows = conn.execute("""SELECT posts.*, products.name AS product_name FROM posts LEFT JOIN products ON products.id=posts.product_id
          ORDER BY CASE WHEN planned_date='' THEN 1 ELSE 0 END, planned_date ASC, posts.id DESC""").fetchall()
    template = """
    <div class="pagehead"><div><h1>Calendário editorial</h1><div class="sub">Planeje, prepare e marque o que já foi publicado.</div></div><a class="btn" href="{{ url_for('new_post') }}">+ Publicação</a></div>
    {% if rows %}{% for p in rows %}
    <div class="card"><div class="itemrow"><div class="itembody"><div class="itemtitle">{{ p['product_name'] or 'Produto não selecionado' }}</div>
    <div class="muted">{{ p['planned_date']|brdate }} · {{ p['format'] }} · <span class="pill {{ 'orange' if p['status']=='Pronto' else '' }}">{{ p['status'] }}</span></div>
    {% if p['caption'] %}<p>{{ p['caption'][:180] }}{% if p['caption']|length > 180 %}…{% endif %}</p>{% endif %}
    <div class="actions"><a class="btn secondary" href="{{ url_for('edit_post', post_id=p['id']) }}">Editar / kit</a>
    {% if p['status'] != 'Publicado' %}<form class="tinyform" method="post" action="{{ url_for('mark_published', post_id=p['id']) }}"><button type="submit">Marcar publicada</button></form>{% endif %}</div>
    </div></div></div>
    {% endfor %}{% else %}<div class="empty">Nenhuma publicação planejada ainda.<br><br><a class="btn" href="{{ url_for('new_post') }}">Planejar primeira publicação</a></div>{% endif %}
    """
    return page("Calendário", template, rows=rows)

POST_FORM = """
<div class="pagehead"><div><h1>{{ heading }}</h1><div class="sub">Preencha os materiais e deixe tudo pronto para copiar e publicar.</div></div></div>
<form class="formcard" method="post" enctype="multipart/form-data">
  <label>Produto</label><select id="post-product" name="product_id"><option value="">— Selecionar produto —</option>{% for product in products %}<option value="{{ product['id'] }}" data-link="{{ product['affiliate_link'] or '' }}" {% if selected_product|string == product['id']|string %}selected{% endif %}>{{ product['name'] }}</option>{% endfor %}</select>
  <label>Link de afiliado do produto</label>
  <div class="actions" style="align-items:center">
    <input id="post-affiliate-link" type="url" value="{{ p['affiliate_link'] if p and p['affiliate_link'] else '' }}" placeholder="Selecione um produto com link cadastrado" readonly style="flex:1;min-width:0">
    <button type="button" onclick="copyField('post-affiliate-link','Link')">Copiar link</button>
  </div>
  <div class="formgrid"><div><label>Data planejada</label><input type="date" name="planned_date" value="{{ p['planned_date'] if p else '' }}"></div>
  <div><label>Formato</label><select name="format">{% for f in formats %}<option {% if p and p['format']==f %}selected{% elif not p and f=='Story' %}selected{% endif %}>{{ f }}</option>{% endfor %}</select></div>
  <div><label>Status</label><select name="status">{% for s in statuses %}<option {% if p and p['status']==s %}selected{% elif not p and s=='Ideia' %}selected{% endif %}>{{ s }}</option>{% endfor %}</select></div></div>
  <label>Legenda</label><textarea name="caption" placeholder="Escreva a legenda da publicação">{{ p['caption'] if p else '' }}</textarea>
  <label>Hashtags</label><textarea id="post-hashtags" name="hashtags" placeholder="#achadinhos #ofertas">{{ p['hashtags'] if p else '' }}</textarea>
  <div class="actions"><button type="button" class="secondary" onclick="copyDescription()">Copiar descrição + hashtags</button></div>
  <label>Chamada para ação (CTA)</label><input name="cta" value="{{ p['cta'] if p else '' }}" placeholder="Ex.: Confira no link do perfil">
  <label>Imagem final (opcional)</label><input name="image" type="file" accept="image/*">
  <label>Observações</label><textarea name="notes" placeholder="Ex.: revisar preço antes de publicar">{{ p['notes'] if p else '' }}</textarea>
  <div class="actions"><button type="submit">Salvar publicação</button><a class="btn secondary" href="{{ url_for('posts') }}">Cancelar</a></div>
</form>
<script>
function copyField(id, label) {
  const field = document.getElementById(id);
  const value = field ? field.value.trim() : '';
  if (!value) { alert(label + ' não disponível. Confira se o produto tem link cadastrado.'); return; }
  const fallback = () => {
    field.focus(); field.select();
    const ok = document.execCommand('copy');
    alert(ok ? label + ' copiado!' : 'Não foi possível copiar. Selecione e copie manualmente.');
  };
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(value).then(() => alert(label + ' copiado!')).catch(fallback);
  } else { fallback(); }
}
function copyDescription() {
  const caption = document.querySelector('[name="caption"]').value.trim();
  const hashtags = document.getElementById('post-hashtags').value.trim();
  const value = [caption, hashtags].filter(Boolean).join('\n\n');
  if (!value) { alert('A descrição e as hashtags estão vazias.'); return; }
  const area = document.createElement('textarea');
  area.value = value; document.body.appendChild(area); area.select();
  const ok = document.execCommand('copy'); area.remove();
  alert(ok ? 'Descrição e hashtags copiadas!' : 'Não foi possível copiar. Tente selecionar o texto manualmente.');
}
(function() {
  const select = document.getElementById('post-product');
  const link = document.getElementById('post-affiliate-link');
  if (!select || !link) return;
  function updateLink() {
    const option = select.options[select.selectedIndex];
    link.value = option ? (option.dataset.link || '') : '';
  }
  select.addEventListener('change', updateLink);
  if (select.value) updateLink();
})();
</script>
{% if p %}
<h2 class="sectiontitle">Kit de publicação</h2><div class="card">
  {% if p['image_filename'] %}<p><img class="thumb" src="{{ url_for('uploaded_file', filename=p['image_filename']) }}" alt="Arte da publicação"></p>{% endif %}
  <div class="kit" id="kit">{{ p['caption'] }}{% if p['caption'] and p['hashtags'] %}

{% endif %}{{ p['hashtags'] }}{% if p['cta'] %}

{{ p['cta'] }}{% endif %}{% if p['affiliate_link'] %}

Link: {{ p['affiliate_link'] }}{% endif %}</div>
  <div class="actions"><button type="button" onclick="copyKit()">Copiar kit completo</button>{% if p['affiliate_link'] %}<a class="btn secondary" target="_blank" rel="noopener" href="{{ p['affiliate_link'] }}">Abrir link</a>{% endif %}</div>
</div>
<script>function copyKit(){const t=document.getElementById('kit').innerText;if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(()=>alert('Kit copiado!')).catch(()=>fallback(t));}else{fallback(t)}}function fallback(t){const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove();alert('Kit copiado!')}</script>
{% endif %}
"""

@app.route("/publicacao/nova", methods=["GET", "POST"])
def new_post():
    products = get_products()
    selected_product = request.args.get("product_id", "")
    if request.method == "POST":
        filename = save_upload(request.files.get("image"))
        with db() as conn:
            conn.execute("""INSERT INTO posts (product_id,planned_date,format,status,caption,hashtags,cta,image_filename,notes)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (to_int(request.form.get("product_id")), request.form.get("planned_date",""),
                 request.form.get("format","Story"), request.form.get("status","Ideia"),
                 request.form.get("caption","").strip(), request.form.get("hashtags","").strip(),
                 request.form.get("cta","").strip(), filename, request.form.get("notes","").strip()))
        flash("Publicação planejada.")
        return redirect(url_for("posts"))
    return page("Nova publicação", POST_FORM, heading="Planejar publicação", p=None, products=products,
                selected_product=selected_product, formats=FORMATS, statuses=STATUSES)

@app.route("/publicacao/<int:post_id>/editar", methods=["GET", "POST"])
def edit_post(post_id):
    p = get_post(post_id)
    if not p:
        flash("Publicação não encontrada.")
        return redirect(url_for("posts"))
    products = get_products()
    if request.method == "POST":
        filename = save_upload(request.files.get("image")) or p["image_filename"]
        with db() as conn:
            conn.execute("""UPDATE posts SET product_id=?,planned_date=?,format=?,status=?,caption=?,hashtags=?,cta=?,image_filename=?,notes=? WHERE id=?""",
                (to_int(request.form.get("product_id")), request.form.get("planned_date",""),
                 request.form.get("format","Story"), request.form.get("status","Ideia"),
                 request.form.get("caption","").strip(), request.form.get("hashtags","").strip(),
                 request.form.get("cta","").strip(), filename, request.form.get("notes","").strip(), post_id))
        flash("Publicação atualizada.")
        return redirect(url_for("edit_post", post_id=post_id))
    return page("Editar publicação", POST_FORM, heading="Editar publicação", p=p, products=products,
                selected_product=p["product_id"] or "", formats=FORMATS, statuses=STATUSES)

@app.route("/publicacao/<int:post_id>/publicada", methods=["POST"])
def mark_published(post_id):
    with db() as conn:
        conn.execute("UPDATE posts SET status='Publicado' WHERE id=?", (post_id,))
    flash("Publicação marcada como publicada.")
    return redirect(url_for("posts"))

@app.route("/resultados", methods=["GET", "POST"])
def metrics():
    products = get_products()
    if request.method == "POST":
        with db() as conn:
            conn.execute("""INSERT INTO metrics (product_id,report_date,clicks,orders,commission_value,notes) VALUES (?,?,?,?,?,?)""",
                (to_int(request.form.get("product_id")), request.form.get("report_date",""),
                 max(0, to_int(request.form.get("clicks")) or 0), max(0, to_int(request.form.get("orders")) or 0),
                 request.form.get("commission_value","").strip(), request.form.get("notes","").strip()))
        flash("Resultado registrado.")
        return redirect(url_for("metrics"))
    with db() as conn:
        rows = conn.execute("""SELECT metrics.*, products.name AS product_name FROM metrics LEFT JOIN products ON products.id=metrics.product_id ORDER BY report_date DESC, metrics.id DESC""").fetchall()
        totals = conn.execute("SELECT COALESCE(SUM(clicks),0), COALESCE(SUM(orders),0) FROM metrics").fetchone()
    template = """
    <div class="pagehead"><div><h1>Resultados</h1><div class="sub">Registre os números do painel oficial da Shopee manualmente nesta primeira versão.</div></div></div>
    <div class="grid"><div class="stat"><small>Cliques registrados</small><strong>{{ totals[0] }}</strong><span>Soma dos registros inseridos</span></div><div class="stat"><small>Pedidos registrados</small><strong>{{ totals[1] }}</strong><span>Não representa sincronização automática</span></div></div>
    <form class="formcard" method="post"><h2 class="sectiontitle" style="margin-top:0">Adicionar resultado</h2>
      <label>Produto</label><select name="product_id"><option value="">— Geral / não selecionado —</option>{% for product in products %}<option value="{{ product['id'] }}">{{ product['name'] }}</option>{% endfor %}</select>
      <label>Data do relatório</label><input type="date" name="report_date" value="{{ today }}">
      <div class="formgrid"><div><label>Cliques</label><input type="number" name="clicks" min="0" value="0"></div><div><label>Pedidos</label><input type="number" name="orders" min="0" value="0"></div></div>
      <label>Comissão exibida (R$ ou texto)</label><input name="commission_value" placeholder="Ex.: 12,40">
      <label>Observações</label><textarea name="notes" placeholder="Período do relatório, origem dos dados..."></textarea>
      <div class="actions"><button type="submit">Salvar resultado</button></div>
    </form>
    <h2 class="sectiontitle">Histórico</h2>
    {% if rows %}{% for r in rows %}<div class="card"><div class="itemtitle">{{ r['product_name'] or 'Geral / sem produto' }}</div><div class="muted">{{ r['report_date']|brdate }} · {{ r['clicks'] }} cliques · {{ r['orders'] }} pedidos</div>{% if r['commission_value'] %}<p>Comissão: {{ r['commission_value'] }}</p>{% endif %}{% if r['notes'] %}<p class="muted">{{ r['notes'] }}</p>{% endif %}</div>{% endfor %}{% else %}<div class="empty">Nenhum resultado registrado.</div>{% endif %}
    """
    return page("Resultados", template, products=products, rows=rows, totals=totals, today=date.today().isoformat())

def to_int(value):
    try:
        return int(value) if value not in (None, "") else None
    except (ValueError, TypeError):
        return None

def save_upload(file):
    if not file or not file.filename:
        return ""
    # Only accept common image formats; filenames are generated to avoid path traversal.
    allowed = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        flash("Imagem não salva: use PNG, JPG, WEBP ou GIF.")
        return ""
    import secrets
    filename = secrets.token_hex(12) + ext
    file.save(os.path.join(UPLOAD_DIR, filename))
    return filename

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(UPLOAD_DIR, filename)

with app.app_context():
    init_db()

if __name__ == "__main__":
    # Acesso local no próprio celular. Não exponha publicamente sem adicionar autenticação.
    app.run(host="127.0.0.1", port=5000, debug=False)
