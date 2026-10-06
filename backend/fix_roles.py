from app.db.session import SessionLocal
from app.models.user import User
from app.models.enums import UserRole

db = SessionLocal()
try:
    engineers = db.query(User).filter(User.role == 'engineer').all()
    for u in engineers:
        print(f'Updating {u.email} from engineer to user')
        u.role = UserRole.USER
    db.commit()
    print('Done')
finally:
    db.close()