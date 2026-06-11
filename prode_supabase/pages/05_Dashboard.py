import streamlit as st
from database import conectar

st.set_page_config(page_title="Dashboard", layout="wide")

st.markdown("""
    <style>
    [data-testid="stApp"] {
        background-image: url('https://raw.githubusercontent.com/arcaltdfootball/PRODEFIFAWC2026UNQ/main/prode_supabase/dashboard.jpg');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }

    /* Recuadros blur para las métricas */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.18);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }

    /* Letras oscuras en las métricas */
    [data-testid="stMetricLabel"] p,
    [data-testid="stMetricLabel"] {
        color: #1e293b !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {
        color: #0f172a !important;
        font-weight: 700 !important;
    }

    /* Título oscuro */
    h1, h2, h3 { color: #0f172a !important; }
    </style>
""", unsafe_allow_html=True)

st.title("DASHBOARD")

try:
    sb = conectar()
except Exception as e:
    st.error(f"Error al conectar: {e}")
    st.stop()

# Contar con count="exact" para que Supabase devuelva el total real sin límite de 1000 filas
resp_part  = sb.table("participantes").select("id", count="exact").execute()
resp_part2 = sb.table("partidos").select("id, resultado").execute()
resp_pron  = sb.table("pronosticos").select("id", count="exact").execute()

total_participantes = resp_part.count
total_partidos      = len(resp_part2.data)
partidos_resueltos  = sum(1 for p in resp_part2.data if p.get("resultado"))
total_pronosticos   = resp_pron.count   # total real sin tope de 1000

# Aciertos: pronósticos sobre partidos ya jugados donde pronostico == resultado
# Se hace join del lado de Supabase para no traer miles de filas
resultados_map = {p["id"]: p["resultado"] for p in resp_part2.data if p.get("resultado")}
partidos_jugados_ids = list(resultados_map.keys())

aciertos = 0
if partidos_jugados_ids:
    # Traer solo los pronósticos de partidos con resultado (cantidad acotada)
    resp_comp = (
        sb.table("pronosticos")
        .select("partido_id, pronostico")
        .in_("partido_id", partidos_jugados_ids)
        .execute()
    )
    aciertos = sum(
        1 for pr in resp_comp.data
        if resultados_map.get(pr["partido_id"]) == pr["pronostico"]
    )

pron_comparables = len(resp_comp.data) if partidos_jugados_ids else 0
pct_aciertos = round((aciertos / pron_comparables) * 100, 1) if pron_comparables > 0 else 0.0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Participantes",        total_participantes)
col2.metric("Partidos jugados",     f"{partidos_resueltos} / {total_partidos}")
col3.metric("Pronósticos totales",  total_pronosticos)
col4.metric("Aciertos totales",     aciertos)
col5.metric("% Aciertos",           f"{pct_aciertos}%")
