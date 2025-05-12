import io
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from app.security import create_access_token
from app.models import Submission


def test_create_submission(client, regular_admin_user, tmp_path):
    # Create access token for regular admin
    access_token = create_access_token(data={"sub": regular_admin_user.username})
    
    # Create test files
    cin_file = io.BytesIO(b"fake cin image data")
    picture_file = io.BytesIO(b"fake picture data")
    grey_card_file = io.BytesIO(b"fake grey card data")
    
    # Create submission with multipart form data
    response = client.post(
        "/submissions/",
        headers={"Authorization": f"Bearer {access_token}"},
        files={
            "cin_file": ("A12345.jpg", cin_file, "image/jpeg"),
            "picture_file": ("A12345_i.jpg", picture_file, "image/jpeg"),
            "grey_card_file": ("123-A-456.jpg", grey_card_file, "image/jpeg")
        },
        data={
            "first_name": "John",
            "last_name": "Doe",
            "cin": "A12345",
            "te_id": "JD001",
            "date_of_birth": "1990-01-01",
            "grey_card_number": "123-A-456",
            "plant": "Plant1"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["submission"]["first_name"] == "John"
    assert data["submission"]["last_name"] == "Doe"


def test_read_submissions_super_admin(client, super_admin_user, db):
    # Create some test submissions
    submission1 = Submission(
        first_name="John",
        last_name="Doe",
        cin="A12345",
        te_id="JD001",
        date_of_birth=datetime(1990, 1, 1),
        grey_card_number="123-A-456",
        plant="Plant1",
        cin_file_path="Plant1/cin/1/file1.jpg",
        picture_file_path="Plant1/pic/1/file1.jpg",
        grey_card_file_path="Plant1/grey_card/1/file1.jpg",
        admin_id=super_admin_user.id
    )
    
    submission2 = Submission(
        first_name="Jane",
        last_name="Smith",
        cin="B67890",
        te_id="JS001",
        date_of_birth=datetime(1992, 2, 2),
        grey_card_number="789-B-012",
        plant="Plant2",
        cin_file_path="Plant2/cin/1/file2.jpg",
        picture_file_path="Plant2/pic/1/file2.jpg",
        grey_card_file_path="Plant2/grey_card/1/file2.jpg",
        admin_id=super_admin_user.id
    )
    
    db.add(submission1)
    db.add(submission2)
    db.commit()
    
    # Create access token for super admin
    access_token = create_access_token(data={"sub": super_admin_user.username})
    
    # Get all submissions
    response = client.get(
        "/submissions/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total"] == 2
    assert len(data["submissions"]) == 2


def test_read_submissions_regular_admin(client, regular_admin_user, db):
    # Create some test submissions
    submission1 = Submission(
        first_name="John",
        last_name="Doe",
        cin="A12345",
        te_id="JD001",
        date_of_birth=datetime(1990, 1, 1),
        grey_card_number="123-A-456",
        plant="Plant1",  # Same as regular_admin_user.plant
        cin_file_path="Plant1/cin/1/file1.jpg",
        picture_file_path="Plant1/pic/1/file1.jpg",
        grey_card_file_path="Plant1/grey_card/1/file1.jpg",
        admin_id=regular_admin_user.id
    )
    
    submission2 = Submission(
        first_name="Jane",
        last_name="Smith",
        cin="B67890",
        te_id="JS001",
        date_of_birth=datetime(1992, 2, 2),
        grey_card_number="789-B-012",
        plant="Plant2",  # Different plant
        cin_file_path="Plant2/cin/1/file2.jpg",
        picture_file_path="Plant2/pic/1/file2.jpg",
        grey_card_file_path="Plant2/grey_card/1/file2.jpg",
        admin_id=regular_admin_user.id
    )
    
    db.add(submission1)
    db.add(submission2)
    db.commit()
    
    # Create access token for regular admin
    access_token = create_access_token(data={"sub": regular_admin_user.username})
    
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
    assert data["submissions"][0]["plant"] == "Plant1"


def test_read_submission_by_id(client, super_admin_user, db):
    # Create a test submission
    submission = Submission(
        first_name="John",
        last_name="Doe",
        cin="A12345",
        te_id="JD001",
        date_of_birth=datetime(1990, 1, 1),
        grey_card_number="123-A-456",
        plant="Plant1",
        cin_file_path="Plant1/cin/1/file1.jpg",
        picture_file_path="Plant1/pic/1/file1.jpg",
        grey_card_file_path="Plant1/grey_card/1/file1.jpg",
        admin_id=super_admin_user.id
    )
    
    db.add(submission)
    db.commit()
    db.refresh(submission)
    
    # Create access token for super admin
    access_token = create_access_token(data={"sub": super_admin_user.username})
    
    # Get submission by ID
    response = client.get(
        f"/submissions/{submission.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["submission"]["first_name"] == "John"
    assert data["submission"]["last_name"] == "Doe"
    assert data["submission"]["cin"] == "A12345"