from flask import Flask, request, redirect, session
import sqlite3
import random
import json
import os
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ulp_drakito_fass_2026_secret")
DB_PATH = os.environ.get("DB_PATH", "/tmp/sistema.db")
LOGO_URL = "https://i.postimg.cc/C1FHfzjr/IMG-20260413-210412-462.jpg"


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

    # Operador Oculto
    cur.execute("SELECT user FROM usuarios WHERE user=?", ("operador1",))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO usuarios (user, pass, rol, creditos, creado_por)
            VALUES (?, ?, ?, ?, ?)
        """, ("operador1", "123456", "operador", 0, "jhorny"))

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
    <div class="{size_class} rounded-full overflow-hidden border-[2px] border-cyan-400 bg-black flex items-center justify-center shadow-[0_0_20px_rgba(34,211,238,0.5)] animate-pulse-slow {extra_class}">
        <img src="{LOGO_URL}" class="w-full h-full object-cover rounded-full scale-125" alt="logo">
    </div>
    """


def layout(content, show_nav=False, login_bg=False):
    u = session.get("user")
    r = session.get("rol")

    is_boss = is_super_admin()
    is_admin = (r == "admin")
    is_operador = (r == "operador")
    is_client_side = can_use_client_features()

    nav = ""
    if show_nav:
        nav = f"""
        <div class="w-full rounded-[24px] overflow-hidden mb-8 relative z-40 bg-[#08101a] border border-[#162336] shadow-[0_0_25px_rgba(0,0,0,0.5)]">
            <div class="flex items-center justify-between px-5 py-4">
                <div class="flex items-center gap-3">
                    {logo_html("w-12 h-12")}
                    <div class="flex flex-col">
                        <span class="text-[17px] font-black tracking-widest bg-gradient-to-r from-cyan-300 to-purple-400 bg-clip-text text-transparent uppercase">
                            ULP DRAKITO FASS
                        </span>
                    </div>
                </div>

                <button onclick="toggleMenu()" class="w-12 h-12 rounded-full bg-[#111a26] flex items-center justify-center text-cyan-400 shadow-md">
                    <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16m-8 6h8"></path>
                    </svg>
                </button>
            </div>
        </div>

        <div id="sidebar" class="fixed top-0 right-0 h-full w-72 bg-[#060b14] border-l border-[#162336] transform translate-x-full transition-transform duration-300 ease-in-out z-50 p-6 shadow-2xl overflow-y-auto">
            <div class="flex justify-between items-center mb-10">
                <span class="text-[11px] font-bold text-cyan-400 uppercase tracking-[0.2em]">MENÚ DE CONTROL</span>
                <button onclick="toggleMenu()" class="text-white text-3xl">&times;</button>
            </div>

            <div class="flex flex-col gap-6">
                <a href="/" class="text-sm font-bold uppercase text-white hover:text-cyan-400 flex items-center gap-2">🏠 INICIO</a>

                {"<a href='/panel_admin' class='text-sm font-bold uppercase text-white hover:text-cyan-400 flex items-center gap-2'>💎 PANEL ADMIN</a>" if is_boss or is_admin else ""}

                {"<a href='/gestion' class='text-sm font-bold uppercase text-white hover:text-cyan-400 flex items-center gap-2'>⚙️ GESTIÓN</a>" if is_operador else ""}

                <a href="/planes" class="text-sm font-bold uppercase text-white hover:text-cyan-400 flex items-center gap-2"> 🛒 COMPRAR CRÉDITOS</a>

                {"<a href='/intelx' class='text-sm font-bold uppercase text-white hover:text-cyan-400 flex items-center gap-2'>🔍 INTELX</a>" if is_client_side else ""}

                {"<a href='/llamadas_spam' class='text-sm font-bold uppercase text-white hover:text-cyan-400 flex items-center gap-2'>📞 LLAMADAS SPAM</a>" if is_client_side else ""}

                <a href="/soporte" class="text-sm font-bold uppercase text-white hover:text-cyan-400 flex items-center gap-2">🎧 SOPORTE</a>

                <hr class="border-[#162336] my-2">

                <a href="/logout" class="text-sm font-bold uppercase text-red-500 flex items-center gap-2">🚪 SALIR</a>
            </div>
        </div>

        <div id="overlay" onclick="toggleMenu()" class="fixed inset-0 bg-black/80 hidden z-40"></div>
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
                alert('No se pudo copiar automatically');
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
${document.getElementById('rep_detalle').innerText}

OPERADOR: ${document.getElementById('rep_operador').innerText}`;

            copyText(texto);
        }
    </script>
    """

    modal_html = f"""
    <div id="modalReport" class="hidden fixed inset-0 bg-black/90 z-[60] flex items-center justify-center p-4">
        <div class="bg-[#08101a] border border-[#162336] w-full max-w-sm rounded-[30px] p-6 shadow-[0_0_30px_rgba(0,0,0,0.8)] relative">
            <button onclick="closeReport()" class="absolute top-4 right-5 text-gray-400 font-bold text-xl hover:text-white transition">&times;</button>

            <div class="text-center mb-6">
                {logo_html("w-16 h-16", "mx-auto mb-3 shadow-[0_0_15px_rgba(34,211,238,0.5)]")}
                <h3 class="text-cyan-400 font-bold uppercase tracking-widest text-sm">REPORTE OFICIAL</h3>
                <p class="text-[9px] text-gray-500 uppercase tracking-widest mt-1">ULP Drakito Fass System</p>
            </div>

            <div class="space-y-4 text-xs font-mono text-gray-300">
                <div class="flex justify-between gap-3 border-b border-[#162336] pb-2">
                    <span class="text-gray-500">TIPO:</span>
                    <span id="rep_tipo" class="text-cyan-400 font-bold uppercase"></span>
                </div>

                <div class="flex justify-between gap-3 border-b border-[#162336] pb-2">
                    <span class="text-gray-500">REFERENCIA:</span>
                    <span id="rep_ref" class="text-white font-bold uppercase"></span>
                </div>

                <div class="border-b border-[#162336] pb-3">
                    <p class="text-gray-500 mb-1">RESPUESTA:</p>
                    <p id="rep_respuesta" class="text-emerald-400 font-bold whitespace-pre-line"></p>
                </div>

                <div class="border-b border-[#162336] pb-3">
                    <p class="text-gray-500 mb-1">DETALLE:</p>
                    <div id="rep_detalle" class="text-white font-bold whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto bg-black/50 p-2 rounded border border-[#1e293b]"></div>
                </div>

                <div class="hidden">
                    <span id="rep_codigo"></span>
                </div>

                <div class="flex justify-between gap-3 border-b border-[#162336] pb-2">
                    <span class="text-gray-500">OPERADOR:</span>
                    <span id="rep_operador" class="text-cyan-500 font-bold"></span>
                </div>
            </div>

            <div class="grid grid-cols-2 gap-4 mt-8">
                <button onclick="copyReport()" class="bg-[#111b29] text-emerald-400 border border-[#1e293b] rounded-full py-3 text-[11px] uppercase font-bold tracking-widest shadow-lg hover:bg-[#1e293b] transition">
                    COPIAR
                </button>
                <button onclick="closeReport()" class="bg-[#111b29] text-cyan-400 border border-[#1e293b] rounded-full py-3 text-[11px] uppercase font-bold tracking-widest shadow-lg hover:bg-[#1e293b] transition">
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
    <style>
        body {
            background-color: #040914;
            color: white;
            font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            touch-action: manipulation;
            overflow-x: hidden;
            min-height: 100vh;
        }

        .animate-pulse-slow {
            animation: pulseGlow 3s ease-in-out infinite alternate;
        }

        @keyframes pulseGlow {
            0% { box-shadow: 0 0 10px rgba(34,211,238,0.3); }
            100% { box-shadow: 0 0 25px rgba(34,211,238,0.6); }
        }

        .neon-card {
            background-color: #08101a;
            border: 1px solid #162336;
            border-radius: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }

        .input-dark {
            background-color: #111a26;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 14px;
            width: 100%;
            outline: none;
            color: white;
            font-size: 14px;
            transition: border-color 0.2s;
        }

        .input-dark:focus {
            border-color: rgba(56, 189, 248, 0.5);
        }

        .input-dark::placeholder {
            color: #64748b;
        }

        .login-bg {
            position: fixed;
            inset: 0;
            background-image: url('https://i.postimg.cc/x8KdvtPQ/IMG-20260411-020447-078.jpg');
            background-size: cover;
            background-position: center;
            transform: scale(1.05);
            animation: bgmove 20s ease-in-out infinite alternate;
            z-index: 0;
            filter: brightness(0.15) saturate(1.2) blur(2px);
        }

        .login-overlay {
            position: fixed;
            inset: 0;
            background: radial-gradient(circle at center, rgba(34,211,238,0.05), #040914 80%);
            z-index: 1;
        }

        @keyframes bgmove {
            0% { transform: scale(1.05) translate(0px, 0px); }
            100% { transform: scale(1.15) translate(-15px, -10px); }
        }

        .content-wrap {
            position: relative;
            z-index: 2;
            width: 100%;
            max-width: 26rem;
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
        LIMIT 8
    """, (session["user"],))
    peds = cur.fetchall()
    conn.close()

    historial = ""
    for p in peds:
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
                class="bg-transparent text-cyan-400 border border-cyan-500/30 rounded-lg px-4 py-1.5 text-[9px] font-bold uppercase tracking-widest hover:bg-cyan-500/10 transition">
                VER REPORTE
            </button>
            """
        elif p["estado"] == "RECHAZADO":
            btn = '<span class="text-[9px] text-[#ff3333] font-bold tracking-widest uppercase">RECHAZADO</span>'
        else:
            btn = '<span class="text-[9px] text-gray-500 italic font-bold tracking-widest uppercase">PROCESANDO</span>'

        historial += f"""
        <div class="flex justify-between items-center border-b border-[#162336] py-4 gap-4">
            <div class="flex flex-col">
                <span class="text-sm font-mono text-white tracking-wide">{p["referencia"] or "SOLICITUD"}</span>
                <span class="text-[10px] text-cyan-500 uppercase mt-1 font-bold">{(p["tipo"] or "").upper()}</span>
            </div>
            {btn}
        </div>
        """

    content = f"""
    <div class="flex flex-col items-center mb-8 mt-2">
        {logo_html("w-20 h-20", "mb-4 border-[3px]")}
        <h1 class="text-4xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-purple-400 text-center">
            ULP DRAKITO<br>FASS
        </h1>
    </div>

    <div class="grid grid-cols-2 gap-4 mb-8">
        <div class="bg-[#08101a] rounded-[20px] p-5 text-center border border-blue-600 shadow-[0_0_15px_rgba(37,99,235,0.15)]">
            <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-2">USADOS</p>
            <h2 class="text-4xl font-bold text-white">{usados}</h2>
        </div>
        <div class="bg-[#08101a] rounded-[20px] p-5 text-center border border-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.15)]">
            <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-2">RESTANTES</p>
            <h2 class="text-4xl font-bold text-white">{restantes}</h2>
        </div>
    </div>

    <div class="neon-card p-6 mb-8">
        <h3 class="text-[11px] font-bold text-cyan-400 uppercase tracking-widest mb-5 text-center">HISTORIAL</h3>
        <div class="space-y-1">
            {historial or "<p class='text-center text-gray-600 text-sm py-5'>Sin historial</p>"}
        </div>
    </div>

    <div class="neon-card p-6 relative overflow-hidden mb-6">
        <h3 class="text-[13px] font-bold text-cyan-400 uppercase text-center mb-8 tracking-[0.2em]">GUÍA DE USO</h3>

        <div class="mb-6">
            <h4 class="text-white font-bold text-sm mb-2 flex items-center gap-2">
                <span>💰</span> Recargas
            </h4>
            <p class="text-gray-400 text-xs mb-1">
                Planes desde <span class="text-[#10b981] font-bold">S/15</span> hasta <span class="text-[#10b981] font-bold">S/200</span>
            </p>
            <p class="text-gray-400 text-xs">Recarga segura con tu vendedor autorizado.</p>
        </div>

        <div class="mb-6">
            <h4 class="text-white font-bold text-sm mb-2 flex items-center gap-2">
                <span>🎧</span> Soporte
            </h4>
            <p class="text-gray-400 text-xs mb-1">Soporte inmediato 24/7 ante cualquier inconveniente.</p>
            <p class="text-[#10b981] font-bold text-xs tracking-widest uppercase">GRATIS</p>
        </div>

        <div class="mb-6">
            <h4 class="text-white font-bold text-sm mb-3 flex items-center gap-2">
                <span class="text-cyan-500">🔍</span> IntelX
            </h4>
            <ul class="list-disc pl-5 text-gray-400 text-xs space-y-2 mb-3">
                <li>Búsqueda profunda de información mediante DNI, dominios, correos o nombres.</li>
                <li>Procesado 100% automático desde la API Oficial.</li>
            </ul>
            <p class="text-[#ff3333] font-bold text-xs flex items-center gap-1">
                <span class="text-yellow-400">💳</span> Costo: 1 crédito
            </p>
        </div>

        <div class="mb-2">
            <h4 class="text-white font-bold text-sm mb-3 flex items-center gap-2">
                <span class="text-red-500">📞</span> Llamadas Spam
            </h4>
            <ul class="list-disc pl-5 text-gray-400 text-xs space-y-2 mb-3">
                <li>Envío masivo y automatizado de llamadas a un número objetivo.</li>
                <li>Ideal para saturar y molestar una línea telefónica específica.</li>
            </ul>
            <p class="text-[#ff3333] font-bold text-xs flex items-center gap-1">
                <span class="text-yellow-400">💳</span> Costo: 2 créditos
            </p>
        </div>
    </div>
    """
    return layout(content, True)


@app.route("/planes")
def planes():
    if not require_login():
        return redirect("/login")

    precios = [
        ("01 CRÉDITO", "S/15.00"),
        ("04 CRÉDITOS", "S/60.00"),
        ("06 CRÉDITOS", "S/90.00"),
        ("10 CRÉDITOS", "S/150.00"),
        ("12 CRÉDITOS", "S/120.00"),
        ("20 CRÉDITOS", "S/200.00"),
    ]

    cards = ""
    for nombre, precio in precios:
        cards += f"""
        <div class="p-5 mb-4 rounded-[20px] border border-[#a855f7]/50 bg-[#08101a] flex justify-between items-center shadow-[0_0_15px_rgba(168,85,247,0.15)]">
            <div>
                <h3 class="text-white font-bold text-xl tracking-tight">{nombre}</h3>
                <p class="text-gray-500 text-sm font-mono mt-1.5">{precio}</p>
            </div>
            <a href="https://t.me/DRAKITO_VIP" target="_blank"
               class="bg-gradient-to-r from-[#d946ef] to-[#9333ea] px-6 py-3 rounded-full text-[10px] font-bold uppercase tracking-widest text-white shadow-[0_0_15px_rgba(217,70,239,0.4)] hover:opacity-90 transition">
               COMPRAR
            </a>
        </div>
        """

    content = f"""
    <div class="mt-6 mb-8 text-center">
        <h2 class="text-[12px] text-cyan-400 font-black italic uppercase tracking-[0.2em] mb-6">
            PAQUETES OFICIALES
        </h2>
    </div>
    <div class="space-y-3">
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
    <div class="flex flex-col items-center mt-16">
        {logo_html("w-28 h-28", "mb-6 border-[3px] shadow-[0_0_30px_rgba(34,211,238,0.6)]")}

        <h1 class="text-4xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-purple-400 text-center leading-tight">
            ULP DRAKITO<br>FASS
        </h1>
        <p class="text-[10px] uppercase tracking-[0.4em] text-cyan-500 mb-8 mt-2 font-bold">
            Access Panel
        </p>

        <form method="post" class="w-full space-y-4 bg-[#08101a]/90 border border-[#162336] rounded-[24px] p-6 shadow-2xl backdrop-blur-sm">
            <input name="u" placeholder="Usuario" class="w-full bg-[#111a26] border border-[#1e293b] rounded-xl p-4 text-white outline-none focus:border-cyan-500 transition" autocomplete="off" required>
            <input name="p" type="password" placeholder="Contraseña" class="w-full bg-[#111a26] border border-[#1e293b] rounded-xl p-4 text-white outline-none focus:border-cyan-500 transition" required>

            <div class="flex gap-3 pt-2">
                <div class="bg-white text-black rounded-xl flex items-center justify-center font-bold w-1/2 text-2xl tracking-widest shadow-inner">
                    {session['captcha_val']}
                </div>
                <input name="cap" placeholder="Captcha" class="w-1/2 bg-[#111a26] border border-[#1e293b] rounded-xl p-4 text-white text-center outline-none focus:border-cyan-500 transition" autocomplete="off" required>
            </div>

            <button class="w-full bg-[#0ea5e9] p-4 rounded-xl font-bold text-sm uppercase tracking-widest text-white shadow-[0_0_15px_rgba(14,165,233,0.4)] mt-4 hover:bg-[#0284c7] transition">
                Acceder
            </button>
        </form>

        <a href="https://t.me/DRAKITO_VIP" target="_blank"
           class="mt-10 text-cyan-400 text-[11px] font-bold uppercase tracking-widest flex items-center justify-center gap-2 italic w-full hover:text-cyan-300 transition">
           <span>👤</span> CONTACTAR AL VENDEDOR
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

            if r_log == "admin" and not is_super_admin() and rol_a_crear != "user":
                conn.close()
                return "Error: admin solo crea clientes", 403

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
            if target not in ["jhorny", "DRAKITO_VIP7020", "operador1"]:
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
        <div class="bg-[#064e3b]/30 border border-[#10b981]/50 rounded-2xl p-5 mb-6 shadow-[0_0_15px_rgba(16,185,129,0.15)]">
            <p class="text-[10px] uppercase text-emerald-400 font-bold mb-4 tracking-widest flex items-center gap-2">
                <span>✅</span> Nuevo acceso generado
            </p>
            <div class="space-y-3 text-xs text-gray-300 font-mono bg-black/40 p-4 rounded-xl">
                <p><span class="text-cyan-500 font-bold">URL:</span> {nuevo_creado["url"]}</p>
                <p><span class="text-cyan-500 font-bold">USUARIO:</span> {nuevo_creado["user"]}</p>
                <p><span class="text-cyan-500 font-bold">CLAVE:</span> {nuevo_creado["pass"]}</p>
                <p><span class="text-cyan-500 font-bold">ROL:</span> {nuevo_creado["rol"]}</p>
            </div>
            <button onclick="copyText(`{texto_copiar}`)" class="w-full mt-4 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl py-3 text-[10px] uppercase font-bold tracking-widest transition shadow-lg">
                Copiar acceso
            </button>
        </div>
        '''
        session.pop("last_user_created", None)

    lista = ""
    for u in users:
        if u["rol"] == "operador":
            continue

        btn_eliminar = ""
        if u["user"] not in ["jhorny", "DRAKITO_VIP7020"]:
            btn_eliminar = f"""
            <form method="POST" onsubmit="return confirm('¿Seguro que deseas eliminar a {u['user']}?');" class="mt-4">
                <input type="hidden" name="action" value="eliminar_usuario">
                <input type="hidden" name="target" value="{u['user']}">
                <button class="w-full bg-[#7f1d1d]/40 text-red-400 border border-red-500/30 rounded-xl py-2.5 text-[10px] font-bold uppercase tracking-widest hover:bg-[#7f1d1d]/60 transition">
                    Eliminar Usuario
                </button>
            </form>
            """

        lista += f"""
        <div class="p-5 bg-[#0b111a] rounded-[20px] border border-[#1e293b] mb-4 shadow-sm">
            <div class="flex justify-between items-center mb-4">
                <div>
                    <span class="text-white font-bold text-base">{u["user"]}</span>
                    <span class="text-gray-500 text-[10px] ml-2 uppercase tracking-widest">({u["rol"]})</span>
                </div>
                <span class="text-cyan-400 font-black text-lg">{u["creditos"]} Cr.</span>
            </div>

            <div class="grid grid-cols-3 gap-2 mb-2">
                <form method="POST">
                    <input type="hidden" name="action" value="sumar_rapido">
                    <input type="hidden" name="target" value="{u["user"]}">
                    <input type="hidden" name="cant" value="1">
                    <button class="w-full bg-[#111a26] text-cyan-400 border border-[#1e293b] rounded-xl py-2.5 text-xs font-bold hover:bg-[#1e293b] transition">+1</button>
                </form>
                <form method="POST">
                    <input type="hidden" name="action" value="sumar_rapido">
                    <input type="hidden" name="target" value="{u["user"]}">
                    <input type="hidden" name="cant" value="5">
                    <button class="w-full bg-[#111a26] text-cyan-400 border border-[#1e293b] rounded-xl py-2.5 text-xs font-bold hover:bg-[#1e293b] transition">+5</button>
                </form>
                <form method="POST">
                    <input type="hidden" name="action" value="sumar_rapido">
                    <input type="hidden" name="target" value="{u["user"]}">
                    <input type="hidden" name="cant" value="10">
                    <button class="w-full bg-[#111a26] text-cyan-400 border border-[#1e293b] rounded-xl py-2.5 text-xs font-bold hover:bg-[#1e293b] transition">+10</button>
                </form>
            </div>

            <div class="grid grid-cols-3 gap-2">
                <form method="POST">
                    <input type="hidden" name="action" value="sumar_rapido">
                    <input type="hidden" name="target" value="{u["user"]}">
                    <input type="hidden" name="cant" value="-1">
                    <button class="w-full bg-[#3f0f15] text-red-400 border border-[#451515] rounded-xl py-2.5 text-xs font-bold hover:bg-[#4f1515] transition">-1</button>
                </form>
                <form method="POST">
                    <input type="hidden" name="action" value="sumar_rapido">
                    <input type="hidden" name="target" value="{u["user"]}">
                    <input type="hidden" name="cant" value="-5">
                    <button class="w-full bg-[#3f0f15] text-red-400 border border-[#451515] rounded-xl py-2.5 text-xs font-bold hover:bg-[#4f1515] transition">-5</button>
                </form>
                <form method="POST">
                    <input type="hidden" name="action" value="sumar_rapido">
                    <input type="hidden" name="target" value="{u["user"]}">
                    <input type="hidden" name="cant" value="-10">
                    <button class="w-full bg-[#3f0f15] text-red-400 border border-[#451515] rounded-xl py-2.5 text-xs font-bold hover:bg-[#4f1515] transition">-10</button>
                </form>
            </div>
            {btn_eliminar}
        </div>
        """

    content = f"""
    {bloque_nuevo}
    <div class="neon-card p-6 mt-4 mb-6">
        <h2 class="text-[13px] text-cyan-400 font-bold uppercase text-center mb-8 tracking-[0.2em]">
            Panel de Control
        </h2>

        <form method="POST" class="space-y-4 mb-10 border-b border-[#1e293b] pb-8">
            <input type="hidden" name="action" value="crear">
            <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest ml-1">Crear Usuario</p>
            <input name="u" placeholder="Usuario Nuevo" class="input-dark" required>
            <input name="p" placeholder="Contraseña" class="input-dark" required>
            <select name="r" class="input-dark appearance-none">
                <option value="user">Cliente</option>
                {"<option value='admin'>Admin Secundario</option>" if is_super_admin() else ""}
            </select>
            <button class="w-full bg-gradient-to-r from-cyan-500 to-blue-600 p-4 rounded-xl font-bold text-xs uppercase tracking-widest text-white shadow-lg mt-2">
                Registrar
            </button>
        </form>

        <form method="POST" class="space-y-4 mb-10 border-b border-[#1e293b] pb-8">
            <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest ml-1">Modificar Saldo</p>
            <input name="target" placeholder="Usuario Destino" class="input-dark" required>
            <input name="cant" type="number" min="1" placeholder="Cantidad" class="input-dark" required>

            <div class="grid grid-cols-2 gap-3 mt-2">
                <button type="submit" name="action" value="creditos" class="w-full bg-gradient-to-r from-emerald-500 to-teal-400 p-4 rounded-xl font-bold text-xs uppercase tracking-widest text-white shadow-lg">
                    Sumar
                </button>
                <button type="submit" name="action" value="quitar_creditos" class="w-full bg-gradient-to-r from-rose-500 to-red-600 p-4 rounded-xl font-bold text-xs uppercase tracking-widest text-white shadow-lg">
                    Quitar
                </button>
            </div>
        </form>

        <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest ml-1 mb-4">Lista de Usuarios</p>

        <div class="max-h-[500px] overflow-y-auto pr-1">
            {lista or "<p class='text-center text-gray-600 text-sm py-8'>Sin usuarios</p>"}
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
            
            # --- LLAMADA A LA API DE INTELX ---
            api_url = "http://38.250.116.172/api/intelx"
            params = {
                "auth": "9ntEzxnOMYzpJuIEDJ0Qgh",
                "url": referencia
            }
            
            try:
                r = requests.get(api_url, params=params, timeout=20)
                if r.status_code == 200:
                    data = r.json()
                    
                    if data.get("Status") == "success" and "results" in data:
                        resultados = data["results"]
                        total = data.get("total", len(resultados))
                        
                        if len(resultados) > 0:
                            detalle_ataque = f"🔎 BÚSQUEDA: {referencia}\\n"
                            detalle_ataque += f"📊 TOTAL ENCONTRADOS: {total}\\n\\n"
                            
                            limite = 150
                            for res in resultados[:limite]:
                                detalle_ataque += f"🌐 HOST: {res.get('host', 'N/A')}\\n"
                                detalle_ataque += f"👤 USER: {res.get('usuario', 'N/A')}\\n"
                                detalle_ataque += f"🔑 PASS: {res.get('password', 'N/A')}\\n"
                                detalle_ataque += "--------------------------\\n"
                                
                            if len(resultados) > limite:
                                detalle_ataque += f"\\n... [Se muestran los primeros {limite} resultados de {total} encontrados]"

                            cur.execute("UPDATE usuarios SET creditos = creditos - ? WHERE user=?", (costo, cliente))
                            cur.execute("""
                                INSERT INTO pedidos (cliente, referencia, estado, tipo, respuesta, detalle, codigo, operador)
                                VALUES (?, ?, 'EXITOSO', 'intelx', 'DATOS ENCONTRADOS', ?, '', 'SISTEMA_API')
                            """, (cliente, referencia, detalle_ataque))
                            conn.commit()
                            
                            msg = f"<p class='text-emerald-400 text-xs text-center font-bold mb-4 bg-emerald-900/30 p-3 rounded-xl uppercase tracking-widest'>¡Datos encontrados! ({total} resultados)</p>"
                        else:
                            msg = "<p class='text-yellow-400 text-xs text-center font-bold mb-4 bg-yellow-900/30 p-3 rounded-xl uppercase tracking-widest'>No se encontró información para este dato.</p>"
                    else:
                        msg = "<p class='text-red-400 text-xs text-center font-bold mb-4 bg-red-900/30 p-3 rounded-xl uppercase tracking-widest'>Error en la respuesta del servidor IntelX.</p>"
                else:
                    msg = "<p class='text-red-400 text-xs text-center font-bold mb-4 bg-red-900/30 p-3 rounded-xl uppercase tracking-widest'>API de IntelX caída o sin respuesta.</p>"
                    
            except Exception as e:
                msg = "<p class='text-red-400 text-xs text-center font-bold mb-4 bg-red-900/30 p-3 rounded-xl uppercase tracking-widest'>Error de conexión con la API de IntelX.</p>"
                
        else:
            msg = "<p class='text-red-400 text-xs text-center font-bold mb-4 bg-red-900/30 p-3 rounded-xl uppercase tracking-widest'>Saldo insuficiente</p>"

        conn.close()

    content = f"""
    <div class="neon-card p-6 mt-10 text-center">
        <h2 class="text-[13px] text-cyan-400 font-bold mb-8 uppercase tracking-[0.2em]">Búsqueda IntelX</h2>
        {msg}
        <form action="/intelx" method="POST" class="space-y-5">
            <div class="bg-[#111a26] p-5 rounded-2xl border border-[#1e293b]">
                <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-3 text-left">Dato a rastrear</p>
                <input type="text" name="dato" placeholder="Dominios (ej: google.com), Correos, DNI..." maxlength="60"
                       class="bg-transparent w-full text-center text-lg font-mono text-white outline-none placeholder-gray-600" required>
            </div>
            <button class="w-full bg-[#06b6d4] p-4 rounded-xl font-bold text-xs uppercase tracking-widest text-white shadow-[0_0_15px_rgba(6,182,212,0.4)] mt-2 hover:bg-[#0891b2] transition">
                Rastrear Dato (1 Cr.)
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
            
            # --- LLAMADA A LA API DE SUPABASE ---
            api_url = "https://gdnnmmlwnhbyngvshxms.supabase.co/functions/v1/spam-api"
            payload = {
                "phone": numero,
                "level": nivel,
                "clave": "angelkbro"
            }
            headers = {
                "Authorization": "Bearer angelkbro",
                "Content-Type": "application/json"
            }
            
            try:
                r = requests.post(api_url, json=payload, headers=headers, timeout=15)
                
                if r.status_code in [200, 201]:
                    cur.execute("UPDATE usuarios SET creditos = creditos - ? WHERE user=?", (costo, cliente))
                    
                    detalle_ataque = f"🎯 NÚMERO: {numero}\\n🔥 NIVEL: {nivel}\\n✅ ESTADO: Ejecutado automáticamente por API."
                    
                    cur.execute("""
                        INSERT INTO pedidos (cliente, referencia, estado, tipo, respuesta, detalle, codigo, operador)
                        VALUES (?, ?, 'EXITOSO', 'llamadas_spam', 'ATAQUE ENVIADO', ?, '', 'SISTEMA_API')
                    """, (cliente, numero, detalle_ataque))
                    
                    conn.commit()
                    msg = f"<p class='text-emerald-400 text-xs text-center font-bold mb-4 bg-emerald-900/30 p-3 rounded-xl uppercase tracking-widest'>¡Ataque Nivel {nivel} enviado al {numero}!</p>"
                else:
                    msg = "<p class='text-red-400 text-xs text-center font-bold mb-4 bg-red-900/30 p-3 rounded-xl uppercase tracking-widest'>Error en la API. No se cobraron créditos.</p>"
            except Exception as e:
                msg = "<p class='text-red-400 text-xs text-center font-bold mb-4 bg-red-900/30 p-3 rounded-xl uppercase tracking-widest'>La API no responde. Intenta más tarde.</p>"
                
        else:
            msg = "<p class='text-red-400 text-xs text-center font-bold mb-4 bg-red-900/30 p-3 rounded-xl uppercase tracking-widest'>Saldo insuficiente</p>"

        conn.close()

    content = f"""
    <div class="neon-card p-6 mt-10">
        <h2 class="text-[13px] text-cyan-400 font-bold mb-8 uppercase text-center tracking-[0.2em]">Spam de Llamadas</h2>
        {msg}
        <form action="/llamadas_spam" method="POST" class="space-y-5">
            <div class="bg-[#111a26] p-5 rounded-2xl border border-[#1e293b]">
                <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-3 text-left">Número Objetivo</p>
                <input type="text" name="numero" placeholder="Ejem: 999888777" class="bg-transparent w-full text-center text-xl font-mono text-white outline-none placeholder-gray-600 mb-6" required>
                
                <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-3 text-left border-t border-[#1e293b] pt-4">Nivel de Ataque</p>
                <select name="level" class="input-dark appearance-none text-center font-bold text-cyan-400 cursor-pointer" required>
                    <option value="1">Nivel 1 (Básico)</option>
                    <option value="2">Nivel 2 (Intermedio)</option>
                    <option value="3">Nivel 3 (Extremo)</option>
                </select>
            </div>
            
            <button class="w-full bg-[#ef4444] p-4 rounded-xl font-bold text-xs uppercase tracking-widest text-white shadow-[0_0_15px_rgba(239,68,68,0.4)] mt-4 hover:bg-[#dc2626] transition">
                Iniciar Ataque (2 Cr.)
            </button>
        </form>
    </div>
    """
    return layout(content, True)


@app.route("/gestion")
def gestion():
    if not require_login() or session.get("rol") != "operador":
        return redirect("/")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id_pedido, cliente, referencia, tipo, estado
        FROM pedidos
        WHERE estado='PENDIENTE'
        ORDER BY id_pedido DESC
    """)
    ps = cur.fetchall()
    conn.close()

    cards = "".join([
        f"""
        <div class="bg-[#111a26] p-5 rounded-[20px] border border-[#1e293b] mb-4 shadow-sm">
            <div class="flex justify-between items-start mb-4">
                <div class="space-y-1">
                    <p class="text-[9px] text-gray-500 font-bold uppercase tracking-widest">CLIENTE: <span class="text-white">{p["cliente"]}</span></p>
                    <p class="text-[9px] text-cyan-500 font-bold uppercase tracking-widest">TIPO: {(p["tipo"] or "").upper()}</p>
                </div>
                <span class="bg-[#1e293b] text-gray-300 text-[10px] px-3 py-1 rounded-full font-mono">ID: {p["id_pedido"]}</span>
            </div>

            <div class="bg-black/30 p-3 rounded-xl border border-[#1e293b] mb-4">
                <p class="text-sm font-mono text-white text-center">{p["referencia"] or "SIN DATO"}</p>
            </div>

            <a href="/trabajar/{p["id_pedido"]}" class="block text-center w-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white px-4 py-3 rounded-xl text-xs font-bold uppercase tracking-widest shadow-lg hover:opacity-90 transition">
                AGARRAR PEDIDO
            </a>
        </div>
        """
        for p in ps
    ])

    return layout(
        f"""
        <div class="mt-6 mb-8 text-center">
            <h2 class="text-[13px] text-yellow-500 font-black uppercase tracking-[0.2em]">Bandeja Operador</h2>
        </div>
        <div class="space-y-2">
            {cards or '<p class="text-center text-gray-600 text-sm py-10">No hay pedidos manuales pendientes.</p>'}
        </div>
        """,
        True
    )


@app.route("/trabajar/<int:id_p>")
def trabajar(id_p):
    if not require_login() or session.get("rol") != "operador":
        return redirect("/")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id_pedido, cliente, referencia, tipo
        FROM pedidos
        WHERE id_pedido=?
    """, (id_p,))
    p = cur.fetchone()
    conn.close()

    if not p:
        return redirect("/gestion")

    tipo = (p["tipo"] or "").lower()

    if tipo == "intelx":
        form_html = f"""
        <form action="/completar" method="POST" class="space-y-4">
            <input type="hidden" name="id_p" value="{p["id_pedido"]}">
            <input type="hidden" name="tipo_form" value="intelx">

            <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest ml-1">Pega aquí los datos obtenidos:</p>
            <textarea name="datos_obtenidos" placeholder="Nombres, DNI, Correos, Direcciones, etc..."
                class="input-dark h-64 resize-none text-sm leading-relaxed" required></textarea>

            <div class="grid grid-cols-2 gap-4 mt-6">
                <button type="submit" name="accion" value="exito" class="w-full bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl py-4 text-xs font-bold uppercase tracking-widest shadow-[0_0_15px_rgba(16,185,129,0.3)] transition">
                    ENVIAR INFO
                </button>
                <button type="submit" name="accion" value="rechazar" class="w-full bg-rose-500 hover:bg-rose-600 text-white rounded-xl py-4 text-xs font-bold uppercase tracking-widest shadow-[0_0_15px_rgba(244,63,94,0.3)] transition">
                    SIN RESULTADO
                </button>
            </div>
        </form>
        """
    else: 
        form_html = f"""
        <form action="/completar" method="POST" class="space-y-4">
            <input type="hidden" name="id_p" value="{p["id_pedido"]}">
            <input type="hidden" name="tipo_form" value="llamadas_spam">

            <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest ml-1">Notas del ataque (Opcional):</p>
            <textarea name="notas_spam" placeholder="Ej: Ataque finalizado con 500 llamadas exitosas..."
                class="input-dark h-32 resize-none text-sm leading-relaxed"></textarea>

            <div class="grid grid-cols-2 gap-4 mt-6">
                <button type="submit" name="accion" value="exito" class="w-full bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl py-4 text-xs font-bold uppercase tracking-widest shadow-[0_0_15px_rgba(16,185,129,0.3)] transition">
                    SPAM COMPLETADO
                </button>
                <button type="submit" name="accion" value="rechazar" class="w-full bg-rose-500 hover:bg-rose-600 text-white rounded-xl py-4 text-xs font-bold uppercase tracking-widest shadow-[0_0_15px_rgba(244,63,94,0.3)] transition">
                    FALLÓ
                </button>
            </div>
        </form>
        """

    content = f"""
    <div class="neon-card p-6 mt-6 shadow-2xl border-cyan-900/30">
        <h2 class="text-center text-[12px] text-cyan-400 font-bold mb-6 uppercase tracking-[0.2em]">
            Responder Solicitud Manual (Legacy)
        </h2>

        <div class="bg-[#111a26] p-4 rounded-xl mb-8 border border-[#1e293b]">
            <div class="flex justify-between items-center mb-2">
                <p class="text-[9px] text-gray-500 uppercase font-bold tracking-widest">CLIENTE:</p>
                <p class="text-[10px] text-white font-bold">{p["cliente"]}</p>
            </div>
            <div class="flex justify-between items-center mb-4">
                <p class="text-[9px] text-gray-500 uppercase font-bold tracking-widest">TIPO:</p>
                <p class="text-[10px] text-cyan-400 font-bold">{(p["tipo"] or "").upper()}</p>
            </div>

            <div class="bg-black/40 p-3 rounded-lg border border-[#1e293b]">
                <p class="text-xs font-mono text-center text-white">{p["referencia"] or "Sin dato"}</p>
            </div>
        </div>

        {form_html}
    </div>
    """
    return layout(content, True)


@app.route("/completar", methods=["POST"])
def completar():
    if not require_login() or session.get("rol") != "operador":
        return redirect("/")

    id_p = request.form.get("id_p")
    tipo_form = request.form.get("tipo_form", "").strip().lower()
    accion = request.form.get("accion")

    conn = get_conn()
    cur = conn.cursor()

    if accion == "rechazar":
        cur.execute("UPDATE pedidos SET estado='RECHAZADO', operador=? WHERE id_pedido=?", (session.get("user", ""), id_p))
        cur.execute("SELECT cliente, tipo FROM pedidos WHERE id_pedido=?", (id_p,))
        row = cur.fetchone()
        if row:
            cliente = row["cliente"]
            tipo_pedido = (row["tipo"] or "").upper()
            reembolso = 1 if tipo_pedido == "INTELX" else 2
            cur.execute("UPDATE usuarios SET creditos = creditos + ? WHERE user=?", (reembolso, cliente))

    elif accion == "exito":
        if tipo_form == "intelx":
            datos = request.form.get("datos_obtenidos", "").strip()
            respuesta_final = "DATOS ENCONTRADOS"
            
            cur.execute("""
                UPDATE pedidos
                SET respuesta=?, detalle=?, codigo='', operador=?, estado='EXITOSO'
                WHERE id_pedido=?
            """, (
                respuesta_final,
                datos,
                session.get("user", ""),
                id_p
            ))

        else: # llamadas_spam
            notas_spam = request.form.get("notas_spam", "").strip()
            if not notas_spam:
                notas_spam = "El ataque de llamadas masivas se ha ejecutado con éxito sobre el número objetivo."

            cur.execute("""
                UPDATE pedidos
                SET respuesta=?, detalle=?, codigo='', operador=?, estado='EXITOSO'
                WHERE id_pedido=?
            """, (
                "ATAQUE FINALIZADO",
                notas_spam,
                session.get("user", ""),
                id_p
            ))

    conn.commit()
    conn.close()

    return redirect("/gestion")


@app.route("/soporte")
def soporte():
    if not require_login():
        return redirect("/login")

    content = """
    <div class="neon-card p-8 mt-6 text-center">
        <h2 class="text-3xl font-black text-white mb-4 tracking-tight">¿Necesitas ayuda?</h2>
        <p class="text-gray-400 text-sm mb-8 leading-relaxed">
            Estamos aquí para apoyarte en todo momento.
        </p>

        <div class="bg-[#111a26] rounded-[20px] p-6 border-l-4 border-cyan-500 text-left mb-10 shadow-sm">
            <p class="text-white text-sm leading-relaxed mb-6">
                <span class="text-cyan-400 font-bold">💬 ¿Dudas con una búsqueda en IntelX?</span><br>
                <span class="text-gray-400">Contáctanos si un resultado no te convence o quieres más datos.</span>
            </p>
            <p class="text-white text-sm leading-relaxed">
                <span class="text-rose-400 font-bold">⚠️ ¿Problemas con el envío de spam?</span><br>
                <span class="text-gray-400">Nuestro soporte revisará qué pasó con tu ataque.</span>
            </p>
        </div>

        <div class="text-center">
            <a href="https://t.me/DRAKITO_VIP" target="_blank"
               class="inline-block bg-[#0f172a] text-cyan-400 border border-[#1e293b] rounded-full py-4 px-12 text-sm uppercase font-bold tracking-widest shadow-lg hover:bg-[#1e293b] transition">
                Contactar
            </a>
            <p class="text-gray-500 text-xs mt-6 uppercase tracking-widest font-bold">Soporte disponible 24/7</p>
        </div>
    </div>
    """
    return layout(content, True)


init_db()

# Esta línea Vercel la ignorará, pero sirve si lo pruebas localmente en Pydroid o Termux
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
