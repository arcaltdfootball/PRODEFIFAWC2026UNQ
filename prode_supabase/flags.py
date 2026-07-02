import unicodedata

FLAGS = {
    # Equipos en la DB
    "Alemania":            "https://hatscripts.github.io/circle-flags/flags/de.svg",
    "Arabia Saudi":        "https://hatscripts.github.io/circle-flags/flags/sa.svg",
    "Argelia":             "https://hatscripts.github.io/circle-flags/flags/dz.svg",
    "Argentina":           "https://hatscripts.github.io/circle-flags/flags/ar.svg",
    "Australia":           "https://hatscripts.github.io/circle-flags/flags/au.svg",
    "Austria":             "https://hatscripts.github.io/circle-flags/flags/at.svg",
    "Belgica":             "https://hatscripts.github.io/circle-flags/flags/be.svg",
    "Bosnia y Herzegovina":"https://hatscripts.github.io/circle-flags/flags/ba.svg",
    "Brasil":              "https://hatscripts.github.io/circle-flags/flags/br.svg",
    "Cabo Verde":          "https://hatscripts.github.io/circle-flags/flags/cv.svg",
    "Canada":              "https://hatscripts.github.io/circle-flags/flags/ca.svg",
    "Catar":               "https://hatscripts.github.io/circle-flags/flags/qa.svg",
    "Colombia":            "https://hatscripts.github.io/circle-flags/flags/co.svg",
    "Costa de Marfil":     "https://hatscripts.github.io/circle-flags/flags/ci.svg",
    "Croacia":             "https://hatscripts.github.io/circle-flags/flags/hr.svg",
    "Curazao":             "https://hatscripts.github.io/circle-flags/flags/cw.svg",
    "Ecuador":             "https://hatscripts.github.io/circle-flags/flags/ec.svg",
    "Egipto":              "https://hatscripts.github.io/circle-flags/flags/eg.svg",
    "Escocia":             "https://hatscripts.github.io/circle-flags/flags/gb-sct.svg",
    "Espana":              "https://hatscripts.github.io/circle-flags/flags/es.svg",
    "España":              "https://hatscripts.github.io/circle-flags/flags/es.svg",
    "Estados Unidos":      "https://hatscripts.github.io/circle-flags/flags/us.svg",
    "Francia":             "https://hatscripts.github.io/circle-flags/flags/fr.svg",
    "Ghana":               "https://hatscripts.github.io/circle-flags/flags/gh.svg",
    "Haiti":               "https://hatscripts.github.io/circle-flags/flags/ht.svg",
    "Inglaterra":          "https://hatscripts.github.io/circle-flags/flags/gb-eng.svg",
    "Irak":                "https://hatscripts.github.io/circle-flags/flags/iq.svg",
    "Iran":                "https://hatscripts.github.io/circle-flags/flags/ir.svg",
    "RI de Iran":          "https://hatscripts.github.io/circle-flags/flags/ir.svg",
    "Japon":               "https://hatscripts.github.io/circle-flags/flags/jp.svg",
    "Jordania":            "https://hatscripts.github.io/circle-flags/flags/jo.svg",
    "Marruecos":           "https://hatscripts.github.io/circle-flags/flags/ma.svg",
    "Mexico":              "https://hatscripts.github.io/circle-flags/flags/mx.svg",
    "Noruega":             "https://hatscripts.github.io/circle-flags/flags/no.svg",
    "Nueva Zelanda":       "https://hatscripts.github.io/circle-flags/flags/nz.svg",
    "Paises Bajos":        "https://hatscripts.github.io/circle-flags/flags/nl.svg",
    "Panama":              "https://hatscripts.github.io/circle-flags/flags/pa.svg",
    "Paraguay":            "https://hatscripts.github.io/circle-flags/flags/py.svg",
    "Portugal":            "https://hatscripts.github.io/circle-flags/flags/pt.svg",
    "RD Congo":            "https://hatscripts.github.io/circle-flags/flags/cd.svg",
    "Republica Checa":     "https://hatscripts.github.io/circle-flags/flags/cz.svg",
    "Republica de Corea":  "https://hatscripts.github.io/circle-flags/flags/kr.svg",
    "Senegal":             "https://hatscripts.github.io/circle-flags/flags/sn.svg",
    "Sudafrica":           "https://hatscripts.github.io/circle-flags/flags/za.svg",
    "Suecia":              "https://hatscripts.github.io/circle-flags/flags/se.svg",
    "Suiza":               "https://hatscripts.github.io/circle-flags/flags/ch.svg",
    "Tunez":               "https://hatscripts.github.io/circle-flags/flags/tn.svg",
    "Turquia":             "https://hatscripts.github.io/circle-flags/flags/tr.svg",
    "Uruguay":             "https://hatscripts.github.io/circle-flags/flags/uy.svg",
    "Uzbekistan":          "https://hatscripts.github.io/circle-flags/flags/uz.svg",

    # ── Alias / nombres alternativos comunes (mismo país, otra forma de escribirlo) ──
    "Arabia Saudita":      "https://hatscripts.github.io/circle-flags/flags/sa.svg",
    "Bélgica":             "https://hatscripts.github.io/circle-flags/flags/be.svg",
    "Corea del Sur":       "https://hatscripts.github.io/circle-flags/flags/kr.svg",
    "Corea":               "https://hatscripts.github.io/circle-flags/flags/kr.svg",
    "Iran":                "https://hatscripts.github.io/circle-flags/flags/ir.svg",
    "Irán":                "https://hatscripts.github.io/circle-flags/flags/ir.svg",
    "Republica Democratica del Congo": "https://hatscripts.github.io/circle-flags/flags/cd.svg",
    "RD del Congo":        "https://hatscripts.github.io/circle-flags/flags/cd.svg",
    "Congo":               "https://hatscripts.github.io/circle-flags/flags/cd.svg",
    "Holanda":             "https://hatscripts.github.io/circle-flags/flags/nl.svg",
    "Republica de Corea del Sur": "https://hatscripts.github.io/circle-flags/flags/kr.svg",
    "Turkiye":             "https://hatscripts.github.io/circle-flags/flags/tr.svg",
    "EE.UU.":              "https://hatscripts.github.io/circle-flags/flags/us.svg",
    "EEUU":                "https://hatscripts.github.io/circle-flags/flags/us.svg",
    "USA":                 "https://hatscripts.github.io/circle-flags/flags/us.svg",
}


