from database import conectar
from scoring import calcular_estadisticas


def obtener_ranking():
    """
    Devuelve lista de tuplas (nombre, puntos, aciertos, disputados)
    ordenada de mayor a menor puntos.
    """
    sb = conectar()
    resp = sb.table("participantes").select("id, nombre").execute()

    ranking = []
    for p in resp.data:
        puntos, aciertos, disputados = calcular_estadisticas(p["id"])
        ranking.append((p["nombre"], puntos, aciertos, disputados))

    ranking.sort(key=lambda x: x[1], reverse=True)
    return ranking
