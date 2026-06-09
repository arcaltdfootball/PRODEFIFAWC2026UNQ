from database import conectar

conn = conectar()

# Con Supabase realizamos la consulta equivalente al SELECT * LIMIT 10
respuesta = conn.table("partidos").select("*").limit(10).execute()

# Convertimos la lista de diccionarios de Supabase a una lista de tuplas 
# para respetar la estructura exacta con la que trabajaba tu código original
partidos = [
    (
        p.get("id"), 
        p.get("grupo"), 
        p.get("fecha"), 
        p.get("hora"), 
        p.get("sede"), 
        p.get("local"), 
        p.get("visitante"), 
        p.get("resultado")
    ) 
    for p in respuesta.data
]

for partido in partidos:
    print(partido)

# Nota: El objeto conector de Streamlit gestiona de forma automática 
# el ciclo de la conexión, eliminando la necesidad de invocar conn.close()