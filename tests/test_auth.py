import pytest
from fastapi.testclient import TestClient
<<<<<<< HEAD
from app.security import get_password_hash


def test_login_successful(client, regular_admin_user):
    """Test successful login"""
    response = client.post(
        "/auth/login",
        json={"username": regular_admin_user.username, "password": "password123"}
    )
=======
from app.security import create_access_token, get_password_hash
from app.models import User


def test_login_success(client, regular_admin_user):
    response = client.post(
        "/auth/login",
        json={
            "username": "regularadmin",
            "password": "password123"
        }
    )
    
>>>>>>> 4b5d3fba7805a1c8557e169e87f416671e14a7ac
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
<<<<<<< HEAD
    assert data["user"]["username"] == regular_admin_user.username
    assert data["user"]["role"] == regular_admin_user.role


def test_login_form_data(client, regular_admin_user):
    """Test login with form data"""
    response = client.post(
        "/auth/login",
        data={"username": regular_admin_user.username, "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_invalid_credentials(client, regular_admin_user):
    """Test login with invalid credentials"""
    response = client.post(
        "/auth/login",
        json={"username": regular_admin_user.username, "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_inactive_user(client, db_session, regular_admin_user):
    """Test login with inactive user"""
    # Deactivate the user
    regular_admin_user.is_active = False
    db_session.commit()
    
    response = client.post(
        "/auth/login",
        json={"username": regular_admin_user.username, "password": "password123"}
    )
    assert response.status_code == 401


def test_login_missing_fields(client):
    """Test login with missing fields"""
    response = client.post(
        "/auth/login",
        json={"username": "testuser"}  # missing password
    )
    assert response.status_code == 400
    
    response = client.post(
        "/auth/login",
        json={"password": "testpass"}  # missing username
    )
    assert response.status_code == 400


def test_reset_password(client, regular_admin_token, db_session, regular_admin_user):
    """Test password reset functionality"""
    response = client.post(
        "/auth/reset-password",
        json={
            "current_password": "password123",
            "new_password": "NewPassword123"
        },
        headers={"Authorization": f"Bearer {regular_admin_token}"}
=======
    assert data["user"]["username"] == "regularadmin"
    assert data["user"]["role"] == "regular_admin"


def test_login_invalid_credentials(client):
    response = client.post(
        "/auth/login",
        json={
            "username": "nonexistent",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_reset_password(client, regular_admin_user):
    # Login first to get token
    login_response = client.post(
        "/auth/login",
        json={
            "username": "regularadmin",
            "password": "password123"
        }
    )
    
    token = login_response.json()["access_token"]
    
    # Reset password
    response = client.post(
        "/auth/reset-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": "password123",
            "new_password": "NewPassword123"
        }
>>>>>>> 4b5d3fba7805a1c8557e169e87f416671e14a7ac
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Password updated successfully"
<<<<<<< HEAD
    
    # Verify user must_reset_password flag was updated
    db_session.refresh(regular_admin_user)
    assert regular_admin_user.must_reset_password == False


def test_reset_password_incorrect_current(client, regular_admin_token):
    """Test password reset with incorrect current password"""
    response = client.post(
        "/auth/reset-password",
        json={
            "current_password": "wrongpassword",
            "new_password": "NewPassword123"
        },
        headers={"Authorization": f"Bearer {regular_admin_token}"}
    )
    
    assert response.status_code == 400
    assert "Current password is incorrect" in response.json()["detail"]


def test_reset_password_weak_new_password(client, regular_admin_token):
    """Test password reset with weak new password"""
    response = client.post(
        "/auth/reset-password",
        json={
            "current_password": "password123",
            "new_password": "weak"  # Too short, no digits, no uppercase
        },
        headers={"Authorization": f"Bearer {regular_admin_token}"}
    )
    
    assert response.status_code == 422  # Validation error


def test_get_current_user(client, regular_admin_token, regular_admin_user):
    """Test getting current user info"""
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {regular_admin_token}"}
=======
    assert not data["user"]["must_reset_password"]


def test_reset_password_wrong_current(client, regular_admin_user):
    # Login first to get token
    login_response = client.post(
        "/auth/login",
        json={
            "username": "regularadmin",
            "password": "password123"
        }
    )
    
    token = login_response.json()["access_token"]
    
    # Try to reset password with wrong current password
    response = client.post(
        "/auth/reset-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": "wrongpassword",
            "new_password": "NewPassword123"
        }
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Current password is incorrect"


def test_get_current_user(client, regular_admin_user):
    # Login first to get token
    login_response = client.post(
        "/auth/login",
        json={
            "username": "regularadmin",
            "password": "password123"
        }
    )
    
    token = login_response.json()["access_token"]
    
    # Get current user info
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
>>>>>>> 4b5d3fba7805a1c8557e169e87f416671e14a7ac
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
<<<<<<< HEAD
    assert data["user"]["username"] == regular_admin_user.username
    assert data["user"]["email"] == regular_admin_user.email
    assert data["user"]["role"] == regular_admin_user.role


def test_get_current_user_invalid_token(client):
    """Test getting user info with invalid token"""
=======
    assert data["user"]["username"] == "regularadmin"
    assert data["user"]["email"] == "regularadmin@example.com"
    assert data["user"]["role"] == "regular_admin"


def test_get_current_user_invalid_token(client):
>>>>>>> 4b5d3fba7805a1c8557e169e87f416671e14a7ac
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
<<<<<<< HEAD
    assert response.status_code == 401
=======
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"
>>>>>>> 4b5d3fba7805a1c8557e169e87f416671e14a7ac
