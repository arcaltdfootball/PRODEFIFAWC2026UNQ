"""
sync_resultados.py
──────────────────
Sincroniza los resultados oficiales de la FIFA World Cup 2026 desde
football-data.org hacia la tabla `partidos` en Supabase.

La lógica de mapeo convierte el score de la API al formato 1/X/2
que usa el prode:
  - goles local > goles visitante  → "1"
  - goles local == goles visitante → "X"
  - goles local < goles visitante  → "2"

Los nombres de equipos se normalizan con el diccionario TEAM_MAP para
que coincidan con los nombres que ya están cargados en la base de datos.
Si algún equipo no está en el diccionario se usa el nombre tal cual viene
de la API (en inglés), por lo que podés ampliarlo según necesites.

Uso desde 04_Admin.py (se importa y se llama a `sincronizar`):
    from sync_resultados import sincronizar
    resultado = sincronizar(sb)  # sb = cliente Supabase ya conectado
    # resultado es un dict con claves: actualizados, sin_partido, errores, detalle
"""

import requests
from datetime import datetime, timezone

# ── Configuración ─────────────────────────────────────────────────────────────
API_TOKEN       = "8c4e708b3dd747ad828f010e7cfae24f"
API_BASE        = "https://api.football-data.org/v4"
COMPETITION     = "WC"
HEADERS         = {"X-Auth-Token": API_TOKEN}

