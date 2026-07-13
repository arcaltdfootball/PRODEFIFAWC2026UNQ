import streamlit as st

from posiciones import calcular_todas_las_posiciones
from escudos_map import url_escudo

st.set_page_config(
    page_title="Posiciones - Liga Profesional 2026",
    page_icon="🏆",
    layout="wide",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;600;700&display=swap');

    .zona-titulo {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2rem;
        letter-spacing: 0.08em;
        color: #FFD700;
        text-shadow: 0 0 20px rgba(255,215,0,0.35);
        text-align: center;
        margin: 6px 0 14px;
    }
    .tabla-wrapper {
        background: rgba(10,15,35,0.82);
        border: 1px solid rgba(255,215,0,0.25);
        border-radius: 18px;
        padding: 10px 14px 16px;
        box-shadow: 0 6px 30px rgba(0,0,0,0.4);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        margin-bottom: 24px;
    }
    table.tabla-posiciones {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Inter', sans-serif;
        color: rgba(255,255,255,0.85);
    }
    table.tabla-posiciones thead th {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: rgba(255,215,0,0.65);
        padding: 8px 6px;
        border-bottom: 1px solid rgba(255,215,0,0.25);
        text-align: center;
    }
    table.tabla-posiciones td {
        padding: 7px 6px;
        text-align: center;
        font-size: 0.88rem;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .col-equipo {
        text-align: left !important;
        display: flex;
        align-items: center;
        gap: 8px;
        white-space: nowrap;
    }
    .escudo-mini {
        width: 22px;
        height: 22px;
        object-fit: contain;
    }
    .col-pts {
        font-weight: 700;
        color: #FFD700;
    }
    tr:nth-child(-n+8) td.col-pos {
        color: #4ADE80;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 Tabla de Posiciones — Clausura 2026")
st.caption(
    "Zona A y Zona B de la Liga Profesional de Fútbol Argentino. "
    "Los partidos interzonales suman dentro de la zona propia de cada equipo."
)

try:
    tablas = calcular_todas_las_posiciones()
except Exception as e:
    st.error(f"No se pudo calcular la tabla de posiciones: {e}")
    st.stop()


def renderizar_zona(nombre_zona: str, filas: list):
    st.markdown(f'<div class="zona-titulo">Zona {nombre_zona}</div>', unsafe_allow_html=True)

    filas_html = []
    for f in filas:
        escudo = url_escudo(f["nombre"])
        img_html = f'<img src="{escudo}" class="escudo-mini">' if escudo else ""
        filas_html.append(
            "<tr>"
            f'<td class="col-pos">{f["pos"]}</td>'
            f'<td class="col-equipo">{img_html}<span>{f["nombre"]}</span></td>'
            f'<td>{f["pj"]}</td>'
            f'<td>{f["pg"]}</td>'
            f'<td>{f["pe"]}</td>'
            f'<td>{f["pp"]}</td>'
            f'<td>{f["gf"]}</td>'
            f'<td>{f["gc"]}</td>'
            f'<td>{f["dg"]}</td>'
            f'<td class="col-pts">{f["pts"]}</td>'
            "</tr>"
        )

    tabla_html = (
        '<div class="tabla-wrapper"><table class="tabla-posiciones">'
        "<thead><tr>"
        "<th>#</th><th style='text-align:left;'>Equipo</th><th>PJ</th><th>PG</th>"
        "<th>PE</th><th>PP</th><th>GF</th><th>GC</th><th>DG</th><th>Pts</th>"
        "</tr></thead><tbody>"
        + "".join(filas_html)
        + "</tbody></table></div>"
    )
    st.markdown(tabla_html, unsafe_allow_html=True)


col_a, col_b = st.columns(2)
with col_a:
    renderizar_zona("A", tablas["A"])
with col_b:
    renderizar_zona("B", tablas["B"])

st.caption(
    "🟢 En verde: posiciones de clasificación directa (ajustá la regla en el CSS "
    "`tr:nth-child(-n+8)` según cuántos equipos clasifiquen en tu formato)."
)
