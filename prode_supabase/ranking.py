from datetime import datetime
from zoneinfo import ZoneInfo

from database import conectar

TZ_ARG = ZoneInfo("America/Argentina/Buenos_Aires")

_MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


def obtener_mes_actual_label():
    """
    Devuelve el mes calendario en curso como texto, ej. "Septiembre 2026"
    (hora Argentina). Se usa tanto acá adentro (`obtener_ranking_mes_actual`)
    como en la home (`app.py`) para rotular la tarjeta del pozo, así los dos
    lugares siempre muestran exactamente el mismo mes sin duplicar lógica.
    """
    hoy = datetime.now(TZ_ARG).date()
    return f"{_MESES_ES[hoy.month]} {hoy.year}"


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


def obtener_ranking_mes_actual():
    """
    Igual que `obtener_ranking()`, pero contando SOLO los partidos cuya
    Fecha (jornada) está asignada al mes calendario en curso en la tabla
    `fecha_mes_map` (la que se carga en la pestaña "Meses" del admin).

    Por qué hace falta esto aparte: `obtener_ranking()` sirve para el
    ranking general/histórico de la temporada (usado en otras páginas), y
    ahí está bien que sume TODOS los partidos ya jugados. Pero en la home,
    la tarjeta "Premio total acumulado" quiere mostrar el líder DEL MES EN
    CURSO — y si `obtener_ranking()` no distingue por mes, apenas arranca
    un mes nuevo esa tarjeta seguía mostrando al líder del mes anterior
    con sus puntos ya acumulados, en vez de arrancar en 0 hasta que se
    jueguen y carguen los primeros resultados del mes nuevo.

    Si todavía no hay ninguna Fecha del mes en curso asignada en
    `fecha_mes_map` (o ninguno de esos partidos tiene resultado cargado
    todavía), devuelve a todos los jugadores habilitados con 0 puntos —
    que es exactamente lo que se quiere mostrar en ese caso.
    """
    sb = conectar()

    jugadores = _fetch_all(lambda: sb.table("jugadores").select("id, nombre, pagado, activo"))
    jugadores = [j for j in jugadores if j.get("pagado") and j.get("activo", True)]

    mes_actual = obtener_mes_actual_label().strip().lower()

    mapa_meses = _fetch_all(lambda: sb.table("fecha_mes_map").select("fecha_numero, mes"))
    fechas_del_mes_actual = {
        r["fecha_numero"] for r in mapa_meses
        if (r.get("mes") or "").strip().lower() == mes_actual
    }

    partidos = _fetch_all(
        lambda: sb.table("partidos").select("id, fecha_numero, goles_local, goles_visitante")
    )
    # Solo partidos cuya Fecha está asignada al mes en curso.
    partidos_por_id = {
        p["id"]: p for p in partidos
        if p.get("fecha_numero") in fechas_del_mes_actual
    }

    pronosticos = _fetch_all(
        lambda: sb.table("pronosticos").select("jugador_id, partido_id, puntos")
    )

    pronosticos_por_jugador = {}
    for pr in pronosticos:
        # Descartamos de una los pronósticos de partidos que no son del mes
        # en curso: así el jugador con 0 partidos del mes nuevo directamente
        # no entra al loop de abajo y queda en 0.
        if pr["partido_id"] not in partidos_por_id:
            continue
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
