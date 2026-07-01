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
        background-image: url('https://raw.githubusercontent.com/arcaltdfootball/PRODEFIFAWC2026UNQ/main/prode_supabase/fwcup202603.jpg');
        background-size: cover;
        background-position: center top;
        background-attachment: fixed;
        background-repeat: no-repeat;
        background-color: #6b0f0f;
    }
    [data-testid="stAppViewContainer"] > div:first-child::before {
        content: '';
        position: fixed;
        inset: 0;
        background: rgba(10, 5, 5, 0.72);
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
# HELPERS DE CONTRASEÑA
# ══════════════════════════════════════════════════════════════════════════════
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "aleotero")


def _hash_pwd(pwd: str) -> str:
    """SHA-256 para almacenar contraseñas."""
    return hashlib.sha256(pwd.encode()).hexdigest()


def generar_password(largo: int = 8) -> str:
    """Genera contraseña aleatoria legible."""
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(largo))


def generar_username(nombre: str) -> str:
    """Username a partir del nombre (sin espacios, minúsculas)."""
    base = nombre.strip().lower().replace(" ", "_")
    base = "".join(c for c in base if c.isalnum() or c == "_")
    return base or "user"


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
        user_input = st.text_input("Usuario", key="sidebar_user", placeholder="Tu usuario...")
        pwd_input  = st.text_input("Contraseña", type="password", key="sidebar_pwd", placeholder="Contraseña...")

        if st.button("Ingresar", use_container_width=True, key="btn_login"):
            if modo_login == "Admin":
                if user_input.strip() == "admin" and pwd_input == ADMIN_PASSWORD:
                    st.session_state.es_admin = True
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
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
        if st.button("🚪 Cerrar sesión", use_container_width=True, key="btn_logout"):
            st.session_state.es_admin = False
            st.rerun()

    else:
        st.markdown(
            '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:15px;'
            'color:#60a5fa;letter-spacing:2px;">✅ ' + (part_logueado_nom or "").upper() + '</div>',
            unsafe_allow_html=True
        )
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

