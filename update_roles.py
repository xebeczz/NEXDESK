import sqlite3
conn = sqlite3.connect('/c/Users/poove/Documents/New folder/backend/data/itdesk.db')
cursor = conn.cursor()
cursor.execute('UPDATE users SET role = "user" WHERE role = "engineer"')
conn.commit()
print('Rows updated:', cursor.rowcount)
cursor.execute('SELECT email, role FROM users')
for row in cursor.fetchall():
    print(row)
conn.close()