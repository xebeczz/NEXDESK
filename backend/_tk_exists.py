import sqlite3, os
B = r"C:\Users\USER\Downloads\AI TICKET SUPPORT\AI TICKET SUPPORT\New folder\backend"
p = os.path.join(B, "data", "itdesk.db")
con = sqlite3.connect(p)
cur = con.execute("SELECT id, ticket_no, assigned_engineer_id FROM tickets WHERE id=?", ("14a48033-3929-423f-8abc-61b333a1459b",))
print("ticket:", cur.fetchone())
cur = con.execute("SELECT COUNT(*) FROM tickets")
print("total tickets:", cur.fetchone())
con.close()
