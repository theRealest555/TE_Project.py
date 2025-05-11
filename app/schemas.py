from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
import re
from .models import RoleType


# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    te_id: str
    plant: str
    role: RoleType = RoleType.REGULAR_ADMIN


class UserCreate(UserBase):
    password: str = None  # Will be set to te_id by default


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    plant: Optional[str] = None
    role: Optional[RoleType] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    id: int
    is_active: bool
    must_reset_password: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class User(UserInDB):
    pass


# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[RoleType] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class PasswordReset(BaseModel):
    current_password: str
    new_password: str

    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v


# Submission schemas
class SubmissionBase(BaseModel):
    first_name: str
    last_name: str
    cin: str
    te_id: str
    date_of_birth: datetime
    grey_card_number: str
    plant: str

    @validator('cin')
    def validate_cin(cls, v):
        if not re.match(r'^[A-Za-z]{1,2}[0-9]+$', v):
            raise ValueError('Invalid CIN format')
        return v

    @validator('grey_card_number')
    def validate_grey_card(cls, v):
        if not re.match(r'^[0-9]+-[A-Za-z]-[0-9]+$', v):
            raise ValueError('Invalid Grey Card format')
        return v


class SubmissionCreate(SubmissionBase):
    pass


class SubmissionInDB(SubmissionBase):
    id: int
    cin_file_path: str
    picture_file_path: str
    grey_card_file_path: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    admin_id: int

    class Config:
        orm_mode = True


class Submission(SubmissionInDB):
    pass


# Report schemas
class ReportFormat(BaseModel):
    format: int = Field(..., ge=1, le=2)