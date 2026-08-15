from database import conectar


def _signo(gl, gv):
    """Deriva el signo (1 / X / 2) a partir de un marcador. None si falta algún gol."""
    if gl is None or gv is None:
        return None
    if gl > gv:
        return "1"
    if gl == gv:
        return "X"
    return "2"


def _calcular_puntos(pr, partido):
    """
    Recalcula el puntaje de UN pronóstico contra el resultado real del partido,
    en vez de confiar en la columna `puntos` guardada en la tabla `pronosticos`.

    Por qué: `puntos` se escribe en dos momentos (cuando el jugador carga su
    pronóstico, y cuando el admin carga el resultado real y se recorren todos
    los pronósticos de ese partido para recalcularlos). Ese segundo recálculo
    hace un UPDATE por cada fila sin verificar que se haya grabado de verdad
    (a diferencia del resto de las escrituras de la app, que sí chequean con
    un SELECT fresco por los gotchas conocidos de Supabase/RLS). Si ese UPDATE
    falla en silencio para una fila puntual, esa fila queda con `puntos` viejo
    o NULL para siempre, aunque el jugador sí haya acertado.

    Recalculando acá, en el momento de armar el ranking, el resultado ya no
    depende de que esa escritura haya funcionado: siempre se compara el
    pronóstico real contra el resultado real.

    Devuelve:
      - None  si el partido todavía no se jugó (no cuenta como disputado)
      - 0, 1 o 3 puntos según corresponda
    """
    gl_real = partido.get("goles_local")
    gv_real = partido.get("goles_visitante")
    if gl_real is None or gv_real is None:
        return None  # partido todavía no jugado

    signo_real = _signo(gl_real, gv_real)

    gl_pred = pr.get("goles_local_pred")
    gv_pred = pr.get("goles_visitante_pred")
    sin_marcador = bool(pr.get("sin_marcador"))

    # Preferimos el signo_pred guardado; si por algún motivo no está, lo
    # derivamos del marcador cargado (compatibilidad con datos viejos).
    signo_pred = pr.get("signo_pred") or _signo(gl_pred, gv_pred)

    if signo_pred is None:
        # No hay ni signo guardado ni marcador para derivarlo: no hay
        # pronóstico real sobre el que calcular puntos.
        return 0

    if sin_marcador:
        # El jugador solo eligió Local/Empate/Visitante, sin cargar un
        # marcador exacto a mano. Tope de 1 punto, aunque el marcador
        # placeholder guardado internamente coincida por casualidad con
        # el resultado real: NUNCA debe dar los 3 puntos en ese caso.
        return 1 if signo_pred == signo_real else 0

    if gl_pred is not None and gv_pred is not None and gl_pred == gl_real and gv_pred == gv_real:
        return 3

    if signo_pred == signo_real:
        return 1

    return 0


def obtener_ranking():
    """
    Devuelve lista de dicts con el ranking de la Liga Profesional Argentina,
    ordenada de mayor a menor puntos.

    Sistema de puntaje:
      - 1 punto si el pronóstico acierta el signo (Local / Empate / Visitante)
      - 3 puntos en total si el pronóstico acierta el marcador exacto

    Los puntos se recalculan acá mismo a partir del pronóstico crudo contra
    el resultado real del partido (ver `_calcular_puntos`), en vez de leer
    directamente la columna `puntos` de la base, para que el ranking sea
    correcto aunque el recálculo que hace el admin al cargar un resultado
    haya fallado en silencio para algún pronóstico puntual.

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

    jugadores = sb.table("jugadores").select("id, nombre, pagado, activo").execute().data or []
    jugadores = [j for j in jugadores if j.get("pagado") and j.get("activo", True)]

    partidos = (
        sb.table("partidos")
        .select("id, goles_local, goles_visitante")
        .execute()
        .data or []
    )
    partidos_por_id = {p["id"]: p for p in partidos}

    pronosticos = (
        sb.table("pronosticos")
        .select(
            "jugador_id, partido_id, signo_pred, goles_local_pred, "
            "goles_visitante_pred, sin_marcador, puntos"
        )
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

            pts = _calcular_puntos(pr, partido)
            if pts is None:
                continue  # partido todavía no jugado: no cuenta como disputado

            disputados += 1
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
