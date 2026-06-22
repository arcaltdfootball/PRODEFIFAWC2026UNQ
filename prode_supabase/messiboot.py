"""
MESSIBOOT — Asistente flotante del PRODE FIFA WORLD CUP 2026
==============================================================
Widget de chat flotante (burbuja abajo a la derecha, visible en todo
el sitio) que responde EXCLUSIVAMENTE sobre el sitio y el prode,
usando datos reales de Supabase (partidos, resultados, ranking,
pronósticos) y la API gratuita de Groq (Llama 3.3 70B) como motor.

ARQUITECTURA — por qué NO usa components.html:
Los componentes custom de Streamlit (components.html) corren dentro de
un <iframe sandboxed>. Ese sandbox bloquea explícitamente cualquier
intento del iframe de navegar a la página padre (window.parent.location,
formularios target="_parent", etc. — todo queda bloqueado igual con el
error "Unsafe attempt to initiate navigation... sandboxed, and is
therefore disallowed from navigating its ancestors"). Por eso este
widget usa SOLO st.markdown para la parte visual (vive en el DOM
principal, sin iframe, sin sandbox) y widgets nativos de Streamlit
(st.text_input / st.button) para la interacción real — esos sí pueden
disparar un rerun de verdad porque no están sandboxeados.

USO — pegar esta única línea al inicio de app.py y de cada página
en pages/, después de los imports de Streamlit:

    from messiboot import render_messiboot; render_messiboot()

CONFIGURACIÓN — definir la API key de Groq en .streamlit/secrets.toml:

    GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxxxxxxxxxx"

(o como variable de entorno GROQ_API_KEY). Se consigue gratis en
https://console.groq.com/keys
"""
import json
import base64
import os
import streamlit as st
from database import conectar

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
HIST_KEY = "messiboot_historial"
OPEN_KEY = "messiboot_abierto"

# ── Avatar en base64 (imagen del robot MessiBoot) ─────────────────────────────
def _get_avatar_b64() -> str:
    """Carga la imagen del avatar de MessiBoot como base64."""
    # Busca la imagen en el mismo directorio que este archivo
    img_path = os.path.join(os.path.dirname(__file__), "messiboot_avatar.png")
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


