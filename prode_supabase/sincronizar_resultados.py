"""
sincronizar_resultados.py
─────────────────────────────────────────────────────────────────────────────
Consulta la API oficial del Mundial 2026 (worldcupapi.com) y actualiza
la columna `resultado` de la tabla `partidos` en Supabase.

La API ya devuelve el resultado como "1", "X" o "2" en outcomes.full_time,
que es exactamente el formato que usa la tabla.

USO:
  1. Completá la constante WC_API_KEY con tu clave de worldcupapi.com
  2. Ejecutá manualmente:    python sincronizar_resultados.py
     O programá con cron:    */30 * * * * python /ruta/sincronizar_resultados.py
"""

import requests
from database import conectar   # mismo módulo que usa la app Streamlit

# ── CONFIGURACIÓN ──────────────────────────────────────────────────────────────
WC_API_KEY  = "Lxn3G82Je3ftZr9p"              # tu clave de worldcupapi.com
WC_BASE_URL = "https://api.worldcupapi.com"
# ──────────────────────────────────────────────────────────────────────────────


def obtener_partidos_terminados() -> list[dict]:
    """
    Trae todos los partidos finalizados del Mundial 2026 desde /history.
    Pagina hasta agotar resultados.
    """
    headers = {"Accept": "application/json"}
    params  = {"key": WC_API_KEY, "page": 1}
    partidos = []

    while True:
        resp = requests.get(
            f"{WC_BASE_URL}/history",
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        # La API devuelve una lista directa
        chunk = data if isinstance(data, list) else data.get("data", [])
        if not chunk:
            break

        partidos.extend(chunk)
        if len(chunk) < 50:   # última página
            break
        params["page"] += 1

    return partidos


def normalizar(nombre: str) -> str:
    return nombre.strip().lower()


def sincronizar():
    print("─── Iniciando sincronización de resultados ───")

    # 1. Conectar a Supabase
    sb = conectar()

    # 2. Traer los partidos de la BD
    resp_db = sb.table("partidos").select("id, local, visitante, resultado").execute()
    partidos_db = resp_db.data
    if not partidos_db:
        print("No hay partidos en la base de datos. Abortando.")
        return

    # Índice rápido: (local_norm, visitante_norm) → fila
    indice_db = {
        (normalizar(p["local"]), normalizar(p["visitante"])): p
        for p in partidos_db
    }

    # 3. Traer partidos terminados desde la API
    print(f"Consultando {WC_BASE_URL}/history …")
    try:
        partidos_api = obtener_partidos_terminados()
    except requests.HTTPError as e:
        print(f"Error al llamar a la API: {e}")
        return

    print(f"  → {len(partidos_api)} partidos terminados recibidos")

    # 4. Cruzar y actualizar
    actualizados = 0
    sin_match    = 0

    for p in partidos_api:
        if p.get("status") != "FINISHED":
            continue

        home_name = (p.get("home") or {}).get("name", "")
        away_name = (p.get("away") or {}).get("name", "")

        # El resultado ya viene en el formato correcto: "1", "X" o "2"
        outcomes       = p.get("outcomes") or {}
        nuevo_resultado = outcomes.get("full_time")   # "1", "X", "2" o None

        # Si hubo penales usamos el resultado final del encuentro
        if outcomes.get("penalty_shootout"):
            nuevo_resultado = outcomes.get("penalty_shootout")

        if nuevo_resultado not in ("1", "X", "2"):
            continue

        clave   = (normalizar(home_name), normalizar(away_name))
        fila_db = indice_db.get(clave)

        if fila_db is None:
            sin_match += 1
            print(f"  ⚠ Sin coincidencia en BD: {home_name} vs {away_name}")
            continue

        # Solo escribir si cambió (evita requests innecesarios a Supabase)
        if fila_db.get("resultado") == nuevo_resultado:
            continue

        scores = p.get("scores", {})
        marcador = scores.get("ft_score") or scores.get("score") or "?-?"

        sb.table("partidos").update({"resultado": nuevo_resultado}).eq("id", fila_db["id"]).execute()
        actualizados += 1
        print(f"  ✓ {home_name} {marcador} {away_name}  →  resultado={nuevo_resultado}")

    print(f"\n─── Listo: {actualizados} actualizados, {sin_match} sin coincidencia ───")


if __name__ == "__main__":
    sincronizar()
