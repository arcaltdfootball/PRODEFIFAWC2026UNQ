import base64
from datetime import datetime, timezone

import streamlit as st
from database import conectar

st.set_page_config(
    page_title="Chat",
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
        background-image: url('https://raw.githubusercontent.com/arcaltdfootball/PRODEFIFAWC2026UNQ/main/prode_supabase/FIFAchat.jpg');
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
        background: rgba(11,15,25,0.82);
        z-index: 0;
        pointer-events: none;
    }
    [data-testid="stVerticalBlock"] { position: relative; z-index: 1; }

    h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 1px; }

    .main-label {
        font-size: 0.75rem; color: #94a3b8; text-align: center;
        text-transform: uppercase; letter-spacing: 3px; margin-bottom: 4px;
    }
    .main-title {
        font-size: 3.2rem; color: #e8c96b; text-align: center;
        margin-top: 0.2rem; margin-bottom: 1.2rem;
        text-shadow: 0 4px 12px rgba(0,0,0,0.5);
        font-family: 'Bebas Neue', sans-serif;
    }

    /* ── IDENTIDAD DEL USUARIO ── */
    .identidad-box {
        background: rgba(20,30,50,0.6);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(232,201,107,0.2);
        border-radius: 20px;
        padding: 16px 20px;
        max-width: 620px;
        margin: 0 auto 20px;
        box-shadow: 0 12px 32px rgba(0,0,0,0.35);
    }

    /* ── CONTENEDOR DEL CHAT ── */
    .chat-window {
        background: rgba(10,16,30,0.55);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 28px;
        padding: 18px 16px 8px;
        max-width: 620px;
        margin: 0 auto 14px;
        box-shadow: 0 24px 48px rgba(0,0,0,0.4);
        max-height: 560px;
        overflow-y: auto;
    }

    .chat-window::-webkit-scrollbar { width: 6px; }
    .chat-window::-webkit-scrollbar-thumb {
        background: rgba(232,201,107,0.35);
        border-radius: 10px;
    }
    .chat-window::-webkit-scrollbar-track { background: transparent; }

    /* ── BURBUJAS DE MENSAJE ── */
    .msg-row {
        display: flex;
        margin-bottom: 14px;
        gap: 10px;
        align-items: flex-end;
    }
    .msg-row.is-mine { flex-direction: row-reverse; }

    .msg-avatar {
        width: 34px; height: 34px;
        border-radius: 50%;
        background: linear-gradient(135deg, #e8c96b, #b8893a);
        color: #1a1208;
        display: flex; align-items: center; justify-content: center;
        font-family: 'Bebas Neue', sans-serif;
        font-size: 15px;
        flex-shrink: 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }

    .msg-bubble-wrap {
        max-width: 76%;
        display: flex;
        flex-direction: column;
    }
    .msg-row.is-mine .msg-bubble-wrap { align-items: flex-end; }
    .msg-row:not(.is-mine) .msg-bubble-wrap { align-items: flex-start; }

    .msg-nombre {
        font-size: 11px;
        font-weight: 600;
        color: #e8c96b;
        margin-bottom: 3px;
        padding: 0 4px;
        letter-spacing: 0.3px;
    }

    .msg-bubble {
        border-radius: 18px;
        padding: 10px 14px;
        font-size: 0.92rem;
        line-height: 1.45;
        color: #f1f5f9;
        word-wrap: break-word;
        box-shadow: 0 4px 14px rgba(0,0,0,0.25);
    }
    .msg-row:not(.is-mine) .msg-bubble {
        background: rgba(30,41,59,0.92);
        border: 1px solid rgba(255,255,255,0.08);
        border-bottom-left-radius: 4px;
    }
    .msg-row.is-mine .msg-bubble {
        background: linear-gradient(135deg, rgba(232,201,107,0.95), rgba(184,137,58,0.95));
        color: #1a1208;
        font-weight: 500;
        border-bottom-right-radius: 4px;
    }

    .msg-img {
        max-width: 100%;
        border-radius: 14px;
        margin-top: 6px;
        display: block;
        box-shadow: 0 4px 14px rgba(0,0,0,0.3);
    }

    .msg-time {
        font-size: 10px;
        color: rgba(255,255,255,0.35);
        margin-top: 3px;
        padding: 0 4px;
        letter-spacing: 0.3px;
    }
    .msg-row.is-mine .msg-time { color: rgba(26,18,8,0.55); text-align: right; }

    .day-divider {
        text-align: center;
        margin: 18px 0 14px;
        position: relative;
    }
    .day-divider span {
        background: rgba(232,201,107,0.12);
        border: 1px solid rgba(232,201,107,0.25);
        color: #e8c96b;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        padding: 4px 16px;
        border-radius: 20px;
    }

    .chat-empty {
        text-align: center;
        color: #64748b;
        font-size: 0.85rem;
        padding: 40px 10px;
    }

    /* ── BARRA DE ENVÍO ── */
    .send-box {
        background: rgba(20,30,50,0.65);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px;
        padding: 14px 18px 6px;
        max-width: 620px;
        margin: 0 auto 30px;
        box-shadow: 0 16px 32px rgba(0,0,0,0.35);
    }

    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 14px !important;
        color: #f1f5f9 !important;
    }
    [data-testid="stTextInput"] input::placeholder,
    [data-testid="stTextArea"] textarea::placeholder {
        color: rgba(255,255,255,0.35) !important;
    }

    .stButton > button {
        border-radius: 12px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: rgba(255,255,255,0.04) !important;
        border: 1px dashed rgba(232,201,107,0.3) !important;
        border-radius: 14px !important;
    }

    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<p class="main-label">Sala de la Comunidad</p>', unsafe_allow_html=True)
