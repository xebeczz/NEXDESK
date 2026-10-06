from app.core.config import settings
from app.core.security import hash_password
from app.db.base import utcnow
from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.models.user import User

db = SessionLocal()
try:
    specs = [
        (settings.SEED_ADMIN_EMAIL, 'admin', 'System Administrator', settings.SEED_ADMIN_PASSWORD, UserRole.ADMIN, 'IT Operations'),
        (settings.SEED_USER_EMAIL, 'user', 'Demo Employee', settings.SEED_USER_PASSWORD, UserRole.USER, 'HR'),
    ]
    for email, username, name, pwd, role, dept in specs:
        existing = db.query(User).filter(User.email == email).one_or_none()
        if existing is not None:
            print(f'User {email} already exists')
            continue
        user = User(
            email=email,
            username=username,
            full_name=name,
            hashed_password=hash_password(pwd),
            role=role,
            department=dept,
            is_active=True,
        )
        db.add(user)
    db.commit()
    print('Users seeded successfully')
finally:
    db.close()