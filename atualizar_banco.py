import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("ALTER TABLE tickets ADD COLUMN usuario TEXT")
conn.commit()

print("Banco atualizado!")