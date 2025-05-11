from fastapi.testclient import TestClient
import pytest
from app.security import create_access_token
from app.models import User, RoleType


def test_create_user(client, super_admin_user):
    # Create access token for super admin
    access_token = create_access_token(data={"sub": super_admin_user.username})
    
    # Create a new user
    response = client.post(
        "/admin/users",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "full_name": "New User",
            "te_id": "NU001",
            "plant": "Plant2",
            "role": "regular_admin"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["must_reset_password"] is True


def test_create_user_regular_admin_forbidden(client, regular_admin_user):
    # Create access token for regular admin
    access_token = create_access_token(data={"sub": regular_admin_user.username})
    
    # Try to create a new user
    response = client.post(
        "/admin/users",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "full_name": "New User",
            "te_id": "NU001",
            "plant": "Plant2",
            "role": "regular_admin"
        }
    )
    
    assert response.status_code == 403


def test_get_users(client, super_admin_user, regular_admin_user):
    # Create access token for super admin
    access_token = create_access_token(data={"sub": super_admin_user.username})
    
    # Get all users
    response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # super_admin_user and regular_admin_user


def test_update_user(client, super_admin_user, regular_admin_user, db):
    # Create access token for super admin
    access_token = create_access_token(data={"sub": super_admin_user.username})
    
    # Update regular admin
    response = client.put(
        f"/admin/users/{regular_admin_user.id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "plant": "UpdatedPlant",
            "is_active": False
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["plant"] == "UpdatedPlant"
    assert data["is_active"] is False
    
    # Verify in database
    updated_user = db.query(User).filter(User.id == regular_admin_user.id).first()
    assert updated_user.plant == "UpdatedPlant"
    assert updated_user.is_active is False


def test_delete_user(client, super_admin_user, regular_admin_user, db):
    # Create access token for super admin
    access_token = create_access_token(data={"sub": super_admin_user.username})
    
    # Delete regular admin
    response = client.delete(
        f"/admin/users/{regular_admin_user.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 204
    
    # Verify in database
    deleted_user = db.query(User).filter(User.id == regular_admin_user.id).first()
    assert deleted_user is None