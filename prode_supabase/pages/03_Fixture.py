"""
03_Fixture.py

Fixture digital del Clausura 2026 para completar el prode partido a partido
(Zona A, Zona B e Interzonal), sobre el esquema de schema_prode.sql
(jugadores / partidos / pronosticos).

Requiere haber corrido migracion_login_jugadores.sql (agrega username y
password_hash a la tabla "jugadores").
"""
import hashlib

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

    .fila-partido {
        display: flex; align-items: center; gap: 10px;
        background: rgba(20,30,50,0.55);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 10px 16px;
        margin-bottom: 8px;
    }
    .fila-equipo {
        display: flex; align-items: center; gap: 8px;
        flex: 1; font-size: 0.9rem; font-family: 'Inter', sans-serif;
    }
    .fila-equipo.derecha { justify-content: flex-end; text-align: right; }
    .fila-escudo { width: 26px; height: 26px; object-fit: contain; }
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
# LOGIN / REGISTRO (tabla "jugadores": username + password_hash)
# ══════════════════════════════════════════════════════════════════════════
def _hash_pwd(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


if "jugador_id" not in st.session_state:
    st.session_state.jugador_id = None
if "jugador_nombre" not in st.session_state:
    st.session_state.jugador_nombre = None


def _cerrar_sesion():
    st.session_state.jugador_id = None
    st.session_state.jugador_nombre = None
    st.rerun()


with st.sidebar:
    st.markdown("### 🔐 Mi cuenta")
    if st.session_state.jugador_id:
        st.success(f"Sesión iniciada como **{st.session_state.jugador_nombre}**")
        if st.button("Cerrar sesión", use_container_width=True):
            _cerrar_sesion()
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

st.markdown('<div class="titulo-pagina">📝 FIXTURE DIGITAL — MI BOLETA</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitulo-pagina">Completá tu pronóstico partido a partido. '
    'Zona A, Zona B e Interzonal, Clausura 2026.</div>',
    unsafe_allow_html=True,
)

if not st.session_state.jugador_id:
    st.info("🔒 Iniciá sesión o creá tu cuenta en la barra lateral para poder cargar tu boleta.")
    st.stop()

jugador_id = st.session_state.jugador_id


# ══════════════════════════════════════════════════════════════════════════
# DATOS: partidos + mis pronósticos ya guardados
# ══════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=30)
def cargar_partidos():
    return sb.table("partidos").select("*").execute().data


def cargar_mis_pronosticos(j_id):
    res = (
        sb.table("pronosticos")
        .select("id, partido_id, goles_local_pred, goles_visitante_pred, puntos")
        .eq("jugador_id", j_id)
        .execute()
    )
    return {row["partido_id"]: row for row in (res.data or [])}


try:
    partidos_db = cargar_partidos()
except Exception as e:
    st.error(f"No se pudieron cargar los partidos: {e}")
    st.stop()

mis_pron = cargar_mis_pronosticos(jugador_id)

if not partidos_db:
    st.info("Todavía no hay partidos cargados.")
    st.stop()

# Agrupar por zona -> fecha_numero
por_zona = {}
for p in partidos_db:
    por_zona.setdefault(p["zona"], {}).setdefault(p["fecha_numero"], []).append(p)

zonas_orden = sorted(
    por_zona.keys(), key=lambda z: (0 if z == "A" else 1 if z == "B" else 2, z)
)
etiquetas_zona = {z: ("Interzonal" if z == "Interzonal" else f"Zona {z}") for z in zonas_orden}

tabs = st.tabs([etiquetas_zona[z] for z in zonas_orden])


def guardar_pronostico(partido_id, gl, gv):
    try:
        existente = mis_pron.get(partido_id)
        payload = {"goles_local_pred": int(gl), "goles_visitante_pred": int(gv)}
        if existente:
            sb.table("pronosticos").update(payload).eq("id", existente["id"]).execute()
        else:
            sb.table("pronosticos").insert({
                "jugador_id": jugador_id,
                "partido_id": partido_id,
                **payload,
            }).execute()
        st.toast(f"Pronóstico guardado: {gl}-{gv}", icon="✅")
        return True
    except Exception as e:
        st.error(f"No se pudo guardar: {e}")
        return False


for tab, zona in zip(tabs, zonas_orden):
    with tab:
        fechas = sorted(por_zona[zona].keys(), key=int)
        for fecha in fechas:
            partidos_fecha = sorted(
                por_zona[zona][fecha],
                key=lambda p: (p.get("fecha_partido") or "9999-99-99", p.get("hora") or "99:99"),
            )
            cargados = sum(1 for p in partidos_fecha if p["id"] in mis_pron)
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

                    prev = mis_pron.get(p["id"])
                    key_gl = f"gl_{jugador_id}_{p['id']}"
                    key_gv = f"gv_{jugador_id}_{p['id']}"

                    if ya_jugado:
                        with col_gl:
                            st.markdown(f'<div class="score-real">{gl_real}</div>', unsafe_allow_html=True)
                        with col_sep:
                            st.markdown('<div class="score-real">-</div>', unsafe_allow_html=True)
                        with col_gv:
                            st.markdown(f'<div class="score-real">{gv_real}</div>', unsafe_allow_html=True)
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
                                    f'<span class="badge-jugado">Tu pron.: {pron_txt}</span>'
                                    + (f'<span class="badge-puntos">+{pts} pts</span>' if pts is not None else ""),
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(
                                    '<span class="badge-jugado" style="background:rgba(148,163,184,0.15);'
                                    'color:#94a3b8;">Sin pronóstico cargado</span>',
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
                                key=f"save_{jugador_id}_{p['id']}",
                                use_container_width=True,
                                disabled=bool(ya_guardado),
                            ):
                                if guardar_pronostico(p["id"], gl_val, gv_val):
                                    st.rerun()

                    st.markdown("<hr style='opacity:0.08;margin:6px 0;'>", unsafe_allow_html=True)
