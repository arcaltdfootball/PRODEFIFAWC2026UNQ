from database import conectar

PUNTOS_ACIERTO = 3


def calcular_estadisticas(participante_id: int):
    """Devuelve (puntos, aciertos, disputados)."""
    sb = conectar()

    resp_pron = (
        sb.table("pronosticos")
        .select("partido_id, pronostico")
        .eq("participante_id", participante_id)
        .execute()
    )
    pronosticos = {r["partido_id"]: r["pronostico"] for r in resp_pron.data}

    if not pronosticos:
        return 0, 0, 0

    partido_ids = list(pronosticos.keys())
    resp_part = (
        sb.table("partidos")
        .select("id, resultado")
        .in_("id", partido_ids)
        .execute()
    )

    puntos = aciertos = disputados = 0
    for partido in resp_part.data:
        resultado = partido.get("resultado") or ""
        if not resultado:
            continue
        disputados += 1
        if resultado == pronosticos.get(partido["id"], ""):
            puntos += PUNTOS_ACIERTO
            aciertos += 1

    return puntos, aciertos, disputados


def calcular_puntos(participante_id: int) -> int:
    puntos, _, _ = calcular_estadisticas(participante_id)
    return puntos