# ── FLAGS ──────────────────────────────────────────────────────────────────────
FLAGS = {
    "Alemania":              "https://hatscripts.github.io/circle-flags/flags/de.svg",
    "Arabia Saudi":          "https://hatscripts.github.io/circle-flags/flags/sa.svg",
    "Argelia":               "https://hatscripts.github.io/circle-flags/flags/dz.svg",
    "Argentina":             "https://hatscripts.github.io/circle-flags/flags/ar.svg",
    "Australia":             "https://hatscripts.github.io/circle-flags/flags/au.svg",
    "Austria":               "https://hatscripts.github.io/circle-flags/flags/at.svg",
    "Belgica":               "https://hatscripts.github.io/circle-flags/flags/be.svg",
    "Bélgica":               "https://hatscripts.github.io/circle-flags/flags/be.svg",
    "Bosnia":                "https://hatscripts.github.io/circle-flags/flags/ba.svg",
    "Bosnia y Herzegovina":  "https://hatscripts.github.io/circle-flags/flags/ba.svg",
    "Brasil":                "https://hatscripts.github.io/circle-flags/flags/br.svg",
    "Cabo Verde":            "https://hatscripts.github.io/circle-flags/flags/cv.svg",
    "Canada":                "https://hatscripts.github.io/circle-flags/flags/ca.svg",
    "Canadá":                "https://hatscripts.github.io/circle-flags/flags/ca.svg",
    "Catar":                 "https://hatscripts.github.io/circle-flags/flags/qa.svg",
    "Colombia":              "https://hatscripts.github.io/circle-flags/flags/co.svg",
    "Costa de Marfil":       "https://hatscripts.github.io/circle-flags/flags/ci.svg",
    "Croacia":               "https://hatscripts.github.io/circle-flags/flags/hr.svg",
    "Curazao":               "https://hatscripts.github.io/circle-flags/flags/cw.svg",
    "Ecuador":               "https://hatscripts.github.io/circle-flags/flags/ec.svg",
    "EE. UU.":               "https://hatscripts.github.io/circle-flags/flags/us.svg",
    "Egipto":                "https://hatscripts.github.io/circle-flags/flags/eg.svg",
    "Escocia":               "https://hatscripts.github.io/circle-flags/flags/gb-sct.svg",
    "Espana":                "https://hatscripts.github.io/circle-flags/flags/es.svg",
    "España":                "https://hatscripts.github.io/circle-flags/flags/es.svg",
    "Estados Unidos":        "https://hatscripts.github.io/circle-flags/flags/us.svg",
    "Francia":               "https://hatscripts.github.io/circle-flags/flags/fr.svg",
    "Ghana":                 "https://hatscripts.github.io/circle-flags/flags/gh.svg",
    "Haiti":                 "https://hatscripts.github.io/circle-flags/flags/ht.svg",
    "Inglaterra":            "https://hatscripts.github.io/circle-flags/flags/gb-eng.svg",
    "Irak":                  "https://hatscripts.github.io/circle-flags/flags/iq.svg",
    "Iran":                  "https://hatscripts.github.io/circle-flags/flags/ir.svg",
    "RI de Iran":            "https://hatscripts.github.io/circle-flags/flags/ir.svg",
    "Japon":                 "https://hatscripts.github.io/circle-flags/flags/jp.svg",
    "Jordania":              "https://hatscripts.github.io/circle-flags/flags/jo.svg",
    "Marruecos":             "https://hatscripts.github.io/circle-flags/flags/ma.svg",
    "Mexico":                "https://hatscripts.github.io/circle-flags/flags/mx.svg",
    "México":                "https://hatscripts.github.io/circle-flags/flags/mx.svg",
    "Noruega":               "https://hatscripts.github.io/circle-flags/flags/no.svg",
    "Nueva Zelanda":         "https://hatscripts.github.io/circle-flags/flags/nz.svg",
    "Paises Bajos":          "https://hatscripts.github.io/circle-flags/flags/nl.svg",
    "Panama":                "https://hatscripts.github.io/circle-flags/flags/pa.svg",
    "Paraguay":              "https://hatscripts.github.io/circle-flags/flags/py.svg",
    "Portugal":              "https://hatscripts.github.io/circle-flags/flags/pt.svg",
    "RD Congo":              "https://hatscripts.github.io/circle-flags/flags/cd.svg",
    "Republica Checa":       "https://hatscripts.github.io/circle-flags/flags/cz.svg",
    "Republica de Corea":    "https://hatscripts.github.io/circle-flags/flags/kr.svg",
    "Senegal":               "https://hatscripts.github.io/circle-flags/flags/sn.svg",
    "Sudafrica":             "https://hatscripts.github.io/circle-flags/flags/za.svg",
    "Suecia":                "https://hatscripts.github.io/circle-flags/flags/se.svg",
    "Suiza":                 "https://hatscripts.github.io/circle-flags/flags/ch.svg",
    "Tunez":                 "https://hatscripts.github.io/circle-flags/flags/tn.svg",
    "Turquia":               "https://hatscripts.github.io/circle-flags/flags/tr.svg",
    "Uruguay":               "https://hatscripts.github.io/circle-flags/flags/uy.svg",
    "Uzbekistan":            "https://hatscripts.github.io/circle-flags/flags/uz.svg",
}


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


def get_iniciales_pais(nombre, largo=3):
    """Devuelve un código corto para el país: el código ISO de la bandera si existe
    (ej. 'AR', 'BR'), o si no, las primeras letras del nombre en mayúsculas."""
    if not nombre:
        return "?"
    url = FLAGS.get(nombre) or FLAGS.get(nombre.strip())
    if url:
        # ej: ".../flags/ar.svg" -> "AR"   |   ".../flags/gb-eng.svg" -> "ENG"
        codigo = url.rsplit("/", 1)[-1].replace(".svg", "")
        if "-" in codigo:
            codigo = codigo.split("-", 1)[1]
        return codigo.upper()[:largo]
    limpio = "".join(c for c in nombre if c.isalpha())
    return limpio.upper()[:largo] if limpio else "?"


