"""
03_Fixture.py — Prode Liga Profesional Argentina
Cambios:
  - Boleta usa marcador exacto (goles local / goles visitante); el signo
    (1/X/2) se deriva automáticamente a partir del marcador cargado.
  - NUEVO: cada partido tiene un "modo de pronóstico" configurable por el
    admin (por fecha completa o partido a partido):
        · "exacto" → el jugador carga el marcador exacto (hasta 3 puntos).
        · "signo"  → el jugador solo elige 1 / X / 2 (hasta 1 punto).
    Esto permite que algunas fechas se jueguen a resultado exacto y otras
    solo a signo.
  - Sistema de puntaje: 1 punto por acertar el signo (Local/Empate/Visitante),
    3 puntos en total si se acierta el marcador exacto (solo aplica en
    partidos con modo "exacto").
  - Admin puede eliminar participantes con confirmación
  - Admin puede resetear (borrar) la lista completa de participantes
  - Resultado se guarda como goles y se refleja en 01_Resultados.py
  - Boleta rediseñada con cards modernas tipo "sabana" de partidos.

IMPORTANTE: la tabla `pronosticos` en Supabase necesita las columnas
`goles_local_pred` (int, nullable) y `goles_visitante_pred` (int, nullable)
además de las existentes `signo_pred` y `puntos`. La tabla `partidos`
necesita la columna `modo_pronostico` (text, nullable, default 'exacto').
Si no existen, correr:

    ALTER TABLE pronosticos ADD COLUMN goles_local_pred integer;
    ALTER TABLE pronosticos ADD COLUMN goles_visitante_pred integer;
    ALTER TABLE partidos ADD COLUMN modo_pronostico text DEFAULT 'exacto';
"""
import base64
import hashlib
import json
import os
import secrets
import string

import streamlit as st
from database import conectar
from escudos_map import url_escudo


def _rol_de_supabase_key():
    """Decodifica el JWT de SUPABASE_KEY (sin validar firma) solo para
    mostrar el campo 'role' (anon / service_role) y así diagnosticar
    a simple vista qué key está usando realmente la app en este momento."""
    key = os.environ.get("SUPABASE_KEY", "")
    if not key:
        try:
            key = st.secrets.get("SUPABASE_KEY", "")
        except Exception:
            key = ""
    if not key or key.count(".") != 2:
        return None, None
    try:
        payload_b64 = key.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)  # padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get("role"), key[-6:]
    except Exception:
        return None, key[-6:] if key else None

