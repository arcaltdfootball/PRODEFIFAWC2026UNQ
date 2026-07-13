import json
import os

import streamlit as st
from database import conectar

st.set_page_config(
    page_title="Resultados",
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
        background-image: url('https://raw.githubusercontent.com/arcaltdfootball/PRODEFIFAWC2026UNQ/main/prode_supabase/FIFAWorldbakcgound.jpg');
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
        background: rgba(11,15,25,0.78);
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
        font-size: 0.9rem; color: #64748b; text-align: center;
        margin-bottom: 1.4rem; letter-spacing: 2px; text-transform: uppercase;
    }

    .outer-card {
        background: rgba(20,30,50,0.55);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 28px;
        padding: 28px 24px 20px;
        box-shadow: 0 24px 48px rgba(0,0,0,0.4);
        max-width: 560px;
        margin: 0 auto 16px;
    }
    .match-meta {
        text-align: center; font-size: 0.75rem; color: #64748b;
        margin-bottom: 18px; text-transform: uppercase; letter-spacing: 1px;
    }
    .match-meta i { color: #e8c96b; margin-right: 3px; }

    .match-inner {
        background: rgba(10,18,35,0.7);
        border-radius: 20px;
        padding: 22px 20px 18px;
        border: 1px solid rgba(255,255,255,0.05);
        margin-bottom: 16px;
    }
    .teams-row {
        display: flex; align-items: center;
        justify-content: space-between; gap: 10px;
    }
    .team-block {
        display: flex; flex-direction: column;
        align-items: center; gap: 10px; flex: 1;
    }
    .escudo-img {
        width: 56px; height: 56px; object-fit: contain;
        border-radius: 12px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.4);
        background: rgba(255,255,255,0.06);
        border: 2px solid rgba(255,255,255,0.12);
        padding: 4px;
    }
    .team-name { font-size: 0.9rem; font-weight: 500; color: #e2e8f0; text-align: center; }
    .score-block { display: flex; flex-direction: column; align-items: center; min-width: 60px; }
    .score-number { font-family: 'Bebas Neue', sans-serif; font-size: 2rem; color: #94a3b8; line-height: 1; }
    .score-number.big { font-size: 3rem; color: #e8c96b; text-shadow: 0 2px 10px rgba(232,201,107,0.35); }
    .score-sep { font-family: 'Bebas Neue', sans-serif; font-size: 2.2rem; color: #64748b; margin: 0 4px; line-height: 1; }
    .score-live-row { display: flex; align-items: center; justify-content: center; }

    .result-bar {
        background: #22c55e; color: white; padding: 13px;
        border-radius: 14px; text-align: center;
        font-weight: 700; font-size: 1rem;
        max-width: 560px; margin: 0 auto 16px;
        letter-spacing: 0.5px;
    }
    .result-bar.empate {
        background: #64748b;
    }
    .result-bar.pending {
        background: rgba(255,255,255,0.05); color: #64748b;
        border: 1px dashed rgba(255,255,255,0.1);
        font-weight: 400; font-size: 0.9rem;
    }

    .nav-wrapper {
        background: rgba(15,23,42,0.6);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 16px; padding: 12px 20px;
        display: flex; align-items: center;
        justify-content: center; gap: 16px;
        max-width: 560px; margin: 0 auto 6px;
    }
    .dots-row { display: flex; justify-content: center; gap: 6px; align-items: center; flex: 1; }
    .nav-counter {
        font-size: 0.75rem; color: #475569;
        text-align: center; margin-top: 4px; letter-spacing: 1px;
    }

    .zona-activa-label {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1rem;
        color: #e8c96b;
        text-align: center;
        letter-spacing: 3px;
        margin-bottom: 10px;
        text-transform: uppercase;
    }

    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<p class="main-label">Fixture Oficial</p>', unsafe_allow_html=True)
st.markdown('<h1 class="main-title">RESULTADOS</h1>', unsafe_allow_html=True)
st.markdown('<p class="main-subtitle">Torneo Clausura 2026 &middot; Liga Profesional Argentina</p>', unsafe_allow_html=True)

try:
    sb = conectar()
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.stop()

# ── Escudos: mapeo entre el nombre "corto" usado en la base (equipos /
# partidos) y el nombre "lindo" que generó escudos_prode.py en escudos.json ──
ALIAS_ESCUDOS = {
    "Boca": "Boca Juniors",
    "River": "River Plate",
    "Racing": "Racing Club",
    "Independiente": "Independiente",
    "San Lorenzo": "San Lorenzo",
    "Huracán": "Huracán",
    "Vélez": "Vélez Sarsfield",
    "Estudiantes": "Estudiantes (LP)",
    "Gimnasia": "Gimnasia y Esgrima (LP)",
    "Newell's": "Newell's Old Boys",
    "Rosario Central": "Rosario Central",
    "Talleres": "Talleres (Córdoba)",
    "Belgrano": "Belgrano (Córdoba)",
    "Instituto": "Instituto (Córdoba)",
    "Argentinos": "Argentinos Juniors",
    "Platense": "Platense",
    "Banfield": "Banfield",
    "Lanús": "Lanús",
    "Tigre": "Tigre",
    "Barracas Central": "Barracas Central",
    "Central Córdoba": "Central Córdoba (SdE)",
    "Independiente Rivadavia": "Independiente Rivadavia",
    "Gimnasia (Mza.)": "Gimnasia y Esgrima (Mza)",
    "Deportivo Riestra": "Deportivo Riestra",
    "Unión": "Unión (Santa Fe)",
    "Sarmiento": "Sarmiento (Junín)",
    "Atlético Tucumán": "Atlético Tucumán",
    "Aldosivi": "Aldosivi",
    "Estudiantes (Río Cuarto)": "Estudiantes (Río Cuarto)",
    "Defensa y Justicia": "Defensa y Justicia",
}

# Posibles ubicaciones del escudos.json generado por escudos_prode.py
_RUTAS_ESCUDOS_JSON = [
    "escudos.json",
    os.path.join(os.path.dirname(__file__), "escudos.json"),
    os.path.join(os.path.dirname(__file__), "..", "escudos.json"),
]


@st.cache_data(ttl=3600)
def cargar_escudos_json():
    for ruta in _RUTAS_ESCUDOS_JSON:
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return {}


def get_escudo(nombre_equipo: str) -> str | None:
    """Devuelve la URL del escudo para un nombre de equipo tal como
    aparece en las tablas 'equipos'/'partidos' (ej. 'Boca', 'River')."""
    escudos = cargar_escudos_json()
    if not escudos:
        return None
    nombre_lindo = ALIAS_ESCUDOS.get(nombre_equipo, nombre_equipo)
    dato = escudos.get(nombre_lindo)
    if isinstance(dato, dict):
        return dato.get("url")
    if isinstance(dato, str):
        return dato
    return None


# ── Carga de partidos (con caché de corta duración) ──────────────────────────
@st.cache_data(ttl=30)
def cargar_partidos():
    return conectar().table("partidos").select("*").execute().data


try:
    partidos_db = cargar_partidos()
except Exception as e:
    st.error(
        "No se pudo leer la tabla 'partidos' desde Supabase.\n\n"
        "Causas más comunes:\n"
        "- La tabla no existe todavía o está vacía (correr schema_prode.sql "
        "y cargar el CSV partidos_clausura_2026.csv).\n"
        "- Row Level Security (RLS) está activado en 'partidos' pero no hay "
        "una policy de SELECT para el rol 'anon'.\n\n"
        f"Detalle técnico: {e}"
    )
    st.stop()

if not partidos_db:
    st.info("No hay partidos registrados todavía.")
    st.stop()

# ── Agrupar por zona y, dentro de cada zona, por fecha_numero ───────────────
partidos_por_zona = {}
for p in partidos_db:
    z = p["zona"]
    partidos_por_zona.setdefault(z, {})
    f = p["fecha_numero"]
    partidos_por_zona[z].setdefault(f, [])
    partidos_por_zona[z][f].append(p)

# Orden de zonas: A, B y cualquier otra (ej. "Interzonal") al final
zonas_disponibles = sorted(
    partidos_por_zona.keys(),
    key=lambda z: (0 if z == "A" else 1 if z == "B" else 2, z)
)

if "zona_activa" not in st.session_state:
    st.session_state["zona_activa"] = zonas_disponibles[0]

# ── Selector de zona ─────────────────────────────────────────────────────────
cols_zona = st.columns(len(zonas_disponibles))
for i, z in enumerate(zonas_disponibles):
    with cols_zona[i]:
        es_activa = (z == st.session_state["zona_activa"])
        etiqueta = "Interzonal" if z == "Interzonal" else f"Zona {z}"
        if st.button(etiqueta, key=f"zona_btn_{z}", use_container_width=True,
                     type="primary" if es_activa else "secondary"):
            st.session_state["zona_activa"] = z
            st.rerun()

zona_sel = st.session_state["zona_activa"]
etiqueta_zona = "INTERZONAL" if zona_sel == "Interzonal" else f"ZONA {zona_sel}"
st.markdown(
    f'<p class="zona-activa-label">{etiqueta_zona}</p>',
    unsafe_allow_html=True
)

# ── Selector de fecha (jornada) dentro de la zona activa ─────────────────────
fechas_disponibles = sorted(partidos_por_zona[zona_sel].keys(), key=int)

key_fecha = f"fecha_activa_{zona_sel}"
if key_fecha not in st.session_state:
    st.session_state[key_fecha] = fechas_disponibles[0]
if st.session_state[key_fecha] not in fechas_disponibles:
    st.session_state[key_fecha] = fechas_disponibles[0]

if len(fechas_disponibles) > 1:
    fecha_sel = st.select_slider(
        "Fecha",
        options=fechas_disponibles,
        value=st.session_state[key_fecha],
        format_func=lambda f: f"Fecha {f}",
        key=f"slider_{zona_sel}",
        label_visibility="collapsed",
    )
    if fecha_sel != st.session_state[key_fecha]:
        st.session_state[key_fecha] = fecha_sel
        st.session_state[f"idx_{zona_sel}_{fecha_sel}"] = 0
else:
    fecha_sel = fechas_disponibles[0]

st.markdown("<br>", unsafe_allow_html=True)

# ── Lista de partidos de la zona + fecha seleccionadas ───────────────────────
lista_partidos = sorted(
    partidos_por_zona[zona_sel][fecha_sel],
    key=lambda p: (p.get("fecha_partido") or "9999-99-99", p.get("hora") or "99:99")
)
total = len(lista_partidos)

key_idx = f"idx_{zona_sel}_{fecha_sel}"
if key_idx not in st.session_state:
    st.session_state[key_idx] = 0
idx = st.session_state[key_idx]
if idx >= total:
    idx = 0
    st.session_state[key_idx] = 0

partido = lista_partidos[idx]

local = partido["equipo_local"]
visitante = partido["equipo_visitante"]
fecha_partido = partido.get("fecha_partido")
hora = partido.get("hora")
estadio = partido.get("estadio")
estado = partido.get("estado") or "a_confirmar"
gl = partido.get("goles_local")
gv = partido.get("goles_visitante")

escudo_local_url = get_escudo(local)
escudo_visitante_url = get_escudo(visitante)

escudo_local_html = (
    '<img src="' + escudo_local_url + '" class="escudo-img">'
    if escudo_local_url else '<span style="font-size:48px">🛡️</span>'
)
escudo_visitante_html = (
    '<img src="' + escudo_visitante_url + '" class="escudo-img">'
    if escudo_visitante_url else '<span style="font-size:48px">🛡️</span>'
)

partido_jugado = gl is not None and gv is not None

if partido_jugado:
    score_center_html = (
        '<div class="score-live-row">'
        '<span class="score-number big">' + str(gl) + '</span>'
        '<span class="score-sep">-</span>'
        '<span class="score-number big">' + str(gv) + '</span>'
        '</div>'
    )
    if gl > gv:
        result_bar_html = '<div class="result-bar">Ganó ' + local + '</div>'
    elif gv > gl:
        result_bar_html = '<div class="result-bar">Ganó ' + visitante + '</div>'
    else:
        result_bar_html = '<div class="result-bar empate">Empate</div>'
else:
    score_center_html = '<span class="score-number">VS</span>'
    if estado == "confirmado":
        result_bar_html = '<div class="result-bar pending">Partido Confirmado &middot; No Jugado</div>'
    else:
        result_bar_html = '<div class="result-bar pending">Fecha y Hora a Confirmar</div>'

# ── Meta del partido (fecha / hora / estadio), solo lo que esté cargado ──────
meta_parts = []
if fecha_partido:
    meta_parts.append('<i class="ti ti-calendar-event"></i> ' + str(fecha_partido))
if hora:
    meta_parts.append('<i class="ti ti-clock"></i> ' + str(hora))
if estadio:
    meta_parts.append('<i class="ti ti-map-pin"></i> ' + str(estadio))
if not meta_parts:
    meta_parts.append('<i class="ti ti-calendar-event"></i> A confirmar')
meta_str = "&nbsp;&nbsp;|&nbsp;&nbsp;".join(meta_parts)

# ── OUTER CARD ─────────────────────────────────────────────────────────────────
outer_card = (
    '<div class="outer-card">'
    '<div class="match-meta">' + meta_str + '</div>'
    '<div class="match-inner">'
    '<div class="teams-row">'
    '<div class="team-block">' + escudo_local_html + '<span class="team-name">' + local + '</span></div>'
    '<div class="score-block">' + score_center_html + '</div>'
    '<div class="team-block">' + escudo_visitante_html + '<span class="team-name">' + visitante + '</span></div>'
    '</div>'
    '</div>'
    '</div>'
)
st.markdown(outer_card, unsafe_allow_html=True)
st.markdown(result_bar_html, unsafe_allow_html=True)

# ── NAVEGACIÓN ─────────────────────────────────────────────────────────────────
dots_inner = ""
for i in range(total):
    if i == idx:
        dots_inner += "<div style='width:20px;height:6px;border-radius:3px;background:#e8c96b'></div>"
    else:
        dots_inner += "<div style='width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,0.15)'></div>"

dots_html = (
    '<div class="nav-wrapper">'
    '<div class="dots-row">' + dots_inner + '</div>'
    '</div>'
    '<p class="nav-counter">Partido ' + str(idx + 1) + ' de ' + str(total) + ' &middot; Fecha ' + str(fecha_sel) + '</p>'
)
st.markdown(dots_html, unsafe_allow_html=True)

_, col_prev, _, col_next, _ = st.columns([1, 1, 4, 1, 1])
with col_prev:
    if st.button("◀", key="prev_btn", disabled=(idx == 0)):
        st.session_state[key_idx] = idx - 1
        st.rerun()
with col_next:
    if st.button("▶", key="next_btn", disabled=(idx == total - 1)):
        st.session_state[key_idx] = idx + 1
        st.rerun()
