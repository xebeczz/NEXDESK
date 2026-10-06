import sys
sys.path.insert(0, 'backend')

from app.db.session import SessionLocal
from sqlalchemy import inspect

db = SessionLocal()
inspector = inspect(db.bind)
cols = inspector.get_columns('tickets')
for c in cols:
    print(f'  {c["name"]}: {c["type"]}')
db.close()