def get_flag_img(nombre, size=48):
    if not nombre:
        return '<span style="font-size:' + str(size) + 'px;line-height:1;display:block;text-align:center;">🏳️</span>'
    nombre = nombre.strip()
    url = FLAGS.get(nombre) or FLAGS.get(nombre.strip())
    if url:
        return (
            '<img src="' + url + '" width="' + str(size) + '" height="' + str(size) + '" '
            'style="border-radius:50%;border:2px solid rgba(255,255,255,0.2);'
            'object-fit:cover;display:block;" />'
        )
    # Placeholder compuesto: "Francia / Suecia" → dos banderas superpuestas
    if " / " in nombre:
        partes = [p.strip() for p in nombre.split(" / ")]
        imgs = []
        for p in partes[:2]:
            u = FLAGS.get(p) or FLAGS.get(p.strip())
            if u:
                imgs.append(u)
        if imgs:
            sz_small = max(int(size * 0.68), 20)
            offset = sz_small // 3
            if len(imgs) == 2:
                return (
                    '<div style="position:relative;width:' + str(size) + 'px;height:' + str(size) + 'px;display:block;">'
                    '<img src="' + imgs[0] + '" width="' + str(sz_small) + '" height="' + str(sz_small) + '" '
                    'style="border-radius:50%;border:2px solid rgba(255,255,255,0.25);'
                    'position:absolute;top:0;left:0;object-fit:cover;" />'
                    '<img src="' + imgs[1] + '" width="' + str(sz_small) + '" height="' + str(sz_small) + '" '
                    'style="border-radius:50%;border:2px solid rgba(255,255,255,0.25);'
                    'position:absolute;bottom:0;right:0;object-fit:cover;" />'
                    '</div>'
                )
            else:
                return (
                    '<img src="' + imgs[0] + '" width="' + str(size) + '" height="' + str(size) + '" '
                    'style="border-radius:50%;border:2px solid rgba(255,255,255,0.2);'
                    'object-fit:cover;display:block;" />'
                )
    return '<span style="font-size:' + str(size) + 'px;line-height:1;display:block;text-align:center;">🏳️</span>'


