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
    </style>
""", unsafe_allow_html=True)

st.title("⚙️ PANEL DE ADMINISTRACIÓN")

# ── Login admin ────────────────────────────────────────────────────────────────
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "prode2026")

if "admin_autenticado" not in st.session_state:
    st.session_state.admin_autenticado = False

if not st.session_state.admin_autenticado:
    st.markdown("<br>", unsafe_allow_html=True)
    col_c, col_form, col_d = st.columns([1, 2, 1])
    with col_form:
        st.markdown(
            '<div style="background:rgba(15,23,42,0.85);backdrop-filter:blur(16px);'
            'border:1px solid rgba(232,201,107,0.3);border-radius:18px;padding:32px 36px;text-align:center;">'
            '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:28px;color:#e8c96b;letter-spacing:3px;margin-bottom:6px;">🔐 ACCESO RESTRINGIDO</div>'
            '<div style="font-size:13px;color:#64748b;margin-bottom:24px;">Ingresá la contraseña de administrador para continuar.</div>'
            '</div>',
            unsafe_allow_html=True
        )
        pwd = st.text_input("Contraseña", type="password", key="admin_pwd_04", label_visibility="collapsed", placeholder="Contraseña de admin...")
        if st.button("Ingresar", use_container_width=True, type="primary", key="btn_login_04"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_autenticado = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
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
st.markdown("## 📋 Carga de Resultados Oficiales")

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
            st.subheader(f"🏆 Grupo {grupo}")

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
