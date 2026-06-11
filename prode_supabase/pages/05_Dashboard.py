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

# Contar con count="exact" para que Supabase devuelva el total real sin límite de 1000 filas
resp_part  = sb.table("participantes").select("id, nombre", count="exact").execute()
resp_pron  = sb.table("pronosticos").select("id", count="exact").execute()

total_participantes = resp_part.count
total_pronosticos   = resp_pron.count

# Aciertos: pronósticos sobre partidos ya jugados donde pronostico == resultado
resultados_map = {p["id"]: p["resultado"] for p in resp_part2.data if p.get("resultado")}
partidos_jugados_ids = list(resultados_map.keys())

aciertos = 0
pron_comparables = 0
if partidos_jugados_ids:
    resp_comp = (
        sb.table("pronosticos")
        .select("partido_id, pronostico")
        .in_("partido_id", partidos_jugados_ids)
        .execute()
    )
    pron_comparables = len(resp_comp.data)
    aciertos = sum(
        1 for pr in resp_comp.data
        if resultados_map.get(pr["partido_id"]) == pr["pronostico"]
    )

pct_aciertos = round((aciertos / pron_comparables) * 100, 1) if pron_comparables > 0 else 0.0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Participantes",        total_participantes)
col2.metric("Partidos jugados",     f"{partidos_resueltos} / {total_partidos}")
col3.metric("Pronósticos totales",  total_pronosticos)
col4.metric("Aciertos totales",     aciertos)
col5.metric("% Aciertos",           f"{pct_aciertos}%")

# ── Alerta de pronósticos faltantes ──────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 📋 Estado de boletas")

# Partidos pendientes (sin resultado aún) — esos son los que hay que pronosticar
partidos_pendientes_ids = [p["id"] for p in resp_part2.data if not p.get("resultado")]
total_pendientes = len(partidos_pendientes_ids)

if total_pendientes == 0:
    st.markdown(
        '<div style="background:rgba(34,197,94,0.15);border:1.5px solid rgba(34,197,94,0.5);'
        'border-radius:12px;padding:14px 20px;display:flex;align-items:center;gap:12px;">'
        '<span style="font-size:28px;">✅</span>'
        '<span style="color:#14532d;font-weight:600;font-size:15px;">'
        'Todos los partidos ya tienen resultado. No hay pronósticos pendientes.'
        '</span></div>',
        unsafe_allow_html=True
    )
else:
    # Para cada participante, ver cuántos de los partidos pendientes les falta pronosticar
    participantes_lista = resp_part.data  # tiene id y nombre
    
    # Traer todos los pronósticos sobre partidos pendientes
    resp_pron_pend = (
        sb.table("pronosticos")
        .select("participante_id, partido_id")
        .in_("partido_id", partidos_pendientes_ids)
        .execute()
    )
    # {participante_id: set de partido_ids pronosticados}
    prons_por_part = {}
    for pr in resp_pron_pend.data:
        pid = pr["participante_id"]
        prons_por_part.setdefault(pid, set())
        prons_por_part[pid].add(pr["partido_id"])

    incompletos = []
    completos   = []
    for p in participantes_lista:
        p_id  = p["id"]
        p_nom = p["nombre"]
        cargados  = len(prons_por_part.get(p_id, set()))
        faltantes = total_pendientes - cargados
        if faltantes > 0:
            incompletos.append((p_nom, cargados, faltantes))
        else:
            completos.append(p_nom)

    if not incompletos:
        st.markdown(
            '<div style="background:rgba(34,197,94,0.15);border:1.5px solid rgba(34,197,94,0.5);'
            'border-radius:12px;padding:14px 20px;display:flex;align-items:center;gap:12px;">'
            '<span style="font-size:28px;">✅</span>'
            '<span style="color:#14532d;font-weight:700;font-size:16px;">'
            '¡Todos los participantes tienen sus boletas completas!'
            '</span></div>',
            unsafe_allow_html=True
        )
    else:
        # Alerta de incompletos
        filas_html = ""
        for nombre, cargados, faltantes in sorted(incompletos, key=lambda x: -x[2]):
            filas_html += (
                '<div style="display:flex;align-items:center;justify-content:space-between;'
                'padding:8px 12px;border-bottom:1px solid rgba(239,68,68,0.12);">'
                '<span style="font-weight:600;color:#1e293b;font-size:14px;">⚠️ ' + nombre + '</span>'
                '<span style="background:rgba(239,68,68,0.12);color:#b91c1c;border-radius:20px;'
                'padding:3px 12px;font-size:12px;font-weight:700;">'
                'Faltan ' + str(faltantes) + ' de ' + str(total_pendientes) + '</span>'
                '</div>'
            )

        st.markdown(
            '<div style="background:rgba(254,242,242,0.9);border:1.5px solid rgba(239,68,68,0.45);'
            'border-radius:14px;overflow:hidden;">'
            '<div style="background:rgba(239,68,68,0.12);padding:12px 16px;'
            'display:flex;align-items:center;gap:10px;border-bottom:1px solid rgba(239,68,68,0.2);">'
            '<span style="font-size:22px;">🚨</span>'
            '<span style="font-weight:700;color:#7f1d1d;font-size:15px;">'
            + str(len(incompletos)) + ' participante(s) con pronósticos incompletos'
            '</span></div>'
            + filas_html +
            '</div>',
            unsafe_allow_html=True
        )

        if completos:
            completos_str = " · ".join(["✅ " + n for n in completos])
            st.markdown(
                '<div style="margin-top:10px;background:rgba(34,197,94,0.1);'
                'border:1px solid rgba(34,197,94,0.3);border-radius:10px;'
                'padding:10px 16px;font-size:13px;color:#14532d;">'
                '<strong>Boletas completas:</strong> ' + completos_str +
                '</div>',
                unsafe_allow_html=True
            )
