"""
08_Comparar_Boletas.py — Prode Liga Profesional Argentina (Torneo Clausura 2026)

Compara, partido por partido, las boletas de dos jugadores: qué le pusieron
a cada partido (1/X/2 + marcador exacto), si coincidieron o no, y el
resultado real una vez jugado.

Usa el MISMO esquema de datos y la MISMA navegación (tabs de Zona A / Zona B
/ Interzonal, indicador de fecha con puntos violetas animados, y mini-cards
de escudos clickeables) que 01_Resultados.py y 05_Pronosticos.py:
  - tabla `partidos`   : zona, fecha_numero, equipo_local, equipo_visitante,
                         fecha_partido, hora, estadio, goles_local, goles_visitante
  - tabla `jugadores`  : id, nombre, username
  - tabla `pronosticos`: jugador_id, partido_id, signo_pred,
                         goles_local_pred, goles_visitante_pred, puntos
  - escudos de clubes  : escudos_map.url_escudo(equipo)
"""
import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from database import conectar
from escudos_map import url_escudo

TZ_ARG = ZoneInfo("America/Argentina/Buenos_Aires")

# Mismos formatos aceptados que en 03_Boleta_digital.py / 05_Pronosticos.py,
# para bancar cómo sea que esté cargado el dato en la base (texto libre,
# date/time de Postgres, etc.)
_FORMATOS_FECHA = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%d/%m/%y",
]
_FORMATOS_HORA = [
    "%H:%M:%S",
    "%H:%M",
    "%H.%M",
    "%Hhs",
    "%H",
]


def _parsear_fecha(fecha_raw):
    if not fecha_raw:
        return None
    fecha_str = str(fecha_raw).strip().split("T")[0].split(" ")[0]
    for fmt in _FORMATOS_FECHA:
        try:
            return datetime.strptime(fecha_str, fmt).date()
        except ValueError:
            continue
    return None


def _parsear_hora(hora_raw):
    if not hora_raw:
        return None
    hora_str = str(hora_raw).strip()
    for fmt in _FORMATOS_HORA:
        try:
            return datetime.strptime(hora_str, fmt).time()
        except ValueError:
            continue
    return None


def _partido_comenzo(fecha_partido, hora) -> bool:
    """
    True si, con la fecha/hora cargada del partido (hora de Argentina), ya
    llegó o pasó el horario de inicio.

    Si no hay fecha/hora cargada, o no se pudo interpretar, se considera
    que TODAVÍA NO comenzó (por seguridad: mejor tapar los pronósticos de
    más que destaparlos antes de tiempo por un dato faltante o mal
    cargado). Así ningún jugador puede ver el pronóstico del otro antes de
    que arranque el partido.
    """
    fecha_obj = _parsear_fecha(fecha_partido)
    hora_obj = _parsear_hora(hora)
    if fecha_obj is None or hora_obj is None:
        return False
    kickoff = datetime.combine(fecha_obj, hora_obj, tzinfo=TZ_ARG)
    return datetime.now(TZ_ARG) >= kickoff


st.set_page_config(
    page_title="Comparar Boletas",
    layout="centered"
)

