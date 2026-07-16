from database import conectar


def obtener_ranking():
    """
    Devuelve lista de dicts con el ranking de la Liga Profesional Argentina,
    ordenada de mayor a menor puntos.

    Sistema de puntaje (definido en 03_Fixture.py):
      - 1 punto si el pronóstico acierta el signo (Local / Empate / Visitante)
      - 3 puntos en total si el pronóstico acierta el marcador exacto

    Cada dict tiene:
      - nombre
      - puntos            (suma total de puntos)
      - aciertos          (partidos donde sumó al menos 1 punto, sea por
                            signo o por resultado exacto)
      - disputados        (partidos ya jugados sobre los que había pronóstico)
      - aciertos_exactos  (partidos donde acertó el marcador exacto, 3 pts)
    """
    sb = conectar()

    jugadores = sb.table("jugadores").select("id, nombre").execute().data or []

    partidos = (
        sb.table("partidos")
        .select("id, goles_local, goles_visitante")
        .execute()
        .data or []
    )
    partidos_por_id = {p["id"]: p for p in partidos}

    pronosticos = (
        sb.table("pronosticos")
        .select("jugador_id, partido_id, puntos")
        .execute()
        .data or []
    )

    pronosticos_por_jugador = {}
    for pr in pronosticos:
        pronosticos_por_jugador.setdefault(pr["jugador_id"], []).append(pr)

    ranking = []
    for j in jugadores:
        puntos_total     = 0
        aciertos         = 0
        disputados       = 0
        aciertos_exactos = 0

        for pr in pronosticos_por_jugador.get(j["id"], []):
            partido = partidos_por_id.get(pr["partido_id"])
            if not partido:
                continue

            gl_real = partido.get("goles_local")
            gv_real = partido.get("goles_visitante")
            if gl_real is None or gv_real is None:
                continue  # partido todavía no jugado: no cuenta como disputado

            disputados += 1
            pts = pr.get("puntos") or 0
            puntos_total += pts

            if pts >= 3:
                aciertos += 1
                aciertos_exactos += 1
            elif pts >= 1:
                aciertos += 1

        ranking.append({
            "nombre":           j["nombre"],
            "puntos":           puntos_total,
            "aciertos":         aciertos,
            "disputados":       disputados,
            "aciertos_exactos": aciertos_exactos,
        })

    ranking.sort(key=lambda x: x["puntos"], reverse=True)
    return ranking
