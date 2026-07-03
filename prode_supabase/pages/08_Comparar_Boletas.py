from flags import FLAGS, get_flag
import streamlit as st
from database import conectar

st.set_page_config(
    page_title="Comparar Boletas",
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
        background-image: url('https://raw.githubusercontent.com/arcaltdfootball/PRODEFIFAWC2026UNQ/main/prode_supabase/FIFA222.jpg');
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

    .grupo-activo-label {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1rem; color: #e8c96b;
        text-align: center; letter-spacing: 3px;
        margin-bottom: 10px; text-transform: uppercase;
    }

    /* CARD COMPARACION */
    .partido-card {
        background: rgba(20,30,50,0.72);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 22px;
        padding: 22px 20px 18px;
        max-width: 580px;
        margin: 0 auto 14px;
        box-shadow: 0 16px 40px rgba(0,0,0,0.35);
    }

    .match-meta {
        font-size: 0.72rem; color: #64748b;
        text-align: center; text-transform: uppercase;
        letter-spacing: 1px; margin-bottom: 14px;
    }
    .match-meta i { color: #e8c96b; margin-right: 3px; }

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
        width: 44px; height: 44px; object-fit: cover;
        border-radius: 50%;
        box-shadow: 0 4px 14px rgba(0,0,0,0.4);
        border: 2px solid rgba(255,255,255,0.12);
    }
    .team-name { font-size: 0.82rem; font-weight: 600; color: #e2e8f0; text-align: center; }
    .vs-text {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.6rem; color: #e8c96b;
        letter-spacing: 2px; line-height: 1;
    }

    .resultado-real { text-align: center; margin-bottom: 14px; }
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

    /* COMPARACION DE PRONOSTICOS */
    .comp-wrap {
        display: flex; gap: 10px; align-items: stretch;
        margin-bottom: 4px;
    }
    .comp-col {
        flex: 1; border-radius: 14px; padding: 12px 10px 10px;
        text-align: center; position: relative;
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.03);
    }
    .comp-col-nombre {
        font-size: 0.68rem; color: #94a3b8;
        text-transform: uppercase; letter-spacing: 1px;
        margin-bottom: 8px; font-weight: 600;
    }
    .comp-pill {
        display: inline-block;
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.5rem; line-height: 1;
        border-radius: 12px; padding: 6px 18px;
        margin-bottom: 4px;
    }
    .comp-pill.op1 { background: rgba(34,197,94,0.18);  color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .comp-pill.opX { background: rgba(232,201,107,0.16); color: #e8c96b; border: 1px solid rgba(232,201,107,0.3); }
    .comp-pill.op2 { background: rgba(239,68,68,0.18);  color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
    .comp-pill.opn { background: rgba(100,116,139,0.12); color: #475569; border: 1px dashed rgba(100,116,139,0.3); font-size: 1rem; }
    .comp-sub { font-size: 0.66rem; color: #64748b; margin-top: 2px; }

    .comp-card.coinciden { border-color: rgba(34,197,94,0.35); box-shadow: 0 16px 40px rgba(34,197,94,0.08); }
    .comp-card.difieren  { border-color: rgba(239,68,68,0.25); }

    .badge-match {
        text-align: center; margin-bottom: 4px;
    }
    .badge-match span {
        font-size: 0.68rem; font-weight: 700; letter-spacing: 1px;
        text-transform: uppercase; border-radius: 20px; padding: 3px 12px;
        display: inline-block;
    }
    .badge-match .si  { background: rgba(34,197,94,0.18); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .badge-match .no  { background: rgba(239,68,68,0.16); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }

    /* HEADER COMPARACION GENERAL */
    .vs-header {
        display: flex; align-items: center; justify-content: center;
        gap: 18px; margin-bottom: 18px;
    }
    .vs-header-name {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.5rem; color: #fff; text-align: center;
        letter-spacing: 1px;
    }
    .vs-header-vs {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.2rem; color: #e8c96b;
    }

    /* RESUMEN */
    .resumen-wrap {
        display: flex; gap: 10px; margin: 4px auto 20px; max-width: 580px;
    }
    .resumen-box {
        flex: 1; text-align: center; border-radius: 16px;
        padding: 14px 8px; border: 1px solid rgba(255,255,255,0.08);
        background: rgba(20,30,50,0.6);
    }
    .resumen-box .num {
        font-family: 'Bebas Neue', sans-serif; font-size: 2rem; line-height: 1;
    }
    .resumen-box .lbl {
        font-size: 0.66rem; color: #94a3b8; text-transform: uppercase;
        letter-spacing: 1px; margin-top: 4px;
    }
    .resumen-box.verde .num { color: #4ade80; }
    .resumen-box.rojo  .num { color: #f87171; }
    .resumen-box.gris  .num { color: #94a3b8; }

    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-label">Fixture Oficial · FIFA World Cup 2026</p>', unsafe_allow_html=True)
st.markdown('<h1 class="main-title">COMPARAR BOLETAS</h1>', unsafe_allow_html=True)

# ── Conexión ────────────────────────────────────────────────────────────────────
try:
    sb = conectar()
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.stop()

# ── Datos (mismo patrón de paginado que 06_Pronosticos.py) ───────────────────────
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
pronosticos_raw = fetch_all("pronosticos", "participante_id, partido_id, pronostico, goles_local, goles_visitante")
dieciseisavos_raw = fetch_all("dieciseisavos", "*", order_cols=["partido_num"])
pronosticos_16_raw = fetch_all("pronosticos_dieciseisavos", "participante_id, cruce_id, pronostico")

if not partidos_raw:
    st.info("No hay partidos registrados todavía.")
    st.stop()

if not participantes_raw or len(participantes_raw) < 2:
    st.info("Hacen falta al menos dos participantes para poder comparar boletas.")
    st.stop()

# ── Índices ─────────────────────────────────────────────────────────────────────
part_nombre = {str(p["id"]): p["nombre"] for p in participantes_raw}

# partido_id → {participante_id: pronostico}
pron_por_partido = {}
for pr in pronosticos_raw:
    pid = str(pr["partido_id"])
    uid = str(pr["participante_id"])
    pron_por_partido.setdefault(pid, {})[uid] = {
        "resultado":       pr["pronostico"],
        "goles_local":     pr.get("goles_local"),
        "goles_visitante": pr.get("goles_visitante"),
    }

# cruce_id → {participante_id: {resultado, goles_local, goles_visitante}}
# pronostico viene como "GL-GV" → lo parseamos igual que scoring.py
def _parsear_marcador(marcador):
    if not marcador or "-" not in str(marcador):
        return None, None, None
    try:
        partes = str(marcador).split("-")
        gl = int(partes[0])
        gv = int(partes[1])
        res = "1" if gl > gv else ("X" if gl == gv else "2")
        return res, gl, gv
    except (ValueError, IndexError):
        return None, None, None

pron_por_cruce = {}
for pr in pronosticos_16_raw:
    cid = str(pr["cruce_id"])
    uid = str(pr["participante_id"])
    res, gl, gv = _parsear_marcador(pr.get("pronostico"))
    pron_por_cruce.setdefault(cid, {})[uid] = {
        "resultado":       res,
        "goles_local":     gl,
        "goles_visitante": gv,
        "pronostico_raw":  pr.get("pronostico"),
    }

# Agrupar partidos por grupo
partidos_por_grupo = {}
for p in partidos_raw:
    g = p["grupo"]
    partidos_por_grupo.setdefault(g, []).append(p)

grupos_lista = sorted(partidos_por_grupo.keys())

# ── Flags ───────────────────────────────────────────────────────────────────────
def flag_html(pais, size=44):
    url = get_flag(pais)
    if url:
        return f'<img src="{url}" class="flag-img" style="width:{size}px;height:{size}px;">'
    return '<span style="font-size:34px">🏳️</span>'

# ── Selección de participantes ────────────────────────────────────────────────
nombres_ordenados = sorted(part_nombre.values())
nombre_a_id = {}
for pid, nom in part_nombre.items():
    nombre_a_id[nom] = pid

st.markdown(
    '<p class="grupo-activo-label">Elegí dos participantes</p>',
    unsafe_allow_html=True,
)

col_a, col_vs, col_b = st.columns([5, 1, 5])
with col_a:
    nombre_1 = st.selectbox(
        "Participante 1",
        nombres_ordenados,
        index=0,
        key="cmp_part_1",
    )
with col_vs:
    st.markdown(
        '<div style="text-align:center;padding-top:32px;'
        'font-family:\'Bebas Neue\',sans-serif;font-size:1.4rem;color:#e8c96b;">VS</div>',
        unsafe_allow_html=True,
    )
with col_b:
    default_idx_2 = 1 if len(nombres_ordenados) > 1 else 0
    nombre_2 = st.selectbox(
        "Participante 2",
        nombres_ordenados,
        index=default_idx_2,
        key="cmp_part_2",
    )

comparar = st.button("⚔️ Comparar boletas", use_container_width=True, type="primary")

if "cmp_activo" not in st.session_state:
    st.session_state["cmp_activo"] = False

if comparar:
    if nombre_1 == nombre_2:
        st.warning("Elegí dos participantes distintos para comparar sus boletas.")
        st.session_state["cmp_activo"] = False
    else:
        st.session_state["cmp_activo"] = True
        st.session_state["cmp_nombre_1"] = nombre_1
        st.session_state["cmp_nombre_2"] = nombre_2

# ── Helper: render resumen ────────────────────────────────────────────────────
def render_resumen(exacto, resultado, difieren, sin_comparar):
    st.markdown(
        '<div class="resumen-wrap">'
        '<div class="resumen-box" style="flex:1;text-align:center;border-radius:16px;padding:14px 8px;'
        'border:1px solid rgba(232,201,107,0.4);background:rgba(232,201,107,0.1);">'
        f'<div class="num" style="font-family:\'Bebas Neue\',sans-serif;font-size:2rem;line-height:1;color:#e8c96b;">{exacto}</div>'
        '<div class="lbl" style="font-size:0.66rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Marcador exacto</div>'
        '</div>'
        '<div class="resumen-box verde" style="flex:1;text-align:center;border-radius:16px;padding:14px 8px;'
        'border:1px solid rgba(34,197,94,0.3);background:rgba(34,197,94,0.08);">'
        f'<div class="num" style="font-family:\'Bebas Neue\',sans-serif;font-size:2rem;line-height:1;color:#4ade80;">{resultado}</div>'
        '<div class="lbl" style="font-size:0.66rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Mismo resultado</div>'
        '</div>'
        '<div class="resumen-box rojo" style="flex:1;text-align:center;border-radius:16px;padding:14px 8px;'
        'border:1px solid rgba(239,68,68,0.25);background:rgba(239,68,68,0.08);">'
        f'<div class="num" style="font-family:\'Bebas Neue\',sans-serif;font-size:2rem;line-height:1;color:#f87171;">{difieren}</div>'
        '<div class="lbl" style="font-size:0.66rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Difieren</div>'
        '</div>'
        '<div class="resumen-box gris" style="flex:1;text-align:center;border-radius:16px;padding:14px 8px;'
        'border:1px solid rgba(255,255,255,0.08);background:rgba(20,30,50,0.6);">'
        f'<div class="num" style="font-family:\'Bebas Neue\',sans-serif;font-size:2rem;line-height:1;color:#94a3b8;">{sin_comparar}</div>'
        '<div class="lbl" style="font-size:0.66rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Sin comparar</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ── Helper: build_card_partido ────────────────────────────────────────────────
def build_card_partido(local, visitante, fecha, hora, sede, resultado,
                       gl_of, gv_of, v1, gl1, gv1, v2, gl2, gv2,
                       n1_sel, n2_sel):
    if v1 is not None and v2 is not None and v1 == v2:
        marcador_igual = (
            gl1 is not None and gv1 is not None
            and gl2 is not None and gv2 is not None
            and int(gl1) == int(gl2) and int(gv1) == int(gv2)
        )
        if marcador_igual:
            estado_clase = "coinciden"
            badge_match = (
                '<span style="background:rgba(232,201,107,0.2);color:#e8c96b;'
                'border:1px solid rgba(232,201,107,0.45);border-radius:20px;'
                'padding:3px 12px;font-size:0.68rem;font-weight:700;'
                'letter-spacing:1px;text-transform:uppercase;">'
                '⭐ Marcador exacto igual</span>'
            )
        else:
            estado_clase = "coinciden"
            badge_match = '<span class="si">✓ Mismo resultado</span>'
    elif v1 is not None and v2 is not None:
        estado_clase = "difieren"
        badge_match = '<span class="no">✗ Difieren</span>'
    else:
        estado_clase = ""
        badge_match = ""

    meta_parts = []
    if fecha:
        meta_parts.append(f'<i class="ti ti-calendar-event"></i> {fecha}')
    if hora:
        meta_parts.append(f'<i class="ti ti-clock"></i> {hora}')
    if sede:
        meta_parts.append(f'<i class="ti ti-map-pin"></i> {sede}')
    meta_str = "&nbsp;&nbsp;|&nbsp;&nbsp;".join(meta_parts)

    if resultado:
        labels_r = {"1": "Gana " + local, "X": "Empate", "2": "Gana " + visitante}
        if gl_of is not None and gv_of is not None:
            marcador_of = (
                f'<span style="font-family:\'Bebas Neue\',sans-serif;font-size:1.3rem;'
                f'color:#e8c96b;margin:0 6px;">{int(gl_of)} - {int(gv_of)}</span> '
            )
        else:
            marcador_of = ""
        res_html = (
            '<div class="resultado-real"><span class="resultado-pill">⚽ '
            + marcador_of + labels_r.get(resultado, resultado) + "</span></div>"
        )
    else:
        res_html = (
            '<div class="resultado-real">'
            '<span class="resultado-pill pending">Partido no jugado</span></div>'
        )

    def pill_html(valor, gl, gv):
        if gl is not None and gv is not None:
            marcador_str = (
                f'<div style="font-family:\'Bebas Neue\',sans-serif;font-size:1.8rem;'
                f'color:#e8c96b;line-height:1;margin-bottom:2px;">{int(gl)} - {int(gv)}</div>'
            )
        else:
            marcador_str = ""
        if valor == "1":
            return marcador_str + f'<div class="comp-pill op1">1</div><div class="comp-sub">Gana {local}</div>'
        if valor == "X":
            return marcador_str + '<div class="comp-pill opX">X</div><div class="comp-sub">Empate</div>'
        if valor == "2":
            return marcador_str + f'<div class="comp-pill op2">2</div><div class="comp-sub">Gana {visitante}</div>'
        return '<div class="comp-pill opn">—</div><div class="comp-sub">Sin pronóstico</div>'

    return (
        f'<div class="partido-card comp-card {estado_clase}">'
        + (f'<div class="match-meta">{meta_str}</div>' if meta_str else "")
        + '<div class="teams-row">'
        + f'<div class="team-block">{flag_html(local)}<span class="team-name">{local}</span></div>'
        + '<div><span class="vs-text">VS</span></div>'
        + f'<div class="team-block">{flag_html(visitante)}<span class="team-name">{visitante}</span></div>'
        + "</div>"
        + res_html
        + '<hr style="border:none;border-top:1px solid rgba(255,255,255,0.07);margin:0 0 12px;">'
        + (f'<div class="badge-match">{badge_match}</div>' if badge_match else "")
        + '<div class="comp-wrap">'
        + f'<div class="comp-col"><div class="comp-col-nombre">{n1_sel}</div>{pill_html(v1, gl1, gv1)}</div>'
        + f'<div class="comp-col"><div class="comp-col-nombre">{n2_sel}</div>{pill_html(v2, gl2, gv2)}</div>'
        + "</div></div>"
    )


# ── Resultado de la comparación ───────────────────────────────────────────────
if st.session_state.get("cmp_activo"):
    n1_sel = st.session_state["cmp_nombre_1"]
    n2_sel = st.session_state["cmp_nombre_2"]
    id1 = nombre_a_id.get(n1_sel)
    id2 = nombre_a_id.get(n2_sel)

    st.markdown(
        '<div class="vs-header">'
        f'<div class="vs-header-name">{n1_sel}</div>'
        '<div class="vs-header-vs">VS</div>'
        f'<div class="vs-header-name">{n2_sel}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    tab_grupos, tab_16 = st.tabs(["🏟️  Fase de Grupos", "⚔️  Dieciseisavos de Final"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — FASE DE GRUPOS
    # ══════════════════════════════════════════════════════════════════════════
    with tab_grupos:
        # Resumen
        coinciden_exacto_n = coinciden_resultado_n = difieren_n = sin_comparar_n = 0
        for p in partidos_raw:
            pid_str = str(p["id"])
            apuestas = pron_por_partido.get(pid_str, {})
            d1 = apuestas.get(id1)
            d2 = apuestas.get(id2)
            r1 = d1["resultado"] if d1 else None
            r2 = d2["resultado"] if d2 else None
            if r1 is None or r2 is None:
                sin_comparar_n += 1
            elif r1 != r2:
                difieren_n += 1
            else:
                gl1_ = d1.get("goles_local");  gv1_ = d1.get("goles_visitante")
                gl2_ = d2.get("goles_local");  gv2_ = d2.get("goles_visitante")
                if (gl1_ is not None and gv1_ is not None
                        and gl2_ is not None and gv2_ is not None
                        and int(gl1_) == int(gl2_) and int(gv1_) == int(gv2_)):
                    coinciden_exacto_n += 1
                else:
                    coinciden_resultado_n += 1

        render_resumen(coinciden_exacto_n, coinciden_resultado_n, difieren_n, sin_comparar_n)

        # Filtro por grupo
        if "cmp_grupo_activo" not in st.session_state or st.session_state["cmp_grupo_activo"] not in grupos_lista:
            st.session_state["cmp_grupo_activo"] = grupos_lista[0]

        cols_g = st.columns(len(grupos_lista))
        for i, g in enumerate(grupos_lista):
            with cols_g[i]:
                es_activo = g == st.session_state["cmp_grupo_activo"]
                if st.button(g, key=f"cmp_tab_{g}", use_container_width=True,
                             type="primary" if es_activo else "secondary"):
                    st.session_state["cmp_grupo_activo"] = g
                    st.rerun()

        grupo_sel = st.session_state["cmp_grupo_activo"]
        lista_part_grupo = partidos_por_grupo[grupo_sel]

        st.markdown(
            '<p class="grupo-activo-label">GRUPO ' + grupo_sel + "</p>",
            unsafe_allow_html=True,
        )

        for p in lista_part_grupo:
            p_id    = p["id"]
            local      = p["local"]
            visitante  = p["visitante"]
            apuestas   = pron_por_partido.get(str(p_id), {})
            pron1 = apuestas.get(id1)
            pron2 = apuestas.get(id2)
            card = build_card_partido(
                local, visitante,
                p.get("fecha", ""), p.get("hora", ""), p.get("sede", ""),
                p.get("resultado") or "",
                p.get("goles_local"), p.get("goles_visitante"),
                pron1["resultado"]       if pron1 else None,
                pron1["goles_local"]     if pron1 else None,
                pron1["goles_visitante"] if pron1 else None,
                pron2["resultado"]       if pron2 else None,
                pron2["goles_local"]     if pron2 else None,
                pron2["goles_visitante"] if pron2 else None,
                n1_sel, n2_sel,
            )
            st.markdown(card, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — DIECISEISAVOS DE FINAL
    # ══════════════════════════════════════════════════════════════════════════
    with tab_16:
        if not dieciseisavos_raw:
            st.info("Todavía no se cargaron los cruces de Dieciseisavos de Final.")
        else:
            # Resumen 8vos
            ex16 = res16 = dif16 = sin16 = 0
            for c in dieciseisavos_raw:
                cid_str = str(c["id"])
                apuestas16 = pron_por_cruce.get(cid_str, {})
                d1 = apuestas16.get(id1)
                d2 = apuestas16.get(id2)
                r1 = d1["resultado"] if d1 else None
                r2 = d2["resultado"] if d2 else None
                if r1 is None or r2 is None:
                    sin16 += 1
                elif r1 != r2:
                    dif16 += 1
                else:
                    gl1_ = d1.get("goles_local");  gv1_ = d1.get("goles_visitante")
                    gl2_ = d2.get("goles_local");  gv2_ = d2.get("goles_visitante")
                    if (gl1_ is not None and gv1_ is not None
                            and gl2_ is not None and gv2_ is not None
                            and int(gl1_) == int(gl2_) and int(gv1_) == int(gv2_)):
                        ex16 += 1
                    else:
                        res16 += 1

            render_resumen(ex16, res16, dif16, sin16)

            st.markdown(
                '<p class="grupo-activo-label">DIECISEISAVOS DE FINAL</p>',
                unsafe_allow_html=True,
            )

            for c in dieciseisavos_raw:
                cid_str = str(c["id"])

                # Nombres de equipos (pueden ser placeholder si no están definidos aún)
                local     = c.get("equipo_local") or c.get("origen_local") or c.get("grupo_local") or "Por definir"
                visitante = c.get("equipo_visitante") or c.get("origen_visitante") or c.get("grupo_visitante") or "Por definir"

                # Resultado oficial del cruce
                resultado_of = c.get("resultado") or ""
                gl_of = c.get("goles_local")
                gv_of = c.get("goles_visitante")
                # Derivar resultado desde goles si no está explícito
                if not resultado_of and gl_of is not None and gv_of is not None:
                    res_der, _, _ = _parsear_marcador(f"{gl_of}-{gv_of}")
                    resultado_of = res_der or ""

                apuestas16 = pron_por_cruce.get(cid_str, {})
                pron1 = apuestas16.get(id1)
                pron2 = apuestas16.get(id2)

                # Meta info
                partido_num = c.get("partido_num", "")
                meta_extra = f'<i class="ti ti-trophy"></i> Partido {partido_num} &nbsp;|&nbsp; ' if partido_num else ""

                card = build_card_partido(
                    local, visitante,
                    c.get("fecha", ""), c.get("hora", ""), c.get("sede", ""),
                    resultado_of,
                    gl_of, gv_of,
                    pron1["resultado"]       if pron1 else None,
                    pron1["goles_local"]     if pron1 else None,
                    pron1["goles_visitante"] if pron1 else None,
                    pron2["resultado"]       if pron2 else None,
                    pron2["goles_local"]     if pron2 else None,
                    pron2["goles_visitante"] if pron2 else None,
                    n1_sel, n2_sel,
                )
                # Inyectar número de partido en el meta si existe
                if partido_num:
                    card = card.replace(
                        '<div class="match-meta">',
                        f'<div class="match-meta">{meta_extra}',
                        1,
                    )
                st.markdown(card, unsafe_allow_html=True)

else:
    st.info("Elegí dos participantes y tocá **Comparar boletas** para ver la comparación partido por partido.")
