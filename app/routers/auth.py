from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any, Dict, Union

from ..database import get_db
from ..models import User
from ..schemas import Token, LoginRequest, PasswordReset, User as UserSchema
from ..security import (
    authenticate_user, 
    create_access_token, 
    get_password_hash, 
    get_current_user,
    verify_password
)
from ..config import settings

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={401: {"description": "Unauthorized"}},
)


@router.post("/login", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: Union[OAuth2PasswordRequestForm, None] = Depends(None),
    login_data: Union[LoginRequest, None] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    # Try to get credentials from either form data or JSON body
    username = None
    password = None
    
    if form_data:
        username = form_data.username
        password = form_data.password
    else:
        # Try to parse JSON body
        try:
            body = await request.json()
            username = body.get("username")
            password = body.get("password")
        except:
            # If no form data and JSON parsing fails, raise error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request format. Provide credentials via form data or JSON body",
            )
    
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required",
        )
    
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, 
        expires_delta=access_token_expires
    )
    
    # Return token and user information
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "must_reset_password": user.must_reset_password
        }
    }


@router.post("/reset-password", response_model=Dict[str, Any])
async def reset_password(
    password_data: PasswordReset,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.must_reset_password = False
    db.commit()
    db.refresh(current_user)
    
    return {
        "status": "success",
        "message": "Password updated successfully",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "must_reset_password": current_user.must_reset_password
        }
    }


@router.get("/me", response_model=Dict[str, Any])
async def read_users_me(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    return {
        "status": "success",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "te_id": current_user.te_id,
            "plant": current_user.plant,
            "role": current_user.role,
            "must_reset_password": current_user.must_reset_password,
            "is_active": current_user.is_active
        }
    }