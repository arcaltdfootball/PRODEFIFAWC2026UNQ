from database import conectar

PUNTOS_RESULTADO  = 1   # Acertó 1/X/2
PUNTOS_EXACTO     = 3   # Acertó el marcador exacto (incluye el 1/X/2)


def calcular_estadisticas(participante_id: int):
    """
    Devuelve (puntos, aciertos, disputados).

    Sistema de puntuación:
      - 1 punto  → acertó el resultado (1 / X / 2)
      - 3 puntos → acertó el marcador exacto (goles_local y goles_visitante)
        El marcador exacto ya implica el resultado correcto, así que son 3 en total.
    """
    sb = conectar()

    resp_pron = (
        sb.table("pronosticos")
        .select("partido_id, pronostico, goles_local, goles_visitante")
        .eq("participante_id", participante_id)
        .execute()
    )

    pronosticos = {}
    for r in resp_pron.data:
        pronosticos[r["partido_id"]] = {
            "resultado":       r["pronostico"],
            "goles_local":     r.get("goles_local"),
            "goles_visitante": r.get("goles_visitante"),
        }

    if not pronosticos:
        return 0, 0, 0

    partido_ids = list(pronosticos.keys())
    resp_part = (
        sb.table("partidos")
        .select("id, resultado, goles_local, goles_visitante")
        .in_("id", partido_ids)
        .execute()
    )

    puntos = aciertos = disputados = 0
    for partido in resp_part.data:
        resultado_oficial = partido.get("resultado") or ""
        if not resultado_oficial:
            continue

        disputados += 1
        pron = pronosticos.get(partido["id"], {})
        resultado_pron = pron.get("resultado") or ""

        if resultado_pron != resultado_oficial:
            # No acertó ni el resultado → 0 pts
            continue

        aciertos += 1

        # Verificar si acertó el marcador exacto
        gl_oficial = partido.get("goles_local")
        gv_oficial = partido.get("goles_visitante")
        gl_pron    = pron.get("goles_local")
        gv_pron    = pron.get("goles_visitante")

        marcador_exacto = (
            gl_oficial is not None
            and gv_oficial is not None
            and gl_pron is not None
            and gv_pron is not None
            and int(gl_pron) == int(gl_oficial)
            and int(gv_pron) == int(gv_oficial)
        )

        puntos += PUNTOS_EXACTO if marcador_exacto else PUNTOS_RESULTADO

    return puntos, aciertos, disputados


def calcular_puntos(participante_id: int) -> int:
    puntos, _, _ = calcular_estadisticas(participante_id)
    return puntos
