import streamlit as st
from database import conectar

st.set_page_config(
    page_title="Administrador",
    layout="wide"
)

st.markdown("""
    <style>
    [data-testid="stApp"] {
        background-image: url('https://raw.githubusercontent.com/arcaltdfootball/PRODEFIFAWC2026UNQ/main/prode_supabase/admin.jpg');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }

    html, body, [class*="css"],
    .stMarkdown, .stMarkdown p, .stMarkdown li,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    .stText, label, .stSelectbox label,
    [data-testid="stWidgetLabel"] p,
    [data-testid="stMetricLabel"] p,
    [data-testid="stMetricValue"],
    [data-testid="stMetricDelta"],
    [data-testid="stCaptionContainer"] p,
    [data-testid="stDataFrame"],
    .stDataFrame, .stAlert p,
    [data-testid="stNotification"] p {
        color: #1e293b !important;
    }

    h1, h2, h3, h4, h5, h6 { color: #0f172a !important; }
    strong { color: #0f172a !important; }
    [data-testid="stCaptionContainer"] { color: #334155 !important; }
    [data-baseweb="select"] span { color: #1e293b !important; }
    </style>
""", unsafe_allow_html=True)

st.title("PANEL DE ADMINISTRACIÓN")

# ── Login admin (sidebar) ─────────────────────────────────────────────────────
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "prode2026")

if "admin_autenticado" not in st.session_state:
    st.session_state.admin_autenticado = False

with st.sidebar:
    st.markdown("---")
    if not st.session_state.admin_autenticado:
        st.markdown(
            '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:18px;'
            'color:#e8c96b;letter-spacing:2px;margin-bottom:8px;">🔐 ACCESO ADMIN</div>',
            unsafe_allow_html=True
        )
        pwd_input = st.text_input("Contraseña", type="password", key="sidebar_pwd_04",
                                  label_visibility="collapsed", placeholder="Contraseña de admin...")
        if st.button("Ingresar", use_container_width=True, key="btn_login_04"):
            if pwd_input == ADMIN_PASSWORD:
                st.session_state.admin_autenticado = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
        st.caption("Solo el administrador puede acceder.")
    else:
        st.markdown(
            '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:16px;'
            'color:#4ade80;letter-spacing:2px;">✅ ADMIN ACTIVO</div>',
            unsafe_allow_html=True
        )
        if st.button("🚪 Cerrar sesión", use_container_width=True, key="btn_logout_04"):
            st.session_state.admin_autenticado = False
            st.rerun()

if not st.session_state.admin_autenticado:
    st.stop()

# ── Conexión Supabase ──────────────────────────────────────────────────────────
try:
    sb = conectar()
except Exception as e:
    st.error(f"Error al conectar: {e}")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# CARGA DE RESULTADOS OFICIALES — FASE DE GRUPOS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## Carga de Resultados Oficiales")

resp = sb.table("partidos").select("id, grupo, fecha, local, visitante, resultado").order("grupo").order("fecha").execute()
partidos = resp.data

if partidos:
    grupo_actual = None

    for partido in partidos:
        partido_id       = partido["id"]
        grupo            = partido["grupo"]
        fecha            = partido["fecha"]
        local            = partido["local"]
        visitante        = partido["visitante"]
        resultado_actual = partido.get("resultado") or ""

        if grupo != grupo_actual:
            grupo_actual = grupo
            st.markdown("---")
            st.subheader(f"Grupo {grupo}")

        col1, col2, col3, col4 = st.columns([3, 3, 2, 2])

        with col1:
            st.write(f"**{local}**")
        with col2:
            st.write(f"**{visitante}**")
        with col3:
            opciones = ["", "1", "X", "2"]
            indice = opciones.index(resultado_actual) if resultado_actual in opciones else 0
            resultado = st.selectbox(
                "Resultado",
                options=opciones,
                index=indice,
                key=f"resultado_{partido_id}"
            )
        with col4:
            if st.button("💾 Guardar", key=f"guardar_{partido_id}"):
                sb.table("partidos").update({"resultado": resultado}).eq("id", partido_id).execute()
                # Invalidar caché para que 01_Resultados refleje el cambio de inmediato
                st.cache_data.clear()
                st.success(f"✅ Resultado guardado: {local} vs {visitante} → {resultado}")
                st.rerun()

        st.caption(
            f"📅 {fecha} | Resultado actual: {resultado_actual if resultado_actual else 'Sin cargar'}"
        )
else:
    st.warning("No hay partidos cargados.")

# ══════════════════════════════════════════════════════════════════════════════
# CARGA DE RESULTADOS — DIECISEISAVOS DE FINAL
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 🏆 Carga de Resultados — Dieciseisavos de Final")

resp_16 = sb.table("dieciseisavos").select("*").order("partido_num").execute()
cruces_16 = resp_16.data