st.set_page_config(page_title="Fixture - Mi Boleta", page_icon="📝", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap');

    [data-testid="stApp"] {
        background-image: url('https://raw.githubusercontent.com/arcaltdfootball/PRODEFIFAWC2026UNQ/main/prode_supabase/AFA2026.png');
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
    .badge-modo-exacto { background:rgba(232,201,107,0.16); color:#e8c96b; border:1px solid rgba(232,201,107,0.35); border-radius:20px; padding:2px 12px; font-size:0.68rem; font-weight:600; font-family:'Inter',sans-serif; letter-spacing:.3px; }
    .badge-modo-signo  { background:rgba(96,165,250,0.16); color:#60a5fa; border:1px solid rgba(96,165,250,0.35); border-radius:20px; padding:2px 12px; font-size:0.68rem; font-weight:600; font-family:'Inter',sans-serif; letter-spacing:.3px; }

    /* Selector 1/X/2 */
    .opcion-1x2 {
        display: flex; gap: 6px; align-items: center; flex-wrap: wrap;
    }

    /* ═══════════ CARD MODERNA DE PARTIDO (sabana de boleta) ═══════════ */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(155deg, rgba(25,31,46,0.92) 0%, rgba(15,20,32,0.94) 100%);
        border: 1px solid rgba(232,201,107,0.14) !important;
        border-radius: 18px !important;
        box-shadow: 0 4px 18px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.03);
        transition: border-color .15s ease, box-shadow .15s ease;
        margin-bottom: 14px;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: rgba(232,201,107,0.35) !important;
        box-shadow: 0 6px 22px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.05);
    }

    .card-top-row {
        display: flex; align-items: center; justify-content: space-between;
        margin-bottom: 10px; gap: 8px; flex-wrap: wrap;
    }
    .card-meta {
        font-size: 0.72rem; color: #64748b; font-family: 'Inter', sans-serif;
        display: flex; align-items: center; gap: 6px;
    }
    .card-tag-fecha {
        background: rgba(255,255,255,0.04); color: #94a3b8; border-radius: 8px;
        padding: 2px 9px; font-size: 0.68rem; font-family: 'Inter', sans-serif;
        border: 1px solid rgba(255,255,255,0.06);
    }

    .card-equipos {
        display: flex; align-items: center; justify-content: space-between;
        gap: 10px; margin: 6px 0 14px 0;
    }
    .card-equipo {
        display: flex; flex-direction: column; align-items: center; gap: 6px;
        flex: 1; min-width: 0;
    }
    .card-equipo .nombre-equipo {
        font-family: 'Inter', sans-serif; font-weight: 600; font-size: 0.82rem;
        color: #e5e7eb; text-align: center; line-height: 1.15;
        overflow: hidden; text-overflow: ellipsis; display: -webkit-box;
        -webkit-line-clamp: 2; -webkit-box-orient: vertical;
    }
    .card-escudo-grande {
        width: 52px; height: 52px; object-fit: contain;
        filter: drop-shadow(0 2px 6px rgba(0,0,0,0.4));
    }
    .card-centro {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        min-width: 64px;
    }
    .card-vs {
        font-family: 'Bebas Neue', sans-serif; font-size: 1.05rem; color: #475569;
        letter-spacing: 1px;
    }
    .card-marcador {
        font-family: 'Bebas Neue', sans-serif; font-size: 1.9rem; color: #e8c96b;
        letter-spacing: 2px; line-height: 1;
    }
    .card-marcador-sub {
        font-size: 0.62rem; color: #64748b; font-family: 'Inter', sans-serif;
        margin-top: 2px; text-transform: uppercase; letter-spacing: .5px;
    }

    .card-footer {
        display: flex; align-items: center; justify-content: space-between;
        gap: 8px; flex-wrap: wrap; margin-top: 10px;
    }

    /* Botones tipo "chip" para 1/X/2 */
    div[data-testid="stButton"] button {
        border-radius: 12px !important;
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


def _modo_partido(p):
    """Devuelve el modo de pronóstico de un partido: 'exacto' o 'signo'.
    Si la columna no existe todavía en la base (None), por defecto es 'exacto'
    para no romper partidos ya cargados."""
    modo = (p.get("modo_pronostico") or "exacto").strip().lower()
    return modo if modo in ("exacto", "signo") else "exacto"


def _badge_modo(modo):
    if modo == "signo":
        return '<span class="badge-modo-signo">🔀 Solo 1 / X / 2</span>'
    return '<span class="badge-modo-exacto">🎯 Resultado exacto</span>'


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
        _rol_key, _tail_key = _rol_de_supabase_key()
        if _rol_key == "service_role":
            st.caption(f"🔑 Supabase key activa: `service_role` (…{_tail_key})")
        elif _rol_key:
            st.caption(f"⚠️ Supabase key activa: `{_rol_key}` (…{_tail_key}) — NO es service_role")
        else:
            st.caption("⚠️ No se pudo leer/decodificar SUPABASE_KEY")
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


@st.cache_data(ttl=20, show_spinner=False)
def cargar_pronosticos_de(j_id):
    """
    Trae SOLO los pronósticos del jugador indicado (filtrado por jugador_id
    en la propia consulta a Supabase). Nunca trae los de otros participantes.
    Se cachea por jugador (ttl corto) para no repetir la consulta en cada
    rerun/click y así hacer la boleta más ágil.
    """
    res = (
        sb.table("pronosticos")
        .select("id, partido_id, signo_pred, goles_local_pred, goles_visitante_pred, puntos")
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

    def _calcular_signo(gl, gv):
        if gl is None or gv is None:
            return None
        if gl > gv:
            return "1"
        if gl == gv:
            return "X"
        return "2"

    def guardar_pronostico(partido_id, gl_pred, gv_pred):
        """
        Guarda el pronóstico de marcador exacto (goles local/visitante).
        El signo (1/X/2) se deriva automáticamente del marcador.
        Sistema de puntaje:
          - 1 punto si acierta el signo (Local / Empate / Visitante)
          - 3 puntos en total si acierta el resultado exacto
        """
        try:
            signo = _calcular_signo(gl_pred, gv_pred)

            # Obtener resultado real del partido para calcular puntos al instante
            partido_data = next((p for p in partidos_db if p["id"] == partido_id), {})
            gl_real = partido_data.get("goles_local")
            gv_real = partido_data.get("goles_visitante")
            signo_real = _calcular_signo(gl_real, gv_real)

            if signo_real is None:
                pts = None  # partido todavía no jugado
            elif gl_pred == gl_real and gv_pred == gv_real:
                pts = 3
            elif signo == signo_real:
                pts = 1
            else:
                pts = 0

            existente = pron.get(partido_id)
            payload = {
                "signo_pred": signo,
                "goles_local_pred": gl_pred,
                "goles_visitante_pred": gv_pred,
            }
            if pts is not None:
                payload["puntos"] = pts

            if existente:
                resp = sb.table("pronosticos").update(payload).eq("id", existente["id"]).execute()
                if not (resp.data or []):
                    st.error(
                        "⚠️ No se guardó (0 filas afectadas). Probablemente RLS está "
                        "bloqueando el UPDATE en 'pronosticos' para la key usada."
                    )
                    return False
            else:
                resp = sb.table("pronosticos").insert({
                    "jugador_id": jugador_objetivo_id,
                    "partido_id": partido_id,
                    **payload,
                }).execute()
                if not (resp.data or []):
                    st.error(
                        "⚠️ No se guardó (0 filas insertadas). Probablemente RLS está "
                        "bloqueando el INSERT en 'pronosticos' para la key usada."
                    )
                    return False
            st.toast(
                f"Pronóstico guardado: {gl_pred}-{gv_pred} ({_signo_a_texto(signo)})",
                icon="✅",
            )
            cargar_pronosticos_de.clear()
            return True
        except Exception as e:
            st.error(f"No se pudo guardar: {e}")
            st.exception(e)
            return False

    def guardar_pronostico_signo(partido_id, signo_pred):
        """
        Guarda el pronóstico de un partido en modo 'solo signo' (1/X/2),
        sin marcador exacto. Puntaje: 1 punto si acierta el signo, 0 si no.
        """
        try:
            partido_data = next((p for p in partidos_db if p["id"] == partido_id), {})
            gl_real = partido_data.get("goles_local")
            gv_real = partido_data.get("goles_visitante")
            signo_real = _calcular_signo(gl_real, gv_real)

            if signo_real is None:
                pts = None  # partido todavía no jugado
            elif signo_pred == signo_real:
                pts = 1
            else:
                pts = 0

            existente = pron.get(partido_id)
            payload = {
                "signo_pred": signo_pred,
                "goles_local_pred": None,
                "goles_visitante_pred": None,
            }
            if pts is not None:
                payload["puntos"] = pts

            if existente:
                resp = sb.table("pronosticos").update(payload).eq("id", existente["id"]).execute()
                if not (resp.data or []):
                    st.error(
                        "⚠️ No se guardó (0 filas afectadas). Probablemente RLS está "
                        "bloqueando el UPDATE en 'pronosticos' para la key usada."
                    )
                    return False
            else:
                resp = sb.table("pronosticos").insert({
                    "jugador_id": jugador_objetivo_id,
                    "partido_id": partido_id,
                    **payload,
                }).execute()
                if not (resp.data or []):
                    st.error(
                        "⚠️ No se guardó (0 filas insertadas). Probablemente RLS está "
                        "bloqueando el INSERT en 'pronosticos' para la key usada."
                    )
                    return False
            st.toast(f"Pronóstico guardado: {_signo_a_texto(signo_pred)}", icon="✅")
            cargar_pronosticos_de.clear()
            return True
        except Exception as e:
            st.error(f"No se pudo guardar: {e}")
            st.exception(e)
            return False

    tabs = st.tabs([etiqueta_zona(z) for z in zonas_orden])
    for tab, zona in zip(tabs, zonas_orden):
        with tab:
            fechas = sorted(por_zona[zona].keys(), key=int)

            # ── Elegir UNA fecha por vez: evita construir los widgets de
            #    todas las fechas del torneo en cada carga/click, que era lo
            #    que hacía pesada la página. Por defecto, arranca en la
            #    primera fecha que todavía tiene partidos sin pronosticar.
            def _fecha_tiene_pendientes(f):
                partidos_f = por_zona[zona][f]
                return any(p["id"] not in pron for p in partidos_f)

            idx_default = 0
            for i, f in enumerate(fechas):
                if _fecha_tiene_pendientes(f):
                    idx_default = i
                    break

            fecha_sel = st.selectbox(
                "📅 Elegí la fecha",
                fechas,
                index=idx_default,
                format_func=lambda f: f"Fecha {f}",
                key=f"fecha_sel_{key_ns}_{jugador_objetivo_id}_{zona}",
            )

            for fecha in [fecha_sel]:
                partidos_fecha = sorted(
                    por_zona[zona][fecha],
                    key=lambda p: (p.get("fecha_partido") or "9999-99-99", p.get("hora") or "99:99"),
                )
                cargados = sum(1 for p in partidos_fecha if p["id"] in pron)
                with st.expander(
                    f"Fecha {fecha}  ·  {cargados}/{len(partidos_fecha)} pronósticos cargados",
                    expanded=True,
                ):
                    for p in partidos_fecha:
                        local     = p["equipo_local"]
                        visitante = p["equipo_visitante"]
                        gl_real   = p.get("goles_local")
                        gv_real   = p.get("goles_visitante")
                        ya_jugado = gl_real is not None and gv_real is not None
                        modo      = _modo_partido(p)

                        signo_real = _calcular_signo(gl_real, gv_real) if ya_jugado else None

                        esc_l = url_escudo(local)    or ""
                        esc_v = url_escudo(visitante) or ""
                        img_l = f'<img src="{esc_l}" class="card-escudo-grande">' if esc_l else '<div style="font-size:2rem;">🛡️</div>'
                        img_v = f'<img src="{esc_v}" class="card-escudo-grande">' if esc_v else '<div style="font-size:2rem;">🛡️</div>'

                        meta_parts = []
                        if p.get("fecha_partido"): meta_parts.append(f"📅 {p['fecha_partido']}")
                        if p.get("hora"):          meta_parts.append(f"🕒 {p['hora']}")
                        if p.get("estadio"):       meta_parts.append(f"📍 {p['estadio']}")
                        meta_str = " &nbsp;·&nbsp; ".join(meta_parts) if meta_parts else "Fecha a confirmar"

                        prev = pron.get(p["id"])
                        signo_prev   = prev["signo_pred"] if prev else None
                        gl_pred_prev = prev.get("goles_local_pred") if prev else None
                        gv_pred_prev = prev.get("goles_visitante_pred") if prev else None

                        with st.container(border=True):
                            # ── Encabezado de la card: meta + modo ──────────
                            st.markdown(
                                f'<div class="card-top-row">'
                                f'<span class="card-meta">{meta_str}</span>'
                                f'<span>{_badge_modo(modo)}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                            # ── Equipos + marcador/VS ────────────────────────
                            if ya_jugado:
                                centro_html = (
                                    f'<div class="card-marcador">{gl_real} - {gv_real}</div>'
                                    f'<div class="card-marcador-sub">Final</div>'
                                )
                            else:
                                centro_html = '<div class="card-vs">VS</div>'

                            st.markdown(
                                f'<div class="card-equipos">'
                                f'<div class="card-equipo">{img_l}<span class="nombre-equipo">{local}</span></div>'
                                f'<div class="card-centro">{centro_html}</div>'
                                f'<div class="card-equipo">{img_v}<span class="nombre-equipo">{visitante}</span></div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                            # ── Zona de pronóstico ───────────────────────────
                            if editable and not ya_jugado:
                                if modo == "signo":
                                    # Selector 1 / X / 2 tipo chips, guardado inmediato
                                    col_b1, col_bx, col_b2 = st.columns(3)
                                    seleccionado = None
                                    with col_b1:
                                        if st.button(
                                            f"🏠 {local}\n1",
                                            key=f"s1_{key_ns}_{jugador_objetivo_id}_{p['id']}",
                                            use_container_width=True,
                                            type="primary" if signo_prev == "1" else "secondary",
                                        ):
                                            seleccionado = "1"
                                    with col_bx:
                                        if st.button(
                                            "🤝 Empate\nX",
                                            key=f"sx_{key_ns}_{jugador_objetivo_id}_{p['id']}",
                                            use_container_width=True,
                                            type="primary" if signo_prev == "X" else "secondary",
                                        ):
                                            seleccionado = "X"
                                    with col_b2:
                                        if st.button(
                                            f"✈️ {visitante}\n2",
                                            key=f"s2_{key_ns}_{jugador_objetivo_id}_{p['id']}",
                                            use_container_width=True,
                                            type="primary" if signo_prev == "2" else "secondary",
                                        ):
                                            seleccionado = "2"

                                    if seleccionado is not None:
                                        if guardar_pronostico_signo(p["id"], seleccionado):
                                            st.rerun()

                                    st.markdown(
                                        f'<div class="card-footer">{_badge_signo(signo_prev)}</div>',
                                        unsafe_allow_html=True,
                                    )
                                else:
                                    # Marcador exacto
                                    col_gl, col_gv, col_btn = st.columns([1, 1, 1.6])
                                    with col_gl:
                                        gl_new_pred = st.number_input(
                                            f"Goles {local}", min_value=0, max_value=15,
                                            value=gl_pred_prev if gl_pred_prev is not None else 0,
                                            key=f"gl_{key_ns}_{jugador_objetivo_id}_{p['id']}",
                                        )
                                    with col_gv:
                                        gv_new_pred = st.number_input(
                                            f"Goles {visitante}", min_value=0, max_value=15,
                                            value=gv_pred_prev if gv_pred_prev is not None else 0,
                                            key=f"gv_{key_ns}_{jugador_objetivo_id}_{p['id']}",
                                        )
                                    with col_btn:
                                        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                                        if st.button(
                                            "💾 Guardar pronóstico",
                                            key=f"guardar_{key_ns}_{jugador_objetivo_id}_{p['id']}",
                                            use_container_width=True,
                                            type="primary",
                                        ):
                                            if guardar_pronostico(p["id"], int(gl_new_pred), int(gv_new_pred)):
                                                st.rerun()

                                    st.markdown(
                                        f'<div class="card-footer">{_badge_signo(signo_prev)}</div>',
                                        unsafe_allow_html=True,
                                    )

                            else:
                                # Solo lectura o partido ya jugado
                                if gl_pred_prev is not None and gv_pred_prev is not None:
                                    pron_html = (
                                        f'<span class="badge-sin">Tu pronóstico: {gl_pred_prev} - {gv_pred_prev}</span> '
                                        + _badge_signo(signo_prev)
                                    )
                                else:
                                    pron_html = _badge_signo(signo_prev)

                                resultado_html = ""
                                if ya_jugado and signo_prev:
                                    pts = prev.get("puntos") if prev else None
                                    if pts == 3:
                                        resultado_html = (
                                            '<span class="badge-ok">✅ Resultado exacto</span>'
                                            '<span class="badge-pts">+3 pts</span>'
                                        )
                                    elif pts and pts >= 1:
                                        resultado_html = (
                                            '<span class="badge-ok">✅ Acertaste el signo</span>'
                                            '<span class="badge-pts">+1 pt</span>'
                                        )
                                    else:
                                        resultado_html = (
                                            f'<span class="badge-sin">❌ No acertaste · '
                                            f'Resultado: {_badge_signo(signo_real)}</span>'
                                        )
                                elif ya_jugado and not signo_prev:
                                    resultado_html = (
                                        f'<span class="badge-sin">Sin pronóstico · '
                                        f'Fue: {_badge_signo(signo_real)}</span>'
                                    )

                                st.markdown(
                                    f'<div class="card-footer">{pron_html}{resultado_html}</div>',
                                    unsafe_allow_html=True,
                                )


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
        "Cargá el resultado real de cada partido. Los pronósticos se comparan "
        "automáticamente: 1 punto si acertaron el signo (1/X/2), 3 puntos en "
        "total si acertaron el marcador exacto."
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
                    # ── Modo de pronóstico de la fecha completa ─────────────
                    modos_fecha = [_modo_partido(p) for p in partidos_fecha]
                    modo_predominante = max(set(modos_fecha), key=modos_fecha.count)
                    st.markdown(
                        f"**Modo de pronóstico de esta fecha:** {_badge_modo(modo_predominante)}",
                        unsafe_allow_html=True,
                    )
                    col_modo, col_aplicar = st.columns([2, 1])
                    with col_modo:
                        modo_elegido = st.radio(
                            "Elegí el modo para TODOS los partidos de esta fecha",
                            options=["exacto", "signo"],
                            format_func=lambda m: "🎯 Resultado exacto (hasta 3 pts)" if m == "exacto"
                                                   else "🔀 Solo 1 / X / 2 (hasta 1 pt)",
                            index=0 if modo_predominante == "exacto" else 1,
                            horizontal=True,
                            key=f"modo_fecha_{zona}_{fecha}",
                        )
                    with col_aplicar:
                        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                        if st.button(
                            "✅ Aplicar a toda la fecha",
                            key=f"aplicar_modo_{zona}_{fecha}",
                            use_container_width=True,
                        ):
                            try:
                                ids_fecha = [p["id"] for p in partidos_fecha]
                                sb.table("partidos").update(
                                    {"modo_pronostico": modo_elegido}
                                ).in_("id", ids_fecha).execute()
                                cargar_partidos.clear()
                                st.cache_data.clear()
                                st.toast(
                                    f"Fecha {fecha} configurada como "
                                    f"'{'Resultado exacto' if modo_elegido == 'exacto' else 'Solo 1/X/2'}'.",
                                    icon="✅",
                                )
                                st.rerun()
                            except Exception as e:
                                st.error(f"No se pudo actualizar el modo de la fecha: {e}")
                                st.exception(e)
                    st.markdown("<hr style='opacity:0.08;'>", unsafe_allow_html=True)

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
                                f"Resultado: `{gl_act}-{gv_act}` → **{signo_actual}** "
                                f"&nbsp; {_badge_modo(_modo_partido(p))}",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                f"**{local}** vs **{visitante}** — *Sin resultado* "
                                f"&nbsp; {_badge_modo(_modo_partido(p))}",
                                unsafe_allow_html=True,
                            )

                        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
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
                            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                            if st.button("💾 Guardar", key=f"admin_save_{p['id']}", use_container_width=True):
                                try:
                                    resp_update = (
                                        sb.table("partidos")
                                        .update({
                                            "goles_local":     int(gl_new),
                                            "goles_visitante": int(gv_new),
                                        })
                                        .eq("id", p["id"])
                                        .execute()
                                    )

                                    filas_afectadas = resp_update.data or []

                                    # Verificación real: traer el registro fresco (sin caché)
                                    # y comparar, porque .data puede venir vacío aunque el
                                    # UPDATE sí se haya aplicado en la base (gotcha conocido
                                    # de supabase-py con el header Prefer/representation).
                                    verificacion = (
                                        sb.table("partidos")
                                        .select("id, goles_local, goles_visitante")
                                        .eq("id", p["id"])
                                        .execute()
                                        .data
                                    )
                                    fila_real = verificacion[0] if verificacion else None
                                    realmente_actualizado = (
                                        fila_real is not None
                                        and fila_real.get("goles_local") == int(gl_new)
                                        and fila_real.get("goles_visitante") == int(gv_new)
                                    )

                                    if not filas_afectadas and not realmente_actualizado:
                                        st.error(
                                            "⚠️ Verifiqué con un SELECT fresco después del UPDATE y el "
                                            "valor en la base sigue siendo el viejo. El UPDATE NO se "
                                            "aplicó de verdad (no es solo un tema de respuesta vacía).\n\n"
                                            f"Fila encontrada en la base: `{fila_real}`\n\n"
                                            "Con service_role esto descarta RLS. Revisar: "
                                            "¿el 'id' que usa esta fila realmente existe en la tabla? "
                                            "¿hay un trigger en 'partidos' que revierte el cambio? "
                                            "¿la app está apuntando a otro proyecto/URL de Supabase "
                                            "distinto al que estás mirando en el dashboard?"
                                        )
                                        st.stop()
                                    elif not filas_afectadas and realmente_actualizado:
                                        st.info(
                                            "ℹ️ El UPDATE sí se aplicó en la base (confirmado con SELECT "
                                            "fresco), solo que la respuesta de Supabase no traía las filas "
                                            "en `.data`. Sigo con el guardado normalmente."
                                        )

                                    # Recalcular puntos de pronósticos de este partido
                                    if gl_new > gv_new:   signo_r = "1"
                                    elif gl_new == gv_new: signo_r = "X"
                                    else:                  signo_r = "2"

                                    prons = (
                                        sb.table("pronosticos")
                                        .select("id, signo_pred, goles_local_pred, goles_visitante_pred")
                                        .eq("partido_id", p["id"])
                                        .execute()
                                        .data or []
                                    )
                                    for pr in prons:
                                        gl_pr = pr.get("goles_local_pred")
                                        gv_pr = pr.get("goles_visitante_pred")
                                        if gl_pr is not None and gv_pr is not None and gl_pr == int(gl_new) and gv_pr == int(gv_new):
                                            pts = 3
                                        elif pr["signo_pred"] == signo_r:
                                            pts = 1
                                        else:
                                            pts = 0
                                        sb.table("pronosticos").update({"puntos": pts}).eq("id", pr["id"]).execute()

                                    cargar_partidos.clear()
                                    st.cache_data.clear()  # limpia también la cache de 01_Resultados.py (funciones cacheadas distintas por módulo)
                                    st.toast(f"Resultado guardado: {gl_new}-{gv_new} ({signo_r})", icon="✅")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al guardar: {e}")
                                    st.exception(e)
                        with c4:
                            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                            deshabilitado_reset = gl_act is None and gv_act is None
                            if st.button(
                                "🔄 Resetear partido",
                                key=f"admin_reset_{p['id']}",
                                use_container_width=True,
                                disabled=deshabilitado_reset,
                                help="Vuelve el partido a 'no disputado': borra el resultado y los puntos ya asignados.",
                            ):
                                try:
                                    sb.table("partidos").update({
                                        "goles_local":     None,
                                        "goles_visitante": None,
                                    }).eq("id", p["id"]).execute()

                                    # Verificación real con SELECT fresco
                                    verif_reset = (
                                        sb.table("partidos")
                                        .select("id, goles_local, goles_visitante")
                                        .eq("id", p["id"])
                                        .execute()
                                        .data
                                    )
                                    fila_reset = verif_reset[0] if verif_reset else None
                                    if not fila_reset or fila_reset.get("goles_local") is not None or fila_reset.get("goles_visitante") is not None:
                                        st.error(
                                            "⚠️ Se intentó resetear el partido pero el valor en la base "
                                            f"sigue siendo el viejo: `{fila_reset}`. Revisar RLS/triggers."
                                        )
                                        st.stop()

                                    # Borrar puntos ya asignados de los pronósticos de este partido
                                    # (vuelven a quedar "pendientes", como si el partido no se hubiera jugado)
                                    sb.table("pronosticos").update({"puntos": None}).eq("partido_id", p["id"]).execute()

                                    cargar_partidos.clear()
                                    st.cache_data.clear()
                                    st.toast(f"Partido {local} vs {visitante} reseteado a no disputado.", icon="🔄")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al resetear: {e}")
                                    st.exception(e)
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

                    # Verificación real con SELECT fresco (no confiar solo en
                    # que no haya habido excepción, por el mismo motivo que
                    # con los resultados: Supabase puede no tirar error aunque
                    # no borre nada, p.ej. por RLS o por FKs).
                    quedan = sb.table("jugadores").select("id").execute().data or []
                    if quedan:
                        st.error(
                            f"⚠️ Se ejecutó el borrado pero todavía quedan {len(quedan)} "
                            "jugadores en la base. Revisar RLS (policy de DELETE) o "
                            "restricciones de foreign key."
                        )
                    else:
                        st.session_state.confirmar_reset_all = False
                        st.toast("✅ Lista de participantes reseteada.", icon="🗑️")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error al resetear: {e}")
                    st.exception(e)
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

                                # Verificación real con SELECT fresco
                                sigue = (
                                    sb.table("jugadores")
                                    .select("id")
                                    .eq("id", j["id"])
                                    .execute()
                                    .data
                                )
                                if sigue:
                                    st.error(
                                        f"⚠️ Se ejecutó el borrado pero {j['nombre']} sigue "
                                        "en la base. Revisar RLS (policy de DELETE) o FKs."
                                    )
                                else:
                                    st.session_state.confirmar_eliminar_id = None
                                    st.toast(f"Jugador {j['nombre']} eliminado.", icon="🗑️")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error al eliminar: {e}")
                                st.exception(e)
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
