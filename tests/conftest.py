import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from pathlib import Path
import os
import tempfile
import shutil
from datetime import datetime, timedelta

from app.database import Base, get_db
from app.main import app
from app.models import User, Submission, RoleType
from app.security import get_password_hash, create_access_token
from app.config import settings


# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def temp_uploads_dir():
    """Create a temporary directory for uploads during tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after tests
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def test_db():
    """Create test database tables before each test and drop them after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db) -> TestingSessionLocal:
    """
    Create a fresh database session for a test.
    We need this to ensure data is cleaned up between tests.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal()
    
    # Setup seed data if needed here
    
    yield session
    
    transaction.rollback()
    session.close()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session, monkeypatch, temp_uploads_dir):
    """
    Create a FastAPI TestClient that uses the test database session
    and mocks the uploads directory
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    # Override settings for tests
    monkeypatch.setattr(settings, "UPLOADS_DIR", temp_uploads_dir)
    
    # Override dependencies
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clear all overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def super_admin_user(db_session):
    """Create a test super admin user"""
    user = User(
        username="superadmin",
        email="superadmin@example.com",
        full_name="Super Admin",
        hashed_password=get_password_hash("password123"),
        te_id="SA12345",
        plant="Plant A",
        role=RoleType.SUPER_ADMIN,
        must_reset_password=False,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def regular_admin_user(db_session):
    """Create a test regular admin user"""
    user = User(
        username="admin",
        email="admin@example.com",
        full_name="Regular Admin",
        hashed_password=get_password_hash("password123"),
        te_id="RA12345",
        plant="Plant A",
        role=RoleType.REGULAR_ADMIN,
        must_reset_password=False,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def super_admin_token(super_admin_user):
    """Create a token for super admin user"""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        data={"sub": super_admin_user.username, "role": super_admin_user.role},
        expires_delta=access_token_expires
    )


@pytest.fixture(scope="function")
def regular_admin_token(regular_admin_user):
    """Create a token for regular admin user"""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        data={"sub": regular_admin_user.username, "role": regular_admin_user.role},
        expires_delta=access_token_expires
    )


@pytest.fixture(scope="function")
def test_submission(db_session, regular_admin_user):
    """Create a test submission"""
    submission = Submission(
        first_name="Test",
        last_name="User",
        cin="AB123456",
        te_id="TE123456",
        date_of_birth=datetime(1990, 1, 1),
        grey_card_number="123-A-456",
        plant="Plant A",
        cin_file_path="Plant A/cin/1/test_cin.jpg",
        picture_file_path="Plant A/pic/1/test_pic.jpg",
        grey_card_file_path="Plant A/grey_card/1/test_grey_card.jpg",
        admin_id=regular_admin_user.id
    )
    db_session.add(submission)
    db_session.commit()
    db_session.refresh(submission)
    return submission