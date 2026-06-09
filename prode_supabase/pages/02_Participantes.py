import os
import streamlit as st
import base64
from database import conectar
from scoring import calcular_puntos

st.set_page_config(
    page_title="Participantes",
    layout="centered"
)

# ── Fondo desde archivo local (opcional, no falla si no existe) ───────────────
def get_base64_image(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

bg_base64 = (
    get_base64_image("fwcup202603.jpg")
    or get_base64_image("assets/fwcup202603.jpg")
    or get_base64_image("fondo_fifa.png")
    or get_base64_image("assets/fondo_fifa.png")
    or get_base64_image("assets/fondo.jpg")
    or get_base64_image("fondo.jpg")
)

fifa_bg_base64 = bg_base64
bg_mime = "image/jpeg"
bg_style = (
    f'url("data:{bg_mime};base64,{bg_base64}")'
    if bg_base64
    else "linear-gradient(135deg, #8b1a1a 0%, #6b0f0f 50%, #8b1a1a 100%)"
)

# ── CSS principal ──────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">

    <style>
    .stApp {{
        background-image: {bg_style};
        background-size: cover;
        background-position: center top;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }}
    .stApp::before {{
        content: "";
        position: fixed;
        inset: 0;
        background: rgba(10, 5, 5, 0.55);
        backdrop-filter: blur(6px);
        -webkit-backdrop-filter: blur(6px);
        z-index: 0;
        pointer-events: none;
    }}
    html, body, [class*="css"], .stMarkdown p {{
        font-family: 'DM Sans', sans-serif !important;
    }}
    h1, h2, h3 {{
        font-family: 'Bebas Neue', sans-serif !important;
        letter-spacing: 1px;
    }}
    .titulo-pagina {{
        font-family: 'Bebas Neue', sans-serif;
        font-size: 42px;
        color: #e8c96b;
        text-align: center;
        letter-spacing: 3px;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.6);
        margin-bottom: 24px;
    }}
    .card-partido {{
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
    }}
    .card-partido-meta {{
        font-size: 11px;
        color: #94a3b8;
        text-align: center;
        letter-spacing: 0.5px;
        margin-bottom: 10px;
    }}
    .card-partido-vs-row {{
        display: flex;
        align-items: center;
        justify-content: space-around;
        gap: 8px;
        margin-bottom: 10px;
    }}
    .card-equipo {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        min-width: 90px;
    }}
    .card-nombre-equipo {{
        font-family: 'DM Sans', sans-serif;
        font-size: 13px;
        font-weight: 600;
        color: #f1f5f9;
        text-align: center;
        letter-spacing: 0.3px;
    }}
    .card-vs {{
        font-family: 'Bebas Neue', sans-serif;
        font-size: 32px;
        color: #e8c96b;
        text-shadow: 0 2px 8px rgba(232,201,107,0.4);
        letter-spacing: 2px;
    }}
    .grupo-header {{
        font-family: 'Bebas Neue', sans-serif;
        font-size: 22px;
        color: #e8c96b;
        border-bottom: 2px solid #e8c96b;
        padding-bottom: 4px;
        margin-top: 20px;
        margin-bottom: 4px;
        letter-spacing: 2px;
    }}
    .part-header {{
        display: flex;
        align-items: center;
        background: rgba(30, 40, 64, 0.90);
        padding: 16px 20px;
        border-radius: 14px;
        margin-top: 10px;
        border-left: 5px solid #e8c96b;
    }}
    .stButton > button {{
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }}
    details summary {{
        font-family: 'Bebas Neue', sans-serif !important;
        font-size: 18px !important;
        letter-spacing: 1px;
    }}
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