# ── Mapa de nombres API (inglés) → nombres en la BD (castellano) ──────────────
# Cubre todos los posibles nombres/alias que usa football-data.org
# para las 48 selecciones del Mundial 2026.
TEAM_MAP = {
    # ── GRUPO A ───────────────────────────────────────────────────────────────
    "United States":              "Estados Unidos",
    "United States of America":   "Estados Unidos",
    "USA":                        "Estados Unidos",
    "US":                         "Estados Unidos",
    "Mexico":                     "México",
    "México":                     "México",
    "Canada":                     "Canadá",
    "Panama":                     "Panamá",

    # ── GRUPO B ───────────────────────────────────────────────────────────────
    "Argentina":                  "Argentina",
    "Chile":                      "Chile",
    "Peru":                       "Perú",
    "Perú":                       "Perú",
    "Australia":                  "Australia",

    # ── GRUPO C ───────────────────────────────────────────────────────────────
    "Brazil":                     "Brasil",
    "Brasil":                     "Brasil",
    "Colombia":                   "Colombia",
    "Paraguay":                   "Paraguay",
    "Ecuador":                    "Ecuador",

    # ── GRUPO D ───────────────────────────────────────────────────────────────
    "France":                     "Francia",
    "England":                    "Inglaterra",
    "Senegal":                    "Senegal",
    "Morocco":                    "Marruecos",

    # ── GRUPO E ───────────────────────────────────────────────────────────────
    "Spain":                      "España",
    "Germany":                    "Alemania",
    "Japan":                      "Japón",
    "Costa Rica":                 "Costa Rica",

    # ── GRUPO F ───────────────────────────────────────────────────────────────
    "Portugal":                   "Portugal",
    "Netherlands":                "Países Bajos",
    "Holland":                    "Países Bajos",
    "Türkiye":                    "Turquía",
    "Turkey":                     "Turquía",
    "Czech Republic":             "República Checa",
    "Czechia":                    "República Checa",

    # ── GRUPO G ───────────────────────────────────────────────────────────────
    "Belgium":                    "Bélgica",
    "Croatia":                    "Croacia",
    "South Korea":                "Corea del Sur",
    "Korea Republic":             "Corea del Sur",
    "Republic of Korea":          "Corea del Sur",
    "Korea DPR":                  "Corea del Norte",
    "North Korea":                "Corea del Norte",
    "Uruguay":                    "Uruguay",

    # ── GRUPO H ───────────────────────────────────────────────────────────────
    "Serbia":                     "Serbia",
    "Switzerland":                "Suiza",
    "Nigeria":                    "Nigeria",
    "Cameroon":                   "Camerún",

    # ── GRUPO I ───────────────────────────────────────────────────────────────
    "Saudi Arabia":               "Arabia Saudita",
    "Egypt":                      "Egipto",
    "Ghana":                      "Ghana",
    "Venezuela":                  "Venezuela",

    # ── GRUPO J ───────────────────────────────────────────────────────────────
    "Denmark":                    "Dinamarca",
    "Iran":                       "Irán",
    "Islamic Republic of Iran":   "Irán",
    "IR Iran":                    "Irán",
    "Slovenia":                   "Eslovenia",
    "Bolivia":                    "Bolivia",

    # ── GRUPO K ───────────────────────────────────────────────────────────────
    "Poland":                     "Polonia",
    "Austria":                    "Austria",
    "Ukraine":                    "Ucrania",
    "Ivory Coast":                "Costa de Marfil",
    "Côte d'Ivoire":              "Costa de Marfil",
    "Cote d'Ivoire":              "Costa de Marfil",
    "Cote dIvoire":               "Costa de Marfil",

    # ── GRUPO L ───────────────────────────────────────────────────────────────
    "Qatar":                      "Catar",
    "New Zealand":                "Nueva Zelanda",
    "Algeria":                    "Argelia",
    "Honduras":                   "Honduras",

    # ── ALIAS EXTRA que puede usar la API ─────────────────────────────────────
    "Scotland":                   "Escocia",
    "Wales":                      "Gales",
    "Republic of Ireland":        "Irlanda",
    "Ireland":                    "Irlanda",
    "Russia":                     "Rusia",
    "Bosnia and Herzegovina":     "Bosnia y Herzegovina",
    "Bosnia & Herzegovina":       "Bosnia y Herzegovina",
    "North Macedonia":            "Macedonia del Norte",
    "Republic of North Macedonia":"Macedonia del Norte",
    "Albania":                    "Albania",
    "Romania":                    "Rumania",
    "Hungary":                    "Hungría",
    "Slovakia":                   "Eslovaquia",
    "Greece":                     "Grecia",
    "Sweden":                     "Suecia",
    "Norway":                     "Noruega",
    "Finland":                    "Finlandia",
    "Israel":                     "Israel",
    "Georgia":                    "Georgia",
    "Jamaica":                    "Jamaica",
    "Trinidad and Tobago":        "Trinidad y Tobago",
    "Cuba":                       "Cuba",
    "El Salvador":                "El Salvador",
    "Guatemala":                  "Guatemala",
    "Haiti":                      "Haití",
    "United Arab Emirates":       "Emiratos Árabes Unidos",
    "UAE":                        "Emiratos Árabes Unidos",
    "Iraq":                       "Irak",
    "Jordan":                     "Jordania",
    "Syria":                      "Siria",
    "Oman":                       "Omán",
    "Bahrain":                    "Bahréin",
    "Kuwait":                     "Kuwait",
    "Lebanon":                    "Líbano",
    "Indonesia":                  "Indonesia",
    "Thailand":                   "Tailandia",
    "Vietnam":                    "Vietnam",
    "China PR":                   "China",
    "China":                      "China",
    "Chinese Taipei":             "Taiwán",
    "India":                      "India",
    "Philippines":                "Filipinas",
    "Tanzania":                   "Tanzania",
    "Mozambique":                 "Mozambique",
    "Angola":                     "Angola",
    "Zambia":                     "Zambia",
    "Zimbabwe":                   "Zimbabue",
    "Kenya":                      "Kenia",
    "Ethiopia":                   "Etiopía",
    "Ivory Coast":                "Costa de Marfil",
    "South Africa":               "Sudáfrica",
    "Tunisia":                    "Túnez",
    "Mali":                       "Malí",
    "Burkina Faso":               "Burkina Faso",
    "Guinea":                     "Guinea",
    "Cape Verde":                 "Cabo Verde",
    "Cabo Verde":                 "Cabo Verde",
    "Gambia":                     "Gambia",
    "Uganda":                     "Uganda",
    "DR Congo":                   "Congo RD",
    "Congo DR":                   "Congo RD",
    "Democratic Republic of Congo": "Congo RD",
    "Republic of Congo":          "Congo",
    "Gabon":                      "Gabón",
    "Benin":                      "Benín",
    "Libya":                      "Libia",
}


