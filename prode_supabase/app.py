import base64
import os

import streamlit as st

# Directorio donde vive este script (la raíz del repo). Usar rutas absolutas
# basadas en __file__ evita que las imágenes "desaparezcan" cuando Streamlit
# se ejecuta con un directorio de trabajo distinto al del repo.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(
    page_title="PRODE FUTBOL ARGENTINO 2026",
    page_icon=os.path.join(BASE_DIR, "icon2026fwc.png"),
    layout="wide"
)

# ══════════════════════════════════════════════════════════════════════════
# IMÁGENES: fondo y logo cargados desde archivo (no van embebidos en base64
# en el código). Para cambiarlos: subí al repositorio un archivo con el
# mismo nombre reemplazando el actual y listo, no hace falta tocar nada más.
# ══════════════════════════════════════════════════════════════════════════
BG_IMAGE_PATH = os.path.join(BASE_DIR, "AFA2026.png")
try:
    with open(BG_IMAGE_PATH, "rb") as _f:
        BG_IMAGE_BASE64 = base64.b64encode(_f.read()).decode()
except FileNotFoundError:
    BG_IMAGE_BASE64 = ""
    st.warning(f"⚠️ No se encontró la imagen de fondo en la ruta '{BG_IMAGE_PATH}'. Verificá que el archivo 'AFA2026.png' esté en la raíz del repo, junto a app.py.")

LOGO_PATH = os.path.join(BASE_DIR, "LOGO.png")
try:
    with open(LOGO_PATH, "rb") as _f:
        LOGO_BASE64 = base64.b64encode(_f.read()).decode()
except FileNotFoundError:
    LOGO_BASE64 = ""
    st.warning(f"⚠️ No se encontró el logo en la ruta '{LOGO_PATH}'. Verificá que el archivo 'LOGO.png' esté en la raíz del repo, junto a app.py.")


# ══════════════════════════════════════════════════════════════════════════
# AVISOS IMPORTANTES — editá esta lista para publicar avisos a los
# jugadores. Cada elemento es un aviso distinto (agregá o quitá los que
# quieras, no hay límite). Se renderizan como tarjetas independientes.
# ══════════════════════════════════════════════════════════════════════════
AVISOS_IMPORTANTES = [
    "En la Boleta Digital de AGOSTO se juegan las fechas: 3 / 4 / 5 / 6 / 7.",
    "FECHA 5 (Cinco) SE JUEGA FECHA EXTRAORDINARIA con MARCADOR EXACTO. Sistema de puntaje: 1 punto por acertar el resultado (Local / Empate / Visitante) · 3 puntos en total si acertás el resultado exacto.",
]

# ══════════════════════════════════════════════════════════════════════════
# TARJETAS INFORMATIVAS — se muestran en una grilla debajo del pozo.
# Agregá, editá o borrá elementos de esta lista para cambiar el contenido.
# Cada tarjeta es un diccionario con: titulo y texto.
# ══════════════════════════════════════════════════════════════════════════
TARJETAS_INFO = [
    {
        "titulo": "Cómo se juega",
        "texto": "Cargá tu pronóstico en BOLETA DIGITAL
                 antes de que arranque cada partido. "
                 "1 punto por acertar Local / Empate / Visitante, 3 puntos "
                 "en total si acertás el marcador exacto.",
    },
    {
        "titulo": "Cómo se arma el pozo",
        "texto": "Se suman $10.000 por cada participante inscripto y con "
                 "la cuota paga. El líder del ranking general se lo lleva "
                 "completo (se reparte en caso de empate).",
    },
    {
        "titulo": "Cierre de pronósticos",
        "texto": "Apenas arranca cada partido, esa boleta se bloquea "
                 "automáticamente: ya no se puede cargar ni modificar el "
                 "pronóstico.",
    },
    {
        "titulo": "Seguí tu posición",
        "texto": "Entrá a Ranking en el menú lateral para ver tu puesto "
                 "actualizado, tus puntos y cómo te comparás con el resto.",
    },
]

# Colores que se van alternando en el borde superior de cada tarjeta
# informativa, solo por variedad visual (podés agregar más si sumás cards).
_ACENTOS_TARJETAS = ["var(--home-gold)", "var(--home-violet)", "var(--home-mint)", "#FF8A65"]


# ══════════════════════════════════════════════════════════════════════════
# ESTILOS GLOBALES
# ══════════════════════════════════════════════════════════════════════════
_CSS_GLOBAL = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

