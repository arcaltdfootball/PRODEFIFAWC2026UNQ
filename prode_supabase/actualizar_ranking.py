from datetime import datetime
from database import conectar
from ranking import obtener_ranking

conn = conectar()

ranking = obtener_ranking()

posicion = 1

# Traemos todos los participantes registrados para emparejar el nombre con su ID correspondiente
res_participantes = conn.table("participantes").select("id, nombre").execute()
mapeo_participantes = {p["nombre"]: p["id"] for p in res_participantes.data}

registros_a_insertar = []

for nombre, puntos in ranking:
    # Verificamos si el nombre del ranking existe en la base de datos
    if nombre in mapeo_participantes:
        participante_id = mapeo_participantes[nombre]

        # Estructuramos el diccionario con los campos exactos de tu tabla
        registros_a_insertar.append({
            "participante_id": participante_id,
            "fecha_control": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "posicion": posicion,
            "puntos": puntos
        })

    posicion += 1

# Si hay registros procesados, hacemos una única inserción masiva en Supabase
if registros_a_insertar:
    conn.table("historial_ranking").insert(registros_a_insertar).execute()

print("Ranking actualizado")