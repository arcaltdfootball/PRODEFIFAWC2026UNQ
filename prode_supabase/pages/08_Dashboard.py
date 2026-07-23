import base64
from pathlib import Path

import streamlit as st
from database import conectar

st.set_page_config(page_title="Dashboard", layout="wide")


@st.cache_data(show_spinner=False)
def _fondo_dashboard_datauri():
    """
    Busca dashboard.png junto a este script (o en subcarpetas 'assets'/'static'
    del proyecto) y la devuelve como data URI en base64, para usarla de fondo
    sin depender de un link externo. Si no la encuentra, devuelve None y se
    usa una URL de respaldo.
    """
    candidatos = [
        Path(__file__).parent / "dashboard.png",
        Path(__file__).parent / "assets" / "dashboard.png",
        Path(__file__).parent / "static" / "dashboard.png",
        Path(__file__).parent.parent / "dashboard.png",
    ]
    for ruta in candidatos:
        try:
            if ruta.is_file():
                b64 = base64.b64encode(ruta.read_bytes()).decode()
                return f"data:image/png;base64,{b64}"
        except Exception:
            pass
    return None


_FONDO_DASHBOARD = _fondo_dashboard_datauri() or (
    "https://raw.githubusercontent.com/arcaltdfootball/PRODEFIFAWC2026UNQ/"
    "main/prode_supabase/dashboard.png"
)

st.markdown(f"""
    <style>
    [data-testid="stApp"] {{
        background-image: url('{_FONDO_DASHBOARD}');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }}

    /* Recuadros blur para las métricas */
    [data-testid="stMetric"] {{
        background: rgba(255, 255, 255, 0.18);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }}

    /* Letras oscuras en las métricas */
    [data-testid="stMetricLabel"] p,
    [data-testid="stMetricLabel"] {{
        color: #1e293b !important;
        font-weight: 600 !important;
    }}
    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {{
        color: #0f172a !important;
        font-weight: 700 !important;
    }}

    /* Título oscuro */
    h1, h2, h3 {{ color: #0f172a !important; }}
    </style>
""", unsafe_allow_html=True)

st.title("DASHBOARD")
st.caption("Prode Liga Profesional Argentina")

try:
    sb = conectar()
except Exception as e:
    st.error(f"Error al conectar: {e}")
    st.stop()

# ── Datos base (esquema real: jugadores / partidos / pronosticos) ─────────────
# jugadores(id, nombre, username, password_hash)
# partidos(id, zona, fecha_numero, equipo_local, equipo_visitante,
#          fecha_partido, hora, estadio, goles_local, goles_visitante)
# pronosticos(id, jugador_id, partido_id, signo_pred, goles_local_pred,
#             goles_visitante_pred, puntos, sin_marcador)
resp_jug   = sb.table("jugadores").select("id, nombre", count="exact").execute()
resp_part2 = sb.table("partidos").select("id, goles_local, goles_visitante").execute()
resp_pron  = sb.table("pronosticos").select("id", count="exact").execute()

total_participantes   = resp_jug.count
total_partidos        = len(resp_part2.data)
partidos_resueltos    = sum(
    1 for p in resp_part2.data
    if p.get("goles_local") is not None and p.get("goles_visitante") is not None
)
total_pronosticos     = resp_pron.count  # count real, sin tope de 1000

# Aciertos sobre partidos ya jugados.
# El puntaje ya viene calculado y guardado en `puntos` (0 / 1 / 3) cada vez
# que se carga un resultado en 03_Fixture.py, así que no hace falta volver a
# comparar signos acá: alcanza con mirar qué pronósticos tienen `puntos` no
# nulo (= partido ya jugado) y cuántos de esos son >= 1 (acertaron al menos
# el signo Local/Empate/Visitante). Se pagina por si hay más de 1000 filas.
puntos_rows = []
page_size = 1000
start = 0
while True:
    resp_page = (
        sb.table("pronosticos")
        .select("puntos")
        .not_.is_("puntos", "null")
        .range(start, start + page_size - 1)
        .execute()
    )
    puntos_rows.extend(resp_page.data)
    if len(resp_page.data) < page_size:
        break
    start += page_size

pron_comparables = len(puntos_rows)
aciertos         = sum(1 for r in puntos_rows if (r.get("puntos") or 0) >= 1)
marcadores_exactos = sum(1 for r in puntos_rows if (r.get("puntos") or 0) == 3)
pct_aciertos = round((aciertos / pron_comparables) * 100, 1) if pron_comparables > 0 else 0.0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Participantes",       total_participantes)
col2.metric("Partidos jugados",    f"{partidos_resueltos} / {total_partidos}")
col3.metric("Pronósticos totales", total_pronosticos)
col4.metric("Aciertos totales",    aciertos)
col5.metric("% Aciertos",          f"{pct_aciertos}%")

st.caption(f"🎯 Marcadores exactos acertados (3 puntos): {marcadores_exactos}")

# ── Estado de boletas ─────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 📋 Estado de boletas")

total_partidos_torneo = total_partidos

# Contar pronósticos POR JUGADOR con count="exact" — evita tope de 1000 filas
incompletos = []
completos   = []
for j in resp_jug.data:
    j_id  = j["id"]
    j_nom = j["nombre"]
    # Una consulta de conteo por jugador: precisa, sin riesgo de truncado
    r = (
        sb.table("pronosticos")
        .select("id", count="exact")
        .eq("jugador_id", j_id)
        .execute()
    )
    cargados  = r.count
    faltantes = total_partidos_torneo - cargados
    if faltantes > 0:
        incompletos.append((j_nom, cargados, faltantes))
    else:
        completos.append(j_nom)

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
