"""
MESSIBOOT — Asistente flotante del PRODE FIFA WORLD CUP 2026
==============================================================
Widget de chat flotante (burbuja abajo a la derecha, visible en todo
el sitio) que responde EXCLUSIVAMENTE sobre el sitio y el prode,
usando datos reales de Supabase (partidos, resultados, ranking,
pronósticos) y la API gratuita de Groq (Llama 3.3 70B) como motor.

USO — pegar esta única línea al inicio de app.py y de cada página
en pages/, después de los imports de Streamlit:

    from messiboot import render_messiboot; render_messiboot()

CONFIGURACIÓN — definir la API key de Groq en .streamlit/secrets.toml:

    GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxxxxxxxxxx"

(o como variable de entorno GROQ_API_KEY). Se consigue gratis en
https://console.groq.com/keys
"""
import json
import streamlit as st
import streamlit.components.v1 as components
from database import conectar

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
HIST_KEY = "messiboot_historial"


# ──────────────────────────────────────────────────────────────────────────
# 1. Recolección de datos reales del prode (Supabase)
# ──────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def _obtener_contexto_prode() -> str:
    """
    Arma un resumen compacto y actualizado del estado real del prode:
    reglas de puntaje, fixture/resultados, ranking y participantes.
    Se cachea 2 minutos para no saturar Supabase en cada mensaje.
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
        "- No se otorgan puntos por marcador exacto, solo por signo (1/X/2)."
    ]

    try:
        participantes = sb.table("participantes").select("id, nombre").execute().data or []
        partidos = sb.table("partidos").select(
            "id, grupo, fecha, hora, sede, local, visitante, resultado"
        ).execute().data or []
        pronosticos = sb.table("pronosticos").select(
            "participante_id, partido_id, pronostico"
        ).execute().data or []

        partidos_por_id = {p["id"]: p for p in partidos}

        puntos_pp, aciertos_pp, disputados_pp = {}, {}, {}
        for pr in pronosticos:
            pid = pr["participante_id"]
            partido = partidos_por_id.get(pr["partido_id"])
            if not partido:
                continue
            resultado = partido.get("resultado") or ""
            if not resultado:
                continue
            disputados_pp[pid] = disputados_pp.get(pid, 0) + 1
            if resultado == pr.get("pronostico"):
                puntos_pp[pid] = puntos_pp.get(pid, 0) + 3
                aciertos_pp[pid] = aciertos_pp.get(pid, 0) + 1

        ranking = sorted(
            (
                {
                    "nombre": p["nombre"],
                    "puntos": puntos_pp.get(p["id"], 0),
                    "aciertos": aciertos_pp.get(p["id"], 0),
                    "disputados": disputados_pp.get(p["id"], 0),
                }
                for p in participantes
            ),
            key=lambda r: r["puntos"],
            reverse=True,
        )

        if ranking:
            ranking_txt = "\n".join(
                f"{i+1}. {r['nombre']} — {r['puntos']} pts "
                f"({r['aciertos']}/{r['disputados']} aciertos)"
                for i, r in enumerate(ranking)
            )
            partes.append(f"RANKING ACTUAL (de mayor a menor puntaje):\n{ranking_txt}")
        else:
            partes.append("RANKING ACTUAL: todavía no hay participantes o pronósticos cargados.")

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
            partes.append(f"PARTIDOS YA JUGADOS:\n{jugados_txt}")

        if pendientes:
            pendientes_txt = "\n".join(
                f"- Grupo {p['grupo']}: {p['local']} vs {p['visitante']} "
                f"el {p['fecha']} {p.get('hora','')} en {p.get('sede','')}"
                for p in pendientes
            )
            partes.append(f"PARTIDOS PENDIENTES (sin jugar):\n{pendientes_txt}")

        partes.append(
            f"TOTAL: {len(participantes)} participantes, {len(partidos)} partidos "
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
# 3. Widget flotante (burbuja + ventana de chat)
# ──────────────────────────────────────────────────────────────────────────
def render_messiboot():
    """Inyecta el widget flotante de MessiBoot en la página actual."""

    if HIST_KEY not in st.session_state:
        st.session_state[HIST_KEY] = []

    # ── 1) Si venimos de un submit del widget, procesamos ANTES de pintar ──
    qp = st.query_params
    pregunta_pendiente = qp.get("messiboot_msg")
    if pregunta_pendiente:
        st.query_params.clear()
        with st.spinner("MessiBoot está pensando... ⚽"):
            contexto = _obtener_contexto_prode()
            respuesta = _llamar_groq(pregunta_pendiente, contexto)
        st.session_state[HIST_KEY].append({"rol": "user", "texto": pregunta_pendiente})
        st.session_state[HIST_KEY].append({"rol": "bot", "texto": respuesta})

    historial_json = json.dumps(st.session_state[HIST_KEY], ensure_ascii=False)
    abierto_js = "true" if pregunta_pendiente else "false"

    widget_html = f"""
    <style>
    #messiboot-bubble {{
        position: fixed; bottom: 22px; right: 22px;
        width: 58px; height: 58px; border-radius: 50%;
        background: linear-gradient(135deg, #e8c96b, #c9a227);
        display: flex; align-items: center; justify-content: center;
        font-size: 26px; cursor: pointer; z-index: 999999;
        box-shadow: 0 8px 24px rgba(0,0,0,0.45);
        border: 2px solid rgba(255,255,255,0.25);
        transition: transform 0.15s;
    }}
    #messiboot-bubble:hover {{ transform: scale(1.08); }}
    #messiboot-panel {{
        position: fixed; bottom: 90px; right: 22px;
        width: 340px; max-height: 460px;
        background: rgba(15,20,35,0.98);
        border: 1px solid rgba(232,201,107,0.3);
        border-radius: 18px; z-index: 999999;
        display: none; flex-direction: column;
        box-shadow: 0 16px 48px rgba(0,0,0,0.6);
        font-family: 'DM Sans', sans-serif;
        overflow: hidden;
    }}
    #messiboot-panel.open {{ display: flex; }}
    #messiboot-header {{
        background: linear-gradient(135deg, #1c2438, #0b0f19);
        padding: 14px 16px; color: #e8c96b; font-weight: 700;
        font-size: 15px; display: flex; align-items: center;
        justify-content: space-between; border-bottom: 1px solid rgba(232,201,107,0.2);
    }}
    #messiboot-close {{ cursor: pointer; color: #94a3b8; font-size: 18px; }}
    #messiboot-messages {{
        flex: 1; overflow-y: auto; padding: 12px; min-height: 200px; max-height: 320px;
    }}
    .mb-msg {{ margin-bottom: 10px; font-size: 13.5px; line-height: 1.4; }}
    .mb-msg.user {{ text-align: right; }}
    .mb-msg.user span {{
        background: #e8c96b; color: #1a1a1a; padding: 7px 12px;
        border-radius: 14px 14px 2px 14px; display: inline-block; max-width: 85%;
        white-space: pre-wrap; text-align: left;
    }}
    .mb-msg.bot span {{
        background: rgba(255,255,255,0.08); color: #f1f5f9; padding: 7px 12px;
        border-radius: 14px 14px 14px 2px; display: inline-block; max-width: 85%;
        white-space: pre-wrap;
    }}
    #messiboot-inputrow {{
        display: flex; gap: 6px; padding: 10px; border-top: 1px solid rgba(255,255,255,0.08);
    }}
    #messiboot-input {{
        flex: 1; border-radius: 20px; border: 1px solid rgba(255,255,255,0.15);
        background: rgba(255,255,255,0.06); color: #fff; padding: 8px 14px; font-size: 13px;
        outline: none;
    }}
    #messiboot-input:disabled {{ opacity: 0.5; }}
    #messiboot-send {{
        background: #e8c96b; border: none; border-radius: 50%;
        width: 36px; height: 36px; cursor: pointer; font-size: 16px; flex-shrink: 0;
    }}
    #messiboot-send:disabled {{ opacity: 0.5; cursor: default; }}
    .mb-welcome {{ color: #64748b; font-size: 12.5px; text-align: center; padding: 14px 6px; }}
    </style>

    <div id="messiboot-bubble" onclick="messibootToggle()" title="MessiBoot · Asistente del Prode">⚽</div>
    <div id="messiboot-panel" class="{'open' if pregunta_pendiente else ''}">
        <div id="messiboot-header">
            <span>🤖 MessiBoot · Asistente del Prode</span>
            <span id="messiboot-close" onclick="messibootToggle()">✕</span>
        </div>
        <div id="messiboot-messages"></div>
        <div id="messiboot-inputrow">
            <input id="messiboot-input" type="text" placeholder="Preguntame sobre el prode..." onkeydown="if(event.key==='Enter')messibootSend()">
            <button id="messiboot-send" onclick="messibootSend()">➤</button>
        </div>
    </div>

    <script>
    const messibootHistorial = {historial_json};
    let messibootAbierto = {abierto_js};

    function messibootApplyOpenState() {{
        const panel = document.getElementById('messiboot-panel');
        if (messibootAbierto) {{ panel.classList.add('open'); }}
        else {{ panel.classList.remove('open'); }}
    }}

    function messibootToggle() {{
        messibootAbierto = !messibootAbierto;
        messibootApplyOpenState();
    }}

    function messibootRender() {{
        const box = document.getElementById('messiboot-messages');
        box.innerHTML = '';
        if (messibootHistorial.length === 0) {{
            box.innerHTML = '<div class="mb-welcome">¡Hola! Soy MessiBoot ⚽<br>Preguntame sobre el ranking, partidos, resultados o pronósticos del prode.</div>';
        }}
        messibootHistorial.forEach(m => {{
            const div = document.createElement('div');
            div.className = 'mb-msg ' + (m.rol === 'user' ? 'user' : 'bot');
            const span = document.createElement('span');
            span.textContent = m.texto;
            div.appendChild(span);
            box.appendChild(div);
        }});
        box.scrollTop = box.scrollHeight;
    }}

    function messibootGetTopWindow() {{
        try {{ return window.parent.parent || window.parent; }}
        catch (e) {{ return window.parent; }}
    }}

    function messibootSend() {{
        const input = document.getElementById('messiboot-input');
        const btn = document.getElementById('messiboot-send');
        const texto = input.value.trim();
        if (!texto) return;
        input.disabled = true;
        btn.disabled = true;

        const top = messibootGetTopWindow();
        const url = new URL(top.location.href);
        url.searchParams.set('messiboot_msg', texto);
        top.location.href = url.toString();
    }}

    messibootApplyOpenState();
    messibootRender();
    </script>
    """

    components.html(widget_html, height=0, width=0)