def _normalizar(texto):
    """Saca acentos, espacios extra y pasa a minúsculas para poder
    comparar nombres de equipos aunque vengan escritos distinto
    (ej. 'España' vs 'espana ' vs 'ESPAÑA')."""
    if not texto:
        return ""
    texto = str(texto).strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower()


# Diccionario auxiliar con las claves normalizadas, para que la búsqueda
# no dependa de que el nombre en la base de datos tenga exactamente los
# mismos acentos/mayúsculas que acá.
_FLAGS_NORMALIZADAS = {_normalizar(k): v for k, v in FLAGS.items()}


def get_flag(nombre_equipo):
    """Devuelve la URL de la bandera de un equipo. Tolera diferencias de
    acentos, mayúsculas/minúsculas y espacios al inicio/final. Si no
    encuentra el equipo, devuelve '' (y el llamador debe mostrar un
    ícono de bandera genérico)."""
    clave = _normalizar(nombre_equipo)
    if not clave:
        return ""

    # 1) Coincidencia exacta (normalizada)
    if clave in _FLAGS_NORMALIZADAS:
        return _FLAGS_NORMALIZADAS[clave]

    # 2) Coincidencia parcial: por si el nombre viene con texto extra
    #    (ej. "Corea del Sur (Rep.)" o "Seleccion de Francia")
    for clave_dict, url in _FLAGS_NORMALIZADAS.items():
        if clave_dict in clave or clave in clave_dict:
            return url

    return ""
