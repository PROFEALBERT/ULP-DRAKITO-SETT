from flask import Flask, request, redirect, session, send_file
import sqlite3
import random
import json
import os
import requests
from fpdf import FPDF
from io import BytesIO
import base64

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ulp_drakito_sett_2026_secret")
DB_PATH = os.environ.get("DB_PATH", "/tmp/sistema.db")
LOGO_URL = "https://i.postimg.cc/x8KdvtPQ/IMG-20260411-020447-078.jpg"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT UNIQUE NOT NULL,
        pass TEXT NOT NULL,
        rol TEXT NOT NULL DEFAULT 'user',
        creditos INTEGER NOT NULL DEFAULT 0,
        creado_por TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id_pedido INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT NOT NULL,
        referencia TEXT,
        tipo TEXT NOT NULL DEFAULT 'intelx',
        estado TEXT NOT NULL DEFAULT 'PENDIENTE',
        respuesta TEXT,
        detalle TEXT,
        codigo TEXT,
        operador TEXT,
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Super admin 1
    cur.execute("SELECT user FROM usuarios WHERE user=?", ("jhorny",))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO usuarios (user, pass, rol, creditos, creado_por)
            VALUES (?, ?, ?, ?, ?)
        """, ("jhorny", "123456", "admin", 999999, "system"))

    # Super admin 2
    cur.execute("SELECT user FROM usuarios WHERE user=?", ("DRAKITO_VIP7020",))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO usuarios (user, pass, rol, creditos, creado_por)
            VALUES (?, ?, ?, ?, ?)
        """, ("DRAKITO_VIP7020", "860055", "admin", 999999, "system"))

    conn.commit()
    conn.close()


def require_login():
    return "user" in session


def is_super_admin():
    return session.get("user") in ["jhorny", "DRAKITO_VIP7020"]


def can_use_client_features():
    return session.get("rol") in ["user", "admin"] or is_super_admin()


def logo_html(size_class: str, extra_class: str = ""):
    return f"""
    <div class="{size_class} rounded-full overflow-hidden border-[2px] border-[#0ea5e9] bg-[#030712] flex items-center justify-center shadow-[0_0_25px_rgba(14,165,233,0.4)] animate-float {extra_class}">
        <img src="{LOGO_URL}" class="w-full h-full object-cover rounded-full scale-125 hover:scale-150 transition-transform duration-500" alt="logo">
    </div>
    """


