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
        background-color: #0b0f19;
        color: #f1f5f9;
    }

    [data-testid="stAppViewContainer"] {
        background-image: url('https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/FIFAWorldbakcgound.jpg');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }

    [data-testid="stAppViewContainer"]::before {
        content: '';
        position: fixed;
        inset: 0;
        background: rgba(11, 15, 25, 0.75);
        z-index: 0;
        pointer-events: none;
    }

    h1, h2, h3 {
        font-family: 'Bebas Neue', sans-serif;
        letter-spacing: 1px;
    }

    .main-title {
        font-size: 3.5rem;
        color: #e8c96b;
        text-align: center;
        margin-top: 1rem;
        margin-bottom: 0.2rem;
        text-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }

    .main-subtitle {
        font-size: 1.1rem;
        color: #94a3b8;
        text-align: center;
        margin-bottom: 2rem;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    .group-container {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 25px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        margin-bottom: 30px;
    }

    .group-header {
        font-size: 2.2rem;
        color: #ffffff;
        text-align: center;
        margin-bottom: 20px;
        border-bottom: 2px solid #e8c96b;
        padding-bottom: 8px;
    }

    .match-card {
        background: rgba(15, 23, 42, 0.6);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid rgba(255, 255, 255, 0.04);
        transition: transform 0.2s;
    }

    .match-info {
        text-align: center;
        font-size: 0.8rem;
        color: #64748b;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .match-info i {
        margin-right: 4px;
        color: #e8c96b;
    }

    .team-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 0;
    }

    .team-block {
        display: flex;
        align-items: center;
        gap: 12px;
        flex: 1;
    }

    .team-block.local { justify-content: flex-start; }
    .team-block.visitante { justify-content: flex-end; }

    .team-name {
        font-size: 1.15rem;
        font-weight: 500;
        color: #f1f5f9;
    }

    .flag-img {
        width: 32px;
        height: 32px;
        object-fit: cover;
        border-radius: 50%;
        box-shadow: 0 0 8px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
    }

    .vs-badge {
        background: rgba(232, 201, 107, 0.1);
        color: #e8c96b;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0 15px;
        border: 1px solid rgba(232, 201, 107, 0.2);
    }

    [data-testid="stHeader"] {background: transparent;}
    .block-container {padding-top: 2rem;}

    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<h1 class="main-title">RESULTADOS OFICIALES</h1>', unsafe_allow_html=True)
st.markdown('<p class="main-subtitle">Fixture & Scores en Tiempo Real</p>', unsafe_allow_html=True)

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

# ── Renderizado por grupo ──────────────────────────────────────────────────────
for grupo, lista_partidos in partidos_por_grupo.items():
    total = len(lista_partidos)
    key_idx = f"idx_grupo_{grupo}"
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
        else '<span style="font-size:28px">🏳️</span>'
    )
    flag_visitante_html = (
        f'<img src="{flag_visitante_url}" class="flag-img">' if flag_visitante_url
        else '<span style="font-size:28px">🏳️</span>'
    )

    st.markdown(f'<div class="group-container"><div class="group-header">GRUPO {grupo_val}</div>', unsafe_allow_html=True)

    card_html = f"""
    <div class="match-card">
        <div class="match-info">
            <i class="ti ti-calendar-event"></i> {fecha} &nbsp;&nbsp;|&nbsp;&nbsp;
            <i class="ti ti-clock"></i> {hora} &nbsp;&nbsp;|&nbsp;&nbsp;
            <i class="ti ti-map-pin"></i> {sede}
        </div>
        <div class="team-row">
            <div class="team-block local">
                {flag_local_html}
                <span class="team-name">{local}</span>
            </div>
            <div class="vs-badge">VS</div>
            <div class="team-block visitante">
                <span class="team-name">{visitante}</span>
                {flag_visitante_html}
            </div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # Resultado
    if not resultado:
        st.markdown(
            "<div style='background:rgba(255,255,255,0.05);color:#94a3b8;padding:10px;"
            "border-radius:10px;text-align:center;margin:10px 0;font-size:0.9rem;"
            "border:1px dashed rgba(255,255,255,0.1)'>Partido No Jugado</div>",
            unsafe_allow_html=True
        )
    else:
        labels = {"1": f"Ganador: {local}", "X": "Empate", "2": f"Ganador: {visitante}"}
        label = labels.get(resultado, resultado)
        st.markdown(
            f"<div style='background:#22c55e;color:white;padding:10px;border-radius:10px;"
            f"text-align:center;margin:10px 0;font-weight:600;'>{label}</div>",
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    nav1, nav2, nav3 = st.columns([1, 3, 1])

    with nav1:
        if st.button("◀", key=f"prev_{grupo}", disabled=(idx == 0)):
            st.session_state[key_idx] = idx - 1
            st.rerun()

    with nav2:
        dots_html = "<div style='display:flex;justify-content:center;gap:6px;align-items:center;padding:8px 0'>"
        for i in range(total):
            if i == idx:
                dots_html += "<div style='width:18px;height:6px;border-radius:3px;background:#e8c96b'></div>"
            else:
                dots_html += "<div style='width:6px;height:6px;border-radius:50%;background:#1e2840'></div>"
        dots_html += "</div>"
        st.markdown(dots_html, unsafe_allow_html=True)

    with nav3:
        if st.button("▶", key=f"next_{grupo}", disabled=(idx == total - 1)):
            st.session_state[key_idx] = idx + 1
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