# ──────────────────────────────────────────────────────────────────────────
# 1. Recolección de datos reales del prode (Supabase)
#    ► Ahora consulta TODOS los datos necesarios: participantes, partidos,
#      resultados, pronósticos individuales y rankings calculados en vivo,
#      igual que lo hacen las páginas Resultados, Ranking, Pronósticos y
#      Dashboard. Así MessiBoot reconoce a TODOS los participantes y puede
#      responder con precisión sobre cualquier dato del sitio.
# ──────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def _obtener_contexto_prode() -> str:
    """
    Arma un resumen compacto y actualizado del estado real del prode:
    reglas de puntaje, fixture/resultados, ranking y participantes.
    Se cachea 2 minutos para no saturar Supabase en cada mensaje.
    Consulta las mismas tablas que 01_Resultados, 03_Ranking, 05_Dashboard
    y 06_Pronosticos para tener datos completos y evitar errores de
    "participante no reconocido".
    """
    try:
        sb = conectar()
    except Exception as e:
        return f"(No se pudo conectar a la base de datos: {e})"

    partes = [
        "REGLAS DEL PRODE:\n"
        "- Cada participante pronostica el signo (1 = gana local, "
        "X = empate, 2 = gana visitante) de cada partido del Mundial.\n"
        "- Acertar el signo exacto otorga 3 puntos.\n"
        "- No se otorgan puntos por marcador exacto, solo por signo (1/X/2).\n"
        "- Hay 72 partidos en total en el torneo."
    ]

    try:
        # ── Participantes (TODOS, igual que 02_Participantes y 05_Dashboard) ──
        participantes_resp = sb.table("participantes").select("id, nombre").execute()
        participantes = participantes_resp.data or []

        # ── Partidos completos (igual que 01_Resultados) ──────────────────────
        partidos_resp = sb.table("partidos").select(
            "id, grupo, fecha, hora, sede, local, visitante, resultado"
        ).order("grupo").order("fecha").order("hora").execute()
        partidos = partidos_resp.data or []

        # ── Pronósticos de TODOS los participantes (igual que 06_Pronosticos) ─
        # Traemos todo de una sola vez para calcular ranking y pronósticos individuales
        pronosticos_resp = sb.table("pronosticos").select(
            "participante_id, partido_id, pronostico"
        ).execute()
        pronosticos = pronosticos_resp.data or []

        # ── Índices rápidos ───────────────────────────────────────────────────
        partidos_por_id = {p["id"]: p for p in partidos}
        participantes_por_id = {p["id"]: p["nombre"] for p in participantes}

        # ── Calcular puntos, aciertos y disputados por participante ────────────
        # (misma lógica que 03_Ranking y 05_Dashboard)
        puntos_pp, aciertos_pp, disputados_pp = {}, {}, {}
        pron_por_participante = {}  # partido_id → pronostico, por participante

        for pr in pronosticos:
            pid = pr["participante_id"]
            partido = partidos_por_id.get(pr["partido_id"])
            if not partido:
                continue
            resultado = partido.get("resultado") or ""

            # Agrupar pronósticos por participante para detalle individual
            if pid not in pron_por_participante:
                pron_por_participante[pid] = {}
            pron_por_participante[pid][pr["partido_id"]] = pr.get("pronostico", "")

            if not resultado:
                continue
            disputados_pp[pid] = disputados_pp.get(pid, 0) + 1
            if resultado == pr.get("pronostico"):
                puntos_pp[pid] = puntos_pp.get(pid, 0) + 3
                aciertos_pp[pid] = aciertos_pp.get(pid, 0) + 1

        # ── Lista completa de participantes con su estado de boleta ───────────
        nombres_participantes = [p["nombre"] for p in participantes]
        partes.append(
            "PARTICIPANTES REGISTRADOS (" + str(len(participantes)) + " en total):\n" +
            "\n".join(f"- {n}" for n in nombres_participantes)
        )

        # ── Ranking calculado en vivo (igual que 03_Ranking) ─────────────────
        ranking = sorted(
            (
                {
                    "nombre": p["nombre"],
                    "id": p["id"],
                    "puntos": puntos_pp.get(p["id"], 0),
                    "aciertos": aciertos_pp.get(p["id"], 0),
                    "disputados": disputados_pp.get(p["id"], 0),
                    "pronosticos_cargados": len(pron_por_participante.get(p["id"], {})),
                }
                for p in participantes
            ),
            key=lambda r: r["puntos"],
            reverse=True,
        )

        if ranking:
            ranking_txt = "\n".join(
                f"{i+1}. {r['nombre']} — {r['puntos']} pts "
                f"({r['aciertos']}/{r['disputados']} aciertos, "
                f"{r['pronosticos_cargados']} pronósticos cargados)"
                for i, r in enumerate(ranking)
            )
            partes.append(f"RANKING ACTUAL (de mayor a menor puntaje):\n{ranking_txt}")
        else:
            partes.append("RANKING ACTUAL: todavía no hay participantes o pronósticos cargados.")

        # ── Estado de boletas (igual que 05_Dashboard) ────────────────────────
        total_partidos_torneo = len(partidos)
        boletas_txt_lines = []
        for r in ranking:
            cargados = r["pronosticos_cargados"]
            faltantes = total_partidos_torneo - cargados
            estado = "✅ completa" if faltantes <= 0 else f"⚠️ incompleta (faltan {faltantes})"
            boletas_txt_lines.append(f"- {r['nombre']}: {cargados}/{total_partidos_torneo} {estado}")
        partes.append("ESTADO DE BOLETAS:\n" + "\n".join(boletas_txt_lines))

        # ── Partidos jugados con resultado (igual que 01_Resultados) ─────────
        jugados = [p for p in partidos if p.get("resultado")]
        pendientes = [p for p in partidos if not p.get("resultado")]

        def _label(p):
            r = p["resultado"]
            if r == "1":
                return f"Gana {p['local']}"
            if r == "2":
                return f"Gana {p['visitante']}"
            return "Empate"

        if jugados:
            jugados_txt = "\n".join(
                f"- Grupo {p['grupo']}: {p['local']} vs {p['visitante']} "
                f"({p['fecha']}) → resultado: {_label(p)}"
                for p in jugados
            )
            partes.append(f"PARTIDOS YA JUGADOS ({len(jugados)}):\n{jugados_txt}")

        if pendientes:
            pendientes_txt = "\n".join(
                f"- Grupo {p['grupo']}: {p['local']} vs {p['visitante']} "
                f"el {p['fecha']} {p.get('hora','')} en {p.get('sede','')}"
                for p in pendientes
            )
            partes.append(f"PARTIDOS PENDIENTES (sin jugar, {len(pendientes)}):\n{pendientes_txt}")

        # ── Pronósticos por participante para los partidos ya jugados ─────────
        # Así MessiBoot puede decir "X pronosticó Y en tal partido"
        if jugados and ranking:
            detalle_prons = []
            for r in ranking:
                pid = r["id"]
                mis_prons = pron_por_participante.get(pid, {})
                lineas = []
                for p in jugados:
                    pron = mis_prons.get(p["id"], "—")
                    resultado_real = p.get("resultado", "")
                    acerto = "✓" if pron == resultado_real else "✗"
                    lineas.append(
                        f"  {p['local']} vs {p['visitante']}: pronosticó {pron} → real {resultado_real} {acerto}"
                    )
                detalle_prons.append(f"{r['nombre']}:\n" + "\n".join(lineas))
            partes.append(
                "DETALLE DE PRONÓSTICOS EN PARTIDOS JUGADOS:\n" +
                "\n\n".join(detalle_prons)
            )

        partes.append(
            f"RESUMEN: {len(participantes)} participantes, {len(partidos)} partidos "
            f"({len(jugados)} jugados, {len(pendientes)} pendientes)."
        )

    except Exception as e:
        partes.append(f"(Aviso: no se pudieron cargar todos los datos en vivo: {e})")

    return "\n\n".join(partes)


