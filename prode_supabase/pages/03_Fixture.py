Skip to content
arcaltdfootball
PRODEFIFAWC2026UNQ
Repository navigation
Code
Issues
Pull requests
Actions
Projects
Security and quality
Insights
Settings
PRODEFIFAWC2026UNQ/prode_supabase/pages
/
03_Fixture.py
in
main

Edit

Preview
Indent mode

Spaces
Indent size

2
Line wrap mode

No wrap
Editing 03_Fixture.py file contents
  1
  2
  3
  4
  5
  6
  7
  8
  9
 10
 11
 12
 13
 14
 15
 16
 17
 18
 19
 20
 21
 22
 23
 24
 25
 26
 27
 28
 29
 30
 31
 32
 33
 34
 35
 36
 37
 38
 39
 40
 41
 42
 43
 44
 45
 46
 47
 48
 49
 50
 51
 52
 53
 54
 55
 56
 57
 58
 59
 60
 61
 62
 63
 64
"""
03_Fixture.py — Prode Liga Profesional Argentina
Cambios:
  - Boleta usa marcador exacto (goles local / goles visitante); el signo
    (1/X/2) se deriva automáticamente a partir del marcador cargado.
  - Sistema de puntaje: 1 punto por acertar el signo (Local/Empate/Visitante),
    3 puntos en total si se acierta el marcador exacto.
  - Admin puede eliminar participantes con confirmación
  - Admin puede resetear (borrar) la lista completa de participantes
  - Resultado se guarda como goles y se refleja en 01_Resultados.py

IMPORTANTE: la tabla `pronosticos` en Supabase necesita las columnas
`goles_local_pred` (int, nullable) y `goles_visitante_pred` (int, nullable)
además de las existentes `signo_pred` y `puntos`. Si no existen, correr:

    ALTER TABLE pronosticos ADD COLUMN goles_local_pred integer;
    ALTER TABLE pronosticos ADD COLUMN goles_visitante_pred integer;
"""
import base64
import hashlib
import json
import os
import secrets
import string

import streamlit as st
from database import conectar
from escudos_map import url_escudo


def _rol_de_supabase_key():
    """Decodifica el JWT de SUPABASE_KEY (sin validar firma) solo para
    mostrar el campo 'role' (anon / service_role) y así diagnosticar
    a simple vista qué key está usando realmente la app en este momento."""
    key = os.environ.get("SUPABASE_KEY", "")
    if not key:
        try:
            key = st.secrets.get("SUPABASE_KEY", "")
        except Exception:
            key = ""
    if not key or key.count(".") != 2:
        return None, None
    try:
        payload_b64 = key.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)  # padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get("role"), key[-6:]
    except Exception:
        return None, key[-6:] if key else None

st.set_page_config(page_title="Fixture - Mi Boleta", page_icon="📝", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap');

    [data-testid="stApp"] {
        background-image: url('https://raw.githubusercontent.com/arcaltdfootball/PRODEFIFAWC2026UNQ/main/prode_supabase/AFA2026.png');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
        background-color: #0b0f19;
Use Control + Shift + m to toggle the tab key moving focus. Alternatively, use esc then tab to move to the next interactive element on the page.
 
