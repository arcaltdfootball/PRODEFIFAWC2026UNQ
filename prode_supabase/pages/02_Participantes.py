import json
import os
import secrets
import string
import hashlib
import base64
import streamlit as st
from database import conectar
from scoring import calcular_puntos

st.set_page_config(
    page_title="Participantes",
    layout="centered"
)

# ── CSS principal ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">

    <style>
    body { font-family: 'DM Sans', sans-serif; color: #f1f5f9; }

    [data-testid="stApp"] {
        background-image: url('https://raw.githubusercontent.com/arcaltdfootball/PRODEFIFAWC2026UNQ/main/prode_supabase/FIFAWorldbakcgound.jpg');
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
        background: rgba(11,15,25,0.78);
        z-index: 0;
        pointer-events: none;
    }
    [data-testid="stVerticalBlock"] { position: relative; z-index: 1; }

    html, body, [class*="css"], .stMarkdown p {
        font-family: 'DM Sans', sans-serif !important;
    }
    h1, h2, h3 {
        font-family: 'Bebas Neue', sans-serif !important;
        letter-spacing: 1px;
    }

    .titulo-pagina {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 42px;
        color: #e8c96b;
        text-align: center;
        letter-spacing: 3px;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.6);
        margin-bottom: 24px;
    }

    .part-number {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 28px;
        color: rgba(232,201,107,0.35);
        min-width: 32px;
        text-align: center;
        line-height: 1;
    }

    .part-puntos-big {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 42px;
        color: #e8c96b;
        line-height: 1;
        text-shadow: 0 2px 10px rgba(232,201,107,0.4);
    }

    .part-puntos-label {
        font-size: 10px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-family: 'DM Sans', sans-serif;
    }

    .card-partido {
        background: rgba(28, 36, 60, 0.96);
        border-radius: 14px;
        padding: 18px 20px 18px 20px;
        margin: 12px 0 2px 0;
        box-shadow: 0 6px 24px rgba(0,0,0,0.35);
        border: 1px solid rgba(232,201,107,0.18);
        display: flex;
        flex-direction: column;
        gap: 4px;
        position: relative;
    }
    .card-partido-meta {
        font-size: 11px;
        color: #94a3b8;
        text-align: center;
        letter-spacing: 0.5px;
        margin-bottom: 10px;
    }
    .card-partido-vs-row {
        display: flex;
        align-items: center;
        justify-content: space-around;
        gap: 8px;
        margin-bottom: 0px;
    }
    .card-equipo {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        min-width: 90px;
    }
    .card-nombre-equipo {
        font-family: 'DM Sans', sans-serif;
        font-size: 13px;
        font-weight: 600;
        color: #f1f5f9;
        text-align: center;
        letter-spacing: 0.3px;
    }
    .card-vs {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 32px;
        color: #e8c96b;
        text-shadow: 0 2px 8px rgba(232,201,107,0.4);
        letter-spacing: 2px;
    }
    /* Recuadros de marcador */
    .score-box-wrap {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        margin: 14px 0 6px 0;
    }
    .score-box {
        width: 62px;
        height: 62px;
        border: 2px dashed rgba(232,201,107,0.55);
        border-radius: 12px;
        background: rgba(232,201,107,0.06);
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Bebas Neue', sans-serif;
        font-size: 36px;
        color: #e8c96b;
        text-shadow: 0 2px 8px rgba(232,201,107,0.3);
    }
    .score-box.empty {
        color: rgba(232,201,107,0.2);
        border-color: rgba(255,255,255,0.12);
        background: rgba(255,255,255,0.02);
    }
    .score-dash {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 28px;
        color: rgba(255,255,255,0.3);
    }
    .score-label {
        font-size: 10px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
        text-align: center;
        margin-top: 2px;
        font-family: 'DM Sans', sans-serif;
    }
    /* Ocultar label de number_input de score */
    .score-input-hide label { display: none !important; }
    .score-input-hide [data-testid="stNumberInput"] input {
        background: transparent !important;
        border: 2px dashed rgba(232,201,107,0.55) !important;
        border-radius: 12px !important;
        color: #e8c96b !important;
        font-family: 'Bebas Neue', sans-serif !important;
        font-size: 28px !important;
        text-align: center !important;
        height: 58px !important;
        padding: 0 !important;
    }
    .score-input-hide [data-testid="stNumberInput"] input:focus {
        border-color: #e8c96b !important;
        box-shadow: 0 0 0 2px rgba(232,201,107,0.2) !important;
    }

    .escudo-img {
        width: 52px; height: 52px; object-fit: contain;
        border-radius: 10px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.4);
        background: rgba(255,255,255,0.06);
        border: 2px solid rgba(255,255,255,0.12);
        padding: 3px;
    }

    .part-header {
        display: flex;
        align-items: center;
        background: rgba(20, 28, 50, 0.92);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        padding: 20px 24px;
        border-radius: 18px;
        margin-top: 10px;
        border: 1px solid rgba(232,201,107,0.2);
        gap: 20px;
    }

    .header-puntos-block {
        margin-left: auto;
        text-align: center;
        background: rgba(232,201,107,0.08);
        border: 1px solid rgba(232,201,107,0.2);
        border-radius: 14px;
        padding: 10px 20px;
    }

    .stButton > button {
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }

    .badge-admin {
        display: inline-block;
        background: rgba(34,197,94,0.18);
        border: 1px solid rgba(34,197,94,0.4);
        color: #4ade80;
        border-radius: 20px;
        padding: 3px 14px;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 18px;
    }
    .badge-participante {
        display: inline-block;
        background: rgba(59,130,246,0.18);
        border: 1px solid rgba(59,130,246,0.4);
        color: #60a5fa;
        border-radius: 20px;
        padding: 3px 14px;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 18px;
    }
    .badge-visitante {
        display: inline-block;
        background: rgba(100,116,139,0.18);
        border: 1px solid rgba(100,116,139,0.3);
        color: #94a3b8;
        border-radius: 20px;
        padding: 3px 14px;
        font-size: 12px;
        margin-bottom: 18px;
    }
    .readonly-notice {
        background: rgba(232,201,107,0.07);
        border: 1px solid rgba(232,201,107,0.15);
        border-radius: 10px;
        padding: 10px 16px;
        font-size: 12px;
        color: #94a3b8;
        text-align: center;
        margin-bottom: 16px;
    }

    .dots-row-clickable {
        display: flex; justify-content: center; gap: 6px; align-items: center;
        margin: 4px 0 2px 0;
    }

    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True
)

# ── Conexión Supabase ──────────────────────────────────────────────────────────
try:
    sb = conectar()
except Exception as e:
    st.error(f"Error al conectar: {e}")
    st.stop()

