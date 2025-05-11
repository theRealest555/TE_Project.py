from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import User, RoleType
from .schemas import TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_password(plain_password, hashed_password):
    """Verify password by comparing plain password to hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Hash a password for storing"""
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str):
    """Authenticate a user by username and password"""
    try:
        print(f"Security - Looking up user: {username}")
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            print(f"Security - User not found: {username}")
            return False
        
        if not user.is_active:
            print(f"Security - User is inactive: {username}")
            return False
            
        if not verify_password(password, user.hashed_password):
            print(f"Security - Invalid password for user: {username}")
            return False
            
        print(f"Security - User authenticated successfully: {username}")
        return user
    except Exception as e:
        print(f"Security - Error during authentication: {str(e)}")
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    except Exception as e:
        print(f"Security - Error creating access token: {str(e)}")
        raise


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get the current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        print(f"Security - JWT Error: {str(e)}")
        raise credentials_exception
    except Exception as e:
        print(f"Security - Unexpected error decoding token: {str(e)}")
        raise credentials_exception
    
    try:
        user = db.query(User).filter(User.username == token_data.username).first()
        if user is None:
            print(f"Security - User from token not found: {token_data.username}")
            raise credentials_exception
        if not user.is_active:
            print(f"Security - User from token is inactive: {token_data.username}")
            raise HTTPException(status_code=400, detail="Inactive user")
        return user
    except HTTPException:
        raise
    except Exception as e:
        print(f"Security - Error getting user from database: {str(e)}")
        raise credentials_exception


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Check if the current user is active"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def check_super_admin(current_user: User = Depends(get_current_user)):
    """Check if the current user is a super admin"""
    if current_user.role != RoleType.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user