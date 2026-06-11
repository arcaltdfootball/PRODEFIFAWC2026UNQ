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
resp_pron   = sb.table("pronosticos").select("participante_id, partido_id, pronostico").execute()

total_participantes = len(resp_part.data)
total_partidos      = len(resp_part2.data)
partidos_resueltos  = sum(1 for p in resp_part2.data if p.get("resultado"))

# Pronósticos completados: solo los que corresponden a partidos con resultado
resultados_map = {p["id"]: p["resultado"] for p in resp_part2.data if p.get("resultado")}
prons_con_resultado = [pr for pr in resp_pron.data if pr["partido_id"] in resultados_map]
total_pronosticos   = len(resp_pron.data)

# Aciertos reales: pronóstico == resultado del partido
aciertos = sum(
    1 for pr in prons_con_resultado
    if resultados_map.get(pr["partido_id"]) == pr["pronostico"]
)

# Porcentaje de aciertos sobre pronósticos que ya se pudieron comparar
pct_aciertos = round((aciertos / len(prons_con_resultado)) * 100, 1) if prons_con_resultado else 0.0

# Pronósticos posibles = participantes × partidos con resultado
posibles = total_participantes * partidos_resueltos
pct_completados = round((len(prons_con_resultado) / posibles) * 100, 1) if posibles > 0 else 0.0

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Participantes",         total_participantes)
col2.metric("Partidos jugados",      f"{partidos_resueltos} / {total_partidos}")
col3.metric("Pronósticos cargados",  total_pronosticos)
col4.metric("Comparables",           len(prons_con_resultado),
            help="Pronósticos sobre partidos ya jugados")
col5.metric("Aciertos totales",      aciertos)
col6.metric("% Aciertos",            f"{pct_aciertos}%",
            delta=f"{pct_completados}% cobertura")