:root {
    --home-ink: #060912;
    --home-card-light: rgba(255,255,255,0.045);
    --home-line: rgba(255,255,255,0.09);
    --home-gold: #E8C96B;
    --home-gold-line: rgba(232,201,107,0.4);
    --home-mint: #4ADE80;
    --home-violet: #A78BFA;
    --home-text-dim: rgba(241,245,249,0.6);
}

.stApp {
    background-image:
        linear-gradient(180deg, rgba(4,7,16,0.80) 0%, rgba(4,7,16,0.52) 32%, rgba(4,7,16,0.68) 68%, rgba(4,7,16,0.92) 100%),
        url('data:image/png;base64,__BG_IMAGE_BASE64__');
    background-size: cover, cover;
    background-position: center, center;
    background-repeat: no-repeat, no-repeat;
    background-attachment: fixed, fixed;
    background-color: var(--home-ink);
}
[data-testid="stHeader"] { background: transparent !important; }
.block-container { padding-top: 2.4rem; max-width: 1080px; }
:focus-visible { outline: 2px solid var(--home-gold); outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) {
    * { animation: none !important; }
}

/* ── HERO ─────────────────────────────────────────────────────────────── */
.home-hero { text-align: center; max-width: 720px; margin: 4px auto 26px; }
.home-kicker {
    font-family: 'Inter', sans-serif; font-size: 0.72rem; font-weight: 600;
    letter-spacing: 0.36em; text-transform: uppercase; color: var(--home-gold);
    opacity: 0.9; margin-bottom: 12px;
}
.home-title {
    font-family: 'Bebas Neue', sans-serif; font-size: clamp(2.3rem, 6vw, 4.1rem);
    letter-spacing: 2px; line-height: 1; color: #fff;
    text-shadow: 0 4px 26px rgba(0,0,0,0.65); margin-bottom: 12px;
}
.home-title span { color: var(--home-gold); }
.home-subtitle {
    font-family: 'Inter', sans-serif; font-size: 0.94rem; font-weight: 400;
    color: var(--home-text-dim); letter-spacing: 0.01em; line-height: 1.5;
}

/* ── AVISO DE MENÚ ────────────────────────────────────────────────────── */
.home-navhint {
    display: flex; align-items: center; justify-content: center; gap: 10px;
    max-width: 540px; margin: 0 auto 34px; padding: 12px 18px;
    background: var(--home-card-light); border: 1px solid var(--home-line);
    border-radius: 12px; font-family: 'Inter', sans-serif; font-size: 0.82rem;
    color: var(--home-text-dim); text-align: center;
}