# ──────────────────────────────────────────────────────────────────────────
# 2. Llamada a Groq
# ──────────────────────────────────────────────────────────────────────────
def _groq_api_key() -> str:
    import os
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        try:
            key = st.secrets.get("GROQ_API_KEY", "")
        except Exception:
            pass
    return key


def _llamar_groq(pregunta: str, contexto: str) -> str:
    import urllib.request
    import urllib.error

    api_key = _groq_api_key()
    if not api_key:
        return (
            "⚠️ Falta configurar GROQ_API_KEY en .streamlit/secrets.toml "
            "(conseguila gratis en console.groq.com/keys)."
        )

    system_prompt = (
        "Sos MessiBoot, el asistente virtual oficial del sitio PRODE FIFA WORLD CUP 2026. "
        "SOLO podés hablar de este sitio y del prode: reglas, puntajes, ranking, partidos, "
        "resultados, pronósticos y participantes. Si te preguntan algo que no tiene que ver "
        "con el sitio o el prode, respondé amablemente que solo podés ayudar con temas del "
        "prode. Usá los datos reales provistos abajo para responder con precisión, números "
        "exactos y nombres correctos. No inventes datos que no estén en el contexto: si no "
        "sabés algo, decilo. Sé breve, claro y con onda futbolera, podés usar algún emoji con "
        "moderación (⚽🏆📊). Respondé siempre en español.\n\n"
        "IMPORTANTE: La sección PARTICIPANTES REGISTRADOS contiene la lista COMPLETA y EXACTA "
        "de todos los jugadores del prode. Si alguien pregunta por un participante, buscá su "
        "nombre en esa lista antes de responder. Nunca digas que alguien no existe si está en "
        "la lista.\n\n"
        "DATOS REALES Y ACTUALIZADOS DEL SITIO:\n" + contexto
    )

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": pregunta},
        ],
        "temperature": 0.4,
        "max_tokens": 600,
    }

    req = urllib.request.Request(
        GROQ_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            # Cloudflare (delante de la API de Groq) devuelve 403 / código
            # 1010 a requests sin un User-Agent de aspecto "normal" — lo
            # agregamos explícitamente porque urllib no manda uno por defecto.
            "User-Agent": "Mozilla/5.0 (compatible; MessiBootProde/1.0)",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        detalle = e.read().decode("utf-8", errors="ignore")
        return f"⚠️ Error de Groq ({e.code}): {detalle[:200]}"
    except Exception as e:
        return f"⚠️ No pude responder ahora mismo ({e})."


# ──────────────────────────────────────────────────────────────────────────
# 3. CSS flotante (sin iframe — vive en el DOM principal de la página)
# ──────────────────────────────────────────────────────────────────────────
_CSS = """
<style>
/* st.container(key="messiboot_panel") genera la clase .st-key-messiboot_panel
   en el DIV real que envuelve sus hijos. Lo anclamos con position:fixed
   a la esquina inferior derecha de la ventana. Como esto vive en el DOM
   principal de la página (sin iframe), position:fixed funciona de verdad. */
.st-key-messiboot_panel {
    position: fixed !important;
    bottom: 20px !important;
    right: 20px !important;
    z-index: 999999 !important;
    width: 360px !important;
    max-width: 92vw !important;
}
.st-key-messiboot_panel > div {
    background: rgba(10,15,28,0.97);
    border: 1px solid rgba(232,201,107,0.35);
    border-radius: 22px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.7), 0 0 0 1px rgba(232,201,107,0.1);
    padding: 0 14px 10px;
    max-height: 78vh;
    overflow-y: auto;
}
.st-key-messiboot_bubble {
    position: fixed !important;
    bottom: 20px !important;
    right: 20px !important;
    z-index: 999999 !important;
    width: 72px !important;
}

#messiboot-header {
    background: linear-gradient(135deg, #1c2438, #0b0f19);
    margin: 0 -14px 10px;
    padding: 0 16px 12px;
    border-radius: 22px 22px 0 0;
    border-bottom: 1px solid rgba(232,201,107,0.2);
}
#messiboot-avatar-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-top: 14px;
}
#messiboot-avatar-img {
    width: 54px;
    height: 54px;
    object-fit: cover;
    object-position: center top;
    border-radius: 50%;
    border: 2px solid rgba(232,201,107,0.6);
    box-shadow: 0 0 14px rgba(232,201,107,0.3);
    flex-shrink: 0;
}
#messiboot-avatar-placeholder {
    width: 54px; height: 54px;
    border-radius: 50%;
    background: linear-gradient(135deg, #e8c96b, #b8893a);
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; flex-shrink: 0;
    border: 2px solid rgba(232,201,107,0.6);
    box-shadow: 0 0 14px rgba(232,201,107,0.3);
}
#messiboot-title-block { flex: 1; }
#messiboot-name {
    font-family: 'Bebas Neue', 'Arial Narrow', sans-serif;
    font-size: 17px; letter-spacing: 1.5px; color: #e8c96b;
    line-height: 1.1; margin: 0;
}
#messiboot-subtitle {
    font-size: 11px; color: rgba(148,163,184,0.8);
    letter-spacing: 0.5px; margin-top: 2px;
}
#messiboot-status {
    display: flex; align-items: center; gap: 5px;
    margin-top: 5px;
}
#messiboot-status-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #4ade80;
    box-shadow: 0 0 6px rgba(74,222,128,0.7);
    animation: mbPulse 2s infinite;
}
@keyframes mbPulse {
    0%, 100% { opacity: 1; } 50% { opacity: 0.4; }
}
#messiboot-status-txt {
    font-size: 10.5px; color: #4ade80; font-weight: 600; letter-spacing: 0.3px;
}

#messiboot-messages { padding: 4px 0; }
.mb-msg { margin-bottom: 10px; font-size: 13.5px; line-height: 1.4; display: flex; }
.mb-msg.user { justify-content: flex-end; }
.mb-msg.bot { justify-content: flex-start; }
.mb-msg span {
    display: inline-block; max-width: 88%; padding: 7px 12px;
    white-space: pre-wrap; word-wrap: break-word; font-family: 'DM Sans', sans-serif;
}
.mb-msg.user span { background: #e8c96b; color: #1a1a1a; border-radius: 14px 14px 2px 14px; font-weight: 600; }
.mb-msg.bot span { background: rgba(255,255,255,0.08); color: #f1f5f9; border-radius: 14px 14px 14px 2px; border: 1px solid rgba(255,255,255,0.06); }
.mb-welcome {
    color: #64748b; font-size: 12.5px; text-align: center;
    padding: 16px 8px; font-family: 'DM Sans', sans-serif;
}

/* Burbuja circular: el botón nativo dentro del contenedor anclado */
.st-key-messiboot_bubble button {
    width: 72px !important; height: 72px !important; border-radius: 50% !important;
    background: linear-gradient(135deg, #1c2438, #0b0f19) !important;
    border: 2.5px solid rgba(232,201,107,0.6) !important;
    font-size: 0 !important;
    box-shadow: 0 8px 28px rgba(0,0,0,0.55), 0 0 0 4px rgba(232,201,107,0.08) !important;
    padding: 0 !important; min-height: 0 !important; line-height: 1 !important;
    overflow: hidden !important;
    position: relative !important;
}

/* Botones enviar / cerrar dentro del panel: chicos y discretos */
.st-key-messiboot_panel button {
    border-radius: 10px !important; font-size: 14px !important;
}
</style>
"""


# ──────────────────────────────────────────────────────────────────────────
# 4. Widget flotante (burbuja + panel + input nativo de Streamlit)
# ──────────────────────────────────────────────────────────────────────────
def _procesar_envio():
    """Callback: toma lo que hay en el input, llama a Groq, y limpia el campo."""
    texto = (st.session_state.get("messiboot_input_box") or "").strip()
    if not texto:
        return
    st.session_state[HIST_KEY].append({"rol": "user", "texto": texto})
    contexto = _obtener_contexto_prode()
    respuesta = _llamar_groq(texto, contexto)
    st.session_state[HIST_KEY].append({"rol": "bot", "texto": respuesta})
    st.session_state["messiboot_input_box"] = ""


def render_messiboot():
    """Inyecta el widget flotante de MessiBoot en la página actual."""

    if HIST_KEY not in st.session_state:
        st.session_state[HIST_KEY] = []
    if OPEN_KEY not in st.session_state:
        st.session_state[OPEN_KEY] = False

    st.markdown(_CSS, unsafe_allow_html=True)

    # Construir HTML del avatar (imagen real o emoji fallback)
    avatar_b64 = _get_avatar_b64()
    if avatar_b64:
        avatar_html = (
            f'<img id="messiboot-avatar-img" '
            f'src="data:image/png;base64,{avatar_b64}" '
            f'alt="MessiBoot">'
        )
    else:
        avatar_html = '<div id="messiboot-avatar-placeholder">🤖</div>'

    header_html = (
        '<div id="messiboot-header">'
        '<div id="messiboot-avatar-row">'
        + avatar_html +
        '<div id="messiboot-title-block">'
        '<div id="messiboot-name">MESSIBOOT</div>'
        '<div id="messiboot-subtitle">Asistente del Prode FIFA 26</div>'
        '<div id="messiboot-status">'
        '<div id="messiboot-status-dot"></div>'
        '<span id="messiboot-status-txt">En línea · datos en vivo</span>'
        '</div>'
        '</div>'
        '</div>'
        '</div>'
    )

    if st.session_state[OPEN_KEY]:
        # Todo lo que va DENTRO de este container queda anclado a la
        # esquina inferior derecha gracias a la clase .st-key-messiboot_panel
        # (position:fixed) definida en _CSS. Como no hay iframe de por
        # medio, los widgets nativos (text_input/button) disparan un
        # rerun real al tocarlos — sin sandboxing, sin bloqueos.
        with st.container(key="messiboot_panel"):
            st.markdown(header_html, unsafe_allow_html=True)

            mensajes_html = ""
            if not st.session_state[HIST_KEY]:
                mensajes_html = (
                    '<div class="mb-welcome">¡Hola! Soy MessiBoot ⚽<br>'
                    "Preguntame sobre el ranking, partidos, resultados o "
                    "pronósticos del prode.</div>"
                )
            else:
                for m in st.session_state[HIST_KEY]:
                    rol = "user" if m["rol"] == "user" else "bot"
                    texto_escapado = (
                        m["texto"]
                        .replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                    )
                    mensajes_html += f'<div class="mb-msg {rol}"><span>{texto_escapado}</span></div>'

            st.markdown(f'<div id="messiboot-messages">{mensajes_html}</div>', unsafe_allow_html=True)

            col_input, col_send, col_close = st.columns([5, 1, 1])
            with col_input:
                st.text_input(
                    "Mensaje a MessiBoot",
                    key="messiboot_input_box",
                    placeholder="Preguntame sobre el prode... (Enter para enviar)",
                    label_visibility="collapsed",
                    on_change=_procesar_envio,
                )
            with col_send:
                enviar_click = st.button("➤", key="messiboot_send_btn", use_container_width=True)
            with col_close:
                cerrar = st.button("✕", key="messiboot_close_btn", use_container_width=True)

        if cerrar:
            st.session_state[OPEN_KEY] = False
            st.rerun()

        if enviar_click:
            with st.spinner("MessiBoot está pensando... ⚽"):
                _procesar_envio()
            st.rerun()

    else:
        # Cerrado: solo la burbuja con la imagen del avatar, anclada con .st-key-messiboot_bubble
        with st.container(key="messiboot_bubble"):
            if avatar_b64:
                # Inyectamos la imagen sobre el botón via HTML dentro del label del botón
                # usando un truco: el botón lleva la imagen como contenido HTML vía markdown
                st.markdown(
                    f'<style>'
                    f'.st-key-messiboot_bubble button::after {{'
                    f'  content: "";'
                    f'  position: absolute;'
                    f'  inset: 3px;'
                    f'  border-radius: 50%;'
                    f'  background: url("data:image/png;base64,{avatar_b64}") center top / cover;'
                    f'}}'
                    f'</style>',
                    unsafe_allow_html=True
                )
            abrir = st.button("⚽", key="messiboot_bubble_btn")
        if abrir:
            st.session_state[OPEN_KEY] = True
            st.rerun()
