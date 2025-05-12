import pytest
from fastapi.testclient import TestClient
import io
import os
from unittest.mock import patch, MagicMock
from datetime import datetime
from app.security import create_access_token
from app.models import Submission, User, RoleType
from app.storage import file_storage


@pytest.fixture
def mock_file():
    """Create a mock file for testing file uploads"""
    return io.BytesIO(b"test file content")


@pytest.fixture
def sample_submission_data():
    """Sample submission form data for testing"""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "cin": "AB123456",
        "te_id": "T12345",
        "date_of_birth": "1990-01-01",
        "grey_card_number": "12345-A-67890",
        "plant": "Plant1"
    }


@pytest.fixture
def mock_save_file():
    """Mock the file_storage.save_file method"""
    with patch('app.storage.FileStorage.save_file') as mock:
        mock.return_value = "test/path/to/file.jpg"
        yield mock


def test_create_submission(client, regular_admin_user, sample_submission_data, mock_file, mock_save_file):
    """Test creating a new submission"""
    # Create access token for regular admin
    access_token = create_access_token(data={"sub": regular_admin_user.username})
    
    # Create a new submission
    files = {
        "cin_file": ("AB123456.jpg", mock_file, "image/jpeg"),
        "picture_file": ("AB123456_i.jpg", mock_file, "image/jpeg"),
        "grey_card_file": ("12345-A-67890.jpg", mock_file, "image/jpeg")
    }
    
    response = client.post(
        "/submissions/",
        headers={"Authorization": f"Bearer {access_token}"},
        data=sample_submission_data,
        files=files
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Submission created successfully"
    assert data["submission"]["first_name"] == sample_submission_data["first_name"]
    assert data["submission"]["last_name"] == sample_submission_data["last_name"]
    assert data["submission"]["cin"] == sample_submission_data["cin"]
    assert data["submission"]["te_id"] == sample_submission_data["te_id"]
    assert data["submission"]["plant"] == sample_submission_data["plant"]
    
    # Verify file_storage.save_file was called 3 times (one for each file)
    assert mock_save_file.call_count == 3


def test_create_submission_invalid_data(client, regular_admin_user, mock_file):
    """Test creating a submission with invalid data"""
    # Create access token for regular admin
    access_token = create_access_token(data={"sub": regular_admin_user.username})
    
    # Create a submission with invalid CIN format
    invalid_data = {
        "first_name": "John",
        "last_name": "Doe",
        "cin": "123456",  # Invalid CIN format, should start with letters
        "te_id": "T12345",
        "date_of_birth": "1990-01-01",
        "grey_card_number": "12345-A-67890",
        "plant": "Plant1"
    }
    
    files = {
        "cin_file": ("123456.jpg", mock_file, "image/jpeg"),
        "picture_file": ("123456_i.jpg", mock_file, "image/jpeg"),
        "grey_card_file": ("12345-A-67890.jpg", mock_file, "image/jpeg")
    }
    
    response = client.post(
        "/submissions/",
        headers={"Authorization": f"Bearer {access_token}"},
        data=invalid_data,
        files=files
    )
    
    assert response.status_code == 400
    assert "Invalid submission data" in response.json()["detail"]


def test_get_submissions(client, regular_admin_user, db, sample_submission_data, mock_save_file):
    """Test getting submissions list"""
    # Create access token for regular admin
    access_token = create_access_token(data={"sub": regular_admin_user.username})
    
    # Create a test submission in the database
    submission = Submission(
        **sample_submission_data,
        date_of_birth=datetime.strptime(sample_submission_data["date_of_birth"], "%Y-%m-%d"),
        cin_file_path="test/path/cin.jpg",
        picture_file_path="test/path/pic.jpg",
        grey_card_file_path="test/path/grey.jpg",
        admin_id=regular_admin_user.id
    )
    db.add(submission)
    db.commit()
    
    # Get submissions
    response = client.get(
        "/submissions/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total"] == 1
    assert len(data["submissions"]) == 1
    assert data["submissions"][0]["first_name"] == sample_submission_data["first_name"]
    assert data["submissions"][0]["last_name"] == sample_submission_data["last_name"]


def test_get_submission_by_id(client, regular_admin_user, db, sample_submission_data):
    """Test getting a specific submission by ID"""
    # Create access token for regular admin
    access_token = create_access_token(data={"sub": regular_admin_user.username})
    
    # Create a test submission in the database
    submission = Submission(
        **sample_submission_data,
        date_of_birth=datetime.strptime(sample_submission_data["date_of_birth"], "%Y-%m-%d"),
        cin_file_path="test/path/cin.jpg",
        picture_file_path="test/path/pic.jpg",
        grey_card_file_path="test/path/grey.jpg",
        admin_id=regular_admin_user.id
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    
    # Get submission by ID
    response = client.get(
        f"/submissions/{submission.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["submission"]["id"] == submission.id
    assert data["submission"]["first_name"] == sample_submission_data["first_name"]
    assert data["submission"]["last_name"] == sample_submission_data["last_name"]


def test_get_submission_by_id_not_found(client, regular_admin_user):
    """Test getting a non-existent submission"""
    # Create access token for regular admin
    access_token = create_access_token(data={"sub": regular_admin_user.username})
    
    # Try to get non-existent submission
    response = client.get(
        "/submissions/9999",  # Non-existent ID
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Submission not found"


def test_super_admin_access_all_plants(client, super_admin_user, regular_admin_user, db, sample_submission_data):
    """Test that super admin can access submissions from all plants"""
    # Create access token for super admin
    access_token = create_access_token(data={"sub": super_admin_user.username})
    
    # Create a test submission for Plant1
    submission1 = Submission(
        **sample_submission_data,
        date_of_birth=datetime.strptime(sample_submission_data["date_of_birth"], "%Y-%m-%d"),
        cin_file_path="test/path/cin.jpg",
        picture_file_path="test/path/pic.jpg",
        grey_card_file_path="test/path/grey.jpg",
        admin_id=regular_admin_user.id
    )
    
    # Create a test submission for Plant2
    sample_submission_data_plant2 = sample_submission_data.copy()
    sample_submission_data_plant2["plant"] = "Plant2"
    sample_submission_data_plant2["cin"] = "CD654321"
    submission2 = Submission(
        **sample_submission_data_plant2,
        date_of_birth=datetime.strptime(sample_submission_data_plant2["date_of_birth"], "%Y-%m-%d"),
        cin_file_path="test/path/cin2.jpg",
        picture_file_path="test/path/pic2.jpg",
        grey_card_file_path="test/path/grey2.jpg",
        admin_id=super_admin_user.id
    )
    
    db.add(submission1)
    db.add(submission2)
    db.commit()
    
    # Super admin should see both submissions
    response = client.get(
        "/submissions/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["submissions"]) == 2
    
    # Test filtering by plant
    response = client.get(
        "/submissions/?plant=Plant2",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["submissions"][0]["plant"] == "Plant2"


def test_regular_admin_access_only_own_plant(client, regular_admin_user, super_admin_user, db, sample_submission_data):
    """Test that regular admin can only access submissions from their own plant"""
    # Create access token for regular admin
    access_token = create_access_token(data={"sub": regular_admin_user.username})
    
    # Create a test submission for Plant1 (regular admin's plant)
    submission1 = Submission(
        **sample_submission_data,
        date_of_birth=datetime.strptime(sample_submission_data["date_of_birth"], "%Y-%m-%d"),
        cin_file_path="test/path/cin.jpg",
        picture_file_path="test/path/pic.jpg",
        grey_card_file_path="test/path/grey.jpg",
        admin_id=regular_admin_user.id
    )
    
    # Create a test submission for Plant2
    sample_submission_data_plant2 = sample_submission_data.copy()
    sample_submission_data_plant2["plant"] = "Plant2"
    sample_submission_data_plant2["cin"] = "CD654321"
    submission2 = Submission(
        **sample_submission_data_plant2,
        date_of_birth=datetime.strptime(sample_submission_data_plant2["date_of_birth"], "%Y-%m-%d"),
        cin_file_path="test/path/cin2.jpg",
        picture_file_path="test/path/pic2.jpg",
        grey_card_file_path="test/path/grey2.jpg",
        admin_id=super_admin_user.id
    )
    
    db.add(submission1)
    db.add(submission2)
    db.commit()
    db.refresh(submission1)
    db.refresh(submission2)
    
    # Regular admin should only see submissions from their plant
    response = client.get(
        "/submissions/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["submissions"][0]["plant"] == regular_admin_user.plant
    
    # Regular admin shouldn't be able to access a submission from another plant
    response = client.get(
        f"/submissions/{submission2.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to access this submission"