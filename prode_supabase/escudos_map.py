"""
escudos_map.py

Traduce los nombres "cortos" que usás en la base (equipos_clausura_2026.csv,
tabla "equipos"/"partidos" en Supabase) a los nombres "lindos" que genera
escudos_prode.py / escudos.json, y devuelve la URL del escudo de cada equipo.

Si en algún momento cambiás/agregás un nombre en el CSV, actualizá el
diccionario ALIAS de acá abajo.

Requiere que "escudos.json" (generado por escudos_prode.py) esté en la raíz
del repo, al lado de este archivo.
"""
import json
import os
import streamlit as st

# nombre en la base (CSV) -> nombre "lindo" usado como clave en escudos.json
ALIAS = {
    "Boca": "Boca Juniors",
    "Independiente": "Independiente",
    "San Lorenzo": "San Lorenzo",
    "Deportivo Riestra": "Deportivo Riestra",
    "Talleres": "Talleres (Córdoba)",
    "Instituto": "Instituto (Córdoba)",
    "Platense": "Platense",
    "Estudiantes": "Estudiantes (LP)",
    "Gimnasia (Mza.)": "Gimnasia y Esgrima (Mza)",
    "Vélez": "Vélez Sarsfield",
    "Newell's": "Newell's Old Boys",
    "Unión": "Unión (Santa Fe)",
    "Lanús": "Lanús",
    "Central Córdoba": "Central Córdoba (SdE)",
    "Defensa y Justicia": "Defensa y Justicia",
    "River": "River Plate",
    "Racing": "Racing Club",
    "Huracán": "Huracán",
    "Barracas Central": "Barracas Central",
    "Belgrano": "Belgrano (Córdoba)",
    "Estudiantes (Río Cuarto)": "Estudiantes (Río Cuarto)",
    "Independiente Rivadavia": "Independiente Rivadavia",
    "Gimnasia": "Gimnasia y Esgrima (LP)",
    "Tigre": "Tigre",
    "Argentinos": "Argentinos Juniors",
    "Sarmiento": "Sarmiento (Junín)",
    "Rosario Central": "Rosario Central",
    "Banfield": "Banfield",
    "Atlético Tucumán": "Atlético Tucumán",
    "Aldosivi": "Aldosivi",
    # nombres alternativos / abreviados que pueden venir de la BD
    "Ind. Rivadavia": "Independiente Rivadavia",
    "Independiente Rivadavia": "Independiente Rivadavia",
    "Banfield": "Banfield",
    "Tigre": "Tigre",
}

_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "escudos.json")


@st.cache_data
def _cargar_escudos() -> dict:
    try:
        with open(_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def url_escudo(nombre_csv: str):
    """
    Recibe el nombre tal cual está en la tabla "equipos"/"partidos" de
    Supabase (ej. "Boca", "River", "Talleres") y devuelve la URL del
    escudo, o None si no se encontró.
    """
    escudos = _cargar_escudos()
    nombre_lindo = ALIAS.get(nombre_csv, nombre_csv)
    data = escudos.get(nombre_lindo)
    return data["url"] if data else None
