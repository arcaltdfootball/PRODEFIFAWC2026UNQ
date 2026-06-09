import os
import streamlit as st
import base64
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

    /* CARD PARTICIPANTE */
    .part-row-card {
        background: rgba(20, 28, 50, 0.82);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 14px 18px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 14px;
    }

    .part-number {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 28px;
        color: rgba(232,201,107,0.35);
        min-width: 32px;
        text-align: center;
        line-height: 1;
    }

    .part-nombre {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 22px;
        color: #fff;
        letter-spacing: 1px;
        line-height: 1.1;
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

    /* CARD PARTIDO */
    .card-partido {
        background: rgba(28, 36, 60, 0.96);
        border-radius: 14px;
        padding: 18px 20px 14px 20px;
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
        margin-bottom: 10px;
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

    /* PANEL EXPANDIDO */
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

    /* LOGIN ADMIN */
    .login-box {
        background: rgba(20, 28, 50, 0.92);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(232,201,107,0.25);
        border-radius: 18px;
        padding: 28px 32px 24px 32px;
        max-width: 380px;
        margin: 0 auto 32px auto;
        text-align: center;
    }
    .login-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 22px;
        color: #e8c96b;
        letter-spacing: 3px;
        margin-bottom: 4px;
    }
    .login-sub {
        font-size: 12px;
        color: #64748b;
        margin-bottom: 18px;
        letter-spacing: 0.5px;
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
# BLOQUE DE LOGIN ADMIN — sidebar
# ══════════════════════════════════════════════════════════════════════════════
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "prode2026")  # definí ADMIN_PASSWORD en secrets.toml

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
        pwd_input = st.text_input("Contraseña", type="password", key="sidebar_pwd", label_visibility="collapsed",
                                  placeholder="Contraseña de admin...")
        if st.button("Ingresar", use_container_width=True, key="btn_login"):
            if pwd_input == ADMIN_PASSWORD:
                st.session_state.es_admin = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
        st.caption("Solo el administrador puede cargar pronósticos.")
    else:
        st.markdown(
            '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:16px;'
            'color:#4ade80;letter-spacing:2px;">✅ ADMIN ACTIVO</div>',
            unsafe_allow_html=True
        )
        if st.button("🚪 Cerrar sesión", use_container_width=True, key="btn_logout"):
            st.session_state.es_admin = False
            st.rerun()

es_admin = st.session_state.es_admin

# Badge de modo visible bajo el título
if es_admin:
    st.markdown('<div style="text-align:center;margin-bottom:10px;"><span class="badge-admin">⚡ Modo Administrador — edición habilitada</span></div>', unsafe_allow_html=True)
else:
    st.markdown(
        '<div class="readonly-notice">'
        '👁️ Modo visitante — podés ver los pronósticos pero solo el admin puede modificarlos'
        '</div>',
        unsafe_allow_html=True
    )

# ── FLAGS ──────────────────────────────────────────────────────────────────────
FLAGS = {
    "Alemania":"https://hatscripts.github.io/circle-flags/flags/de.svg",
    "Arabia Saudi":"https://hatscripts.github.io/circle-flags/flags/sa.svg",
    "Argelia":"https://hatscripts.github.io/circle-flags/flags/dz.svg",
    "Argentina":"https://hatscripts.github.io/circle-flags/flags/ar.svg",
    "Australia":"https://hatscripts.github.io/circle-flags/flags/au.svg",
    "Austria":"https://hatscripts.github.io/circle-flags/flags/at.svg",
    "Belgica":"https://hatscripts.github.io/circle-flags/flags/be.svg",
    "Bosnia y Herzegovina":"https://hatscripts.github.io/circle-flags/flags/ba.svg",
    "Brasil":"https://hatscripts.github.io/circle-flags/flags/br.svg",
    "Cabo Verde":"https://hatscripts.github.io/circle-flags/flags/cv.svg",
    "Canada":"https://hatscripts.github.io/circle-flags/flags/ca.svg",
    "Catar":"https://hatscripts.github.io/circle-flags/flags/qa.svg",
    "Colombia":"https://hatscripts.github.io/circle-flags/flags/co.svg",
    "Costa de Marfil":"https://hatscripts.github.io/circle-flags/flags/ci.svg",
    "Croacia":"https://hatscripts.github.io/circle-flags/flags/hr.svg",
    "Curazao":"https://hatscripts.github.io/circle-flags/flags/cw.svg",
    "Ecuador":"https://hatscripts.github.io/circle-flags/flags/ec.svg",
    "Egipto":"https://hatscripts.github.io/circle-flags/flags/eg.svg",
    "Escocia":"https://hatscripts.github.io/circle-flags/flags/gb-sct.svg",
    "Espana":"https://hatscripts.github.io/circle-flags/flags/es.svg",
    "España":"https://hatscripts.github.io/circle-flags/flags/es.svg",
    "Estados Unidos":"https://hatscripts.github.io/circle-flags/flags/us.svg",
    "Francia":"https://hatscripts.github.io/circle-flags/flags/fr.svg",
    "Ghana":"https://hatscripts.github.io/circle-flags/flags/gh.svg",
    "Haiti":"https://hatscripts.github.io/circle-flags/flags/ht.svg",
    "Inglaterra":"https://hatscripts.github.io/circle-flags/flags/gb-eng.svg",
    "Irak":"https://hatscripts.github.io/circle-flags/flags/iq.svg",
    "Iran":"https://hatscripts.github.io/circle-flags/flags/ir.svg",
    "RI de Iran":"https://hatscripts.github.io/circle-flags/flags/ir.svg",
    "Japon":"https://hatscripts.github.io/circle-flags/flags/jp.svg",
    "Jordania":"https://hatscripts.github.io/circle-flags/flags/jo.svg",
    "Marruecos":"https://hatscripts.github.io/circle-flags/flags/ma.svg",
    "Mexico":"https://hatscripts.github.io/circle-flags/flags/mx.svg",
    "Noruega":"https://hatscripts.github.io/circle-flags/flags/no.svg",
    "Nueva Zelanda":"https://hatscripts.github.io/circle-flags/flags/nz.svg",
    "Paises Bajos":"https://hatscripts.github.io/circle-flags/flags/nl.svg",
    "Panama":"https://hatscripts.github.io/circle-flags/flags/pa.svg",
    "Paraguay":"https://hatscripts.github.io/circle-flags/flags/py.svg",
    "Portugal":"https://hatscripts.github.io/circle-flags/flags/pt.svg",
    "RD Congo":"https://hatscripts.github.io/circle-flags/flags/cd.svg",
    "Republica Checa":"https://hatscripts.github.io/circle-flags/flags/cz.svg",
    "Republica de Corea":"https://hatscripts.github.io/circle-flags/flags/kr.svg",
    "Senegal":"https://hatscripts.github.io/circle-flags/flags/sn.svg",
    "Sudafrica":"https://hatscripts.github.io/circle-flags/flags/za.svg",
    "Suecia":"https://hatscripts.github.io/circle-flags/flags/se.svg",
    "Suiza":"https://hatscripts.github.io/circle-flags/flags/ch.svg",
    "Tunez":"https://hatscripts.github.io/circle-flags/flags/tn.svg",
    "Turquia":"https://hatscripts.github.io/circle-flags/flags/tr.svg",
    "Uruguay":"https://hatscripts.github.io/circle-flags/flags/uy.svg",
    "Uzbekistan":"https://hatscripts.github.io/circle-flags/flags/uz.svg",
}

# ── Helpers ────────────────────────────────────────────────────────────────────
def avatar_html_from_bytes(foto_bytes, nombre, size=65, font_size=24, border=2):
    """Avatar circular con bytes de imagen o inicial."""
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

def get_flag_img(nombre, size=48):
    url = FLAGS.get(nombre) or FLAGS.get(nombre.strip())
    if url:
        return (
            '<img src="' + url + '" width="' + str(size) + '" height="' + str(size) + '" '
            'style="border-radius:50%;border:2px solid rgba(255,255,255,0.2);'
            'object-fit:cover;display:block;" />'
        )
    return '<span style="font-size:' + str(size) + 'px;line-height:1;display:block;text-align:center;">🏳️</span>'

# ── Guardar pronóstico (solo admin) ───────────────────────────────────────────
def guardar_pron(p_id, partido_id, nuevo_val):
    if not es_admin:
        st.warning("Solo el administrador puede modificar pronósticos.")
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
            if existente.data:
                row_id = existente.data[0]["id"]
                sb.table("pronosticos")\
                    .update({"pronostico": nuevo_val})\
                    .eq("id", row_id)\
                    .execute()
            else:
                sb.table("pronosticos").insert({
                    "participante_id": p_id,
                    "partido_id":      partido_id,
                    "pronostico":      nuevo_val
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
        foto_nueva   = st.file_uploader("Foto del participante (opcional)", type=["jpg","jpeg","png"], key="foto_nueva")
        if st.button("💾 Guardar Participante", use_container_width=True):
            if nombre_nuevo.strip():
                foto_b64 = ""
                if foto_nueva is not None:
                    foto_bytes = foto_nueva.read()
                    foto_b64   = base64.b64encode(foto_bytes).decode()
                sb.table("participantes").insert({
                    "nombre": nombre_nuevo.strip(),
                    "foto":   foto_b64
                }).execute()
                st.success("¡Participante '" + nombre_nuevo.strip() + "' agregado con éxito!")
                st.rerun()
            else:
                st.error("El nombre no puede estar vacío.")

# ══════════════════════════════════════════════════════════════════════════════
# LISTADO DE PARTICIPANTES
# ══════════════════════════════════════════════════════════════════════════════
resp_p = sb.table("participantes").select("id, nombre, foto").order("nombre").execute()
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

for numero, p in enumerate(participantes, start=1):
    p_id   = p["id"]
    p_nom  = p["nombre"]
    p_foto_b64 = p.get("foto") or ""
    foto_bytes = base64.b64decode(p_foto_b64) if p_foto_b64 else None
    puntos = calcular_puntos(p_id)
    expandido   = st.session_state.part_expandido == p_id
    confirmando = st.session_state.confirmar_eliminar == p_id

    av_small = avatar_html_from_bytes(foto_bytes, p_nom, size=50, font_size=20)

    # ── Fila de participante ───────────────────────────────────────────────────
    # Admin: muestra botón eliminar | Visitante: no muestra
    if es_admin:
        col_av, col_info, col_pts, col_btn, col_del = st.columns([1, 4, 2, 2, 1])
    else:
        col_av, col_info, col_pts, col_btn = st.columns([1, 4, 2, 2])
        col_del = None

    with col_av:
        st.markdown(
            '<div style="padding-top:6px;display:flex;align-items:center;gap:6px;">'
            '<span class="part-number">' + str(numero) + '</span>'
            + av_small +
            '</div>',
            unsafe_allow_html=True
        )

    with col_info:
        st.markdown(
            '<div style="padding:6px 0;">'
            '<div style="font-family:\'Bebas Neue\',sans-serif;font-size:20px;color:#fff;letter-spacing:1px;">'
            + p_nom.upper() +
            '</div></div>',
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

    # Botón eliminar solo para admin
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

        # Cargar partidos
        resp_todos = sb.table("partidos").select("id, local, visitante, fecha, grupo").order("grupo").order("fecha").execute()
        todos_partidos = resp_todos.data

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

            # Cargar pronósticos del participante
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
                comp = sum(1 for (pid2, *_) in pts if pid2 in pron_dict)
                return comp, len(pts)

            # ── Tabs de grupos ─────────────────────────────────────────────────
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

            # ── Navegación de partidos ─────────────────────────────────────────
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

            # ── Tarjeta del partido actual ─────────────────────────────────────
            partido_id, local, visitante, fecha = partidos_grp[idx]
            valor_actual = pron_dict.get(partido_id)

            img_local = get_flag_img(local,  size=52)
            img_visit = get_flag_img(visitante, size=52)

            if valor_actual == "1":
                badge = (
                    '<span style="background:rgba(34,197,94,0.25);color:#4ade80;'
                    'border-radius:20px;padding:3px 14px;font-size:12px;font-weight:700;">'
                    '✅ 1 · ' + local + '</span>'
                )
            elif valor_actual == "X":
                badge = (
                    '<span style="background:rgba(232,201,107,0.25);color:#e8c96b;'
                    'border-radius:20px;padding:3px 14px;font-size:12px;font-weight:700;">'
                    '✅ X · Empate</span>'
                )
            elif valor_actual == "2":
                badge = (
                    '<span style="background:rgba(239,68,68,0.25);color:#f87171;'
                    'border-radius:20px;padding:3px 14px;font-size:12px;font-weight:700;">'
                    '✅ 2 · ' + visitante + '</span>'
                )
            else:
                badge = (
                    '<span style="background:rgba(100,116,139,0.18);color:#64748b;'
                    'border-radius:20px;padding:3px 14px;font-size:12px;">'
                    '— Sin pronóstico</span>'
                )

            st.markdown(
                '<div class="card-partido">'
                '<div class="card-partido-meta">📅 ' + str(fecha) + '</div>'
                '<div class="card-partido-vs-row">'
                '<div class="card-equipo">' + img_local + '<div class="card-nombre-equipo">' + local + '</div></div>'
                '<div class="card-vs">VS</div>'
                '<div class="card-equipo">' + img_visit + '<div class="card-nombre-equipo">' + visitante + '</div></div>'
                '</div>'
                '<div style="text-align:center;margin-top:6px;">' + badge + '</div>'
                '</div>',
                unsafe_allow_html=True
            )

            # ── Botones de pronóstico — solo admin ────────────────────────────
            if es_admin:
                lbl1  = "✅ 1 · " + local     if valor_actual == "1" else "1 · " + local
                lblx  = "✅ X · Empate"        if valor_actual == "X" else "X · Empate"
                lbl2  = "✅ 2 · " + visitante  if valor_actual == "2" else "2 · " + visitante
                tipo1 = "primary"   if valor_actual == "1" else "secondary"
                tipox = "primary"   if valor_actual == "X" else "secondary"
                tipo2 = "primary"   if valor_actual == "2" else "secondary"

                col1b, colxb, col2b, col_del2 = st.columns([3, 3, 3, 1])

                with col1b:
                    if st.button(lbl1, key="btn1_" + str(p_id) + "_" + str(partido_id),
                                 use_container_width=True, type=tipo1):
                        nuevo = "1" if valor_actual != "1" else None
                        if guardar_pron(p_id, partido_id, nuevo):
                            st.rerun()

                with colxb:
                    if st.button(lblx, key="btnx_" + str(p_id) + "_" + str(partido_id),
                                 use_container_width=True, type=tipox):
                        nuevo = "X" if valor_actual != "X" else None
                        if guardar_pron(p_id, partido_id, nuevo):
                            st.rerun()

                with col2b:
                    if st.button(lbl2, key="btn2_" + str(p_id) + "_" + str(partido_id),
                                 use_container_width=True, type=tipo2):
                        nuevo = "2" if valor_actual != "2" else None
                        if guardar_pron(p_id, partido_id, nuevo):
                            st.rerun()

                with col_del2:
                    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
                    if st.button("🗑️", key="del_" + str(p_id) + "_" + str(partido_id),
                                 help="Resetear " + local + " vs " + visitante,
                                 use_container_width=True):
                        sb.table("pronosticos").delete()\
                            .eq("participante_id", p_id)\
                            .eq("partido_id", partido_id)\
                            .execute()
                        st.toast("Pronóstico reseteado.", icon="🗑️")
                        st.rerun()

                # ── Resetear boleta completa ───────────────────────────────────
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
                # Visitante: mensaje informativo en lugar de botones
                st.markdown(
                    '<div style="background:rgba(100,116,139,0.1);border:1px solid rgba(100,116,139,0.2);'
                    'border-radius:10px;padding:10px 16px;text-align:center;margin-top:8px;">'
                    '<span style="font-size:12px;color:#64748b;">'
                    '🔒 Iniciá sesión como admin para modificar pronósticos'
                    '</span></div>',
                    unsafe_allow_html=True
                )

    st.markdown("<br>", unsafe_allow_html=True)
