import streamlit as st
import pandas as pd
import base64
import math
from pathlib import Path
from ranking import obtener_ranking, _fetch_all
from database import conectar

try:
    from excel_export import exportar_ranking
    TIENE_EXCEL = True
except ImportError:
    TIENE_EXCEL = False


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

st.set_page_config(
    page_title="Ranking - Liga Profesional Argentina",
    page_icon="🏅",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600;700&display=swap');

[data-testid="stAppViewContainer"] {
    background-image:
        linear-gradient(160deg, rgba(5,11,24,0.88) 0%, rgba(11,18,48,0.85) 45%, rgba(5,5,16,0.90) 100%),
        url('__FONDO_AFA2026__');
    background-size: cover, cover;
    background-position: center, center;
    background-repeat: no-repeat, no-repeat;
    background-attachment: fixed, fixed;
    background-color: #050510;
}
[data-testid="stHeader"] { background: transparent !important; }
* { box-sizing: border-box; }
html, body, p, span:not(.material-symbols-rounded):not(.material-icons):not([data-testid]), h1, h2, h3, h4, h5, h6, a, li, td, th, input, label {
    font-family: 'Inter', sans-serif;
}
[data-testid="stVerticalBlock"] { position: relative; z-index: 1; }

.hero-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(2rem, 5vw, 4rem);
    letter-spacing: 0.06em;
    line-height: 1;
    color: #fff;
    text-shadow: 0 0 30px rgba(96,165,250,0.45), 0 4px 16px rgba(0,0,0,0.8);
    margin: 0 0 2px 0;
}
.hero-sub {
    font-size: 0.8rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: rgba(96,165,250,0.85);
    font-weight: 500;
    margin-bottom: 6px;
}
.hero-rule {
    font-size: 0.78rem;
    color: rgba(255,255,255,0.55);
    margin-bottom: 16px;
}
.hero-rule b { color: #e8c96b; }
.glass {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 14px;
    backdrop-filter: blur(14px) saturate(1.2);
    -webkit-backdrop-filter: blur(14px) saturate(1.2);
    padding: 12px 16px;
    margin-bottom: 8px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}
.glass.gold-card {
    background: rgba(255,215,0,0.12);
    border: 1px solid rgba(255,215,0,0.45);
    box-shadow: 0 4px 20px rgba(255,215,0,0.2);
}
.glass.silver-card {
    background: rgba(192,192,192,0.1);
    border: 1px solid rgba(192,192,192,0.35);
    box-shadow: 0 4px 16px rgba(192,192,192,0.15);
}
.rank-card { display: flex; align-items: center; gap: 12px; position: relative; }
.rank-pos {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.2rem; line-height: 1;
    min-width: 40px; text-align: center;
    color: rgba(255,255,255,0.25);
}
.rank-pos.gold   { color: #FFD700; text-shadow: 0 0 14px rgba(255,215,0,0.6); }
.rank-pos.silver { color: #C0C0C0; text-shadow: 0 0 14px rgba(192,192,192,0.4); }
.rank-pos.bronze { color: #CD7F32; }
.rank-name { font-size: 1rem; font-weight: 700; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rank-pts { font-family: 'Bebas Neue', sans-serif; font-size: 1.8rem; color: #FFD700; line-height: 1; min-width: 60px; text-align: right; }
.pts-label { font-size: 0.6rem; letter-spacing: 0.2em; text-transform: uppercase; color: rgba(255,210,0,0.6); text-align: right; margin-top: -2px; }
.stats-row { display: flex; gap: 6px; margin-top: 6px; flex-wrap: wrap; }
.stat-pill {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 50px;
    padding: 3px 10px;
    font-size: 0.72rem;
    display: flex; align-items: center; gap: 4px;
    white-space: nowrap;
}
.stat-pill .label { color: rgba(255,255,255,0.45); font-weight: 300; }
.stat-pill .value { font-weight: 700; color: #fff; }
.stat-pill .pct   { font-weight: 800; color: #34d399; }
.stat-pill.exacto {
    background: rgba(232,201,107,0.15);
    border-color: rgba(232,201,107,0.35);
}
.stat-pill.exacto .label { color: rgba(232,201,107,0.8); }
.stat-pill.exacto .value { color: #e8c96b; }
.trend { font-size: 1rem; font-weight: 900; min-width: 22px; text-align: center; }
.trend.up   { color: #34d399; }
.trend.down { color: #f87171; }
.trend.same { color: rgba(255,255,255,0.3); }
.pct-bar-bg { width: 70px; height: 4px; background: rgba(255,255,255,0.1); border-radius: 99px; overflow: hidden; margin-top: 2px; display: inline-block; vertical-align: middle; }
.pct-bar-fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, #34d399, #059669); }
[data-testid="stTextInput"] input {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.18) !important;
    border-radius: 50px !important;
    color: #fff !important;
    font-size: 1rem !important;
    padding: 12px 20px !important;
    backdrop-filter: blur(10px);
}
[data-testid="stTextInput"] input::placeholder { color: rgba(255,255,255,0.35) !important; }
[data-testid="baseButton-secondary"], [data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #60a5fa 0%, #2563eb 100%) !important;
    color: #fff !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 50px !important;
    padding: 10px 28px !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.05em !important;
    box-shadow: 0 4px 20px rgba(37,99,235,0.4) !important;
}
.divider { height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.12), transparent); margin: 8px 0 20px; }

/* Tabs styling (por si se agregan zonas a futuro) */
[data-testid="stTabs"] [data-testid="stTab"] {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.1rem !important;
    letter-spacing: 0.08em !important;
    color: rgba(255,255,255,0.5) !important;
}
[data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"] {
    color: #60a5fa !important;
    border-bottom-color: #60a5fa !important;
}
[data-testid="stTabs"] {
    background: transparent !important;
}
</style>
""".replace("__FONDO_AFA2026__", _FONDO_AFA2026), unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='padding: 18px 0 6px 0;'>
    <div class='hero-title'>Ranking General</div>
    <div class='hero-sub'>Liga Profesional Argentina · Pronósticos</div>
    <div class='hero-rule'>Sistema de puntaje: <b>1 punto</b> por acertar el resultado (Local / Empate / Visitante) ·
    <b>3 puntos en total</b> si acertás el resultado exacto.</div>
</div>
""", unsafe_allow_html=True)

# ── Cargar datos ──────────────────────────────────────────────────────────────
try:
    sb = conectar()
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.stop()

try:
    ranking = obtener_ranking()
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.exception(e)
    st.stop()

# `obtener_ranking()` ya devuelve solo jugadores habilitados (pagaron y no
# están pausados por el admin) — el filtro vive en ranking.py.
try:
    _jugadores_raw = _fetch_all(
        lambda: sb.table("jugadores").select("id, nombre, pagado, activo")
    )
except Exception as e:
    st.error(f"No se pudo leer la lista de jugadores: {e}")
    _jugadores_raw = []

_ids_habilitados = {
    j["id"] for j in _jugadores_raw if j.get("pagado") and j.get("activo", True)
}


# ── Ranking mensual: agrupa por Fecha→Mes asignado desde el admin ──────────
def obtener_meses_disponibles():
    """Devuelve los meses configurados, ordenados cronológicamente según la
    fecha (jornada) más chica que tengan asignada."""
    try:
        filas = sb.table("fecha_mes_map").select("fecha_numero, mes").execute().data or []
    except Exception:
        return []
    orden = {}
    for r in filas:
        orden.setdefault(r["mes"], []).append(r["fecha_numero"])
    return sorted(orden.keys(), key=lambda m: min(orden[m]))


def obtener_ranking_mensual(mes, ids_habilitados):
    """Misma lógica de puntaje que ranking.obtener_ranking() (1 pto por
    signo, 3 en total si es exacto; "disputado" = el partido ya tiene
    goles_local/goles_visitante cargados), pero acotada a los partidos de
    las Fechas asignadas a `mes`."""
    fechas = [
        r["fecha_numero"]
        for r in sb.table("fecha_mes_map").select("fecha_numero").eq("mes", mes).execute().data or []
    ]
    if not fechas:
        return []

    partidos_mes = _fetch_all(
        lambda: sb.table("partidos")
        .select("id, goles_local, goles_visitante")
        .in_("fecha_numero", fechas)
    )
    partidos_por_id = {p["id"]: p for p in partidos_mes}
    if not partidos_por_id:
        return []

    pronos = _fetch_all(
        lambda: sb.table("pronosticos")
        .select("jugador_id, partido_id, puntos")
        .in_("partido_id", list(partidos_por_id.keys()))
    )

    agregados = {}
    for pr in pronos:
        jid = pr["jugador_id"]
        if jid not in ids_habilitados:
            continue
        partido = partidos_por_id.get(pr["partido_id"])
        if not partido:
            continue
        gl_real = partido.get("goles_local")
        gv_real = partido.get("goles_visitante")
        if gl_real is None or gv_real is None:
            continue  # partido todavía no jugado: no cuenta como disputado

        a = agregados.setdefault(jid, {"puntos": 0, "aciertos": 0, "disputados": 0, "aciertos_exactos": 0})
        a["disputados"] += 1
        pts = pr.get("puntos") or 0
        a["puntos"] += pts
        if pts >= 3:
            a["aciertos"] += 1
            a["aciertos_exactos"] += 1
        elif pts >= 1:
            a["aciertos"] += 1

    nombres_por_id = {j["id"]: j["nombre"] for j in _jugadores_raw}
    filas = [
        {
            "nombre": nombres_por_id.get(jid, f"Jugador {jid}"),
            "puntos": a["puntos"],
            "aciertos": a["aciertos"],
            "disputados": a["disputados"],
            "aciertos_exactos": a["aciertos_exactos"],
        }
        for jid, a in agregados.items()
    ]
    filas.sort(key=lambda x: x["puntos"], reverse=True)
    return filas


_meses_disponibles = obtener_meses_disponibles()

# ── Helpers ───────────────────────────────────────────────────────────────────
def calcular_efectividad(aciertos, disputados):
    try:
        ef = round((float(aciertos) / float(disputados)) * 100, 1) if disputados else None
        if ef is not None:
            if math.isnan(ef) or math.isinf(ef):
                return None
            return min(ef, 100.0)
    except (TypeError, ValueError, ZeroDivisionError):
        pass
    return None


def build_df(ranking_data, session_key):
    """Construye un DataFrame con posiciones y tendencias para el ranking."""
    if session_key not in st.session_state:
        st.session_state[session_key] = {}

    posiciones_anteriores = st.session_state[session_key]
    nuevas_posiciones = {}
    datos = []

    for i, row in enumerate(ranking_data):
        nombre     = row["nombre"]
        puntos     = row.get("puntos") or 0
        aciertos   = row.get("aciertos") or 0
        disputados = row.get("disputados") or 0
        exactos    = row.get("aciertos_exactos") or 0

        pos_actual = i + 1
        nuevas_posiciones[nombre] = pos_actual
        prev_pos = posiciones_anteriores.get(nombre, pos_actual)

        if prev_pos > pos_actual:
            trend_icon, trend_cls = "▲", "up"
        elif prev_pos < pos_actual:
            trend_icon, trend_cls = "▼", "down"
        else:
            trend_icon, trend_cls = "—", "same"

        efectividad = calcular_efectividad(aciertos, disputados)

        datos.append({
            "Posición": pos_actual, "Participante": nombre, "Puntos": puntos,
            "Tendencia": trend_icon, "Tendencia Clase": trend_cls,
            "Aciertos": aciertos, "Disputados": disputados, "Efectividad %": efectividad,
            "Exactos": exactos,
        })

    st.session_state[session_key] = nuevas_posiciones
    return pd.DataFrame(datos)


pos_class = {1: "gold", 2: "silver", 3: "bronze"}


def build_card(row, puntos_1):
    pos         = int(row["Posición"])
    nombre      = row["Participante"]
    puntos      = row["Puntos"]
    trend_icon  = row["Tendencia"]
    trend_cls   = row["Tendencia Clase"]
    aciertos    = row["Aciertos"]
    disputados  = row["Disputados"]
    efectividad = row["Efectividad %"]
    exactos     = row["Exactos"]

    pc = pos_class.get(pos, "")
    card_extra_class = "gold-card" if pos == 1 else ("silver-card" if pos == 2 else "")

    pills_html = ""

    # Aciertos de signo (1 punto)
    if aciertos is not None and disputados is not None:
        pills_html += (
            f'<div class="stat-pill">'
            f'<span class="label">Aciertos</span>'
            f'<span class="value">{int(aciertos)}/{int(disputados)}</span>'
            f'</div>'
        )

    # Efectividad
    if efectividad is not None and not math.isnan(efectividad):
        bar_w = int(efectividad)
        pills_html += (
            f'<div class="stat-pill">'
            f'<span class="label">Efectividad</span>'
            f'<span class="pct">{efectividad}%</span>'
            f'<div class="pct-bar-bg"><div class="pct-bar-fill" style="width:{bar_w}%"></div></div>'
            f'</div>'
        )

    # Resultados exactos (3 puntos en total)
    if exactos:
        pills_html += (
            f'<div class="stat-pill exacto">'
            f'<span class="label">Resultado exacto</span>'
            f'<span class="value">{int(exactos)}</span>'
            f'</div>'
        )

    # Diferencia vs 1°
    if puntos_1 is not None and pos != 1:
        diferencia = int(puntos_1) - int(puntos)
        pills_html += (
            f'<div class="stat-pill">'
            f'<span class="label">Vs. 1°</span>'
            f'<span class="value">-{diferencia} pts</span>'
            f'</div>'
        )

    return (
        f'<div class="glass {card_extra_class}" style="padding:8px 12px;margin-bottom:6px;">'
        f'<div class="rank-card" style="gap:8px;">'
        f'<div class="rank-pos {pc}" style="font-size:1.6rem;min-width:30px;">{pos}</div>'
        f'<div class="trend {trend_cls}" style="font-size:0.85rem;min-width:16px;">{trend_icon}</div>'
        f'<div style="flex:1; min-width:0;">'
        f'<div class="rank-name" style="font-size:0.85rem;">{nombre}</div>'
        f'<div class="stats-row" style="gap:4px;margin-top:3px;">{pills_html}</div>'
        f'</div>'
        f'<div>'
        f'<div class="rank-pts" style="font-size:1.4rem;">{puntos}</div>'
        f'<div class="pts-label">puntos</div>'
        f'</div>'
        f'</div></div>'
    )


def render_ranking(df_full, busqueda, session_key):
    df = df_full.copy()
    if busqueda:
        df = df[df["Participante"].str.contains(busqueda, case=False)]

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    if df.empty:
        st.markdown("<div class='glass'><p style='text-align:center;opacity:.5'>Sin resultados para esa búsqueda.</p></div>", unsafe_allow_html=True)
        return

    rows_list = list(df.iterrows())
    puntos_1 = df[df["Posición"] == 1]["Puntos"].values[0] if not df[df["Posición"] == 1].empty else None

    mid = (len(rows_list) + 1) // 2
    col_a, col_b = st.columns(2)

    with col_a:
        for _, row in rows_list[:mid]:
            st.markdown(build_card(row, puntos_1), unsafe_allow_html=True)

    with col_b:
        for _, row in rows_list[mid:]:
            st.markdown(build_card(row, puntos_1), unsafe_allow_html=True)


# ── Preparar DataFrame ────────────────────────────────────────────────────────
df_general = build_df(ranking, "pos_ant_general")

# ── Tabs: General + un tab por mes configurado ──────────────────────────────
_nombres_tabs = ["🏆 General"] + [f"🗓️ {m}" for m in _meses_disponibles]
_tabs = st.tabs(_nombres_tabs)

with _tabs[0]:
    busqueda = st.text_input("🔍  Buscar participante", placeholder="Nombre...", key="busq_general")

    if TIENE_EXCEL:
        col_exp, _ = st.columns([1, 4])
        with col_exp:
            try:
                excel_bytes = exportar_ranking(df_general)
                st.download_button(
                    "⬇️ Exportar ranking (Excel)",
                    data=excel_bytes,
                    file_name="ranking_liga_profesional_argentina.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_general",
                )
            except Exception:
                pass

    render_ranking(df_general, busqueda, "pos_ant_general")

for _tab, _mes in zip(_tabs[1:], _meses_disponibles):
    with _tab:
        _ranking_mes = obtener_ranking_mensual(_mes, _ids_habilitados)
        if not _ranking_mes:
            st.info(f"Todavía no hay puntos cargados para {_mes}.")
        else:
            _key_mes = f"pos_ant_mes_{_mes}"
            df_mes = build_df(_ranking_mes, _key_mes)
            busqueda_mes = st.text_input(
                "🔍  Buscar participante", placeholder="Nombre...", key=f"busq_{_mes}"
            )
            if TIENE_EXCEL:
                col_exp_m, _ = st.columns([1, 4])
                with col_exp_m:
                    try:
                        excel_bytes_m = exportar_ranking(df_mes)
                        st.download_button(
                            f"⬇️ Exportar ranking de {_mes} (Excel)",
                            data=excel_bytes_m,
                            file_name=f"ranking_{_mes.replace(' ', '_')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"dl_{_mes}",
                        )
                    except Exception:
                        pass
            render_ranking(df_mes, busqueda_mes, _key_mes)