st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">

    <style>
    body { font-family: 'DM Sans', sans-serif; color: #f1f5f9; }

    [data-testid="stApp"] {
        background-image: url('https://raw.githubusercontent.com/arcaltdfootball/PRODEFIFAWC2026UNQ/main/prode_supabase/AFA2026.png');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
        background-color: #0b0f19;
    }
    [data-testid="stAppViewContainer"] > div:first-child::before {
        content: '';
        position: fixed;
        inset: 0;
        background: rgba(11,15,25,0.80);
        z-index: 0;
        pointer-events: none;
    }
    [data-testid="stVerticalBlock"] { position: relative; z-index: 1; }

    h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 1px; }

    .main-label {
        font-size: 0.75rem; color: #94a3b8; text-align: center;
        text-transform: uppercase; letter-spacing: 3px; margin-bottom: 4px;
    }
    .main-title {
        font-size: 3.2rem; color: #e8c96b; text-align: center;
        margin-top: 0.2rem; margin-bottom: 0.2rem;
        text-shadow: 0 4px 12px rgba(0,0,0,0.5);
        font-family: 'Bebas Neue', sans-serif;
    }
    .main-subtitle {
        font-size: 0.82rem; color: #64748b; text-align: center;
        margin-bottom: 1.6rem; letter-spacing: 2px; text-transform: uppercase;
    }

    .zona-activa-label {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1rem; color: #e8c96b;
        text-align: center; letter-spacing: 3px;
        margin-bottom: 10px; text-transform: uppercase;
    }
    .seccion-label {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1rem; color: #e8c96b;
        text-align: center; letter-spacing: 3px;
        margin-bottom: 10px; text-transform: uppercase;
    }

    /* FECHA (puntos violetas animados, idéntico a 01_Resultados.py) */
    .fecha-slider-label {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.05rem; color: #e2e8f0; letter-spacing: 3px;
        text-align: center; margin-bottom: 4px;
    }
    .fecha-slider-sub {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.62rem; color: #94a3b8; letter-spacing: 1px;
        text-transform: none;
    }
    .fecha-dots-row {
        display: flex; align-items: center; justify-content: center;
        gap: 5px; flex-wrap: wrap;
    }

    /* CARD COMPARACION */
    .partido-card {
        background: rgba(20,30,50,0.72);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 22px;
        padding: 22px 20px 18px;
        max-width: 580px;
        margin: 0 auto 14px;
        box-shadow: 0 16px 40px rgba(0,0,0,0.35);
    }

    .match-meta {
        font-size: 0.72rem; color: #64748b;
        text-align: center; text-transform: uppercase;
        letter-spacing: 1px; margin-bottom: 14px;
    }
    .match-meta i { color: #e8c96b; margin-right: 3px; }

    .teams-row {
        display: flex; align-items: center;
        justify-content: space-between; gap: 10px;
        margin-bottom: 16px;
    }
    .team-block {
        display: flex; flex-direction: column;
        align-items: center; gap: 8px; flex: 1;
    }
    .escudo-card-img {
        width: 48px; height: 48px; object-fit: contain;
        filter: drop-shadow(0 4px 10px rgba(0,0,0,0.5));
    }
    .team-name { font-size: 0.82rem; font-weight: 600; color: #e2e8f0; text-align: center; }
    .vs-text {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.6rem; color: #e8c96b;
        letter-spacing: 2px; line-height: 1;
    }

    .resultado-real { text-align: center; margin-bottom: 14px; }
    .resultado-pill {
        display: inline-block;
        background: rgba(34,197,94,0.15); color: #4ade80;
        border: 1px solid rgba(34,197,94,0.3);
        border-radius: 20px; padding: 4px 16px;
        font-size: 0.8rem; font-weight: 700;
    }
    .resultado-pill.pending {
        background: rgba(255,255,255,0.04); color: #64748b;
        border: 1px dashed rgba(255,255,255,0.12);
        font-weight: 400;
    }

    /* COMPARACION DE PRONOSTICOS */
    .comp-wrap {
        display: flex; gap: 10px; align-items: stretch;
        margin-bottom: 4px;
    }
    .comp-col {
        flex: 1; border-radius: 14px; padding: 12px 10px 10px;
        text-align: center; position: relative;
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.03);
    }
    .comp-col-nombre {
        font-size: 0.68rem; color: #94a3b8;
        text-transform: uppercase; letter-spacing: 1px;
        margin-bottom: 8px; font-weight: 600;
    }
    .comp-pill {
        display: inline-block;
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.5rem; line-height: 1;
        border-radius: 12px; padding: 6px 18px;
        margin-bottom: 4px;
    }
    .comp-pill.op1 { background: rgba(34,197,94,0.18);  color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .comp-pill.opX { background: rgba(232,201,107,0.16); color: #e8c96b; border: 1px solid rgba(232,201,107,0.3); }
    .comp-pill.op2 { background: rgba(239,68,68,0.18);  color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
    .comp-pill.opn { background: rgba(100,116,139,0.12); color: #475569; border: 1px dashed rgba(100,116,139,0.3); font-size: 1rem; }
    .comp-sub { font-size: 0.66rem; color: #64748b; margin-top: 2px; }

    .comp-card.coinciden { border-color: rgba(34,197,94,0.35); box-shadow: 0 16px 40px rgba(34,197,94,0.08); }
    .comp-card.difieren  { border-color: rgba(239,68,68,0.25); }

    .badge-match {
        text-align: center; margin-bottom: 4px;
    }
    .badge-match span {
        font-size: 0.68rem; font-weight: 700; letter-spacing: 1px;
        text-transform: uppercase; border-radius: 20px; padding: 3px 12px;
        display: inline-block;
    }
    .badge-match .si  { background: rgba(34,197,94,0.18); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .badge-match .no  { background: rgba(239,68,68,0.16); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }

    /* HEADER COMPARACION GENERAL */
    .vs-header {
        display: flex; align-items: center; justify-content: center;
        gap: 18px; margin-bottom: 18px;
    }
    .vs-header-name {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.5rem; color: #fff; text-align: center;
        letter-spacing: 1px;
    }
    .vs-header-vs {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.2rem; color: #e8c96b;
    }

    /* RESUMEN */
    .resumen-wrap {
        display: flex; gap: 10px; margin: 4px auto 20px; max-width: 580px;
    }
    .resumen-box {
        flex: 1; text-align: center; border-radius: 16px;
        padding: 14px 8px; border: 1px solid rgba(255,255,255,0.08);
        background: rgba(20,30,50,0.6);
    }
    .resumen-box .num {
        font-family: 'Bebas Neue', sans-serif; font-size: 2rem; line-height: 1;
    }
    .resumen-box .lbl {
        font-size: 0.66rem; color: #94a3b8; text-transform: uppercase;
        letter-spacing: 1px; margin-top: 4px;
    }
    .resumen-box.verde .num { color: #4ade80; }
    .resumen-box.rojo  .num { color: #f87171; }
    .resumen-box.gris  .num { color: #94a3b8; }

    /* MINI-CARDS DE ESCUDOS PARA NAVEGAR PARTIDOS (idéntico a 01_Resultados.py) */
    .match-card {
        display: flex; align-items: center; justify-content: center; gap: 6px;
        width: 78px; height: 54px; border-radius: 14px;
        background: rgba(15,23,42,0.65);
        border: 1.5px solid rgba(255,255,255,0.10);
        transition: all 0.18s ease;
        margin: 0 auto; position: relative; z-index: 1;
        pointer-events: none;
    }
    .match-card-escudo {
        width: 24px; height: 24px; object-fit: contain;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));
    }
    .match-card-fallback { font-size: 18px; opacity: 0.6; }
    .match-card-vs {
        font-family: 'Bebas Neue', sans-serif; font-size: 0.55rem;
        color: rgba(255,255,255,0.35); letter-spacing: 1px;
    }

    /* PRONÓSTICOS BLOQUEADOS (hasta que arranca el partido, idéntico a
       05_Pronosticos.py) */
    .pron-bloqueado {
        text-align: center;
        background: rgba(255,255,255,0.03);
        border: 1px dashed rgba(255,255,255,0.14);
        border-radius: 16px;
        padding: 22px 16px 20px;
        margin-bottom: 4px;
    }
    .pron-bloqueado .candado {
        font-size: 1.8rem; margin-bottom: 6px; opacity: 0.85;
    }
    .pron-bloqueado .titulo {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.05rem; letter-spacing: 1.5px;
        color: #e2e8f0; margin-bottom: 4px;
    }
    .pron-bloqueado .subtitulo {
        font-size: 0.75rem; color: #64748b;
        letter-spacing: 0.3px; line-height: 1.4;
        max-width: 360px; margin: 0 auto;
    }

    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 2rem; }

    /* TABS PRINCIPALES (Zona A / Zona B / Interzonal) */
    [data-baseweb="tab-list"] {
        gap: 14px;
        background: rgba(20,30,50,0.55);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 20px;
        padding: 10px;
        margin: 0 auto 28px;
        max-width: 640px;
        box-shadow: 0 16px 40px rgba(0,0,0,0.35);
    }
    [data-baseweb="tab"] {
        flex: 1;
        background: rgba(255,255,255,0.03);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 16px 18px !important;
        transition: all 0.25s ease;
    }
    [data-baseweb="tab"] p {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.35rem !important;
        letter-spacing: 1.5px;
        color: #cbd5e1 !important;
    }
    [data-baseweb="tab"]:hover {
        background: rgba(232,201,107,0.10);
        border-color: rgba(232,201,107,0.3);
        transform: translateY(-2px);
    }
    [data-baseweb="tab"][aria-selected="true"] {
        background: rgba(232,201,107,0.18);
        border-color: rgba(232,201,107,0.55);
        box-shadow: 0 8px 24px rgba(232,201,107,0.18);
    }
    [data-baseweb="tab"][aria-selected="true"] p {
        color: #e8c96b !important;
        text-shadow: 0 2px 10px rgba(232,201,107,0.35);
    }
    [data-baseweb="tab-highlight"] { display: none; }
    [data-baseweb="tab-border"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-label">Fixture Oficial</p>', unsafe_allow_html=True)
st.markdown('<h1 class="main-title">COMPARAR BOLETAS</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="main-subtitle">Torneo Clausura 2026 &middot; Liga Profesional Argentina</p>',
    unsafe_allow_html=True,
)

# ── Conexión ────────────────────────────────────────────────────────────────────
try:
    sb = conectar()
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.stop()

# ── Datos (mismo patrón de paginado que 05_Pronosticos.py) ───────────────────────
def fetch_all(table_name, columns, order_cols=None, page_size=1000):
    rows = []
    start = 0
    while True:
        query = sb.table(table_name).select(columns)
        if order_cols:
            for col in order_cols:
                query = query.order(col)
        chunk = query.range(start, start + page_size - 1).execute().data or []
        rows.extend(chunk)
        if len(chunk) < page_size:
            break
        start += page_size
    return rows


partidos_raw = fetch_all("partidos", "*", order_cols=["zona", "fecha_numero"])
jugadores_raw = fetch_all("jugadores", "id, nombre", order_cols=["nombre"])
pronosticos_raw = fetch_all(
    "pronosticos",
    "jugador_id, partido_id, signo_pred, goles_local_pred, goles_visitante_pred, puntos",
)

if not partidos_raw:
    st.info("No hay partidos registrados todavía.")
    st.stop()

if not jugadores_raw or len(jugadores_raw) < 2:
    st.info("Hacen falta al menos dos jugadores registrados para poder comparar boletas.")
    st.stop()

# ── Índices ─────────────────────────────────────────────────────────────────────
jugador_nombre = {str(j["id"]): j["nombre"] for j in jugadores_raw}

# partido_id → {jugador_id: {resultado, goles_local, goles_visitante, puntos}}
pron_por_partido = {}
for pr in pronosticos_raw:
    pid = str(pr["partido_id"])
    uid = str(pr["jugador_id"])
    pron_por_partido.setdefault(pid, {})[uid] = {
        "resultado":       pr.get("signo_pred"),
        "goles_local":     pr.get("goles_local_pred"),
        "goles_visitante": pr.get("goles_visitante_pred"),
        "puntos":          pr.get("puntos"),
    }

# Agrupar partidos por zona → fecha_numero
partidos_por_zona = {}
for p in partidos_raw:
    z = p["zona"]
    f = p["fecha_numero"]
    partidos_por_zona.setdefault(z, {}).setdefault(f, []).append(p)

zonas_lista = sorted(
    partidos_por_zona.keys(),
    key=lambda z: (0 if z == "A" else 1 if z == "B" else 2, z),
)


def etiqueta_zona(z):
    return "Interzonal" if z == "Interzonal" else f"Zona {z}"


VIOLET = "#a78bfa"


def fecha_dot_size(dist):
    """El punto se agranda cuanto más cerca está de la fecha en la que estás parado."""
    if dist == 0: return 24
    if dist == 1: return 18
    if dist == 2: return 13
    if dist == 3: return 10
    return 8


def fecha_dot_color(dist):
    if dist == 0: return VIOLET
    if dist == 1: return "rgba(167,139,250,0.55)"
    if dist == 2: return "rgba(167,139,250,0.30)"
    return "rgba(255,255,255,0.15)"


# ── Escudos ───────────────────────────────────────────────────────────────────────────
def escudo_html(equipo, size=48):
    url = url_escudo(equipo)
    if url:
        return f'<img src="{url}" class="escudo-card-img" style="width:{size}px;height:{size}px;">'
    return '<span style="font-size:34px">🛡️</span>'


# ── Selección de jugadores ─────────────────────────────────────────────────────
nombres_ordenados = sorted(jugador_nombre.values())
nombre_a_id = {}
for jid, nom in jugador_nombre.items():
    nombre_a_id[nom] = jid

st.markdown(
    '<p class="seccion-label">Elegí dos jugadores</p>',
    unsafe_allow_html=True,
)

col_a, col_vs, col_b = st.columns([5, 1, 5])
with col_a:
    nombre_1 = st.selectbox(
        "Jugador 1",
        nombres_ordenados,
        index=0,
        key="cmp_jug_1",
    )
with col_vs:
    st.markdown(
        '<div style="text-align:center;padding-top:32px;'
        'font-family:\'Bebas Neue\',sans-serif;font-size:1.4rem;color:#e8c96b;">VS</div>',
        unsafe_allow_html=True,
    )
with col_b:
    default_idx_2 = 1 if len(nombres_ordenados) > 1 else 0
    nombre_2 = st.selectbox(
        "Jugador 2",
        nombres_ordenados,
        index=default_idx_2,
        key="cmp_jug_2",
    )

comparar = st.button("COMPARAR BOLETAS", use_container_width=True, type="primary")

if "cmp_activo" not in st.session_state:
    st.session_state["cmp_activo"] = False

if comparar:
    if nombre_1 == nombre_2:
        st.warning("Elegí dos jugadores distintos para comparar sus boletas.")
        st.session_state["cmp_activo"] = False
    else:
        st.session_state["cmp_activo"] = True
        st.session_state["cmp_nombre_1"] = nombre_1
        st.session_state["cmp_nombre_2"] = nombre_2


# ── Helper: render resumen ────────────────────────────────────────────────────
def render_resumen(exacto, resultado, difieren, sin_comparar):
    st.markdown(
        '<div class="resumen-wrap">'
        '<div class="resumen-box" style="flex:1;text-align:center;border-radius:16px;padding:14px 8px;'
        'border:1px solid rgba(232,201,107,0.4);background:rgba(232,201,107,0.1);">'
        f'<div class="num" style="font-family:\'Bebas Neue\',sans-serif;font-size:2rem;line-height:1;color:#e8c96b;">{exacto}</div>'
        '<div class="lbl" style="font-size:0.66rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Marcador exacto</div>'
        '</div>'
        '<div class="resumen-box verde" style="flex:1;text-align:center;border-radius:16px;padding:14px 8px;'
        'border:1px solid rgba(34,197,94,0.3);background:rgba(34,197,94,0.08);">'
        f'<div class="num" style="font-family:\'Bebas Neue\',sans-serif;font-size:2rem;line-height:1;color:#4ade80;">{resultado}</div>'
        '<div class="lbl" style="font-size:0.66rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Mismo resultado</div>'
        '</div>'
        '<div class="resumen-box rojo" style="flex:1;text-align:center;border-radius:16px;padding:14px 8px;'
        'border:1px solid rgba(239,68,68,0.25);background:rgba(239,68,68,0.08);">'
        f'<div class="num" style="font-family:\'Bebas Neue\',sans-serif;font-size:2rem;line-height:1;color:#f87171;">{difieren}</div>'
        '<div class="lbl" style="font-size:0.66rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Difieren</div>'
        '</div>'
        '<div class="resumen-box gris" style="flex:1;text-align:center;border-radius:16px;padding:14px 8px;'
        'border:1px solid rgba(255,255,255,0.08);background:rgba(20,30,50,0.6);">'
        f'<div class="num" style="font-family:\'Bebas Neue\',sans-serif;font-size:2rem;line-height:1;color:#94a3b8;">{sin_comparar}</div>'
        '<div class="lbl" style="font-size:0.66rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Sin comparar</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ── Helper: build_card_partido ────────────────────────────────────────────────
def build_card_partido(local, visitante, fecha_partido, hora, estadio, resultado,
                       gl_of, gv_of, v1, gl1, gv1, v2, gl2, gv2,
                       n1_sel, n2_sel, revelado: bool = True):
    # ══════════════════════════════════════════════════════════════════════
    # CANDADO: hasta que el partido no arrancó (o ya se jugó, que implica
    # que arrancó), NO comparamos ni mostramos los pronósticos de cada
    # jugador — así ninguno de los dos puede espiar ni copiarse del otro
    # antes de tiempo. `revelado` ya viene resuelto por quien llama a esta
    # función usando la hora real de Argentina (ver _partido_comenzo).
    # ══════════════════════════════════════════════════════════════════════
    if not revelado:
        v1 = v2 = gl1 = gv1 = gl2 = gv2 = None

    if v1 is not None and v2 is not None and v1 == v2:
        marcador_igual = (
            gl1 is not None and gv1 is not None
            and gl2 is not None and gv2 is not None
            and int(gl1) == int(gl2) and int(gv1) == int(gv2)
        )
        if marcador_igual:
            estado_clase = "coinciden"
            badge_match = (
                '<span style="background:rgba(232,201,107,0.2);color:#e8c96b;'
                'border:1px solid rgba(232,201,107,0.45);border-radius:20px;'
                'padding:3px 12px;font-size:0.68rem;font-weight:700;'
                'letter-spacing:1px;text-transform:uppercase;">'
                '⭐ Marcador exacto igual</span>'
            )
        else:
            estado_clase = "coinciden"
            badge_match = '<span class="si">✓ Mismo resultado</span>'
    elif v1 is not None and v2 is not None:
        estado_clase = "difieren"
        badge_match = '<span class="no">✗ Difieren</span>'
    else:
        estado_clase = ""
        badge_match = ""

    meta_parts = []
    if fecha_partido:
        meta_parts.append(f'<i class="ti ti-calendar-event"></i> {fecha_partido}')
    if hora:
        meta_parts.append(f'<i class="ti ti-clock"></i> {hora}')
    if estadio:
        meta_parts.append(f'<i class="ti ti-map-pin"></i> {estadio}')
    meta_str = "&nbsp;&nbsp;|&nbsp;&nbsp;".join(meta_parts)

    if resultado:
        labels_r = {"1": "Gana " + local, "X": "Empate", "2": "Gana " + visitante}
        if gl_of is not None and gv_of is not None:
            marcador_of = (
                f'<span style="font-family:\'Bebas Neue\',sans-serif;font-size:1.3rem;'
                f'color:#e8c96b;margin:0 6px;">{int(gl_of)} - {int(gv_of)}</span> '
            )
        else:
            marcador_of = ""
        res_html = (
            '<div class="resultado-real"><span class="resultado-pill">⚽ '
            + marcador_of + labels_r.get(resultado, resultado) + "</span></div>"
        )
    else:
        res_html = (
            '<div class="resultado-real">'
            '<span class="resultado-pill pending">Partido no jugado</span></div>'
        )

    def pill_html(valor, gl, gv):
        if gl is not None and gv is not None:
            marcador_str = (
                f'<div style="font-family:\'Bebas Neue\',sans-serif;font-size:1.8rem;'
                f'color:#e8c96b;line-height:1;margin-bottom:2px;">{int(gl)} - {int(gv)}</div>'
            )
        else:
            marcador_str = ""
        if valor == "1":
            return marcador_str + f'<div class="comp-pill op1">1</div><div class="comp-sub">Gana {local}</div>'
        if valor == "X":
            return marcador_str + '<div class="comp-pill opX">X</div><div class="comp-sub">Empate</div>'
        if valor == "2":
            return marcador_str + f'<div class="comp-pill op2">2</div><div class="comp-sub">Gana {visitante}</div>'
        return '<div class="comp-pill opn">—</div><div class="comp-sub">Sin pronóstico</div>'

    if revelado:
        bloque_comparacion = (
            (f'<div class="badge-match">{badge_match}</div>' if badge_match else "")
            + '<div class="comp-wrap">'
            + f'<div class="comp-col"><div class="comp-col-nombre">{n1_sel}</div>{pill_html(v1, gl1, gv1)}</div>'
            + f'<div class="comp-col"><div class="comp-col-nombre">{n2_sel}</div>{pill_html(v2, gl2, gv2)}</div>'
            + "</div>"
        )
    else:
        # Partido todavía no arrancó: tapamos las boletas de ambos
        # jugadores para que ninguno pueda copiarse del otro.
        bloque_comparacion = (
            '<div class="pron-bloqueado">'
            + '<div class="candado">🔒</div>'
            + '<div class="titulo">Boletas ocultas</div>'
            + '<div class="subtitulo">La comparación entre '
            f'{n1_sel} y {n2_sel} se va a revelar automáticamente apenas '
            'arranque el partido.</div>'
            + '</div>'
        )

    return (
        f'<div class="partido-card comp-card {estado_clase}">'
        + (f'<div class="match-meta">{meta_str}</div>' if meta_str else "")
        + '<div class="teams-row">'
        + f'<div class="team-block">{escudo_html(local)}<span class="team-name">{local}</span></div>'
        + '<div><span class="vs-text">VS</span></div>'
        + f'<div class="team-block">{escudo_html(visitante)}<span class="team-name">{visitante}</span></div>'
        + "</div>"
        + res_html
        + '<hr style="border:none;border-top:1px solid rgba(255,255,255,0.07);margin:0 0 12px;">'
        + bloque_comparacion
        + "</div>"
    )


# ── Helper: dots de navegación de partidos (idéntico a 01_Resultados.py) ─────────
def render_dots(idx, total):
    dots_inner = ""
    for i in range(total):
        if i == idx:
            dots_inner += "<div style='width:20px;height:6px;border-radius:3px;background:#e8c96b'></div>"
        else:
            dots_inner += "<div style='width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,0.15)'></div>"
    st.markdown(
        '<div style="display:flex;justify-content:center;gap:6px;align-items:center;'
        'background:rgba(15,23,42,0.5);backdrop-filter:blur(12px);border:1px solid '
        'rgba(255,255,255,0.07);border-radius:14px;padding:10px 20px;max-width:560px;margin:0 auto 4px;">'
        + dots_inner + "</div>"
        + f'<p style="text-align:center;font-size:0.72rem;color:#475569;letter-spacing:1px;margin-top:4px;">'
        f"Partido {idx + 1} de {total}</p>",
        unsafe_allow_html=True,
    )


# ── Resultado de la comparación ───────────────────────────────────────────────
if st.session_state.get("cmp_activo"):
    n1_sel = st.session_state["cmp_nombre_1"]
    n2_sel = st.session_state["cmp_nombre_2"]
    id1 = nombre_a_id.get(n1_sel)
    id2 = nombre_a_id.get(n2_sel)

    st.markdown(
        '<div class="vs-header">'
        f'<div class="vs-header-name">{n1_sel}</div>'
        '<div class="vs-header-vs">VS</div>'
        f'<div class="vs-header-name">{n2_sel}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Resumen general (sobre TODOS los partidos, todas las zonas) ──────────
    # Mismo candado que en la card de cada partido: mientras el partido no
    # arrancó, no se compara (ni se filtra información de) la boleta de
    # ninguno de los dos jugadores.
    coinciden_exacto_n = coinciden_resultado_n = difieren_n = sin_comparar_n = 0
    for p in partidos_raw:
        pid_str = str(p["id"])
        gl_p = p.get("goles_local")
        gv_p = p.get("goles_visitante")
        ya_jugado_p = gl_p is not None and gv_p is not None
        if not (ya_jugado_p or _partido_comenzo(p.get("fecha_partido"), p.get("hora"))):
            sin_comparar_n += 1
            continue

        apuestas = pron_por_partido.get(pid_str, {})
        d1 = apuestas.get(id1)
        d2 = apuestas.get(id2)
        r1 = d1["resultado"] if d1 else None
        r2 = d2["resultado"] if d2 else None
        if r1 is None or r2 is None:
            sin_comparar_n += 1
        elif r1 != r2:
            difieren_n += 1
        else:
            gl1_ = d1.get("goles_local");  gv1_ = d1.get("goles_visitante")
            gl2_ = d2.get("goles_local");  gv2_ = d2.get("goles_visitante")
            if (gl1_ is not None and gv1_ is not None
                    and gl2_ is not None and gv2_ is not None
                    and int(gl1_) == int(gl2_) and int(gv1_) == int(gv2_)):
                coinciden_exacto_n += 1
            else:
                coinciden_resultado_n += 1

    render_resumen(coinciden_exacto_n, coinciden_resultado_n, difieren_n, sin_comparar_n)

    # ════════════════════════════════════════════════════════════════════════
    # TABS: Zona A / Zona B / Interzonal (idéntico a 01_Resultados.py / 05_Pronosticos.py)
    # ════════════════════════════════════════════════════════════════════════
    tabs_zona = st.tabs([etiqueta_zona(z) for z in zonas_lista])

    for tab, zona in zip(tabs_zona, zonas_lista):
        with tab:
            fechas_zona = sorted(partidos_por_zona[zona].keys(), key=int)

            key_fecha = f"cmp_fecha_{zona}"
            if key_fecha not in st.session_state:
                st.session_state[key_fecha] = fechas_zona[0]
            if st.session_state[key_fecha] not in fechas_zona:
                st.session_state[key_fecha] = fechas_zona[0]

            st.markdown(
                f'<p class="zona-activa-label">{etiqueta_zona(zona)}</p>',
                unsafe_allow_html=True,
            )

            fecha_idx = fechas_zona.index(st.session_state[key_fecha])

            # ── Selector de fecha: puntos violetas animados ──────────────────
            with st.container(key=f"cmp_fecha_wrap_{zona}"):
                st.markdown(
                    f'<div class="fecha-slider-label">FECHA {st.session_state[key_fecha]}'
                    f'<div class="fecha-slider-sub">estás parado acá</div></div>',
                    unsafe_allow_html=True
                )

                fecha_cols = st.columns(len(fechas_zona))
                for i, f in enumerate(fechas_zona):
                    with fecha_cols[i]:
                        if st.button("●", key=f"cmp_fdot_{zona}_{f}", help=f"Ir a la fecha {f}"):
                            st.session_state[key_fecha] = f
                            st.session_state[f"cmp_idx_{zona}_{f}"] = 0
                            st.rerun()

            _fecha_rules = []
            for i, f in enumerate(fechas_zona):
                dist = abs(i - fecha_idx)
                size = fecha_dot_size(dist)
                color = fecha_dot_color(dist)
                is_active = (dist == 0)
                glow = "box-shadow: 0 0 16px rgba(167,139,250,0.85) !important;" if is_active else "box-shadow: none !important;"
                border = "border: 2px solid rgba(255,255,255,0.9) !important;" if is_active else "border: none !important;"
                btn_key = f"cmp_fdot_{zona}_{f}"
                _fecha_rules.append(
                    f'.st-key-{btn_key} button {{ '
                    f'width:{size}px !important; height:{size}px !important; '
                    f'min-height:0 !important; min-width:0 !important; '
                    f'border-radius:50% !important; padding:0 !important; '
                    f'background:{color} !important; color:transparent !important; '
                    f'{border} {glow} transition: all 0.2s ease; margin:0 auto !important; }}'
                )

            st.markdown(
                f"""
                <style>
                .st-key-cmp_fecha_wrap_{zona} {{
                    max-width: 580px; margin: 0 auto 6px;
                    background: rgba(15,23,42,0.55);
                    backdrop-filter: blur(14px);
                    border: 1px solid rgba(255,255,255,0.07);
                    border-radius: 18px;
                    padding: 18px 24px 16px;
                }}
                div[data-testid="stHorizontalBlock"]:has([class*="st-key-cmp_fdot_{zona}_"]) {{
                    gap: 6px !important; align-items: center !important;
                    flex-wrap: wrap !important; justify-content: center !important;
                }}
                {"".join(_fecha_rules)}
                [class*="st-key-cmp_fdot_{zona}_"] button:hover {{
                    transform: scale(1.3) !important;
                    background: {VIOLET} !important;
                }}
                [class*="st-key-cmp_fdot_{zona}_"] button p {{ visibility: hidden; }}
                </style>
                """,
                unsafe_allow_html=True
            )

            st.markdown("<div style='margin-top:6px'></div>", unsafe_allow_html=True)

            fecha_sel = st.session_state[key_fecha]

            lista_part = sorted(
                partidos_por_zona[zona][fecha_sel],
                key=lambda p: (p.get("fecha_partido") or "9999-99-99", p.get("hora") or "99:99"),
            )
            total = len(lista_part)

            key_idx = f"cmp_idx_{zona}_{fecha_sel}"
            if key_idx not in st.session_state:
                st.session_state[key_idx] = 0
            idx = st.session_state[key_idx]
            if idx >= total:
                idx = 0
                st.session_state[key_idx] = 0

            # ── Selección de partido con mini-cards de escudos (idéntico a
            # 01_Resultados.py / 05_Pronosticos.py) ──────────────────────────
            dot_cols = st.columns(total)
            _card_keys = []
            for i, part in enumerate(lista_part):
                with dot_cols[i]:
                    esc_l = url_escudo(part["equipo_local"])
                    esc_v = url_escudo(part["equipo_visitante"])
                    es_actual = (i == idx)

                    img_l = (
                        f'<img src="{esc_l}" class="match-card-escudo">'
                        if esc_l else '<span class="match-card-fallback">🛡️</span>'
                    )
                    img_v = (
                        f'<img src="{esc_v}" class="match-card-escudo">'
                        if esc_v else '<span class="match-card-fallback">🛡️</span>'
                    )

                    btn_key = f"cmp_sel_{zona}_{fecha_sel}_{i}"
                    _card_keys.append(btn_key)

                    with st.container(key=f"cardwrap_{btn_key}"):
                        st.markdown(
                            f'<div class="match-card {"active" if es_actual else ""}">'
                            f'{img_l}<span class="match-card-vs">vs</span>{img_v}'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        help_txt = f"{part['equipo_local']} vs {part['equipo_visitante']}"
                        if part.get("hora"):
                            help_txt += f" · {part['hora']}"
                        if st.button(" ", key=btn_key, help=help_txt):
                            st.session_state[key_idx] = i
                            st.rerun()

            # CSS: reseteamos a "static" todo lo interno del wrapper (Streamlit
            # le pone "position: relative" a sus propios divs, lo que rompía el
            # área de click si no se neutraliza) y recién ahí el botón se
            # estira con position:absolute/inset:0 para cubrir TODO el recuadro.
            _card_rules = []
            for btn_key in _card_keys:
                _card_rules.append(f'.st-key-cardwrap_{btn_key} * {{ position: static !important; }}')
                _card_rules.append(
                    f'.st-key-cardwrap_{btn_key} {{ '
                    f'position: relative !important; width: 78px !important; margin: 0 auto !important; '
                    f'cursor: pointer !important; }}'
                )
                _card_rules.append(
                    f'.st-key-cardwrap_{btn_key} [data-testid="stButton"] {{ '
                    f'position: absolute !important; inset: 0 !important; '
                    f'width: 100% !important; height: 100% !important; z-index: 5 !important; }}'
                )
                _card_rules.append(
                    f'.st-key-cardwrap_{btn_key} button {{ '
                    f'position: absolute !important; inset: 0 !important; '
                    f'width: 100% !important; height: 100% !important; min-height: 0 !important; '
                    f'padding: 0 !important; background: transparent !important; '
                    f'border: none !important; opacity: 0 !important; cursor: pointer !important; }}'
                )

            active_card_style = (
                f'background: rgba(167,139,250,0.20) !important; '
                f'border-color: {VIOLET} !important; '
                f'box-shadow: 0 0 0 2px {VIOLET}55, 0 6px 16px rgba(167,139,250,0.35) !important; '
                f'transform: scale(1.06) !important;'
            )

            st.markdown(
                f"""
                <style>
                div[data-testid="stHorizontalBlock"]:has([class*="st-key-cardwrap_"]) {{
                    gap: 8px !important; align-items: flex-start !important;
                    flex-wrap: wrap !important; justify-content: center !important;
                }}
                .match-card.active {{ {active_card_style} }}
                [class*="st-key-cardwrap_"]:hover .match-card {{
                    border-color: {VIOLET}; transform: scale(1.04);
                }}
                {"".join(_card_rules)}
                </style>
                """,
                unsafe_allow_html=True
            )

            # ── Prev / next (arriba) ──────────────────────────────────────────
            _, col_prev_top, _, col_next_top, _ = st.columns([1, 1, 4, 1, 1])
            with col_prev_top:
                if st.button("◀", key=f"cmp_prev_top_{zona}_{fecha_sel}", disabled=(idx == 0)):
                    st.session_state[key_idx] = idx - 1
                    st.rerun()
            with col_next_top:
                if st.button("▶", key=f"cmp_next_top_{zona}_{fecha_sel}", disabled=(idx == total - 1)):
                    st.session_state[key_idx] = idx + 1
                    st.rerun()

            # ── Card de comparación del partido actual ────────────────────────
            p = lista_part[idx]
            p_id      = p["id"]
            local     = p["equipo_local"]
            visitante = p["equipo_visitante"]
            fecha_part= p.get("fecha_partido")
            hora      = p.get("hora")
            estadio   = p.get("estadio")
            gl_of     = p.get("goles_local")
            gv_of     = p.get("goles_visitante")

            resultado_of = None
            if gl_of is not None and gv_of is not None:
                if gl_of > gv_of:   resultado_of = "1"
                elif gl_of == gv_of: resultado_of = "X"
                else:                resultado_of = "2"

            apuestas   = pron_por_partido.get(str(p_id), {})
            pron1 = apuestas.get(id1)
            pron2 = apuestas.get(id2)

            ya_jugado = gl_of is not None and gv_of is not None
            revelado = ya_jugado or _partido_comenzo(fecha_part, hora)

            card = build_card_partido(
                local, visitante, fecha_part, hora, estadio,
                resultado_of, gl_of, gv_of,
                pron1["resultado"]       if pron1 else None,
                pron1["goles_local"]     if pron1 else None,
                pron1["goles_visitante"] if pron1 else None,
                pron2["resultado"]       if pron2 else None,
                pron2["goles_local"]     if pron2 else None,
                pron2["goles_visitante"] if pron2 else None,
                n1_sel, n2_sel,
                revelado=revelado,
            )
            st.markdown(card, unsafe_allow_html=True)

            render_dots(idx, total)

            _, col_prev, _, col_next, _ = st.columns([1, 1, 4, 1, 1])
            with col_prev:
                if st.button("◀", key=f"cmp_prev_{zona}_{fecha_sel}", disabled=(idx == 0)):
                    st.session_state[key_idx] = idx - 1
                    st.rerun()
            with col_next:
                if st.button("▶", key=f"cmp_next_{zona}_{fecha_sel}", disabled=(idx == total - 1)):
                    st.session_state[key_idx] = idx + 1
                    st.rerun()

else:
    st.info("Elegí dos jugadores y tocá **Comparar boletas** para ver la comparación partido por partido.")
