"""
escudos_map.py

Devuelve la URL del escudo de cada equipo, acepte el nombre "corto" (el que
usás en equipos_clausura_2026.csv / tabla "equipos"/"partidos" de Supabase,
ej. "Boca", "River", "Vélez") o el nombre "largo"/prolijo que a veces
aparece en otras fuentes de datos (ej. la tabla de posiciones), como
"Boca Juniors", "River Plate", "Vélez Sarsfield".

Todo vive en un solo diccionario, ESCUDOS, hardcodeado acá abajo: cada
entrada mapea uno o más nombres posibles a la URL del escudo. No hay
archivo externo que leer ni caché de por medio.

Importante sobre las URLs: usamos el archivo ORIGINAL de Wikimedia
Commons (ej. ".../commons/f/fc/Escudo_....svg"), NO la ruta de
miniatura "/thumb/.../200px-....png". El pipeline de miniaturas de
Wikimedia rompía la carga de casi todos los escudos en este proyecto;
el archivo original (SVG en la mayoría de los casos) carga siempre y
además se ve limpio: sin fondo, sin recuadro, solo el escudo, porque el
navegador lo renderiza nativamente en vez de mostrar un PNG rasterizado
que podía fallar.

Si en algún momento cambiás/agregás un nombre en el CSV o en otra
fuente, o querés actualizar una URL, editá el diccionario ESCUDOS_RAW
de acá abajo (agregá el/los alias que falten a la lista de nombres de
ese equipo).
"""