def layout(content, show_nav=False, login_bg=False):
    u = session.get("user")
    r = session.get("rol")

    is_boss = is_super_admin()
    is_admin = (r == "admin")
    is_client_side = can_use_client_features()

    nav = ""
    if show_nav:
        nav = f"""
        <div class="w-full rounded-[24px] overflow-hidden mb-8 relative z-40 bg-white/5 backdrop-blur-xl border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
            <div class="flex items-center justify-between px-5 py-4">
                <div class="flex items-center gap-4">
                    {logo_html("w-12 h-12")}
                    <div class="flex flex-col">
                        <span class="text-[18px] font-black tracking-widest bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 bg-clip-text text-transparent uppercase">
                            ULP DRAKITO SETT
                        </span>
                    </div>
                </div>

                <button onclick="toggleMenu()" class="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-cyan-400 shadow-lg hover:bg-white/10 transition-all">
                    <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16m-8 6h8"></path>
                    </svg>
                </button>
            </div>
        </div>

        <div id="sidebar" class="fixed top-0 right-0 h-full w-72 bg-[#030712]/95 backdrop-blur-3xl border-l border-white/10 transform translate-x-full transition-transform duration-400 ease-out z-50 p-6 shadow-2xl overflow-y-auto">
            <div class="flex justify-between items-center mb-12">
                <span class="text-[11px] font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500 uppercase tracking-[0.3em]">MENÚ PRINCIPAL</span>
                <button onclick="toggleMenu()" class="text-gray-400 hover:text-white text-3xl transition-colors">&times;</button>
            </div>

            <div class="flex flex-col gap-6">
                <a href="/" class="menu-link text-sm font-bold uppercase text-gray-300 hover:text-cyan-400 flex items-center gap-3 transition-colors">
                    <span class="text-xl">🏠</span> INICIO
                </a>

                {"<a href='/panel_admin' class='menu-link text-sm font-bold uppercase text-gray-300 hover:text-cyan-400 flex items-center gap-3 transition-colors'><span class='text-xl'>💎</span> PANEL ADMIN</a>" if is_boss or is_admin else ""}

                <a href="/planes" class="menu-link text-sm font-bold uppercase text-gray-300 hover:text-cyan-400 flex items-center gap-3 transition-colors">
                    <span class="text-xl">🛒</span> COMPRAR CRÉDITOS
                </a>

                {"<a href='/intelx' class='menu-link text-sm font-bold uppercase text-gray-300 hover:text-cyan-400 flex items-center gap-3 transition-colors'><span class='text-xl'>🔍</span> INTELX</a>" if is_client_side else ""}

                {"<a href='/llamadas_spam' class='menu-link text-sm font-bold uppercase text-gray-300 hover:text-cyan-400 flex items-center gap-3 transition-colors'><span class='text-xl'>📞</span> LLAMADAS SPAM</a>" if is_client_side else ""}

                <a href="/soporte" class="menu-link text-sm font-bold uppercase text-gray-300 hover:text-cyan-400 flex items-center gap-3 transition-colors">
                    <span class="text-xl">🎧</span> SOPORTE
                </a>

                <hr class="border-white/10 my-4">

                <a href="/logout" class="menu-link text-sm font-bold uppercase text-red-500 hover:text-red-400 flex items-center gap-3 transition-colors">
                    <span class="text-xl">🚪</span> SALIR
                </a>
            </div>
        </div>

        <div id="overlay" onclick="toggleMenu()" class="fixed inset-0 bg-black/60 backdrop-blur-sm hidden z-40 transition-opacity"></div>
        """

    modal_script = """
    <script>
        function toggleMenu() {
            document.getElementById('sidebar')?.classList.toggle('translate-x-full');
            document.getElementById('overlay')?.classList.toggle('hidden');
        }

        function showReport(tipo, referencia, respuesta, detalle, codigo, operador) {
            document.getElementById('rep_tipo').innerText = tipo || '';
            document.getElementById('rep_ref').innerText = referencia || '';

            if(respuesta) {
                document.getElementById('rep_respuesta').innerHTML = "✅ " + respuesta + " ✅";
            } else {
                document.getElementById('rep_respuesta').innerHTML = "";
            }

            document.getElementById('rep_detalle').innerText = detalle || '';
            document.getElementById('rep_codigo').innerText = codigo || '';
            document.getElementById('rep_operador').innerText = operador || '';
            document.getElementById('modalReport').classList.remove('hidden');
        }

        function closeReport() {
            document.getElementById('modalReport').classList.add('hidden');
        }

        function copyText(texto) {
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(texto).then(() => {
                    alert('Copiado correctamente');
                }).catch(() => {
                    fallbackCopy(texto);
                });
            } else {
                fallbackCopy(texto);
            }
        }

        function fallbackCopy(texto) {
            const area = document.createElement('textarea');
            area.value = texto;
            area.style.position = 'fixed';
            area.style.left = '-9999px';
            area.style.top = '0';
            document.body.appendChild(area);
            area.focus();
            area.select();
            try {
                document.execCommand('copy');
                alert('Copiado correctamente');
            } catch (err) {
                alert('No se pudo copiar automáticamente');
            }
            document.body.removeChild(area);
        }

        function copyReport() {
            const texto =
`TIPO: ${document.getElementById('rep_tipo').innerText}

REFERENCIA: ${document.getElementById('rep_ref').innerText}

RESPUESTA:
${document.getElementById('rep_respuesta').innerText}

DETALLE:
${document.getElementById('rep_detalle').innerText}`;

            copyText(texto);
        }
    </script>
    """

    modal_html = f"""
    <div id="modalReport" class="hidden fixed inset-0 bg-black/80 backdrop-blur-md z-[60] flex items-center justify-center p-4">
        <div class="bg-[#0b1120] border border-cyan-500/30 w-full max-w-sm rounded-[32px] p-8 shadow-[0_0_40px_rgba(6,182,212,0.15)] relative transform transition-all">
            <button onclick="closeReport()" class="absolute top-5 right-6 text-gray-500 font-bold text-2xl hover:text-white transition">&times;</button>

            <div class="text-center mb-8">
                {logo_html("w-20 h-20", "mx-auto mb-4 shadow-[0_0_20px_rgba(14,165,233,0.3)]")}
                <h3 class="text-white font-black uppercase tracking-[0.2em] text-sm">REPORTE DE SISTEMA</h3>
                <p class="text-[9px] text-cyan-500 uppercase tracking-widest mt-1 font-bold">ULP Drakito Sett</p>
            </div>

            <div class="space-y-5 text-xs font-mono text-gray-300 bg-white/5 p-5 rounded-2xl border border-white/5">
                <div class="flex justify-between gap-3 border-b border-white/10 pb-2">
                    <span class="text-gray-500">TIPO:</span>
                    <span id="rep_tipo" class="text-cyan-400 font-bold uppercase"></span>
                </div>

                <div class="flex justify-between gap-3 border-b border-white/10 pb-2">
                    <span class="text-gray-500">REF:</span>
                    <span id="rep_ref" class="text-white font-bold uppercase truncate max-w-[150px]"></span>
                </div>

                <div class="border-b border-white/10 pb-3">
                    <p class="text-gray-500 mb-2">ESTADO:</p>
                    <p id="rep_respuesta" class="text-emerald-400 font-bold whitespace-pre-line"></p>
                </div>

                <div class="pt-1">
                    <p class="text-gray-500 mb-2">DATA EXTRAÍDA:</p>
                    <div id="rep_detalle" class="text-gray-200 font-medium whitespace-pre-wrap leading-relaxed max-h-40 overflow-y-auto custom-scrollbar"></div>
                </div>

                <div class="hidden">
                    <span id="rep_codigo"></span>
                    <span id="rep_operador"></span>
                </div>
            </div>

            <div class="grid grid-cols-2 gap-4 mt-8">
                <button onclick="copyReport()" class="bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-2xl py-3.5 text-[11px] uppercase font-bold tracking-widest shadow-lg hover:shadow-emerald-500/25 transition-all">
                    COPIAR
                </button>
                <button onclick="closeReport()" class="bg-white/5 border border-white/10 text-white rounded-2xl py-3.5 text-[11px] uppercase font-bold tracking-widest hover:bg-white/10 transition-all">
                    CERRAR
                </button>
            </div>
        </div>
    </div>
    """

    login_background_html = ""
    if login_bg:
        login_background_html = f"""
        <div class="login-bg"></div>
        <div class="login-overlay"></div>
        """

    styles = """
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800;900&display=swap" rel="stylesheet">
    <style>
        body {
            background-color: #030712;
            color: #f8fafc;
            font-family: 'Outfit', sans-serif;
            touch-action: manipulation;
            overflow-x: hidden;
            min-height: 100vh;
        }

        .animate-float {
            animation: floating 3s ease-in-out infinite alternate;
        }

        @keyframes floating {
            0% { transform: translateY(0px); box-shadow: 0 0 15px rgba(14,165,233,0.3); }
            100% { transform: translateY(-5px); box-shadow: 0 0 30px rgba(14,165,233,0.6); }
        }

        .neon-card {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(56, 189, 248, 0.15);
            border-radius: 28px;
            box-shadow: 0 10px 40px -10px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.05);
        }

        .input-dark {
            background: rgba(3, 7, 18, 0.5);
            border: 1px solid rgba(51, 65, 85, 0.6);
            border-radius: 16px;
            padding: 16px;
            width: 100%;
            outline: none;
            color: white;
            font-size: 15px;
            transition: all 0.3s ease;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
        }

        .input-dark:focus {
            border-color: rgba(14, 165, 233, 0.8);
            box-shadow: 0 0 15px rgba(14,165,233,0.15), inset 0 2px 4px rgba(0,0,0,0.2);
        }

        .input-dark::placeholder {
            color: #475569;
            font-weight: 400;
        }

        .custom-scrollbar::-webkit-scrollbar {
            width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
            background: rgba(0,0,0,0.2); 
            border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(56, 189, 248, 0.5); 
            border-radius: 10px;
        }

        .login-bg {
            position: fixed;
            inset: 0;
            background-image: url('https://i.postimg.cc/x8KdvtPQ/IMG-20260411-020447-078.jpg');
            background-size: cover;
            background-position: center;
            transform: scale(1.05);
            animation: bgmove 25s ease-in-out infinite alternate;
            z-index: 0;
            filter: brightness(0.2) saturate(1.1) blur(4px);
        }

        .login-overlay {
            position: fixed;
            inset: 0;
            background: radial-gradient(circle at center, rgba(14,165,233,0.08), #030712 90%);
            z-index: 1;
        }

        @keyframes bgmove {
            0% { transform: scale(1.05) translate(0px, 0px); }
            100% { transform: scale(1.15) translate(-20px, -15px); }
        }

        .content-wrap {
            position: relative;
            z-index: 2;
            width: 100%;
            max-width: 28rem;
            margin: 0 auto;
        }
    </style>
    """

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <script src="https://cdn.tailwindcss.com"></script>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    {styles}
    {modal_script}
