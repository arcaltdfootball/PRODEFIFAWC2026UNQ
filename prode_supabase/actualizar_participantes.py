import sqlite3

conn = sqlite3.connect("prode.db")

cursor = conn.cursor()

try:

    cursor.execute("""
    ALTER TABLE participantes
    ADD COLUMN foto TEXT
    """)

    conn.commit()

except:
    pass

conn.close()

print("OK")