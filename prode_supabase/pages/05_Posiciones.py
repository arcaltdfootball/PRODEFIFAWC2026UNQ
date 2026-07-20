import base64
from pathlib import Path

import streamlit as st

from posiciones import calcular_todas_las_posiciones
from escudos_map import url_escudo

# ══════════════════════════════════════════════════════════════════════════
# CONFIG — ajustá estos números según el formato del torneo
# ══════════════════════════════════════════════════════════════════════════
CLASIFICAN_TOP = 8      # cuántos puestos (desde el 1°) clasifican, en CADA zona


st.set_page_config(
    page_title="Posiciones - Liga Profesional 2026",
    page_icon="🏆",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def _fondo_pagina_datauri():
    """
    Busca AFA2026.png junto a este script (o en subcarpetas 'assets'/'static'
    del proyecto) y la devuelve como data URI en base64, para usarla de fondo
    sin depender de un link externo. Si no la encuentra, devuelve None y se
    usa una URL de respaldo.
    """
    candidatos = [
        Path(__file__).parent / "AFA2026.png",
        Path(__file__).parent / "assets" / "AFA2026.png",
        Path(__file__).parent / "static" / "AFA2026.png",
        Path(__file__).parent.parent / "AFA2026.png",
    ]
    for ruta in candidatos:
        try:
            if ruta.is_file():
                b64 = base64.b64encode(ruta.read_bytes()).decode()
                return f"data:image/png;base64,{b64}"
        except Exception:
            pass
    return None


_FONDO_AFA2026 = _fondo_pagina_datauri() or (
    "https://raw.githubusercontent.com/arcaltdfootball/PRODEFIFAWC2026UNQ/"
    "main/prode_supabase/AFA2026.png"
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600;700&display=swap');

    [data-testid="stAppViewContainer"] {
        background-image:
            linear-gradient(160deg, rgba(9,12,22,0.87) 0%, rgba(13,17,32,0.84) 45%, rgba(7,9,16,0.90) 100%),
            url('__FONDO_AFA2026__');
        background-size: cover, cover;
        background-position: center, center;
        background-repeat: no-repeat, no-repeat;
        background-attachment: fixed, fixed;
        background-color: #0b0f19;
    }
    [data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stVerticalBlock"] { position: relative; z-index: 1; }
    * { box-sizing: border-box; }

    /* ═══════════ HERO ═══════════ */
    .hero-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: clamp(2rem, 5vw, 3.6rem);
        letter-spacing: 0.06em;
        line-height: 1;
        color: #fff;
        text-shadow: 0 0 30px rgba(255,215,0,0.35), 0 4px 16px rgba(0,0,0,0.8);
        margin: 10px 0 2px 0;
        text-align: center;
    }
    .hero-sub {
        font-size: 0.8rem;
        letter-spacing: 0.25em;
        text-transform: uppercase;
        color: rgba(255,215,0,0.75);
        font-weight: 500;
        margin-bottom: 6px;
        text-align: center;
        font-family: 'Inter', sans-serif;
    }
    .hero-rule {
        font-size: 0.8rem;
        color: rgba(255,255,255,0.55);
        margin-bottom: 22px;
        text-align: center;
        font-family: 'Inter', sans-serif;
    }
    .hero-rule b { color: #e8c96b; }

    /* ═══════════ ZONA: encabezado ═══════════ */
    .zona-header {
        display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
        margin: 28px 0 14px;
    }
    .zona-titulo {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2.1rem;
        letter-spacing: 0.08em;
        color: #FFD700;
        text-shadow: 0 0 20px rgba(255,215,0,0.35);
        margin: 0;
        white-space: nowrap;
    }
    .zona-linea {
        flex: 1; height: 1px;
        background: linear-gradient(90deg, rgba(255,215,0,0.35), transparent);
        min-width: 40px;
    }

    /* ═══════════ TARJETA DE TABLA (glass) ═══════════ */
    .tabla-wrapper {
        background: rgba(10,15,35,0.78);
        border: 1px solid rgba(255,215,0,0.20);
        border-radius: 20px;
        padding: 4px;
        box-shadow: 0 10px 36px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.04);
        backdrop-filter: blur(18px) saturate(160%);
        -webkit-backdrop-filter: blur(18px) saturate(160%);
        margin-bottom: 30px;
        overflow: hidden;
    }
    /* Contenedor con scroll horizontal propio: esto evita que en pantallas
       chicas o con zoom distinto una columna quede "cortada" fuera del
       recuadro — ahora hace scroll DENTRO de la card en vez de desbordar. */
    .tabla-scroll {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        padding: 10px 10px 14px;
        scrollbar-width: thin;
        scrollbar-color: rgba(255,215,0,0.35) transparent;
    }
    .tabla-scroll::-webkit-scrollbar { height: 6px; }
    .tabla-scroll::-webkit-scrollbar-thumb {
        background: rgba(255,215,0,0.3); border-radius: 10px;
    }

    table.tabla-posiciones {
        width: 100%;
        min-width: 820px;
        border-collapse: collapse;
        font-family: 'Inter', sans-serif;
        color: rgba(255,255,255,0.85);
    }
    table.tabla-posiciones thead th {
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: rgba(255,215,0,0.65);
        padding: 10px 6px;
        border-bottom: 1px solid rgba(255,215,0,0.25);
        text-align: center;
        white-space: nowrap;
    }
    table.tabla-posiciones tbody tr {
        transition: background .15s ease;
    }
    table.tabla-posiciones tbody tr:hover {
        background: rgba(255,255,255,0.035);
    }
    table.tabla-posiciones td {
        padding: 8px 6px;
        text-align: center;
        font-size: 0.86rem;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        white-space: nowrap;
    }
    .col-equipo {
        text-align: left !important;
        display: flex;
        align-items: center;
        gap: 8px;
        white-space: nowrap;
        min-width: 190px;
    }
    .nombre-equipo-txt { overflow: hidden; text-overflow: ellipsis; }
    .escudo-mini {
        width: 30px;
        height: 30px;
        object-fit: contain;
        flex-shrink: 0;
    }
    .col-pts {
        font-weight: 800;
        color: #FFD700;
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.05rem;
        letter-spacing: 0.04em;
    }
    .col-dg-pos { color: #6bffb0; font-weight: 600; }
    .col-dg-neg { color: #ff8080; font-weight: 600; }
    .col-dg-neu { color: rgba(255,255,255,0.55); }

    /* ── Badge de posición: solo distingue "clasifica" (top N) ── */
    .pos-badge {
        display: inline-flex; align-items: center; justify-content: center;
        width: 28px; height: 28px; border-radius: 50%;
        font-weight: 700; font-family: 'Bebas Neue', sans-serif; font-size: 1rem;
    }
    .pos-badge.clasifica { background: rgba(74,222,128,0.18); color:#4ade80; border:1px solid rgba(74,222,128,0.45); box-shadow: 0 0 10px rgba(74,222,128,0.25); }
    .pos-badge.normal    { background: rgba(255,255,255,0.06); color: rgba(255,255,255,0.7); border:1px solid rgba(255,255,255,0.08); }

    /* ── Barra de efectividad ── */
    .ef-wrap { display: flex; flex-direction: column; align-items: center; gap: 3px; min-width: 78px; }
    .ef-pct { font-size: 0.82rem; font-weight: 700; }
    .ef-bar-bg {
        width: 68px; height: 5px; background: rgba(255,255,255,0.10);
        border-radius: 99px; overflow: hidden;
    }
    .ef-bar-fill { height: 100%; border-radius: 99px; }

    /* ── Leyenda ── */
    .leyenda {
        display: flex; gap: 16px; flex-wrap: wrap; margin: -6px 0 26px;
        font-family: 'Inter', sans-serif; font-size: 0.76rem; color: rgba(255,255,255,0.55);
    }
    </style>
    """.replace("__FONDO_AFA2026__", _FONDO_AFA2026),
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class='hero-title'>Tabla de Posiciones</div>
    <div class='hero-sub'>Liga Profesional Argentina · Clausura 2026</div>
    <div class='hero-rule'>Zona A y Zona B · los partidos <b>interzonales</b> suman
    dentro de la zona propia de cada equipo.</div>
    """,
    unsafe_allow_html=True,
)

try:
    tablas = calcular_todas_las_posiciones()
except Exception as e:
    st.error(f"No se pudo calcular la tabla de posiciones: {e}")
    st.stop()


def _pos_badge_html(pos: int, total: int) -> str:
    cls = "clasifica" if pos <= CLASIFICAN_TOP else "normal"
    return f'<span class="pos-badge {cls}">{pos}</span>'


def _dg_html(dg) -> str:
    try:
        dg = int(dg)
    except (TypeError, ValueError):
        return f'<span class="col-dg-neu">{dg}</span>'
    if dg > 0:
        return f'<span class="col-dg-pos">+{dg}</span>'
    if dg < 0:
        return f'<span class="col-dg-neg">{dg}</span>'
    return f'<span class="col-dg-neu">{dg}</span>'


def _efectividad_html(pts, pj) -> str:
    try:
        pj = int(pj)
        pts = int(pts)
    except (TypeError, ValueError):
        pj = 0
        pts = 0
    pct = round((pts / (pj * 3)) * 100, 1) if pj > 0 else 0.0
    pct = max(0.0, min(pct, 100.0))

    if pct >= 60:
        color_txt, color_grad = "#4ade80", "linear-gradient(90deg,#22c55e,#4ade80)"
    elif pct >= 40:
        color_txt, color_grad = "#e8c96b", "linear-gradient(90deg,#d97706,#e8c96b)"
    else:
        color_txt, color_grad = "#f87171", "linear-gradient(90deg,#dc2626,#f87171)"

    return (
        '<div class="ef-wrap">'
        f'<span class="ef-pct" style="color:{color_txt};">{pct}%</span>'
        f'<div class="ef-bar-bg"><div class="ef-bar-fill" '
        f'style="width:{pct}%;background:{color_grad};"></div></div>'
        "</div>"
    )


def renderizar_zona(nombre_zona: str, filas: list):
    if not filas:
        st.info(f"Todavía no hay datos para la Zona {nombre_zona}.")
        return

    total = len(filas)

    # ── Encabezado de zona ───────────────────────────────────────────────
    st.markdown(
        f'<div class="zona-header">'
        f'<div class="zona-titulo">Zona {nombre_zona}</div>'
        f'<div class="zona-linea"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Filas de la tabla ────────────────────────────────────────────────
    filas_html = []
    for f in filas:
        escudo = url_escudo(f["nombre"])
        img_html = f'<img src="{escudo}" class="escudo-mini">' if escudo else ""

        filas_html.append(
            "<tr>"
            f'<td>{_pos_badge_html(f["pos"], total)}</td>'
            f'<td class="col-equipo">{img_html}'
            f'<span class="nombre-equipo-txt">{f["nombre"]}</span></td>'
            f'<td>{f["pj"]}</td>'
            f'<td>{f["pg"]}</td>'
            f'<td>{f["pe"]}</td>'
            f'<td>{f["pp"]}</td>'
            f'<td>{f["gf"]}</td>'
            f'<td>{f["gc"]}</td>'
            f'<td>{_dg_html(f["dg"])}</td>'
            f'<td>{_efectividad_html(f["pts"], f["pj"])}</td>'
            f'<td class="col-pts">{f["pts"]}</td>'
            "</tr>"
        )

    tabla_html = (
        '<div class="tabla-wrapper"><div class="tabla-scroll">'
        '<table class="tabla-posiciones">'
        "<thead><tr>"
        "<th>#</th><th style='text-align:left;'>Equipo</th><th>PJ</th><th>PG</th>"
        "<th>PE</th><th>PP</th><th>GF</th><th>GC</th><th>DG</th>"
        "<th>Efectividad</th><th>Pts</th>"
        "</tr></thead><tbody>"
        + "".join(filas_html)
        + "</tbody></table></div></div>"
    )
    st.markdown(tabla_html, unsafe_allow_html=True)


# ── Zonas apiladas (una debajo de la otra) para aprovechar todo el ancho ──
renderizar_zona("A", tablas["A"])
renderizar_zona("B", tablas["B"])

st.markdown(
    f"""
    <div class="leyenda">
        <span>🟢 Clasifican los primeros {CLASIFICAN_TOP} de cada zona.</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(
    "La Efectividad muestra el rendimiento sobre los puntos posibles "
    "(puntos obtenidos / puntos en juego × 100). Ajustá `CLASIFICAN_TOP` "
    "al principio del archivo según el formato del torneo."
)