</head>
<body class="p-4 flex flex-col items-center">
    {login_background_html}
    <div class="content-wrap">
        {nav}
        {content}
    </div>
    {modal_html if not login_bg else ""}
</body>
</html>"""


@app.route("/")
def index():
    if not require_login():
        return redirect("/login")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT creditos FROM usuarios WHERE user=?", (session["user"],))
    row = cur.fetchone()
    restantes = row["creditos"] if row else 0

    cur.execute("SELECT COUNT(*) AS total FROM pedidos WHERE cliente=? AND estado='EXITOSO'", (session["user"],))
    usados = cur.fetchone()["total"]

    cur.execute("""
        SELECT referencia, estado, tipo, respuesta, detalle, codigo, operador
        FROM pedidos
        WHERE cliente=?
        ORDER BY id_pedido DESC
        LIMIT 10
    """, (session["user"],))
    peds = cur.fetchall()
    conn.close()

    historial = ""
    for p in peds:
        # Calcular creditos descontados segun el tipo de pedido
        costo_descontado = 1 if p["tipo"] == "intelx" else (2 if p["tipo"] == "llamadas_spam" else 0)

        if p["estado"] == "EXITOSO":
            args = ",".join([
                json.dumps((p["tipo"] or "").upper()),
                json.dumps(p["referencia"] or ""),
                json.dumps(p["respuesta"] or ""),
                json.dumps(p["detalle"] or ""),
                json.dumps(p["codigo"] or ""),
                json.dumps(p["operador"] or "")
            ])
            btn = f"""
            <button onclick='showReport({args})'
                class="bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-xl px-4 py-2 text-[9px] font-black uppercase tracking-widest hover:bg-cyan-500/20 hover:scale-105 transition-all">
                REPORTE
            </button>
            """
        else:
            btn = '<span class="text-[9px] bg-red-500/10 border border-red-500/20 px-3 py-1.5 rounded-lg text-[#ef4444] font-black tracking-widest uppercase">ERROR</span>'

        historial += f"""
        <div class="flex justify-between items-center border-b border-white/5 py-4 gap-4 hover:bg-white/[0.02] transition-colors rounded-xl px-2">
            <div class="flex flex-col">
                <span class="text-[13px] font-bold text-white tracking-wide truncate max-w-[160px]">Consulta: {p["referencia"] or "SOLICITUD"}</span>
                <span class="text-[9px] text-blue-400 uppercase mt-1 font-bold tracking-widest">{(p["tipo"] or "").replace('_', ' ')} • -{costo_descontado} CRÉDITOS</span>
            </div>
            {btn}
        </div>
        """

    content = f"""
    <div class="flex flex-col items-center mb-10 mt-4">
        {logo_html("w-24 h-24", "mb-5")}
        <h1 class="text-4xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 via-blue-400 to-purple-400 text-center leading-tight">
            ULP DRAKITO<br>SETT
        </h1>
    </div>

    <div class="grid grid-cols-2 gap-4 mb-8">
        <div class="bg-gradient-to-br from-[#08101a] to-[#040914] rounded-[24px] p-6 text-center border border-blue-500/20 shadow-[0_10px_30px_rgba(59,130,246,0.1)] relative overflow-hidden">
            <div class="absolute top-0 right-0 w-16 h-16 bg-blue-500/10 rounded-full blur-xl -mr-8 -mt-8"></div>
            <p class="text-[10px] text-blue-400 uppercase font-bold tracking-[0.2em] mb-2">USADOS</p>
            <h2 class="text-5xl font-black text-white">{usados}</h2>
        </div>
        <div class="bg-gradient-to-br from-[#08101a] to-[#040914] rounded-[24px] p-6 text-center border border-emerald-500/20 shadow-[0_10px_30px_rgba(16,185,129,0.1)] relative overflow-hidden">
            <div class="absolute top-0 right-0 w-16 h-16 bg-emerald-500/10 rounded-full blur-xl -mr-8 -mt-8"></div>
            <p class="text-[10px] text-emerald-400 uppercase font-bold tracking-[0.2em] mb-2">RESTANTES</p>
            <h2 class="text-5xl font-black text-white">{restantes}</h2>
        </div>
    </div>

    <div class="neon-card p-7 mb-8">
        <h3 class="text-[11px] font-black text-transparent bg-clip-text bg-gradient-to-r from-gray-200 to-gray-500 uppercase tracking-[0.3em] mb-6 text-center">HISTORIAL RECIENTE</h3>
        <div class="space-y-1">
            {historial or "<p class='text-center text-gray-500 text-xs py-6 font-medium'>Aún no hay registros de pedidos.</p>"}
        </div>
    </div>

    <div class="neon-card p-8 relative overflow-hidden mb-6">
        <h3 class="text-[12px] font-black text-cyan-400 uppercase text-center mb-8 tracking-[0.3em]">MÓDULOS DEL SISTEMA</h3>

        <div class="space-y-8">
            <div class="flex gap-4 items-start">
                <div class="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center flex-shrink-0">
                    <span class="text-xl">🔍</span>
                </div>
                <div>
                    <h4 class="text-white font-bold text-sm mb-1 tracking-wide">IntelX Tracker</h4>
                    <p class="text-gray-400 text-xs leading-relaxed mb-2">Búsqueda profunda automatizada. Extrae data vinculada a correos, DNI o dominios al instante.</p>
                    <span class="bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 text-[9px] font-bold px-2 py-1 rounded-md uppercase tracking-widest">1 CRÉDITO</span>
                </div>
            </div>

            <div class="flex gap-4 items-start">
                <div class="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center flex-shrink-0">
                    <span class="text-xl">📞</span>
                </div>
                <div>
                    <h4 class="text-white font-bold text-sm mb-1 tracking-wide">Call Bomber (Spam)</h4>
                    <p class="text-gray-400 text-xs leading-relaxed mb-2">Ataque de llamadas masivas para saturar líneas telefónicas automáticamente vía API. 3 niveles de potencia.</p>
                    <span class="bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 text-[9px] font-bold px-2 py-1 rounded-md uppercase tracking-widest">2 CRÉDITOS</span>
                </div>
            </div>
        </div>
    </div>
    """
    return layout(content, True)


@app.route("/planes")
def planes():
    if not require_login():
        return redirect("/login")

    precios = [
        ("10 CRÉDITO", "S/15.00"),
        ("40 CRÉDITOS", "S/60.00"),
        ("60 CRÉDITOS", "S/90.00"),
        ("100 CRÉDITOS", "S/150.00"),
        ("120 CRÉDITOS", "S/120.00"),
        ("180 CRÉDITOS", "S/200.00"),
    ]

    cards = ""
    for nombre, precio in precios:
        cards += f"""
        <div class="p-6 mb-4 rounded-[24px] border border-purple-500/20 bg-white/[0.02] flex justify-between items-center shadow-lg hover:border-purple-500/50 hover:bg-white/[0.04] transition-all group">
            <div>
                <h3 class="text-white font-black text-xl tracking-tight mb-1">{nombre}</h3>
                <p class="text-purple-400 text-sm font-mono font-bold">{precio}</p>
            </div>
            <a href="https://t.me/DRAKITO_VIP" target="_blank"
               class="bg-gradient-to-r from-purple-600 to-pink-500 px-6 py-3.5 rounded-xl text-[10px] font-black uppercase tracking-widest text-white shadow-[0_0_20px_rgba(168,85,247,0.3)] group-hover:scale-105 transition-transform">
               OBTENER
            </a>
        </div>
        """

    content = f"""
    <div class="mt-8 mb-10 text-center">
        <h2 class="text-[11px] text-cyan-400 font-black uppercase tracking-[0.4em] mb-2">STORE</h2>
        <h1 class="text-3xl font-black text-white">Planes Oficiales</h1>
    </div>
    <div class="space-y-4">
        {cards}
    </div>
    """
    return layout(content, True)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("cap") == str(session.get("captcha_val")):
            u = request.form.get("u", "").strip()
            p = request.form.get("p", "").strip()

            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT rol FROM usuarios WHERE user=? AND pass=?", (u, p))
            res = cur.fetchone()
            conn.close()

            if res:
                session["user"] = u
                session["rol"] = res["rol"]
                return redirect("/")

    session["captcha_val"] = random.randint(100000, 999999)

    content = f"""
    <div class="flex flex-col items-center mt-12 w-full">
        {logo_html("w-32 h-32", "mb-8 shadow-[0_0_40px_rgba(14,165,233,0.5)]")}

        <h1 class="text-5xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 via-blue-400 to-purple-400 text-center leading-[1.1] mb-2">
            ULP DRAKITO<br>SETT
        </h1>
        <p class="text-[11px] uppercase tracking-[0.5em] text-blue-500 mb-10 font-black">
            System Access
        </p>

        <form method="post" class="w-full space-y-5 bg-[#030712]/60 border border-white/10 rounded-[32px] p-8 shadow-2xl backdrop-blur-2xl">
            <input name="u" placeholder="Usuario de acceso" class="input-dark" autocomplete="off" required>
            <input name="p" type="password" placeholder="Clave secreta" class="input-dark" required>

            <div class="flex gap-4 pt-2 items-center">
                <div class="bg-white/10 border border-white/10 text-cyan-400 rounded-2xl flex items-center justify-center font-black w-1/2 h-[54px] text-2xl tracking-[0.2em] shadow-inner">
                    {session['captcha_val']}
                </div>
                <input name="cap" placeholder="Captcha" class="input-dark w-1/2 text-center !text-lg" autocomplete="off" required>
            </div>

            <button class="w-full bg-gradient-to-r from-cyan-500 to-blue-600 p-4 rounded-2xl font-black text-xs uppercase tracking-[0.2em] text-white shadow-[0_10px_20px_rgba(14,165,233,0.3)] mt-6 hover:scale-[1.02] transition-transform">
                INGRESAR AL PANEL
            </button>
        </form>

        <a href="https://t.me/DRAKITO_VIP" target="_blank"
           class="mt-10 text-gray-500 hover:text-cyan-400 text-[10px] font-bold uppercase tracking-widest flex items-center justify-center gap-2 transition-colors w-full">
           <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.223-.548.223l.188-2.85 5.18-4.686c.223-.195-.054-.304-.346-.11l-6.4 4.02-2.76-.86c-.6-.188-.612-.6.126-.89l10.81-4.17c.5-.188.94.116.805.903z"/></svg>
           CONTACTAR AL DESARROLLADOR
        </a>
    </div>
    """
    return layout(content, False, True)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/panel_admin", methods=["GET", "POST"])
def panel_admin():
    if not require_login():
        return redirect("/login")

    u_log = session.get("user")
    r_log = session.get("rol")

    if not is_super_admin() and r_log != "admin":
        return redirect("/")

    conn = get_conn()
    cur = conn.cursor()

    if request.method == "POST":
        action = request.form.get("action", "")

        if action == "crear":
            rol_a_crear = request.form.get("r", "user")
            try:
                nuevo_user = request.form["u"]
                nuevo_pass = request.form["p"]

                cur.execute("""
                    INSERT INTO usuarios (user, pass, rol, creditos, creado_por)
                    VALUES (?, ?, ?, 0, ?)
                """, (nuevo_user, nuevo_pass, rol_a_crear, u_log))
                conn.commit()

                session["last_user_created"] = {
                    "user": nuevo_user,
                    "pass": nuevo_pass,
                    "rol": rol_a_crear,
                    "url": request.host_url + "login"
                }
            except sqlite3.IntegrityError:
                pass

        elif action == "creditos":
            target = request.form["target"]
            cant = int(request.form["cant"])

            cur.execute("SELECT creditos FROM usuarios WHERE user=?", (u_log,))
            admin_row = cur.fetchone()
            saldo_admin = admin_row["creditos"] if admin_row else 0

            if is_super_admin() or saldo_admin >= cant:
                cur.execute("UPDATE usuarios SET creditos = creditos + ? WHERE user=?", (cant, target))
                if not is_super_admin():
                    cur.execute("UPDATE usuarios SET creditos = creditos - ? WHERE user=?", (cant, u_log))
                conn.commit()

        elif action == "quitar_creditos":
            target = request.form["target"]
            cant = int(request.form["cant"])

            cur.execute("SELECT creditos FROM usuarios WHERE user=?", (target,))
            target_row = cur.fetchone()

            if target_row:
                quitar_real = min(cant, target_row["creditos"])
                if quitar_real > 0:
                    cur.execute("UPDATE usuarios SET creditos = creditos - ? WHERE user=?", (quitar_real, target))
                    if not is_super_admin():
                        cur.execute("UPDATE usuarios SET creditos = creditos + ? WHERE user=?", (quitar_real, u_log))
                    conn.commit()

        elif action == "sumar_rapido":
            target = request.form["target"]
            cant = int(request.form["cant"])

            cur.execute("SELECT creditos FROM usuarios WHERE user=?", (u_log,))
            admin_row = cur.fetchone()
            saldo_admin = admin_row["creditos"] if admin_row else 0

            cur.execute("SELECT creditos FROM usuarios WHERE user=?", (target,))
            target_row = cur.fetchone()

            if target_row:
                saldo_target = target_row["creditos"]

                if cant > 0:
                    if is_super_admin() or saldo_admin >= cant:
                        cur.execute("UPDATE usuarios SET creditos = creditos + ? WHERE user=?", (cant, target))
                        if not is_super_admin():
                            cur.execute("UPDATE usuarios SET creditos = creditos - ? WHERE user=?", (cant, u_log))
                        conn.commit()
                else:
                    quitar = abs(cant)
                    quitar_real = min(quitar, saldo_target)
                    if quitar_real > 0:
                        cur.execute("UPDATE usuarios SET creditos = creditos - ? WHERE user=?", (quitar_real, target))
                        if not is_super_admin():
                            cur.execute("UPDATE usuarios SET creditos = creditos + ? WHERE user=?", (quitar_real, u_log))
                        conn.commit()

        elif action == "eliminar_usuario":
            target = request.form.get("target")
            if target not in ["jhorny", "DRAKITO_VIP7020"]:
                if is_super_admin():
                    cur.execute("DELETE FROM usuarios WHERE user=?", (target,))
                else:
                    cur.execute("DELETE FROM usuarios WHERE user=? AND creado_por=?", (target, u_log))
                conn.commit()

    if is_super_admin():
        cur.execute("SELECT user, creditos, rol FROM usuarios ORDER BY id DESC")
    else:
        cur.execute("SELECT user, creditos, rol FROM usuarios WHERE creado_por=? ORDER BY id DESC", (u_log,))

    users = cur.fetchall()
    conn.close()

    nuevo_creado = session.get("last_user_created")
    bloque_nuevo = ""

    if nuevo_creado:
        texto_copiar = f"URL: {nuevo_creado['url']}\\nUSUARIO: {nuevo_creado['user']}\\nCLAVE: {nuevo_creado['pass']}\\nROL: {nuevo_creado['rol']}"
        bloque_nuevo = f'''
        <div class="bg-emerald-500/10 border border-emerald-500/30 rounded-[24px] p-6 mb-8 shadow-[0_0_20px_rgba(16,185,129,0.1)]">
            <p class="text-[10px] uppercase text-emerald-400 font-black mb-5 tracking-widest flex items-center gap-2">
                <span class="text-base">✅</span> Acceso Generado Exitosamente
            </p>
            <div class="space-y-3 text-xs text-gray-300 font-mono bg-black/40 p-5 rounded-2xl border border-white/5">
                <p><span class="text-cyan-500 font-bold">URL:</span> {nuevo_creado["url"]}</p>
                <p><span class="text-cyan-500 font-bold">USER:</span> {nuevo_creado["user"]}</p>
                <p><span class="text-cyan-500 font-bold">PASS:</span> {nuevo_creado["pass"]}</p>
                <p><span class="text-cyan-500 font-bold">ROL:</span> {nuevo_creado["rol"]}</p>
            </div>
            <button onclick="copyText(`{texto_copiar}`)" class="w-full mt-5 bg-emerald-500 hover:bg-emerald-400 text-white rounded-xl py-3.5 text-[10px] uppercase font-black tracking-widest transition shadow-lg">
                Copiar Info
            </button>
        </div>
        '''
        session.pop("last_user_created", None)

    lista = ""
    for u in users:
        btn_eliminar = ""
        if u["user"] not in ["jhorny", "DRAKITO_VIP7020"]:
            btn_eliminar = f"""
            <form method="POST" onsubmit="return confirm('¿Seguro que deseas eliminar a {u['user']}?');" class="mt-5">
                <input type="hidden" name="action" value="eliminar_usuario">
                <input type="hidden" name="target" value="{u['user']}">
                <button class="w-full bg-red-500/10 text-red-400 border border-red-500/20 rounded-xl py-3 text-[10px] font-black uppercase tracking-widest hover:bg-red-500/20 transition-colors">
                    Remover Cliente
                </button>
            </form>
            """

        lista += f"""
        <div class="p-6 bg-white/[0.02] rounded-[24px] border border-white/10 mb-4 shadow-sm hover:border-white/20 transition-colors">
            <div class="flex justify-between items-center mb-5">
                <div>
                    <span class="text-white font-black text-lg">{u["user"]}</span>
                    <span class="text-gray-500 text-[10px] ml-2 uppercase tracking-widest font-bold">({u["rol"]})</span>
                </div>
                <span class="text-cyan-400 font-black text-xl">{u["creditos"]} <span class="text-sm text-cyan-500/50">Cr.</span></span>
            </div>

            <div class="grid grid-cols-3 gap-3 mb-3">
                <form method="POST">
                    <input type="hidden" name="action" value="sumar_rapido">
                    <input type="hidden" name="target" value="{u["user"]}">
                    <input type="hidden" name="cant" value="1">
                    <button class="w-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-xl py-3 text-xs font-black hover:bg-cyan-500/20 transition">+1</button>
                </form>
                <form method="POST">
                    <input type="hidden" name="action" value="sumar_rapido">
                    <input type="hidden" name="target" value="{u["user"]}">
                    <input type="hidden" name="cant" value="5">
                    <button class="w-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-xl py-3 text-xs font-black hover:bg-cyan-500/20 transition">+5</button>
                </form>
                <form method="POST">
                    <input type="hidden" name="action" value="sumar_rapido">
                    <input type="hidden" name="target" value="{u["user"]}">
                    <input type="hidden" name="cant" value="10">
                    <button class="w-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-xl py-3 text-xs font-black hover:bg-cyan-500/20 transition">+10</button>
                </form>
            </div>

            <div class="grid grid-cols-3 gap-3">
                <form method="POST">
                    <input type="hidden" name="action" value="sumar_rapido">
                    <input type="hidden" name="target" value="{u["user"]}">
                    <input type="hidden" name="cant" value="-1">
                    <button class="w-full bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-xl py-3 text-xs font-black hover:bg-rose-500/20 transition">-1</button>
                </form>
                <form method="POST">
                    <input type="hidden" name="action" value="sumar_rapido">
                    <input type="hidden" name="target" value="{u["user"]}">
                    <input type="hidden" name="cant" value="-5">
                    <button class="w-full bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-xl py-3 text-xs font-black hover:bg-rose-500/20 transition">-5</button>
                </form>
                <form method="POST">
                    <input type="hidden" name="action" value="sumar_rapido">
                    <input type="hidden" name="target" value="{u["user"]}">
                    <input type="hidden" name="cant" value="-10">
                    <button class="w-full bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-xl py-3 text-xs font-black hover:bg-rose-500/20 transition">-10</button>
                </form>
            </div>
            {btn_eliminar}
        </div>
        """

    content = f"""
    {bloque_nuevo}
    <div class="neon-card p-8 mt-4 mb-6">
        <h2 class="text-[12px] text-cyan-400 font-black uppercase text-center mb-8 tracking-[0.3em]">
            Panel Maestro
        </h2>

        <form method="POST" class="space-y-4 mb-10 border-b border-white/10 pb-10">
            <input type="hidden" name="action" value="crear">
            <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest ml-1 mb-2">Crear Nuevo Acceso</p>
            <input name="u" placeholder="Usuario" class="input-dark" required>
            <input name="p" placeholder="Contraseña" class="input-dark" required>
            <select name="r" class="input-dark appearance-none font-medium">
                <option value="user">Rol: Cliente</option>
                {"<option value='admin'>Rol: Admin Secundario</option>" if is_super_admin() else ""}
            </select>
            <button class="w-full bg-gradient-to-r from-blue-500 to-cyan-500 p-4 rounded-xl font-black text-[11px] uppercase tracking-[0.2em] text-white shadow-lg mt-4 hover:scale-[1.02] transition-transform">
                Registrar
            </button>
        </form>

        <form method="POST" class="space-y-4 mb-10 border-b border-white/10 pb-10">
            <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest ml-1 mb-2">Modificar Saldo Manual</p>
            <input name="target" placeholder="Usuario Destino" class="input-dark" required>
            <input name="cant" type="number" min="1" placeholder="Cantidad de Créditos" class="input-dark" required>

            <div class="grid grid-cols-2 gap-4 mt-4">
                <button type="submit" name="action" value="creditos" class="w-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 p-4 rounded-xl font-black text-[10px] uppercase tracking-[0.2em] shadow-lg hover:bg-emerald-500/30 transition">
                    Inyectar
                </button>
                <button type="submit" name="action" value="quitar_creditos" class="w-full bg-rose-500/20 border border-rose-500/40 text-rose-400 p-4 rounded-xl font-black text-[10px] uppercase tracking-[0.2em] shadow-lg hover:bg-rose-500/30 transition">
                    Restar
                </button>
            </div>
        </form>

        <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest ml-1 mb-5">Directorio de Usuarios</p>

        <div class="max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
            {lista or "<p class='text-center text-gray-500 text-sm py-8 font-medium'>No hay usuarios registrados</p>"}
        </div>
    </div>
    """
    return layout(content, True)


@app.route("/intelx", methods=["GET", "POST"])
def intelx():
    if not require_login() or not can_use_client_features():
        return redirect("/")

    msg = ""
    if request.method == "POST":
        cliente = session.get("user")
        referencia = request.form.get("dato", "").strip()
        costo = 1

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT creditos FROM usuarios WHERE user=?", (cliente,))
        row = cur.fetchone()

        if row and row["creditos"] >= costo:
            api_url = "http://38.250.116.172/api/intelx"
            params = {
                "auth": "9ntEzxnOMYzpJuIEDJ0Qgh",
                "url": referencia
            }
            
            try:
                # Timeout de 25s por si la API tarda en buscar
                r = requests.get(api_url, params=params, timeout=25)
                
                if r.status_code == 200:
                    try:
                        data = r.json()
                        status_api = data.get("Status") or data.get("status")
                        
                        if status_api in ["success", "Success", "SUCCESS", True] and "results" in data:
                            resultados = data["results"]
                            total = data.get("total", len(resultados))
                            
                            if len(resultados) > 0:
                                detalle_ataque = f"🔎 RASTREO: {referencia}\\n"
                                detalle_ataque += f"📊 DATA OBTENIDA: {total} registros\\n\\n"
                                
                                limite = 150
                                for res in resultados[:limite]:
                                    detalle_ataque += f"🌐 HOST: {res.get('host', 'N/A')}\\n"
                                    detalle_ataque += f"👤 USER: {res.get('usuario', 'N/A')}\\n"
                                    detalle_ataque += f"🔑 PASS: {res.get('password', 'N/A')}\\n"
                                    detalle_ataque += "--------------------------\\n"
                                    
                                if len(resultados) > limite:
                                    detalle_ataque += f"\\n... [Mostrando primeros {limite} resultados de {total}]"

                                cur.execute("UPDATE usuarios SET creditos = creditos - ? WHERE user=?", (costo, cliente))
                                cur.execute("""
                                    INSERT INTO pedidos (cliente, referencia, estado, tipo, respuesta, detalle, codigo, operador)
                                    VALUES (?, ?, 'EXITOSO', 'intelx', 'TARGET LOCALIZADO', ?, '', 'SISTEMA_API')
                                """, (cliente, referencia, detalle_ataque))
                                conn.commit()
                                
                                # GENERACIÓN DEL PDF EN MEMORIA Y CONVERSIÓN A BASE64
                                pdf = FPDF()
                                pdf.add_page()
                                pdf.set_font("Arial", 'B', 16)
                                pdf.cell(200, 10, txt="Reporte IntelX - ULP DRAKITO SETT", ln=True, align='C')
                                pdf.ln(5)
                                pdf.set_font("Arial", size=10)
                                
                                texto_limpio = detalle_ataque.replace('\\n', '\n')
                                texto_final = texto_limpio.encode('latin-1', 'replace').decode('latin-1')
                                pdf.multi_cell(0, 8, txt=texto_final)
                                
                                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                                pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
                                data_uri = f"data:application/pdf;base64,{pdf_b64}"
                                nombre_archivo = f"IntelX_{referencia.replace('.', '_').replace('/', '_')}.pdf"
                                
                                msg = f"""
                                <p class='text-emerald-400 text-[11px] text-center font-black mb-4 bg-emerald-500/10 border border-emerald-500/30 p-4 rounded-2xl uppercase tracking-widest'>¡Datos Extraídos! ({total})</p>
                                
                                <div class="bg-black/40 border border-white/10 rounded-2xl p-5 mb-6 text-center shadow-lg">
                                    <h3 class="text-white font-black text-sm mb-1">{nombre_archivo}</h3>
                                    <p class="text-gray-400 text-[10px] uppercase tracking-widest mb-4 font-bold">Vista Previa del Reporte</p>
                                    
                                    <iframe src="{data_uri}#toolbar=0" class="w-full h-64 rounded-xl border border-white/20 mb-5 bg-white"></iframe>
                                    
                                    <div class="grid grid-cols-2 gap-4">
                                        <a href="{data_uri}" target="_blank" class="w-full bg-blue-500/20 border border-blue-500/40 text-blue-400 p-3 rounded-xl font-black text-[10px] uppercase tracking-[0.2em] shadow-lg hover:bg-blue-500/30 transition flex items-center justify-center gap-2">
                                            <span class="text-base">👁️</span> VER
                                        </a>
                                        <a href="{data_uri}" download="{nombre_archivo}" class="w-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 p-3 rounded-xl font-black text-[10px] uppercase tracking-[0.2em] shadow-lg hover:bg-emerald-500/30 transition flex items-center justify-center gap-2">
                                            <span class="text-base">📥</span> DESCARGAR
                                        </a>
                                    </div>
                                </div>
                                """
                            else:
                                msg = "<p class='text-yellow-400 text-[11px] text-center font-black mb-6 bg-yellow-500/10 border border-yellow-500/30 p-4 rounded-2xl uppercase tracking-widest'>Sin registros en la DB IntelX.</p>"
                        else:
                            msg = f"<p class='text-rose-400 text-[11px] text-center font-black mb-6 bg-rose-500/10 border border-rose-500/30 p-4 rounded-2xl uppercase tracking-widest'>Fallo de API: Estructura desconocida.</p>"
                    except json.JSONDecodeError:
                        msg = "<p class='text-rose-400 text-[11px] text-center font-black mb-6 bg-rose-500/10 border border-rose-500/30 p-4 rounded-2xl uppercase tracking-widest'>Fallo crítico: La API no devolvió un JSON válido.</p>"
                else:
                    msg = f"<p class='text-rose-400 text-[11px] text-center font-black mb-6 bg-rose-500/10 border border-rose-500/30 p-4 rounded-2xl uppercase tracking-widest'>API Error HTTP {r.status_code}. El servidor rechazó la conexión.</p>"
                    
            except requests.exceptions.Timeout:
                msg = "<p class='text-rose-400 text-[11px] text-center font-black mb-6 bg-rose-500/10 border border-rose-500/30 p-4 rounded-2xl uppercase tracking-widest'>Timeout: La API de IntelX tardó demasiado en responder (>25s).</p>"
            except requests.exceptions.ConnectionError:
                msg = "<p class='text-rose-400 text-[11px] text-center font-black mb-6 bg-rose-500/10 border border-rose-500/30 p-4 rounded-2xl uppercase tracking-widest'>Error: Conexión rechazada o caída en el servidor IntelX.</p>"
            except Exception as e:
                msg = f"<p class='text-rose-400 text-[10px] text-center font-bold mb-6 bg-rose-500/10 border border-rose-500/30 p-4 rounded-2xl'>Error interno: {str(e)[:50]}</p>"
                
        else:
            msg = "<p class='text-rose-400 text-[11px] text-center font-black mb-6 bg-rose-500/10 border border-rose-500/30 p-4 rounded-2xl uppercase tracking-widest'>Créditos Insuficientes</p>"

        try:
            conn.close()
        except:
            pass

    content = f"""
    <div class="neon-card p-8 mt-10 text-center">
        <h2 class="text-[13px] text-cyan-400 font-black mb-8 uppercase tracking-[0.3em]">Módulo IntelX</h2>
        {msg}
        <form action="/intelx" method="POST" class="space-y-6">
            <div class="bg-white/[0.02] p-6 rounded-[24px] border border-white/10 relative overflow-hidden">
                <div class="absolute inset-0 bg-gradient-to-b from-cyan-500/5 to-transparent"></div>
                <p class="text-[10px] text-gray-400 uppercase font-black tracking-widest mb-4 text-left relative z-10">Target a escanear</p>
                <input type="text" name="dato" placeholder="Dominios (ej: google.com), Correos..." maxlength="60"
                       class="relative z-10 bg-black/40 w-full text-center text-lg font-mono font-bold text-white outline-none placeholder-gray-600 border border-white/10 rounded-xl py-4 focus:border-cyan-500/50 transition-colors" required>
            </div>
            <button class="w-full bg-gradient-to-r from-cyan-500 to-blue-500 p-4 rounded-xl font-black text-xs uppercase tracking-[0.2em] text-white shadow-[0_10px_20px_rgba(14,165,233,0.3)] hover:scale-[1.02] transition-transform">
                EJECUTAR EXTRACCIÓN (1 Cr.)
            </button>
        </form>
    </div>
    """
    return layout(content, True)


@app.route("/llamadas_spam", methods=["GET", "POST"])
def llamadas_spam():
    if not require_login() or not can_use_client_features():
        return redirect("/")

    msg = ""
    if request.method == "POST":
        cliente = session.get("user")
        numero = request.form.get("numero", "").strip()
        try:
            nivel = int(request.form.get("level", 1))
        except:
            nivel = 1

        costo = 2

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT creditos FROM usuarios WHERE user=?", (cliente,))
        row = cur.fetchone()

        if row and row["creditos"] >= costo:
            
            api_url = "https://gdnnmmlwnhbyngvshxms.supabase.co/functions/v1/spam-api"
            payload = {"phone": numero, "level": nivel, "clave": "angelkbro"}
            headers = {"Authorization": "Bearer angelkbro", "Content-Type": "application/json"}
            
            try:
                r = requests.post(api_url, json=payload, headers=headers, timeout=15)
                
                if r.status_code in [200, 201]:
                    cur.execute("UPDATE usuarios SET creditos = creditos - ? WHERE user=?", (costo, cliente))
                    
                    detalle_ataque = f"🎯 TARGET: {numero}\\n🔥 POTENCIA: Nivel {nivel}\\n✅ ESTADO: Bombardeo iniciado."
                    
                    cur.execute("""
                        INSERT INTO pedidos (cliente, referencia, estado, tipo, respuesta, detalle, codigo, operador)
                        VALUES (?, ?, 'EXITOSO', 'llamadas_spam', 'SISTEMA ACTIVO', ?, '', 'SISTEMA_API')
                    """, (cliente, numero, detalle_ataque))
                    
                    conn.commit()
                    msg = f"<p class='text-emerald-400 text-[11px] text-center font-black mb-6 bg-emerald-500/10 border border-emerald-500/30 p-4 rounded-2xl uppercase tracking-widest'>¡Bombardeo Nivel {nivel} en curso hacia el {numero}!</p>"
                else:
                    msg = f"<p class='text-rose-400 text-[11px] text-center font-black mb-6 bg-rose-500/10 border border-rose-500/30 p-4 rounded-2xl uppercase tracking-widest'>Error en la API. HTTP {r.status_code}.</p>"
            except Exception as e:
                msg = f"<p class='text-rose-400 text-[11px] text-center font-black mb-6 bg-rose-500/10 border border-rose-500/30 p-4 rounded-2xl uppercase tracking-widest'>Error de conexión: La API Spam no responde.</p>"
                
        else:
            msg = "<p class='text-rose-400 text-[11px] text-center font-black mb-6 bg-rose-500/10 border border-rose-500/30 p-4 rounded-2xl uppercase tracking-widest'>Créditos Insuficientes</p>"

        conn.close()

    content = f"""
    <div class="neon-card p-8 mt-10">
        <h2 class="text-[13px] text-red-400 font-black mb-8 uppercase text-center tracking-[0.3em]">Call Bomber</h2>
        {msg}
        <form action="/llamadas_spam" method="POST" class="space-y-6">
            <div class="bg-white/[0.02] p-6 rounded-[24px] border border-white/10 relative overflow-hidden">
                <div class="absolute inset-0 bg-gradient-to-b from-red-500/5 to-transparent"></div>
                
                <p class="text-[10px] text-gray-400 uppercase font-black tracking-widest mb-3 text-left relative z-10">Número Objetivo</p>
                <input type="text" name="numero" placeholder="Ejem: 999888777" class="relative z-10 bg-black/40 w-full text-center text-xl font-mono font-bold text-white outline-none placeholder-gray-600 border border-white/10 rounded-xl py-4 mb-6 focus:border-red-500/50 transition-colors" required>
                
                <p class="text-[10px] text-gray-400 uppercase font-black tracking-widest mb-3 text-left border-t border-white/10 pt-5 relative z-10">Potencia de Ataque</p>
                <select name="level" class="relative z-10 input-dark appearance-none text-center font-bold text-red-400 cursor-pointer !bg-black/40 !border-white/10 focus:!border-red-500/50" required>
                    <option value="1">Nivel 1 (Aviso)</option>
                    <option value="2">Nivel 2 (Molestia Constante)</option>
                    <option value="3">Nivel 3 (Saturación Total)</option>
                </select>
            </div>
            
            <button class="w-full bg-gradient-to-r from-red-600 to-rose-500 p-4 rounded-xl font-black text-xs uppercase tracking-[0.2em] text-white shadow-[0_10px_20px_rgba(225,29,72,0.3)] mt-4 hover:scale-[1.02] transition-transform">
                INICIAR BOMBARDEO (2 Cr.)
            </button>
        </form>
    </div>
    """
    return layout(content, True)


@app.route("/soporte")
def soporte():
    if not require_login():
        return redirect("/login")

    content = """
    <div class="neon-card p-10 mt-6 text-center">
        <div class="w-20 h-20 bg-blue-500/10 border border-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <span class="text-4xl">🛡️</span>
        </div>
        <h2 class="text-3xl font-black text-white mb-3 tracking-tight">Centro de Mando</h2>
        <p class="text-gray-400 text-sm mb-10 leading-relaxed max-w-[250px] mx-auto">
            Resolución inmediata de conflictos técnicos y fallos de API.
        </p>

        <div class="bg-white/[0.02] rounded-[24px] p-6 border border-white/10 text-left mb-10 shadow-sm relative overflow-hidden">
            <div class="absolute left-0 top-0 w-1 h-full bg-gradient-to-b from-cyan-500 to-purple-500"></div>
            <p class="text-white text-sm leading-relaxed mb-6 pl-2">
                <span class="text-cyan-400 font-black tracking-wide">💡 Dudas con IntelX</span><br>
                <span class="text-gray-400 text-xs">Si el tracker bota un HTTP Error, reporta el dominio o IP para su parche.</span>
            </p>
            <p class="text-white text-sm leading-relaxed pl-2">
                <span class="text-rose-400 font-black tracking-wide">⚠️ Falla en Bomber</span><br>
                <span class="text-gray-400 text-xs">Si los créditos se consumieron pero el target no recibe el spam, abriremos un ticket.</span>
            </p>
        </div>

        <div class="text-center">
            <a href="https://t.me/DRAKITO_VIP" target="_blank"
               class="inline-block bg-white text-black rounded-xl py-4 px-12 text-xs uppercase font-black tracking-[0.2em] shadow-[0_0_20px_rgba(255,255,255,0.2)] hover:scale-105 transition-transform">
                ABRIR TICKET ➔
            </a>
            <p class="text-gray-500 text-[10px] mt-6 uppercase tracking-[0.3em] font-bold">Respuesta en < 5 mins</p>
        </div>
    </div>
    """
    return layout(content, True)


init_db()

# Ignorado por Vercel
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
