from flags import FLAGS, get_flag
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

    /* CHIP CON MARCADOR DEBAJO */
    .chip-stack {
        display: flex; flex-direction: column; align-items: center; gap: 2px;
    }
    .chip-marcador {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 0.78rem; letter-spacing: 0.5px;
        color: #94a3b8;
    }

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

    /* TABS PRINCIPALES (Fase de Grupos / Dieciseisavos) */
    [data-baseweb="tab-list"] {
        gap: 14px;
        background: rgba(20,30,50,0.55);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 20px;
        padding: 10px;
        margin: 0 auto 28px;
        max-width: 640px;
        box-shadow: 0 16px 40px rgba(0,0,0,0.35);
    }
    [data-baseweb="tab"] {
        flex: 1;
        background: rgba(255,255,255,0.03);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 16px 18px !important;
        transition: all 0.25s ease;
    }
    [data-baseweb="tab"] p {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.35rem !important;
        letter-spacing: 1.5px;
        color: #cbd5e1 !important;
    }
    [data-baseweb="tab"]:hover {
        background: rgba(232,201,107,0.10);
        border-color: rgba(232,201,107,0.3);
        transform: translateY(-2px);
    }
    [data-baseweb="tab"][aria-selected="true"] {
        background: rgba(232,201,107,0.18);
        border-color: rgba(232,201,107,0.55);
        box-shadow: 0 8px 24px rgba(232,201,107,0.18);
    }
    [data-baseweb="tab"][aria-selected="true"] p {
        color: #e8c96b !important;
        text-shadow: 0 2px 10px rgba(232,201,107,0.35);
    }
    [data-baseweb="tab-highlight"] { display: none; }
    [data-baseweb="tab-border"] { display: none; }
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
pronosticos_raw = fetch_all("pronosticos", "participante_id, partido_id, pronostico")
dieciseisavos_raw = fetch_all("dieciseisavos", "*", order_cols=["partido_num"])
pronosticos_16_raw = fetch_all("pronosticos_dieciseisavos", "participante_id, cruce_id, pronostico")

if not partidos_raw:
    st.info("No hay partidos registrados todavía.")
    st.stop()

# ── Índices ─────────────────────────────────────────────────────────────────────
part_nombre = {str(p["id"]): p["nombre"] for p in participantes_raw}
total_participantes = len(participantes_raw)

# partido_id → {participante_id: pronostico}
pron_por_partido = {}
for pr in pronosticos_raw:
    pid = str(pr["partido_id"])
    uid = str(pr["participante_id"])
    pron_por_partido.setdefault(pid, {})[uid] = pr["pronostico"]

# cruce_id → {participante_id: pronostico}
pron_por_cruce = {}
for pr in pronosticos_16_raw:
    cid = str(pr["cruce_id"])
    uid = str(pr["participante_id"])
    pron_por_cruce.setdefault(cid, {})[uid] = pr["pronostico"]

# Agrupar partidos por grupo
partidos_por_grupo = {}
for p in partidos_raw:
    g = p["grupo"]
    partidos_por_grupo.setdefault(g, []).append(p)

grupos_lista = sorted(partidos_por_grupo.keys())


# ── Flags ───────────────────────────────────────────────────────────────────────────────
def flag_html(pais, size=52):
    url = get_flag(pais)
    if url:
        return f'<img src="{url}" class="flag-img" style="width:{size}px;height:{size}px;">'
    return '<span style="font-size:40px">🏳️</span>'

# ── Helper: parsear marcador "GL-GV" → signo 1/X/2 ─────────────────────────────
def signo_de_marcador(valor):
    if valor and "-" in str(valor):
        partes = str(valor).split("-")
        try:
            gl = int(partes[0])
            gv = int(partes[1])
        except ValueError:
            return None
        if gl > gv:   return "1"
        elif gl == gv: return "X"
        else:          return "2"
    return None

