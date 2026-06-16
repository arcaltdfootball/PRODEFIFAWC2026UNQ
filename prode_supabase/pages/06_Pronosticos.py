from flags import FLAGS
import streamlit as st
from database import conectar

st.set_page_config(
    page_title="Pronósticos por Partido",
    layout="centered"
)

st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">

    <style>
    body { font-family: 'DM Sans', sans-serif; color: #f1f5f9; }

    [data-testid="stApp"] {
        background-image: url('https://raw.githubusercontent.com/arcaltdfootball/PRODEFIFAWC2026UNQ/main/prode_supabase/FIFA666.jpg');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
        background-color: #0b0f19;
    }
    [data-testid="stAppViewContainer"] > div:first-child::before {
        content: '';
        position: fixed;
        inset: 0;
        background: rgba(11,15,25,0.80);
        z-index: 0;
        pointer-events: none;
    }
    [data-testid="stVerticalBlock"] { position: relative; z-index: 1; }

    h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 1px; }

    .main-label {
        font-size: 0.75rem; color: #94a3b8; text-align: center;
        text-transform: uppercase; letter-spacing: 3px; margin-bottom: 4px;
    }
    .main-title {
        font-size: 3.2rem; color: #e8c96b; text-align: center;
        margin-top: 0.2rem; margin-bottom: 1.5rem;
        text-shadow: 0 4px 12px rgba(0,0,0,0.5);
        font-family: 'Bebas Neue', sans-serif;
    }

    /* CARD PARTIDO */
    .partido-card {
        background: rgba(20,30,50,0.72);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 22px;
        padding: 22px 20px 18px;
        max-width: 580px;
        margin: 0 auto 20px;
        box-shadow: 0 16px 40px rgba(0,0,0,0.35);
    }

    /* META */
    .match-meta {
        font-size: 0.72rem; color: #64748b;
        text-align: center; text-transform: uppercase;
        letter-spacing: 1px; margin-bottom: 14px;
    }
    .match-meta i { color: #e8c96b; margin-right: 3px; }

    /* EQUIPOS */
    .teams-row {
        display: flex; align-items: center;
        justify-content: space-between; gap: 10px;
        margin-bottom: 16px;
    }
    .team-block {
        display: flex; flex-direction: column;
        align-items: center; gap: 8px; flex: 1;
    }
    .flag-img {
        width: 52px; height: 52px; object-fit: cover;
        border-radius: 50%;
        box-shadow: 0 4px 14px rgba(0,0,0,0.4);
        border: 2px solid rgba(255,255,255,0.12);
    }
    .team-name { font-size: 0.88rem; font-weight: 600; color: #e2e8f0; text-align: center; }
    .vs-text {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.8rem; color: #e8c96b;
        letter-spacing: 2px; line-height: 1;
    }

    /* RESULTADO REAL */
    .resultado-real {
        text-align: center; margin-bottom: 14px;
    }
    .resultado-pill {
        display: inline-block;
        background: rgba(34,197,94,0.15); color: #4ade80;
        border: 1px solid rgba(34,197,94,0.3);
        border-radius: 20px; padding: 4px 16px;
        font-size: 0.8rem; font-weight: 700;
    }
    .resultado-pill.pending {
        background: rgba(255,255,255,0.04); color: #64748b;
        border: 1px dashed rgba(255,255,255,0.12);
        font-weight: 400;
    }

    /* BARRA CONTEO */
    .conteo-titulo {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 0.85rem; color: #94a3b8;
        text-transform: uppercase; letter-spacing: 2px;
        margin-bottom: 10px; text-align: center;
    }
    .barra-wrap {
        display: flex; gap: 6px; align-items: stretch;
        margin-bottom: 12px;
    }
    .barra-opcion {
        flex: 1; border-radius: 12px; padding: 10px 8px 8px;
        text-align: center; position: relative;
        border: 1px solid rgba(255,255,255,0.07);
    }
    .barra-opcion.op1  { background: rgba(34,197,94,0.12);  border-color: rgba(34,197,94,0.25); }
    .barra-opcion.opX  { background: rgba(232,201,107,0.10); border-color: rgba(232,201,107,0.25); }
    .barra-opcion.op2  { background: rgba(239,68,68,0.12);  border-color: rgba(239,68,68,0.25); }
    .barra-label {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.4rem; line-height: 1;
    }
    .barra-opcion.op1 .barra-label  { color: #4ade80; }
    .barra-opcion.opX .barra-label  { color: #e8c96b; }
    .barra-opcion.op2 .barra-label  { color: #f87171; }
    .barra-sublabel {
        font-size: 0.68rem; color: #94a3b8;
        margin-top: 2px; margin-bottom: 6px;
    }
    .barra-count {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2.4rem; line-height: 1;
        color: #fff;
    }
    .barra-pct {
        font-size: 0.72rem; color: #64748b; margin-top: 1px;
    }

    /* NOMBRES DE APOSTADORES */
    .apostadores-wrap {
        margin-top: 4px;
    }
    .chips-row {
        display: flex; flex-wrap: wrap; gap: 5px;
        justify-content: center; margin-top: 5px;
    }
    .chip {
        font-size: 0.72rem; font-family: 'DM Sans', sans-serif;
        font-weight: 600; border-radius: 20px;
        padding: 3px 10px;
    }
    .chip.c1 { background: rgba(34,197,94,0.18);  color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .chip.cX { background: rgba(232,201,107,0.15); color: #e8c96b; border: 1px solid rgba(232,201,107,0.3); }
    .chip.c2 { background: rgba(239,68,68,0.18);  color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
    .chip.cn { background: rgba(100,116,139,0.12); color: #475569; border: 1px dashed rgba(100,116,139,0.3); }

    /* SIN APUESTAS */
    .sin-apuestas {
        text-align: center; color: #475569; font-size: 0.8rem;
        padding: 8px 0 4px; letter-spacing: 0.5px;
    }

    /* GRUPO LABEL */
    .grupo-activo-label {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1rem; color: #e8c96b;
        text-align: center; letter-spacing: 3px;
        margin-bottom: 10px; text-transform: uppercase;
    }

    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-label">Fixture Oficial · FIFA World Cup 2026</p>', unsafe_allow_html=True)
st.markdown('<h1 class="main-title">PRONÓSTICOS</h1>', unsafe_allow_html=True)

# ── Conexión ────────────────────────────────────────────────────────────────────
try:
    sb = conectar()
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.stop()

# ── Datos ───────────────────────────────────────────────────────────────────────
# Supabase/PostgREST limita cada consulta a un máximo de 1000 filas por defecto.
# Con muchos participantes y partidos, la tabla "pronosticos" supera fácilmente
# esa cantidad de filas, así que sin paginar se perdían pronósticos reales y
# aparecían como "Sin pronóstico" aunque el participante sí había apostado.
# Esta función trae TODAS las filas, pidiendo de a "page_size" por vez.
def fetch_all(table_name, columns, order_cols=None, page_size=1000):
    rows = []
    start = 0
    while True:
        query = sb.table(table_name).select(columns)
        if order_cols:
            for col in order_cols:
                query = query.order(col)
        chunk = query.range(start, start + page_size - 1).execute().data or []
        rows.extend(chunk)
        if len(chunk) < page_size:
            break
        start += page_size
    return rows

partidos_raw = fetch_all("partidos", "*", order_cols=["grupo", "fecha", "hora"])

participantes_raw = fetch_all("participantes", "id, nombre", order_cols=["nombre"])

pronosticos_raw = fetch_all(
    "pronosticos", "participante_id, partido_id, pronostico"
)

if not partidos_raw:
    st.info("No hay partidos registrados todavía.")
    st.stop()

# ── Índices ─────────────────────────────────────────────────────────────────────
# participante_id → nombre (clave normalizada a string)
part_nombre = {str(p["id"]): p["nombre"] for p in participantes_raw}
total_participantes = len(participantes_raw)

# partido_id → {participante_id: pronostico}
# Las claves se normalizan a string para que coincidan sin importar si
# Supabase devuelve los ids como int o como str en cada tabla.
pron_por_partido = {}
for pr in pronosticos_raw:
    pid  = str(pr["partido_id"])
    uid  = str(pr["participante_id"])
    val  = pr["pronostico"]
    pron_por_partido.setdefault(pid, {})[uid] = val

# Agrupar partidos por grupo
partidos_por_grupo = {}
for p in partidos_raw:
    g = p["grupo"]
    partidos_por_grupo.setdefault(g, []).append(p)

grupos_lista = sorted(partidos_por_grupo.keys())

# ── Estado ──────────────────────────────────────────────────────────────────────
if "grupo_activo" not in st.session_state:
    st.session_state["grupo_activo"] = grupos_lista[0]

# ── Tabs de grupos ───────────────────────────────────────────────────────────────
cols = st.columns(len(grupos_lista))
for i, g in enumerate(grupos_lista):
    with cols[i]:
        es_activo = g == st.session_state["grupo_activo"]
        if st.button(g, key=f"tab_{g}", use_container_width=True,
                     type="primary" if es_activo else "secondary"):
            st.session_state["grupo_activo"] = g
            st.session_state[f"pron_idx_{g}"] = 0
            st.rerun()

grupo_sel   = st.session_state["grupo_activo"]
lista_part  = partidos_por_grupo[grupo_sel]
total       = len(lista_part)

st.markdown(
    '<p class="grupo-activo-label">GRUPO ' + grupo_sel + "</p>",
    unsafe_allow_html=True,
)

# ── Navegación por partido ───────────────────────────────────────────────────────
key_idx = f"pron_idx_{grupo_sel}"
if key_idx not in st.session_state:
    st.session_state[key_idx] = 0
idx = st.session_state[key_idx]
if idx >= total:
    idx = 0
    st.session_state[key_idx] = 0

p = lista_part[idx]
p_id      = p["id"]
local     = p["local"]
visitante = p["visitante"]
fecha     = p["fecha"]
hora      = p.get("hora", "")
sede      = p.get("sede", "")
resultado = p.get("resultado") or ""

# ── Flags ───────────────────────────────────────────────────────────────────────
def flag_html(pais, size=52):
    url = FLAGS.get(pais, "")
    if url:
        return f'<img src="{url}" class="flag-img" style="width:{size}px;height:{size}px;">'
    return '<span style="font-size:40px">🏳️</span>'

# ── Conteo de pronósticos para este partido ─────────────────────────────────────
apuestas = pron_por_partido.get(str(p_id), {})
votos_1  = {uid: part_nombre.get(uid, f"#{uid}") for uid, v in apuestas.items() if v == "1"}
votos_X  = {uid: part_nombre.get(uid, f"#{uid}") for uid, v in apuestas.items() if v == "X"}
votos_2  = {uid: part_nombre.get(uid, f"#{uid}") for uid, v in apuestas.items() if v == "2"}
sin_voto = {
    p2["id"]: p2["nombre"]
    for p2 in participantes_raw
    if str(p2["id"]) not in apuestas
}

n1  = len(votos_1)
nX  = len(votos_X)
n2  = len(votos_2)
n_sin = len(sin_voto)
total_con_voto = n1 + nX + n2

def pct(n):
    return f"{round(n / total_con_voto * 100)}%" if total_con_voto else "—"

# ── Resultado real badge ─────────────────────────────────────────────────────────
if resultado:
    labels_r = {"1": "Gana " + local, "X": "Empate", "2": "Gana " + visitante}
    res_html = (
        '<div class="resultado-real">'
        '<span class="resultado-pill">⚽ Resultado: '
        + labels_r.get(resultado, resultado)
        + "</span></div>"
    )
else:
    res_html = (
        '<div class="resultado-real">'
        '<span class="resultado-pill pending">Partido no jugado</span>'
        "</div>"
    )

# ── Chips helpers ────────────────────────────────────────────────────────────────
def chips_html(nombres_dict, cls):
    if not nombres_dict:
        return '<div class="sin-apuestas">—</div>'
    return (
        '<div class="chips-row">'
        + "".join(
            f'<span class="chip {cls}">{nom}</span>'
            for nom in sorted(nombres_dict.values())
        )
        + "</div>"
    )

# ── Renderizar card ──────────────────────────────────────────────────────────────
meta_parts = []
if fecha:
    meta_parts.append(f'<i class="ti ti-calendar-event"></i> {fecha}')
if hora:
    meta_parts.append(f'<i class="ti ti-clock"></i> {hora}')
if sede:
    meta_parts.append(f'<i class="ti ti-map-pin"></i> {sede}')
meta_str = "&nbsp;&nbsp;|&nbsp;&nbsp;".join(meta_parts)

card_html = (
    '<div class="partido-card">'
    # meta
    + (f'<div class="match-meta">{meta_str}</div>' if meta_str else "")
    # equipos
    + '<div class="teams-row">'
    + f'<div class="team-block">{flag_html(local)}<span class="team-name">{local}</span></div>'
    + '<div><span class="vs-text">VS</span></div>'
    + f'<div class="team-block">{flag_html(visitante)}<span class="team-name">{visitante}</span></div>'
    + "</div>"
    # resultado real
    + res_html
    # separador
    + '<hr style="border:none;border-top:1px solid rgba(255,255,255,0.07);margin:0 0 14px;">'
    # conteo
    + '<div class="conteo-titulo">¿Quién apostó a qué?</div>'
    + '<div class="barra-wrap">'
    # columna 1
    + '<div class="barra-opcion op1">'
    + f'<div class="barra-label">1</div>'
    + f'<div class="barra-sublabel">Gana {local}</div>'
    + f'<div class="barra-count">{n1}</div>'
    + f'<div class="barra-pct">{pct(n1)}</div>'
    + chips_html(votos_1, "c1")
    + "</div>"
    # columna X
    + '<div class="barra-opcion opX">'
    + '<div class="barra-label">X</div>'
    + '<div class="barra-sublabel">Empate</div>'
    + f'<div class="barra-count">{nX}</div>'
    + f'<div class="barra-pct">{pct(nX)}</div>'
    + chips_html(votos_X, "cX")
    + "</div>"
    # columna 2
    + '<div class="barra-opcion op2">'
    + f'<div class="barra-label">2</div>'
    + f'<div class="barra-sublabel">Gana {visitante}</div>'
    + f'<div class="barra-count">{n2}</div>'
    + f'<div class="barra-pct">{pct(n2)}</div>'
    + chips_html(votos_2, "c2")
    + "</div>"
    + "</div>"  # /barra-wrap
)

# Sin pronóstico
if sin_voto:
    card_html += (
        '<div style="margin-top:6px;">'
        '<div class="barra-sublabel" style="text-align:center;margin-bottom:5px;">'
        f"Sin pronóstico ({n_sin})</div>"
        + chips_html(sin_voto, "cn")
        + "</div>"
    )

card_html += "</div>"  # /partido-card

st.markdown(card_html, unsafe_allow_html=True)

# ── Dots de navegación ───────────────────────────────────────────────────────────
dots_inner = ""
for i in range(total):
    if i == idx:
        dots_inner += "<div style='width:20px;height:6px;border-radius:3px;background:#e8c96b'></div>"
    else:
        dots_inner += "<div style='width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,0.15)'></div>"

st.markdown(
    '<div style="display:flex;justify-content:center;gap:6px;align-items:center;'
    'background:rgba(15,23,42,0.5);backdrop-filter:blur(12px);border:1px solid '
    'rgba(255,255,255,0.07);border-radius:14px;padding:10px 20px;max-width:560px;margin:0 auto 4px;">'
    + dots_inner
    + "</div>"
    + f'<p style="text-align:center;font-size:0.72rem;color:#475569;letter-spacing:1px;margin-top:4px;">'
    f"Partido {idx + 1} de {total}</p>",
    unsafe_allow_html=True,
)

# ── Botones prev / next ──────────────────────────────────────────────────────────
_, col_prev, _, col_next, _ = st.columns([1, 1, 4, 1, 1])
with col_prev:
    if st.button("◀", key="prev_btn", disabled=(idx == 0)):
        st.session_state[key_idx] = idx - 1
        st.rerun()
with col_next:
    if st.button("▶", key="next_btn", disabled=(idx == total - 1)):
        st.session_state[key_idx] = idx + 1
        st.rerun()
