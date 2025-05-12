import pytest
from datetime import datetime
from app.models import User, Submission, RoleType
from sqlalchemy.exc import IntegrityError


def test_user_model_create(db):
    """Test creating a user model with valid data"""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed_password",
        te_id="TE123",
        role=RoleType.REGULAR_ADMIN,
        plant="Plant1"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"
    assert user.hashed_password == "hashed_password"
    assert user.te_id == "TE123"
    assert user.role == RoleType.REGULAR_ADMIN
    assert user.plant == "Plant1"
    assert user.must_reset_password is True  # Default value
    assert user.is_active is True  # Default value
    assert user.created_at is not None
    assert user.updated_at is None


def test_user_model_unique_constraints(db):
    """Test unique constraints on user model"""
    # Create a user
    user1 = User(
        username="uniqueuser",
        email="unique@example.com",
        full_name="Unique User",
        hashed_password="hashed_password",
        te_id="UQ123",
        role=RoleType.REGULAR_ADMIN,
        plant="Plant1"
    )
    db.add(user1)
    db.commit()
    
    # Try to create another user with the same username
    user2 = User(
        username="uniqueuser",  # Same username
        email="different@example.com",
        full_name="Different User",
        hashed_password="hashed_password",
        te_id="DIF123",
        role=RoleType.REGULAR_ADMIN,
        plant="Plant2"
    )
    db.add(user2)
    
    with pytest.raises(IntegrityError):
        db.commit()
    
    db.rollback()
    
    # Try to create another user with the same email
    user3 = User(
        username="different",
        email="unique@example.com",  # Same email
        full_name="Different User",
        hashed_password="hashed_password",
        te_id="DIF456",
        role=RoleType.REGULAR_ADMIN,
        plant="Plant2"
    )
    db.add(user3)
    
    with pytest.raises(IntegrityError):
        db.commit()
    
    db.rollback()
    
    # Try to create another user with the same te_id
    user4 = User(
        username="different",
        email="different@example.com",
        full_name="Different User",
        hashed_password="hashed_password",
        te_id="UQ123",  # Same te_id
        role=RoleType.REGULAR_ADMIN,
        plant="Plant2"
    )
    db.add(user4)
    
    with pytest.raises(IntegrityError):
        db.commit()


def test_submission_model_create(db):
    """Test creating a submission model with valid data"""
    # First create a user
    user = User(
        username="adminuser",
        email="admin@example.com",
        full_name="Admin User",
        hashed_password="hashed_password",
        te_id="AD123",
        role=RoleType.REGULAR_ADMIN,
        plant="Plant1"
    )
    db.add(user)
    db.commit()
    
    # Now create a submission
    dob = datetime(1990, 1, 1)
    submission = Submission(
        first_name="John",
        last_name="Doe",
        cin="AB12345",
        te_id="JD123",
        date_of_birth=dob,
        grey_card_number="123-A-456",
        plant="Plant1",
        cin_file_path="Plant1/cin/1/cinfile.jpg",
        picture_file_path="Plant1/pic/1/picfile.jpg",
        grey_card_file_path="Plant1/grey_card/1/gcfile.jpg",
        admin_id=user.id
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    
    assert submission.id is not None
    assert submission.first_name == "John"
    assert submission.last_name == "Doe"
    assert submission.cin == "AB12345"
    assert submission.te_id == "JD123"
    assert submission.date_of_birth == dob
    assert submission.grey_card_number == "123-A-456"
    assert submission.plant == "Plant1"
    assert submission.cin_file_path == "Plant1/cin/1/cinfile.jpg"
    assert submission.picture_file_path == "Plant1/pic/1/picfile.jpg"
    assert submission.grey_card_file_path == "Plant1/grey_card/1/gcfile.jpg"
    assert submission.admin_id == user.id
    assert submission.created_at is not None
    assert submission.updated_at is None


def test_relationship_user_submissions(db):
    """Test relationship between user and submissions"""
    # Create a user
    user = User(
        username="relationuser",
        email="relation@example.com",
        full_name="Relation User",
        hashed_password="hashed_password",
        te_id="REL123",
        role=RoleType.REGULAR_ADMIN,
        plant="Plant1"
    )
    db.add(user)
    db.commit()
    
    # Create multiple submissions for this user
    for i in range(3):
        submission = Submission(
            first_name=f"User{i}",
            last_name=f"Test{i}",
            cin=f"AB{i}12345",
            te_id=f"UT{i}123",
            date_of_birth=datetime(1990, 1, 1),
            grey_card_number=f"{i}123-A-456",
            plant="Plant1",
            cin_file_path=f"Plant1/cin/1/cinfile{i}.jpg",
            picture_file_path=f"Plant1/pic/1/picfile{i}.jpg",
            grey_card_file_path=f"Plant1/grey_card/1/gcfile{i}.jpg",
            admin_id=user.id
        )
        db.add(submission)
    
    db.commit()
    db.refresh(user)
    
    # Check that the relationship works
    assert len(user.submissions) == 3
    assert user.submissions[0].admin_id == user.id
    assert user.submissions[0].admin.id == user.id
    assert user.submissions[0].admin.username == "relationuser"


def test_user_role_enum(db):
    """Test RoleType enum in user model"""
    # Create a super admin user
    super_admin = User(
        username="superadmin",
        email="super@example.com",
        full_name="Super Admin",
        hashed_password="hashed_password",
        te_id="SA123",
        role=RoleType.SUPER_ADMIN,
        plant="HQ"
    )
    db.add(super_admin)
    
    # Create a regular admin user
    regular_admin = User(
        username="regularadmin",
        email="regular@example.com",
        full_name="Regular Admin",
        hashed_password="hashed_password",
        te_id="RA123",
        role=RoleType.REGULAR_ADMIN,
        plant="Plant1"
    )
    db.add(regular_admin)
    
    db.commit()
    db.refresh(super_admin)
    db.refresh(regular_admin)
    
    # Verify role values
    assert super_admin.role == RoleType.SUPER_ADMIN
    assert super_admin.role == "super_admin"
    assert regular_admin.role == RoleType.REGULAR_ADMIN
    assert regular_admin.role == "regular_admin"