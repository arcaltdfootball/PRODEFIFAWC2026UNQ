import sqlite3
import streamlit as st
from database import conectar

def migrar_tabla(tabla_nombre, conn_supabase):
    print(f"Migrando tabla: {tabla_nombre}...")
    
    # 1. Leer los datos locales de SQLite
    try:
        conn_local = sqlite3.connect("prode.db")
        cursor = conn_local.cursor()
        cursor.execute(f"SELECT * FROM {tabla_nombre}")
        columnas = [descripcion[0] for descripcion in cursor.description]
        filas = cursor.fetchall()
        conn_local.close()
    except Exception as e:
        print(f"No se pudo leer la tabla local {tabla_nombre}: {e}")
        return

    if not filas:
        print(f"La tabla {tabla_nombre} local está vacía.")
        return

    # 2. Convertir las filas en formato de diccionario para Supabase
    datos_a_insertar = []
    for fila in filas:
        registro = dict(zip(columnas, fila))
        datos_a_insertar.append(registro)

    # 3. Insertar masivamente en Supabase
    try:
        conn_supabase.table(tabla_nombre).insert(datos_a_insertar).execute()
        print(f"¡Éxito! Se migraron {len(datos_a_insertar)} registros a la tabla '{tabla_nombre}' online.")
    except Exception as e:
        print(f"Error al subir los datos de {tabla_nombre} a Supabase: {e}")

if __name__ == "__main__":
    print("--- Iniciando migración de datos a Supabase ---")
    try:
        supabase_conn = conectar()
        
        # Lista de tus 4 tablas exactas
        tablas = ["participantes", "partidos", "pronosticos", "historial_ranking"]
        
        for tabla in tablas:
            migrar_tabla(tabla, supabase_conn)
            
        print("\n--- Proceso finalizado ---")
    except Exception as e:
        print(f"Error crítico en la conexión: {e}")