st.markdown('<h1 class="main-title">💬 CHAT DEL PRODE</h1>', unsafe_allow_html=True)

# ── Conexión Supabase ──────────────────────────────────────────────────────────
try:
    sb = conectar()
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE DE LOGIN ADMIN — sidebar (misma password que 02_Participantes.py)
# ══════════════════════════════════════════════════════════════════════════════
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "aleotero")

if "es_admin" not in st.session_state:
    st.session_state.es_admin = False

with st.sidebar:
    st.markdown("---")
    if not st.session_state.es_admin:
        st.markdown(
            '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:18px;'
            'color:#e8c96b;letter-spacing:2px;margin-bottom:8px;">🔐 ACCESO ADMIN</div>',
            unsafe_allow_html=True
        )
        pwd_input = st.text_input("Contraseña", type="password", key="sidebar_pwd_chat", label_visibility="collapsed",
                                  placeholder="Contraseña de admin...")
        if st.button("Ingresar", use_container_width=True, key="btn_login_chat"):
            if pwd_input == ADMIN_PASSWORD:
                st.session_state.es_admin = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
        st.caption("Solo el administrador puede borrar mensajes del chat.")
    else:
        st.markdown(
            '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:16px;'
            'color:#4ade80;letter-spacing:2px;">✅ ADMIN ACTIVO</div>',
            unsafe_allow_html=True
        )
        if st.button("🚪 Cerrar sesión", use_container_width=True, key="btn_logout_chat"):
            st.session_state.es_admin = False
            st.rerun()

es_admin = st.session_state.es_admin

if es_admin:
    st.markdown(
        '<div style="text-align:center;margin-bottom:10px;">'
        '<span style="display:inline-block;background:rgba(34,197,94,0.18);'
        'border:1px solid rgba(34,197,94,0.4);color:#4ade80;border-radius:20px;'
        'padding:3px 14px;font-size:12px;font-weight:600;">'
        '⚡ Modo Administrador — podés borrar mensajes</span></div>',
        unsafe_allow_html=True
    )