st.markdown('<div class="titulo-pagina"> ADMINISTRACIÓN DE PARTICIPANTES</div>', unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────────────────────────
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

def avatar_html(foto_path, nombre, size=65, font_size=24, border=2):
    """Avatar circular con foto o inicial."""
    if foto_path and os.path.exists(foto_path):
        with open(foto_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
        ext = foto_path.rsplit(".", 1)[-1].lower()
        mime = "image/png" if ext == "png" else "image/jpeg"
        return (
            f'<img src="data:{mime};base64,{encoded}" '
            f'style="width:{size}px; height:{size}px; border-radius:50%; '
            f'object-fit:cover; margin-right:15px; '
            f'border:{border}px solid #e8c96b; vertical-align:middle; flex-shrink:0;">'
        )
    inicial = nombre[0].upper() if nombre else "?"
    return (
        f'<div style="width:{size}px; height:{size}px; border-radius:50%; '
        f'background:#1e2840; color:#e8c96b; display:inline-flex; '
        f'align-items:center; justify-content:center; '
        f"font-family:'Bebas Neue'; font-size:{font_size}px; "
        f'margin-right:15px; border:{border}px solid #e8c96b; '
        f'vertical-align:middle; flex-shrink:0;">{inicial}</div>'
    )

def get_flag_img(nombre, size=48):
    url = FLAGS.get(nombre) or FLAGS.get(nombre.strip())
    if url:
        return (
            f'<img src="{url}" width="{size}" height="{size}" '
            f'style="border-radius:50%;border:2px solid rgba(255,255,255,0.2);'
            f'object-fit:cover;display:block;" />'
        )
    return f'<span style="font-size:{size}px;line-height:1;display:block;text-align:center;">🏳️</span>'

# ══════════════════════════════════════════════════════════════════════════════
# AGREGAR PARTICIPANTE
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("➕ Agregar nuevo participante"):
    nombre_nuevo = st.text_input("Nombre del participante", key="input_nombre_nuevo")
    # Nota: fotos de perfil no se suben a Supabase Storage en esta versión
    if st.button("💾 Guardar Participante", use_container_width=True):
        if nombre_nuevo.strip():
            sb.table("participantes").insert({"nombre": nombre_nuevo.strip(), "foto": ""}).execute()
            st.success(f"¡Participante '{nombre_nuevo.strip()}' agregado con éxito!")
            st.rerun()
        else:
            st.error("El nombre no puede estar vacío.")

# ══════════════════════════════════════════════════════════════════════════════
# LISTADO DE PARTICIPANTES
# ══════════════════════════════════════════════════════════════════════════════
resp_p = sb.table("participantes").select("id, nombre, foto").order("nombre").execute()
participantes = resp_p.data

if not participantes:
    st.info("Aún no se han registrado participantes. Despliega la pestaña superior para añadir uno.")
    st.stop()

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<h3 style="color:#e8c96b; font-family:\'Bebas Neue\',sans-serif; letter-spacing:2px;">📋 PARTICIPANTES</h3>', unsafe_allow_html=True)

if "part_expandido" not in st.session_state:
    st.session_state.part_expandido = None
if "confirmar_eliminar" not in st.session_state:
    st.session_state.confirmar_eliminar = None

for p in participantes:
    p_id  = p["id"]
    p_nom = p["nombre"]
    p_foto = p.get("foto") or ""
    puntos = calcular_puntos(p_id)
    expandido   = st.session_state.part_expandido == p_id
    confirmando = st.session_state.confirmar_eliminar == p_id

    col_av, col_info, col_btn, col_del = st.columns([1, 5, 2, 1])

    with col_av:
        av = avatar_html(p_foto, p_nom, size=50, font_size=20)
        st.markdown(f'<div style="padding-top:6px;">{av}</div>', unsafe_allow_html=True)

    with col_info:
        st.markdown(
            f"""
            <div style="padding:6px 0;">
                <div style="font-family:'Bebas Neue',sans-serif; font-size:20px; color:#fff; letter-spacing:1px;">{p_nom.upper()}</div>
                <div style="font-size:13px; color:#e8c96b;">⭐ {puntos} pts</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_btn:
        label_btn = "▲ Cerrar" if expandido else "📝 Boleta"
        if st.button(label_btn, key=f"toggle_{p_id}", use_container_width=True):
            st.session_state.part_expandido = None if expandido else p_id
            st.session_state.confirmar_eliminar = None
            st.rerun()

    with col_del:
        if confirmando:
            st.markdown(
                '<div style="font-size:10px;color:#f87171;text-align:center;padding-top:2px;">¿Eliminar?</div>',
                unsafe_allow_html=True
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✓", key=f"confirm_del_{p_id}", use_container_width=True):
                    sb.table("pronosticos").delete().eq("participante_id", p_id).execute()
                    sb.table("participantes").delete().eq("id", p_id).execute()
                    st.session_state.confirmar_eliminar = None
                    if st.session_state.part_expandido == p_id:
                        st.session_state.part_expandido = None
                    st.toast(f"'{p_nom}' eliminado.", icon="🗑️")
                    st.rerun()
            with c2:
                if st.button("✗", key=f"cancel_del_{p_id}", use_container_width=True):
                    st.session_state.confirmar_eliminar = None
                    st.rerun()
        else:
            st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
            if st.button("✕", key=f"del_part_{p_id}", use_container_width=True):
                st.session_state.confirmar_eliminar = p_id
                st.rerun()

    st.markdown('<hr style="border:none; border-top:1px solid rgba(255,255,255,0.08); margin:2px 0 6px 0;">', unsafe_allow_html=True)

    # ── Panel expandido ────────────────────────────────────────────────────────
    if expandido:
        av_grande = avatar_html(p_foto, p_nom, size=65, font_size=26)
        st.markdown(
            f"""
            <div class="part-header">
                {av_grande}
                <div>
                    <div style="font-family:'Bebas Neue',sans-serif; font-size:32px; color:#e8c96b; margin:0;">{p_nom.upper()}</div>
                    <div style="font-size:14px; color:#cbd5e1;">⭐ Puntos actuales: <strong style="color:#e8c96b;">{puntos}</strong></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            '<div style="font-family:\'Bebas Neue\',sans-serif; font-size:26px; color:#fff; '
            'letter-spacing:2px; margin-top:18px; margin-bottom:4px;">📝 BOLETA DE PRONÓSTICOS</div>',
            unsafe_allow_html=True
        )

        # Cargar partidos desde Supabase
        resp_todos = sb.table("partidos").select("id, local, visitante, fecha, grupo").order("grupo").order("fecha").execute()
        todos_partidos = resp_todos.data

        if not todos_partidos:
            st.info("No hay partidos cargados en la base de datos.")
        else:
            # Agrupar partidos
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

            # Cargar todos los pronósticos del participante de una sola vez
            resp_pron = (
                sb.table("pronosticos")
                .select("partido_id, pronostico")
                .eq("participante_id", p_id)
                .execute()
            )
            pron_dict = {r["partido_id"]: r["pronostico"] for r in resp_pron.data}

            key_grp  = f"grp_sel_{p_id}"
            key_part = f"part_idx_{p_id}"
            if key_grp  not in st.session_state:
                st.session_state[key_grp]  = grupos_ordenados[0]
            if key_part not in st.session_state:
                st.session_state[key_part] = 0

            # ── Roller de grupos ───────────────────────────────────────────────
            def prog_grupo(g):
                pts = grupos_dict.get(g, [])
                comp = sum(1 for (pid2, *_) in pts if pid2 in pron_dict)
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
                        f"""
                        <div style="background:{bg};border:2px solid {borde};border-radius:10px;
                            padding:6px 4px 5px 4px;text-align:center;margin-bottom:-8px;">
                            <div style="font-family:'Bebas Neue',sans-serif;font-size:18px;
                                color:{color_letra};letter-spacing:1px;line-height:1.1;">{grp}</div>
                            <div style="font-size:9px;color:#64748b;font-family:'DM Sans',sans-serif;
                                margin-top:1px;">{comp_g}/{tot_g}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if st.button("‎", key=f"grp_{p_id}_{grp}", use_container_width=True,
                                 help=f"Grupo {grp}  ({comp_g}/{tot_g} pronósticos)"):
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
                f'<div style="font-family:\'Bebas Neue\',sans-serif;font-size:17px;'
                f'color:#e8c96b;letter-spacing:2px;margin:14px 0 6px 0;">'
                f'GRUPO {grupo_sel} '
                f'<span style="font-size:12px;color:#94a3b8;font-family:\'DM Sans\',sans-serif;font-weight:400;">'
                f'· {comp_sel}/{total_g} pronósticos</span></div>',
                unsafe_allow_html=True
            )

            # ── Navegación de partidos ─────────────────────────────────────────
            col_prev, col_ind, col_next = st.columns([1, 4, 1])
            with col_prev:
                if st.button("◀", key=f"prev_{p_id}", use_container_width=True, disabled=(idx == 0)):
                    st.session_state[key_part] = idx - 1
                    st.rerun()
            with col_ind:
                st.markdown(
                    f'<div style="text-align:center;font-family:\'DM Sans\',sans-serif;'
                    f'font-size:13px;color:#94a3b8;padding-top:8px;">'
                    f'Partido <strong style="color:#fff;">{idx+1}</strong> de {total_g}</div>',
                    unsafe_allow_html=True
                )
            with col_next:
                if st.button("▶", key=f"next_{p_id}", use_container_width=True, disabled=(idx == total_g - 1)):
                    st.session_state[key_part] = idx + 1
                    st.rerun()

            # ── Tarjeta del partido actual ─────────────────────────────────────
            partido_id, local, visitante, fecha = partidos_grp[idx]
            valor_actual = pron_dict.get(partido_id)

            img_local = get_flag_img(local,  size=52)
            img_visit = get_flag_img(visitante, size=52)

            if valor_actual == "1":
                badge = (f'<span style="background:rgba(34,197,94,0.25);color:#4ade80;'
                         f'border-radius:20px;padding:3px 14px;font-size:12px;font-weight:700;">'
                         f'✅ 1 · {local}</span>')
            elif valor_actual == "X":
                badge = ('<span style="background:rgba(232,201,107,0.25);color:#e8c96b;'
                         'border-radius:20px;padding:3px 14px;font-size:12px;font-weight:700;">'
                         '✅ X · Empate</span>')
            elif valor_actual == "2":
                badge = (f'<span style="background:rgba(239,68,68,0.25);color:#f87171;'
                         f'border-radius:20px;padding:3px 14px;font-size:12px;font-weight:700;">'
                         f'✅ 2 · {visitante}</span>')
            else:
                badge = ('<span style="background:rgba(100,116,139,0.18);color:#64748b;'
                         'border-radius:20px;padding:3px 14px;font-size:12px;">'
                         '— Sin pronóstico</span>')

            st.markdown(
                f"""
                <div class="card-partido">
                    <div class="card-partido-meta">📅 {fecha}</div>
                    <div class="card-partido-vs-row">
                        <div class="card-equipo">
                            {img_local}
                            <div class="card-nombre-equipo">{local}</div>
                        </div>
                        <div class="card-vs">VS</div>
                        <div class="card-equipo">
                            {img_visit}
                            <div class="card-nombre-equipo">{visitante}</div>
                        </div>
                    </div>
                    <div style="text-align:center;margin-top:6px;">{badge}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # ── Botones de pronóstico ──────────────────────────────────────────
            lbl1  = f"✅ 1 · {local}"     if valor_actual == "1" else f"1 · {local}"
            lblx  = "✅ X · Empate"       if valor_actual == "X" else "X · Empate"
            lbl2  = f"✅ 2 · {visitante}" if valor_actual == "2" else f"2 · {visitante}"
            tipo1 = "primary"   if valor_actual == "1" else "secondary"
            tipox = "primary"   if valor_actual == "X" else "secondary"
            tipo2 = "primary"   if valor_actual == "2" else "secondary"

            col1b, colxb, col2b, col_del2 = st.columns([3, 3, 3, 1])

            def _guardar_pron(pid, nuevo_val):
                """Upsert o borrar pronóstico."""
                if nuevo_val:
                    sb.table("pronosticos").upsert(
                        {"participante_id": p_id, "partido_id": pid, "pronostico": nuevo_val},
                        on_conflict="participante_id,partido_id"
                    ).execute()
                else:
                    sb.table("pronosticos").delete().eq("participante_id", p_id).eq("partido_id", pid).execute()

            with col1b:
                if st.button(lbl1, key=f"btn1_{p_id}_{partido_id}", use_container_width=True, type=tipo1):
                    _guardar_pron(partido_id, "1" if valor_actual != "1" else None)
                    st.rerun()

            with colxb:
                if st.button(lblx, key=f"btnx_{p_id}_{partido_id}", use_container_width=True, type=tipox):
                    _guardar_pron(partido_id, "X" if valor_actual != "X" else None)
                    st.rerun()

            with col2b:
                if st.button(lbl2, key=f"btn2_{p_id}_{partido_id}", use_container_width=True, type=tipo2):
                    _guardar_pron(partido_id, "2" if valor_actual != "2" else None)
                    st.rerun()

            with col_del2:
                st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{p_id}_{partido_id}",
                             help=f"Resetear {local} vs {visitante}", use_container_width=True):
                    sb.table("pronosticos").delete().eq("participante_id", p_id).eq("partido_id", partido_id).execute()
                    st.toast("Pronóstico reseteado.", icon="🗑️")
                    st.rerun()

            # ── Resetear boleta completa ───────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            _, col_reset = st.columns([3, 1])
            with col_reset:
                if st.button("🗑️ Resetear Boleta", key=f"reset_total_{p_id}",
                             use_container_width=True,
                             help="Borra todos los pronósticos de este participante"):
                    sb.table("pronosticos").delete().eq("participante_id", p_id).execute()
                    st.toast(f"Boleta de {p_nom} reseteada.", icon="🔄")
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
