from database import conectar

PUNTOS_RESULTADO = 1   # Acertó local/empate/visitante
PUNTOS_EXACTO    = 3   # Acertó marcador exacto (incluye el resultado)


def _resultado_desde_marcador(marcador: str) -> str:
    """
    Convierte "2-1" → "1", "1-1" → "X", "0-2" → "2".
    Devuelve "" si no se puede parsear.
    """
    if not marcador or "-" not in str(marcador):
        return ""
    try:
        partes = str(marcador).split("-")
        gl = int(partes[0])
        gv = int(partes[1])
        if gl > gv:
            return "1"
        elif gl == gv:
            return "X"
        else:
            return "2"
    except (ValueError, IndexError):
        return ""


def _calcular_fase(sb, tabla_pron: str, tabla_part: str, id_col_pron: str, id_col_part: str, participante_id: int):
    """
    Lógica común para calcular puntos de una fase.
    - tabla_pron:   nombre de la tabla de pronósticos (ej. "pronosticos" o "pronosticos_dieciseisavos")
    - tabla_part:   nombre de la tabla de partidos/cruces (ej. "partidos" o "dieciseisavos")
    - id_col_pron:  columna de FK al partido en la tabla de pronósticos (ej. "partido_id" o "cruce_id")
    - id_col_part:  columna PK de la tabla de partidos (ej. "id")

    La tabla de pronósticos debe tener la columna "pronostico" con formato "GL-GV".
    La tabla de partidos/cruces debe tener "resultado" (1/X/2) O "marcador" (GL-GV)
    O "goles_local"/"goles_visitante" para derivar el resultado.

    Devuelve (puntos, aciertos, disputados).
    """
    resp_pron = (
        sb.table(tabla_pron)
        .select(id_col_pron + ", pronostico")
        .eq("participante_id", participante_id)
        .execute()
    )

    if not resp_pron.data:
        return 0, 0, 0

    pron_dict = {r[id_col_pron]: r["pronostico"] for r in resp_pron.data}
    ids_pronosticados = list(pron_dict.keys())

    resp_part = (
        sb.table(tabla_part)
        .select(id_col_part + ", resultado, goles_local, goles_visitante")
        .in_(id_col_part, ids_pronosticados)
        .execute()
    )

    puntos = aciertos = disputados = 0

    for partido in resp_part.data:
        pid = partido[id_col_part]

        # Determinar resultado oficial (1/X/2)
        resultado_oficial = partido.get("resultado") or ""
        if not resultado_oficial:
            # Derivar desde goles_local / goles_visitante
            gl_of = partido.get("goles_local")
            gv_of = partido.get("goles_visitante")
            if gl_of is not None and gv_of is not None:
                resultado_oficial = _resultado_desde_marcador(str(gl_of) + "-" + str(gv_of))

        if not resultado_oficial:
            continue  # Partido no jugado aún

        disputados += 1

        marcador_pron = pron_dict.get(pid) or ""
        resultado_pron = _resultado_desde_marcador(marcador_pron)

        if resultado_pron != resultado_oficial:
            continue  # No acertó resultado → 0 pts

        aciertos += 1

        # Verificar marcador exacto
        gl_oficial = partido.get("goles_local")
        gv_oficial = partido.get("goles_visitante")

        if marcador_pron and "-" in marcador_pron:
            try:
                parts_p = marcador_pron.split("-")
                gl_pron = int(parts_p[0])
                gv_pron = int(parts_p[1])
                marcador_exacto = (
                    gl_oficial is not None
                    and gv_oficial is not None
                    and gl_pron == int(gl_oficial)
                    and gv_pron == int(gv_oficial)
                )
            except (ValueError, IndexError):
                marcador_exacto = False
        else:
            marcador_exacto = False

        puntos += PUNTOS_EXACTO if marcador_exacto else PUNTOS_RESULTADO

    return puntos, aciertos, disputados


def calcular_estadisticas(participante_id: int):
    """
    Devuelve (puntos_total, aciertos_total, disputados_total)
    sumando fase de grupos + dieciseisavos de final.
    """
    sb = conectar()

    pts_g, ac_g, dis_g = _calcular_fase(
        sb,
        tabla_pron="pronosticos",
        tabla_part="partidos",
        id_col_pron="partido_id",
        id_col_part="id",
        participante_id=participante_id,
    )

    pts_16, ac_16, dis_16 = _calcular_fase(
        sb,
        tabla_pron="pronosticos_dieciseisavos",
        tabla_part="dieciseisavos",
        id_col_pron="cruce_id",
        id_col_part="id",
        participante_id=participante_id,
    )

    return (
        pts_g + pts_16,
        ac_g + ac_16,
        dis_g + dis_16,
    )


def calcular_estadisticas_desglose(participante_id: int):
    """
    Devuelve dict con puntos/aciertos/disputados separados por fase.
    Útil para mostrar desglose en el ranking.
    """
    sb = conectar()

    pts_g, ac_g, dis_g = _calcular_fase(
        sb,
        tabla_pron="pronosticos",
        tabla_part="partidos",
        id_col_pron="partido_id",
        id_col_part="id",
        participante_id=participante_id,
    )

    pts_16, ac_16, dis_16 = _calcular_fase(
        sb,
        tabla_pron="pronosticos_dieciseisavos",
        tabla_part="dieciseisavos",
        id_col_pron="cruce_id",
        id_col_part="id",
        participante_id=participante_id,
    )

    return {
        "grupos":       {"puntos": pts_g,   "aciertos": ac_g,   "disputados": dis_g},
        "dieciseisavos": {"puntos": pts_16, "aciertos": ac_16,  "disputados": dis_16},
        "total":        {"puntos": pts_g + pts_16, "aciertos": ac_g + ac_16, "disputados": dis_g + dis_16},
    }


def calcular_puntos(participante_id: int) -> int:
    puntos, _, _ = calcular_estadisticas(participante_id)
    return puntos
