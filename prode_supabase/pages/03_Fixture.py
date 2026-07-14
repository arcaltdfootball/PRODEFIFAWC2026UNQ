"""
03_Fixture.py — Prode FIFA WC 2026
Cambios:
  - Boleta usa 1 / X / 2 (local / empate / visitante) en vez de goles
  - Admin puede eliminar participantes con confirmación
  - Admin puede resetear (borrar) la lista completa de participantes
  - Resultado se guarda como 1/X/2 y se refleja en 01_Resultados.py
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

    /* Badges */
    .badge-1   { background:rgba(59,130,246,0.18); color:#60a5fa;   border-radius:10px; padding:3px 12px; font-size:0.78rem; font-weight:700; }
    .badge-x   { background:rgba(148,163,184,0.18); color:#94a3b8;  border-radius:10px; padding:3px 12px; font-size:0.78rem; font-weight:700; }
    .badge-2   { background:rgba(239,68,68,0.18);  color:#f87171;   border-radius:10px; padding:3px 12px; font-size:0.78rem; font-weight:700; }
    .badge-ok  { background:rgba(74,222,128,0.15); color:#4ade80;   border-radius:10px; padding:3px 10px; font-size:0.72rem; }
    .badge-pts { background:rgba(232,201,107,0.18);color:#e8c96b;   border-radius:10px; padding:3px 10px; font-size:0.72rem; margin-left:6px; }
    .badge-sin { background:rgba(148,163,184,0.15);color:#94a3b8;   border-radius:10px; padding:3px 10px; font-size:0.72rem; }
    .badge-admin { background:rgba(239,68,68,0.15);color:#f87171;   border-radius:10px; padding:2px 10px; font-size:0.72rem; }

    /* Selector 1/X/2 */
    .opcion-1x2 {
        display: flex; gap: 6px; align-items: center; flex-wrap: wrap;
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


def _signo_a_texto(signo):
    """Convierte 1/X/2 a texto descriptivo."""
    return {"1": "Local (1)", "X": "Empate (X)", "2": "Visitante (2)"}.get(signo, signo or "—")


def _badge_signo(signo):
    """Devuelve HTML del badge según signo."""
    if signo == "1":
        return '<span class="badge-1">1 · LOCAL</span>'
    if signo == "X":
        return '<span class="badge-x">X · EMPATE</span>'
    if signo == "2":
        return '<span class="badge-2">2 · VISIT.</span>'
    return '<span class="badge-sin">Sin pronóstico</span>'


# ══════════════════════════════════════════════════════════════════════════
# ESTADO DE SESIÓN
# ══════════════════════════════════════════════════════════════════════════
for key, default in [
    ("es_admin", False),
    ("jugador_id", None),
    ("jugador_nombre", None),
    ("confirmar_eliminar_id", None),
    ("confirmar_reset_all", False),
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
            pwd_a  = st.text_input("Contraseña", type="password", key="admin_pwd")
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
                pwd_in  = st.text_input("Contraseña", type="password", key="login_pwd")
                if st.button("Ingresar", use_container_width=True, key="btn_ingresar"):
                    try:
                        res = (
                            sb.table("jugadores")
                            .select("id, nombre, username, password_hash")
                            .eq("username", user_in.strip().lower())
                            .execute()
                        )
                        if res.data and res.data[0].get("password_hash") == _hash_pwd(pwd_in):
                            st.session_state.jugador_id     = res.data[0]["id"]
                            st.session_state.jugador_nombre = res.data[0]["nombre"]
                            st.rerun()
                        else:
                            st.error("Usuario o contraseña incorrectos.")
                    except Exception as e:
                        st.error(f"Error al ingresar: {e}")

            with tab_registro:
                nombre_new = st.text_input("Tu nombre", key="reg_nombre")
                user_new   = st.text_input("Elegí un usuario", key="reg_user")
                pwd_new    = st.text_input("Elegí una contraseña", type="password", key="reg_pwd")
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
                                st.session_state.jugador_id     = nuevo.data[0]["id"]
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
        .select("id, partido_id, signo_pred, puntos")
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
# RENDER DE BOLETA CON 1 / X / 2
# ══════════════════════════════════════════════════════════════════════════
def mostrar_boleta(jugador_objetivo_id, jugador_objetivo_nombre, editable: bool, key_ns: str):
    por_zona, zonas_orden = agrupar_por_zona_fecha(partidos_db)
    pron = cargar_pronosticos_de(jugador_objetivo_id)

    def guardar_signo(partido_id, signo):
        """Guarda pronóstico 1/X/2. Calcula puntos si ya hay resultado oficial."""
        try:
            # Obtener resultado real del partido para calcular puntos al instante
            partido_data = next((p for p in partidos_db if p["id"] == partido_id), {})
            gl = partido_data.get("goles_local")
            gv = partido_data.get("goles_visitante")
            signo_real = None
            if gl is not None and gv is not None:
                if gl > gv:
                    signo_real = "1"
                elif gl == gv:
                    signo_real = "X"
                else:
                    signo_real = "2"
            pts = 3 if (signo_real and signo == signo_real) else (0 if signo_real else None)

            existente = pron.get(partido_id)
            payload = {"signo_pred": signo}
            if pts is not None:
                payload["puntos"] = pts

            if existente:
                sb.table("pronosticos").update(payload).eq("id", existente["id"]).execute()
            else:
                sb.table("pronosticos").insert({
                    "jugador_id": jugador_objetivo_id,
                    "partido_id": partido_id,
                    **payload,
                }).execute()
            st.toast(f"Pronóstico guardado: {_signo_a_texto(signo)}", icon="✅")
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
                        local     = p["equipo_local"]
                        visitante = p["equipo_visitante"]
                        gl_real   = p.get("goles_local")
                        gv_real   = p.get("goles_visitante")
                        ya_jugado = gl_real is not None and gv_real is not None

                        # Calcular signo real del partido
                        signo_real = None
                        if ya_jugado:
                            if gl_real > gv_real:   signo_real = "1"
                            elif gl_real == gv_real: signo_real = "X"
                            else:                    signo_real = "2"

                        esc_l = url_escudo(local)    or ""
                        esc_v = url_escudo(visitante) or ""
                        img_l = f'<img src="{esc_l}" class="fila-escudo">' if esc_l else "🛡️"
                        img_v = f'<img src="{esc_v}" class="fila-escudo">' if esc_v else "🛡️"

                        meta_parts = []
                        if p.get("fecha_partido"): meta_parts.append(str(p["fecha_partido"]))
                        if p.get("hora"):          meta_parts.append(str(p["hora"]))
                        if p.get("estadio"):       meta_parts.append(str(p["estadio"]))
                        meta_str = " · ".join(meta_parts) if meta_parts else "Fecha a confirmar"
                        st.markdown(f'<div class="fila-meta">{meta_str}</div>', unsafe_allow_html=True)

                        prev = pron.get(p["id"])
                        signo_prev = prev["signo_pred"] if prev else None

                        col_local, col_vs, col_visit = st.columns([4, 3, 4])
                        with col_local:
                            st.markdown(
                                f'<div class="fila-equipo">{img_l}<span>{local}</span></div>',
                                unsafe_allow_html=True,
                            )
                        with col_vs:
                            if ya_jugado:
                                st.markdown(
                                    f'<div style="text-align:center;font-family:\'Bebas Neue\',sans-serif;'
                                    f'font-size:1.6rem;color:#e8c96b;">{gl_real} - {gv_real}</div>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(
                                    '<div style="text-align:center;font-family:\'Bebas Neue\',sans-serif;'
                                    'font-size:1.2rem;color:#475569;">VS</div>',
                                    unsafe_allow_html=True,
                                )
                        with col_visit:
                            st.markdown(
                                f'<div class="fila-equipo derecha"><span>{visitante}</span>{img_v}</div>',
                                unsafe_allow_html=True,
                            )

                        # ── Selector 1 / X / 2 ──────────────────────────────
                        if editable and not ya_jugado:
                            col_b1, col_bx, col_b2, col_estado = st.columns([1, 1, 1, 2])
                            with col_b1:
                                activo_1 = signo_prev == "1"
                                if st.button(
                                    "1 · LOCAL" if not activo_1 else "✅ 1",
                                    key=f"b1_{key_ns}_{jugador_objetivo_id}_{p['id']}",
                                    use_container_width=True,
                                    type="primary" if activo_1 else "secondary",
                                ):
                                    if guardar_signo(p["id"], "1"):
                                        st.rerun()
                            with col_bx:
                                activo_x = signo_prev == "X"
                                if st.button(
                                    "X · EMPATE" if not activo_x else "✅ X",
                                    key=f"bx_{key_ns}_{jugador_objetivo_id}_{p['id']}",
                                    use_container_width=True,
                                    type="primary" if activo_x else "secondary",
                                ):
                                    if guardar_signo(p["id"], "X"):
                                        st.rerun()
                            with col_b2:
                                activo_2 = signo_prev == "2"
                                if st.button(
                                    "2 · VISIT." if not activo_2 else "✅ 2",
                                    key=f"b2_{key_ns}_{jugador_objetivo_id}_{p['id']}",
                                    use_container_width=True,
                                    type="primary" if activo_2 else "secondary",
                                ):
                                    if guardar_signo(p["id"], "2"):
                                        st.rerun()
                            with col_estado:
                                st.markdown(_badge_signo(signo_prev), unsafe_allow_html=True)

                        else:
                            # Solo lectura o partido ya jugado
                            col_pron, col_pts = st.columns([3, 2])
                            with col_pron:
                                st.markdown(_badge_signo(signo_prev), unsafe_allow_html=True)
                            with col_pts:
                                if ya_jugado and signo_prev:
                                    pts = prev.get("puntos") if prev else None
                                    if signo_prev == signo_real:
                                        st.markdown(
                                            f'<span class="badge-ok">✅ Acertaste</span>'
                                            + (f'<span class="badge-pts">+{pts} pts</span>' if pts is not None else ""),
                                            unsafe_allow_html=True,
                                        )
                                    else:
                                        st.markdown(
                                            f'<span class="badge-sin">❌ No acertaste · Resultado: {_badge_signo(signo_real)}</span>',
                                            unsafe_allow_html=True,
                                        )
                                elif ya_jugado and not signo_prev:
                                    st.markdown(
                                        f'<span class="badge-sin">Sin pronóstico · Fue: {_badge_signo(signo_real)}</span>',
                                        unsafe_allow_html=True,
                                    )

                        st.markdown("<hr style='opacity:0.08;margin:8px 0;'>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# VISTA JUGADOR NORMAL
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
# VISTA ADMIN
# ══════════════════════════════════════════════════════════════════════════
tab_resultados, tab_jugadores, tab_boletas = st.tabs(
    ["⚽ Cargar Resultados", "👥 Jugadores", "📋 Boletas de Jugadores"]
)

# ── Tab 1: resultados reales ──────────────────────────────────────────────
with tab_resultados:
    st.caption(
        "Cargá el resultado real de cada partido. El signo (1/X/2) se calcula "
        "automáticamente y los pronósticos se comparan para asignar puntos."
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
                        gl_act = p.get("goles_local")
                        gv_act = p.get("goles_visitante")

                        # Mostrar signo actual si ya está jugado
                        if gl_act is not None and gv_act is not None:
                            if gl_act > gv_act:   signo_actual = "1 · LOCAL"
                            elif gl_act == gv_act: signo_actual = "X · EMPATE"
                            else:                  signo_actual = "2 · VISITANTE"
                            st.markdown(
                                f"**{local}** vs **{visitante}** — "
                                f"Resultado: `{gl_act}-{gv_act}` → **{signo_actual}**"
                            )
                        else:
                            st.markdown(f"**{local}** vs **{visitante}** — *Sin resultado*")

                        c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
                        with c1:
                            gl_new = st.number_input(
                                "Goles local", min_value=0, max_value=20,
                                value=gl_act if gl_act is not None else 0,
                                key=f"admin_gl_{p['id']}",
                            )
                        with c2:
                            gv_new = st.number_input(
                                "Goles visitante", min_value=0, max_value=20,
                                value=gv_act if gv_act is not None else 0,
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
                                        "goles_local":     int(gl_new),
                                        "goles_visitante": int(gv_new),
                                        "estado":          estado_new,
                                    }).eq("id", p["id"]).execute()

                                    # Recalcular puntos de pronósticos de este partido
                                    if gl_new > gv_new:   signo_r = "1"
                                    elif gl_new == gv_new: signo_r = "X"
                                    else:                  signo_r = "2"

                                    prons = (
                                        sb.table("pronosticos")
                                        .select("id, signo_pred")
                                        .eq("partido_id", p["id"])
                                        .execute()
                                        .data or []
                                    )
                                    for pr in prons:
                                        pts = 3 if pr["signo_pred"] == signo_r else 0
                                        sb.table("pronosticos").update({"puntos": pts}).eq("id", pr["id"]).execute()

                                    cargar_partidos.clear()
                                    st.cache_data.clear()  # limpia también la cache de 01_Resultados.py (funciones cacheadas distintas por módulo)
                                    st.toast(f"Resultado guardado: {gl_new}-{gv_new} ({signo_r})", icon="✅")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al guardar: {e}")
                        st.markdown("<hr style='opacity:0.08;'>", unsafe_allow_html=True)


# ── Tab 2: administrar jugadores ──────────────────────────────────────────
with tab_jugadores:

    # ── Crear jugador ────────────────────────────────────────────────────
    st.subheader("➕ Crear jugador manualmente")
    with st.form("form_nuevo_jugador"):
        nombre_adm = st.text_input("Nombre")
        user_adm   = st.text_input("Usuario")
        crear_adm  = st.form_submit_button("Crear jugador (contraseña autogenerada)")
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
                            "nombre":        nombre_adm.strip(),
                            "username":      user_adm.strip().lower(),
                            "password_hash": _hash_pwd(pwd_gen),
                        }).execute()
                        st.success(
                            f"Jugador creado. Usuario: `{user_adm.strip().lower()}` · "
                            f"Contraseña: `{pwd_gen}` (copiala ahora)."
                        )
                except Exception as e:
                    st.error(f"Error al crear jugador: {e}")

    st.divider()

    # ── Reset total ───────────────────────────────────────────────────────
    st.subheader("🔴 Resetear lista completa de participantes")
    st.warning(
        "⚠️ Esto **elimina TODOS los jugadores y sus pronósticos**. "
        "La acción es irreversible."
    )

    if not st.session_state.confirmar_reset_all:
        if st.button("🗑️ Eliminar TODOS los participantes", type="secondary"):
            st.session_state.confirmar_reset_all = True
            st.rerun()
    else:
        st.error("¿Estás seguro? Esta acción no se puede deshacer.")
        col_si, col_no = st.columns(2)
        with col_si:
            if st.button("✅ Sí, eliminar todo", type="primary"):
                try:
                    # Borrar pronósticos primero (FK), luego jugadores
                    sb.table("pronosticos").delete().neq("id", 0).execute()
                    sb.table("jugadores").delete().neq("id", 0).execute()
                    st.session_state.confirmar_reset_all = False
                    st.toast("✅ Lista de participantes reseteada.", icon="🗑️")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al resetear: {e}")
        with col_no:
            if st.button("❌ Cancelar"):
                st.session_state.confirmar_reset_all = False
                st.rerun()

    st.divider()

    # ── Lista jugadores con eliminar individual ───────────────────────────
    st.subheader("👥 Jugadores registrados")
    try:
        jugadores_resp = sb.table("jugadores").select("id, nombre, username").order("nombre").execute()
        jugadores = jugadores_resp.data or []
    except Exception as e:
        st.error(f"No se pudo listar jugadores: {e}")
        jugadores = []

    if not jugadores:
        st.info("Todavía no hay jugadores registrados.")
    else:
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
                # Botón eliminar con confirmación inline
                if st.session_state.confirmar_eliminar_id == j["id"]:
                    # Modo confirmación
                    st.markdown(f"**¿Eliminar {j['nombre']}?**")
                    col_si2, col_no2 = st.columns(2)
                    with col_si2:
                        if st.button("✅ Sí", key=f"del_si_{j['id']}", use_container_width=True):
                            try:
                                # Borrar pronósticos del jugador primero
                                sb.table("pronosticos").delete().eq("jugador_id", j["id"]).execute()
                                sb.table("jugadores").delete().eq("id", j["id"]).execute()
                                st.session_state.confirmar_eliminar_id = None
                                st.toast(f"Jugador {j['nombre']} eliminado.", icon="🗑️")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al eliminar: {e}")
                    with col_no2:
                        if st.button("❌ No", key=f"del_no_{j['id']}", use_container_width=True):
                            st.session_state.confirmar_eliminar_id = None
                            st.rerun()
                else:
                    if st.button("🗑️", key=f"del_{j['id']}", help="Eliminar jugador"):
                        st.session_state.confirmar_eliminar_id = j["id"]
                        st.rerun()


# ── Tab 3: ver/editar boleta de cualquier jugador ─────────────────────────
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
        nombres_map  = {j["nombre"]: j["id"] for j in jugadores2}
        nombre_sel   = st.selectbox("Ver boleta de:", list(nombres_map.keys()), key="sel_jugador_admin")
        jid_sel      = nombres_map[nombre_sel]
        editar_admin = st.checkbox("Permitir editar esta boleta como admin", value=False, key="chk_editar_admin")
        mostrar_boleta(jid_sel, nombre_sel, editable=editar_admin, key_ns=f"admin_{jid_sel}")
