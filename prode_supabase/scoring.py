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


def calcular_estadisticas_bulk(participante_ids: list[int]) -> dict[int, tuple]:
    """
    Calcula (puntos, aciertos, disputados) para todos los participantes
    en solo 2 queries a Supabase, en lugar de 2 queries por participante.

    Retorna: {participante_id: (puntos, aciertos, disputados)}
    """
    if not participante_ids:
        return {}

    sb = conectar()

    # 1 query: todos los pronósticos de los participantes pedidos
    resp_pron = (
        sb.table("pronosticos")
        .select("participante_id, partido_id, pronostico")
        .in_("participante_id", participante_ids)
        .execute()
    )

    # Mapear partido_ids únicos necesarios
    partido_ids = list({r["partido_id"] for r in resp_pron.data})
    if not partido_ids:
        return {pid: (0, 0, 0) for pid in participante_ids}

    # 1 query: todos los partidos relevantes
    resp_part = (
        sb.table("partidos")
        .select("id, resultado")
        .in_("id", partido_ids)
        .execute()
    )
    resultado_por_partido = {
        p["id"]: p.get("resultado") or ""
        for p in resp_part.data
    }

    # Acumular por participante
    stats: dict[int, list] = {pid: [0, 0, 0] for pid in participante_ids}  # [puntos, aciertos, disputados]
    for pr in resp_pron.data:
        pid = pr["participante_id"]
        if pid not in stats:
            continue
        resultado = resultado_por_partido.get(pr["partido_id"], "")
        if not resultado:
            continue
        stats[pid][2] += 1  # disputados
        if resultado == pr.get("pronostico"):
            stats[pid][0] += PUNTOS_ACIERTO  # puntos
            stats[pid][1] += 1               # aciertos

    return {pid: tuple(v) for pid, v in stats.items()}
