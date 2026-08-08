"""
05_Pronosticos.py — Prode Liga Profesional Argentina (Torneo Clausura 2026)

Muestra, partido por partido, el listado de pronósticos que cargó cada
jugador: cuántos apostaron a Local/Empate/Visitante, con qué marcador
exacto, y el resultado real una vez jugado.

Usa el MISMO esquema de datos que 01_Resultados.py y 03_Fixture.py:
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

# Mismos formatos aceptados que en 03_Boleta_digital.py, para bancar cómo
# sea que esté cargado el dato en la base (texto libre, date/time de
# Postgres, etc.)
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
    cargado). Así nadie puede ver ni copiar el pronóstico de otro
    participante antes de que arranque el partido.
    """
    fecha_obj = _parsear_fecha(fecha_partido)
    hora_obj = _parsear_hora(hora)
    if fecha_obj is None or hora_obj is None:
        return False
    kickoff = datetime.combine(fecha_obj, hora_obj, tzinfo=TZ_ARG)
    return datetime.now(TZ_ARG) >= kickoff


st.set_page_config(
    page_title="Pronósticos por Partido",
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

    /* CARD PARTIDO */
    .partido-card {
        background: rgba(20,30,50,0.72);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 22px;
        padding: 22px 20px 18px;
        max-width: 580px;
        margin: 0 auto 20px;
        box-shadow: 0 16px 40px rgba(0,0,0,0.35);
    }

    /* META */
    .match-meta {
        font-size: 0.72rem; color: #64748b;
        text-align: center; text-transform: uppercase;
        letter-spacing: 1px; margin-bottom: 14px;
    }
    .match-meta i { color: #e8c96b; margin-right: 3px; }

    /* EQUIPOS */
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
        width: 56px; height: 56px; object-fit: contain;
        filter: drop-shadow(0 4px 10px rgba(0,0,0,0.5));
    }
    .team-name { font-size: 0.88rem; font-weight: 600; color: #e2e8f0; text-align: center; }
    .vs-text {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.8rem; color: #e8c96b;
        letter-spacing: 2px; line-height: 1;
    }

    /* RESULTADO REAL */
    .resultado-real {
        text-align: center; margin-bottom: 14px;
    }
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

    /* BARRA CONTEO */
    .conteo-titulo {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 0.85rem; color: #94a3b8;
        text-transform: uppercase; letter-spacing: 2px;
        margin-bottom: 10px; text-align: center;
    }
    .barra-wrap {
        display: flex; gap: 6px; align-items: stretch;
        margin-bottom: 12px;
    }
    .barra-opcion {
        flex: 1; border-radius: 12px; padding: 10px 8px 8px;
        text-align: center; position: relative;
        border: 1px solid rgba(255,255,255,0.07);
    }
    .barra-opcion.op1  { background: rgba(34,197,94,0.12);  border-color: rgba(34,197,94,0.25); }
    .barra-opcion.opX  { background: rgba(232,201,107,0.10); border-color: rgba(232,201,107,0.25); }
    .barra-opcion.op2  { background: rgba(239,68,68,0.12);  border-color: rgba(239,68,68,0.25); }
    .barra-label {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.4rem; line-height: 1;
    }
    .barra-opcion.op1 .barra-label  { color: #4ade80; }
    .barra-opcion.opX .barra-label  { color: #e8c96b; }
    .barra-opcion.op2 .barra-label  { color: #f87171; }
    .barra-sublabel {
        font-size: 0.68rem; color: #94a3b8;
        margin-top: 2px; margin-bottom: 6px;
    }
    .barra-count {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2.4rem; line-height: 1;
        color: #fff;
    }
    .barra-pct {
        font-size: 0.72rem; color: #64748b; margin-top: 1px;
    }

    /* NOMBRES DE APOSTADORES */
    .apostadores-wrap {
        margin-top: 4px;
    }
    .chips-row {
        display: flex; flex-wrap: wrap; gap: 5px;
        justify-content: center; margin-top: 5px;
    }
    .chip {
        font-size: 0.72rem; font-family: 'DM Sans', sans-serif;
        font-weight: 600; border-radius: 20px;
        padding: 3px 10px;
    }
    .chip.c1 { background: rgba(34,197,94,0.18);  color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .chip.cX { background: rgba(232,201,107,0.15); color: #e8c96b; border: 1px solid rgba(232,201,107,0.3); }
    .chip.c2 { background: rgba(239,68,68,0.18);  color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
    .chip.cn { background: rgba(100,116,139,0.12); color: #475569; border: 1px dashed rgba(100,116,139,0.3); }

    /* CHIP CON MARCADOR DEBAJO */
    .chip-stack {
        display: flex; flex-direction: column; align-items: center; gap: 2px;
    }
    .chip-marcador {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 0.78rem; letter-spacing: 0.5px;
        color: #94a3b8;
    }
    .chip-marcador.acerto  { color: #4ade80; }
    .chip-marcador.erro    { color: #f87171; }

    /* SIN APUESTAS */
    .sin-apuestas {
        text-align: center; color: #475569; font-size: 0.8rem;
        padding: 8px 0 4px; letter-spacing: 0.5px;
    }

    /* PRONÓSTICOS BLOQUEADOS (hasta que arranca el partido) */
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

    /* ZONA LABEL */
    .zona-activa-label {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1rem; color: #e8c96b;
        text-align: center; letter-spacing: 3px;
        margin-bottom: 10px; text-transform: uppercase;
    }
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
st.markdown('<h1 class="main-title">PRONÓSTICOS</h1>', unsafe_allow_html=True)
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

# ── Datos ───────────────────────────────────────────────────────────────────────
# Supabase/PostgREST limita cada consulta a un máximo de 1000 filas por defecto.
# Con muchos jugadores y partidos, la tabla "pronosticos" puede superar esa
# cantidad de filas, así que sin paginar se perderían pronósticos reales y
# aparecerían como "Sin pronóstico" aunque el jugador sí había apostado.
# Esta función trae TODAS las filas, pidiendo de a "page_size" por vez.
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
    "jugador_id, partido_id, signo_pred, goles_local_pred, goles_visitante_pred, puntos, sin_marcador",
)

if not partidos_raw:
    st.info("No hay partidos registrados todavía.")
    st.stop()

if not jugadores_raw:
    st.info("Todavía no hay jugadores registrados.")
    st.stop()

# ── Índices ─────────────────────────────────────────────────────────────────────
jugador_nombre = {str(j["id"]): j["nombre"] for j in jugadores_raw}
total_jugadores = len(jugadores_raw)

# partido_id → {jugador_id: fila de pronóstico}
pron_por_partido = {}
for pr in pronosticos_raw:
    pid = str(pr["partido_id"])
    uid = str(pr["jugador_id"])
    pron_por_partido.setdefault(pid, {})[uid] = pr

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
def escudo_html(equipo, size=56):
    url = url_escudo(equipo)
    if url:
        return f'<img src="{url}" class="escudo-card-img" style="width:{size}px;height:{size}px;">'
    return '<span style="font-size:40px">🛡️</span>'


# ── Helper: chips HTML ───────────────────────────────────────────────────────────
def chips_html(nombres_dict, cls, marcadores=None, acierto_map=None):
    if not nombres_dict:
        return '<div class="sin-apuestas">—</div>'
    marcadores = marcadores or {}
    acierto_map = acierto_map or {}
    chips = []
    for uid, nom in sorted(nombres_dict.items(), key=lambda x: x[1]):
        marcador = marcadores.get(uid)
        if marcador:
            acierto = acierto_map.get(uid)  # True / False / None (pendiente)
            marcador_cls = "acerto" if acierto is True else ("erro" if acierto is False else "")
            chips.append(
                f'<div class="chip-stack">'
                f'<span class="chip {cls}">{nom}</span>'
                f'<span class="chip-marcador {marcador_cls}">{marcador}</span>'
                f'</div>'
            )
        else:
            chips.append(f'<span class="chip {cls}">{nom}</span>')
    return '<div class="chips-row">' + "".join(chips) + "</div>"


# ── Helper: render card de partido ───────────────────────────────────────────────
def render_card_partido(local, visitante, fecha_partido, hora, estadio,
                         gl_real, gv_real, apuestas_dict, comenzo: bool):
    ya_jugado = gl_real is not None and gv_real is not None

    # ══════════════════════════════════════════════════════════════════════
    # CANDADO: hasta que el partido no arrancó (o ya se jugó, que implica
    # que arrancó), NO calculamos ni mostramos nada de quién apostó a qué
    # — así nadie puede espiar ni copiar el pronóstico de otro participante
    # antes de tiempo. `comenzo` ya viene resuelto por quien llama a esta
    # función usando la hora real de Argentina (ver _partido_comenzo).
    # ══════════════════════════════════════════════════════════════════════
    revelado = comenzo or ya_jugado

    votos_1 = {}
    votos_X = {}
    votos_2 = {}
    marcador_de = {}
    acierto_de = {}
    signo_real = None
    if ya_jugado:
        if gl_real > gv_real:
            signo_real = "1"
        elif gl_real == gv_real:
            signo_real = "X"
        else:
            signo_real = "2"

    # El CONTEO (cuántos apostaron a 1/X/2) se calcula siempre, esté o no
    # revelado el partido: no expone quién apostó qué, sólo cuántos, así
    # que no hay riesgo de que alguien se copie. Los NOMBRES (votos_1,
    # votos_X, votos_2, marcadores, aciertos) sólo se completan cuando
    # `revelado` es True.
    n1 = n2 = nX = 0
    for uid, pr in apuestas_dict.items():
        signo = pr.get("signo_pred")
        if signo not in ("1", "X", "2"):
            continue
        if signo == "1":
            n1 += 1
        elif signo == "X":
            nX += 1
        else:
            n2 += 1

        if revelado:
            gl_p = pr.get("goles_local_pred")
            gv_p = pr.get("goles_visitante_pred")
            sin_marc = bool(pr.get("sin_marcador"))
            if gl_p is not None and gv_p is not None and not sin_marc:
                marcador_de[uid] = f"{gl_p}-{gv_p}"
                if ya_jugado:
                    acierto_de[uid] = (gl_p == gl_real and gv_p == gv_real) or (signo == signo_real)

            nombre_j = jugador_nombre.get(uid, f"#{uid}")
            if signo == "1":
                votos_1[uid] = nombre_j
            elif signo == "X":
                votos_X[uid] = nombre_j
            else:
                votos_2[uid] = nombre_j

    con_pronostico = set(apuestas_dict.keys())
    sin_voto = {
        str(j["id"]): j["nombre"]
        for j in jugadores_raw
        if str(j["id"]) not in con_pronostico
        or apuestas_dict.get(str(j["id"]), {}).get("signo_pred") not in ("1", "X", "2")
    }

    n_sin = len(sin_voto)
    total_con_voto = n1 + nX + n2

    def pct(n):
        return f"{round(n / total_con_voto * 100)}%" if total_con_voto else "—"

    if ya_jugado:
        if gl_real > gv_real:
            resultado_txt = f"{local} {gl_real} - {gv_real} {visitante}"
        elif gv_real > gl_real:
            resultado_txt = f"{local} {gl_real} - {gv_real} {visitante}"
        else:
            resultado_txt = f"{local} {gl_real} - {gv_real} {visitante} (Empate)"
        res_html = (
            '<div class="resultado-real"><span class="resultado-pill">⚽ Resultado: '
            + resultado_txt + "</span></div>"
        )
    else:
        res_html = (
            '<div class="resultado-real">'
            '<span class="resultado-pill pending">Partido no jugado</span></div>'
        )

    meta_parts = []
    if fecha_partido:
        meta_parts.append(f'<i class="ti ti-calendar-event"></i> {fecha_partido}')
    if hora:
        meta_parts.append(f'<i class="ti ti-clock"></i> {hora}')
    if estadio:
        meta_parts.append(f'<i class="ti ti-map-pin"></i> {estadio}')
    meta_str = "&nbsp;&nbsp;|&nbsp;&nbsp;".join(meta_parts)

    card_head = (
        '<div class="partido-card">'
        + (f'<div class="match-meta">{meta_str}</div>' if meta_str else "")
        + '<div class="teams-row">'
        + f'<div class="team-block">{escudo_html(local)}<span class="team-name">{local}</span></div>'
        + '<div><span class="vs-text">VS</span></div>'
        + f'<div class="team-block">{escudo_html(visitante)}<span class="team-name">{visitante}</span></div>'
        + "</div>"
        + res_html
        + '<hr style="border:none;border-top:1px solid rgba(255,255,255,0.07);margin:0 0 14px;">'
    )

    if revelado:
        bloque_pronosticos = (
            '<div class="conteo-titulo">¿Quién apostó a qué?</div>'
            + '<div class="barra-wrap">'
            + '<div class="barra-opcion op1">'
            + '<div class="barra-label">1</div>'
            + f'<div class="barra-sublabel">Gana {local}</div>'
            + f'<div class="barra-count">{n1}</div>'
            + f'<div class="barra-pct">{pct(n1)}</div>'
            + chips_html(votos_1, "c1", marcador_de, acierto_de)
            + "</div>"
            + '<div class="barra-opcion opX">'
            + '<div class="barra-label">X</div>'
            + '<div class="barra-sublabel">Empate</div>'
            + f'<div class="barra-count">{nX}</div>'
            + f'<div class="barra-pct">{pct(nX)}</div>'
            + chips_html(votos_X, "cX", marcador_de, acierto_de)
            + "</div>"
            + '<div class="barra-opcion op2">'
            + '<div class="barra-label">2</div>'
            + f'<div class="barra-sublabel">Gana {visitante}</div>'
            + f'<div class="barra-count">{n2}</div>'
            + f'<div class="barra-pct">{pct(n2)}</div>'
            + chips_html(votos_2, "c2", marcador_de, acierto_de)
            + "</div>"
            + "</div>"
        )
        if sin_voto:
            bloque_pronosticos += (
                '<div style="margin-top:6px;">'
                '<div class="barra-sublabel" style="text-align:center;margin-bottom:5px;">'
                f"Sin pronóstico ({n_sin})</div>"
                + chips_html(sin_voto, "cn")
                + "</div>"
            )
    else:
        # Partido todavía no arrancó: tapamos quién apostó a qué (nombres,
        # marcadores) para que nadie pueda copiarse de otro participante,
        # pero sí mostramos la cantidad y el porcentaje por opción — eso
        # no permite identificar a nadie.
        bloque_pronosticos = (
            '<div class="conteo-titulo">¿Cómo vienen los pronósticos?</div>'
            + '<div class="barra-wrap">'
            + '<div class="barra-opcion op1">'
            + '<div class="barra-label">1</div>'
            + f'<div class="barra-sublabel">Gana {local}</div>'
            + f'<div class="barra-count">{n1}</div>'
            + f'<div class="barra-pct">{pct(n1)}</div>'
            + "</div>"
            + '<div class="barra-opcion opX">'
            + '<div class="barra-label">X</div>'
            + '<div class="barra-sublabel">Empate</div>'
            + f'<div class="barra-count">{nX}</div>'
            + f'<div class="barra-pct">{pct(nX)}</div>'
            + "</div>"
            + '<div class="barra-opcion op2">'
            + '<div class="barra-label">2</div>'
            + f'<div class="barra-sublabel">Gana {visitante}</div>'
            + f'<div class="barra-count">{n2}</div>'
            + f'<div class="barra-pct">{pct(n2)}</div>'
            + "</div>"
            + "</div>"
            + (
                f'<div class="barra-sublabel" style="text-align:center;margin-bottom:10px;">'
                f"Sin pronóstico ({n_sin})</div>"
                if n_sin else ""
            )
            + '<div class="pron-bloqueado">'
            + '<div class="candado">🔒</div>'
            + '<div class="titulo">Nombres ocultos</div>'
            + '<div class="subtitulo">Quién apostó a qué se va a revelar '
            'automáticamente apenas arranque el partido, para que nadie '
            'pueda copiarse de otro participante.</div>'
            + '</div>'
        )

    card_html = card_head + bloque_pronosticos + "</div>"
    st.markdown(card_html, unsafe_allow_html=True)


# ── Helper: dots de navegación ───────────────────────────────────────────────────
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


# ════════════════════════════════════════════════════════════════════════════════
# TABS PRINCIPALES: Zona A / Zona B / Interzonal
# ════════════════════════════════════════════════════════════════════════════════
tabs_zona = st.tabs([etiqueta_zona(z) for z in zonas_lista])

for tab, zona in zip(tabs_zona, zonas_lista):
    with tab:
        fechas_zona = sorted(partidos_por_zona[zona].keys(), key=int)

        key_fecha = f"pron_fecha_{zona}"
        if key_fecha not in st.session_state:
            st.session_state[key_fecha] = fechas_zona[0]
        if st.session_state[key_fecha] not in fechas_zona:
            st.session_state[key_fecha] = fechas_zona[0]

        st.markdown(
            f'<p class="zona-activa-label">{etiqueta_zona(zona)}</p>',
            unsafe_allow_html=True,
        )

        fecha_idx = fechas_zona.index(st.session_state[key_fecha])

        # ── Selector de fecha: puntos violetas animados, idéntico a
        # 01_Resultados.py (mismo mecanismo de key= -> clase st-key-<key>) ──
        with st.container(key=f"fecha_wrap_{zona}"):
            st.markdown(
                f'<div class="fecha-slider-label">FECHA {st.session_state[key_fecha]}'
                f'<div class="fecha-slider-sub">estás parado acá</div></div>',
                unsafe_allow_html=True
            )

            fecha_cols = st.columns(len(fechas_zona))
            for i, f in enumerate(fechas_zona):
                with fecha_cols[i]:
                    if st.button("●", key=f"pron_fdot_{zona}_{f}", help=f"Ir a la fecha {f}"):
                        st.session_state[key_fecha] = f
                        st.session_state[f"pron_idx_{zona}_{f}"] = 0
                        st.rerun()

        # CSS: cada punto se targetea por su propia clase st-key-<key>
        _fecha_rules = []
        for i, f in enumerate(fechas_zona):
            dist = abs(i - fecha_idx)
            size = fecha_dot_size(dist)
            color = fecha_dot_color(dist)
            is_active = (dist == 0)
            glow = "box-shadow: 0 0 16px rgba(167,139,250,0.85) !important;" if is_active else "box-shadow: none !important;"
            border = "border: 2px solid rgba(255,255,255,0.9) !important;" if is_active else "border: none !important;"
            btn_key = f"pron_fdot_{zona}_{f}"
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
            .st-key-fecha_wrap_{zona} {{
                max-width: 580px; margin: 0 auto 6px;
                background: rgba(15,23,42,0.55);
                backdrop-filter: blur(14px);
                border: 1px solid rgba(255,255,255,0.07);
                border-radius: 18px;
                padding: 18px 24px 16px;
            }}
            div[data-testid="stHorizontalBlock"]:has([class*="st-key-pron_fdot_{zona}_"]) {{
                gap: 6px !important; align-items: center !important;
                flex-wrap: wrap !important; justify-content: center !important;
            }}
            {"".join(_fecha_rules)}
            [class*="st-key-pron_fdot_{zona}_"] button:hover {{
                transform: scale(1.3) !important;
                background: {VIOLET} !important;
            }}
            [class*="st-key-pron_fdot_{zona}_"] button p {{ visibility: hidden; }}
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

        key_idx = f"pron_idx_{zona}_{fecha_sel}"
        if key_idx not in st.session_state:
            st.session_state[key_idx] = 0
        idx = st.session_state[key_idx]
        if idx >= total:
            idx = 0
            st.session_state[key_idx] = 0

        p = lista_part[idx]
        p_id      = p["id"]
        local     = p["equipo_local"]
        visitante = p["equipo_visitante"]
        fecha_part= p.get("fecha_partido")
        hora      = p.get("hora")
        estadio   = p.get("estadio")
        gl_real   = p.get("goles_local")
        gv_real   = p.get("goles_visitante")

        # ── Selección de partido con mini-cards de escudos (idéntico a
        # 01_Resultados.py): recuadro compacto con escudo · vs · escudo,
        # 100% clickeable ──────────────────────────────────────────────────
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

                btn_key = f"pron_sel_{zona}_{fecha_sel}_{i}"
                _card_keys.append(btn_key)

                # escudo + botón viven en el MISMO contenedor: el botón se
                # superpone con position:absolute cubriendo el 100% del
                # recuadro (ver nota de CSS más abajo).
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

        # CSS: reseteamos a "static" todo lo interno del wrapper (Streamlit le
        # pone "position: relative" a sus propios divs, lo que rompía el área
        # de click si no se neutraliza) y recién ahí el botón se estira con
        # position:absolute/inset:0 para cubrir TODO el recuadro.
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

        st.markdown(
            f"""
            <style>
            div[data-testid="stHorizontalBlock"]:has([class*="st-key-cardwrap_"]) {{
                gap: 8px !important; align-items: flex-start !important;
                flex-wrap: wrap !important; justify-content: center !important;
            }}
            .match-card {{
                display: flex; align-items: center; justify-content: center; gap: 6px;
                width: 78px; height: 54px; border-radius: 14px;
                background: rgba(15,23,42,0.65);
                border: 1.5px solid rgba(255,255,255,0.10);
                transition: all 0.18s ease;
                margin: 0 auto; position: relative; z-index: 1;
                pointer-events: none;
            }}
            .match-card.active {{
                background: rgba(167,139,250,0.20);
                border-color: {VIOLET};
                box-shadow: 0 0 0 2px {VIOLET}55, 0 6px 16px rgba(167,139,250,0.35);
                transform: scale(1.06);
            }}
            .match-card-escudo {{
                width: 24px; height: 24px; object-fit: contain;
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));
            }}
            .match-card-fallback {{ font-size: 18px; opacity: 0.6; }}
            .match-card-vs {{
                font-family: 'Bebas Neue', sans-serif; font-size: 0.55rem;
                color: rgba(255,255,255,0.35); letter-spacing: 1px;
            }}
            [class*="st-key-cardwrap_"]:hover .match-card {{
                border-color: {VIOLET}; transform: scale(1.04);
            }}
            {"".join(_card_rules)}
            </style>
            """,
            unsafe_allow_html=True
        )

        # ── Botones prev / next (ARRIBA) ─────────────────────────────────────
        _, col_prev_top, _, col_next_top, _ = st.columns([1, 1, 4, 1, 1])
        with col_prev_top:
            if st.button("◀", key=f"pron_prev_top_{zona}_{fecha_sel}", disabled=(idx == 0)):
                st.session_state[key_idx] = idx - 1
                st.rerun()
        with col_next_top:
            if st.button("▶", key=f"pron_next_top_{zona}_{fecha_sel}", disabled=(idx == total - 1)):
                st.session_state[key_idx] = idx + 1
                st.rerun()

        render_card_partido(
            local, visitante, fecha_part, hora, estadio,
            gl_real, gv_real,
            pron_por_partido.get(str(p_id), {}),
            comenzo=_partido_comenzo(fecha_part, hora),
        )

        render_dots(idx, total)

        _, col_prev, _, col_next, _ = st.columns([1, 1, 4, 1, 1])
        with col_prev:
            if st.button("◀", key=f"pron_prev_{zona}_{fecha_sel}", disabled=(idx == 0)):
                st.session_state[key_idx] = idx - 1
                st.rerun()
        with col_next:
            if st.button("▶", key=f"pron_next_{zona}_{fecha_sel}", disabled=(idx == total - 1)):
                st.session_state[key_idx] = idx + 1
                st.rerun()
