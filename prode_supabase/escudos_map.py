"""
escudos_map.py

Devuelve la URL del escudo de cada equipo, acepte el nombre "corto" (el que
usás en equipos_clausura_2026.csv / tabla "equipos"/"partidos" de Supabase,
ej. "Boca", "River", "Vélez") o el nombre "largo"/prolijo que a veces
aparece en otras fuentes de datos (ej. la tabla de posiciones), como
"Boca Juniors", "River Plate", "Vélez Sarsfield".

Historial de esta fuente de datos (por qué terminamos acá):
1) Al principio leíamos un JSON externo (escudos.json) generado por
   escudos_prode.py, con @st.cache_data sin TTL: quedaba cacheado para
   siempre y dependía de un archivo separado.
2) Después hardcodeamos URLs de Wikimedia Commons directamente acá, pero
   usando la ruta de miniatura ("/thumb/.../200px-....png"): ese pipeline
   de resize de Wikimedia fallaba para casi todos los escudos.
3) Cambiamos a los archivos ORIGINALES de Wikimedia (sin /thumb/), lo cual
   arregló la mayoría, pero varios (Aldosivi, Rosario Central, Argentinos
   Juniors) seguían con problemas: alguno directamente no cargaba, y otros
   (Rosario Central, Argentinos Juniors) son archivos JPG/PNG viejos con
   fondo BLANCO sólido en vez de transparente, porque nunca fueron subidos
   como PNG transparente en Commons.
4) Ahora usamos FootyLogos.com (footylogos.com), que aloja los 30 escudos
   de la Liga Profesional Argentina en un mismo CDN, en SVG, todos con
   fondo transparente garantizado y con un patrón de URL consistente y
   estable. Esto resuelve de raíz los tres problemas anteriores.

Si en algún momento cambiás/agregás un nombre en el CSV o en otra fuente,
o querés actualizar una URL, editá el diccionario _ESCUDOS_RAW de acá
abajo (agregá el/los alias que falten a la lista de nombres de ese
equipo, o el "slug" si cambia en footylogos.com).
"""

_BASE_URL = "https://pub-3bd35431294c47068cbf31a95d572166.r2.dev/logos/{slug}/{slug}-logo-footylogos.svg"

# Cada tupla: (slug en footylogos.com, [todos los nombres posibles para ese equipo])
_ESCUDOS_RAW = [
    ("boca-juniors", ["Boca", "Boca Juniors"]),
    ("independiente", ["Independiente"]),
    ("san-lorenzo", ["San Lorenzo"]),
    ("deportivo-riestra", ["Deportivo Riestra"]),
    ("talleres", ["Talleres", "Talleres (Córdoba)"]),
    ("instituto-cordoba", ["Instituto", "Instituto (Córdoba)"]),
    ("atletico-platense", ["Platense"]),
    ("estudiantes-de-la-plata", ["Estudiantes", "Estudiantes (LP)"]),
    ("gimnasia-y-esgrima", ["Gimnasia (Mza.)", "Gimnasia y Esgrima (Mza)"]),
    ("velez-sarsfield", ["Vélez", "Vélez Sarsfield"]),
    ("newells-old-boys", ["Newell's", "Newell's Old Boys"]),
    ("union", ["Unión", "Unión (Santa Fe)"]),
    ("lanus", ["Lanús"]),
    ("central-cordoba-se", ["Central Córdoba", "Central Córdoba (SdE)"]),
    ("defensa-y-justicia", ["Defensa y Justicia"]),
    ("river-plate", ["River", "River Plate"]),
    ("racing-club", ["Racing", "Racing Club"]),
    ("huracan", ["Huracán"]),
    ("barracas-central", ["Barracas Central"]),
    ("belgrano", ["Belgrano", "Belgrano (Córdoba)"]),
    ("estudiantes-de-rio-cuarto", ["Estudiantes (Río Cuarto)"]),
    ("independiente-rivadavia", ["Independiente Rivadavia", "Ind. Rivadavia"]),
    ("gimnasia-y-esgrima-lp", ["Gimnasia", "Gimnasia y Esgrima (LP)"]),
    ("tigre", ["Tigre"]),
    ("argentinos-juniors", ["Argentinos", "Argentinos Juniors"]),
    ("sarmiento", ["Sarmiento", "Sarmiento (Junín)"]),
    ("rosario-central", ["Rosario Central"]),
    ("banfield", ["Banfield"]),
    ("atletico-tucuman", ["Atlético Tucumán"]),
    ("aldosivi", ["Aldosivi"]),
]

# nombre (corto o largo) -> URL del escudo
ESCUDOS = {
    nombre: _BASE_URL.format(slug=slug)
    for slug, nombres in _ESCUDOS_RAW
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
