from flags import get_flag
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
        margin-top: 0.2rem; margin-bottom: 1.5rem;
        text-shadow: 0 4px 12px rgba(0,0,0,0.5);
        font-family: 'Bebas Neue', sans-serif;
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
    .flag-img {
        width: 56px; height: 56px; object-fit: cover;
        border-radius: 50%;
        box-shadow: 0 4px 14px rgba(0,0,0,0.4);
        border: 2px solid rgba(255,255,255,0.12);
    }
    .team-name { font-size: 0.9rem; font-weight: 500; color: #e2e8f0; text-align: center; }
    .score-block { display: flex; flex-direction: column; align-items: center; min-width: 60px; }
    .score-number { font-family: 'Bebas Neue', sans-serif; font-size: 2rem; color: #94a3b8; line-height: 1; }
    .score-number.big { font-size: 3rem; color: #e8c96b; text-shadow: 0 2px 10px rgba(232,201,107,0.35); }
    .score-sep { font-family: 'Bebas Neue', sans-serif; font-size: 2.2rem; color: #64748b; margin: 0 4px; line-height: 1; }
    .score-live-row { display: flex; align-items: center; justify-content: center; }

    .result-badge-inner { text-align: center; margin-top: 14px; }
    .badge-pill {
        display: inline-block;
        background: rgba(34,197,94,0.15); color: #4ade80;
        border: 1px solid rgba(34,197,94,0.3);
        border-radius: 20px; padding: 5px 18px;
        font-size: 0.82rem; font-weight: 600;
    }
    .badge-pill.pending {
        background: rgba(255,255,255,0.04); color: #64748b;
        border: 1px dashed rgba(255,255,255,0.1);
    }

    .result-bar {
        background: #22c55e; color: white; padding: 13px;
        border-radius: 14px; text-align: center;
        font-weight: 700; font-size: 1rem;
        max-width: 560px; margin: 0 auto 16px;
        letter-spacing: 0.5px;
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

    .grupo-activo-label {
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

try:
    sb = conectar()
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.stop()

# ── Funciones de carga con caché de corta duración (30 seg) ──────────────────
@st.cache_data(ttl=30)
def cargar_partidos():
    return conectar().table("partidos").select("*").order("grupo").order("fecha").order("hora").execute().data

@st.cache_data(ttl=30)
def cargar_dieciseisavos():
    return conectar().table("dieciseisavos").select("*").order("partido_num").execute().data

# ── Selector de fase ──────────────────────────────────────────────────────────
if "fase_resultados" not in st.session_state:
    st.session_state["fase_resultados"] = "grupos"

col_fase1, col_fase2 = st.columns(2)
with col_fase1:
    if st.button("📋 Fase de Grupos", key="fase_grupos_btn", use_container_width=True,
                 type="primary" if st.session_state["fase_resultados"] == "grupos" else "secondary"):
        st.session_state["fase_resultados"] = "grupos"
        st.rerun()
with col_fase2:
    if st.button("🏆 Dieciseisavos de Final", key="fase_16_btn", use_container_width=True,
                 type="primary" if st.session_state["fase_resultados"] == "dieciseisavos" else "secondary"):
        st.session_state["fase_resultados"] = "dieciseisavos"
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

if st.session_state["fase_resultados"] == "dieciseisavos":
    # ── DIECISEISAVOS DE FINAL ─────────────────────────────────────────────────
    cruces = cargar_dieciseisavos()

    if not cruces:
        st.info("Todavía no se cargaron los cruces de Dieciseisavos de Final.")
        st.stop()

    for c in cruces:
        nombre_local = (
            c.get("equipo_local")
            or c.get("origen_local")
            or c.get("grupo_local")
            or "Por definir"
        )
        nombre_visitante = (
            c.get("equipo_visitante")
            or c.get("origen_visitante")
            or c.get("grupo_visitante")
            or "Por definir"
        )
        es_placeholder = not c.get("equipo_local")

        flag_l_url = get_flag(nombre_local)
        flag_v_url = get_flag(nombre_visitante)
        flag_l_html = (
            '<img src="' + flag_l_url + '" class="flag-img">'
            if flag_l_url else '<span style="font-size:48px">🏳️</span>'
        )
        flag_v_html = (
            '<img src="' + flag_v_url + '" class="flag-img">'
            if flag_v_url else '<span style="font-size:48px">🏳️</span>'
        )

        resultado_16 = c.get("resultado") or ""
        marcador_16  = c.get("marcador") or ""

        # Parseo del marcador "N-M" para mostrarlo grande en el medio de la card
        gl_16, gv_16 = None, None
        if marcador_16 and "-" in str(marcador_16):
            partes_score = str(marcador_16).split("-")
            try:
                gl_16 = int(partes_score[0].strip())
                gv_16 = int(partes_score[1].strip())
            except (ValueError, IndexError):
                gl_16, gv_16 = None, None

        if gl_16 is not None and gv_16 is not None:
            score_center_html = (
                '<div class="score-live-row">'
                '<span class="score-number big">' + str(gl_16) + '</span>'
                '<span class="score-sep">-</span>'
                '<span class="score-number big">' + str(gv_16) + '</span>'
                '</div>'
            )
        else:
            score_center_html = '<span class="score-number">VS</span>'

        if resultado_16:
            labels_16 = {"1": "Gana " + nombre_local, "2": "Gana " + nombre_visitante}
            label_16  = labels_16.get(resultado_16, resultado_16)
            if marcador_16:
                label_16 = label_16 + " (" + marcador_16 + ")"
            result_bar_16 = '<div class="result-bar">' + label_16 + '</div>'
        else:
            result_bar_16 = '<div class="result-bar pending">Partido No Jugado</div>'

        meta_parts_16 = ["Cruce " + str(c.get("partido_num"))]
        if c.get("fecha"):
            meta_parts_16.append('<i class="ti ti-calendar-event"></i> ' + str(c["fecha"]))
        if c.get("hora"):
            meta_parts_16.append('<i class="ti ti-clock"></i> ' + str(c["hora"]))
        if c.get("sede"):
            meta_parts_16.append('<i class="ti ti-map-pin"></i> ' + str(c["sede"]))
        meta_str_16 = "&nbsp;&nbsp;|&nbsp;&nbsp;".join(meta_parts_16)

        outer_card_16 = (
            '<div class="outer-card">'
            '<div class="match-meta">' + meta_str_16 + '</div>'
            '<div class="match-inner">'
            '<div class="teams-row">'
            '<div class="team-block">' + flag_l_html + '<span class="team-name">' + nombre_local
            + ('<br><span style="font-size:0.65rem;color:#64748b;">(' + (c.get("grupo_local") or "") + ')</span>' if not es_placeholder and c.get("grupo_local") else '')
            + '</span></div>'
            '<div class="score-block">' + score_center_html + '</div>'
            '<div class="team-block">' + flag_v_html + '<span class="team-name">' + nombre_visitante
            + ('<br><span style="font-size:0.65rem;color:#64748b;">(' + (c.get("grupo_visitante") or "") + ')</span>' if not es_placeholder and c.get("grupo_visitante") else '')
            + '</span></div>'
            '</div>'
            '</div>'
            '</div>'
        )
        st.markdown(outer_card_16, unsafe_allow_html=True)
        st.markdown(result_bar_16, unsafe_allow_html=True)

    st.stop()

# ── FASE DE GRUPOS ────────────────────────────────────────────────────────────
partidos_db = cargar_partidos()

if not partidos_db:
    st.info("No hay partidos registrados todavía.")
    st.stop()

partidos_por_grupo = {}
for p in partidos_db:
    g = p["grupo"]
    partidos_por_grupo.setdefault(g, [])
    partidos_por_grupo[g].append((
        p["id"], p["grupo"], p["fecha"], p["hora"],
        p["sede"], p["local"], p["visitante"], p.get("resultado") or ""
    ))

grupos_lista = sorted(partidos_por_grupo.keys())

if "grupo_activo" not in st.session_state:
    st.session_state["grupo_activo"] = grupos_lista[0]

# ── TABS ───────────────────────────────────────────────────────────────────────
cols = st.columns(len(grupos_lista))
for i, g in enumerate(grupos_lista):
    with cols[i]:
        es_activo = (g == st.session_state["grupo_activo"])
        btn_style = "primary" if es_activo else "secondary"
        if st.button(g, key=f"tab_{g}", use_container_width=True, type=btn_style):
            st.session_state["grupo_activo"] = g
            st.session_state[f"idx_grupo_{g}"] = 0
            st.rerun()

st.markdown(
    '<p class="grupo-activo-label">GRUPO ' + st.session_state["grupo_activo"] + '</p>',
    unsafe_allow_html=True
)

grupo_sel = st.session_state["grupo_activo"]
lista_partidos = partidos_por_grupo[grupo_sel]
total = len(lista_partidos)

key_idx = f"idx_grupo_{grupo_sel}"
if key_idx not in st.session_state:
    st.session_state[key_idx] = 0
idx = st.session_state[key_idx]
if idx >= total:
    idx = 0
    st.session_state[key_idx] = 0

p_id, grupo_val, fecha, hora, sede, local, visitante, resultado = lista_partidos[idx]

flag_local_url     = get_flag(local)
flag_visitante_url = get_flag(visitante)

flag_local_html = (
    '<img src="' + flag_local_url + '" class="flag-img">'
    if flag_local_url else '<span style="font-size:48px">🏳️</span>'
)
flag_visitante_html = (
    '<img src="' + flag_visitante_url + '" class="flag-img">'
    if flag_visitante_url else '<span style="font-size:48px">🏳️</span>'
)

if resultado:
    labels = {"1": "Gana " + local, "X": "Empate", "2": "Gana " + visitante}
    label_text = labels.get(resultado, resultado)
    result_bar_html = '<div class="result-bar">' + label_text + '</div>'
else:
    result_bar_html = '<div class="result-bar pending">Partido No Jugado</div>'

# ── OUTER CARD ─────────────────────────────────────────────────────────────────
outer_card = (
    '<div class="outer-card">'
    '<div class="match-meta">'
    '<i class="ti ti-calendar-event"></i> ' + str(fecha) +
    '&nbsp;&nbsp;|&nbsp;&nbsp;'
    '<i class="ti ti-clock"></i> ' + str(hora) +
    '&nbsp;&nbsp;|&nbsp;&nbsp;'
    '<i class="ti ti-map-pin"></i> ' + str(sede) +
    '</div>'
    '<div class="match-inner">'
    '<div class="teams-row">'
    '<div class="team-block">' + flag_local_html + '<span class="team-name">' + local + '</span></div>'
    '<div class="score-block"><span class="score-number">VS</span></div>'
    '<div class="team-block">' + flag_visitante_html + '<span class="team-name">' + visitante + '</span></div>'
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
    '<p class="nav-counter">Partido ' + str(idx + 1) + ' de ' + str(total) + '</p>'
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