# ── Helper: chips HTML ───────────────────────────────────────────────────────────
def chips_html(nombres_dict, cls, marcadores=None):
    if not nombres_dict:
        return '<div class="sin-apuestas">—</div>'
    marcadores = marcadores or {}
    chips = []
    for uid, nom in sorted(nombres_dict.items(), key=lambda x: x[1]):
        marcador = marcadores.get(uid)
        if marcador:
            chips.append(
                f'<div class="chip-stack">'
                f'<span class="chip {cls}">{nom}</span>'
                f'<span class="chip-marcador">{marcador}</span>'
                f'</div>'
            )
        else:
            chips.append(f'<span class="chip {cls}">{nom}</span>')
    return '<div class="chips-row">' + "".join(chips) + "</div>"

# ── Helper: render card de partido ───────────────────────────────────────────────
def render_card_partido(local, visitante, fecha, hora, sede, resultado,
                        apuestas_dict, partido_num=None):
    votos_1 = {}; votos_X = {}; votos_2 = {}
    marcador_de = {}

    for uid, v in apuestas_dict.items():
        signo = signo_de_marcador(v)
        if signo is None:
            continue
        marcador_de[uid] = v
        nombre_part = part_nombre.get(uid, f"#{uid}")
        if signo == "1":   votos_1[uid] = nombre_part
        elif signo == "X": votos_X[uid] = nombre_part
        else:              votos_2[uid] = nombre_part

    sin_voto = {
        str(p2["id"]): p2["nombre"]
        for p2 in participantes_raw
        if signo_de_marcador(apuestas_dict.get(str(p2["id"]))) is None
    }

    n1 = len(votos_1); nX = len(votos_X); n2 = len(votos_2); n_sin = len(sin_voto)
    total_con_voto = n1 + nX + n2

    def pct(n):
        return f"{round(n / total_con_voto * 100)}%" if total_con_voto else "—"

    if resultado:
        labels_r = {"1": "Gana " + local, "X": "Empate", "2": "Gana " + visitante}
        res_html = (
            '<div class="resultado-real"><span class="resultado-pill">⚽ Resultado: '
            + labels_r.get(resultado, resultado) + "</span></div>"
        )
    else:
        res_html = (
            '<div class="resultado-real">'
            '<span class="resultado-pill pending">Partido no jugado</span></div>'
        )

    meta_parts = []
    if partido_num:
        meta_parts.append(f'<i class="ti ti-trophy"></i> Partido {partido_num}')
    if fecha:
        meta_parts.append(f'<i class="ti ti-calendar-event"></i> {fecha}')
    if hora:
        meta_parts.append(f'<i class="ti ti-clock"></i> {hora}')
    if sede:
        meta_parts.append(f'<i class="ti ti-map-pin"></i> {sede}')
    meta_str = "&nbsp;&nbsp;|&nbsp;&nbsp;".join(meta_parts)

    card_html = (
        '<div class="partido-card">'
        + (f'<div class="match-meta">{meta_str}</div>' if meta_str else "")
        + '<div class="teams-row">'
        + f'<div class="team-block">{flag_html(local)}<span class="team-name">{local}</span></div>'
        + '<div><span class="vs-text">VS</span></div>'
        + f'<div class="team-block">{flag_html(visitante)}<span class="team-name">{visitante}</span></div>'
        + "</div>"
        + res_html
        + '<hr style="border:none;border-top:1px solid rgba(255,255,255,0.07);margin:0 0 14px;">'
        + '<div class="conteo-titulo">¿Quién apostó a qué?</div>'
        + '<div class="barra-wrap">'
        + '<div class="barra-opcion op1">'
        + f'<div class="barra-label">1</div>'
        + f'<div class="barra-sublabel">Gana {local}</div>'
        + f'<div class="barra-count">{n1}</div>'
        + f'<div class="barra-pct">{pct(n1)}</div>'
        + chips_html(votos_1, "c1", marcador_de)
        + "</div>"
        + '<div class="barra-opcion opX">'
        + '<div class="barra-label">X</div>'
        + '<div class="barra-sublabel">Empate</div>'
        + f'<div class="barra-count">{nX}</div>'
        + f'<div class="barra-pct">{pct(nX)}</div>'
        + chips_html(votos_X, "cX", marcador_de)
        + "</div>"
        + '<div class="barra-opcion op2">'
        + f'<div class="barra-label">2</div>'
        + f'<div class="barra-sublabel">Gana {visitante}</div>'
        + f'<div class="barra-count">{n2}</div>'
        + f'<div class="barra-pct">{pct(n2)}</div>'
        + chips_html(votos_2, "c2", marcador_de)
        + "</div>"
        + "</div>"
    )
    if sin_voto:
        card_html += (
            '<div style="margin-top:6px;">'
            '<div class="barra-sublabel" style="text-align:center;margin-bottom:5px;">'
            f"Sin pronóstico ({n_sin})</div>"
            + chips_html(sin_voto, "cn")
            + "</div>"
        )
    card_html += "</div>"
    st.markdown(card_html, unsafe_allow_html=True)