st.markdown('<div class="titulo-pagina">ADMINISTRACIÓN DE PARTICIPANTES</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ESCUDOS — igual que en 01_Resultados.py
# ══════════════════════════════════════════════════════════════════════════════
ALIAS_ESCUDOS = {
    "Boca": "Boca Juniors",
    "River": "River Plate",
    "Racing": "Racing Club",
    "Independiente": "Independiente",
    "San Lorenzo": "San Lorenzo",
    "Huracán": "Huracán",
    "Vélez": "Vélez Sarsfield",
    "Estudiantes": "Estudiantes (LP)",
    "Gimnasia": "Gimnasia y Esgrima (LP)",
    "Newell's": "Newell's Old Boys",
    "Rosario Central": "Rosario Central",
    "Talleres": "Talleres (Córdoba)",
    "Belgrano": "Belgrano (Córdoba)",
    "Instituto": "Instituto (Córdoba)",
    "Argentinos": "Argentinos Juniors",
    "Platense": "Platense",
    "Banfield": "Banfield",
    "Lanús": "Lanús",
    "Tigre": "Tigre",
    "Barracas Central": "Barracas Central",
    "Central Córdoba": "Central Córdoba (SdE)",
    "Independiente Rivadavia": "Independiente Rivadavia",
    "Gimnasia (Mza.)": "Gimnasia y Esgrima (Mza)",
    "Deportivo Riestra": "Deportivo Riestra",
    "Unión": "Unión (Santa Fe)",
    "Sarmiento": "Sarmiento (Junín)",
    "Atlético Tucumán": "Atlético Tucumán",
    "Aldosivi": "Aldosivi",
    "Estudiantes (Río Cuarto)": "Estudiantes (Río Cuarto)",
    "Defensa y Justicia": "Defensa y Justicia",
}

_RUTAS_ESCUDOS_JSON = [
    "escudos.json",
    os.path.join(os.path.dirname(__file__), "escudos.json"),
    os.path.join(os.path.dirname(__file__), "..", "escudos.json"),
]


@st.cache_data(ttl=3600)
def cargar_escudos_json():
    for ruta in _RUTAS_ESCUDOS_JSON:
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return {}


def get_escudo_url(nombre_equipo: str) -> str | None:
    """Devuelve la URL del escudo para un nombre de equipo (ej. 'Boca', 'River')."""
    escudos = cargar_escudos_json()
    if not escudos:
        return None
    nombre_lindo = ALIAS_ESCUDOS.get(nombre_equipo, nombre_equipo)
    dato = escudos.get(nombre_lindo)
    if isinstance(dato, dict):
        return dato.get("url")
    if isinstance(dato, str):
        return dato
    return None


def get_escudo_img(nombre_equipo: str, size: int = 52) -> str:
    """Devuelve HTML con el escudo del equipo (img o placeholder)."""
    url = get_escudo_url(nombre_equipo)
    if url:
        return f'<img src="{url}" class="escudo-img" width="{size}" height="{size}">'
    inicial = nombre_equipo[0].upper() if nombre_equipo else "?"
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:10px;'
        f'background:#1e2840;color:#e8c96b;display:inline-flex;'
        f'align-items:center;justify-content:center;'
        f"font-family:'Bebas Neue';font-size:{size // 2}px;"
        f'border:2px solid rgba(255,255,255,0.12);">{inicial}</div>'
    )


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS DE CONTRASEÑA
# ══════════════════════════════════════════════════════════════════════════════
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "aleotero")


def _hash_pwd(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


def generar_password(largo: int = 8) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(largo))


def generar_username(nombre: str) -> str:
    base = nombre.strip().lower().replace(" ", "_")
    base = "".join(c for c in base if c.isalnum() or c == "_")
    return base or "user"


# ══════════════════════════════════════════════════════════════════════════════
# CANDADO GLOBAL DE ACCESO
# ══════════════════════════════════════════════════════════════════════════════
def obtener_acceso_bloqueado() -> bool:
    try:
        res = sb.table("configuracion_app").select("acceso_bloqueado").eq("id", 1).execute()
        if res.data:
            return bool(res.data[0].get("acceso_bloqueado", False))
        try:
            sb.table("configuracion_app").upsert({"id": 1, "acceso_bloqueado": False}).execute()
        except Exception:
            pass
        return False
    except Exception:
        return False


def set_acceso_bloqueado(valor: bool) -> bool:
    try:
        sb.table("configuracion_app").upsert({"id": 1, "acceso_bloqueado": valor}).execute()
        return True
    except Exception as ex:
        st.error(
            "⚠️ No se pudo guardar el estado del candado. Es probable que falte crear la tabla "
            "'configuracion_app' en Supabase (o los permisos RLS de insert/update). "
            "Ejecutá esto en el SQL Editor de Supabase:\n\n"
            "```sql\n"
            "create table if not exists configuracion_app (\n"
            "    id int primary key,\n"
            "    acceso_bloqueado boolean not null default false\n"
            ");\n"
            "insert into configuracion_app (id, acceso_bloqueado)\n"
            "values (1, false) on conflict (id) do nothing;\n\n"
            "alter table configuracion_app enable row level security;\n"
            "create policy \"permitir todo\" on configuracion_app\n"
            "    for all using (true) with check (true);\n"
            "```\n\n"
            "Detalle técnico: " + str(ex)
        )
        return False


# ══════════════════════════════════════════════════════════════════════════════
# ESTADO DE SESIÓN
# ══════════════════════════════════════════════════════════════════════════════
if "es_admin" not in st.session_state:
    st.session_state.es_admin = False
if "participante_logueado_id" not in st.session_state:
    st.session_state.participante_logueado_id = None
if "participante_logueado_nom" not in st.session_state:
    st.session_state.participante_logueado_nom = None

es_admin = st.session_state.es_admin
part_logueado_id  = st.session_state.participante_logueado_id
part_logueado_nom = st.session_state.participante_logueado_nom

