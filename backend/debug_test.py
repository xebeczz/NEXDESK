"""Debug test"""
import sys
sys.path.insert(0, 'C:\\Users\\poove\\Documents\\New folder\\backend')

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import UserRole
from app.models.user import User
from app.core.security import hash_password

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

Base.metadata.create_all(engine)
session = TestSession()

def make_user(db, role=UserRole.USER.value, department="IT Support"):
    import uuid
    idx = uuid.uuid4().hex[:8]
    user = User(
        email=f"{idx}@test.io",
        username=f"user_{idx}",
        full_name=f"Tester {idx}",
        role=role,
        department=department,
        hashed_password=hash_password("Password@123"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

alice = make_user(session, department="HR")
bob = make_user(session, department="HR")

print(f"Alice: {alice.id}")
print(f"Bob: {bob.id}")

def auth_headers(user):
    from app.core.security import create_access_token
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}

def override_get_db():
    try:
        yield session
    finally:
        pass

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Create ticket as Alice
res = client.post("/api/v1/tickets", json={
    "title": "Alice ticket",
    "description": "desc",
    "category": "General",
    "priority": "medium"
}, headers=auth_headers(alice))
print(f"Alice create: {res.status_code}, {res.json()}")

# Create ticket as Bob
res = client.post("/api/v1/tickets", json={
    "title": "Bob ticket",
    "description": "desc",
    "category": "General",
    "priority": "medium"
}, headers=auth_headers(bob))
print(f"Bob create: {res.status_code}, {res.json()}")

# List tickets as Alice
res = client.get("/api/v1/tickets", headers=auth_headers(alice))
print(f"Alice list: {res.status_code}")
print(f"Items: {res.json()['items']}")

for item in res.json()['items']:
    print(f"  {item.get('ticket_no', 'N/A')} - created_by: {item['created_by']['id']}")

print("Done")