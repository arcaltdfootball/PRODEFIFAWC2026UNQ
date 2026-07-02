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

# ── Datos base ───────────────────────────────────────────────────────────────
resp_part  = sb.table("participantes").select("id, nombre", count="exact").execute()
resp_part2 = sb.table("partidos").select("id, resultado").execute()
resp_pron  = sb.table("pronosticos").select("id", count="exact").execute()

total_participantes   = resp_part.count
total_partidos        = len(resp_part2.data)
partidos_resueltos    = sum(1 for p in resp_part2.data if p.get("resultado"))
total_pronosticos     = resp_pron.count  # count real, sin tope de 1000

# Aciertos sobre partidos ya jugados
resultados_map        = {p["id"]: p["resultado"] for p in resp_part2.data if p.get("resultado")}
partidos_jugados_ids  = list(resultados_map.keys())
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
col1.metric("Participantes",       total_participantes)
col2.metric("Partidos jugados",    f"{partidos_resueltos} / {total_partidos}")
col3.metric("Pronósticos totales", total_pronosticos)
col4.metric("Aciertos totales",    aciertos)
col5.metric("% Aciertos",          f"{pct_aciertos}%")

# ── Estado de boletas ─────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 📋 Estado de boletas")

total_partidos_torneo = total_partidos  # 72

# Contar pronósticos POR PARTICIPANTE con count="exact" — evita tope de 1000 filas
incompletos = []
completos   = []
for p in resp_part.data:
    p_id  = p["id"]
    p_nom = p["nombre"]
    # Una consulta de conteo por participante: precisa, sin riesgo de truncado
    r = (
        sb.table("pronosticos")
        .select("id", count="exact")
        .eq("participante_id", p_id)
        .execute()
    )
    cargados  = r.count
    faltantes = total_partidos_torneo - cargados
    if faltantes > 0:
        incompletos.append((p_nom, cargados, faltantes))
    else:
        completos.append(p_nom)

incompletos.sort(key=lambda x: -x[2])  # más faltantes primero

if not incompletos:
    st.markdown(
        '<div style="background:rgba(34,197,94,0.15);border:1.5px solid rgba(34,197,94,0.5);'
        'border-radius:12px;padding:16px 20px;display:flex;align-items:center;gap:12px;">'
        '<span style="font-size:30px">✅</span>'
        '<span style="color:#14532d;font-weight:700;font-size:16px;">'
        '¡Todos los participantes tienen su boleta completa ('
        + str(total_partidos_torneo) + '/' + str(total_partidos_torneo) + ')!'
        '</span></div>',
        unsafe_allow_html=True
    )
else:
    filas_html = ""
    for nombre, cargados, faltantes in incompletos:
        filas_html += (
            '<div style="display:flex;align-items:center;justify-content:space-between;'
            'padding:10px 16px;border-bottom:1px solid rgba(239,68,68,0.1);">'
            '<span style="font-weight:600;color:#1e293b;font-size:14px;">⚠️ &nbsp;' + nombre + '</span>'
            '<div style="display:flex;align-items:center;gap:10px;">'
            '<span style="color:#64748b;font-size:12px;">'
            + str(cargados) + ' / ' + str(total_partidos_torneo) + ' cargados</span>'
            '<span style="background:rgba(239,68,68,0.15);color:#b91c1c;border-radius:20px;'
            'padding:3px 14px;font-size:12px;font-weight:700;">Faltan ' + str(faltantes) + '</span>'
            '</div></div>'
        )

    st.markdown(
        '<div style="background:rgba(255,255,255,0.88);border:1.5px solid rgba(239,68,68,0.5);'
        'border-radius:14px;overflow:hidden;backdrop-filter:blur(10px);">'
        '<div style="background:rgba(239,68,68,0.1);padding:12px 18px;'
        'display:flex;align-items:center;gap:10px;">'
        '<span style="font-size:24px">🚨</span>'
        '<span style="font-weight:700;color:#7f1d1d;font-size:15px;">'
        + str(len(incompletos)) + ' participante(s) con boleta incompleta</span>'
        '</div>'
        + filas_html +
        '</div>',
        unsafe_allow_html=True
    )

    if completos:
        st.markdown(
            '<div style="margin-top:10px;background:rgba(34,197,94,0.12);'
            'border:1px solid rgba(34,197,94,0.35);border-radius:10px;'
            'padding:10px 16px;font-size:13px;color:#14532d;">'
            '<strong>✅ Boletas completas:</strong> &nbsp;'
            + ' &nbsp;·&nbsp; '.join(completos) +
            '</div>',
            unsafe_allow_html=True
        )

# ── DIECISEISAVOS DE FINAL ────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("## 🏆 Dieciseisavos de Final")

# NOTA: se asume columna "fase" en la tabla "partidos". El filtro ilike captura
# tanto "Dieciseisavos" como "Dieciseisavos de Final" sin importar mayúsculas.
resp_partidos_16 = (
    sb.table("partidos")
    .select("id, resultado")
    .ilike("fase", "%dieciseisavos%")
    .execute()
)

partidos_16          = resp_partidos_16.data
total_partidos_16    = len(partidos_16)
partidos_16_ids      = [p["id"] for p in partidos_16]
resueltos_16         = sum(1 for p in partidos_16 if p.get("resultado"))

