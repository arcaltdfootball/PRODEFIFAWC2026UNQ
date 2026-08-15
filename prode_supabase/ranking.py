from database import conectar


def _to_int(v):
    """
    Convierte a int de forma tolerante. Soluciona el caso en que un gol
    haya quedado guardado como texto ("3") en vez de número (3): en Python
    `3 == "3"` da False, así que sin este cast un marcador exacto podía
    NUNCA calzar con el resultado real y jamás dar los 3 puntos, aunque el
    jugador hubiera acertado perfecto.
    """
    if v is None:
        return None
    if isinstance(v, bool):  # bool es subclase de int en Python; evitar confusiones
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _to_key(v):
    """
    Normaliza un id (de jugador o de partido) a string para usarlo como
    clave de diccionario. Soluciona el caso en que el mismo id venga con
    tipos distintos entre tablas (ej. `partidos.id` como número y
    `pronosticos.partido_id` como texto, o un UUID con mayúsculas/espacios
    distintos): sin normalizar, el lookup fallaba en silencio y ese
    pronóstico se salteaba directo, como si no existiera.
    """
    if v is None:
        return None
    return str(v).strip()


def _signo(gl, gv):
    """Deriva el signo (1 / X / 2) a partir de un marcador. None si falta algún gol."""
    gl, gv = _to_int(gl), _to_int(gv)
    if gl is None or gv is None:
        return None
    if gl > gv:
        return "1"
    if gl == gv:
        return "X"
    return "2"


def _normalizar_signo(s):
    """Normaliza el signo guardado ('1'/'X'/'2') tolerando espacios o
    mayúsculas/minúsculas distintas, para que la comparación no falle por
    un detalle de formato."""
    if s is None:
        return None
    s = str(s).strip().upper()
    return s if s in ("1", "X", "2") else None


def _calcular_puntos(pr, partido):
    """
    Recalcula el puntaje de UN pronóstico contra el resultado real del
    partido, en vez de confiar en la columna `puntos` guardada en
    `pronosticos` (que puede quedar desactualizada si el UPDATE que hace
    el admin al cargar un resultado falla en silencio para alguna fila).

    Devuelve:
      - None  si el partido todavía no se jugó (no cuenta como disputado)
      - 0, 1 o 3 puntos según corresponda
    """
    gl_real = _to_int(partido.get("goles_local"))
    gv_real = _to_int(partido.get("goles_visitante"))
    if gl_real is None or gv_real is None:
        return None  # partido todavía no jugado

    signo_real = _signo(gl_real, gv_real)

    gl_pred = _to_int(pr.get("goles_local_pred"))
    gv_pred = _to_int(pr.get("goles_visitante_pred"))
    sin_marcador = bool(pr.get("sin_marcador"))

    # Preferimos el signo_pred guardado; si por algún motivo no está (o no
    # es un valor válido), lo derivamos del marcador cargado.
    signo_pred = _normalizar_signo(pr.get("signo_pred")) or _signo(gl_pred, gv_pred)

    if signo_pred is None:
        return 0  # no hay pronóstico real sobre el que calcular puntos

    if sin_marcador:
        # Solo eligió Local/Empate/Visitante, sin marcador exacto a mano.
        # Tope de 1 punto, aunque el placeholder interno coincida con el
        # resultado real por casualidad: NUNCA debe dar 3 puntos acá.
        return 1 if signo_pred == signo_real else 0

    if gl_pred is not None and gv_pred is not None and gl_pred == gl_real and gv_pred == gv_real:
        return 3

    if signo_pred == signo_real:
        return 1

    return 0


