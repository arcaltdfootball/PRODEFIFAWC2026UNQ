import streamlit as st
import base64
import os
from pathlib import Path

# ── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="PRODE FIFA WORLD CUP 2026",
    page_icon="⚽",
    layout="wide"
)

# ── Fondo ─────────────────────────────────────────────────────────────────────
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

bg_image = get_base64_image("fotos/fwc2026_bg.webp")

if bg_image:
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/webp;base64,{bg_image}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
    """, unsafe_allow_html=True)

# ── Variables de entorno para Supabase ────────────────────────────────────────
# En Streamlit Cloud se configuran en Settings → Secrets:
#   SUPABASE_URL = "https://xxxx.supabase.co"
#   SUPABASE_KEY = "eyJh..."
#
# En local se puede usar un archivo .env o configurar directamente aquí.

if "SUPABASE_URL" not in os.environ:
    try:
        os.environ["SUPABASE_URL"] = st.secrets["SUPABASE_URL"]
        os.environ["SUPABASE_KEY"] = st.secrets["SUPABASE_KEY"]
    except Exception:
        pass  # El usuario verá el error al intentar usar la app

# ── Contenido principal ───────────────────────────────────────────────────────
st.title("⚽ PRODE FIFA WORLD CUP 2026")

st.markdown("""
### BIENVENIDOS AL SISTEMA DE APUESTAS ONLINE
""")

st.info("Despliegue el menú lateral para navegar entre secciones.")
