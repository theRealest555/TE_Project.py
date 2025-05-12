import pytest
from datetime import timedelta
from fastapi import HTTPException
from jose import jwt
from app.security import (
    verify_password, 
    get_password_hash, 
    authenticate_user, 
    create_access_token, 
    get_current_user
)
from app.models import User, RoleType
from app.config import settings


def test_password_hashing():
    """Test password hashing and verification"""
    password = "TestPassword123"
    hashed = get_password_hash(password)
    
    # Hashed password should be different from original
    assert hashed != password
    
    # Verification should work
    assert verify_password(password, hashed) is True
    
    # Wrong password should fail verification
    assert verify_password("WrongPassword", hashed) is False


def test_authenticate_user(db, regular_admin_user):
    """Test user authentication"""
    # Test with correct credentials
    user = authenticate_user(db, "regularadmin", "password123")
    assert user is not False
    assert user.username == "regularadmin"
    
    # Test with incorrect password
    user = authenticate_user(db, "regularadmin", "wrongpassword")
    assert user is False
    
    # Test with non-existent user
    user = authenticate_user(db, "nonexistentuser", "password123")
    assert user is False
    
    # Test with inactive user
    regular_admin_user.is_active = False
    db.commit()
    user = authenticate_user(db, "regularadmin", "password123")
    assert user is False


def test_create_access_token():
    """Test access token creation"""
    # Create token with default expiry
    data = {"sub": "testuser"}
    token = create_access_token(data)
    
    # Decode and verify token
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "testuser"
    assert "exp" in payload
    
    # Create token with custom expiry
    delta = timedelta(minutes=15)
    token = create_access_token(data, expires_delta=delta)
    
    # Decode and verify token
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "testuser"
    assert "exp" in payload


async def test_get_current_user(db, regular_admin_user):
    """Test getting current user from token"""
    # Create a token
    data = {"sub": regular_admin_user.username}
    token = create_access_token(data)
    
    # Get user from token
    user = await get_current_user(token=token, db=db)
    assert user.id == regular_admin_user.id
    assert user.username == regular_admin_user.username
    
    # Test with invalid token
    invalid_token = "invalid.token.string"
    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(token=invalid_token, db=db)
    assert excinfo.value.status_code == 401
    
    # Test with non-existent user
    data = {"sub": "nonexistentuser"}
    token = create_access_token(data)
    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(token=token, db=db)
    assert excinfo.value.status_code == 401
    
    # Test with inactive user
    regular_admin_user.is_active = False
    db.commit()
    data = {"sub": regular_admin_user.username}
    token = create_access_token(data)
    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(token=token, db=db)
    assert excinfo.value.status_code == 400


async def test_check_super_admin(db, super_admin_user, regular_admin_user):
    """Test super admin permission check"""
    from app.security import check_super_admin
    
    # Test with super admin
    result = check_super_admin(super_admin_user)
    assert result == super_admin_user
    
    # Test with regular admin (should raise exception)
    with pytest.raises(HTTPException) as excinfo:
        check_super_admin(regular_admin_user)
    assert excinfo.value.status_code == 403
    assert "Not enough permissions" in excinfo.value.detail


def test_token_data_extraction(db, regular_admin_user):
    """Test extraction of data from token payload"""
    # Create a token with role information
    data = {
        "sub": regular_admin_user.username,
        "role": regular_admin_user.role
    }
    token = create_access_token(data)
    
    # Decode token
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    
    # Verify payload contents
    assert payload["sub"] == regular_admin_user.username
    assert payload["role"] == regular_admin_user.role
    assert "exp" in payload