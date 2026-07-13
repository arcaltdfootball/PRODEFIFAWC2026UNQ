"""
escudos_prode.py

Descarga los escudos de los 30 equipos de la Primera División de Argentina
(temporada 2026) desde Wikipedia/Wikimedia Commons y genera:

  1. Una carpeta "escudos/" con cada escudo guardado como archivo local.
  2. Un archivo "escudos.json" con el mapeo {nombre_equipo: url_del_escudo}
     para que lo levante tu prode directamente (por ejemplo, para mostrar
     el escudo al lado de cada partido).

No necesita API key. Solo requiere el paquete "requests":
    pip install requests

Uso:
    python escudos_prode.py
"""

import json
import os
import time
import unicodedata

import requests

# Nombre del artículo en Wikipedia en español -> nombre "lindo" para mostrar
EQUIPOS = {
    "Club Atlético Boca Juniors": "Boca Juniors",
    "Club Atlético River Plate": "River Plate",
    "Racing Club": "Racing Club",
    "Club Atlético Independiente": "Independiente",
    "Club Atlético San Lorenzo de Almagro": "San Lorenzo",
    "Club Atlético Huracán": "Huracán",
    "Club Atlético Vélez Sarsfield": "Vélez Sarsfield",
    "Club Estudiantes de La Plata": "Estudiantes (LP)",
    "Club de Gimnasia y Esgrima La Plata": "Gimnasia y Esgrima (LP)",
    "Club Atlético Newell's Old Boys": "Newell's Old Boys",
    "Club Atlético Rosario Central": "Rosario Central",
    "Club Atlético Talleres (Córdoba)": "Talleres (Córdoba)",
    "Club Atlético Belgrano": "Belgrano (Córdoba)",
    "Instituto Atlético Central Córdoba": "Instituto (Córdoba)",
    "Asociación Atlética Argentinos Juniors": "Argentinos Juniors",
    "Club Atlético Platense": "Platense",
    "Club Atlético Banfield": "Banfield",
    "Club Atlético Lanús": "Lanús",
    "Club Atlético Tigre": "Tigre",
    "Barracas Central": "Barracas Central",
    "Club Central Córdoba (Santiago del Estero)": "Central Córdoba (SdE)",
    "Club Atlético Independiente Rivadavia": "Independiente Rivadavia",
    "Club de Gimnasia y Esgrima (Mendoza)": "Gimnasia y Esgrima (Mza)",
    "Club Deportivo Riestra": "Deportivo Riestra",
    "Club Atlético Unión (Santa Fe)": "Unión (Santa Fe)",
    "Club Atlético Sarmiento (Junín)": "Sarmiento (Junín)",
    "Club Atlético Tucumán": "Atlético Tucumán",
    "Club Atlético Aldosivi": "Aldosivi",
    "Estudiantes de Río Cuarto": "Estudiantes (Río Cuarto)",
    "Club Social y Deportivo Defensa y Justicia": "Defensa y Justicia",
}

WIKI_API = "https://es.wikipedia.org/w/api.php"
OUTPUT_DIR = "escudos"
JSON_PATH = "escudos.json"

# Wikimedia rechaza (403) los pedidos sin un User-Agent identificado.
# Ver: https://meta.wikimedia.org/wiki/User-Agent_policy
HEADERS = {
    "User-Agent": "ProdeAFA2026Bot/1.0 (uso personal, no comercial; "
                  "contacto: ale.otero.prode@example.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/*,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Referer": "https://es.wikipedia.org/",
}


def slugify(texto: str) -> str:
    """Convierte el nombre del equipo en un nombre de archivo seguro."""
    nfkd = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in nfkd if not unicodedata.combining(c))
    return (
        sin_tildes.lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("'", "")
    )