acceso_bloqueado = obtener_acceso_bloqueado()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR DE LOGIN
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("---")
    sesion_activa = es_admin or part_logueado_id is not None

    if not sesion_activa:
        st.markdown(
            '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:18px;'
            'color:#e8c96b;letter-spacing:2px;margin-bottom:8px;">🔐 INICIAR SESIÓN</div>',
            unsafe_allow_html=True
        )
        modo_login = st.radio("Ingresar como:", ["Participante", "Admin"], key="modo_login", horizontal=True)

        if modo_login == "Participante" and acceso_bloqueado:
            st.warning("🔒 El acceso de participantes está bloqueado temporalmente por el administrador.")

        user_input = st.text_input("Usuario", key="sidebar_user", placeholder="Tu usuario...")
        pwd_input  = st.text_input("Contraseña", type="password", key="sidebar_pwd", placeholder="Contraseña...")

        if st.button("Ingresar", use_container_width=True, key="btn_login"):
            if modo_login == "Admin":
                if user_input.strip() == "admin" and pwd_input == ADMIN_PASSWORD:
                    st.session_state.es_admin = True
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
            elif acceso_bloqueado:
                st.error("🔒 El acceso está bloqueado temporalmente. Esperá a que el administrador lo habilite.")
            else:
                try:
                    res = (
                        sb.table("participantes")
                        .select("id, nombre, username, password_hash")
                        .eq("username", user_input.strip().lower())
                        .execute()
                    )
                    if res.data:
                        row = res.data[0]
                        if row.get("password_hash") == _hash_pwd(pwd_input):
                            st.session_state.participante_logueado_id  = row["id"]
                            st.session_state.participante_logueado_nom = row["nombre"]
                            st.rerun()
                        else:
                            st.error("Contraseña incorrecta.")
                    else:
                        st.error("Usuario no encontrado.")
                except Exception as ex:
                    st.error("Error al autenticar: " + str(ex))

    elif es_admin:
        st.markdown(
            '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:16px;'
            'color:#4ade80;letter-spacing:2px;">✅ ADMIN ACTIVO</div>',
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)

        if acceso_bloqueado:
            st.markdown(
                '<div style="text-align:center;margin-bottom:6px;">'
                '<span style="background:rgba(239,68,68,0.18);color:#f87171;'
                'border:1px solid rgba(239,68,68,0.4);border-radius:20px;'
                'padding:3px 14px;font-size:12px;font-weight:600;">'
                '🔒 Acceso bloqueado</span></div>',
                unsafe_allow_html=True
            )
            if st.button("🔓 Habilitar ingreso de participantes", use_container_width=True, key="btn_toggle_lock"):
                if set_acceso_bloqueado(False):
                    st.toast("🔓 Ingreso de participantes habilitado.", icon="🔓")
                    st.rerun()
        else:
            st.markdown(
                '<div style="text-align:center;margin-bottom:6px;">'
                '<span style="background:rgba(34,197,94,0.18);color:#4ade80;'
                'border:1px solid rgba(34,197,94,0.4);border-radius:20px;'
                'padding:3px 14px;font-size:12px;font-weight:600;">'
                '🔓 Acceso habilitado</span></div>',
                unsafe_allow_html=True
            )
            if st.button("🔒 Bloquear acceso de participantes", use_container_width=True, key="btn_toggle_lock"):
                if set_acceso_bloqueado(True):
                    st.toast("🔒 Ingreso de participantes bloqueado.", icon="🔒")
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Cerrar sesión", use_container_width=True, key="btn_logout"):
            st.session_state.es_admin = False
            st.rerun()

    else:
        st.markdown(
            '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:15px;'
            'color:#60a5fa;letter-spacing:2px;">✅ ' + (part_logueado_nom or "").upper() + '</div>',
            unsafe_allow_html=True
        )
        if acceso_bloqueado:
            st.warning("🔒 El administrador bloqueó temporalmente la edición de boletas.")
        else:
            st.caption("Podés editar solo tu boleta.")
        if st.button("🚪 Cerrar sesión", use_container_width=True, key="btn_logout_part"):
            st.session_state.participante_logueado_id  = None
            st.session_state.participante_logueado_nom = None
            st.rerun()

# Re-leer estado tras posibles cambios
es_admin          = st.session_state.es_admin
part_logueado_id  = st.session_state.participante_logueado_id
part_logueado_nom = st.session_state.participante_logueado_nom

# Badge de modo
if es_admin:
    st.markdown(
        '<div style="text-align:center;margin-bottom:10px;">'
        '<span class="badge-admin">⚡ Modo Administrador — edición habilitada</span></div>',
        unsafe_allow_html=True
    )
elif part_logueado_id:
    st.markdown(
        '<div style="text-align:center;margin-bottom:10px;">'
        '<span class="badge-participante">🙋 ' + part_logueado_nom + ' — solo tu boleta es editable</span>'
        '</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        '<div class="readonly-notice">'
        '👁️ Modo visitante — podés ver los pronósticos, pero iniciá sesión para modificar los tuyos'
        '</div>',
        unsafe_allow_html=True
    )

# ══════════════════════════════════════════════════════════════════════════════
# INDICADOR + CONTROL DEL CANDADO GLOBAL
# ══════════════════════════════════════════════════════════════════════════════
if acceso_bloqueado:
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, rgba(239,68,68,0.22) 0%, rgba(153,27,27,0.28) 100%);
            border: 2px solid #ef4444;
            border-radius: 16px;
            padding: 16px 20px;
            margin: 6px 0 16px 0;
            text-align: center;
            box-shadow: 0 0 22px rgba(239,68,68,0.35);
        ">
            <div style="font-family:'Bebas Neue',sans-serif;font-size:24px;letter-spacing:2px;
                color:#fca5a5;line-height:1.1;">
                🔴 ACCESO BLOQUEADO
            </div>
            <div style="font-size:12px;color:#fecaca;margin-top:4px;">
                Los participantes NO pueden ingresar ni editar sus boletas.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, rgba(34,197,94,0.18) 0%, rgba(21,128,61,0.22) 100%);
            border: 2px solid #22c55e;
            border-radius: 16px;
            padding: 16px 20px;
            margin: 6px 0 16px 0;
            text-align: center;
            box-shadow: 0 0 22px rgba(34,197,94,0.25);
        ">
            <div style="font-family:'Bebas Neue',sans-serif;font-size:24px;letter-spacing:2px;
                color:#86efac;line-height:1.1;">
                🟢 ACCESO HABILITADO
            </div>
            <div style="font-size:12px;color:#bbf7d0;margin-top:4px;">
                Los participantes pueden ingresar y editar sus boletas con normalidad.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

if es_admin:
    if acceso_bloqueado:
        if st.button("🔓 DESBLOQUEAR — habilitar ingreso de participantes",
                      use_container_width=True, key="btn_toggle_lock_main", type="primary"):
            if set_acceso_bloqueado(False):
                st.toast("🔓 Ingreso de participantes habilitado.", icon="🔓")
                st.rerun()
    else:
        if st.button("🔒 BLOQUEAR — cortar el ingreso de participantes",
                      use_container_width=True, key="btn_toggle_lock_main", type="primary"):
            if set_acceso_bloqueado(True):
                st.toast("🔒 Ingreso de participantes bloqueado.", icon="🔒")
                st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)


