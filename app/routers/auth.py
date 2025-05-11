from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any, Dict, Union
import logging

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
    """
    Authenticate user and return access token with user info
    """
    try:
        # Get credentials from either form data or JSON body
        username = None
        password = None
        
        if form_data:
            username = form_data.username
            password = form_data.password
            print(f"Debug - Form data received: username={username}")
        else:
            # Try to parse JSON body
            try:
                body = await request.json()
                username = body.get("username")
                password = body.get("password")
                print(f"Debug - JSON data received: username={username}")
            except Exception as e:
                print(f"Debug - Error parsing JSON: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid request format: {str(e)}. Provide credentials via form data or JSON body",
                )
        
        if not username or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password are required",
            )
        
        # Authenticate user
        print(f"Debug - Authenticating user: {username}")
        user = authenticate_user(db, username, password)
        if not user:
            print(f"Debug - Authentication failed for user: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generate token
        print(f"Debug - Authentication successful for user: {username}")
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role}, 
            expires_delta=access_token_expires
        )
        
        # Prepare and return response
        response_data = {
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
        print(f"Debug - Returning token and user data")
        return response_data

    except HTTPException as he:
        # Re-raise HTTP exceptions as they are already properly formatted
        print(f"Debug - HTTP Exception: {he.detail}")
        raise
    except Exception as e:
        # Catch any other exceptions and return a 500 error
        print(f"Debug - Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.post("/reset-password", response_model=Dict[str, Any])
async def reset_password(
    password_data: PasswordReset,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    try:
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
    except HTTPException as he:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.get("/me", response_model=Dict[str, Any])
async def read_users_me(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    try:
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )