import streamlit as st
from database import conectar
from escudos_map import url_escudo

st.set_page_config(
    page_title="Resultados",
    layout="centered"
)

st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
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
        background: rgba(11,15,25,0.80);
        z-index: 0;
        pointer-events: none;
    }
    [data-testid="stVerticalBlock"] { position: relative; z-index: 1; }

    h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 1px; }

    .main-label {
        font-size: 0.72rem; color: #94a3b8; text-align: center;
        text-transform: uppercase; letter-spacing: 4px; margin-bottom: 4px;
    }
    .main-title {
        font-size: 3.4rem; color: #e8c96b; text-align: center;
        margin-top: 0.2rem; margin-bottom: 0.2rem;
        text-shadow: 0 4px 18px rgba(232,201,107,0.35);
        font-family: 'Bebas Neue', sans-serif;
    }
    .main-subtitle {
        font-size: 0.82rem; color: #64748b; text-align: center;
        margin-bottom: 1.6rem; letter-spacing: 2px; text-transform: uppercase;
    }

    .fecha-slider-wrap {
        max-width: 580px; margin: 0 auto 6px;
        background: rgba(15,23,42,0.55);
        backdrop-filter: blur(14px);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 18px;
        padding: 18px 24px 14px;
    }
    .fecha-slider-label {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.05rem; color: #e8c96b; letter-spacing: 3px;
        text-align: center; margin-bottom: 14px;
    }
    .fecha-dots-row {
        display: flex; align-items: center; justify-content: center;
        gap: 5px; flex-wrap: wrap;
    }
    .fdot {
        border-radius: 50%;
        background: rgba(255,255,255,0.15);
        cursor: pointer;
        transition: all 0.2s ease;
        border: none; padding: 0;
        flex-shrink: 0;
    }
    .fdot:hover { background: rgba(232,201,107,0.45); transform: scale(1.15); }
    .fdot.active { background: #e8c96b !important; box-shadow: 0 0 12px rgba(232,201,107,0.55); }
    .fdot.near   { background: rgba(232,201,107,0.5); }
    .fdot.medium { background: rgba(232,201,107,0.28); }

    .outer-card {
        background: rgba(16,26,46,0.65);
        backdrop-filter: blur(22px);
        -webkit-backdrop-filter: blur(22px);
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 28px;
        padding: 26px 22px 18px;
        box-shadow: 0 28px 56px rgba(0,0,0,0.5), 0 0 0 1px rgba(232,201,107,0.06);
        max-width: 580px;
        margin: 0 auto 14px;
    }
    .match-meta {
        text-align: center; font-size: 0.73rem; color: #64748b;
        margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1.5px;
        display: flex; align-items: center; justify-content: center; gap: 10px;
        flex-wrap: wrap;
    }
    .match-meta-chip {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 8px;
        padding: 4px 10px;
        display: inline-flex; align-items: center; gap: 5px;
        color: #94a3b8; font-size: 0.72rem;
    }
    .match-meta-chip i { color: #e8c96b; font-size: 0.9rem; }

    .match-inner {
        background: rgba(8,14,28,0.75);
        border-radius: 22px;
        padding: 28px 20px 22px;
        border: 1px solid rgba(255,255,255,0.06);
    }
    .teams-row {
        display: flex; align-items: center;
        justify-content: space-between; gap: 8px;
    }
    .team-block {
        display: flex; flex-direction: column;
        align-items: center; gap: 14px; flex: 1;
    }
    .escudo-img {
        width: 110px; height: 110px; object-fit: contain;
        border-radius: 20px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.5);
        background: rgba(255,255,255,0.07);
        border: 2px solid rgba(255,255,255,0.13);
        padding: 8px;
        transition: transform 0.2s;
    }
    .team-name {
        font-size: 0.88rem; font-weight: 600; color: #e2e8f0;
        text-align: center; line-height: 1.2;
        max-width: 110px;
    }

    .score-block { display: flex; flex-direction: column; align-items: center; min-width: 70px; gap: 4px; }
    .score-vs    { font-family: 'Bebas Neue', sans-serif; font-size: 1.6rem; color: #475569; letter-spacing: 2px; }
    .score-live-row { display: flex; align-items: center; justify-content: center; gap: 2px; }
    .score-number { font-family: 'Bebas Neue', sans-serif; font-size: 2rem; color: #94a3b8; line-height: 1; }
    .score-number.big {
        font-size: 4rem; color: #e8c96b;
        text-shadow: 0 0 28px rgba(232,201,107,0.5), 0 4px 12px rgba(0,0,0,0.5);
        line-height: 1;
    }
    .score-sep { font-family: 'Bebas Neue', sans-serif; font-size: 3rem; color: #334155; margin: 0 6px; line-height: 1; }

    /* ── Result bar con signo 1/X/2 ── */
    .result-bar {
        background: linear-gradient(135deg, #16a34a, #22c55e);
        color: white; padding: 14px 20px;
        border-radius: 16px; text-align: center;
        font-weight: 700; font-size: 1.05rem;
        max-width: 580px; margin: 0 auto 8px;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 16px rgba(34,197,94,0.3);
    }
    .result-bar.empate {
        background: linear-gradient(135deg, #475569, #64748b);
        box-shadow: 0 4px 16px rgba(100,116,139,0.25);
    }
    .result-bar.pending {
        background: rgba(255,255,255,0.04); color: #475569;
        border: 1px dashed rgba(255,255,255,0.1);
        font-weight: 400; font-size: 0.88rem;
        box-shadow: none;
    }

    /* ── Signo 1/X/2 badge ── */
    .signo-bar {
        max-width: 580px; margin: 0 auto 16px;
        display: flex; justify-content: center; gap: 10px;
        align-items: center;
    }
    .signo-chip {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.1rem; letter-spacing: 3px;
        padding: 6px 18px; border-radius: 10px;
        opacity: 0.35;
    }
    .signo-chip.activo {
        opacity: 1;
        box-shadow: 0 0 16px rgba(232,201,107,0.4);
        transform: scale(1.12);
    }
    .signo-1 { background: rgba(59,130,246,0.25); color: #60a5fa; border: 1px solid #3b82f6; }
    .signo-x { background: rgba(148,163,184,0.18); color: #94a3b8; border: 1px solid #475569; }
    .signo-2 { background: rgba(239,68,68,0.22);  color: #f87171; border: 1px solid #ef4444; }

    /* Pronóstico strip */
    .pron-strip {
        max-width: 580px; margin: 0 auto 16px;
        background: rgba(15,23,42,0.5);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 12px 18px;
        font-size: 0.82rem; color: #94a3b8;
        text-align: center;
    }
    .pron-strip b { color: #e8c96b; }

    .nav-wrapper {
        background: rgba(12,20,38,0.65);
        backdrop-filter: blur(14px);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 18px; padding: 14px 22px;
        max-width: 580px; margin: 0 auto 6px;
    }
    .nav-label {
        font-size: 0.68rem; color: #475569; text-align: center;
        text-transform: uppercase; letter-spacing: 2px;
        margin-bottom: 12px;
    }
    .match-dots-row {
        display: flex; justify-content: center;
        gap: 8px; align-items: center; flex-wrap: wrap;
    }
    .mdot {
        border-radius: 50%; cursor: pointer;
        border: 2px solid transparent;
        transition: all 0.18s ease;
        padding: 0; background: rgba(255,255,255,0.15);
        flex-shrink: 0;
    }
    .mdot:hover { transform: scale(1.25); background: rgba(232,201,107,0.4); }
    .mdot.active {
        background: #e8c96b !important;
        border-color: rgba(232,201,107,0.5);
        box-shadow: 0 0 14px rgba(232,201,107,0.6);
        transform: scale(1.35);
    }
    .nav-counter {
        font-size: 0.72rem; color: #475569;
        text-align: center; margin-top: 10px; letter-spacing: 1px;
    }
    .zona-activa-label {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.05rem; color: #e8c96b;
        text-align: center; letter-spacing: 4px;
        margin-bottom: 12px; text-transform: uppercase;
    }

    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 2rem; }
    div[data-testid="stSlider"] > div > div > div:last-child { display: none !important; }
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

get_escudo = url_escudo


@st.cache_data(ttl=0)
def cargar_partidos():
    return sb.table("partidos").select("*").execute().data


try:
    partidos_db = cargar_partidos()
except Exception as e:
    st.error(
        "No se pudo leer la tabla 'partidos' desde Supabase.\n\n"
        f"Detalle técnico: {e}"
    )
    st.stop()

if not partidos_db:
    st.info("No hay partidos registrados todavía.")
    st.stop()

# ── Sesión: jugador logueado (para mostrar su pronóstico) ─────────────────
jugador_logueado_id = st.session_state.get("jugador_id")

# ── Función: calcular signo de un partido ────────────────────────────────
def signo_de(gl, gv):
    if gl is None or gv is None:
        return None
    if gl > gv:   return "1"
    if gl == gv:  return "X"
    return "2"


# ── Agrupar por zona → fecha ─────────────────────────────────────────────
partidos_por_zona = {}
for p in partidos_db:
    z = p["zona"]
    partidos_por_zona.setdefault(z, {})
    f = p["fecha_numero"]
    partidos_por_zona[z].setdefault(f, [])
    partidos_por_zona[z][f].append(p)

zonas_disponibles = sorted(
    partidos_por_zona.keys(),
    key=lambda z: (0 if z == "A" else 1 if z == "B" else 2, z)
)

if "zona_activa" not in st.session_state:
    st.session_state["zona_activa"] = zonas_disponibles[0]

# ── Selector de zona ─────────────────────────────────────────────────────
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
st.markdown(f'<p class="zona-activa-label">{etiqueta_zona}</p>', unsafe_allow_html=True)

# ── Selector de fecha ────────────────────────────────────────────────────
fechas_disponibles = sorted(partidos_por_zona[zona_sel].keys(), key=int)
total_fechas = len(fechas_disponibles)

key_fecha = f"fecha_activa_{zona_sel}"
if key_fecha not in st.session_state:
    st.session_state[key_fecha] = fechas_disponibles[0]
if st.session_state[key_fecha] not in fechas_disponibles:
    st.session_state[key_fecha] = fechas_disponibles[0]

fecha_sel = st.session_state[key_fecha]
fecha_idx = fechas_disponibles.index(fecha_sel)


def dot_size(dist):
    if dist == 0: return 22
    if dist == 1: return 17
    if dist == 2: return 13
    if dist == 3: return 10
    return 8

def dot_class(dist):
    if dist == 0: return "fdot active"
    if dist == 1: return "fdot near"
    if dist == 2: return "fdot medium"
    return "fdot"


fecha_dots_html = '<div class="fecha-dots-row">'
for i, f in enumerate(fechas_disponibles):
    dist = abs(i - fecha_idx)
    sz   = dot_size(dist)
    cls  = dot_class(dist)
    fecha_dots_html += (
        f'<button class="{cls}" '
        f'style="width:{sz}px;height:{sz}px;" '
        f'title="Fecha {f}"></button>'
    )
fecha_dots_html += '</div>'

st.markdown(
    f'<div class="fecha-slider-wrap">'
    f'<div class="fecha-slider-label">FECHA {fecha_sel}</div>'
    f'{fecha_dots_html}'
    f'</div>',
    unsafe_allow_html=True
)

if total_fechas > 1:
    with st.expander("📅 Ir a fecha...", expanded=False):
        cols_f = st.columns(min(total_fechas, 8))
        for i, f in enumerate(fechas_disponibles):
            with cols_f[i % 8]:
                if st.button(f"F{f}", key=f"fdate_{zona_sel}_{f}",
                             type="primary" if f == fecha_sel else "secondary",
                             use_container_width=True):
                    st.session_state[key_fecha] = f
                    st.session_state[f"idx_{zona_sel}_{f}"] = 0
                    st.rerun()

st.markdown("<div style='margin-top:6px'></div>", unsafe_allow_html=True)

# ── Lista de partidos ────────────────────────────────────────────────────
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

partido   = lista_partidos[idx]
local     = partido["equipo_local"]
visitante = partido["equipo_visitante"]
fecha_part= partido.get("fecha_partido")
hora      = partido.get("hora")
estadio   = partido.get("estadio")
estado    = partido.get("estado") or "a_confirmar"
gl        = partido.get("goles_local")
gv        = partido.get("goles_visitante")

escudo_local_url     = get_escudo(local)
escudo_visitante_url = get_escudo(visitante)

escudo_local_html = (
    f'<img src="{escudo_local_url}" class="escudo-img">'
    if escudo_local_url else '<span style="font-size:64px">🛡️</span>'
)
escudo_visitante_html = (
    f'<img src="{escudo_visitante_url}" class="escudo-img">'
    if escudo_visitante_url else '<span style="font-size:64px">🛡️</span>'
)

partido_jugado = gl is not None and gv is not None
signo_real     = signo_de(gl, gv)

# ── Score center ─────────────────────────────────────────────────────────
if partido_jugado:
    score_center_html = (
        '<div class="score-live-row">'
        f'<span class="score-number big">{gl}</span>'
        '<span class="score-sep">-</span>'
        f'<span class="score-number big">{gv}</span>'
        '</div>'
    )
    if gl > gv:
        result_bar_html = f'<div class="result-bar">🏆 Ganó {local}</div>'
    elif gv > gl:
        result_bar_html = f'<div class="result-bar">🏆 Ganó {visitante}</div>'
    else:
        result_bar_html = '<div class="result-bar empate">⚖️ Empate</div>'
else:
    score_center_html = '<span class="score-vs">VS</span>'
    if estado == "confirmado":
        result_bar_html = '<div class="result-bar pending">Partido Confirmado · No Jugado</div>'
    else:
        result_bar_html = '<div class="result-bar pending">Fecha y Hora a Confirmar</div>'

# ── Meta chips ────────────────────────────────────────────────────────────
meta_chips = []
if fecha_part:
    meta_chips.append(f'<span class="match-meta-chip"><i class="ti ti-calendar-event"></i>{fecha_part}</span>')
if hora:
    meta_chips.append(f'<span class="match-meta-chip"><i class="ti ti-clock"></i>{hora}</span>')
if estadio:
    meta_chips.append(f'<span class="match-meta-chip"><i class="ti ti-map-pin"></i>{estadio}</span>')
if not meta_chips:
    meta_chips.append('<span class="match-meta-chip"><i class="ti ti-calendar-event"></i>A confirmar</span>')
meta_str = " ".join(meta_chips)

# ── Render card ───────────────────────────────────────────────────────────
outer_card = (
    '<div class="outer-card">'
    f'<div class="match-meta">{meta_str}</div>'
    '<div class="match-inner">'
    '<div class="teams-row">'
    f'<div class="team-block">{escudo_local_html}<span class="team-name">{local}</span></div>'
    f'<div class="score-block">{score_center_html}</div>'
    f'<div class="team-block">{escudo_visitante_html}<span class="team-name">{visitante}</span></div>'
    '</div>'
    '</div>'
    '</div>'
)
st.markdown(outer_card, unsafe_allow_html=True)
st.markdown(result_bar_html, unsafe_allow_html=True)

# ── SIGNO 1 / X / 2 visual ───────────────────────────────────────────────
activo_1 = "activo" if signo_real == "1" else ""
activo_x = "activo" if signo_real == "X" else ""
activo_2 = "activo" if signo_real == "2" else ""

st.markdown(
    f'<div class="signo-bar">'
    f'<span class="signo-chip signo-1 {activo_1}">1 · LOCAL</span>'
    f'<span class="signo-chip signo-x {activo_x}">X · EMPATE</span>'
    f'<span class="signo-chip signo-2 {activo_2}">2 · VISITANTE</span>'
    f'</div>',
    unsafe_allow_html=True
)

# ── Pronóstico del jugador logueado para este partido ────────────────────
if jugador_logueado_id:
    try:
        pron_resp = (
            sb.table("pronosticos")
            .select("signo_pred, puntos")
            .eq("jugador_id", jugador_logueado_id)
            .eq("partido_id", partido["id"])
            .execute()
        )
        pron_data = pron_resp.data[0] if pron_resp.data else None
    except Exception:
        pron_data = None

    if pron_data and pron_data.get("signo_pred"):
        signo_p = pron_data["signo_pred"]
        pts_p   = pron_data.get("puntos")
        labels  = {"1": "1 · LOCAL", "X": "X · EMPATE", "2": "2 · VISITANTE"}
        label_p = labels.get(signo_p, signo_p)

        if partido_jugado:
            if signo_p == signo_real:
                texto_pts = f"✅ +{pts_p} pts" if pts_p is not None else "✅ Acertaste"
                strip_html = (
                    f'<div class="pron-strip">'
                    f'Tu pronóstico: <b>{label_p}</b> · {texto_pts}'
                    f'</div>'
                )
            else:
                strip_html = (
                    f'<div class="pron-strip">'
                    f'Tu pronóstico: <b>{label_p}</b> · ❌ No acertaste'
                    f'</div>'
                )
        else:
            strip_html = (
                f'<div class="pron-strip">'
                f'Tu pronóstico: <b>{label_p}</b> · ⏳ Partido pendiente'
                f'</div>'
            )
    else:
        if partido_jugado:
            strip_html = '<div class="pron-strip">Sin pronóstico para este partido.</div>'
        else:
            strip_html = (
                '<div class="pron-strip">'
                'No cargaste pronóstico · '
                '<a href="/03_Fixture" target="_self" style="color:#e8c96b;">Ir al Fixture →</a>'
                '</div>'
            )
    st.markdown(strip_html, unsafe_allow_html=True)

# ── Navegación de partidos ────────────────────────────────────────────────
st.markdown(
    '<div class="nav-wrapper">'
    '<div class="nav-label">Partidos de la Fecha</div>'
    '<div class="match-dots-row" id="match-dots-row">',
    unsafe_allow_html=True
)

dot_cols = st.columns(total)
for i in range(total):
    with dot_cols[i]:
        is_active  = (i == idx)
        dot_label  = "●" if is_active else "○"
        if st.button(
            dot_label,
            key=f"mdot_{zona_sel}_{fecha_sel}_{i}",
            help=f"Partido {i+1}: {lista_partidos[i]['equipo_local']} vs {lista_partidos[i]['equipo_visitante']}"
        ):
            st.session_state[key_idx] = i
            st.rerun()

st.markdown("</div></div>", unsafe_allow_html=True)

st.markdown(
    f"""
    <style>
    {"".join([
        f'div[data-testid="column"]:nth-child({i+1}) button[kind="secondary"] '
        f'{{ width:14px !important; height:14px !important; min-height:0 !important; '
        f'border-radius:50% !important; padding:0 !important; '
        f'background:{"#e8c96b" if i==idx else "rgba(255,255,255,0.18)"} !important; '
        f'color:transparent !important; border:none !important; '
        f'box-shadow:{"0 0 12px rgba(232,201,107,0.6)" if i==idx else "none"} !important; '
        f'transform:{"scale(1.4)" if i==idx else "scale(1)"} !important; }}'
        for i in range(total)
    ])}
    .stColumns > div button p {{ visibility: hidden; }}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f'<p class="nav-counter">Partido {idx + 1} de {total} &middot; Fecha {fecha_sel}</p>',
    unsafe_allow_html=True
)

_, col_prev, _, col_next, _ = st.columns([1, 1, 4, 1, 1])
with col_prev:
    if st.button("◀", key="prev_btn", disabled=(idx == 0)):
        st.session_state[key_idx] = idx - 1
        st.rerun()
with col_next:
    if st.button("▶", key="next_btn", disabled=(idx == total - 1)):
        st.session_state[key_idx] = idx + 1
        st.rerun()