# Pronósticos totales cargados para partidos de dieciseisavos
total_pronosticos_16 = 0
if partidos_16_ids:
    resp_pron_16 = (
        sb.table("pronosticos")
        .select("id", count="exact")
        .in_("partido_id", partidos_16_ids)
        .execute()
    )
    total_pronosticos_16 = resp_pron_16.count

# Aciertos sobre partidos de dieciseisavos ya jugados
resultados_map_16       = {p["id"]: p["resultado"] for p in partidos_16 if p.get("resultado")}
partidos_jugados_16_ids = list(resultados_map_16.keys())
aciertos_16 = 0
pron_comparables_16 = 0
if partidos_jugados_16_ids:
    resp_comp_16 = (
        sb.table("pronosticos")
        .select("partido_id, pronostico")
        .in_("partido_id", partidos_jugados_16_ids)
        .execute()
    )
    pron_comparables_16 = len(resp_comp_16.data)
    aciertos_16 = sum(
        1 for pr in resp_comp_16.data
        if resultados_map_16.get(pr["partido_id"]) == pr["pronostico"]
    )
pct_aciertos_16 = round((aciertos_16 / pron_comparables_16) * 100, 1) if pron_comparables_16 > 0 else 0.0

col1_16, col2_16, col3_16, col4_16, col5_16 = st.columns(5)
col1_16.metric("Participantes",       total_participantes)
col2_16.metric("Partidos jugados",    f"{resueltos_16} / {total_partidos_16}")
col3_16.metric("Pronósticos totales", total_pronosticos_16)
col4_16.metric("Aciertos totales",    aciertos_16)
col5_16.metric("% Aciertos",          f"{pct_aciertos_16}%")

# ── Estado de boletas — Dieciseisavos de Final ────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 📋 Estado de boletas — Dieciseisavos de Final")

incompletos_16 = []
completos_16   = []
if total_partidos_16 > 0:
    for p in resp_part.data:
        p_id  = p["id"]
        p_nom = p["nombre"]
        r16 = (
            sb.table("pronosticos")
            .select("id", count="exact")
            .eq("participante_id", p_id)
            .in_("partido_id", partidos_16_ids)
            .execute()
        )
        cargados_16  = r16.count
        faltantes_16 = total_partidos_16 - cargados_16
        if faltantes_16 > 0:
            incompletos_16.append((p_nom, cargados_16, faltantes_16))
        else:
            completos_16.append(p_nom)

    incompletos_16.sort(key=lambda x: -x[2])  # más faltantes primero

    if not incompletos_16:
        st.markdown(
            '<div style="background:rgba(34,197,94,0.15);border:1.5px solid rgba(34,197,94,0.5);'
            'border-radius:12px;padding:16px 20px;display:flex;align-items:center;gap:12px;">'
            '<span style="font-size:30px">✅</span>'
            '<span style="color:#14532d;font-weight:700;font-size:16px;">'
            '¡Todos los participantes tienen su boleta completa de Dieciseisavos ('
            + str(total_partidos_16) + '/' + str(total_partidos_16) + ')!'
            '</span></div>',
            unsafe_allow_html=True
        )
    else:
        filas_html_16 = ""
        for nombre, cargados_16, faltantes_16 in incompletos_16:
            filas_html_16 += (
                '<div style="display:flex;align-items:center;justify-content:space-between;'
                'padding:10px 16px;border-bottom:1px solid rgba(239,68,68,0.1);">'
                '<span style="font-weight:600;color:#1e293b;font-size:14px;">⚠️ &nbsp;' + nombre + '</span>'
                '<div style="display:flex;align-items:center;gap:10px;">'
                '<span style="color:#64748b;font-size:12px;">'
                + str(cargados_16) + ' / ' + str(total_partidos_16) + ' cargados</span>'
                '<span style="background:rgba(239,68,68,0.15);color:#b91c1c;border-radius:20px;'
                'padding:3px 14px;font-size:12px;font-weight:700;">Faltan ' + str(faltantes_16) + '</span>'
                '</div></div>'
            )

        st.markdown(
            '<div style="background:rgba(255,255,255,0.88);border:1.5px solid rgba(239,68,68,0.5);'
            'border-radius:14px;overflow:hidden;backdrop-filter:blur(10px);">'
            '<div style="background:rgba(239,68,68,0.1);padding:12px 18px;'
            'display:flex;align-items:center;gap:10px;">'
            '<span style="font-size:24px">🚨</span>'
            '<span style="font-weight:700;color:#7f1d1d;font-size:15px;">'
            + str(len(incompletos_16)) + ' participante(s) con boleta incompleta de Dieciseisavos</span>'
            '</div>'
            + filas_html_16 +
            '</div>',
            unsafe_allow_html=True
        )

        if completos_16:
            st.markdown(
                '<div style="margin-top:10px;background:rgba(34,197,94,0.12);'
                'border:1px solid rgba(34,197,94,0.35);border-radius:10px;'
                'padding:10px 16px;font-size:13px;color:#14532d;">'
                '<strong>✅ Boletas completas:</strong> &nbsp;'
                + ' &nbsp;·&nbsp; '.join(completos_16) +
                '</div>',
                unsafe_allow_html=True
            )
else:
    st.info("Todavía no hay partidos cargados para la fase de Dieciseisavos de Final.")