def avatar_html_from_bytes(foto_bytes, nombre, size=65, font_size=24, border=2):
    if foto_bytes:
        encoded = base64.b64encode(foto_bytes).decode()
        return (
            '<img src="data:image/jpeg;base64,' + encoded + '" '
            'style="width:' + str(size) + 'px; height:' + str(size) + 'px; border-radius:50%; '
            'object-fit:cover; margin-right:15px; '
            'border:' + str(border) + 'px solid #e8c96b; vertical-align:middle; flex-shrink:0;">'
        )
    inicial = nombre[0].upper() if nombre else "?"
    return (
        '<div style="width:' + str(size) + 'px; height:' + str(size) + 'px; border-radius:50%; '
        'background:#1e2840; color:#e8c96b; display:inline-flex; '
        'align-items:center; justify-content:center; '
        "font-family:'Bebas Neue'; font-size:" + str(font_size) + 'px; '
        'margin-right:15px; border:' + str(border) + 'px solid #e8c96b; '
        'vertical-align:middle; flex-shrink:0;">' + inicial + '</div>'
    )


def puede_editar(p_id: int) -> bool:
    if es_admin:
        return True
    if acceso_bloqueado:
        return False
    if part_logueado_id is not None and part_logueado_id == p_id:
        return True
    return False


def guardar_pron(p_id, partido_id, nuevo_val, gol_local=None, gol_visitante=None):
    if not puede_editar(p_id):
        st.warning("No tenés permiso para modificar esta boleta.")
        return False
    try:
        existente = (
            sb.table("pronosticos")
            .select("id")
            .eq("participante_id", p_id)
            .eq("partido_id", partido_id)
            .execute()
        )
        if nuevo_val:
            if gol_local is None or gol_visitante is None:
                try:
                    partes_gv = str(nuevo_val).split("-")
                    gol_local = int(partes_gv[0])
                    gol_visitante = int(partes_gv[1])
                except (ValueError, IndexError):
                    gol_local = None
                    gol_visitante = None

            payload = {
                "pronostico": nuevo_val,
                "gol_local": gol_local,
                "gol_visitante": gol_visitante,
            }

            if existente.data:
                row_id = existente.data[0]["id"]
                sb.table("pronosticos").update(payload).eq("id", row_id).execute()
            else:
                sb.table("pronosticos").insert({
                    "participante_id": p_id,
                    "partido_id": partido_id,
                    **payload
                }).execute()
        else:
            if existente.data:
                row_id = existente.data[0]["id"]
                sb.table("pronosticos").delete().eq("id", row_id).execute()
        return True
    except Exception as ex:
        st.error("Error al guardar: " + str(ex))
        return False


# ══════════════════════════════════════════════════════════════════════════════
# AGREGAR PARTICIPANTE — solo admin
# ══════════════════════════════════════════════════════════════════════════════
if es_admin:
    with st.expander("➕ Agregar nuevo participante"):
        nombre_nuevo = st.text_input("Nombre del participante", key="input_nombre_nuevo")
        foto_nueva   = st.file_uploader("Foto del participante (opcional)", type=["jpg", "jpeg", "png"], key="foto_nueva")

        if nombre_nuevo.strip():
            st.caption(f"Usuario generado: **{generar_username(nombre_nuevo)}**  ·  Se asignará contraseña aleatoria al guardar")

        if st.button("💾 Guardar Participante", use_container_width=True):
            if nombre_nuevo.strip():
                foto_b64 = ""
                if foto_nueva is not None:
                    foto_bytes_up = foto_nueva.read()
                    foto_b64 = base64.b64encode(foto_bytes_up).decode()

                username_gen = generar_username(nombre_nuevo)
                password_gen = generar_password(8)

                existing = sb.table("participantes").select("id").eq("username", username_gen).execute()
                if existing.data:
                    username_gen = username_gen + "_" + generar_password(3).lower()

                sb.table("participantes").insert({
                    "nombre": nombre_nuevo.strip(),
                    "foto": foto_b64,
                    "username": username_gen,
                    "password_hash": _hash_pwd(password_gen),
                }).execute()

                st.success(
                    f"✅ **{nombre_nuevo.strip()}** agregado con éxito!\n\n"
                    f"🔑 **Usuario:** `{username_gen}`\n\n"
                    f"🔒 **Contraseña:** `{password_gen}`\n\n"
                    f"⚠️ Copiá estas credenciales ahora — la contraseña no se muestra nuevamente."
                )
                st.rerun()
            else:
                st.error("El nombre no puede estar vacío.")

# ══════════════════════════════════════════════════════════════════════════════
# RESETEAR TODAS LAS BOLETAS — solo admin
# ══════════════════════════════════════════════════════════════════════════════
if es_admin:
    if "confirmar_reset_total" not in st.session_state:
        st.session_state.confirmar_reset_total = False

    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, rgba(239,68,68,0.08) 0%, rgba(185,28,28,0.12) 100%);
            border: 1px solid rgba(239,68,68,0.3);
            border-radius: 16px;
            padding: 16px 20px;
            margin: 12px 0 4px 0;
            display: flex;
            align-items: center;
            gap: 14px;
        ">
            <div style="font-size:28px;line-height:1;">🧹</div>
            <div>
                <div style="font-family:'Bebas Neue',sans-serif;font-size:17px;
                    color:#f87171;letter-spacing:2px;line-height:1.1;">
                    LIMPIAR LISTA DE PARTICIPANTES
                </div>
                <div style="font-size:11px;color:#94a3b8;margin-top:3px;">
                    Elimina todos los participantes inscriptos y sus pronósticos.
                    Esta acción no se puede deshacer.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not st.session_state.confirmar_reset_total:
        if st.button(
            "🧹  Limpiar lista de participantes",
            key="btn_reset_all_boletas",
            use_container_width=True,
            type="secondary",
        ):
            st.session_state.confirmar_reset_total = True
            st.rerun()
    else:
        st.markdown(
            '<div style="background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.4);'
            'border-radius:10px;padding:10px 16px;text-align:center;margin-bottom:6px;">'
            '<span style="color:#f87171;font-weight:700;font-size:13px;">'
            '⚠️ ¿Confirmar? Se borrarán TODOS los participantes y sus pronósticos. Sin vuelta atrás.</span>'
            '</div>',
            unsafe_allow_html=True
        )
        col_confirm, col_cancel = st.columns(2)
        with col_confirm:
            if st.button("✓ Sí, borrar todo", key="btn_reset_all_confirm",
                         use_container_width=True, type="primary"):
                try:
                    sb.table("pronosticos").delete().neq("id", 0).execute()
                    sb.table("participantes").delete().neq("id", 0).execute()
                    for k in list(st.session_state.keys()):
                        if any(k.startswith(p) for p in ["gl_", "gv_",
                                                          "part_expandido", "confirmar_eliminar",
                                                          "editando_participante"]):
                            del st.session_state[k]
                    st.session_state.confirmar_reset_total = False
                    st.toast("✅ Lista de participantes limpiada.", icon="🧹")
                    st.rerun()
                except Exception as e:
                    st.error("Error al limpiar: " + str(e))
                    st.session_state.confirmar_reset_total = False
        with col_cancel:
            if st.button("✗ Cancelar", key="btn_reset_all_cancel",
                         use_container_width=True):
                st.session_state.confirmar_reset_total = False
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# CARGA DE PARTIDOS (con caché) — usa columnas de Liga Profesional
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=30)
def cargar_partidos():
    return (
        conectar()
        .table("partidos")
        .select("id, equipo_local, equipo_visitante, zona, fecha_numero, fecha_partido, hora, estadio")
        .execute()
        .data
    )


