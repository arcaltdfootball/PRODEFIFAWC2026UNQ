import streamlit as st

st.set_page_config(
    page_title="MessiBot FIFA 2026",
    page_icon="🐐",
    layout="wide"
)

# ==========================================================
# FONDO FIFA 2026 (MISMO ESTILO DEL DASHBOARD)
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

.sugerencia{
    background: rgba(255,255,255,0.15);
    border-radius: 10px;
    padding: 10px;
    margin-bottom: 10px;
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
# MEMORIA DEL CHAT
# ==========================================================

if "messi_chat" not in st.session_state:
    st.session_state.messi_chat = []

# ==========================================================
# RESPUESTAS
# ==========================================================

def responder(texto):

    texto = texto.lower()

    if "hola" in texto:
        return "Hola. Soy MessiBot. ¿Cómo va ese Prode?"

    elif "argentina" in texto:
        return (
            "Argentina siempre tiene la obligación de competir. "
            "Hay un gran grupo y mucha ilusión."
        )

    elif "mundial" in texto:
        return (
            "Un Mundial siempre es especial. "
            "Hay que ir partido a partido."
        )

    elif "campeon" in texto:
        return (
            "Hay varias selecciones candidatas, "
            "pero nunca hay que subestimar a Argentina."
        )

    elif "brasil" in texto:
        return (
            "Brasil tiene muchísimo talento y siempre pelea arriba."
        )

    elif "francia" in texto:
        return (
            "Francia tiene grandes jugadores y experiencia."
        )

    elif "prode" in texto:
        return (
            "En los Prodes siempre aparecen resultados inesperados. "
            "No te confíes."
        )

    elif "gol" in texto:
        return (
            "Cada gol tiene algo especial, "
            "pero los del Mundial son inolvidables."
        )

    elif "ranking" in texto:
        return (
            "Lo importante no es cómo empezás, "
            "sino cómo terminás el torneo."
        )

    elif "quien gana" in texto:
        return (
            "Si supiera eso tendría el Prode perfecto."
        )

    elif "messi" in texto:
        return (
            "Intenté disfrutar cada momento de mi carrera."
        )

    else:
        return (
            "No estoy seguro de la respuesta, "
            "pero disfrutá el Mundial y seguí confiando en tus pronósticos."
        )

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

    st.session_state.messi_chat.append({
        "role": "user",
        "content": pregunta
    })

    respuesta = responder(pregunta)

    st.session_state.messi_chat.append({
        "role": "assistant",
        "content": f"🐐 {respuesta}"
    })

    st.rerun()