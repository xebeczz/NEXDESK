import sqlite3
conn = sqlite3.connect('c:/Users/poove/Documents/New folder/backend/data/itdesk.db')
cursor = conn.cursor()
cursor.execute('UPDATE tickets SET assigned_to_id = assigned_engineer_id WHERE assigned_to_id IS NULL')
conn.commit()
print('Rows updated:', cursor.rowcount)
conn.close()