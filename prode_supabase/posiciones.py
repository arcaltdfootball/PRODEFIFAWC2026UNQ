"""
posiciones.py

Calcula la tabla de posiciones de la Liga Profesional de Fútbol Argentina
(Zona A y Zona B), incluyendo los partidos interzonales dentro de la zona
propia de cada equipo (tal como funciona la Liga Profesional real).

Requiere que en Supabase existan las tablas "equipos" y "partidos" con la
estructura de schema_prode.sql.
"""
from database import conectar


def _fila_vacia(nombre: str) -> dict:
    return {
        "nombre": nombre,
        "pj": 0, "pg": 0, "pe": 0, "pp": 0,
        "gf": 0, "gc": 0, "dg": 0, "pts": 0,
    }


def calcular_todas_las_posiciones() -> dict:
    """
    Devuelve {"A": [fila, fila, ...], "B": [fila, fila, ...]}
    Cada fila es un dict con: pos, nombre, pj, pg, pe, pp, gf, gc, dg, pts.
    Las listas ya vienen ordenadas de 1° a 15° puesto.
    """
    sb = conectar()

    equipos_resp = sb.table("equipos").select("nombre, zona").execute()
    equipos = equipos_resp.data or []
    zona_de = {e["nombre"]: e["zona"] for e in equipos}

    stats = {e["nombre"]: _fila_vacia(e["nombre"]) for e in equipos}

    partidos_resp = (
        sb.table("partidos")
        .select("equipo_local, equipo_visitante, goles_local, goles_visitante")
        .execute()
    )
    partidos = partidos_resp.data or []

    for p in partidos:
        gl = p.get("goles_local")
        gv = p.get("goles_visitante")
        if gl is None or gv is None:
            continue  # partido todavía no jugado -> no suma

        local = p.get("equipo_local")
        visitante = p.get("equipo_visitante")

        if local not in stats or visitante not in stats:
            # nombre que no matchea con la tabla equipos: lo ignoramos
            # (revisar que equipo_local/equipo_visitante en "partidos"
            #  usen exactamente los mismos nombres que en "equipos")
            continue

        gl, gv = int(gl), int(gv)
        el, ev = stats[local], stats[visitante]

        el["pj"] += 1
        ev["pj"] += 1
        el["gf"] += gl
        el["gc"] += gv
        ev["gf"] += gv
        ev["gc"] += gl

        if gl > gv:
            el["pg"] += 1
            el["pts"] += 3
            ev["pp"] += 1
        elif gl < gv:
            ev["pg"] += 1
            ev["pts"] += 3
            el["pp"] += 1
        else:
            el["pe"] += 1
            ev["pe"] += 1
            el["pts"] += 1
            ev["pts"] += 1

    for fila in stats.values():
        fila["dg"] = fila["gf"] - fila["gc"]

    def ordenar(lista):
        # Desempate estándar: Pts, luego DG, luego GF, luego alfabético
        return sorted(lista, key=lambda e: (-e["pts"], -e["dg"], -e["gf"], e["nombre"]))

    tabla_a = ordenar([s for n, s in stats.items() if zona_de.get(n) == "A"])
    tabla_b = ordenar([s for n, s in stats.items() if zona_de.get(n) == "B"])

    for i, fila in enumerate(tabla_a, start=1):
        fila["pos"] = i
    for i, fila in enumerate(tabla_b, start=1):
        fila["pos"] = i

    return {"A": tabla_a, "B": tabla_b}
