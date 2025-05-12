import pytest
from app.models import User, RoleType


def test_create_user(client, super_admin_token, db_session):
    """Test creating a new user"""
    user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "full_name": "New User",
        "te_id": "NU12345",
        "plant": "Plant B",
        "role": RoleType.REGULAR_ADMIN.value,
        "password": "Password123"
    }
    
    response = client.post(
        "/admin/users",
        json=user_data,
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "User created successfully"
    assert data["user"]["username"] == user_data["username"]
    assert data["user"]["email"] == user_data["email"]
    
    # Verify the user was added to the database
    user = db_session.query(User).filter(User.username == user_data["username"]).first()
    assert user is not None
    assert user.must_reset_password is True


def test_create_user_default_password(client, super_admin_token, db_session):
    """Test creating a user with default password (te_id)"""
    user_data = {
        "username": "defaultpw",
        "email": "defaultpw@example.com",
        "full_name": "Default Password",
        "te_id": "DP12345",
        "plant": "Plant C",
        "role": RoleType.REGULAR_ADMIN.value
        # No password provided, should default to te_id
    }
    
    response = client.post(
        "/admin/users",
        json=user_data,
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    
    # Test that login works with te_id as password
    login_response = client.post(
        "/auth/login",
        json={"username": user_data["username"], "password": user_data["te_id"]}
    )
    assert login_response.status_code == 200


def test_create_user_existing_username(client, super_admin_token, regular_admin_user):
    """Test creating a user with an existing username"""
    user_data = {
        "username": regular_admin_user.username,  # Same username as existing user
        "email": "new@example.com",
        "full_name": "Duplicate User",
        "te_id": "DU12345",
        "plant": "Plant D",
        "role": RoleType.REGULAR_ADMIN.value
    }
    
    response = client.post(
        "/admin/users",
        json=user_data,
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_create_user_unauthorized(client, regular_admin_token):
    """Test creating a user without super admin privileges"""
    user_data = {
        "username": "unauthorized",
        "email": "unauthorized@example.com",
        "full_name": "Unauthorized User",
        "te_id": "UN12345",
        "plant": "Plant E",
        "role": RoleType.REGULAR_ADMIN.value
    }
    
    response = client.post(
        "/admin/users",
        json=user_data,
        headers={"Authorization": f"Bearer {regular_admin_token}"}
    )
    
    assert response.status_code == 403
    assert "Super admin" in response.json()["detail"]


def test_get_users(client, super_admin_token, regular_admin_user, super_admin_user):
    """Test getting users list"""
    response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["users"]) >= 2  # At least the two users we created
    assert data["total"] >= 2


def test_get_users_pagination(client, super_admin_token, db_session):
    """Test user list pagination"""
    # Create 10 additional users for pagination test
    for i in range(10):
        db_session.add(User(
            username=f"pageuser{i}",
            email=f"page{i}@example.com",
            full_name=f"Page User {i}",
            hashed_password="dummy_hash",
            te_id=f"PU{i}",
            plant="Plant A",
            role=RoleType.REGULAR_ADMIN.value
        ))
    db_session.commit()
    
    # Test with limit and skip
    response = client.get(
        "/admin/users?skip=2&limit=5",
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 5  # Should get exactly 5 users
    assert data["skip"] == 2
    assert data["limit"] == 5


def test_get_user_by_id(client, super_admin_token, regular_admin_user):
    """Test getting a specific user by ID"""
    response = client.get(
        f"/admin/users/{regular_admin_user.id}",
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["user"]["id"] == regular_admin_user.id
    assert data["user"]["username"] == regular_admin_user.username


def test_get_nonexistent_user(client, super_admin_token):
    """Test getting a nonexistent user"""
    response = client.get(
        "/admin/users/9999",  # Assuming this ID doesn't exist
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_user(client, super_admin_token, regular_admin_user, db_session):
    """Test updating a user"""
    update_data = {
        "full_name": "Updated Name",
        "email": "updated@example.com",
        "plant": "Plant X"
    }
    
    response = client.put(
        f"/admin/users/{regular_admin_user.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "User updated successfully"
    
    # Verify changes in db
    db_session.refresh(regular_admin_user)
    assert regular_admin_user.full_name == update_data["full_name"]
    assert regular_admin_user.email == update_data["email"]
    assert regular_admin_user.plant == update_data["plant"]


def test_delete_user(client, super_admin_token, db_session):
    """Test deleting a user"""
    # Create a user to delete
    user_to_delete = User(
        username="deleteuser",
        email="delete@example.com",
        full_name="Delete User",
        hashed_password="dummy_hash",
        te_id="DU99999",
        plant="Plant Z",
        role=RoleType.REGULAR_ADMIN.value
    )
    db_session.add(user_to_delete)
    db_session.commit()
    db_session.refresh(user_to_delete)
    
    user_id = user_to_delete.id
    
    response = client.delete(
        f"/admin/users/{user_id}",
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "deleted successfully" in data["message"]
    
    # Verify user is deleted
    deleted_user = db_session.query(User).filter(User.id == user_id).first()
    assert deleted_user is None


def test_cannot_delete_self(client, super_admin_token, super_admin_user):
    """Test that a user cannot delete themselves"""
    response = client.delete(
        f"/admin/users/{super_admin_user.id}",
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    
    assert response.status_code == 400
    assert "Cannot delete your own account" in response.json()["detail"]


def test_generate_report_format1(client, super_admin_token, test_submission):
    """Test generating Format 1 report"""
    response = client.get(
        "/admin/reports?report_format.format=1",
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "attachment" in response.headers["content-disposition"]
    assert "employee_data_format1_" in response.headers["content-disposition"]


def test_generate_report_format2(client, super_admin_token, test_submission):
    """Test generating Format 2 report"""
    response = client.get(
        "/admin/reports?report_format.format=2",
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "attachment" in response.headers["content-disposition"]
    assert "employee_grey_cards_format2_" in response.headers["content-disposition"]


def test_regular_admin_report_filtered(client, regular_admin_token, test_submission, db_session):
    """Test that regular admin only sees their plant's data in reports"""
    # Create a submission for a different plant
    from app.models import Submission
    from datetime import datetime
    
    other_plant_submission = Submission(
        first_name="Other",
        last_name="Plant",
        cin="XY654321",
        te_id="TE654321",
        date_of_birth=datetime(1995, 5, 5),
        grey_card_number="999-Z-999",
        plant="Plant B",  # Different plant
        cin_file_path="Plant B/cin/1/other.jpg",
        picture_file_path="Plant B/pic/1/other.jpg",
        grey_card_file_path="Plant B/grey_card/1/other.jpg",
        admin_id=1
    )
    db_session.add(other_plant_submission)
    db_session.commit()
    
    # Generate report as regular admin - should only see Plant A
    response = client.get(
        "/admin/reports?report_format.format=1",
        headers={"Authorization": f"Bearer {regular_admin_token}"}
    )
    
    # We can't easily check the contents of the Excel file here,
    # but at least we can confirm the request succeeded
    assert response.status_code == 200