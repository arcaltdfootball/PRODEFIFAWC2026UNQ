"""
escudos_map.py

Devuelve la URL del escudo de cada equipo a partir del nombre "corto" que
usás en la base (equipos_clausura_2026.csv, tabla "equipos"/"partidos" en
Supabase).

Antes esto se resolvía en dos pasos (ALIAS -> nombre "lindo" -> lookup en
escudos.json), leyendo un archivo externo y cacheándolo con
@st.cache_data (sin TTL, por lo que quedaba cacheado para siempre y no
se enteraba de cambios en el JSON).

Ahora todo vive en un solo diccionario, ESCUDOS, hardcodeado acá abajo:
nombre_csv -> URL del escudo. No hay archivo que leer ni caché de por
medio, así que no puede quedar desactualizado ni fallar por no encontrar
escudos.json.

Si en algún momento cambiás/agregás un nombre en el CSV, o querés
actualizar una URL, editá el diccionario ESCUDOS de acá abajo.
"""

# nombre en la base (CSV) -> URL del escudo
ESCUDOS = {
    "Boca": "https://upload.wikimedia.org/wikipedia/commons/4/41/CABJ70.png",
    "Independiente": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Escudo_del_Club_Atl%C3%A9tico_Independiente_de_Avellaneda.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Independiente_de_Avellaneda.svg.png",
    "San Lorenzo": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Escudo_del_Club_Atl%C3%A9tico_San_Lorenzo_de_Almagro.svg/200px-Escudo_del_Club_Atl%C3%A9tico_San_Lorenzo_de_Almagro.svg.png",
    "Deportivo Riestra": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Escudo_del_Club_Deportivo_Riestra.svg/200px-Escudo_del_Club_Deportivo_Riestra.svg.png",
    "Talleres": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Escudo_Talleres_2015.svg/200px-Escudo_Talleres_2015.svg.png",
    "Instituto": "https://upload.wikimedia.org/wikipedia/commons/6/6d/Escudo_Instituto_Atletico_Central_Cordoba.png",
    "Platense": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/Club_Alt%C3%A9tico_Platense_crest_(2025).svg/200px-Club_Alt%C3%A9tico_Platense_crest_(2025).svg.png",
    "Estudiantes": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Escudo_del_Club_Estudiantes_de_La_Plata.svg/200px-Escudo_del_Club_Estudiantes_de_La_Plata.svg.png",
    "Gimnasia (Mza.)": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Escudo_Club_Gimnasia_y_Esgrima_Mendoza.svg/200px-Escudo_Club_Gimnasia_y_Esgrima_Mendoza.svg.png",
    "Vélez": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.svg/200px-Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.svg.png",
    "Newell's": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Escudo_del_Club_Atl%C3%A9tico_Newell%27s_Old_Boys_de_Rosario.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Newell%27s_Old_Boys_de_Rosario.svg.png",
    "Unión": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Escudo_club_Atl%C3%A9tico_Uni%C3%B3n_de_santa_fe.svg/200px-Escudo_club_Atl%C3%A9tico_Uni%C3%B3n_de_santa_fe.svg.png",
    "Lanús": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Escudo_de_Lan%C3%BAs_(sin_estrellas).svg/200px-Escudo_de_Lan%C3%BAs_(sin_estrellas).svg.png",
    "Central Córdoba": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Central_Cordoba_SdE_crest_(2025).svg/200px-Central_Cordoba_SdE_crest_(2025).svg.png",
    "Defensa y Justicia": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Escudo_del_Club_Social_y_Deportivo_Defensa_y_Justicia.svg/200px-Escudo_del_Club_Social_y_Deportivo_Defensa_y_Justicia.svg.png",
    "River": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Club_Atl%C3%A9tico_River_Plate_logo.svg/200px-Club_Atl%C3%A9tico_River_Plate_logo.svg.png",
    "Racing": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Escudo_de_Racing_Club_(2014).svg/200px-Escudo_de_Racing_Club_(2014).svg.png",
    "Huracán": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Emblema_oficial_del_Club_Atl%C3%A9tico_Hurac%C3%A1n.svg/200px-Emblema_oficial_del_Club_Atl%C3%A9tico_Hurac%C3%A1n.svg.png",
    "Barracas Central": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/99/Barracas_central_logo.svg/200px-Barracas_central_logo.svg.png",
    "Belgrano": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Club_Atl%C3%A9tico_Belgrano_2026.svg/200px-Club_Atl%C3%A9tico_Belgrano_2026.svg.png",
    "Estudiantes (Río Cuarto)": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Escudo_Asociacion_Atl%C3%A9tica_Estudiantes_de_R%C3%ADo_Cuarto.svg/200px-Escudo_Asociacion_Atl%C3%A9tica_Estudiantes_de_R%C3%ADo_Cuarto.svg.png",
    "Independiente Rivadavia": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Escudo_del_Club_Independiente_Rivadavia.svg/200px-Escudo_del_Club_Independiente_Rivadavia.svg.png",
    "Gimnasia": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/CGE_Logo_2026_v1.svg/200px-CGE_Logo_2026_v1.svg.png",
    "Tigre": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Escudo_del_Club_Atl%C3%A9tico_Tigre.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Tigre.svg.png",
    "Argentinos": "https://upload.wikimedia.org/wikipedia/commons/7/75/EscudoAAAJ.png",
    "Sarmiento": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Escudo_del_Club_Atl%C3%A9tico_Sarmiento_de_Jun%C3%ADn.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Sarmiento_de_Jun%C3%ADn.svg.png",
    "Rosario Central": "https://upload.wikimedia.org/wikipedia/commons/c/cc/Rosario_Central_shield.jpg",
    "Banfield": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Escudo_del_Club_Atl%C3%A9tico_Banfield.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Banfield.svg.png",
    "Atlético Tucumán": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Atletico_tucuman_nuevo2.svg/200px-Atletico_tucuman_nuevo2.svg.png",
    "Aldosivi": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Escudo_del_Club_Atl%C3%A9tico_Aldosivi.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Aldosivi.svg.png",
    # nombre alternativo / abreviado que puede venir de la BD
    "Ind. Rivadavia": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Escudo_del_Club_Independiente_Rivadavia.svg/200px-Escudo_del_Club_Independiente_Rivadavia.svg.png",
}


def url_escudo(nombre_csv: str):
    """
    Recibe el nombre tal cual está en la tabla "equipos"/"partidos" de
    Supabase (ej. "Boca", "River", "Talleres") y devuelve la URL del
    escudo, o None si no se encontró.
    """
    return ESCUDOS.get(nombre_csv)
