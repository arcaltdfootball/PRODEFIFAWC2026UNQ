import streamlit as st
import pandas as pd
import base64
from ranking import obtener_ranking
from excel_export import exportar_ranking

st.set_page_config(
    page_title="Ranking FIFA 26",
    page_icon="🏅",
    layout="wide",
)


st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600;700&display=swap');

[data-testid="stAppViewContainer"] {{
    background-image: url("https://raw.githubusercontent.com/arcaltdfootball/PRODEFIFAWC2026UNQ/main/prode_supabase/fifaranking.jpeg");
    background-size: cover;
    background-position: center top;
    background-attachment: fixed;
    background-repeat: no-repeat;
}}
[data-testid="stHeader"] {{ background: transparent !important; }}
[data-testid="stAppViewContainer"]::before {{
    content: "";
    position: fixed;
    inset: 0;
    background: linear-gradient(160deg,rgba(0,0,0,0.82) 0%,rgba(5,15,40,0.78) 50%,rgba(0,0,0,0.88) 100%);
    z-index: 0;
    pointer-events: none;
}}
* {{ box-sizing: border-box; }}
html, body, p, span:not(.material-symbols-rounded):not(.material-icons):not([data-testid]), h1, h2, h3, h4, h5, h6, a, li, td, th, input, label {{
    font-family: 'Inter', sans-serif;
}}
[data-testid="stVerticalBlock"] {{ position: relative; z-index: 1; }}

.hero-title {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(3.5rem, 8vw, 7rem);
    letter-spacing: 0.06em;
    line-height: 1;
    color: #fff;
    text-shadow: 0 0 40px rgba(255,210,0,0.55), 0 4px 24px rgba(0,0,0,0.8);
    margin: 0 0 4px 0;
}}
.hero-sub {{
    font-size: 0.95rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: rgba(255,210,0,0.85);
    font-weight: 500;
    margin-bottom: 32px;
}}
.glass {{
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.13);
    border-radius: 20px;
    backdrop-filter: blur(22px) saturate(1.4);
    -webkit-backdrop-filter: blur(22px) saturate(1.4);
    padding: 28px 32px;
    margin-bottom: 16px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.1);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}
