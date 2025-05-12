import pytest
from fastapi.testclient import TestClient
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
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
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
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Password updated successfully"
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
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["user"]["username"] == "regularadmin"
    assert data["user"]["email"] == "regularadmin@example.com"
    assert data["user"]["role"] == "regular_admin"


def test_get_current_user_invalid_token(client):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"