if cruces_16:
    for c in cruces_16:
        cruce_id     = c["id"]
        partido_num  = c.get("partido_num")
        nombre_local = c.get("equipo_local") or c.get("origen_local") or c.get("grupo_local") or "Por definir"
        nombre_visit = c.get("equipo_visitante") or c.get("origen_visitante") or c.get("grupo_visitante") or "Por definir"
        resultado_actual_16 = c.get("resultado") or ""
        marcador_actual_16  = c.get("marcador") or ""

        gl_actual, gv_actual = None, None
        if marcador_actual_16 and "-" in str(marcador_actual_16):
            partes_m = str(marcador_actual_16).split("-")
            try:
                gl_actual = int(partes_m[0])
                gv_actual = int(partes_m[1])
            except ValueError:
                pass

        st.markdown(f"**Cruce {partido_num}** — {nombre_local} vs {nombre_visit}")

        col1, col2, col_gl, col_sep, col_gv, col3, col4 = st.columns([2.2, 2.2, 1, 0.3, 1, 1.8, 1.5])

        with col1:
            st.write(nombre_local)
        with col2:
            st.write(nombre_visit)
        with col_gl:
            gl_input_16 = st.number_input(
                nombre_local[:10], min_value=0, max_value=20,
                value=gl_actual if gl_actual is not None else 0,
                key=f"gl16_{cruce_id}", label_visibility="collapsed"
            )
        with col_sep:
            st.markdown(
                '<div style="text-align:center;padding-top:8px;font-weight:700;">-</div>',
                unsafe_allow_html=True
            )
        with col_gv:
            gv_input_16 = st.number_input(
                nombre_visit[:10], min_value=0, max_value=20,
                value=gv_actual if gv_actual is not None else 0,
                key=f"gv16_{cruce_id}", label_visibility="collapsed"
            )
        with col3:
            opciones_16 = ["", "1", "X", "2"]
            if gl_input_16 > gv_input_16:
                sugerido_16 = "1"
            elif gv_input_16 > gl_input_16:
                sugerido_16 = "2"
            else:
                sugerido_16 = "X"
            indice_16 = opciones_16.index(sugerido_16) if sugerido_16 in opciones_16 else 0
            resultado_16 = st.selectbox(
                "Ganador", options=opciones_16, index=indice_16,
                key=f"resultado16_{cruce_id}", label_visibility="collapsed"
            )
        with col4:
            if st.button("💾 Guardar", key=f"guardar16_{cruce_id}"):
                marcador_nuevo_16 = f"{gl_input_16}-{gv_input_16}"
                if gl_input_16 > gv_input_16:
                    res_auto_16 = "1"
                elif gv_input_16 > gl_input_16:
                    res_auto_16 = "2"
                else:
                    res_auto_16 = "X"
                res_final_16 = resultado_16 if resultado_16 else res_auto_16

                try:
                    resp_update_16 = (
                        sb.table("dieciseisavos")
                        .update({
                            "resultado": res_final_16,
                            "marcador":  marcador_nuevo_16,
                        })
                        .eq("id", cruce_id)
                        .execute()
                    )
                except Exception as ex:
                    st.error(f"❌ Error al guardar en Supabase: {ex}")
                else:
                    if resp_update_16.data:
                        # Invalidar caché para que 01_Resultados refleje el cambio de inmediato
                        st.cache_data.clear()
                        st.success(f"✅ Guardado: {nombre_local} {marcador_nuevo_16} {nombre_visit}")
                        st.rerun()
                    else:
                        st.error(
                            "⚠️ Supabase no actualizó ninguna fila. Esto suele pasar por "
                            "permisos (RLS) en la tabla 'dieciseisavos' que bloquean el UPDATE, "
                            "o porque falta alguna columna ('resultado' / 'marcador'). "
                            "Revisá el archivo SQL adjunto."
                        )

        st.caption(
            f"📅 {c.get('fecha') or '—'} | Marcador actual: {marcador_actual_16 if marcador_actual_16 else 'Sin cargar'} "
            f"| Resultado: {resultado_actual_16 if resultado_actual_16 else 'Sin cargar'}"
        )
        st.markdown("&nbsp;", unsafe_allow_html=True)
else:
    st.warning("No hay cruces de Dieciseisavos de Final cargados todavía.")

# ══════════════════════════════════════════════════════════════════════════════
# RESUMEN DE RESULTADOS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 📊 Estado de Resultados")

resp_total = sb.table("partidos").select("id, resultado").execute()
todos      = resp_total.data
total_partidos = len(todos)
cargados   = sum(1 for p in todos if p.get("resultado"))
pendientes = total_partidos - cargados
porcentaje = round((cargados / total_partidos) * 100, 1) if total_partidos > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Partidos",            total_partidos)
col2.metric("Resultados cargados", cargados)
col3.metric("Pendientes",          pendientes)
col4.metric("% Completo",          f"{porcentaje}%")

# ══════════════════════════════════════════════════════════════════════════════
# HISTORIAL DE RANKING
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 📈 Últimas Actualizaciones del Ranking")

st.info("Podés guardar un snapshot del ranking actual en el historial.")
if st.button("📸 Guardar Snapshot del Ranking", type="primary", use_container_width=True):
    from ranking import obtener_ranking
    from datetime import datetime

    ranking = obtener_ranking()
    resp_parts = sb.table("participantes").select("id, nombre").execute()
    nombre_a_id = {p["nombre"]: p["id"] for p in resp_parts.data}
    fecha_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filas = []
    for pos, (nombre, puntos, *_) in enumerate(ranking, 1):
        pid = nombre_a_id.get(nombre)
        if pid:
            filas.append({
                "participante_id": pid,
                "fecha_control":   fecha_now,
                "posicion":        pos,
                "puntos":          puntos,
            })
    if filas:
        sb.table("historial_ranking").insert(filas).execute()
        st.success(f"✅ Snapshot guardado ({len(filas)} entradas).")
    else:
        st.warning("No hay participantes en el ranking.")

resp_hist = (
    sb.table("historial_ranking")
    .select("fecha_control, posicion, puntos, participantes(nombre)")
    .order("fecha_control", desc=True)
    .limit(30)
    .execute()
)

if resp_hist.data:
    datos_hist = []
    for fila in resp_hist.data:
        nombre = fila.get("participantes", {}).get("nombre", "—") if fila.get("participantes") else "—"
        datos_hist.append({
            "Fecha":        fila["fecha_control"],
            "Participante": nombre,
            "Posición":     fila["posicion"],
            "Puntos":       fila["puntos"],
        })
    st.dataframe(datos_hist, use_container_width=True, hide_index=True)
else:
    st.warning("Todavía no hay historial de ranking.")