def obtener_url_escudo(titulo_articulo: str) -> str | None:
    """
    Busca en el artículo de Wikipedia la imagen principal (el escudo del
    club) y devuelve la URL del archivo original (SVG casi siempre).

    Si el artículo no tiene una "imagen principal" detectada automáticamente
    (pasa en algunos artículos con infoboxes atípicas), busca entre todas
    las imágenes de la página alguna que parezca un escudo/logo.
    """
    params = {
        "action": "query",
        "titles": titulo_articulo,
        "prop": "pageimages",
        "piprop": "original",
        "format": "json",
        "redirects": 1,
    }
    resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    paginas = data.get("query", {}).get("pages", {})
    for pagina in paginas.values():
        original = pagina.get("original")
        if original:
            return original.get("source")

    # ── Respaldo: listar todas las imágenes de la página y quedarnos con
    # la primera que parezca un escudo/logo por su nombre de archivo ──
    return _buscar_imagen_de_respaldo(titulo_articulo)


PALABRAS_CLAVE_ESCUDO = ("escudo", "logo", "crest", "badge", "emblema")


def _buscar_imagen_de_respaldo(titulo_articulo: str) -> str | None:
    params = {
        "action": "query",
        "titles": titulo_articulo,
        "prop": "images",
        "imlimit": "50",
        "format": "json",
        "redirects": 1,
    }
    resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    paginas = data.get("query", {}).get("pages", {})
    candidatos = []
    for pagina in paginas.values():
        for img in pagina.get("images", []):
            titulo_archivo = img.get("title", "")
            if any(palabra in titulo_archivo.lower() for palabra in PALABRAS_CLAVE_ESCUDO):
                candidatos.append(titulo_archivo)

    for titulo_archivo in candidatos:
        params_info = {
            "action": "query",
            "titles": titulo_archivo,
            "prop": "imageinfo",
            "iiprop": "url",
            "format": "json",
        }
        resp2 = requests.get(WIKI_API, params=params_info, headers=HEADERS, timeout=15)
        resp2.raise_for_status()
        data2 = resp2.json()
        paginas2 = data2.get("query", {}).get("pages", {})
        for pagina2 in paginas2.values():
            imageinfo = pagina2.get("imageinfo")
            if imageinfo:
                return imageinfo[0].get("url")
    return None


def descargar_archivo(url: str, destino: str) -> None:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    with open(destino, "wb") as f:
        f.write(resp.content)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    resultado = {}

    for titulo_wiki, nombre_lindo in EQUIPOS.items():
        print(f"Buscando escudo de {nombre_lindo}...")
        try:
            url = obtener_url_escudo(titulo_wiki)
            if not url:
                print(f"  -> No se encontró imagen para {nombre_lindo}")
                continue

            # Lo único que necesita la app es la URL: la guardamos ya mismo,
            # así el JSON queda completo aunque falle la descarga local.
            resultado[nombre_lindo] = {"url": url, "archivo_local": None}
            print(f"  -> URL OK: {url}")

            # Descarga local best-effort (respaldo, NO la usa la app).
            # Si el CDN de imágenes de Wikimedia bloquea el pedido (403 u
            # otro error), no pasa nada: seguimos con el resto de equipos.
            try:
                extension = url.split(".")[-1].split("?")[0]
                nombre_archivo = f"{slugify(nombre_lindo)}.{extension}"
                ruta_destino = os.path.join(OUTPUT_DIR, nombre_archivo)
                descargar_archivo(url, ruta_destino)
                resultado[nombre_lindo]["archivo_local"] = ruta_destino
                print(f"     (respaldo local guardado en {ruta_destino})")
            except requests.RequestException as e_dl:
                status = getattr(getattr(e_dl, "response", None), "status_code", "sin respuesta")
                print(f"     (no se pudo guardar el respaldo local, status {status} — no afecta a la app)")

        except requests.RequestException as e:
            status = getattr(getattr(e, "response", None), "status_code", "sin respuesta")
            print(f"  -> Error con {nombre_lindo} (status {status}): {e}")

        # Pequeña pausa para no saturar la API de Wikipedia
        time.sleep(0.3)

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"\nListo. {len(resultado)}/{len(EQUIPOS)} URLs de escudos guardadas en {JSON_PATH}.")
    print(f"Carpeta de respaldo local: {OUTPUT_DIR}/ (puede estar incompleta, no afecta a la app)")


if __name__ == "__main__":
    main()