# ── Helper: dots de navegación ───────────────────────────────────────────────────
def render_dots(idx, total):
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
        + dots_inner + "</div>"
        + f'<p style="text-align:center;font-size:0.72rem;color:#475569;letter-spacing:1px;margin-top:4px;">'
        f"Partido {idx + 1} de {total}</p>",
        unsafe_allow_html=True,
    )

# ════════════════════════════════════════════════════════════════════════════════
# TABS PRINCIPALES
# ════════════════════════════════════════════════════════════════════════════════
tab_grupos, tab_16 = st.tabs(["Fase de Grupos", "8vos de Final"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — FASE DE GRUPOS
# ══════════════════════════════════════════════════════════════════════════════
with tab_grupos:
    if "grupo_activo" not in st.session_state:
        st.session_state["grupo_activo"] = grupos_lista[0]

    cols = st.columns(len(grupos_lista))
    for i, g in enumerate(grupos_lista):
        with cols[i]:
            es_activo = g == st.session_state["grupo_activo"]
            if st.button(g, key=f"tab_{g}", use_container_width=True,
                         type="primary" if es_activo else "secondary"):
                st.session_state["grupo_activo"] = g
                st.session_state[f"pron_idx_{g}"] = 0
                st.rerun()

    grupo_sel  = st.session_state["grupo_activo"]
    lista_part = partidos_por_grupo[grupo_sel]
    total      = len(lista_part)

    st.markdown(
        '<p class="grupo-activo-label">GRUPO ' + grupo_sel + "</p>",
        unsafe_allow_html=True,
    )

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

    # ── Botones de selección directa de partido ──────────────────────────────
    btn_cols = st.columns(total)
    for i, part in enumerate(lista_part):
        with btn_cols[i]:
            es_actual = i == idx
            lbl = f"{part['local'][:3].upper()} vs {part['visitante'][:3].upper()}"
            if st.button(lbl, key=f"sel_partido_{grupo_sel}_{i}",
                         use_container_width=True,
                         type="primary" if es_actual else "secondary"):
                st.session_state[key_idx] = i
                st.rerun()

    # ── Botones prev / next (ARRIBA) ─────────────────────────────────────────
    _, col_prev_top, _, col_next_top, _ = st.columns([1, 1, 4, 1, 1])
    with col_prev_top:
        if st.button("◀", key="prev_btn_top", disabled=(idx == 0)):
            st.session_state[key_idx] = idx - 1
            st.rerun()
    with col_next_top:
        if st.button("▶", key="next_btn_top", disabled=(idx == total - 1)):
            st.session_state[key_idx] = idx + 1
            st.rerun()

    render_card_partido(
        local, visitante, fecha, hora, sede, resultado,
        pron_por_partido.get(str(p_id), {}),
    )

    render_dots(idx, total)

    _, col_prev, _, col_next, _ = st.columns([1, 1, 4, 1, 1])
    with col_prev:
        if st.button("◀", key="prev_btn", disabled=(idx == 0)):
            st.session_state[key_idx] = idx - 1
            st.rerun()
    with col_next:
        if st.button("▶", key="next_btn", disabled=(idx == total - 1)):
            st.session_state[key_idx] = idx + 1
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DIECISEISAVOS DE FINAL
# ══════════════════════════════════════════════════════════════════════════════
with tab_16:
    if not dieciseisavos_raw:
        st.info("Todavía no se cargaron los cruces de Dieciseisavos de Final.")
    else:
        total_16 = len(dieciseisavos_raw)

        key_idx_16 = "pron_idx_16"
        if key_idx_16 not in st.session_state:
            st.session_state[key_idx_16] = 0
        idx_16 = st.session_state[key_idx_16]
        if idx_16 >= total_16:
            idx_16 = 0
            st.session_state[key_idx_16] = 0

        c = dieciseisavos_raw[idx_16]
        cruce_id   = c["id"]
        local_16   = c.get("equipo_local") or c.get("origen_local") or c.get("grupo_local") or "Por definir"
        visit_16   = c.get("equipo_visitante") or c.get("origen_visitante") or c.get("grupo_visitante") or "Por definir"
        fecha_16   = c.get("fecha", "")
        hora_16    = c.get("hora", "")
        sede_16    = c.get("sede", "")
        partido_num_16 = c.get("partido_num", "")

        # Resultado oficial: derivar desde goles si no hay campo "resultado"
        resultado_16 = c.get("resultado") or ""
        if not resultado_16:
            gl_of = c.get("goles_local")
            gv_of = c.get("goles_visitante")
            if gl_of is not None and gv_of is not None:
                resultado_16 = signo_de_marcador(f"{gl_of}-{gv_of}") or ""

        st.markdown(
            '<p class="grupo-activo-label">8VOS DE FINAL</p>',
            unsafe_allow_html=True,
        )

        # Botones de selección directa de cruce
        btn_cols_16 = st.columns(total_16)
        for i, cruce_n in enumerate(dieciseisavos_raw):
            with btn_cols_16[i]:
                nom_l = cruce_n.get("equipo_local") or cruce_n.get("origen_local") or cruce_n.get("grupo_local") or "?"
                nom_v = cruce_n.get("equipo_visitante") or cruce_n.get("origen_visitante") or cruce_n.get("grupo_visitante") or "?"
                lbl_16 = f"{nom_l[:3].upper()} vs {nom_v[:3].upper()}"
                if st.button(lbl_16, key=f"sel_16_{i}",
                             use_container_width=True,
                             type="primary" if i == idx_16 else "secondary"):
                    st.session_state[key_idx_16] = i
                    st.rerun()

        # Prev / next arriba
        _, col_prev16_top, _, col_next16_top, _ = st.columns([1, 1, 4, 1, 1])
        with col_prev16_top:
            if st.button("◀", key="prev16_top", disabled=(idx_16 == 0)):
                st.session_state[key_idx_16] = idx_16 - 1
                st.rerun()
        with col_next16_top:
            if st.button("▶", key="next16_top", disabled=(idx_16 == total_16 - 1)):
                st.session_state[key_idx_16] = idx_16 + 1
                st.rerun()

        render_card_partido(
            local_16, visit_16, fecha_16, hora_16, sede_16, resultado_16,
            pron_por_cruce.get(str(cruce_id), {}),
            partido_num=partido_num_16,
        )

        render_dots(idx_16, total_16)

        _, col_prev16, _, col_next16, _ = st.columns([1, 1, 4, 1, 1])
        with col_prev16:
            if st.button("◀", key="prev16", disabled=(idx_16 == 0)):
                st.session_state[key_idx_16] = idx_16 - 1
                st.rerun()
        with col_next16:
            if st.button("▶", key="next16", disabled=(idx_16 == total_16 - 1)):
                st.session_state[key_idx_16] = idx_16 + 1
                st.rerun()