def _cargar_datos_base():
    """Trae jugadores habilitados, partidos y pronósticos, con los ids
    normalizados a string para poder cruzarlos sin que un tipo de dato
    distinto entre tablas haga que algo se pierda en silencio.

    Además DEDUPLICA: si por lo que sea quedaron dos filas en `pronosticos`
    para el mismo (jugador, partido) — típicamente por una condición de
    carrera al guardar (dos guardados casi simultáneos que no se vieron el
    uno al otro en el caché en memoria y terminaron haciendo un INSERT cada
    uno en vez de un UPDATE) — nos quedamos con UNA sola fila por partido.
    Sin este paso, un jugador con una fila duplicada para un mismo partido
    contaba ESE partido dos veces como "disputado" y sumaba sus puntos dos
    veces, lo que infla su cantidad de partidos disputados por encima del
    total real de partidos jugados — exactamente el patrón de "un jugador
    tiene más partidos disputados que otro" cuando todos jugaron el mismo
    fixture.
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
    partidos_por_id = {_to_key(p["id"]): p for p in partidos}

    pronosticos = (
        sb.table("pronosticos")
        .select(
            "id, jugador_id, partido_id, signo_pred, goles_local_pred, "
            "goles_visitante_pred, sin_marcador, puntos"
        )
        .execute()
        .data or []
    )

    # Paso 1: agrupar por jugador, y DENTRO de cada jugador por partido, para
    # poder detectar y descartar duplicados de (jugador, partido).
    crudo_por_jugador = {}
    for pr in pronosticos:
        jkey = _to_key(pr["jugador_id"])
        crudo_por_jugador.setdefault(jkey, {}).setdefault(_to_key(pr["partido_id"]), []).append(pr)

    duplicados = []  # para diagnóstico: qué (jugador, partido) tenían más de una fila
    pronosticos_por_jugador = {}
    for jkey, por_partido in crudo_por_jugador.items():
        pronosticos_por_jugador[jkey] = []
        for pkey, filas in por_partido.items():
            if len(filas) > 1:
                # Nos quedamos con la fila de mayor `id` (la más reciente,
                # asumiendo id autoincremental), que es la que más chances
                # tiene de reflejar el último pronóstico realmente cargado.
                elegida = max(filas, key=lambda f: f.get("id") or 0)
                duplicados.append({
                    "jugador_id": pr_jugador_id_original(filas),
                    "partido_id": elegida["partido_id"],
                    "ids_duplicados": [f.get("id") for f in filas],
                })
            else:
                elegida = filas[0]
            pronosticos_por_jugador[jkey].append(elegida)

    return jugadores, partidos_por_id, pronosticos_por_jugador, duplicados


def pr_jugador_id_original(filas):
    """Devuelve el jugador_id (sin normalizar) de un grupo de filas, para
    mostrarlo tal cual en el diagnóstico."""
    return filas[0].get("jugador_id") if filas else None


def obtener_ranking():
    """
    Devuelve lista de dicts con el ranking de la Liga Profesional Argentina,
    ordenada de mayor a menor puntos.

    Sistema de puntaje:
      - 1 punto si el pronóstico acierta el signo (Local / Empate / Visitante)
      - 3 puntos en total si el pronóstico acierta el marcador exacto

    Los puntos se recalculan acá mismo a partir del pronóstico crudo contra
    el resultado real del partido (ver `_calcular_puntos`), con los ids
    normalizados (ver `_to_key`) y los goles convertidos a número de forma
    tolerante (ver `_to_int`), para que el ranking sea correcto aunque haya
    inconsistencias de tipo entre columnas o algún UPDATE previo haya
    fallado en silencio.

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
    jugadores, partidos_por_id, pronosticos_por_jugador, _duplicados = _cargar_datos_base()

    ranking = []
    for j in jugadores:
        puntos_total     = 0
        aciertos         = 0
        disputados       = 0
        aciertos_exactos = 0

        for pr in pronosticos_por_jugador.get(_to_key(j["id"]), []):
            partido = partidos_por_id.get(_to_key(pr["partido_id"]))
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


