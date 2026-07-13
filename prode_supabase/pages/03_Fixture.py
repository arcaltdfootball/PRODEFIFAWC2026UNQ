"""
03_Fixture.py

Fixture digital del Clausura 2026 para completar el prode partido a partido
(Zona A, Zona B e Interzonal), sobre el esquema de schema_prode.sql
(jugadores / partidos / pronosticos).

Incluye:
  - Login/registro de jugadores (cada uno carga y ve SOLO su propia boleta).
  - Acceso Admin (usuario "admin", contraseña configurable via
    st.secrets["ADMIN_PASSWORD"], default "aleotero") con control total:
    cargar resultados reales de los partidos, administrar jugadores
    (resetear contraseña / eliminar / crear) y ver o editar la boleta
    de cualquier jugador.

Requiere haber corrido migracion_login_jugadores.sql (agrega username y
password_hash a la tabla "jugadores").
"""
import hashlib
import secrets
import string

import streamlit as st
from database import conectar
from escudos_map import url_escudo

st.set_page_config(page_title="Fixture - Mi Boleta", page_icon="📝", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap');

    h1, h2, h3 { font-family: 'Bebas Neue', sans-serif !important; letter-spacing: 1px; }

    .titulo-pagina {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 40px; color: #e8c96b; text-align: center;
        letter-spacing: 3px; margin-bottom: 4px;
    }
    .subtitulo-pagina {
        text-align: center; color: #94a3b8; font-size: 0.9rem;
        margin-bottom: 24px; font-family: 'Inter', sans-serif;
    }
    .fila-equipo {
        display: flex; align-items: center; gap: 8px;
        flex: 1; font-size: 0.9rem; font-family: 'Inter', sans-serif;
    }
    .fila-equipo.derecha { justify-content: flex-end; text-align: right; }
    .fila-escudo { width: 40px; height: 40px; object-fit: contain; }
    .fila-meta {
        font-size: 0.7rem; color: #64748b; text-align: center;
        margin-bottom: 2px; font-family: 'Inter', sans-serif;
    }
    .badge-jugado {
        background: rgba(74,222,128,0.15); color: #4ade80;
        border-radius: 10px; padding: 2px 10px; font-size: 0.72rem;
        white-space: nowrap;
    }
    .badge-puntos {
        background: rgba(232,201,107,0.18); color: #e8c96b;
        border-radius: 10px; padding: 2px 10px; font-size: 0.72rem;
        white-space: nowrap; margin-left: 6px;
    }
    .score-real {
        font-family: 'Bebas Neue', sans-serif; font-size: 1.3rem;
        color: #94a3b8; min-width: 46px; text-align: center;
    }
    .badge-admin {
        background: rgba(239,68,68,0.15); color: #f87171;
        border-radius: 10px; padding: 2px 10px; font-size: 0.72rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

try:
    sb = conectar()
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "aleotero")


def _hash_pwd(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


def _generar_password(largo: int = 8) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(largo))


# ══════════════════════════════════════════════════════════════════════════
# ESTADO DE SESIÓN
# ══════════════════════════════════════════════════════════════════════════
for key, default in [
    ("es_admin", False),
    ("jugador_id", None),
    ("jugador_nombre", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def _cerrar_sesion():
    st.session_state.es_admin = False
    st.session_state.jugador_id = None
    st.session_state.jugador_nombre = None
    st.rerun()


sesion_activa = st.session_state.es_admin or st.session_state.jugador_id is not None

# ══════════════════════════════════════════════════════════════════════════
# SIDEBAR: LOGIN / REGISTRO
# ══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🔐 Mi cuenta")

    if st.session_state.es_admin:
        st.markdown('<span class="badge-admin">✅ ADMIN ACTIVO</span>', unsafe_allow_html=True)
        if st.button("Cerrar sesión", use_container_width=True):
            _cerrar_sesion()

    elif st.session_state.jugador_id:
        st.success(f"Sesión iniciada como **{st.session_state.jugador_nombre}**")
        if st.button("Cerrar sesión", use_container_width=True):
            _cerrar_sesion()

    else:
        modo = st.radio("Ingresar como:", ["Jugador", "Admin"], key="modo_login", horizontal=True)

        if modo == "Admin":
            user_a = st.text_input("Usuario admin", key="admin_user")
            pwd_a = st.text_input("Contraseña", type="password", key="admin_pwd")
            if st.button("Ingresar", use_container_width=True, key="btn_admin"):
                if user_a.strip() == ADMIN_USERNAME and pwd_a == ADMIN_PASSWORD:
                    st.session_state.es_admin = True
                    st.rerun()
                else:
                    st.error("Usuario o contraseña de admin incorrectos.")

        else:
            tab_login, tab_registro = st.tabs(["Ingresar", "Crear cuenta"])

            with tab_login:
                user_in = st.text_input("Usuario", key="login_user")
                pwd_in = st.text_input("Contraseña", type="password", key="login_pwd")
                if st.button("Ingresar", use_container_width=True, key="btn_ingresar"):
                    try:
                        res = (
                            sb.table("jugadores")
                            .select("id, nombre, username, password_hash")
                            .eq("username", user_in.strip().lower())
                            .execute()
                        )
                        if res.data and res.data[0].get("password_hash") == _hash_pwd(pwd_in):
                            st.session_state.jugador_id = res.data[0]["id"]
                            st.session_state.jugador_nombre = res.data[0]["nombre"]
                            st.rerun()
                        else:
                            st.error("Usuario o contraseña incorrectos.")
                    except Exception as e:
                        st.error(f"Error al ingresar: {e}")

            with tab_registro:
                nombre_new = st.text_input("Tu nombre", key="reg_nombre")
                user_new = st.text_input("Elegí un usuario", key="reg_user")
                pwd_new = st.text_input("Elegí una contraseña", type="password", key="reg_pwd")
                if st.button("Crear cuenta", use_container_width=True, key="btn_registrar"):
                    if not (nombre_new.strip() and user_new.strip() and pwd_new):
                        st.warning("Completá nombre, usuario y contraseña.")
                    else:
                        try:
                            existe = (
                                sb.table("jugadores")
                                .select("id")
                                .eq("username", user_new.strip().lower())
                                .execute()
                            )
                            if existe.data:
                                st.error("Ese usuario ya existe, elegí otro.")
                            else:
                                nuevo = (
                                    sb.table("jugadores")
                                    .insert({
                                        "nombre": nombre_new.strip(),
                                        "username": user_new.strip().lower(),
                                        "password_hash": _hash_pwd(pwd_new),
                                    })
                                    .execute()
                                )
                                st.session_state.jugador_id = nuevo.data[0]["id"]
                                st.session_state.jugador_nombre = nuevo.data[0]["nombre"]
                                st.success("¡Cuenta creada! Ya podés cargar tu boleta.")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error al crear la cuenta: {e}")

st.markdown('<div class="titulo-pagina">📝 FIXTURE DIGITAL</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitulo-pagina">Clausura 2026 · Zona A, Zona B e Interzonal</div>',
    unsafe_allow_html=True,
)

if not sesion_activa:
    st.info(
        "🔒 Iniciá sesión, creá tu cuenta, o entrá como Admin en la barra lateral "
        "para acceder al fixture."
    )
    st.stop()


# ══════════════════════════════════════════════════════════════════════════
# DATOS COMPARTIDOS
# ══════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=30)
def cargar_partidos():
    return sb.table("partidos").select("*").execute().data


def cargar_pronosticos_de(j_id):
    res = (
        sb.table("pronosticos")
        .select("id, partido_id, goles_local_pred, goles_visitante_pred, puntos")
        .eq("jugador_id", j_id)
        .execute()
    )
    return {row["partido_id"]: row for row in (res.data or [])}


def agrupar_por_zona_fecha(partidos):
    por_zona = {}
    for p in partidos:
        por_zona.setdefault(p["zona"], {}).setdefault(p["fecha_numero"], []).append(p)
    zonas_orden = sorted(
        por_zona.keys(), key=lambda z: (0 if z == "A" else 1 if z == "B" else 2, z)
    )
    return por_zona, zonas_orden


def etiqueta_zona(z):
    return "Interzonal" if z == "Interzonal" else f"Zona {z}"


try:
    partidos_db = cargar_partidos()
except Exception as e:
    st.error(f"No se pudieron cargar los partidos: {e}")
    st.stop()

if not partidos_db:
    st.info("Todavía no hay partidos cargados.")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════
# RENDER DE UNA BOLETA (reutilizable: jugador viendo la suya, o admin
# viendo/editando la de cualquiera)
# ══════════════════════════════════════════════════════════════════════════
def mostrar_boleta(jugador_objetivo_id, jugador_objetivo_nombre, editable: bool, key_ns: str):
    por_zona, zonas_orden = agrupar_por_zona_fecha(partidos_db)
    pron = cargar_pronosticos_de(jugador_objetivo_id)

    def guardar(partido_id, gl, gv):
        try:
            existente = pron.get(partido_id)
            payload = {"goles_local_pred": int(gl), "goles_visitante_pred": int(gv)}
            if existente:
                sb.table("pronosticos").update(payload).eq("id", existente["id"]).execute()
            else:
                sb.table("pronosticos").insert({
                    "jugador_id": jugador_objetivo_id,
                    "partido_id": partido_id,
                    **payload,
                }).execute()
            st.toast(f"Pronóstico guardado: {gl}-{gv}", icon="✅")
            return True
        except Exception as e:
            st.error(f"No se pudo guardar: {e}")
            return False

    tabs = st.tabs([etiqueta_zona(z) for z in zonas_orden])
    for tab, zona in zip(tabs, zonas_orden):
        with tab:
            fechas = sorted(por_zona[zona].keys(), key=int)
            for fecha in fechas:
                partidos_fecha = sorted(
                    por_zona[zona][fecha],
                    key=lambda p: (p.get("fecha_partido") or "9999-99-99", p.get("hora") or "99:99"),
                )
                cargados = sum(1 for p in partidos_fecha if p["id"] in pron)
                with st.expander(f"Fecha {fecha}  ·  {cargados}/{len(partidos_fecha)} pronósticos cargados"):
                    for p in partidos_fecha:
                        local = p["equipo_local"]
                        visitante = p["equipo_visitante"]
                        gl_real = p.get("goles_local")
                        gv_real = p.get("goles_visitante")
                        ya_jugado = gl_real is not None and gv_real is not None

                        esc_local = url_escudo(local) or ""
                        esc_visit = url_escudo(visitante) or ""
                        img_local = f'<img src="{esc_local}" class="fila-escudo">' if esc_local else "🛡️"
                        img_visit = f'<img src="{esc_visit}" class="fila-escudo">' if esc_visit else "🛡️"

                        meta_parts = []
                        if p.get("fecha_partido"):
                            meta_parts.append(str(p["fecha_partido"]))
                        if p.get("hora"):
                            meta_parts.append(str(p["hora"]))
                        if p.get("estadio"):
                            meta_parts.append(str(p["estadio"]))
                        meta_str = " · ".join(meta_parts) if meta_parts else "Fecha a confirmar"
                        st.markdown(f'<div class="fila-meta">{meta_str}</div>', unsafe_allow_html=True)

                        col_local, col_gl, col_sep, col_gv, col_visit, col_estado = st.columns(
                            [3, 1, 0.4, 1, 3, 2]
                        )
                        with col_local:
                            st.markdown(
                                f'<div class="fila-equipo">{img_local}<span>{local}</span></div>',
                                unsafe_allow_html=True,
                            )

                        prev = pron.get(p["id"])
                        key_gl = f"gl_{key_ns}_{jugador_objetivo_id}_{p['id']}"
                        key_gv = f"gv_{key_ns}_{jugador_objetivo_id}_{p['id']}"

                        if ya_jugado or not editable:
                            with col_gl:
                                st.markdown(
                                    f'<div class="score-real">{gl_real if ya_jugado else "-"}</div>',
                                    unsafe_allow_html=True,
                                )
                            with col_sep:
                                st.markdown('<div class="score-real">-</div>', unsafe_allow_html=True)
                            with col_gv:
                                st.markdown(
                                    f'<div class="score-real">{gv_real if ya_jugado else "-"}</div>',
                                    unsafe_allow_html=True,
                                )
                            with col_visit:
                                st.markdown(
                                    f'<div class="fila-equipo derecha"><span>{visitante}</span>{img_visit}</div>',
                                    unsafe_allow_html=True,
                                )
                            with col_estado:
                                if prev:
                                    pts = prev.get("puntos")
                                    pron_txt = f'{prev["goles_local_pred"]}-{prev["goles_visitante_pred"]}'
                                    st.markdown(
                                        f'<span class="badge-jugado">Pron.: {pron_txt}</span>'
                                        + (f'<span class="badge-puntos">+{pts} pts</span>' if pts is not None else ""),
                                        unsafe_allow_html=True,
                                    )
                                else:
                                    st.markdown(
                                        '<span class="badge-jugado" style="background:rgba(148,163,184,0.15);'
                                        'color:#94a3b8;">Sin pronóstico</span>',
                                        unsafe_allow_html=True,
                                    )
                        else:
                            with col_gl:
                                gl_val = st.number_input(
                                    f"Goles {local}", min_value=0, max_value=20,
                                    value=prev["goles_local_pred"] if prev else 0,
                                    key=key_gl, label_visibility="collapsed",
                                )
                            with col_sep:
                                st.markdown('<div class="score-real">-</div>', unsafe_allow_html=True)
                            with col_gv:
                                gv_val = st.number_input(
                                    f"Goles {visitante}", min_value=0, max_value=20,
                                    value=prev["goles_visitante_pred"] if prev else 0,
                                    key=key_gv, label_visibility="collapsed",
                                )
                            with col_visit:
                                st.markdown(
                                    f'<div class="fila-equipo derecha"><span>{visitante}</span>{img_visit}</div>',
                                    unsafe_allow_html=True,
                                )
                            with col_estado:
                                ya_guardado = (
                                    prev
                                    and prev["goles_local_pred"] == gl_val
                                    and prev["goles_visitante_pred"] == gv_val
                                )
                                if st.button(
                                    "✅ Guardado" if ya_guardado else "💾 Guardar",
                                    key=f"save_{key_ns}_{jugador_objetivo_id}_{p['id']}",
                                    use_container_width=True,
                                    disabled=bool(ya_guardado),
                                ):
                                    if guardar(p["id"], gl_val, gv_val):
                                        st.rerun()

                        st.markdown("<hr style='opacity:0.08;margin:6px 0;'>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# VISTA JUGADOR NORMAL — solo ve/edita su propia boleta
# ══════════════════════════════════════════════════════════════════════════
if not st.session_state.es_admin:
    mostrar_boleta(
        st.session_state.jugador_id,
        st.session_state.jugador_nombre,
        editable=True,
        key_ns="propia",
    )
    st.stop()


# ══════════════════════════════════════════════════════════════════════════
# VISTA ADMIN — control total
# ══════════════════════════════════════════════════════════════════════════
tab_resultados, tab_jugadores, tab_boletas = st.tabs(
    ["⚽ Cargar Resultados", "👥 Jugadores", "📋 Boletas de Jugadores"]
)

# --- Tab 1: cargar/editar resultados reales de los partidos --------------
with tab_resultados:
    st.caption(
        "Cargá el resultado real de cada partido. Al guardar, el trigger de la "
        "base recalcula automáticamente los puntos de todos los jugadores que "
        "pronosticaron ese partido."
    )
    por_zona, zonas_orden = agrupar_por_zona_fecha(partidos_db)
    tabs_r = st.tabs([etiqueta_zona(z) for z in zonas_orden])
    for tab, zona in zip(tabs_r, zonas_orden):
        with tab:
            fechas = sorted(por_zona[zona].keys(), key=int)
            for fecha in fechas:
                partidos_fecha = sorted(
                    por_zona[zona][fecha],
                    key=lambda p: (p.get("fecha_partido") or "9999-99-99", p.get("hora") or "99:99"),
                )
                with st.expander(f"Fecha {fecha}"):
                    for p in partidos_fecha:
                        local, visitante = p["equipo_local"], p["equipo_visitante"]
                        st.markdown(f"**{local}** vs **{visitante}**")
                        c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
                        with c1:
                            gl_new = st.number_input(
                                "Goles local", min_value=0, max_value=20,
                                value=p.get("goles_local") if p.get("goles_local") is not None else 0,
                                key=f"admin_gl_{p['id']}",
                            )
                        with c2:
                            gv_new = st.number_input(
                                "Goles visitante", min_value=0, max_value=20,
                                value=p.get("goles_visitante") if p.get("goles_visitante") is not None else 0,
                                key=f"admin_gv_{p['id']}",
                            )
                        with c3:
                            estado_new = st.selectbox(
                                "Estado", ["a_confirmar", "confirmado"],
                                index=0 if p.get("estado") != "confirmado" else 1,
                                key=f"admin_estado_{p['id']}",
                            )
                        with c4:
                            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                            if st.button("💾 Guardar", key=f"admin_save_{p['id']}", use_container_width=True):
                                try:
                                    sb.table("partidos").update({
                                        "goles_local": int(gl_new),
                                        "goles_visitante": int(gv_new),
                                        "estado": estado_new,
                                    }).eq("id", p["id"]).execute()
                                    cargar_partidos.clear()
                                    st.toast("Resultado guardado.", icon="✅")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al guardar: {e}")
                        st.markdown("<hr style='opacity:0.08;'>", unsafe_allow_html=True)

# --- Tab 2: administrar jugadores -----------------------------------------
with tab_jugadores:
    st.subheader("➕ Crear jugador manualmente")
    with st.form("form_nuevo_jugador"):
        nombre_adm = st.text_input("Nombre")
        user_adm = st.text_input("Usuario")
        crear_adm = st.form_submit_button("Crear jugador (contraseña autogenerada)")
        if crear_adm:
            if not (nombre_adm.strip() and user_adm.strip()):
                st.warning("Completá nombre y usuario.")
            else:
                try:
                    existe = sb.table("jugadores").select("id").eq("username", user_adm.strip().lower()).execute()
                    if existe.data:
                        st.error("Ese usuario ya existe.")
                    else:
                        pwd_gen = _generar_password(8)
                        sb.table("jugadores").insert({
                            "nombre": nombre_adm.strip(),
                            "username": user_adm.strip().lower(),
                            "password_hash": _hash_pwd(pwd_gen),
                        }).execute()
                        st.success(
                            f"Jugador creado. Usuario: `{user_adm.strip().lower()}` · "
                            f"Contraseña: `{pwd_gen}` (copiala ahora, no se vuelve a mostrar)."
                        )
                except Exception as e:
                    st.error(f"Error al crear jugador: {e}")

    st.divider()
    st.subheader("👥 Jugadores registrados")
    try:
        jugadores_resp = sb.table("jugadores").select("id, nombre, username").order("nombre").execute()
        jugadores = jugadores_resp.data or []
    except Exception as e:
        st.error(f"No se pudo listar jugadores: {e}")
        jugadores = []

    if not jugadores:
        st.info("Todavía no hay jugadores registrados.")

    for j in jugadores:
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        with c1:
            st.write(f"**{j['nombre']}**")
        with c2:
            st.caption(f"@{j.get('username', '—')}")
        with c3:
            if st.button("🔑 Resetear contraseña", key=f"reset_{j['id']}", use_container_width=True):
                nueva_pwd = _generar_password(8)
                sb.table("jugadores").update({"password_hash": _hash_pwd(nueva_pwd)}).eq("id", j["id"]).execute()
                st.success(f"Nueva contraseña para **{j['nombre']}**: `{nueva_pwd}` (copiala ahora).")
        with c4:
            if st.button("🗑️", key=f"del_{j['id']}", help="Eliminar jugador (borra también sus pronósticos)"):
                try:
                    sb.table("jugadores").delete().eq("id", j["id"]).execute()
                    st.toast(f"Jugador {j['nombre']} eliminado.", icon="🗑️")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al eliminar: {e}")

# --- Tab 3: ver/editar la boleta de cualquier jugador ---------------------
with tab_boletas:
    try:
        jugadores_resp2 = sb.table("jugadores").select("id, nombre").order("nombre").execute()
        jugadores2 = jugadores_resp2.data or []
    except Exception as e:
        st.error(f"No se pudo listar jugadores: {e}")
        jugadores2 = []

    if not jugadores2:
        st.info("Todavía no hay jugadores registrados.")
    else:
        nombres_map = {j["nombre"]: j["id"] for j in jugadores2}
        nombre_sel = st.selectbox("Ver boleta de:", list(nombres_map.keys()), key="sel_jugador_admin")
        jid_sel = nombres_map[nombre_sel]
        editar_boleta_admin = st.checkbox(
            "Permitir editar esta boleta como admin", value=False, key="chk_editar_admin"
        )
        mostrar_boleta(jid_sel, nombre_sel, editable=editar_boleta_admin, key_ns=f"admin_{jid_sel}")