.glass:hover {{
    transform: translateY(-2px);
    box-shadow: 0 14px 50px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.12);
}}
.rank-card {{ display: flex; align-items: center; gap: 24px; position: relative; }}
.rank-pos {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 4rem; line-height: 1;
    min-width: 72px; text-align: center;
    color: rgba(255,255,255,0.25);
}}
.rank-pos.gold   {{ color: #FFD700; text-shadow: 0 0 20px rgba(255,215,0,0.6); }}
.rank-pos.silver {{ color: #C0C0C0; text-shadow: 0 0 20px rgba(192,192,192,0.4); }}
.rank-pos.bronze {{ color: #CD7F32; text-shadow: 0 0 20px rgba(205,127,50,0.4); }}
.rank-name {{ font-size: 1.45rem; font-weight: 700; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.rank-pts {{ font-family: 'Bebas Neue', sans-serif; font-size: 2.8rem; color: #FFD700; line-height: 1; min-width: 90px; text-align: right; }}
.pts-label {{ font-size: 0.7rem; letter-spacing: 0.2em; text-transform: uppercase; color: rgba(255,210,0,0.6); text-align: right; margin-top: -2px; }}
.stats-row {{ display: flex; gap: 12px; margin-top: 14px; flex-wrap: wrap; }}
.stat-pill {{
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 50px;
    padding: 6px 16px;
    font-size: 0.82rem;
    display: flex; align-items: center; gap: 6px;
    white-space: nowrap;
}}
.stat-pill .label {{ color: rgba(255,255,255,0.5); font-weight: 300; }}
.stat-pill .value {{ font-weight: 700; color: #fff; }}
.stat-pill .pct   {{ font-weight: 800; color: #34d399; }}
.trend {{ font-size: 1.5rem; font-weight: 900; min-width: 36px; text-align: center; }}
.trend.up   {{ color: #34d399; }}
.trend.down {{ color: #f87171; }}
.trend.same {{ color: rgba(255,255,255,0.3); }}
.pct-bar-bg {{ width: 110px; height: 6px; background: rgba(255,255,255,0.1); border-radius: 99px; overflow: hidden; margin-top: 2px; display: inline-block; vertical-align: middle; }}
.pct-bar-fill {{ height: 100%; border-radius: 99px; background: linear-gradient(90deg, #34d399, #059669); }}
[data-testid="stTextInput"] input {{
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.18) !important;
    border-radius: 50px !important;
    color: #fff !important;
    font-size: 1rem !important;
    padding: 12px 20px !important;
    backdrop-filter: blur(10px);
}}
[data-testid="stTextInput"] input::placeholder {{ color: rgba(255,255,255,0.35) !important; }}
[data-testid="baseButton-secondary"], [data-testid="baseButton-primary"] {{
    background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%) !important;
    color: #000 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 50px !important;
    padding: 10px 28px !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.05em !important;
    box-shadow: 0 4px 20px rgba(255,165,0,0.4) !important;
}}
.divider {{ height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.12), transparent); margin: 8px 0 20px; }}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='padding: 40px 0 10px 0;'>
    <div class='hero-title'> Ranking General</div>
    <div class='hero-sub'>FIFA World Cup 26 · Predicciones</div>
</div>
""", unsafe_allow_html=True)

# ── Cargar datos ──────────────────────────────────────────────────────────────
try:
    ranking = obtener_ranking()
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.stop()

if "posiciones_anteriores" not in st.session_state:
    st.session_state.posiciones_anteriores = {}

posiciones_anteriores = st.session_state.posiciones_anteriores
nuevas_posiciones = {}
datos = []

for i, row in enumerate(ranking):
    nombre, puntos, aciertos, disputados = row[0], row[1], row[2] if len(row) > 2 else None, row[3] if len(row) > 3 else None
    pos_actual = i + 1
    nuevas_posiciones[nombre] = pos_actual
    prev_pos = posiciones_anteriores.get(nombre, pos_actual)

    if prev_pos > pos_actual:
        trend_icon, trend_cls = "▲", "up"
    elif prev_pos < pos_actual:
        trend_icon, trend_cls = "▼", "down"
    else:
        trend_icon, trend_cls = "—", "same"

    try:
        _ac = float(aciertos) if aciertos is not None else None
        _di = float(disputados) if disputados is not None else None
        efectividad = round((_ac / _di) * 100, 1) if (_di and _di > 0 and _ac is not None) else None
        if efectividad is not None:
            efectividad = min(efectividad, 100.0)
    except (TypeError, ValueError, ZeroDivisionError):
        efectividad = None

    datos.append({
        "Posición": pos_actual, "Participante": nombre, "Puntos": puntos,
        "Tendencia": trend_icon, "Tendencia Clase": trend_cls,
        "Aciertos": aciertos, "Disputados": disputados, "Efectividad %": efectividad,
    })

st.session_state.posiciones_anteriores = nuevas_posiciones
df_full = pd.DataFrame(datos)

# ── Búsqueda y exportar ───────────────────────────────────────────────────────
col_search, col_export = st.columns([3, 1])
with col_search:
    busqueda = st.text_input("🔍  Buscar participante", placeholder="Nombre...")
with col_export:
    st.write("")
    if st.button("📥  Exportar Excel", use_container_width=True):
        buffer = exportar_ranking()
        st.download_button(
            "⬇️  Descargar",
            data=buffer,
            file_name="ranking_prode_2026.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

df = df_full.copy()
if busqueda:
    df = df[df["Participante"].str.contains(busqueda, case=False)]

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ── Tarjetas de ranking ───────────────────────────────────────────────────────
if df.empty:
    st.markdown("<div class='glass'><p style='text-align:center;opacity:.5'>Sin resultados para esa búsqueda.</p></div>", unsafe_allow_html=True)
else:
    pos_class = {1: "gold", 2: "silver", 3: "bronze"}
    for _, row in df.iterrows():
        pos, nombre, puntos = int(row["Posición"]), row["Participante"], row["Puntos"]
        trend_icon, trend_cls = row["Tendencia"], row["Tendencia Clase"]
        aciertos, disputados, efectividad = row["Aciertos"], row["Disputados"], row["Efectividad %"]
        pc = pos_class.get(pos, "")

        pills_html = ""
        if aciertos is not None and disputados is not None:
            pills_html += f'<div class="stat-pill"><span class="label">Aciertos</span> <span class="value">{int(aciertos)}/{int(disputados)}</span></div>'
        if efectividad is not None:
            bar_w = int(efectividad)
            pills_html += f'<div class="stat-pill"><span class="label">Efectividad</span> <span class="pct">{efectividad}%</span><div class="pct-bar-bg"><div class="pct-bar-fill" style="width:{bar_w}%"></div></div></div>'

        st.markdown(
            f'<div class="glass"><div class="rank-card">'
            f'<div class="rank-pos {pc}">{pos}</div>'
            f'<div class="trend {trend_cls}">{trend_icon}</div>'
            f'<div style="flex:1; min-width:0;"><div class="rank-name">{nombre}</div>'
            f'<div class="stats-row">{pills_html}</div></div>'
            f'<div><div class="rank-pts">{puntos}</div><div class="pts-label">puntos</div></div>'
            f'</div></div>',
            unsafe_allow_html=True
        )
