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
from database import conectar
from escudos_map import url_escudo

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
        background-image: url('https://raw.githubusercontent.com/arcaltdfootball/PRODEFIFAWC2026UNQ/main/prode_supabase/FIFA666.jpg');
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

    /* ZONA LABEL */
    .zona-activa-label {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1rem; color: #e8c96b;
        text-align: center; letter-spacing: 3px;
        margin-bottom: 10px; text-transform: uppercase;
    }
    .fecha-label {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 0.85rem; color: #94a3b8;
        text-align: center; letter-spacing: 2px;
        margin: 4px 0 12px; text-transform: uppercase;
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
    "jugador_id, partido_id, signo_pred, goles_local_pred, goles_visitante_pred, puntos",
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
                         gl_real, gv_real, apuestas_dict):
    votos_1 = {}
    votos_X = {}
    votos_2 = {}
    marcador_de = {}
    acierto_de = {}

    ya_jugado = gl_real is not None and gv_real is not None
    signo_real = None
    if ya_jugado:
        if gl_real > gv_real:
            signo_real = "1"
        elif gl_real == gv_real:
            signo_real = "X"
        else:
            signo_real = "2"

    for uid, pr in apuestas_dict.items():
        signo = pr.get("signo_pred")
        if signo not in ("1", "X", "2"):
            continue
        gl_p = pr.get("goles_local_pred")
        gv_p = pr.get("goles_visitante_pred")
        if gl_p is not None and gv_p is not None:
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

    n1 = len(votos_1)
    nX = len(votos_X)
    n2 = len(votos_2)
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

    card_html = (
        '<div class="partido-card">'
        + (f'<div class="match-meta">{meta_str}</div>' if meta_str else "")
        + '<div class="teams-row">'
        + f'<div class="team-block">{escudo_html(local)}<span class="team-name">{local}</span></div>'
        + '<div><span class="vs-text">VS</span></div>'
        + f'<div class="team-block">{escudo_html(visitante)}<span class="team-name">{visitante}</span></div>'
        + "</div>"
        + res_html
        + '<hr style="border:none;border-top:1px solid rgba(255,255,255,0.07);margin:0 0 14px;">'
        + '<div class="conteo-titulo">¿Quién apostó a qué?</div>'
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
        card_html += (
            '<div style="margin-top:6px;">'
            '<div class="barra-sublabel" style="text-align:center;margin-bottom:5px;">'
            f"Sin pronóstico ({n_sin})</div>"
            + chips_html(sin_voto, "cn")
            + "</div>"
        )
    card_html += "</div>"
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

        # ── Selector de fecha ────────────────────────────────────────────────
        cols_fecha = st.columns(len(fechas_zona))
        for i, f in enumerate(fechas_zona):
            with cols_fecha[i]:
                es_activa = (f == st.session_state[key_fecha])
                if st.button(f"Fecha {f}", key=f"pron_fbtn_{zona}_{f}",
                             use_container_width=True,
                             type="primary" if es_activa else "secondary"):
                    st.session_state[key_fecha] = f
                    st.session_state[f"pron_idx_{zona}_{f}"] = 0
                    st.rerun()

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

        # ── Botones de selección directa de partido ──────────────────────────
        btn_cols = st.columns(total)
        for i, part in enumerate(lista_part):
            with btn_cols[i]:
                es_actual = i == idx
                lbl = f"{part['equipo_local'][:3].upper()} vs {part['equipo_visitante'][:3].upper()}"
                if st.button(lbl, key=f"pron_sel_{zona}_{fecha_sel}_{i}",
                             use_container_width=True,
                             type="primary" if es_actual else "secondary"):
                    st.session_state[key_idx] = i
                    st.rerun()

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
