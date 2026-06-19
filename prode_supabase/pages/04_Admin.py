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

    /* Tipografía oscura para fondo claro */
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
        pwd_input = st.text_input("Contraseña", type="password", key="sidebar_pwd_04", label_visibility="collapsed",
                                  placeholder="Contraseña de admin...")
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
# CARGA DE RESULTADOS OFICIALES
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
                st.success(f"Resultado guardado: {local} vs {visitante}")
                st.rerun()

        st.caption(
            f"📅 {fecha} | Resultado actual: {resultado_actual if resultado_actual else 'Sin cargar'}"
        )
else:
    st.warning("No hay partidos cargados.")

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

# Guardar snapshot del ranking actual en historial
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

# Mostrar historial reciente
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
# ══════════════════════════════════════════════════════════════════════════════
# SINCRONIZACIÓN AUTOMÁTICA DESDE football-data.org
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 🔄 Sincronización Automática de Resultados")
st.caption("Fuente: football-data.org · FIFA World Cup 2026 (WC)")

from sync_resultados import sincronizar, test_conexion_api
import time as _time

# ── Test de conexión ───────────────────────────────────────────────────────────
with st.expander("🛰️ Estado de conexión con la API", expanded=False):
    if st.button("Verificar conexión", key="btn_test_api"):
        with st.spinner("Conectando con football-data.org..."):
            check = test_conexion_api()
        if check["ok"]:
            st.success(check["mensaje"])
        else:
            st.error(check["mensaje"])

# ── Sincronización manual / automática ────────────────────────────────────────
col_auto1, col_auto2 = st.columns([2, 1])

with col_auto1:
    st.markdown(
        "Sincroniza todos los partidos **finalizados** desde la API y "
        "actualiza el resultado (1/X/2) en la base de datos. "
        "El resultado manual ingresado arriba **tiene prioridad**: "
        "la sincronización solo escribe si el campo está vacío o "
        "el resultado de la API difiere."
    )

with col_auto2:
    auto_sync = st.toggle(
        "Auto-sync cada 5 min",
        key="toggle_autosync",
        value=False,
        help="Recarga la página automáticamente cada 5 minutos y sincroniza."
    )

if st.button("▶️ Sincronizar Ahora", key="btn_sync_now", type="primary", use_container_width=True):
    with st.spinner("Consultando football-data.org..."):
        res = sincronizar(sb)

    if res["actualizados"] > 0:
        st.success(f"✅ {res['actualizados']} partido(s) actualizado(s).")
        for linea in res["detalle"]:
            st.write(linea)
    else:
        st.info("Sin cambios: todos los resultados ya están al día o no hay partidos finalizados.")

    if res["sin_partido"]:
        with st.expander(f"⚠️ {len(res['sin_partido'])} partido(s) de la API sin coincidencia en la BD"):
            st.caption(
                "Estos partidos vinieron de la API pero no se encontró el par "
                "local/visitante en tu tabla. Revisá el diccionario TEAM_MAP en "
                "sync_resultados.py para mapear los nombres correctamente."
            )
            for nombre in res["sin_partido"]:
                st.write(f"• {nombre}")

    if res["errores"]:
        with st.expander(f"❌ {len(res['errores'])} error(es)"):
            for err in res["errores"]:
                st.error(err)

# ── Auto-sync: recarga cada 5 minutos ─────────────────────────────────────────
if auto_sync:
    st.caption("⏱️ Auto-sync activo. La página se recargará cada 5 minutos.")

    # Sincronizar en el fondo al momento de la recarga
    if st.session_state.get("_autosync_ejecutado") != _time.strftime("%H:%M"):
        res_auto = sincronizar(sb)
        st.session_state["_autosync_ejecutado"] = _time.strftime("%H:%M")
        if res_auto["actualizados"] > 0:
            st.toast(f"Auto-sync: {res_auto['actualizados']} resultado(s) actualizado(s).")

    # Recarga automática con st.rerun después de 300 segundos
    _placeholder_timer = st.empty()
    import threading as _threading

    def _auto_rerun():
        _time.sleep(300)
        st.rerun()

    if not st.session_state.get("_timer_corriendo"):
        st.session_state["_timer_corriendo"] = True
        t = _threading.Thread(target=_auto_rerun, daemon=True)
        t.start()
else:
    st.session_state["_timer_corriendo"] = False
