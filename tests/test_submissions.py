import io
import pytest
from fastapi.testclient import TestClient
from app.security import create_access_token
from app.models import Submission


def test_read_submissions_super_admin(client, super_admin_user, db):
    # Create some test submissions
    submission1 = Submission(
        first_name="John",
        last_name="Doe",
        cin="A12345",
        te_id="JD001",
        date_of_birth="1990-01-01",
        grey_card_number="123-A-456",
        plant="Plant1",
        cin_file_path="Plant1/cin/1/file1.jpg",
        picture_file_path="Plant1/pic/1/file1.jpg",
        grey_card_file_path="Plant1/grey_card/1/file1.jpg"
    )
    
    submission2 = Submission(
        first_name="Jane",
        last_name="Smith",
        cin="B67890",
        te_id="JS001",
        date_of_birth="1992-02-02",
        grey_card_number="789-B-012",
        plant="Plant2",
        cin_file_path="Plant2/cin/1/file2.jpg",
        picture_file_path="Plant2/pic/1/file2.jpg",
        grey_card_file_path="Plant2/grey_card/1/file2.jpg"
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
    assert len(data) == 2  # Should see all submissions


def test_read_submissions_regular_admin(client, regular_admin_user, db):
    # Create some test submissions
    submission1 = Submission(
        first_name="John",
        last_name="Doe",
        cin="A12345",
        te_id="JD001",
        date_of_birth="1990-01-01",
        grey_card_number="123-A-456",
        plant="Plant1",  # Same as regular_admin_user.plant
        cin_file_path="Plant1/cin/1/file1.jpg",
        picture_file_path="Plant1/pic/1/file1.jpg",
        grey_card_file_path="Plant1/grey_card/1/file1.jpg"
    )
    
    submission2 = Submission(
        first_name="Jane",
        last_name="Smith",
        cin="B67890",
        te_id="JS001",
        date_of_birth="1992-02-02",
        grey_card_number="789-B-012",
        plant="Plant2",  # Different plant
        cin_file_path="Plant2/cin/1/file2.jpg",
        picture_file_path="Plant2/pic/1/file2.jpg",
        grey_card_file_path="Plant2/grey_card/1/file2.jpg"
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
    assert len(data) == 1  # Should only see submissions from their plant
    assert data[0]["plant"] == "Plant1"


def test_read_submission_by_id(client, super_admin_user, db):
    # Create a test submission
    submission = Submission(
        first_name="John",
        last_name="Doe",
        cin="A12345",
        te_id="JD001",
        date_of_birth="1990-01-01",
        grey_card_number="123-A-456",
        plant="Plant1",
        cin_file_path="Plant1/cin/1/file1.jpg",
        picture_file_path="Plant1/pic/1/file1.jpg",
        grey_card_file_path="Plant1/grey_card/1/file1.jpg"
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
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["cin"] == "A12345"