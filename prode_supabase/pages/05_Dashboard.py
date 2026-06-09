import streamlit as st
from database import conectar

st.title("📊 DASHBOARD")

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