try:
    todos_partidos = cargar_partidos()
except Exception as e:
    st.error(
        "No se pudo leer la tabla 'partidos' desde Supabase.\n\n"
        "Causas más comunes:\n"
        "- La tabla no existe todavía o está vacía.\n"
        "- Row Level Security (RLS) está activado sin policy de SELECT para 'anon'.\n\n"
        f"Detalle técnico: {e}"
    )
    st.stop()

if not todos_partidos:
    st.info("No hay partidos cargados en la base de datos.")
    st.stop()

# ── Agrupar por zona y, dentro de cada zona, por fecha_numero ────────────────
partidos_por_zona: dict = {}
for p in todos_partidos:
    z = p["zona"]
    partidos_por_zona.setdefault(z, {})
    f = p["fecha_numero"]
    partidos_por_zona[z].setdefault(f, [])
    partidos_por_zona[z][f].append(p)

zonas_disponibles = sorted(
    partidos_por_zona.keys(),
    key=lambda z: (0 if z == "A" else 1 if z == "B" else 2, z)
)


# ══════════════════════════════════════════════════════════════════════════════
# LISTA DE PARTICIPANTES
# ══════════════════════════════════════════════════════════════════════════════
resp_p = sb.table("participantes").select("id, nombre, foto, username").order("nombre").execute()
participantes = resp_p.data

if not participantes:
    st.info("Aún no se han registrado participantes.")
    st.stop()

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    '<h3 style="color:#e8c96b; font-family:\'Bebas Neue\',sans-serif; letter-spacing:2px;">📋 PARTICIPANTES</h3>',
    unsafe_allow_html=True
)

if "part_expandido" not in st.session_state:
    st.session_state.part_expandido = None
if "confirmar_eliminar" not in st.session_state:
    st.session_state.confirmar_eliminar = None
if "editando_participante" not in st.session_state:
    st.session_state.editando_participante = None

busqueda_part = st.text_input("🔍 Buscar participante", placeholder="Escribí un nombre...", key="buscar_participante")
participantes_filtrados = [
    p for p in participantes
    if busqueda_part.strip() == "" or busqueda_part.strip().lower() in p["nombre"].lower()
]
if busqueda_part.strip() and not participantes_filtrados:
    st.info("No se encontraron participantes con ese nombre.")

