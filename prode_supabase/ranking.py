from database import conectar
from scoring import calcular_estadisticas_desglose


def obtener_ranking():
    """
    Devuelve lista de dicts con puntos totales y desglose por fase,
    ordenada de mayor a menor puntos.
    """
    sb = conectar()
    resp = sb.table("participantes").select("id, nombre").execute()

    ranking = []
    for p in resp.data:
        desglose = calcular_estadisticas_desglose(p["id"])
        ranking.append({
            "nombre":            p["nombre"],
            "puntos":            desglose["total"]["puntos"],
            "aciertos":          desglose["total"]["aciertos"],
            "disputados":        desglose["total"]["disputados"],
            "pts_grupos":        desglose["grupos"]["puntos"],
            "ac_grupos":         desglose["grupos"]["aciertos"],
            "dis_grupos":        desglose["grupos"]["disputados"],
            "pts_dieciseisavos": desglose["dieciseisavos"]["puntos"],
            "ac_dieciseisavos":  desglose["dieciseisavos"]["aciertos"],
            "dis_dieciseisavos": desglose["dieciseisavos"]["disputados"],
        })

    ranking.sort(key=lambda x: x["puntos"], reverse=True)
    return ranking
