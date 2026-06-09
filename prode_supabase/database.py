"""
Capa de acceso a datos — Supabase.
Expone get_client() que devuelve el cliente Supabase listo para usar.
"""
import os
from supabase import create_client, Client


def conectar() -> Client:
    """
    Devuelve el cliente Supabase.
    Compatibilidad: el código existente llama conectar() igual que antes,
    pero ahora recibe un cliente Supabase en lugar de una conexión SQLite.
    """
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")

    # Streamlit Cloud: leer desde st.secrets si no están en el entorno
    if not url or not key:
        try:
            import streamlit as st
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
