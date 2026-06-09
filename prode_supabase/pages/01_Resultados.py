from flags import FLAGS
import streamlit as st
from database import conectar

st.set_page_config(
    page_title="Resultados",
    layout="centered"
)

# ── CSS principal ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">

    <style>

    body {
        font-family: 'DM Sans', sans-serif;
        color: #f1f5f9;
    }

    /* ── FONDO DE IMAGEN ── */
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
        background: rgba(11, 15, 25, 0.78);
        z-index: 0;
        pointer-events: none;
    }

    [data-testid="stVerticalBlock"] {
        position: relative;
        z-index: 1;
    }

    h1, h2, h3 {
        font-family: 'Bebas Neue', sans-serif;
        letter-spacing: 1px;
    }

    /* ── TÍTULO ── */
    .main-label {
        font-size: 0.75rem;
        color: #94a3b8;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin-bottom: 4px;
    }

    .main-title {
        font-size: 3.2rem;
        color: #e8c96b;
        text-align: center;
        margin-top: 0.2rem;
        margin-bottom: 1.5rem;
        text-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }

    /* ── TABS DE GRUPOS ── */
    .tabs-wrapper {
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 16px;
        padding: 10px 16px;
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 6px;
        margin-bottom: 20px;
    }

    .tab-btn {
        background: transparent;
        border: 1px solid rgba(255,255,255,0.1);
        color: #94a3b8;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        font-family: 'DM Sans', sans-serif;
        letter-spacing: 0.5px;
    }

    .tab-btn:hover {
        background: rgba(232,201,107,0.1);
        color: #e8c96b;
        border-color: rgba(232,201,107,0.3);
    }

    .tab-btn.active {
        background: rgba(232,201,107,0.15);
        color: #e8c96b;
        border-color: #e8c96b;
        font-weight: 600;
    }

    /* ── OUTER CARD (blur exterior) ── */
    .outer-card {
        background: rgba(20, 30, 50, 0.55);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 28px;
        padding: 28px 24px 20px;
        box-shadow: 0 24px 48px rgba(0,0,0,0.4);
        max-width: 560px;
        margin: 0 auto 20px;
    }

    /* ── MATCH INFO ── */
    .match-meta {
        text-align: center;
        font-size: 0.75rem;
        color: #64748b;
        margin-bottom: 18px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .match-meta i {
        color: #e8c96b;
        margin-right: 3px;
    }

    /* ── INNER CARD ── */
    .match-inner {
        background: rgba(10, 18, 35, 0.7);
        border-radius: 20px;
        padding: 22px 20px 18px;
        border: 1px solid rgba(255,255,255,0.05);
        margin-bottom: 16px;
    }

    /* ── EQUIPOS ── */
    .teams-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
    }

    .team-block {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
        flex: 1;
    }

    .flag-img {
        width: 56px;
        height: 56px;
        object-fit: cover;
        border-radius: 50%;
        box-shadow: 0 4px 14px rgba(0,0,0,0.4);
        border: 2px solid rgba(255,255,255,0.12);
    }

    .team-name {
        font-size: 0.9rem;
        font-weight: 500;
        color: #e2e8f0;
        text-align: center;
    }

    /* ── MARCADOR VS ── */
    .score-block {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        min-width: 60px;
    }

    .score-number {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 3rem;
        color: #ffffff;
        line-height: 1;
    }

    .vs-text {
        font-size: 0.7rem;
        color: #475569;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    /* ── BADGE RESULTADO DENTRO DE CARD ── */
    .result-badge-inner {
        text-align: center;
        margin-top: 14px;
    }

    .badge-pill {
        display: inline-block;
        background: rgba(34,197,94,0.15);
        color: #4ade80;
        border: 1px solid rgba(34,197,94,0.3);
        border-radius: 20px;
        padding: 5px 18px;
        font-size: 0.82rem;
        font-weight: 600;
    }

    .badge-pill.pending {
        background: rgba(255,255,255,0.04);
        color: #64748b;
        border: 1px dashed rgba(255,255,255,0.1);
    }

    /* ── RESULTADO GRANDE ── */
    .result-bar {
        background: #22c55e;
        color: white;
        padding: 13px;
        border-radius: 14px;
        text-align: center;
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 16px;
        max-width: 560px;
        margin-left: auto;
        margin-right: auto;
        letter-spacing: 0.5px;
    }

    .result-bar.pending {
        background: rgba(255,255,255,0.05);
        color: #64748b;
        border: 1px dashed rgba(255,255,255,0.1);
        font-weight: 400;
        font-size: 0.9rem;
    }

    /* ── NAVEGACIÓN ── */
    .nav-wrapper {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 16px;
        padding: 12px 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 16px;
        max-width: 560px;
        margin: 0 auto;
    }

    .dots-row {
        display: flex;
        justify-content: center;
        gap: 6px;
        align-items: center;
        flex: 1;
    }

    .nav-counter {
        font-size: 0.75rem;
        color: #475569;
        text-align: center;
        margin-top: 8px;
        letter-spacing: 1px;
    }

    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 2rem; }

    /* Ocultar decoraciones de Streamlit en botones de navegación */
    div[data-testid="stHorizontalBlock"] { gap: 0 !important; }

    </style>
    """,
    unsafe_allow_html=True
)

# ── TÍTULO ──────────────────────────────────────────────────────────────────────
st.markdown('<p class="main-label">Fixture Oficial</p>', unsafe_allow_html=True)
st.markdown('<h1 class="main-title">RESULTADOS</h1>', unsafe_allow_html=True)

# ── Conexión Supabase ──────────────────────────────────────────────────────────
try:
    sb = conectar()
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.stop()

# ── Consulta partidos ──────────────────────────────────────────────────────────
resp = sb.table("partidos").select("*").order("grupo").order("fecha").order("hora").execute()
partidos_db = resp.data

if not partidos_db:
    st.info("No hay partidos registrados todavía.")
    st.stop()

# ── Agrupar por grupo ──────────────────────────────────────────────────────────
partidos_por_grupo = {}
for p in partidos_db:
    g = p["grupo"]
    partidos_por_grupo.setdefault(g, [])
    partidos_por_grupo[g].append((
        p["id"], p["grupo"], p["fecha"], p["hora"],
        p["sede"], p["local"], p["visitante"], p.get("resultado") or ""
    ))

grupos_lista = sorted(partidos_por_grupo.keys())

# ── Selector de grupo con tabs ─────────────────────────────────────────────────
if "grupo_activo" not in st.session_state:
    st.session_state["grupo_activo"] = grupos_lista[0]

# Tabs HTML centradas
tabs_html = '<div class="tabs-wrapper">'
for g in grupos_lista:
    activo = "active" if g == st.session_state["grupo_activo"] else ""
    tabs_html += f'<button class="tab-btn {activo}" onclick="window.location.href=\'?grupo={g}\'">{g}</button>'
tabs_html += '</div>'
st.markdown(tabs_html, unsafe_allow_html=True)

# Leer parámetro de URL para cambio de grupo
query_params = st.query_params
if "grupo" in query_params:
    grupo_url = query_params["grupo"]
    if grupo_url in partidos_por_grupo:
        st.session_state["grupo_activo"] = grupo_url

# Selector nativo de Streamlit (oculto visualmente, funcional)
cols_tabs = st.columns(len(grupos_lista))
for i, g in enumerate(grupos_lista):
    with cols_tabs[i]:
        if st.button(g, key=f"tab_{g}", use_container_width=True):
            st.session_state["grupo_activo"] = g
            key_idx = f"idx_grupo_{g}"
            st.session_state[key_idx] = 0
            st.rerun()

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

flag_local_url     = FLAGS.get(local, "")
flag_visitante_url = FLAGS.get(visitante, "")

flag_local_html = (
    f'<img src="{flag_local_url}" class="flag-img">' if flag_local_url
    else '<span style="font-size:48px">🏳️</span>'
)
flag_visitante_html = (
    f'<img src="{flag_visitante_url}" class="flag-img">' if flag_visitante_url
    else '<span style="font-size:48px">🏳️</span>'
)

# ── OUTER CARD ─────────────────────────────────────────────────────────────────
card_html = f"""
<div class="outer-card">
    <div class="match-meta">
        <i class="ti ti-calendar-event"></i> {fecha}
        &nbsp;&nbsp;|&nbsp;&nbsp;
        <i class="ti ti-clock"></i> {hora}
        &nbsp;&nbsp;|&nbsp;&nbsp;
        <i class="ti ti-map-pin"></i> {sede}
    </div>

    <div class="match-inner">
        <div class="teams-row">
            <div class="team-block">
                {flag_local_html}
                <span class="team-name">{local}</span>
            </div>
            <div class="score-block">
                <span class="score-number">VS</span>
            </div>
            <div class="team-block">
                {flag_visitante_html}
                <span class="team-name">{visitante}</span>
            </div>
        </div>
    </div>