# Cada tupla: (URL del escudo, [todos los nombres posibles para ese equipo])
_ESCUDOS_RAW = [
    ("https://upload.wikimedia.org/wikipedia/commons/4/41/CABJ70.png",
     ["Boca", "Boca Juniors"]),
    ("https://upload.wikimedia.org/wikipedia/commons/3/38/Escudo_del_Club_Atl%C3%A9tico_Independiente_de_Avellaneda.svg",
     ["Independiente"]),
    ("https://upload.wikimedia.org/wikipedia/commons/7/77/Escudo_del_Club_Atl%C3%A9tico_San_Lorenzo_de_Almagro.svg",
     ["San Lorenzo"]),
    ("https://upload.wikimedia.org/wikipedia/commons/a/ab/Escudo_del_Club_Deportivo_Riestra.svg",
     ["Deportivo Riestra"]),
    ("https://upload.wikimedia.org/wikipedia/commons/9/9b/Escudo_Talleres_2015.svg",
     ["Talleres", "Talleres (Córdoba)"]),
    ("https://upload.wikimedia.org/wikipedia/commons/6/6d/Escudo_Instituto_Atletico_Central_Cordoba.png",
     ["Instituto", "Instituto (Córdoba)"]),
    ("https://upload.wikimedia.org/wikipedia/commons/d/db/Club_Alt%C3%A9tico_Platense_crest_(2025).svg",
     ["Platense"]),
    ("https://upload.wikimedia.org/wikipedia/commons/6/68/Escudo_del_Club_Estudiantes_de_La_Plata.svg",
     ["Estudiantes", "Estudiantes (LP)"]),
    ("https://upload.wikimedia.org/wikipedia/commons/1/13/Escudo_Club_Gimnasia_y_Esgrima_Mendoza.svg",
     ["Gimnasia (Mza.)", "Gimnasia y Esgrima (Mza)"]),
    ("https://upload.wikimedia.org/wikipedia/commons/2/21/Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.svg",
     ["Vélez", "Vélez Sarsfield"]),
    ("https://upload.wikimedia.org/wikipedia/commons/6/69/Escudo_del_Club_Atl%C3%A9tico_Newell%27s_Old_Boys_de_Rosario.svg",
     ["Newell's", "Newell's Old Boys"]),
    ("https://upload.wikimedia.org/wikipedia/commons/7/7c/Escudo_club_Atl%C3%A9tico_Uni%C3%B3n_de_santa_fe.svg",
     ["Unión", "Unión (Santa Fe)"]),
    ("https://upload.wikimedia.org/wikipedia/commons/a/a9/Escudo_de_Lan%C3%BAs_(sin_estrellas).svg",
     ["Lanús"]),
    ("https://upload.wikimedia.org/wikipedia/commons/9/92/Central_Cordoba_SdE_crest_(2025).svg",
     ["Central Córdoba", "Central Córdoba (SdE)"]),
    ("https://upload.wikimedia.org/wikipedia/commons/7/70/Escudo_del_Club_Social_y_Deportivo_Defensa_y_Justicia.svg",
     ["Defensa y Justicia"]),
    ("https://upload.wikimedia.org/wikipedia/commons/4/43/Club_Atl%C3%A9tico_River_Plate_logo.svg",
     ["River", "River Plate"]),
    ("https://upload.wikimedia.org/wikipedia/commons/5/56/Escudo_de_Racing_Club_(2014).svg",
     ["Racing", "Racing Club"]),
    ("https://upload.wikimedia.org/wikipedia/commons/d/dd/Emblema_oficial_del_Club_Atl%C3%A9tico_Hurac%C3%A1n.svg",
     ["Huracán"]),
    ("https://upload.wikimedia.org/wikipedia/commons/9/99/Barracas_central_logo.svg",
     ["Barracas Central"]),
    ("https://upload.wikimedia.org/wikipedia/commons/a/a7/Club_Atl%C3%A9tico_Belgrano_2026.svg",
     ["Belgrano", "Belgrano (Córdoba)"]),
    ("https://upload.wikimedia.org/wikipedia/commons/2/20/Escudo_Asociacion_Atl%C3%A9tica_Estudiantes_de_R%C3%ADo_Cuarto.svg",
     ["Estudiantes (Río Cuarto)"]),
    ("https://upload.wikimedia.org/wikipedia/commons/7/7f/Escudo_del_Club_Independiente_Rivadavia.svg",
     ["Independiente Rivadavia", "Ind. Rivadavia"]),
    ("https://upload.wikimedia.org/wikipedia/commons/e/ea/CGE_Logo_2026_v1.svg",
     ["Gimnasia", "Gimnasia y Esgrima (LP)"]),
    ("https://upload.wikimedia.org/wikipedia/commons/8/8a/Escudo_del_Club_Atl%C3%A9tico_Tigre.svg",
     ["Tigre"]),
    ("https://upload.wikimedia.org/wikipedia/commons/7/75/EscudoAAAJ.png",
     ["Argentinos", "Argentinos Juniors"]),
    ("https://upload.wikimedia.org/wikipedia/commons/9/92/Escudo_del_Club_Atl%C3%A9tico_Sarmiento_de_Jun%C3%ADn.svg",
     ["Sarmiento", "Sarmiento (Junín)"]),
    ("https://upload.wikimedia.org/wikipedia/commons/c/cc/Rosario_Central_shield.jpg",
     ["Rosario Central"]),
    ("https://upload.wikimedia.org/wikipedia/commons/a/a2/Escudo_del_Club_Atl%C3%A9tico_Banfield.svg",
     ["Banfield"]),
    ("https://upload.wikimedia.org/wikipedia/commons/9/92/Atletico_tucuman_nuevo2.svg",
     ["Atlético Tucumán"]),
    ("https://upload.wikimedia.org/wikipedia/commons/f/fc/Escudo_del_Club_Atl%C3%A9tico_Aldosivi.svg",
     ["Aldosivi"]),
]

# nombre (corto o largo) -> URL del escudo
ESCUDOS = {
    nombre: url
    for url, nombres in _ESCUDOS_RAW
    for nombre in nombres
}


def url_escudo(nombre_csv: str):
    """
    Recibe el nombre del equipo tal cual esté en la fuente de datos que
    se esté usando (nombre corto de la BD, ej. "Boca", o nombre largo,
    ej. "Boca Juniors") y devuelve la URL del escudo, o None si no se
    encontró ninguna coincidencia.
    """
    return ESCUDOS.get(nombre_csv)
