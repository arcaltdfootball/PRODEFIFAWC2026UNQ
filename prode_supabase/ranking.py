from database import conectar
from scoring import calcular_estadisticas_bulk


def obtener_ranking():
    """
    Devuelve lista de tuplas (nombre, puntos, aciertos, disputados)
    ordenada de mayor a menor puntos.

    Usa calcular_estadisticas_bulk() para resolver todos los puntajes
    en 2 queries a Supabase, sin importar cuántos participantes haya.
    """
    sb = conectar()
    resp = sb.table("participantes").select("id, nombre").execute()

    participantes = resp.data or []
    if not participantes:
        return []

    # Deduplicar por nombre (por si hay filas repetidas en Supabase)
    vistos = set()
    unicos = []
    for p in participantes:
        if p["nombre"] not in vistos:
            vistos.add(p["nombre"])
            unicos.append(p)

    ids = [p["id"] for p in unicos]
    stats = calcular_estadisticas_bulk(ids)  # {id: (puntos, aciertos, disputados)}

    ranking = [
        (p["nombre"], *stats.get(p["id"], (0, 0, 0)))
        for p in unicos
    ]
    ranking.sort(key=lambda x: x[1], reverse=True)
    return ranking
