"""
03_Fixture.py — Prode Liga Profesional Argentina
Cambios:
  - Boleta usa marcador exacto (goles local / goles visitante); el signo
    (1/X/2) se deriva automáticamente a partir del marcador cargado.
  - Sistema de puntaje: 1 punto por acertar el signo (Local/Empate/Visitante),
    3 puntos en total si se acierta el marcador exacto.
  - Admin puede eliminar participantes con confirmación
  - Admin puede resetear (borrar) la lista completa de participantes
  - Resultado se guarda como goles y se refleja en 01_Resultados.py

IMPORTANTE: la tabla `pronosticos` en Supabase necesita las columnas
`goles_local_pred` (int, nullable) y `goles_visitante_pred` (int, nullable)
además de las existentes `signo_pred` y `puntos`. Si no existen, correr:

    ALTER TABLE pronosticos ADD COLUMN goles_local_pred integer;
    ALTER TABLE pronosticos ADD COLUMN goles_visitante_pred integer;
"""
import base64
import hashlib
import json
import os
import secrets
import string
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st
from database import conectar
from escudos_map import url_escudo


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

    [data-testid="stAppViewContainer"] {
        background-image:
            linear-gradient(160deg, rgba(9,12,22,0.87) 0%, rgba(13,17,32,0.84) 45%, rgba(7,9,16,0.90) 100%),
            url('__FONDO_AFA2026__');
        background-size: cover, cover;
        background-position: center, center;
        background-repeat: no-repeat, no-repeat;
        background-attachment: fixed, fixed;
        background-color: #0b0f19;
    }
    [data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stVerticalBlock"] { position: relative; z-index: 1; }

    h1, h2, h3 { font-family: 'Bebas Neue', sans-serif !important; letter-spacing: 1px; }

    /* ═══════════ TABS DE ZONA — estilo glass / blur 2026 ═══════════ */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        display: inline-flex;
        gap: 6px;
        background: rgba(255,255,255,0.045);
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 999px;
        padding: 6px;
        backdrop-filter: blur(22px) saturate(180%);
        -webkit-backdrop-filter: blur(22px) saturate(180%);
        box-shadow: 0 8px 32px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.06);
        margin-bottom: 18px;
    }
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }
    [data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }
    [data-testid="stTabs"] button[data-baseweb="tab"],
    [data-testid="stTabs"] [data-testid="stTab"] {
        font-family: 'Bebas Neue', sans-serif !important;
        font-size: 1.05rem !important;
        letter-spacing: 0.06em !important;
        color: rgba(255,255,255,0.55) !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 999px !important;
        padding: 9px 24px !important;
        margin: 0 !important;
        transition: all .22s ease !important;
    }
    [data-testid="stTabs"] button[data-baseweb="tab"]:hover,
    [data-testid="stTabs"] [data-testid="stTab"]:hover {
        color: #fff !important;
        background: rgba(255,255,255,0.07) !important;
    }
    [data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"],
    [data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"] {
        color: #e8c96b !important;
        background: linear-gradient(135deg, rgba(232,201,107,0.28) 0%, rgba(232,201,107,0.08) 100%) !important;
        border: 1px solid rgba(232,201,107,0.45) !important;
        box-shadow: 0 4px 18px rgba(232,201,107,0.22), inset 0 1px 0 rgba(255,255,255,0.12) !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab-panel"] { padding-top: 4px; }

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
    """.replace("__FONDO_AFA2026__", _FONDO_AFA2026),
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


TZ_ARG = ZoneInfo("America/Argentina/Buenos_Aires")
MINUTOS_CIERRE_ANTES = 5


def _horario_confirmado(p) -> bool:
    """True si el partido tiene fecha Y hora cargadas (confirmadas)."""
    return bool(p.get("fecha_partido")) and bool(p.get("hora"))


# Formatos de fecha y hora aceptados, para bancar cómo sea que esté
# cargado el dato en la base (texto libre, date/time de Postgres, etc.)
_FORMATOS_FECHA = [
    "%Y-%m-%d",   # 2026-07-25 (ISO, lo que devuelve Postgres normalmente)
    "%d/%m/%Y",   # 25/07/2026 (formato argentino)
    "%d-%m-%Y",   # 25-07-2026
    "%Y/%m/%d",   # 2026/07/25
    "%d/%m/%y",   # 25/07/26
]
_FORMATOS_HORA = [
    "%H:%M:%S",   # 20:00:00 (time de Postgres)
    "%H:%M",      # 20:00
    "%H.%M",      # 20.00
    "%Hhs",       # 20hs
    "%H",         # 20
]


def _parsear_fecha(fecha_raw):
    fecha_str = str(fecha_raw).strip()
    # Si viene como timestamp ISO ("2026-07-25T00:00:00" o con espacio),
    # nos quedamos solo con la parte de fecha.
    fecha_str = fecha_str.split("T")[0].split(" ")[0]
    for fmt in _FORMATOS_FECHA:
        try:
            return datetime.strptime(fecha_str, fmt).date()
        except ValueError:
            continue
    return None


def _parsear_hora(hora_raw):
    hora_str = str(hora_raw).strip()
    for fmt in _FORMATOS_HORA:
        try:
            return datetime.strptime(hora_str, fmt).time()
        except ValueError:
            continue
    return None


def _momento_cierre(p):
    """
    Devuelve (datetime_cierre, error) donde datetime_cierre es el momento
    (con tz Argentina) a partir del cual se cierra el pronóstico para ese
    partido (kickoff - MINUTOS_CIERRE_ANTES minutos), o None si no se pudo
    calcular. `error` trae un mensaje si fecha/hora estaban cargadas pero no
    se pudieron interpretar (para poder mostrarlo y detectar el problema,
    en vez de fallar en silencio).
    """
    if not _horario_confirmado(p):
        return None, None

    fecha_obj = _parsear_fecha(p["fecha_partido"])
    hora_obj = _parsear_hora(p["hora"])

    if fecha_obj is None or hora_obj is None:
        return None, (
            f"No se pudo interpretar fecha/hora del partido "
            f"(fecha_partido={p.get('fecha_partido')!r}, hora={p.get('hora')!r})."
        )

    kickoff = datetime.combine(fecha_obj, hora_obj, tzinfo=TZ_ARG)
    return kickoff - timedelta(minutes=MINUTOS_CIERRE_ANTES), None


def _pronostico_cerrado(p) -> bool:
    """
    True si, con fecha/hora confirmada, ya estamos dentro de la ventana de
    cierre (a partir de MINUTOS_CIERRE_ANTES minutos antes del partido, hora
    de Argentina). Si no hay fecha/hora confirmada, nunca se cierra por esta
    vía (solo se cierra cuando el partido ya fue jugado).

    Si hay fecha/hora cargadas pero no se pudieron interpretar, se cierra
    igual por seguridad (mejor bloquear de más que dejar pronosticar un
    partido que ya empezó por un problema de formato).
    """
    cierre, error = _momento_cierre(p)
    if cierre is None:
        return error is not None  # confirmado pero ilegible -> cerrar por seguridad
    ahora = datetime.now(TZ_ARG)
    return ahora >= cierre


AUTO_REFRESH_MAX_SEGUNDOS = 20  # tope de espera entre chequeos automáticos


def _segundos_hasta_proximo_refresco(partidos):
    """
    Calcula cuántos segundos hay que esperar antes de refrescar la página
    sola, para que apenas se cumpla el horario de cierre de algún partido
    (fecha/hora confirmada, todavía no jugado, todavía no cerrado) el
    pronóstico se bloquee sin que el usuario tenga que hacer nada.

    Devuelve None si no hay ningún cierre pendiente (nada que esperar).
    """
    ahora = datetime.now(TZ_ARG)
    proximos_cierres = []
    for p in partidos:
        ya_jugado_p = p.get("goles_local") is not None and p.get("goles_visitante") is not None
        if ya_jugado_p:
            continue
        cierre, _error = _momento_cierre(p)
        if cierre is not None and cierre > ahora:
            proximos_cierres.append(cierre)

    if not proximos_cierres:
        return None

    segundos_hasta_cierre = (min(proximos_cierres) - ahora).total_seconds()
    # Esperamos exactamente hasta el próximo cierre si falta poco; si falta
    # mucho, esperamos como máximo AUTO_REFRESH_MAX_SEGUNDOS y volvemos a
    # chequear (así no hace falta un timer exacto por cada partido).
    return max(1.0, min(segundos_hasta_cierre + 1, AUTO_REFRESH_MAX_SEGUNDOS))


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


def cargar_pronosticos_de(j_id):
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
            return True
        except Exception as e:
            st.error(f"No se pudo guardar: {e}")
            st.exception(e)
            return False

    def resetear_pronostico(partido_id):
        """
        Borra el pronóstico cargado para ese partido, para que el jugador
        pueda volver a cargarlo desde cero. Solo tiene sentido para partidos
        que todavía no se jugaron.

        Se borra la fila entera (en vez de poner sus columnas en null) porque
        `goles_local_pred` / `goles_visitante_pred` tienen restricción NOT
        NULL en la base.
        """
        try:
            existente = pron.get(partido_id)
            if not existente:
                return True  # no había nada cargado, no hay nada que resetear

            resp = sb.table("pronosticos").delete().eq("id", existente["id"]).execute()

            # Verificación real con SELECT fresco, por si la respuesta de
            # Supabase viene vacía en .data aunque el DELETE sí se haya
            # aplicado (mismo gotcha que en el resto del archivo).
            sigue = (
                sb.table("pronosticos")
                .select("id")
                .eq("id", existente["id"])
                .execute()
                .data
            )
            if sigue:
                st.error(
                    "⚠️ Se ejecutó el borrado pero el pronóstico sigue en la base. "
                    "Revisar RLS (policy de DELETE)."
                )
                return False

            st.toast("Pronóstico reseteado.", icon="🔄")
            return True
        except Exception as e:
            st.error(f"No se pudo resetear: {e}")
            st.exception(e)
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

                        # ── Predicción de marcador exacto ────────────────────
                        gl_pred_prev = prev.get("goles_local_pred") if prev else None
                        gv_pred_prev = prev.get("goles_visitante_pred") if prev else None

                        cerrado_por_horario = (not ya_jugado) and _pronostico_cerrado(p)

                        if editable and not ya_jugado and not cerrado_por_horario:
                            col_gl, col_gv, col_btn, col_reset, col_estado = st.columns([1, 1, 1.3, 1.3, 1.6])
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
                                ):
                                    if guardar_pronostico(p["id"], int(gl_new_pred), int(gv_new_pred)):
                                        st.rerun()
                            with col_reset:
                                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                                if st.button(
                                    "🔄 Resetear",
                                    key=f"resetear_{key_ns}_{jugador_objetivo_id}_{p['id']}",
                                    use_container_width=True,
                                    disabled=(gl_pred_prev is None and gv_pred_prev is None),
                                    help="Borra el pronóstico cargado para este partido.",
                                ):
                                    if resetear_pronostico(p["id"]):
                                        st.rerun()
                            with col_estado:
                                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                                st.markdown(_badge_signo(signo_prev), unsafe_allow_html=True)

                        else:
                            # Solo lectura: partido ya jugado, o cerrado por
                            # horario (fecha/hora confirmada y dentro de la
                            # ventana de cierre), o boleta no editable.
                            col_pron, col_pts = st.columns([3, 2])
                            with col_pron:
                                if gl_pred_prev is not None and gv_pred_prev is not None:
                                    st.markdown(
                                        f'<span class="badge-sin">Tu pronóstico: {gl_pred_prev} - {gv_pred_prev}</span> '
                                        + _badge_signo(signo_prev),
                                        unsafe_allow_html=True,
                                    )
                                else:
                                    st.markdown(_badge_signo(signo_prev), unsafe_allow_html=True)
                                if cerrado_por_horario:
                                    st.markdown(
                                        '<span class="badge-admin">🔒 Pronósticos cerrados '
                                        f'(desde {MINUTOS_CIERRE_ANTES} min. antes del partido)</span>',
                                        unsafe_allow_html=True,
                                    )
                                if st.session_state.es_admin:
                                    _cierre_dbg, _error_dbg = _momento_cierre(p)
                                    if _error_dbg:
                                        st.caption(f"⚠️ {_error_dbg}")
                                    elif _cierre_dbg is not None:
                                        st.caption(
                                            f"🕒 Cierre de pronóstico: {_cierre_dbg.strftime('%d/%m/%Y %H:%M')} (ARG) · "
                                            f"Ahora: {datetime.now(TZ_ARG).strftime('%d/%m/%Y %H:%M')} (ARG)"
                                        )
                            with col_pts:
                                if ya_jugado and signo_prev:
                                    pts = prev.get("puntos") if prev else None
                                    if pts == 3:
                                        st.markdown(
                                            '<span class="badge-ok">✅ Resultado exacto</span>'
                                            '<span class="badge-pts">+3 pts</span>',
                                            unsafe_allow_html=True,
                                        )
                                    elif pts and pts >= 1:
                                        st.markdown(
                                            '<span class="badge-ok">✅ Acertaste el signo</span>'
                                            '<span class="badge-pts">+1 pt</span>',
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
    # Auto-refresh: si hay algún partido con horario confirmado a punto de
    # cerrarse (o de cerrarse más adelante), esperamos y refrescamos solos
    # para que el pronóstico se bloquee apenas llegue el momento, sin que
    # el jugador tenga que recargar la página a mano.
    _espera = _segundos_hasta_proximo_refresco(partidos_db)
    if _espera is not None:
        time.sleep(_espera)
        st.rerun()
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
