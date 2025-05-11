import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import User, RoleType
from app.security import get_password_hash

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    
    # Create a session for testing
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        
    # Drop all tables after the test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    # Override the get_db dependency to use the test database
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    # Remove the override after the test
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def super_admin_user(db):
    # Create a super admin user for testing
    user = User(
        username="superadmin",
        email="superadmin@example.com",
        full_name="Super Admin",
        hashed_password=get_password_hash("password123"),
        te_id="SA001",
        role=RoleType.SUPER_ADMIN,
        plant="HQ",
        must_reset_password=False,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def regular_admin_user(db):
    # Create a regular admin user for testing
    user = User(
        username="regularadmin",
        email="regularadmin@example.com",
        full_name="Regular Admin",
        hashed_password=get_password_hash("password123"),
        te_id="RA001",
        role=RoleType.REGULAR_ADMIN,
        plant="Plant1",
        must_reset_password=False,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user