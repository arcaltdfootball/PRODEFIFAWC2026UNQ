"""
Capa de acceso a datos — Supabase.
Expone conectar() que devuelve el cliente Supabase listo para usar.
El cliente se cachea con @st.cache_resource para no recrearlo en cada render.
"""
import os
import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def conectar() -> Client:
    """
    Devuelve el cliente Supabase cacheado.
    Se crea una sola vez por sesión de Streamlit Cloud.
    """
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")

    # Streamlit Cloud: leer desde st.secrets si no están en el entorno
    if not url or not key:
        try:
            url = st.secrets.get("SUPABASE_URL", url)
            key = st.secrets.get("SUPABASE_KEY", key)
        except Exception:
            pass

    if not url or not key:
        raise ValueError(
            "Faltan SUPABASE_URL y SUPABASE_KEY.\n"
            "Defínilas en .streamlit/secrets.toml o como variables de entorno."
        )

    return create_client(url, key)


# Alias por si algún módulo importa get_client directamente
get_client = conectar
