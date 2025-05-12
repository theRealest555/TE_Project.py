import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.security import create_access_token
from app.models import Submission


def test_generate_report_format_1(client, super_admin_user, db):
    # Create some test submissions
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
    
    # Create access token for super admin
    access_token = create_access_token(data={"sub": super_admin_user.username})
    
    # Generate report format 1
    response = client.get(
        "/admin/reports?format=1",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "Content-Disposition" in response.headers
    assert "attachment; filename=employee_data_format1_" in response.headers["Content-Disposition"]


def test_generate_report_format_2(client, super_admin_user, db):
    # Create some test submissions
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
    
    # Create access token for super admin
    access_token = create_access_token(data={"sub": super_admin_user.username})
    
    # Generate report format 2
    response = client.get(
        "/admin/reports?format=2",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "Content-Disposition" in response.headers
    assert "attachment; filename=employee_grey_cards_format2_" in response.headers["Content-Disposition"]


def test_regular_admin_can_only_see_their_plant_data(client, regular_admin_user, db):
    # Create submissions for different plants
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
    
    # Generate report format 1
    response = client.get(
        "/admin/reports?format=1",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "Content-Disposition" in response.headers
    assert "attachment; filename=employee_data_format1_" in response.headers["Content-Disposition"]


def test_invalid_report_format(client, super_admin_user):
    # Create access token for super admin
    access_token = create_access_token(data={"sub": super_admin_user.username})
    
    # Try to generate report with invalid format
    response = client.get(
        "/admin/reports?format=3",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 422  # Validation error


def test_unauthorized_report_access(client):
    # Try to generate report without authentication
    response = client.get("/admin/reports?format=1")
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"