for numero, p in enumerate(participantes_filtrados, start=1):
    p_id       = p["id"]
    p_nom      = p["nombre"]
    p_username = p.get("username") or "—"
    p_foto_b64 = p.get("foto") or ""
    foto_bytes = base64.b64decode(p_foto_b64) if p_foto_b64 else None
    puntos     = calcular_puntos(p_id)
    expandido  = st.session_state.part_expandido == p_id
    confirmando = st.session_state.confirmar_eliminar == p_id
    editable   = puede_editar(p_id)

    av_small = avatar_html_from_bytes(foto_bytes, p_nom, size=50, font_size=20)

    if es_admin:
        col_av, col_info, col_pts, col_btn, col_edit, col_del = st.columns([1, 4, 2, 2, 1, 1])
    else:
        col_av, col_info, col_pts, col_btn = st.columns([1, 4, 2, 2])
        col_edit = None
        col_del  = None

    with col_av:
        st.markdown(
            '<div style="padding-top:6px;display:flex;align-items:center;gap:6px;">'
            '<span class="part-number">' + str(numero) + '</span>'
            + av_small + '</div>',
            unsafe_allow_html=True
        )

    with col_info:
        user_tag = (
            '<div style="font-size:10px;color:#64748b;font-family:\'DM Sans\',sans-serif;">'
            '👤 ' + p_username + '</div>'
        ) if es_admin else ""
        st.markdown(
            '<div style="padding:6px 0 6px 12px;">'
            '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:20px;color:#fff;letter-spacing:1px;">'
            + p_nom.upper() + '</div>' + user_tag + '</div>',
            unsafe_allow_html=True
        )

    with col_pts:
        st.markdown(
            '<div style="text-align:center;padding-top:2px;">'
            '<div class="part-puntos-big">' + str(puntos) + '</div>'
            '<div class="part-puntos-label">pts</div>'
            '</div>',
            unsafe_allow_html=True
        )

    with col_btn:
        label_btn = "▲ Cerrar" if expandido else "📝 Boleta"
        if st.button(label_btn, key="toggle_" + str(p_id), use_container_width=True):
            st.session_state.part_expandido = None if expandido else p_id
            st.session_state.confirmar_eliminar = None
            st.rerun()

    if col_edit is not None:
        with col_edit:
            editando_this = st.session_state.editando_participante == p_id
            label_edit = "✖️" if editando_this else "✏️"
            st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
            if st.button(label_edit, key="edit_part_" + str(p_id), use_container_width=True,
                         help="Editar " + p_nom):
                st.session_state.editando_participante = None if editando_this else p_id
                st.rerun()

    if col_del is not None:
        with col_del:
            if confirmando:
                st.markdown(
                    '<div style="font-size:10px;color:#f87171;text-align:center;padding-top:2px;">¿Eliminar?</div>',
                    unsafe_allow_html=True
                )
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✓", key="confirm_del_" + str(p_id), use_container_width=True):
                        sb.table("pronosticos").delete().eq("participante_id", p_id).execute()
                        sb.table("participantes").delete().eq("id", p_id).execute()
                        st.session_state.confirmar_eliminar = None
                        if st.session_state.part_expandido == p_id:
                            st.session_state.part_expandido = None
                        st.toast("'" + p_nom + "' eliminado.", icon="🗑️")
                        st.rerun()
                with c2:
                    if st.button("✗", key="cancel_del_" + str(p_id), use_container_width=True):
                        st.session_state.confirmar_eliminar = None
                        st.rerun()
            else:
                st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
                if st.button("✕", key="del_part_" + str(p_id), use_container_width=True):
                    st.session_state.confirmar_eliminar = p_id
                    st.rerun()

    st.markdown(
        '<hr style="border:none; border-top:1px solid rgba(255,255,255,0.08); margin:2px 0 6px 0;">',
        unsafe_allow_html=True
    )

    # ── Panel edición nombre/foto + reseteo de contraseña (admin) ─────────────
    if es_admin and st.session_state.editando_participante == p_id:
        st.markdown(
            '<div style="background:rgba(20,28,50,0.92);border:1px solid rgba(232,201,107,0.3);'
            'border-radius:14px;padding:16px 20px;margin-bottom:10px;">',
            unsafe_allow_html=True
        )
        col_enombre, col_efoto = st.columns([2, 2])
        with col_enombre:
            nuevo_nombre = st.text_input("✏️ Nombre", value=p_nom, key="edit_nombre_" + str(p_id))
        with col_efoto:
            nueva_foto = st.file_uploader(
                "🖼️ Nueva foto (opcional)", type=["jpg", "jpeg", "png"],
                key="edit_foto_" + str(p_id)
            )
        col_guardar, col_cancelar, col_resetpwd = st.columns([2, 1, 2])
        with col_guardar:
            if st.button("💾 Guardar cambios", key="save_edit_" + str(p_id), use_container_width=True):
                update_data = {}
                nombre_limpio = nuevo_nombre.strip()
                if nombre_limpio and nombre_limpio != p_nom:
                    update_data["nombre"] = nombre_limpio
                if nueva_foto is not None:
                    foto_bytes_new = nueva_foto.read()
                    update_data["foto"] = base64.b64encode(foto_bytes_new).decode()
                if update_data:
                    sb.table("participantes").update(update_data).eq("id", p_id).execute()
                    st.toast("✅ Participante actualizado.", icon="✅")
                st.session_state.editando_participante = None
                st.rerun()
        with col_cancelar:
            if st.button("✗ Cancelar", key="cancel_edit_" + str(p_id), use_container_width=True):
                st.session_state.editando_participante = None
                st.rerun()
        with col_resetpwd:
            if st.button("🔑 Nueva contraseña", key="reset_pwd_" + str(p_id), use_container_width=True):
                nueva_pwd = generar_password(8)
                sb.table("participantes").update({"password_hash": _hash_pwd(nueva_pwd)}).eq("id", p_id).execute()
                st.success(
                    f"Nueva contraseña para **{p_nom}**: `{nueva_pwd}`  — copiala ahora."
                )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Panel expandido ────────────────────────────────────────────────────────
    if expandido:
        av_grande = avatar_html_from_bytes(foto_bytes, p_nom, size=70, font_size=28)

        st.markdown(
            '<div class="part-header">'
            + av_grande +
            '<div>'
            '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:32px;color:#e8c96b;margin:0;">'
            + p_nom.upper() +
            '</div>'
            '<div style="font-size:13px;color:#94a3b8;margin-top:2px;">Participante #' + str(numero) + '</div>'
            '</div>'
            '<div class="header-puntos-block">'
            '<div class="part-puntos-big" style="font-size:56px;">' + str(puntos) + '</div>'
            '<div class="part-puntos-label">puntos actuales</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:26px;color:#fff;'
            'letter-spacing:2px;margin-top:18px;margin-bottom:4px;">📝 BOLETA DE PRONÓSTICOS</div>',
            unsafe_allow_html=True
        )

        # ── Pronósticos del participante (todos) ──────────────────────────────
        resp_pron = (
            sb.table("pronosticos")
            .select("partido_id, pronostico")
            .eq("participante_id", p_id)
            .execute()
        )
        pron_dict = {r["partido_id"]: r["pronostico"] for r in resp_pron.data}

        # ── Selector de zona ──────────────────────────────────────────────────
        key_zona = "zona_boleta_" + str(p_id)
        if key_zona not in st.session_state:
            st.session_state[key_zona] = zonas_disponibles[0]

        cols_zona = st.columns(len(zonas_disponibles))
        for i, z in enumerate(zonas_disponibles):
            with cols_zona[i]:
                es_activa = st.session_state[key_zona] == z
                etiqueta_z = "Interzonal" if z == "Interzonal" else f"Zona {z}"
                if st.button(
                    etiqueta_z,
                    key=f"zona_boleta_{p_id}_{z}",
                    use_container_width=True,
                    type="primary" if es_activa else "secondary"
                ):
                    st.session_state[key_zona] = z
                    # Resetear índice de fecha al cambiar de zona
                    st.session_state.pop(f"fecha_boleta_{p_id}_{z}", None)
                    st.rerun()

        zona_sel = st.session_state[key_zona]
        etiqueta_zona_lbl = "INTERZONAL" if zona_sel == "Interzonal" else f"ZONA {zona_sel}"
        st.markdown(
            f'<div style="font-family:\'Bebas Neue\',sans-serif;font-size:1rem;color:#e8c96b;'
            f'text-align:center;letter-spacing:3px;margin-bottom:10px;">{etiqueta_zona_lbl}</div>',
            unsafe_allow_html=True
        )

        # ── Partidos de la zona seleccionada agrupados por fecha ─────────────
        fechas_zona = sorted(partidos_por_zona.get(zona_sel, {}).keys(), key=int)
        if not fechas_zona:
            st.info("No hay partidos en esta zona.")
        else:
            key_fecha = f"fecha_boleta_{p_id}_{zona_sel}"
            if key_fecha not in st.session_state:
                st.session_state[key_fecha] = fechas_zona[0]
            if st.session_state[key_fecha] not in fechas_zona:
                st.session_state[key_fecha] = fechas_zona[0]

            # ── Selector de fecha (jornada) ───────────────────────────────────
            def prog_fecha(f):
                pts_f = partidos_por_zona[zona_sel].get(f, [])
                comp = sum(
                    1 for pt in pts_f
                    if pt["id"] in pron_dict
                    and pron_dict[pt["id"]]
                    and "-" in str(pron_dict[pt["id"]])
                )
                return comp, len(pts_f)

            n_fechas = len(fechas_zona)
            cols_f = st.columns(min(n_fechas, 8))
            for i, f in enumerate(fechas_zona):
                with cols_f[i % len(cols_f)]:
                    activo_f = st.session_state[key_fecha] == f
                    comp_f, tot_f = prog_fecha(f)
                    completo_f = comp_f == tot_f
                    if activo_f:
                        borde_f, bg_f, color_f = "#e8c96b", "rgba(232,201,107,0.12)", "#e8c96b"
                    elif completo_f:
                        borde_f, bg_f, color_f = "#22c55e", "rgba(34,197,94,0.07)", "#4ade80"
                    else:
                        borde_f, bg_f, color_f = "rgba(255,255,255,0.12)", "rgba(255,255,255,0.03)", "#94a3b8"

                    st.markdown(
                        f'<div style="background:{bg_f};border:2px solid {borde_f};border-radius:10px;'
                        f'padding:6px 4px 5px 4px;text-align:center;margin-bottom:-8px;">'
                        f'<div style="font-family:\'Bebas Neue\',sans-serif;font-size:15px;'
                        f'color:{color_f};letter-spacing:1px;line-height:1.1;">F{f}</div>'
                        f'<div style="font-size:9px;color:#64748b;font-family:\'DM Sans\',sans-serif;'
                        f'margin-top:1px;">{comp_f}/{tot_f}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    if st.button("‎", key=f"fecha_{p_id}_{zona_sel}_{f}", use_container_width=True,
                                 help=f"Fecha {f}  ({comp_f}/{tot_f} pronósticos)"):
                        if st.session_state[key_fecha] != f:
                            st.session_state[key_fecha] = f
                            st.session_state.pop(f"part_idx_{p_id}_{zona_sel}_{f}", None)
                        st.rerun()

            fecha_sel = st.session_state[key_fecha]
            comp_sel, _ = prog_fecha(fecha_sel)
            partidos_fecha = sorted(
                partidos_por_zona[zona_sel].get(fecha_sel, []),
                key=lambda x: (x.get("fecha_partido") or "9999-99-99", x.get("hora") or "99:99")
            )
            total_f = len(partidos_fecha)

            st.markdown(
                f'<div style="font-family:\'Bebas Neue\',sans-serif;font-size:17px;'
                f'color:#e8c96b;letter-spacing:2px;margin:14px 0 6px 0;">'
                f'FECHA {fecha_sel}'
                f' <span style="font-size:12px;color:#94a3b8;font-family:\'DM Sans\',sans-serif;font-weight:400;">'
                f'· {comp_sel}/{total_f} pronósticos</span></div>',
                unsafe_allow_html=True
            )

            key_idx = f"part_idx_{p_id}_{zona_sel}_{fecha_sel}"
            if key_idx not in st.session_state:
                st.session_state[key_idx] = 0
            idx = min(st.session_state[key_idx], total_f - 1)
            st.session_state[key_idx] = idx

            # ── Navegación entre partidos de la fecha ─────────────────────────
            col_prev, col_ind, col_next = st.columns([1, 4, 1])
            with col_prev:
                if st.button("◀", key=f"prev_{p_id}_{zona_sel}_{fecha_sel}", use_container_width=True,
                             disabled=(idx == 0)):
                    st.session_state[key_idx] = idx - 1
                    st.rerun()
            with col_ind:
                st.markdown(
                    f'<div style="text-align:center;font-family:\'DM Sans\',sans-serif;'
                    f'font-size:13px;color:#94a3b8;padding-top:8px;">'
                    f'Partido <strong style="color:#fff;">{idx + 1}</strong> de {total_f}</div>',
                    unsafe_allow_html=True
                )
            with col_next:
                if st.button("▶", key=f"next_{p_id}_{zona_sel}_{fecha_sel}", use_container_width=True,
                             disabled=(idx == total_f - 1)):
                    st.session_state[key_idx] = idx + 1
                    st.rerun()

            dots_inner = ""
            for n in range(total_f):
                if n == idx:
                    dots_inner += "<div style='width:20px;height:6px;border-radius:3px;background:#e8c96b'></div>"
                else:
                    dots_inner += "<div style='width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,0.15)'></div>"
            st.markdown('<div class="dots-row-clickable">' + dots_inner + '</div>', unsafe_allow_html=True)

            # ── Selector directo de partido ───────────────────────────────────
            with st.expander("🔢 Ir directamente a un partido", expanded=False):
                n_cols_f = 2
                filas_f = (total_f + n_cols_f - 1) // n_cols_f
                for fila in range(filas_f):
                    cols_sel_f = st.columns(n_cols_f)
                    for c in range(n_cols_f):
                        n = fila * n_cols_f + c
                        if n >= total_f:
                            continue
                        with cols_sel_f[c]:
                            pt_n = partidos_fecha[n]
                            tiene_pron = (
                                pt_n["id"] in pron_dict
                                and pron_dict[pt_n["id"]]
                                and "-" in str(pron_dict[pt_n["id"]])
                            )
                            ini_l = (pt_n["equipo_local"] or "")[:6].upper()
                            ini_v = (pt_n["equipo_visitante"] or "")[:6].upper()
                            icono_sel = "✅" if tiene_pron else "⬜"
                            if st.button(
                                icono_sel + " " + ini_l + " vs " + ini_v,
                                key=f"seldirecto_{p_id}_{zona_sel}_{fecha_sel}_{n}",
                                use_container_width=True,
                                type="primary" if n == idx else "secondary",
                                help=f"Ir al partido {n + 1}: {pt_n['equipo_local']} vs {pt_n['equipo_visitante']}",
                            ):
                                st.session_state[key_idx] = n
                                st.rerun()

            # ── Tarjeta del partido actual ────────────────────────────────────
            partido_actual = partidos_fecha[idx]
            partido_id  = partido_actual["id"]
            local       = partido_actual["equipo_local"]
            visitante   = partido_actual["equipo_visitante"]
            fecha_ptdo  = partido_actual.get("fecha_partido")
            hora_ptdo   = partido_actual.get("hora")
            estadio_ptdo = partido_actual.get("estadio")

            valor_actual = pron_dict.get(partido_id)
            goles_local_guardado = None
            goles_visit_guardado = None
            if valor_actual and "-" in str(valor_actual):
                partes = str(valor_actual).split("-")
                try:
                    goles_local_guardado = int(partes[0])
                    goles_visit_guardado = int(partes[1])
                except ValueError:
                    pass

            img_local = get_escudo_img(local, size=52)
            img_visit = get_escudo_img(visitante, size=52)

            # Meta del partido
            meta_parts = []
            if fecha_ptdo:
                meta_parts.append('<i class="ti ti-calendar-event"></i> ' + str(fecha_ptdo))
            if hora_ptdo:
                meta_parts.append('<i class="ti ti-clock"></i> ' + str(hora_ptdo))
            if estadio_ptdo:
                meta_parts.append('<i class="ti ti-map-pin"></i> ' + str(estadio_ptdo))
            meta_str = "&nbsp;&nbsp;|&nbsp;&nbsp;".join(meta_parts) if meta_parts else "A confirmar"

            if goles_local_guardado is not None and goles_visit_guardado is not None:
                gl = goles_local_guardado
                gv = goles_visit_guardado
                if gl > gv:
                    signo = "1"; color_b = "#4ade80"; bg_b = "rgba(34,197,94,0.2)"; label_b = "✅ Gana " + local
                elif gl == gv:
                    signo = "X"; color_b = "#e8c96b"; bg_b = "rgba(232,201,107,0.18)"; label_b = "✅ Empate"
                else:
                    signo = "2"; color_b = "#f87171"; bg_b = "rgba(239,68,68,0.2)"; label_b = "✅ Gana " + visitante
                badge = (
                    '<span style="background:' + bg_b + ';color:' + color_b + ';'
                    'border-radius:20px;padding:3px 14px;font-size:12px;font-weight:700;">'
                    + label_b + ' · ' + signo + '</span>'
                )
                score_html = (
                    '<div class="score-box-wrap">'
                    '<div style="text-align:center;">'
                    '<div class="score-box">' + str(gl) + '</div>'
                    '<div class="score-label">' + local[:10] + '</div>'
                    '</div>'
                    '<div class="score-dash">-</div>'
                    '<div style="text-align:center;">'
                    '<div class="score-box">' + str(gv) + '</div>'
                    '<div class="score-label">' + visitante[:10] + '</div>'
                    '</div>'
                    '</div>'
                )
            else:
                badge = (
                    '<span style="background:rgba(100,116,139,0.18);color:#64748b;'
                    'border-radius:20px;padding:3px 14px;font-size:12px;">'
                    '— Sin pronóstico</span>'
                )
                score_html = (
                    '<div class="score-box-wrap">'
                    '<div style="text-align:center;">'
                    '<div class="score-box empty">?</div>'
                    '<div class="score-label">' + local[:10] + '</div>'
                    '</div>'
                    '<div class="score-dash">-</div>'
                    '<div style="text-align:center;">'
                    '<div class="score-box empty">?</div>'
                    '<div class="score-label">' + visitante[:10] + '</div>'
                    '</div>'
                    '</div>'
                )

            st.markdown(
                '<div class="card-partido">'
                '<div class="card-partido-meta">' + meta_str + '</div>'
                '<div class="card-partido-vs-row">'
                '<div class="card-equipo">' + img_local + '<div class="card-nombre-equipo">' + local + '</div></div>'
                '<div class="card-vs">VS</div>'
                '<div class="card-equipo">' + img_visit + '<div class="card-nombre-equipo">' + visitante + '</div></div>'
                '</div>'
                + score_html +
                '<div style="text-align:center;margin-top:8px;">' + badge + '</div>'
                '</div>',
                unsafe_allow_html=True
            )

            # ── Inputs de edición ─────────────────────────────────────────────
            if editable:
                st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

                key_gl = "gl_" + str(p_id) + "_" + str(partido_id)
                key_gv = "gv_" + str(p_id) + "_" + str(partido_id)

                if key_gl not in st.session_state:
                    st.session_state[key_gl] = goles_local_guardado if goles_local_guardado is not None else 0
                if key_gv not in st.session_state:
                    st.session_state[key_gv] = goles_visit_guardado if goles_visit_guardado is not None else 0

                if goles_local_guardado is not None:
                    if st.session_state[key_gl] != goles_local_guardado and partido_id not in st.session_state.get("_dirty_" + str(p_id), set()):
                        st.session_state[key_gl] = goles_local_guardado
                if goles_visit_guardado is not None:
                    if st.session_state[key_gv] != goles_visit_guardado and partido_id not in st.session_state.get("_dirty_" + str(p_id), set()):
                        st.session_state[key_gv] = goles_visit_guardado

                col_inp_l, col_guion, col_inp_v, col_guardar_m, col_del2 = st.columns([3, 1, 3, 3, 1])

                with col_inp_l:
                    st.markdown(
                        '<div style="font-size:11px;color:#94a3b8;text-align:center;margin-bottom:2px;">'
                        + local[:14] + '</div>',
                        unsafe_allow_html=True
                    )
                    gl_val = st.number_input(
                        "⚽ " + local, min_value=0, max_value=20,
                        value=st.session_state[key_gl],
                        key=key_gl, label_visibility="collapsed"
                    )

                with col_guion:
                    st.markdown(
                        '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:28px;'
                        'color:#e8c96b;text-align:center;padding-top:28px;line-height:1;">-</div>',
                        unsafe_allow_html=True
                    )

                with col_inp_v:
                    st.markdown(
                        '<div style="font-size:11px;color:#94a3b8;text-align:center;margin-bottom:2px;">'
                        + visitante[:14] + '</div>',
                        unsafe_allow_html=True
                    )
                    gv_val = st.number_input(
                        "⚽ " + visitante, min_value=0, max_value=20,
                        value=st.session_state[key_gv],
                        key=key_gv, label_visibility="collapsed"
                    )

                with col_guardar_m:
                    st.markdown('<div style="height:26px;"></div>', unsafe_allow_html=True)
                    marcador_nuevo = str(gl_val) + "-" + str(gv_val)
                    ya_guardado = (marcador_nuevo == valor_actual)
                    tipo_btn = "primary" if not ya_guardado else "secondary"
                    lbl_btn  = "✅ Guardado" if ya_guardado else "💾 Guardar"
                    if st.button(lbl_btn, key="save_m_" + str(p_id) + "_" + str(partido_id),
                                 use_container_width=True, type=tipo_btn, disabled=ya_guardado):
                        if guardar_pron(p_id, partido_id, marcador_nuevo, gl_val, gv_val):
                            st.toast("✅ Pronóstico guardado: " + marcador_nuevo, icon="⚽")
                            st.rerun()

                with col_del2:
                    st.markdown('<div style="height:26px;"></div>', unsafe_allow_html=True)
                    if st.button("🗑️", key="del_" + str(p_id) + "_" + str(partido_id),
                                 help="Borrar pronóstico",
                                 use_container_width=True):
                        sb.table("pronosticos").delete()\
                            .eq("participante_id", p_id)\
                            .eq("partido_id", partido_id)\
                            .execute()
                        st.session_state[key_gl] = 0
                        st.session_state[key_gv] = 0
                        st.toast("Pronóstico borrado.", icon="🗑️")
                        st.rerun()

                st.markdown("<br>", unsafe_allow_html=True)
                _, col_reset = st.columns([3, 1])
                with col_reset:
                    if st.button("🗑️ Resetear Boleta", key="reset_total_" + str(p_id),
                                 use_container_width=True,
                                 help="Borra todos los pronósticos de este participante"):
                        sb.table("pronosticos").delete().eq("participante_id", p_id).execute()
                        st.toast("Boleta de " + p_nom + " reseteada.", icon="🔄")
                        st.rerun()

            else:
                st.markdown(
                    '<div style="background:rgba(100,116,139,0.1);border:1px solid rgba(100,116,139,0.2);'
                    'border-radius:10px;padding:10px 16px;text-align:center;margin-top:8px;">'
                    '<span style="font-size:12px;color:#64748b;">'
                    '🔒 Iniciá sesión como <strong>' + p_nom + '</strong> para modificar esta boleta'
                    '</span></div>',
                    unsafe_allow_html=True
                )

st.markdown("<br>", unsafe_allow_html=True)