/* ── AVISO IMPORTANTE ─────────────────────────────────────────────────── */
.home-aviso-wrap { max-width: 720px; margin: 0 auto 32px; }
.home-aviso-card {
    position: relative; overflow: hidden;
    background: linear-gradient(160deg, rgba(120,20,20,0.32), rgba(50,8,8,0.22));
    border: 1px solid rgba(255,90,90,0.42); border-radius: 16px;
    padding: 24px 24px 20px;
    backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
    box-shadow: 0 12px 36px rgba(255,40,40,0.12);
}
.home-aviso-card::before {
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 6px;
    background: repeating-linear-gradient(135deg, #FFC53D 0 14px, #14161c 14px 28px);
    opacity: 0.92;
}
.home-aviso-head { text-align: center; margin: 6px 0 18px; }
.home-aviso-kicker {
    font-family: 'Inter', sans-serif; font-size: 0.66rem; font-weight: 600;
    letter-spacing: 0.22em; text-transform: uppercase; color: rgba(255,180,180,0.8);
    margin-bottom: 3px;
}
.home-aviso-title {
    font-family: 'Bebas Neue', sans-serif; font-size: 1.55rem; letter-spacing: 2px;
    color: #FF6B6B; text-shadow: 0 0 22px rgba(255,60,60,0.4);
}
.home-aviso-list { display: flex; flex-direction: column; gap: 10px; }
.home-aviso-item {
    display: flex; gap: 12px; align-items: flex-start;
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.09);
    border-radius: 11px; padding: 13px 15px;
}
.home-aviso-bar {
    flex: none; width: 4px; align-self: stretch; border-radius: 3px;
    background: linear-gradient(180deg, #FFC53D, #FF5A5A);
}
.home-aviso-item p {
    margin: 0; font-family: 'Inter', sans-serif; font-size: 0.86rem;
    line-height: 1.55; color: rgba(255,255,255,0.9);
}

/* ── POZO — TARJETA "BOLETO" ──────────────────────────────────────────── */
.home-pozo-wrap { max-width: 620px; margin: 8px auto 36px; }
.home-pozo-card {
    position: relative; overflow: hidden;
    background: linear-gradient(165deg, rgba(10,15,35,0.94), rgba(10,15,35,0.78));
    border: 1px solid var(--home-gold-line); border-radius: 22px;
    padding: 36px 32px 28px;
    box-shadow: 0 0 0 1px rgba(232,201,107,0.07), 0 22px 64px rgba(0,0,0,0.55),
                0 0 90px rgba(232,201,107,0.10);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
}
.home-pozo-card::before, .home-pozo-card::after {
    content: ""; position: absolute; width: 26px; height: 26px; border-radius: 50%;
    background: var(--home-ink); box-shadow: inset 0 0 0 1px var(--home-gold-line);
    top: 50%; transform: translateY(-50%);
}
.home-pozo-card::before { left: -13px; }
.home-pozo-card::after { right: -13px; }
.home-pozo-logo { display: flex; justify-content: center; margin-bottom: 18px; }
.home-pozo-logo img {
    max-width: 190px; width: 100%; height: auto;
    filter: drop-shadow(0 4px 18px rgba(0,0,0,0.6));
}
.home-pozo-kicker {
    font-family: 'Inter', sans-serif; font-size: 0.7rem; font-weight: 600;
    letter-spacing: 0.34em; text-transform: uppercase; color: rgba(232,201,107,0.75);
    text-align: center; margin-bottom: 8px;
}
.home-pozo-monto {
    font-family: 'Bebas Neue', sans-serif; font-size: clamp(3rem, 10vw, 5.6rem);
    line-height: 1; text-align: center; color: #FFD700; letter-spacing: 0.03em;
    font-variant-numeric: tabular-nums;
    text-shadow: 0 0 40px rgba(255,215,0,0.45), 0 4px 20px rgba(0,0,0,0.8);
    animation: home-glow-pulse 3.6s ease-in-out infinite;
}
@keyframes home-glow-pulse {
    0%, 100% { text-shadow: 0 0 40px rgba(255,215,0,0.45), 0 4px 20px rgba(0,0,0,0.8); }
    50%      { text-shadow: 0 0 62px rgba(255,215,0,0.72), 0 4px 20px rgba(0,0,0,0.8); }
}
.home-pozo-sub {
    font-family: 'Inter', sans-serif; font-size: 0.78rem; color: rgba(255,255,255,0.42);
    text-align: center; margin-bottom: 24px;
}
.home-pozo-tear {
    height: 0; border-top: 2px dashed rgba(232,201,107,0.35); margin: 0 -32px 22px;
}
.home-ganadores-titulo {
    font-family: 'Bebas Neue', sans-serif; font-size: 1.05rem; letter-spacing: 0.2em;
    color: rgba(255,255,255,0.55); text-align: center; text-transform: uppercase;
    margin-bottom: 14px;
}
.home-empate-nota {
    font-family: 'Inter', sans-serif; font-size: 0.72rem; color: rgba(255,215,0,0.8);
    text-align: center; margin: -6px 0 14px; letter-spacing: 0.02em;
}
.home-ganador-row {
    position: relative; display: flex; align-items: center; gap: 14px; overflow: hidden;
    background: linear-gradient(135deg, rgba(255,215,0,0.10), rgba(255,215,0,0.03));
    border: 1px solid rgba(255,215,0,0.34); border-radius: 12px; padding: 14px 18px;
    margin-bottom: 10px;
}
.home-ganador-row::before {
    content: ""; position: absolute; top: 0; left: 0; width: 4px; height: 100%;
    background: linear-gradient(180deg, #FFD700, #FFA500);
}
.home-ganador-nombre {
    font-family: 'Inter', sans-serif; font-weight: 700; font-size: 1rem; color: #fff;
    flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.home-ganador-datos { display: flex; align-items: center; gap: 16px; }
.home-ganador-pts-box { text-align: center; }
.home-ganador-pts {
    font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.35rem;
    color: #FFD700; line-height: 1;
}
.home-ganador-pts-label {
    font-size: 0.56rem; color: rgba(255,210,0,0.5); text-transform: uppercase; letter-spacing: 0.14em;
}
.home-ganador-premio-box {
    text-align: center; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,215,0,0.25);
    border-radius: 9px; padding: 4px 12px;
}
.home-ganador-premio {
    font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1rem;
    color: #4ADE80; line-height: 1.1;
}
.home-ganador-premio-label {
    font-size: 0.54rem; color: rgba(74,222,128,0.6); text-transform: uppercase; letter-spacing: 0.12em;
}
.home-sin-ganador {
    text-align: center; color: rgba(255,255,255,0.32); font-size: 0.85rem;
    padding: 14px 0; font-family: 'Inter', sans-serif;
}
.home-pozo-formula {
    font-family: 'Inter', sans-serif; font-size: 0.68rem; color: rgba(255,255,255,0.35);
    text-align: center; margin-top: 20px; letter-spacing: 0.03em;
}
.home-pozo-barcode {
    margin: 22px auto 0; height: 26px; max-width: 220px; opacity: 0.32;
    background: repeating-linear-gradient(90deg,
        rgba(255,255,255,0.55) 0 2px, transparent 2px 5px,
        rgba(255,255,255,0.55) 5px 6px, transparent 6px 10px,
        rgba(255,255,255,0.55) 10px 13px, transparent 13px 17px);
}
.home-pozo-ticketno {
    font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; letter-spacing: 0.16em;
    color: rgba(255,255,255,0.3); text-align: center; margin-top: 7px; text-transform: uppercase;
}

/* ── TARJETAS INFORMATIVAS ────────────────────────────────────────────── */
.home-info-section { max-width: 1000px; margin: 0 auto 42px; }
.home-info-heading {
    font-family: 'Bebas Neue', sans-serif; font-size: 1rem; letter-spacing: 0.22em;
    text-transform: uppercase; color: rgba(255,255,255,0.5); text-align: center;
    margin-bottom: 18px;
}
.home-info-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px;
}
.home-info-card {
    position: relative; overflow: hidden;
    background: rgba(255,255,255,0.04); border: 1px solid var(--home-line);
    border-radius: 14px; padding: 20px 20px 18px;
    transition: transform 0.18s ease, border-color 0.18s ease;
}
.home-info-card:hover { transform: translateY(-3px); border-color: rgba(255,255,255,0.22); }
.home-info-card::before {
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: var(--accent, var(--home-gold));
}
.home-info-titulo {
    font-family: 'Bebas Neue', sans-serif; font-size: 1.05rem; letter-spacing: 1px;
    color: #fff; margin-bottom: 6px;
}
.home-info-texto {
    font-family: 'Inter', sans-serif; font-size: 0.8rem; line-height: 1.55;
    color: rgba(255,255,255,0.65);
}
</style>
""".replace("__BG_IMAGE_BASE64__", BG_IMAGE_BASE64)

st.markdown(_CSS_GLOBAL, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════════════════════════════════
st.markdown(
    '<div class="home-hero">'
    '<div class="home-kicker">Temporada 2026</div>'
    '<h1 class="home-title">PRODE FÚTBOL <span>ARGENTINO</span> 2026</h1>'
    '<p class="home-subtitle">Pronosticá cada fecha, sumá puntos y peleá el pozo '
    'junto con el resto de los participantes.</p>'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="home-navhint">'
    '<span>Desplegá el menú lateral para cargar tu boleta, ver el fixture, '
    'los resultados y el ranking.</span></div>',
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════
# AVISOS IMPORTANTES
# ══════════════════════════════════════════════════════════════════════════
if AVISOS_IMPORTANTES:
    avisos_html = "".join(
        f'<div class="home-aviso-item"><span class="home-aviso-bar"></span><p>{aviso}</p></div>'
        for aviso in AVISOS_IMPORTANTES
    )
    st.markdown(
        '<div class="home-aviso-wrap">'
        '<div class="home-aviso-card">'
        '<div class="home-aviso-head">'
        '<div class="home-aviso-kicker">Atención participantes</div>'
        '<div class="home-aviso-title">AVISO IMPORTANTE</div>'
        '</div>'
        f'<div class="home-aviso-list">{avisos_html}</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════
# POZO Y GANADORES
# ══════════════════════════════════════════════════════════════════════════
try:
    from database import conectar
    from ranking import obtener_ranking

    sb = conectar()
    resp_part = sb.table("jugadores").select("id, pagado, activo").execute()
    # El pozo solo debe sumar jugadores que pagaron la inscripción Y que no
    # estén pausados/ocultos por el admin. Si "activo" no existiera todavía
    # en algún registro viejo, se lo trata como True por defecto.
    _jugadores_habilitados = [
        j for j in (resp_part.data or [])
        if j.get("pagado") and j.get("activo", True)
    ]
    total_participantes = len(_jugadores_habilitados)
    pozo = total_participantes * 10_000

    ranking = obtener_ranking()

    if ranking:
        max_puntos = ranking[0]["puntos"]
        ganadores = [r for r in ranking if r["puntos"] == max_puntos]
    else:
        max_puntos = 0
        ganadores = []

    pozo_fmt = f"${pozo:,.0f}".replace(",", ".")

    cant_ganadores = len(ganadores)
    premio_individual = pozo / cant_ganadores if cant_ganadores > 0 else 0
    premio_individual_fmt = f"${premio_individual:,.0f}".replace(",", ".")

    if ganadores and max_puntos > 0:
        filas = []
        for g in ganadores:
            fila = (
                '<div class="home-ganador-row">'
                f'<div class="home-ganador-nombre">{g["nombre"]}</div>'
                '<div class="home-ganador-datos">'
                '<div class="home-ganador-pts-box">'
                f'<div class="home-ganador-pts">{g["puntos"]}</div>'
                '<div class="home-ganador-pts-label">puntos</div>'
                '</div>'
                '<div class="home-ganador-premio-box">'
                f'<div class="home-ganador-premio">{premio_individual_fmt}</div>'
                '<div class="home-ganador-premio-label">le toca</div>'
                '</div>'
                '</div>'
                '</div>'
            )
            filas.append(fila)
        ganadores_html = "".join(filas)
    else:
        ganadores_html = '<div class="home-sin-ganador">— Aún no hay puntos registrados —</div>'

    if cant_ganadores > 1:
        empate_html = (
            f'<div class="home-empate-nota">Empate entre {cant_ganadores} participantes '
            '— el pozo se reparte en partes iguales</div>'
        )
        formula_texto = f"El pozo se divide en partes iguales entre los {cant_ganadores} líderes del 1° puesto"
    elif cant_ganadores == 1:
        empate_html = ""
        formula_texto = "El ganador del 1° puesto se lleva el pozo completo"
    else:
        empate_html = ""
        formula_texto = "El ganador del 1° puesto se lleva el pozo completo"

    titulo_ganadores = f"Líder{'es' if cant_ganadores > 1 else ''} del ranking"

    logo_header_html = (
        f'<div class="home-pozo-logo"><img src="data:image/png;base64,{LOGO_BASE64}"></div>'
        if LOGO_BASE64 else ""
    )

    ticket_no = f"BOLETA N.° {total_participantes:04d} / TEMPORADA 2026"

    card_html = (
        '<div class="home-pozo-wrap">'
        '<div class="home-pozo-card">'
        f'{logo_header_html}'
        '<div class="home-pozo-kicker">Premio total acumulado</div>'
        f'<div class="home-pozo-monto">{pozo_fmt}</div>'
        f'<div class="home-pozo-sub">{total_participantes} participantes · $10.000 c/u</div>'
        '<div class="home-pozo-tear"></div>'
        f'<div class="home-ganadores-titulo">{titulo_ganadores}</div>'
        f'{empate_html}'
        f'{ganadores_html}'
        f'<div class="home-pozo-formula">{formula_texto}</div>'
        '<div class="home-pozo-barcode"></div>'
        f'<div class="home-pozo-ticketno">{ticket_no}</div>'
        '</div>'
        '</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)

except Exception as e:
    st.warning(f"No se pudo cargar el pozo: {e}")


# ══════════════════════════════════════════════════════════════════════════
# TARJETAS INFORMATIVAS
# ══════════════════════════════════════════════════════════════════════════
if TARJETAS_INFO:
    tarjetas_html = "".join(
        f'<div class="home-info-card" style="--accent:{_ACENTOS_TARJETAS[i % len(_ACENTOS_TARJETAS)]}">'
        f'<div class="home-info-titulo">{t["titulo"]}</div>'
        f'<div class="home-info-texto">{t["texto"]}</div>'
        '</div>'
        for i, t in enumerate(TARJETAS_INFO)
    )
    st.markdown(
        '<div class="home-info-section">'
        '<div class="home-info-heading">Antes de arrancar</div>'
        f'<div class="home-info-grid">{tarjetas_html}</div>'
        '</div>',
        unsafe_allow_html=True,
    )