def _score_a_resultado(score_data: dict) -> str | None:
    """
    Convierte el objeto score de la API al código 1/X/2.
    Usa `fullTime` como resultado principal; si está a None usa `regularTime`.
    Devuelve None si el partido no tiene marcador válido.
    """
    ft = score_data.get("fullTime") or {}
    home = ft.get("home")
    away = ft.get("away")

    if home is None or away is None:
        rt = score_data.get("regularTime") or {}
        home = rt.get("home")
        away = rt.get("away")

    if home is None or away is None:
        return None

    if home > away:
        return "1"
    elif home == away:
        return "X"
    else:
        return "2"


def _nombre_normalizado(nombre_api: str) -> str:
    return TEAM_MAP.get(nombre_api, nombre_api)


def obtener_partidos_finalizados() -> list[dict]:
    """
    Llama a la API y devuelve la lista de partidos con status FINISHED.
    Lanza excepción si hay error de red o HTTP.
    """
    url = f"{API_BASE}/competitions/{COMPETITION}/matches"
    params = {"status": "FINISHED"}
    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get("matches", [])


def sincronizar(sb) -> dict:
    """
    Sincroniza resultados finalizados de la API con la tabla `partidos`.

    Parámetros
    ----------
    sb : cliente Supabase (ya conectado)

    Retorna
    -------
    dict con:
        actualizados  : int  – partidos actualizados en la BD
        sin_partido   : list – nombres de partidos de la API sin match en BD
        errores       : list – errores individuales
        detalle       : list – descripción de cada actualización
    """
    resultado = {
        "actualizados": 0,
        "sin_partido":  [],
        "errores":      [],
        "detalle":      [],
    }

    # 1. Traer partidos finalizados desde la API
    try:
        matches_api = obtener_partidos_finalizados()
    except Exception as e:
        resultado["errores"].append(f"Error al consultar la API: {e}")
        return resultado

    if not matches_api:
        resultado["detalle"].append("La API no devolvió partidos finalizados.")
        return resultado

    # 2. Leer todos los partidos de la BD (una sola consulta)
    try:
        resp_bd = sb.table("partidos").select("id, local, visitante, resultado").execute()
        partidos_bd = resp_bd.data
    except Exception as e:
        resultado["errores"].append(f"Error al leer la BD: {e}")
        return resultado

    # Indexar por par (local, visitante) para búsqueda rápida
    # Guardamos en minúsculas para comparación case-insensitive
    indice_bd = {}
    for p in partidos_bd:
        clave = (p["local"].strip().lower(), p["visitante"].strip().lower())
        indice_bd[clave] = p

    # 3. Procesar cada partido finalizado de la API
    for m in matches_api:
        local_api    = m.get("homeTeam", {}).get("name", "") or ""
        visitante_api = m.get("awayTeam", {}).get("name", "") or ""

        local_bd    = _nombre_normalizado(local_api)
        visitante_bd = _nombre_normalizado(visitante_api)

        nuevo_resultado = _score_a_resultado(m.get("score", {}))
        if nuevo_resultado is None:
            continue  # partido sin marcador válido todavía

        clave = (local_bd.strip().lower(), visitante_bd.strip().lower())
        partido_en_bd = indice_bd.get(clave)

        if partido_en_bd is None:
            resultado["sin_partido"].append(f"{local_api} vs {visitante_api}")
            continue

        # Solo actualizar si el resultado cambió o está vacío
        if partido_en_bd.get("resultado") == nuevo_resultado:
            continue

        try:
            sb.table("partidos").update({"resultado": nuevo_resultado}).eq(
                "id", partido_en_bd["id"]
            ).execute()
            resultado["actualizados"] += 1
            resultado["detalle"].append(
                f"✅ {local_bd} vs {visitante_bd} → {nuevo_resultado}"
            )
        except Exception as e:
            resultado["errores"].append(
                f"Error al guardar {local_bd} vs {visitante_bd}: {e}"
            )

    return resultado


def test_conexion_api() -> dict:
    """
    Prueba rápida de conectividad con la API.
    Retorna dict con `ok` (bool) y `mensaje` (str).
    """
    try:
        url = f"{API_BASE}/competitions/{COMPETITION}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            nombre = data.get("name", "FIFA World Cup")
            return {"ok": True, "mensaje": f"Conectado: {nombre}"}
        else:
            return {
                "ok": False,
                "mensaje": f"HTTP {resp.status_code}: {resp.text[:200]}",
            }
    except Exception as e:
        return {"ok": False, "mensaje": str(e)}