# ── Identidad del usuario (se guarda en la sesión, no en la DB) ───────────────
if "chat_nombre" not in st.session_state:
    st.session_state.chat_nombre = ""

st.markdown('<div class="identidad-box">', unsafe_allow_html=True)
col_id1, col_id2 = st.columns([3, 1])
with col_id1:
    nombre_input = st.text_input(
        "Tu nombre o usuario",
        value=st.session_state.chat_nombre,
        placeholder="Escribí cómo querés aparecer en el chat...",
        key="input_nombre_chat"
    )
with col_id2:
    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
    if st.button("✅ Listo", use_container_width=True, key="btn_set_nombre"):
        if nombre_input.strip():
            st.session_state.chat_nombre = nombre_input.strip()
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

mi_nombre = st.session_state.chat_nombre

if not mi_nombre:
    st.info("👆 Ingresá tu nombre arriba para empezar a chatear.")
    st.stop()

# ── Helpers de formato de fecha/hora ───────────────────────────────────────────
MESES = ["enero","febrero","marzo","abril","mayo","junio",
         "julio","agosto","septiembre","octubre","noviembre","diciembre"]
DIAS  = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]

def parsear_fecha(iso_str):
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)

def etiqueta_dia(dt):
    hoy = datetime.now(timezone.utc).date()
    d   = dt.date()
    if d == hoy:
        return "Hoy"
    elif (hoy - d).days == 1:
        return "Ayer"
    else:
        return f"{DIAS[dt.weekday()].capitalize()} {dt.day} de {MESES[dt.month - 1]}"

def hora_str(dt):
    return dt.strftime("%H:%M")

def iniciales(nombre):
    partes = nombre.strip().split()
    if len(partes) >= 2:
        return (partes[0][0] + partes[1][0]).upper()
    return nombre[:2].upper() if nombre else "?"

# ── Cargar mensajes ────────────────────────────────────────────────────────────
resp = sb.table("chat_mensajes").select("*").order("creado_en", desc=False).execute()
mensajes = resp.data

# ── Renderizar ventana de chat ─────────────────────────────────────────────────
if not mensajes:
    chat_html = '<div class="chat-window"><div class="chat-empty">💭 Todavía no hay mensajes. ¡Sé el primero en escribir!</div></div>'
    st.markdown(chat_html, unsafe_allow_html=True)
else:
    partes_html = ['<div class="chat-window" id="chatwin">']
    ultimo_dia = None

    for m in mensajes:
        nombre  = m.get("nombre", "—")
        texto   = m.get("mensaje", "") or ""
        imagen  = m.get("imagen", "") or ""
        dt      = parsear_fecha(m.get("creado_en", ""))
        dia_lbl = etiqueta_dia(dt)

        if dia_lbl != ultimo_dia:
            partes_html.append(f'<div class="day-divider"><span>{dia_lbl}</span></div>')
            ultimo_dia = dia_lbl

        es_mio   = (nombre == mi_nombre)
        row_cls  = "msg-row is-mine" if es_mio else "msg-row"
        avatar   = iniciales(nombre)

        texto_escapado = (
            texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )

        img_html = ""
        if imagen:
            img_html = f'<img src="data:image/jpeg;base64,{imagen}" class="msg-img">'

        partes_html.append(
            f'<div class="{row_cls}">'
            f'<div class="msg-avatar">{avatar}</div>'
            f'<div class="msg-bubble-wrap">'
            f'<div class="msg-nombre">{nombre}</div>'
            f'<div class="msg-bubble">{texto_escapado}{img_html}</div>'
            f'<div class="msg-time">{hora_str(dt)}</div>'
            f'</div></div>'
        )

    partes_html.append('</div>')
    chat_html = "".join(partes_html)
    st.markdown(chat_html, unsafe_allow_html=True)

    # Auto-scroll al final del chat
    st.markdown(
        """
        <script>
        var chatwin = window.parent.document.querySelectorAll('.chat-window');
        if (chatwin.length > 0) {
            var last = chatwin[chatwin.length - 1];
            last.scrollTop = last.scrollHeight;
        }
        </script>
        """,
        unsafe_allow_html=True
    )

