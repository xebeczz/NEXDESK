import sqlite3, os
db=os.path.join(r"C:\Users\USER\Downloads\AI TICKET SUPPORT\AI TICKET SUPPORT\New folder\backend\data","itdesk.db")
tid="14a48033-3929-423f-8abc-61b333a1459b"
con=sqlite3.connect(db); con.execute("UPDATE tickets SET assigned_engineer_id=NULL WHERE id=?",(tid,)); con.commit(); con.close()
print("Reset", tid, "-> Unassigned")
