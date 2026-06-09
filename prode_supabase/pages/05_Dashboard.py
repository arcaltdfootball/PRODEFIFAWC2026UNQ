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

resp_part   = sb.table("participantes").select("id").execute()
resp_part2  = sb.table("partidos").select("id, resultado").execute()
resp_pron   = sb.table("pronosticos").select("id").execute()

total_participantes = len(resp_part.data)
total_partidos      = len(resp_part2.data)
partidos_resueltos  = sum(1 for p in resp_part2.data if p.get("resultado"))
total_pronosticos   = len(resp_pron.data)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Participantes",        total_participantes)
col2.metric("Partidos",             total_partidos)
col3.metric("Resultados cargados",  partidos_resueltos)
col4.metric("Pronósticos totales",  total_pronosticos)