def puede_editar(p_id: int) -> bool:
    """True si la sesión activa puede editar la boleta de p_id."""
    if es_admin:
        return True
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
            # Si no me pasaron los goles por separado, los deduzco del string "N-M"
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

                # Garantizar unicidad del username
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
# LISTADO DE PARTICIPANTES
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

        resp_todos = sb.table("partidos").select("id, local, visitante, fecha, grupo").order("grupo").order("fecha").execute()
        todos_partidos = resp_todos.data

        # ── Selector de fase: Grupos / Dieciseisavos ────────────────────────
        key_fase = "fase_boleta_" + str(p_id)
        if key_fase not in st.session_state:
            st.session_state[key_fase] = "grupos"

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if st.button("📋 Fase de Grupos", key="fboleta_grupos_" + str(p_id),
                         use_container_width=True,
                         type="primary" if st.session_state[key_fase] == "grupos" else "secondary"):
                st.session_state[key_fase] = "grupos"
                st.rerun()
        with col_f2:
            if st.button("🏆 Dieciseisavos", key="fboleta_16_" + str(p_id),
                         use_container_width=True,
                         type="primary" if st.session_state[key_fase] == "dieciseisavos" else "secondary"):
                st.session_state[key_fase] = "dieciseisavos"
                st.rerun()

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════
        # BOLETA — FASE DE GRUPOS
        # ══════════════════════════════════════════════════════════════════
        if st.session_state[key_fase] == "grupos":
            if not todos_partidos:
                st.info("No hay partidos cargados en la base de datos.")
            else:
                grupos_dict = {}
                for pt in todos_partidos:
                    grp = pt["grupo"]
                    grupos_dict.setdefault(grp, [])
                    grupos_dict[grp].append((pt["id"], pt["local"], pt["visitante"], pt["fecha"]))

                ORDEN = list("ABCDEFGHIJKL")
                grupos_ordenados = [g for g in ORDEN if g in grupos_dict]
                for g in sorted(grupos_dict.keys()):
                    if g not in grupos_ordenados:
                        grupos_ordenados.append(g)

                resp_pron = (
                    sb.table("pronosticos")
                    .select("partido_id, pronostico")
                    .eq("participante_id", p_id)
                    .execute()
                )
                pron_dict = {r["partido_id"]: r["pronostico"] for r in resp_pron.data}

                key_grp  = "grp_sel_" + str(p_id)
                key_part = "part_idx_" + str(p_id)
                if key_grp  not in st.session_state:
                    st.session_state[key_grp]  = grupos_ordenados[0]
                if key_part not in st.session_state:
                    st.session_state[key_part] = 0

                def prog_grupo(g):
                    pts = grupos_dict.get(g, [])
                    comp = sum(
                        1 for (pid2, *_) in pts
                        if pid2 in pron_dict and pron_dict[pid2] and "-" in str(pron_dict[pid2])
                    )
                    return comp, len(pts)

                n_grp = len(grupos_ordenados)
                cols_grp = st.columns(n_grp)
                for i, grp in enumerate(grupos_ordenados):
                    with cols_grp[i]:
                        activo = st.session_state[key_grp] == grp
                        comp_g, tot_g = prog_grupo(grp)
                        completo = comp_g == tot_g
                        if activo:
                            borde, bg, color_letra = "#e8c96b", "rgba(232,201,107,0.12)", "#e8c96b"
                        elif completo:
                            borde, bg, color_letra = "#22c55e", "rgba(34,197,94,0.07)", "#4ade80"
                        else:
                            borde, bg, color_letra = "rgba(255,255,255,0.12)", "rgba(255,255,255,0.03)", "#94a3b8"

                        st.markdown(
                            '<div style="background:' + bg + ';border:2px solid ' + borde + ';border-radius:10px;'
                            'padding:6px 4px 5px 4px;text-align:center;margin-bottom:-8px;">'
                            '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:18px;'
                            'color:' + color_letra + ';letter-spacing:1px;line-height:1.1;">' + grp + '</div>'
                            '<div style="font-size:9px;color:#64748b;font-family:\'DM Sans\',sans-serif;'
                            'margin-top:1px;">' + str(comp_g) + '/' + str(tot_g) + '</div>'
                            '</div>',
                            unsafe_allow_html=True
                        )
                        if st.button("‎", key="grp_" + str(p_id) + "_" + grp, use_container_width=True,
                                     help="Grupo " + grp + "  (" + str(comp_g) + "/" + str(tot_g) + " pronósticos)"):
                            if st.session_state[key_grp] != grp:
                                st.session_state[key_grp]  = grp
                                st.session_state[key_part] = 0
                            st.rerun()

                grupo_sel    = st.session_state[key_grp]
                partidos_grp = grupos_dict.get(grupo_sel, [])
                total_g      = len(partidos_grp)

                idx = min(st.session_state[key_part], total_g - 1)
                st.session_state[key_part] = idx

                comp_sel, _ = prog_grupo(grupo_sel)
                st.markdown(
                    '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:17px;'
                    'color:#e8c96b;letter-spacing:2px;margin:14px 0 6px 0;">'
                    'GRUPO ' + grupo_sel +
                    ' <span style="font-size:12px;color:#94a3b8;font-family:\'DM Sans\',sans-serif;font-weight:400;">'
                    '· ' + str(comp_sel) + '/' + str(total_g) + ' pronósticos</span></div>',
                    unsafe_allow_html=True
                )

                col_prev, col_ind, col_next = st.columns([1, 4, 1])
                with col_prev:
                    if st.button("◀", key="prev_" + str(p_id), use_container_width=True, disabled=(idx == 0)):
                        st.session_state[key_part] = idx - 1
                        st.rerun()
                with col_ind:
                    st.markdown(
                        '<div style="text-align:center;font-family:\'DM Sans\',sans-serif;'
                        'font-size:13px;color:#94a3b8;padding-top:8px;">'
                        'Partido <strong style="color:#fff;">' + str(idx + 1) + '</strong> de ' + str(total_g) + '</div>',
                        unsafe_allow_html=True
                    )
                with col_next:
                    if st.button("▶", key="next_" + str(p_id), use_container_width=True, disabled=(idx == total_g - 1)):
                        st.session_state[key_part] = idx + 1
                        st.rerun()

                dots_inner = ""
                for n in range(total_g):
                    if n == idx:
                        dots_inner += "<div style='width:20px;height:6px;border-radius:3px;background:#e8c96b'></div>"
                    else:
                        dots_inner += "<div style='width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,0.15)'></div>"
                st.markdown('<div class="dots-row-clickable">' + dots_inner + '</div>', unsafe_allow_html=True)

                # ── Selector directo de partido ──
                with st.expander("🔢 Ir directamente a un partido", expanded=False):
                    n_cols_g = 2
                    filas_g = (total_g + n_cols_g - 1) // n_cols_g
                    for fila in range(filas_g):
                        cols_sel_g = st.columns(n_cols_g)
                        for c in range(n_cols_g):
                            n = fila * n_cols_g + c
                            if n >= total_g:
                                continue
                            with cols_sel_g[c]:
                                partido_n_id, local_n, visitante_n, _fecha_n = partidos_grp[n]
                                tiene_pron_g = (
                                    partido_n_id in pron_dict
                                    and pron_dict[partido_n_id]
                                    and "-" in str(pron_dict[partido_n_id])
                                )
                                ini_l_g = get_iniciales_pais(local_n)
                                ini_v_g = get_iniciales_pais(visitante_n)
                                icono_sel_g = "✅" if tiene_pron_g else "⬜"
                                if st.button(
                                    icono_sel_g + " " + ini_l_g + " vs " + ini_v_g,
                                    key="seldirecto_" + str(p_id) + "_" + str(n),
                                    use_container_width=True,
                                    type="primary" if n == idx else "secondary",
                                    help="Ir al partido " + str(n + 1) + ": " + local_n + " vs " + visitante_n,
                                ):
                                    st.session_state[key_part] = n
                                    st.rerun()

                partido_id, local, visitante, fecha = partidos_grp[idx]
                valor_actual = pron_dict.get(partido_id)

                img_local = get_flag_img(local, size=52)
                img_visit = get_flag_img(visitante, size=52)

                goles_local_guardado = None
                goles_visit_guardado = None
                if valor_actual and "-" in str(valor_actual):
                    partes = str(valor_actual).split("-")
                    try:
                        goles_local_guardado = int(partes[0])
                        goles_visit_guardado = int(partes[1])
                    except ValueError:
                        pass

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
                    '<div class="card-partido-meta">📅 ' + str(fecha) + '</div>'
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
                                     help="Borra todos los pronósticos de grupos de este participante"):
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

        # ══════════════════════════════════════════════════════════════════
        # BOLETA — DIECISEISAVOS DE FINAL
        # ══════════════════════════════════════════════════════════════════
        elif st.session_state[key_fase] == "dieciseisavos":
            resp_16 = sb.table("dieciseisavos").select("*").order("partido_num").execute()
            cruces_16 = resp_16.data

            if not cruces_16:
                st.info("Todavía no se cargaron los cruces de Dieciseisavos de Final.")
            else:
                resp_pron_16 = (
                    sb.table("pronosticos_dieciseisavos")
                    .select("cruce_id, pronostico")
                    .eq("participante_id", p_id)
                    .execute()
                )
                pron_dict_16 = {r["cruce_id"]: r["pronostico"] for r in resp_pron_16.data}

                key_idx16 = "idx16_" + str(p_id)
                if key_idx16 not in st.session_state:
                    st.session_state[key_idx16] = 0

                total_16 = len(cruces_16)
                idx16 = min(st.session_state[key_idx16], total_16 - 1)
                st.session_state[key_idx16] = idx16

                comp_16 = sum(
                    1 for c in cruces_16
                    if c["id"] in pron_dict_16 and pron_dict_16[c["id"]] and "-" in str(pron_dict_16[c["id"]])
                )
                st.markdown(
                    '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:17px;'
                    'color:#e8c96b;letter-spacing:2px;margin:14px 0 6px 0;">'
                    'DIECISEISAVOS DE FINAL'
                    ' <span style="font-size:12px;color:#94a3b8;font-family:\'DM Sans\',sans-serif;font-weight:400;">'
                    '· ' + str(comp_16) + '/' + str(total_16) + ' pronósticos</span></div>',
                    unsafe_allow_html=True
                )

                col_prev16, col_ind16, col_next16 = st.columns([1, 4, 1])
                with col_prev16:
                    if st.button("◀", key="prev16_" + str(p_id), use_container_width=True, disabled=(idx16 == 0)):
                        st.session_state[key_idx16] = idx16 - 1
                        st.rerun()
                with col_ind16:
                    st.markdown(
                        '<div style="text-align:center;font-family:\'DM Sans\',sans-serif;'
                        'font-size:13px;color:#94a3b8;padding-top:8px;">'
                        'Cruce <strong style="color:#fff;">' + str(idx16 + 1) + '</strong> de ' + str(total_16) + '</div>',
                        unsafe_allow_html=True
                    )
                with col_next16:
                    if st.button("▶", key="next16_" + str(p_id), use_container_width=True, disabled=(idx16 == total_16 - 1)):
                        st.session_state[key_idx16] = idx16 + 1
                        st.rerun()

                dots_inner16 = ""
                for n in range(total_16):
                    if n == idx16:
                        dots_inner16 += "<div style='width:20px;height:6px;border-radius:3px;background:#e8c96b'></div>"
                    else:
                        dots_inner16 += "<div style='width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,0.15)'></div>"
                st.markdown('<div class="dots-row-clickable">' + dots_inner16 + '</div>', unsafe_allow_html=True)

                # ── Selector directo de cruce (grilla de botones numerados) ──
                with st.expander("🔢 Ir directamente a un cruce", expanded=False):
                    n_cols16 = 2
                    filas16 = (total_16 + n_cols16 - 1) // n_cols16
                    for fila in range(filas16):
                        cols_sel16 = st.columns(n_cols16)
                        for c in range(n_cols16):
                            n = fila * n_cols16 + c
                            if n >= total_16:
                                continue
                            with cols_sel16[c]:
                                cruce_n = cruces_16[n]
                                tiene_pron16 = (
                                    cruce_n["id"] in pron_dict_16
                                    and pron_dict_16[cruce_n["id"]]
                                    and "-" in str(pron_dict_16[cruce_n["id"]])
                                )
                                nom_l_n = cruce_n.get("equipo_local") or cruce_n.get("origen_local") or cruce_n.get("grupo_local")
                                nom_v_n = cruce_n.get("equipo_visitante") or cruce_n.get("origen_visitante") or cruce_n.get("grupo_visitante")
                                ini_l_n = get_iniciales_pais(nom_l_n) if nom_l_n else "?"
                                ini_v_n = get_iniciales_pais(nom_v_n) if nom_v_n else "?"
                                icono_sel16 = "✅" if tiene_pron16 else "⬜"
                                if st.button(
                                    icono_sel16 + " " + ini_l_n + " vs " + ini_v_n,
                                    key="seldirecto16_" + str(p_id) + "_" + str(n),
                                    use_container_width=True,
                                    type="primary" if n == idx16 else "secondary",
                                    help="Ir al cruce " + str(n + 1) + ": " + (nom_l_n or "Por definir") + " vs " + (nom_v_n or "Por definir"),
                                ):
                                    st.session_state[key_idx16] = n
                                    st.rerun()

                c_actual = cruces_16[idx16]
                cruce_id = c_actual["id"]
                nombre_local = c_actual.get("equipo_local") or c_actual.get("origen_local") or c_actual.get("grupo_local") or "Por definir"
                nombre_visit = c_actual.get("equipo_visitante") or c_actual.get("origen_visitante") or c_actual.get("grupo_visitante") or "Por definir"
                es_placeholder_16 = not (
                    c_actual.get("equipo_local")
                    or c_actual.get("origen_local")
                    or c_actual.get("grupo_local")
                )

                img_local16 = get_flag_img(nombre_local, size=52)
                img_visit16 = get_flag_img(nombre_visit, size=52)

                valor_actual_16 = pron_dict_16.get(cruce_id)
                gl16_guardado, gv16_guardado = None, None
                if valor_actual_16 and "-" in str(valor_actual_16):
                    partes16 = str(valor_actual_16).split("-")
                    try:
                        gl16_guardado = int(partes16[0])
                        gv16_guardado = int(partes16[1])
                    except ValueError:
                        pass

                if gl16_guardado is not None and gv16_guardado is not None:
                    if gl16_guardado > gv16_guardado:
                        badge16 = (
                            '<span style="background:rgba(34,197,94,0.2);color:#4ade80;'
                            'border-radius:20px;padding:3px 14px;font-size:12px;font-weight:700;">'
                            '✅ Avanza ' + nombre_local + '</span>'
                        )
                    elif gv16_guardado > gl16_guardado:
                        badge16 = (
                            '<span style="background:rgba(239,68,68,0.2);color:#f87171;'
                            'border-radius:20px;padding:3px 14px;font-size:12px;font-weight:700;">'
                            '✅ Avanza ' + nombre_visit + '</span>'
                        )
                    else:
                        badge16 = (
                            '<span style="background:rgba(232,201,107,0.18);color:#e8c96b;'
                            'border-radius:20px;padding:3px 14px;font-size:12px;font-weight:700;">'
                            '✅ Empate (120\')</span>'
                        )
                    score_html16 = (
                        '<div class="score-box-wrap">'
                        '<div style="text-align:center;"><div class="score-box">' + str(gl16_guardado) + '</div>'
                        '<div class="score-label">' + nombre_local[:10] + '</div></div>'
                        '<div class="score-dash">-</div>'
                        '<div style="text-align:center;"><div class="score-box">' + str(gv16_guardado) + '</div>'
                        '<div class="score-label">' + nombre_visit[:10] + '</div></div>'
                        '</div>'
                    )
                else:
                    badge16 = (
                        '<span style="background:rgba(100,116,139,0.18);color:#64748b;'
                        'border-radius:20px;padding:3px 14px;font-size:12px;">'
                        '— Sin pronóstico</span>'
                    )
                    score_html16 = (
                        '<div class="score-box-wrap">'
                        '<div style="text-align:center;"><div class="score-box empty">?</div>'
                        '<div class="score-label">' + nombre_local[:10] + '</div></div>'
                        '<div class="score-dash">-</div>'
                        '<div style="text-align:center;"><div class="score-box empty">?</div>'
                        '<div class="score-label">' + nombre_visit[:10] + '</div></div>'
                        '</div>'
                    )

                # Meta info del cruce
                meta_fecha = c_actual.get("fecha", "")
                meta_hora  = c_actual.get("hora", "")
                meta_sede  = c_actual.get("sede", "")
                meta_line1 = "🏆 Partido " + str(c_actual.get("partido_num", ""))
                meta_line2_parts = []
                if meta_fecha:
                    meta_line2_parts.append("📅 " + meta_fecha)
                if meta_hora:
                    meta_line2_parts.append("🕐 " + meta_hora + " (ARG)")
                if meta_sede:
                    meta_line2_parts.append("📍 " + meta_sede)
                meta_line2 = "  &nbsp;·&nbsp;  ".join(meta_line2_parts)

                st.markdown(
                    '<div class="card-partido">'
                    '<div class="card-partido-meta">' + meta_line1 + '</div>'
                    + ('<div class="card-partido-meta" style="font-size:10px;margin-top:-6px;margin-bottom:8px;">' + meta_line2 + '</div>' if meta_line2 else '') +
                    '<div class="card-partido-vs-row">'
                    '<div class="card-equipo">' + img_local16 + '<div class="card-nombre-equipo">' + nombre_local + '</div></div>'
                    '<div class="card-vs">VS</div>'
                    '<div class="card-equipo">' + img_visit16 + '<div class="card-nombre-equipo">' + nombre_visit + '</div></div>'
                    '</div>'
                    + score_html16 +
                    '<div style="text-align:center;margin-top:8px;">' + badge16 + '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

                if editable and not es_placeholder_16:
                    key_gl16 = "gl16_inp_" + str(p_id) + "_" + str(cruce_id)
                    key_gv16 = "gv16_inp_" + str(p_id) + "_" + str(cruce_id)
                    if key_gl16 not in st.session_state:
                        st.session_state[key_gl16] = gl16_guardado if gl16_guardado is not None else 0
                    if key_gv16 not in st.session_state:
                        st.session_state[key_gv16] = gv16_guardado if gv16_guardado is not None else 0

                    col_il, col_g, col_iv, col_sm, col_d = st.columns([3, 1, 3, 3, 1])
                    with col_il:
                        st.markdown(
                            '<div style="font-size:11px;color:#94a3b8;text-align:center;margin-bottom:2px;">'
                            + nombre_local[:14] + '</div>',
                            unsafe_allow_html=True
                        )
                        gl16_val = st.number_input(
                            "⚽ " + nombre_local, min_value=0, max_value=20,
                            value=st.session_state[key_gl16], key=key_gl16, label_visibility="collapsed"
                        )
                    with col_g:
                        st.markdown(
                            '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:28px;'
                            'color:#e8c96b;text-align:center;padding-top:28px;line-height:1;">-</div>',
                            unsafe_allow_html=True
                        )
                    with col_iv:
                        st.markdown(
                            '<div style="font-size:11px;color:#94a3b8;text-align:center;margin-bottom:2px;">'
                            + nombre_visit[:14] + '</div>',
                            unsafe_allow_html=True
                        )
                        gv16_val = st.number_input(
                            "⚽ " + nombre_visit, min_value=0, max_value=20,
                            value=st.session_state[key_gv16], key=key_gv16, label_visibility="collapsed"
                        )
                    with col_sm:
                        st.markdown('<div style="height:26px;"></div>', unsafe_allow_html=True)
                        marcador_nuevo16 = str(gl16_val) + "-" + str(gv16_val)
                        ya_guardado16 = (marcador_nuevo16 == valor_actual_16)
                        tipo_btn16 = "primary" if not ya_guardado16 else "secondary"
                        lbl_btn16  = "✅ Guardado" if ya_guardado16 else "💾 Guardar"
                        if st.button(lbl_btn16, key="save16_" + str(p_id) + "_" + str(cruce_id),
                                     use_container_width=True, type=tipo_btn16, disabled=ya_guardado16):
                            try:
                                existente16 = (
                                    sb.table("pronosticos_dieciseisavos")
                                    .select("id")
                                    .eq("participante_id", p_id)
                                    .eq("cruce_id", cruce_id)
                                    .execute()
                                )
                                if existente16.data:
                                    resp_save16 = sb.table("pronosticos_dieciseisavos")\
                                        .update({"pronostico": marcador_nuevo16})\
                                        .eq("id", existente16.data[0]["id"]).execute()
                                else:
                                    resp_save16 = sb.table("pronosticos_dieciseisavos").insert({
                                        "participante_id": p_id,
                                        "cruce_id":        cruce_id,
                                        "pronostico":      marcador_nuevo16,
                                    }).execute()

                                if not resp_save16.data:
                                    st.error("No se pudo guardar el pronóstico. Supabase no devolvió confirmación (puede ser un problema de permisos / RLS en la tabla pronosticos_dieciseisavos).")
                                else:
                                    st.toast("✅ Pronóstico guardado: " + marcador_nuevo16, icon="🏆")
                                    st.rerun()
                            except Exception as e:
                                st.error("Error al guardar el pronóstico de Dieciseisavos: " + str(e))
                    with col_d:
                        st.markdown('<div style="height:26px;"></div>', unsafe_allow_html=True)
                        if st.button("🗑️", key="deldieci_" + str(p_id) + "_" + str(cruce_id),
                                     help="Borrar pronóstico", use_container_width=True):
                            sb.table("pronosticos_dieciseisavos").delete()\
                                .eq("participante_id", p_id).eq("cruce_id", cruce_id).execute()
                            st.session_state[key_gl16] = 0
                            st.session_state[key_gv16] = 0
                            st.toast("Pronóstico borrado.", icon="🗑️")
                            st.rerun()
                elif es_placeholder_16:
                    st.markdown(
                        '<div style="background:rgba(100,116,139,0.1);border:1px solid rgba(100,116,139,0.2);'
                        'border-radius:10px;padding:10px 16px;text-align:center;margin-top:8px;">'
                        '<span style="font-size:12px;color:#64748b;">'
                        '⏳ Este cruce todavía no tiene equipos confirmados</span></div>',
                        unsafe_allow_html=True
                    )
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
