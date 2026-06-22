import streamlit as st
from groq import Groq

st.set_page_config(
    page_title="MessiBot FIFA 2026",
    page_icon="🐐",
    layout="wide"
)

# ==========================================================
# FONDO FIFA 2026
# ==========================================================

st.markdown("""
<style>

[data-testid="stApp"] {
    background-image: url('https://raw.githubusercontent.com/arcaltdfootball/PRODEFIFAWC2026UNQ/main/prode_supabase/dashboard.jpg');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    background-repeat: no-repeat;
}

.bloque-messi{
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-radius: 20px;
    padding: 25px;
    border: 1px solid rgba(255,255,255,0.3);
    margin-bottom: 20px;
}

.titulo{
    text-align:center;
    color:white;
    font-size:40px;
    font-weight:700;
}

.subtitulo{
    text-align:center;
    color:white;
    font-size:18px;
}

</style>
""", unsafe_allow_html=True)

# ==========================================================
# CABECERA
# ==========================================================

st.markdown(
    """
    <div class="bloque-messi">
        <div class="titulo">🐐 MessiBot FIFA World Cup 2026</div>
        <div class="subtitulo">
            Charlá con Lionel Messi sobre el Mundial, Argentina y tu Prode.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ==========================================================
# CLIENTE GROQ
# ✅ FIX: modelo liviano con límite 500x mayor (6M TPM vs 12K TPM)
# ==========================================================

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

MODELO = "llama-3.1-8b-instant"   # ✅ antes: llama-3.3-70b-versatile

SYSTEM_PROMPT = """Sos Lionel Messi durante la Copa del Mundo FIFA 2026.
Respondé siempre en primera persona, con la voz tranquila, reflexiva y humilde que lo caracteriza.
Hablás en español rioplatense (Argentina). Podés usar algunas expresiones argentinas.
Respondé de forma corta y natural, como en una charla informal (máximo 3 oraciones).
Podés hablar sobre: fútbol, el Mundial 2026, selecciones participantes, el Prode del usuario, tus recuerdos de carrera.
Si no sabés algo, decilo con humildad. Nunca salgas del personaje.
Usá emojis con moderación (1-2 por respuesta máximo)."""

# ==========================================================
# MEMORIA DEL CHAT
# ==========================================================

if "messi_chat" not in st.session_state:
    st.session_state.messi_chat = []

# ==========================================================
# FUNCIÓN DE RESPUESTA CON GROQ
# ✅ FIX: historial limitado a últimos 6 mensajes
# ✅ FIX: max_tokens=200 para no gastar tokens innecesarios
# ✅ FIX: manejo de errores con mensaje amigable
# ==========================================================

def responder_con_groq(historial):
    try:
        # ✅ Solo mandamos los últimos 6 mensajes (3 intercambios) + system
        historial_recortado = historial[-6:]

        response = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *historial_recortado
            ],
            max_tokens=200,        # ✅ respuestas cortas, menos tokens consumidos
            temperature=0.7,
        )

        return response.choices[0].message.content

    except Exception as e:
        error_str = str(e)

        if "413" in error_str or "TPM" in error_str or "rate" in error_str.lower():
            return "Hay mucho tráfico en este momento, esperá unos segundos y volvé a preguntar. 🐐"

        elif "401" in error_str or "auth" in error_str.lower():
            return "Hay un problema con la conexión. Avisale al admin del Prode."

        else:
            return "No pude responder ahora, intentá de nuevo en un momento. 🐐"

# ==========================================================
# SUGERENCIAS
# ==========================================================

with st.expander("💡 Preguntas sugeridas"):
    st.markdown("""
    - ¿Quién gana el Mundial?
    - ¿Cómo ves a Argentina?
    - ¿Qué opinás de Brasil?
    - ¿Qué opinás de Francia?
    - ¿Cuál fue tu mejor gol?
    - ¿Quién será campeón?
    - ¿Cómo me irá en el Prode?
    """)

# ==========================================================
# MOSTRAR CHAT
# ==========================================================

for mensaje in st.session_state.messi_chat:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])

# ==========================================================
# INPUT
# ==========================================================

pregunta = st.chat_input("Escribile a Messi...")

if pregunta:

    # Mostrar mensaje del usuario
    st.session_state.messi_chat.append({
        "role": "user",
        "content": pregunta
    })

    with st.chat_message("user"):
        st.markdown(pregunta)

    # Obtener y mostrar respuesta
    with st.chat_message("assistant"):
        with st.spinner("Messi está pensando..."):
            respuesta = responder_con_groq(st.session_state.messi_chat)
        st.markdown(f"🐐 {respuesta}")

    st.session_state.messi_chat.append({
        "role": "assistant",
        "content": f"🐐 {respuesta}"
    })