def diagnosticar_ranking():
    """
    Recorre TODOS los pronósticos de jugadores habilitados y devuelve una
    lista de anomalías concretas, para poder ver en pantalla (sin tocar la
    base de datos a mano) qué está pasando en casos puntuales:

      - "partido_no_encontrado": el pronóstico apunta a un partido_id que
        no aparece en la tabla `partidos` (aunque se normalicen los ids a
        string). Esto hace que ese pronóstico NUNCA se compute, ni bien ni
        mal — el síntoma de "no le computa partidos jugados".

      - "puntos_guardados_no_coinciden": el partido ya está jugado y el
        puntaje recalculado en vivo NO coincide con lo que quedó guardado
        en la columna `puntos` de la base. Esto es la huella de un UPDATE
        que falló en silencio al cargar el resultado (o de un pronóstico
        cargado/editado después de guardado el resultado).

    Cada anomalía trae jugador_id, partido_id y el detalle, para poder
    ir directo a esa fila en Supabase si hace falta.

    Además del cruce por pronóstico, agrega dos chequeos a nivel jugador:

      - "pronostico_duplicado": el jugador tenía DOS (o más) filas en
        `pronosticos` para el mismo partido. Esto infla su cantidad de
        partidos disputados y sus puntos (se contaba el mismo partido más
        de una vez) — es la causa más probable de que en el ranking un
        jugador aparezca con MÁS partidos disputados que el total real de
        partidos jugados, o más que otros jugadores del mismo fixture.

      - "partido_jugado_sin_pronostico": el partido ya se jugó pero no se
        encontró ningún pronóstico de ese jugador para él (ni siquiera con
        un id "raro" — genuinamente no hay fila). Es la causa más probable
        de que a un jugador le falten partidos disputados respecto a otros.
    """
    jugadores, partidos_por_id, pronosticos_por_jugador, duplicados = _cargar_datos_base()
    nombres_por_id = {_to_key(j["id"]): j["nombre"] for j in jugadores}

    anomalias = []

    for d in duplicados:
        nombre = nombres_por_id.get(_to_key(d["jugador_id"]), f"jugador_id={d['jugador_id']!r}")
        anomalias.append({
            "jugador": nombre,
            "partido_id": d["partido_id"],
            "motivo": "pronostico_duplicado",
            "detalle": (
                f"{nombre} tiene {len(d['ids_duplicados'])} filas en "
                f"`pronosticos` para el mismo partido_id={d['partido_id']!r} "
                f"(ids: {d['ids_duplicados']}). El ranking ahora usa solo "
                "una (la de id más alto), pero convendría borrar la(s) "
                "fila(s) duplicada(s) de más directamente en Supabase."
            ),
        })

    partidos_jugados_ids = {
        pkey for pkey, p in partidos_por_id.items()
        if p.get("goles_local") is not None and p.get("goles_visitante") is not None
    }

    for jid_key, pronos in pronosticos_por_jugador.items():
        if jid_key not in nombres_por_id:
            continue  # jugador no habilitado (pagado/activo) o no encontrado
        nombre = nombres_por_id[jid_key]

        partidos_con_pronostico = {_to_key(pr["partido_id"]) for pr in pronos}
        faltantes = partidos_jugados_ids - partidos_con_pronostico
        if faltantes:
            anomalias.append({
                "jugador": nombre,
                "partido_id": sorted(faltantes),
                "motivo": "partido_jugado_sin_pronostico",
                "detalle": (
                    f"{nombre} no tiene ningún pronóstico cargado para "
                    f"{len(faltantes)} partido(s) ya jugado(s) "
                    f"(partido_id: {sorted(faltantes)}). Si el jugador "
                    "dice que sí los cargó, revisar esas filas en "
                    "`pronosticos` — puede que el jugador_id o partido_id "
                    "hayan quedado mal guardados."
                ),
            })

        for pr in pronos:
            partido = partidos_por_id.get(_to_key(pr["partido_id"]))
            if not partido:
                anomalias.append({
                    "jugador": nombre,
                    "partido_id": pr["partido_id"],
                    "motivo": "partido_no_encontrado",
                    "detalle": (
                        f"El pronóstico de {nombre} apunta a partido_id="
                        f"{pr['partido_id']!r}, que no existe (o no calza "
                        "de tipo) en la tabla `partidos`. Este pronóstico "
                        "nunca se computa en el ranking."
                    ),
                })
                continue

            pts_calculado = _calcular_puntos(pr, partido)
            if pts_calculado is None:
                continue  # partido no jugado, nada que comparar

            pts_guardado = pr.get("puntos")
            if pts_guardado != pts_calculado:
                anomalias.append({
                    "jugador": nombre,
                    "partido_id": pr["partido_id"],
                    "motivo": "puntos_guardados_no_coinciden",
                    "detalle": (
                        f"{nombre} — partido_id={pr['partido_id']!r}: el "
                        f"puntaje guardado en la base es {pts_guardado!r} "
                        f"pero el recalculado a partir del pronóstico real "
                        f"es {pts_calculado}. El ranking ya usa el valor "
                        "recalculado, así que esto no afecta el ranking, "
                        "pero indica una fila con `puntos` desactualizado "
                        "en la tabla `pronosticos`."
                    ),
                })

    return anomalias
