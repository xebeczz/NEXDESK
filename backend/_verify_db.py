import sqlite3, os
db=os.path.join(r"C:\Users\USER\Downloads\AI TICKET SUPPORT\AI TICKET SUPPORT\New folder\backend\data","itdesk.db")
print("WAL file exists:", os.path.exists(db+'-wal'))
con=sqlite3.connect(db)
con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
tid="14a48033-3929-423f-8abc-61b333a1459b"
cur=con.execute("SELECT id, assigned_engineer_id FROM tickets WHERE id=?",(tid,))
print("DIRECT SQL:", cur.fetchone())
# Now reset
con.execute("UPDATE tickets SET assigned_engineer_id=NULL WHERE id=?",(tid,))
con.commit()
con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
cur=con.execute("SELECT id, assigned_engineer_id FROM tickets WHERE id=?",(tid,))
print("AFTER RESET:", cur.fetchone())
con.close()
