import sqlite3
conn = sqlite3.connect('/c/Users/poove/Documents/New folder/backend/data/itdesk.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
for t in tables:
    print(t[0])
conn.close()