"""

# Resultado dentro del outer card
if not resultado:
    card_html += """
    <div class="result-badge-inner">
        <span class="badge-pill pending">Partido No Jugado</span>
    </div>
"""
else:
    labels = {"1": f"Gana {local}", "X": "Empate", "2": f"Gana {visitante}"}
    label = labels.get(resultado, resultado)
    card_html += f"""
    <div class="result-badge-inner">
        <span class="badge-pill">{label}</span>
    </div>
"""

card_html += "</div>"
st.markdown(card_html, unsafe_allow_html=True)

# ── BARRA RESULTADO GRANDE ─────────────────────────────────────────────────────
if not resultado:
    st.markdown(
        "<div class='result-bar pending'>Partido No Jugado</div>",
        unsafe_allow_html=True
    )
else:
    labels = {"1": f"Gana {local}", "X": "Empate", "2": f"Gana {visitante}"}
    label = labels.get(resultado, resultado)
    st.markdown(
        f"<div class='result-bar'>{label}</div>",
        unsafe_allow_html=True
    )

# ── NAVEGACIÓN CENTRADA ────────────────────────────────────────────────────────
dots_html = "<div style='display:flex;justify-content:center;gap:6px;align-items:center'>"
for i in range(total):
    if i == idx:
        dots_html += "<div style='width:20px;height:6px;border-radius:3px;background:#e8c96b'></div>"
    else:
        dots_html += "<div style='width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,0.15)'></div>"
dots_html += "</div>"

nav_wrapper = f"""
<div class="nav-wrapper">
    <span style="color:#64748b;font-size:0.8rem">◀</span>
    {dots_html}
    <span style="color:#64748b;font-size:0.8rem">▶</span>
</div>
<p class="nav-counter">Partido {idx+1} de {total}</p>
"""
st.markdown(nav_wrapper, unsafe_allow_html=True)

# Botones funcionales de navegación (debajo, funcionales)
_, col_prev, col_mid, col_next, _ = st.columns([1, 1, 4, 1, 1])
with col_prev:
    if st.button("◀", key=f"prev_{grupo_sel}", disabled=(idx == 0)):
        st.session_state[key_idx] = idx - 1
        st.rerun()
with col_next:
    if st.button("▶", key=f"next_{grupo_sel}", disabled=(idx == total - 1)):
        st.session_state[key_idx] = idx + 1
        st.rerun()