# ── Panel de moderación — solo admin ───────────────────────────────────────────
if es_admin and mensajes:
    with st.expander("🛡️ Moderación · Borrar mensajes indebidos"):
        for m in reversed(mensajes):
            msg_id = m.get("id")
            nombre = m.get("nombre", "—")
            texto  = m.get("mensaje", "") or ""
            imagen = m.get("imagen", "") or ""
            dt     = parsear_fecha(m.get("creado_en", ""))

            preview = texto if texto else ("📷 Imagen adjunta" if imagen else "(mensaje vacío)")
            if len(preview) > 60:
                preview = preview[:60] + "…"

            col_mod1, col_mod2 = st.columns([5, 1])
            with col_mod1:
                st.markdown(
                    f"**{nombre}** · {etiqueta_dia(dt)} {hora_str(dt)}  \n"
                    f"<span style='color:#94a3b8;font-size:0.85em;'>{preview}</span>",
                    unsafe_allow_html=True
                )
            with col_mod2:
                if msg_id is not None and st.button("🗑️ Borrar", key=f"del_msg_{msg_id}", use_container_width=True):
                    try:
                        sb.table("chat_mensajes").delete().eq("id", msg_id).execute()
                        st.toast("Mensaje borrado.", icon="🗑️")
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo borrar el mensaje: {e}")
            st.markdown('<hr style="border-top:1px solid rgba(255,255,255,0.08);margin:4px 0;">', unsafe_allow_html=True)

# ── Botón de refrescar mensajes ────────────────────────────────────────────────
col_r1, col_r2, col_r3 = st.columns([2, 1, 2])
with col_r2:
    if st.button("🔄 Actualizar", use_container_width=True, key="btn_refresh_chat"):
        st.rerun()

# ── Barra de envío ──────────────────────────────────────────────────────────────
st.markdown('<div class="send-box">', unsafe_allow_html=True)

if "chat_uploader_key" not in st.session_state:
    st.session_state.chat_uploader_key = 0

mensaje_texto = st.text_area(
    "Mensaje",
    placeholder="Escribí tu mensaje... 😀⚽🔥",
    label_visibility="collapsed",
    height=80,
    key="texto_mensaje_chat"
)

col_f1, col_f2 = st.columns([3, 1])
with col_f1:
    foto_adjunta = st.file_uploader(
        "📎 Adjuntar foto (opcional)",
        type=["jpg", "jpeg", "png", "gif", "webp"],
        key=f"foto_chat_{st.session_state.chat_uploader_key}"
    )
with col_f2:
    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
    enviar = st.button("📤 Enviar", use_container_width=True, type="primary", key="btn_enviar_chat")

st.caption("💡 Tip: podés usar emojis directamente desde el teclado de tu celular o compu.")
st.markdown('</div>', unsafe_allow_html=True)

if enviar:
    texto_limpio = mensaje_texto.strip()
    imagen_b64   = ""

    if foto_adjunta is not None:
        try:
            imagen_bytes = foto_adjunta.read()
            imagen_b64   = base64.b64encode(imagen_bytes).decode()
        except Exception as e:
            st.error(f"No se pudo procesar la imagen: {e}")

    if not texto_limpio and not imagen_b64:
        st.warning("Escribí un mensaje o adjuntá una foto antes de enviar.")
    else:
        try:
            sb.table("chat_mensajes").insert({
                "nombre":  mi_nombre,
                "mensaje": texto_limpio,
                "imagen":  imagen_b64,
            }).execute()
            st.session_state.chat_uploader_key += 1
            st.rerun()
        except Exception as e:
            st.error(f"No se pudo enviar el mensaje: {e}")
