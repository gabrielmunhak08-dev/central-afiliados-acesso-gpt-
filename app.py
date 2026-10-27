from flask import Flask, request, redirect, url_for, render_template_string, flash, session
import sqlite3
import os
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "central.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("CENTRAL_SECRET_KEY", "central-afiliado-chave-local-trocar")

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
:root{color-scheme:dark;--bg:#0b0d10;--card:#15181d;--panel2:#1c222b;--ink:#e5e7eb;--muted:#9ca3af;--line:#303640;--accent:#ff6b00;--accent2:#3a2416}
*{box-sizing:border-box}html{background:var(--bg);scroll-behavior:smooth}body{margin:0;background:radial-gradient(ellipse at top,#171b22 0%,var(--bg) 48%);color:var(--ink);font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;min-height:100vh}
header{background:#111419;color:#fff;padding:20px 16px 16px;border-bottom:1px solid var(--line)}header .brand{font-size:21px;font-weight:850;letter-spacing:.2px}header p{margin:5px 0 0;color:#a1aab8;font-size:13px}
nav{display:flex;gap:8px;overflow-x:auto;padding:10px 12px;background:rgba(15,17,21,.97);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:10;scrollbar-width:thin;backdrop-filter:blur(12px)}nav a{white-space:nowrap;text-decoration:none!important;color:#cbd5e1!important;background:#1b2028;padding:10px 13px;border:1px solid #2b323d;border-radius:12px;font-size:13px;font-weight:700}nav a:hover{background:#332216;border-color:var(--accent);color:#ff9b52!important}
main{max-width:1040px;margin:0 auto;padding:20px 14px 100px}.pagehead{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin:6px 0 18px;flex-wrap:wrap}.pagehead h1{font-size:clamp(22px,5vw,28px);letter-spacing:-.5px;margin:0}.sub{color:var(--muted);font-size:13px;margin-top:6px;line-height:1.5}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.stat,.card,.formcard{background:linear-gradient(145deg,#171b21,#13161b);border:1px solid var(--line);border-radius:17px;padding:15px;margin-bottom:12px;box-shadow:0 8px 24px rgba(0,0,0,.12)}.stat small{color:var(--muted);display:block;font-size:12px}.stat strong{font-size:clamp(25px,6vw,31px);display:block;margin-top:7px;letter-spacing:-.7px}.stat span{font-size:12px;color:var(--muted)}
.btn,button{border:1px solid transparent;background:var(--accent);color:#fff!important;padding:11px 14px;border-radius:11px;font-weight:800;font-size:14px;text-decoration:none!important;display:inline-flex;align-items:center;justify-content:center;gap:6px;cursor:pointer;min-height:42px;transition:transform .15s,filter .15s}.btn:hover,button:hover{filter:brightness(1.08);transform:translateY(-1px)}.btn.secondary,button.secondary{background:#202630!important;color:#e5e7eb!important;border-color:#343c48!important;box-shadow:none}.btn.danger,button.danger{background:#7f1d1d!important;color:#fecaca!important}.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
label{display:block;font-size:13px;font-weight:750;margin:14px 0 6px;color:#d8dee8}input,select,textarea{font:inherit;font-size:16px;width:100%;border:1px solid #343c48;border-radius:11px;padding:12px;background:var(--panel2);color:var(--ink);outline:none}input:focus,select:focus,textarea:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(255,107,0,.13)}input[type=file]{font-size:13px;padding:9px}textarea{min-height:92px;resize:vertical}.formgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:0 12px}
.itemtitle{font-size:17px;font-weight:820;margin:0 0 6px;overflow-wrap:anywhere}.muted{color:var(--muted);font-size:13px;line-height:1.5}.pill{display:inline-block;border-radius:999px;padding:5px 9px;font-size:11px;font-weight:800;background:#242a33;color:#d1d5db}.pill.orange{background:#3a2416;color:#ffb37b}.itemrow{display:flex;gap:12px;align-items:flex-start}.thumb{width:72px;height:72px;object-fit:cover;border-radius:12px;background:#202630;flex-shrink:0}.itembody{min-width:0;flex:1}.itembody a{overflow-wrap:anywhere;color:#ff9b52}.empty{padding:28px 18px;text-align:center;color:var(--muted);background:#14181e;border:1px dashed #3a424e;border-radius:16px}.flash{padding:12px 14px;background:#123021;border:1px solid #226b45;color:#86efac;border-radius:12px;margin-bottom:14px}.tinyform{display:inline}.tinyform button{padding:8px 10px;font-size:12px;min-height:36px}.sectiontitle{font-size:16px;margin:22px 0 11px}.kit{white-space:pre-wrap;background:#101318;border:1px solid var(--line);padding:14px;border-radius:12px;font-size:14px;overflow-wrap:anywhere}
a{color:#ff9b52}p{line-height:1.55}footer{text-align:center;color:#788291;font-size:12px;padding:18px 16px 28px}
@media(min-width:700px){header{padding-left:max(18px,calc((100% - 1000px)/2));padding-right:max(18px,calc((100% - 1000px)/2))}nav{justify-content:center}.grid{grid-template-columns:repeat(auto-fit,minmax(170px,1fr))}main{padding-left:20px;padding-right:20px}}
@media(max-width:420px){main{padding:16px 10px 100px}.stat,.card,.formcard{padding:13px;border-radius:15px}.pagehead .btn{width:100%}.actions .btn,.actions button{flex:1 1 auto}}

/* REDESIGN PREMIUM COMPLETO — somente apresentação visual */
:root{color-scheme:dark;--bg:#080a0e;--card:#111720;--card2:#171f2a;--ink:#f4f7fb;--muted:#aab4c3;--line:#293443;--accent:#ff7417;--accent-soft:#3b2417}
*{box-sizing:border-box}
html{background:var(--bg)!important;scroll-behavior:smooth}
body{margin:0;background:radial-gradient(ellipse at 50% -14%,rgba(255,116,23,.17),transparent 43%),linear-gradient(180deg,#0c1118 0%,#080a0e 70%)!important;color:var(--ink)!important;font-family:Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;min-height:100vh}
header{position:relative;overflow:hidden;background:linear-gradient(115deg,#1a222d 0%,#10151d 72%)!important;border-bottom:1px solid rgba(255,116,23,.35)!important;padding:23px 16px 21px!important}
header:after{content:"";position:absolute;left:0;right:0;bottom:0;height:3px;background:linear-gradient(90deg,#ff7417,#ffb36b,transparent 85%)}
header .brand{font-size:clamp(22px,5vw,29px)!important;font-weight:900!important;letter-spacing:-.8px!important;color:#fff}
header p{color:#aeb9c8!important;font-size:13px;line-height:1.55}
nav{display:flex;gap:8px!important;overflow-x:auto;padding:12px!important;background:rgba(8,10,14,.96)!important;border-bottom:1px solid #28313d!important;position:sticky;top:0;z-index:20;scrollbar-width:thin;backdrop-filter:blur(14px);box-shadow:0 8px 24px rgba(0,0,0,.2)}
nav a{white-space:nowrap;text-decoration:none!important;color:#dbe3ed!important;background:#151c26!important;padding:11px 14px!important;border:1px solid #2c3746!important;border-radius:12px!important;font-size:13px;font-weight:750;transition:all .18s ease}
nav a:hover,nav a:focus{background:#302117!important;border-color:var(--accent)!important;color:#ffb47c!important;transform:translateY(-1px)}
main{max-width:1180px!important;margin:0 auto;padding:25px 16px 90px!important}
.pagehead{display:flex;align-items:center;justify-content:space-between;gap:13px;margin:4px 0 22px!important;flex-wrap:wrap}
.pagehead h1{font-size:clamp(25px,5.8vw,36px)!important;line-height:1.12;font-weight:900!important;letter-spacing:-1.1px!important;margin:0;color:#f8fafc}
.sub{color:var(--muted)!important;font-size:14px!important;line-height:1.6;margin-top:7px}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px!important}
.stat,.card,.formcard{position:relative;background:linear-gradient(145deg,#171f2a 0%,#10151d 100%)!important;border:1px solid #2d3948!important;border-radius:18px!important;padding:17px!important;margin-bottom:13px;box-shadow:0 12px 30px rgba(0,0,0,.2)!important;color:var(--ink)!important}
.stat{overflow:hidden}
.stat:before{content:"";display:block;width:42px;height:3px;background:var(--accent);border-radius:9px;margin:-17px 0 14px}
.stat small{color:var(--muted)!important;font-size:12px!important;line-height:1.5}
.stat strong{font-size:clamp(25px,5vw,32px)!important;display:block;margin-top:8px;color:#ff9a50!important;letter-spacing:-.8px;font-variant-numeric:tabular-nums}
.stat span{font-size:12px;color:var(--muted)!important}
.sectiontitle{font-size:19px!important;font-weight:850!important;color:#f6f8fb;margin:25px 0 12px!important}
.itemtitle{font-size:18px!important;font-weight:850!important;line-height:1.35;margin:0 0 7px!important;overflow-wrap:anywhere;color:#f6f8fb}
.muted{color:var(--muted)!important;font-size:13px;line-height:1.55}
.pill{display:inline-block;border-radius:999px;padding:5px 10px;font-size:11px;font-weight:800;background:#252f3c;color:#dce5ef}
.pill.orange{background:#3b2417;color:#ffb47c}
.itemrow{display:flex;gap:13px;align-items:flex-start}
.thumb{width:82px;height:82px;object-fit:contain;border-radius:13px;flex-shrink:0;background:#0c1118!important;border:1px solid #303b49}
.itembody{min-width:0;flex:1}
.itembody a{overflow-wrap:anywhere;color:#ffab6a!important}
.btn,button{border:1px solid transparent!important;background:linear-gradient(135deg,#ff8c3d,#f45e08)!important;color:#fff!important;padding:11px 15px!important;border-radius:12px!important;font-weight:850!important;font-size:14px;min-height:44px;display:inline-flex;align-items:center;justify-content:center;gap:7px;cursor:pointer;text-decoration:none!important;box-shadow:0 5px 14px rgba(244,94,8,.15);transition:filter .15s,transform .15s}
.btn:hover,button:hover{filter:brightness(1.08);transform:translateY(-1px)}
.btn.secondary,button.secondary{background:#202a37!important;color:#f1f5f9!important;border:1px solid #394657!important;box-shadow:none}
.btn.danger,button.danger{background:#7f1d1d!important;color:#fecaca!important}
.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:13px}
label{display:block;font-size:13px;font-weight:800;margin:15px 0 7px;color:#dce4ee!important}
input,select,textarea{font:inherit;font-size:16px;width:100%;border:1px solid #354151!important;border-radius:12px!important;padding:12px 13px;background:#0e151f!important;color:#f1f5f9!important;outline:none}
input:focus,select:focus,textarea:focus{border-color:var(--accent)!important;box-shadow:0 0 0 3px rgba(255,116,23,.15)!important}
input[type=file]{font-size:13px;padding:9px}
textarea{min-height:100px;resize:vertical}
.formgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:0 13px}
.empty{padding:30px 18px;text-align:center;color:var(--muted)!important;background:#121923!important;border:1px dashed #3b4858!important;border-radius:18px!important;line-height:1.65}
.flash{padding:13px 15px;background:#123021!important;border:1px solid #226b45!important;color:#9af0b7!important;border-radius:13px;margin-bottom:15px}
.kit{white-space:pre-wrap;background:#0b1017!important;border:1px solid #2b3745!important;padding:15px;border-radius:13px;font-size:14px;overflow-wrap:anywhere;color:#eaf0f7}
a{color:#ffab6a}
p{line-height:1.6}
table{width:100%;border-collapse:collapse}
table th,table td{border-color:#303b49!important;padding:10px;text-align:left}
footer{text-align:center;color:#8491a2!important;font-size:12px;padding:20px 16px 30px}
@media(min-width:760px){header{padding-left:max(20px,calc((100% - 1140px)/2))!important;padding-right:max(20px,calc((100% - 1140px)/2))!important}nav{justify-content:center}.grid{grid-template-columns:repeat(auto-fit,minmax(190px,1fr))}main{padding-left:22px!important;padding-right:22px!important}}
@media(max-width:520px){main{padding:19px 12px 84px!important}header{padding:21px 14px 19px!important}nav{justify-content:flex-start!important}nav a{padding:10px 12px!important;font-size:12px!important}.pagehead{align-items:stretch!important}.pagehead .btn{width:100%}.grid{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:9px!important}.stat{padding:13px!important}.stat:before{margin:-13px 0 12px}.stat strong{font-size:25px!important}.card,.formcard{padding:14px!important}.itemrow{gap:10px}.thumb{width:68px;height:68px}.actions{gap:7px!important}.actions .btn,.actions button{flex:1 1 auto}.formgrid{grid-template-columns:1fr}}

"""

LAYOUT = """
<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#0b0d10"><title>{{ title }} · Central Afiliado</title><style>""" + STYLE + """</style>
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

/* VISUAL PREMIUM V3 — hierarquia, navegação e cartões mobile */
:root {
  --bg: #090b0f;
  --panel: #141922;
  --panel2: #1c2430;
  --text: #f5f7fb;
  --muted: #a8b2c2;
  --accent: #ff7417;
  --border: #303947;
}
html { background: #090b0f !important; }
body {
  background:
    radial-gradient(ellipse at 50% -12%, rgba(255,116,23,.19), transparent 43%),
    linear-gradient(180deg, #0e1219 0%, #090b0f 65%) !important;
  color: var(--text) !important;
}
header {
  position: relative;
  overflow: hidden;
  background: linear-gradient(115deg, #1b222d 0%, #10141b 72%) !important;
  border-bottom: 1px solid rgba(255,116,23,.35) !important;
  padding-top: 24px !important;
  padding-bottom: 22px !important;
}
header:after {
  content: "";
  display: block;
  position: absolute;
  height: 3px;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, #ff7417, #ffb36b, transparent 85%);
  opacity: .8;
}
header .brand { font-size: clamp(22px, 5vw, 27px) !important; font-weight: 900 !important; letter-spacing: -.7px !important; }
header p { max-width: 620px; line-height: 1.5; }
nav {
  gap: 8px !important;
  padding: 12px 10px !important;
  background: rgba(8,10,14,.94) !important;
  border-bottom: 1px solid #272e39 !important;
  box-shadow: 0 8px 22px rgba(0,0,0,.18);
}
nav a {
  border-radius: 12px !important;
  padding: 11px 14px !important;
  background: #171d26 !important;
  border-color: #2d3643 !important;
  transition: background .15s ease, border-color .15s ease, transform .15s ease;
}
nav a:hover { background: #2b2019 !important; border-color: #ff7417 !important; transform: translateY(-1px); }
main { max-width: 980px !important; padding-top: 28px !important; }
.pagehead { align-items: center !important; margin: 4px 0 22px !important; }
.pagehead h1 { font-size: clamp(26px, 6vw, 35px) !important; font-weight: 900 !important; letter-spacing: -1.1px !important; line-height: 1.12 !important; }
.sub { color: #a8b2c2 !important; font-size: 14px !important; max-width: 650px; }
.grid { gap: 12px !important; }
.stat, .card, .formcard {
  background: linear-gradient(145deg, #171e28 0%, #11161e 100%) !important;
  border: 1px solid #303947 !important;
  border-radius: 18px !important;
  box-shadow: 0 12px 28px rgba(0,0,0,.22) !important;
  padding: 17px !important;
}
.stat { position: relative; overflow: hidden; }
.stat:before { content: ""; display: block; height: 2px; width: 42px; margin: -17px 0 14px; background: #ff7417; border-radius: 4px; }
.stat strong { color: #ff9a50 !important; font-variant-numeric: tabular-nums; }
.sectiontitle { font-size: 19px !important; font-weight: 850 !important; margin-top: 26px !important; }
.itemtitle { font-size: 18px !important; line-height: 1.32 !important; overflow-wrap: anywhere; }
.card .muted, .formcard .muted { line-height: 1.55; }
.thumb { background: #0e131b !important; border: 1px solid #303947; }
.btn, button, input[type="submit"] {
  min-height: 44px;
  border-radius: 12px !important;
  font-weight: 800 !important;
}
.btn:not(.secondary), button:not(.secondary), input[type="submit"] {
  background: linear-gradient(135deg, #ff8b36 0%, #f45b08 100%) !important;
  box-shadow: 0 5px 14px rgba(244,91,8,.16);
}
.btn.secondary, button.secondary {
  background: #202834 !important;
  border: 1px solid #364252 !important;
  color: #f1f5f9 !important;
}
input, select, textarea {
  border-radius: 12px !important;
  background: #101722 !important;
  border-color: #354050 !important;
}
input:focus, select:focus, textarea:focus {
  border-color: #ff7417 !important;
  box-shadow: 0 0 0 3px rgba(255,116,23,.16) !important;
}
.empty { background: #121821 !important; border-color: #414b5a !important; border-radius: 18px !important; }
.flash { border-radius: 13px !important; }
a { overflow-wrap: anywhere; }
footer { padding-bottom: 32px !important; color: #8793a4 !important; }
@media (max-width: 520px) {
  main { padding: 20px 12px 84px !important; }
  header { padding: 21px 14px 19px !important; }
  nav { justify-content: flex-start !important; }
  nav a { padding: 10px 12px !important; font-size: 12px !important; }
  .pagehead { align-items: stretch !important; }
  .pagehead .btn { width: 100%; }
  .grid { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; gap: 9px !important; }
  .stat { padding: 13px !important; }
  .stat:before { margin: -13px 0 12px; }
  .stat strong { font-size: 25px !important; }
  .card, .formcard { padding: 14px !important; }
  .actions { gap: 7px !important; }
  .actions .btn, .actions button { flex: 1 1 100%; }
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

LOGIN_USER = os.environ.get("CENTRAL_USERNAME", "1")
LOGIN_PASSWORD = os.environ.get("CENTRAL_PASSWORD", "1")
LOGIN_PAGE = """<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#0b0d10"><title>Entrar · Central de Afiliados</title><style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#0b0d10;color:#e5e7eb;font-family:system-ui,sans-serif;padding:18px;box-sizing:border-box}.box{width:100%;max-width:380px;background:#15181d;border:1px solid #303640;border-radius:20px;padding:24px;box-sizing:border-box}h1{font-size:24px;margin:0 0 6px}.muted{color:#9ca3af;font-size:13px;margin-bottom:20px}label{display:block;font-size:13px;margin:14px 0 6px}input{width:100%;box-sizing:border-box;padding:13px;border-radius:11px;border:1px solid #343c48;background:#1c222b;color:#fff;font-size:16px}button{width:100%;margin-top:18px;padding:13px;background:#ff6b00;color:#fff;border:0;border-radius:11px;font-size:15px;font-weight:800}.error{color:#fca5a5;font-size:13px}
body{background:radial-gradient(ellipse at 50% 0%,rgba(255,116,23,.2),transparent 42%),linear-gradient(180deg,#0c1118,#080a0e)!important;color:#f4f7fb!important;padding:18px!important}
.box{position:relative;width:100%;max-width:420px!important;background:linear-gradient(145deg,#19212c,#10151d)!important;border:1px solid #344151!important;border-radius:22px!important;padding:28px!important;box-shadow:0 24px 70px rgba(0,0,0,.45)!important}
.box:before{content:"";display:block;width:54px;height:4px;background:linear-gradient(90deg,#ff7417,#ffb36b);border-radius:9px;margin-bottom:20px}
h1{font-size:clamp(24px,6vw,30px)!important;line-height:1.2!important;font-weight:900!important;letter-spacing:-.8px!important;color:#fff!important}
.muted{color:#aab4c3!important;line-height:1.55!important}
label{color:#dce4ee!important;font-weight:800!important;margin:16px 0 7px!important}
input{background:#0e151f!important;color:#f1f5f9!important;border:1px solid #354151!important;border-radius:12px!important;padding:13px!important;min-height:48px}
input:focus{outline:none;border-color:#ff7417!important;box-shadow:0 0 0 3px rgba(255,116,23,.15)}
button{background:linear-gradient(135deg,#ff8c3d,#f45e08)!important;border-radius:12px!important;min-height:48px!important;font-weight:850!important;box-shadow:0 6px 18px rgba(244,94,8,.2)}
.error{background:#371b1c;border:1px solid #793136;border-radius:10px;padding:10px;color:#fecaca!important}
</style></head><body><form class="box" method="post"><h1>🛍️ Central de Afiliados</h1><div class="muted">Entre para continuar</div>{% if error %}<p class="error">{{ error }}</p>{% endif %}<label>Usuário</label><input name="username" autocomplete="username" required><label>Senha</label><input name="password" type="password" autocomplete="current-password" required><button type="submit">Entrar</button></form></body></html>"""

@app.before_request
def require_login():
    if request.endpoint in ("login", "static"):
        return None
    if not session.get("authenticated"):
        return redirect(url_for("login", next=request.path))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        if request.form.get("username", "") == LOGIN_USER and request.form.get("password", "") == LOGIN_PASSWORD:
            session.clear()
            session["authenticated"] = True
            return redirect(request.args.get("next") or url_for("index"))
        error = "Usuário ou senha incorretos."
    return render_template_string(LOGIN_PAGE, error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
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
  <label>Nome do produto *</label><input name="name" autocomplete="off" required value="{{ p['name'] if p else '' }}" placeholder="Ex.: Relógio esportivo">
  <div class="formgrid"><div><label>Categoria</label><input name="category" value="{{ p['category'] if p else '' }}" placeholder="Casa, beleza, tecnologia..."></div><div><label>Preço exibido (R$)</label><input name="price" value="{{ p['price'] if p else '' }}" placeholder="Ex.: 49,90"></div></div>
  <label>Link de afiliado (cole aqui o link da Shopee)</label><input name="affiliate_link" id="affiliate_link" type="url" autocomplete="url" inputmode="url" value="{{ p['affiliate_link'] if p else '' }}" placeholder="https://...">
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
