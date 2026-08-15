from database import conectar


def _fetch_all(tabla_query_factory, tamano_pagina=1000):
    """
    Trae TODAS las filas de una consulta a Supabase, paginando con
    `.range()` en vez de confiar en un solo `.execute()`.

    Por qué hace falta esto: PostgREST (lo que usa Supabase por debajo)
    devuelve como máximo ~1000 filas por consulta por default, y lo hace
    EN SILENCIO — no tira ningún error, simplemente corta ahí. A medida
    que crecen `pronosticos` (jugadores × partidos disputados), en algún
    momento se cruza esa marca y las filas que quedan afuera son las más
    nuevas (las que Supabase devuelve al final), es decir los partidos
    más recientes. Eso hacía que jugadores con pronósticos correctos en
    la base (puntos bien calculados) igual dieran de menos en el Ranking,
    porque esas filas ni siquiera llegaban a Python para sumarse.

    `tabla_query_factory` es una función SIN argumentos que arma y
    devuelve una query nueva de supabase-py cada vez que se llama (hace
    falta una query nueva por página, no se puede reusar la misma).
    """
    todas_las_filas = []
    offset = 0
    while True:
        resp = tabla_query_factory().range(offset, offset + tamano_pagina - 1).execute()
        pagina = resp.data or []
        todas_las_filas.extend(pagina)
        if len(pagina) < tamano_pagina:
            break  # última página: vino incompleta, no hay más para traer
        offset += tamano_pagina
    return todas_las_filas


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

    Solo incluye jugadores HABILITADOS: que pagaron la inscripción
    (columna `pagado`) y que el admin no los ocultó/pausó (columna `activo`).
    """
    sb = conectar()

    jugadores = _fetch_all(lambda: sb.table("jugadores").select("id, nombre, pagado, activo"))
    jugadores = [j for j in jugadores if j.get("pagado") and j.get("activo", True)]

    partidos = _fetch_all(
        lambda: sb.table("partidos").select("id, goles_local, goles_visitante")
    )
    partidos_por_id = {p["id"]: p for p in partidos}

    pronosticos = _fetch_all(
        lambda: sb.table("pronosticos").select("jugador_id, partido_id, puntos")
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
