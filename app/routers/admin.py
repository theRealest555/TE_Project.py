from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from fastapi.responses import StreamingResponse

from ..database import get_db
from ..models import User, RoleType
from ..schemas import User as UserSchema, UserCreate, UserUpdate, ReportFormat
from ..dependencies import get_super_admin, get_current_admin
from ..security import get_password_hash
from ..reports import report_generator


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.post("/users", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    current_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    # Check if username or email already exists
    db_user = db.query(User).filter(
        (User.username == user_create.username) | 
        (User.email == user_create.email) |
        (User.te_id == user_create.te_id)
    ).first()
    
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username, email, or TE ID already registered"
        )
    
    # Set default password to TE ID if not provided
    password = user_create.password if user_create.password else user_create.te_id
    hashed_password = get_password_hash(password)
    
    # Create new user
    db_user = User(
        username=user_create.username,
        email=user_create.email,
        full_name=user_create.full_name,
        hashed_password=hashed_password,
        te_id=user_create.te_id,
        plant=user_create.plant,
        role=user_create.role,
        must_reset_password=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {
        "status": "success",
        "message": "User created successfully",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "full_name": db_user.full_name,
            "te_id": db_user.te_id,
            "plant": db_user.plant,
            "role": db_user.role
        }
    }


@router.get("/users", response_model=Dict[str, Any])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    # Get total count for pagination
    total_count = db.query(User).count()
    
    # Apply pagination
    users = db.query(User).offset(skip).limit(limit).all()
    
    return {
        "status": "success",
        "total": total_count,
        "skip": skip,
        "limit": limit,
        "users": users
    }


@router.get("/users/{user_id}", response_model=Dict[str, Any])
async def read_user(
    user_id: int,
    current_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "status": "success",
        "user": db_user
    }


@router.put("/users/{user_id}", response_model=Dict[str, Any])
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update user fields if provided
    update_data = user_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    
    return {
        "status": "success",
        "message": "User updated successfully",
        "user": db_user
    }


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting yourself
    if db_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    db.delete(db_user)
    db.commit()
    
    return {
        "status": "success",
        "message": f"User {db_user.username} deleted successfully"
    }


@router.get("/reports")
async def generate_report(
    report_format: ReportFormat,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    # For regular admins, only show their plant's data
    plant = current_user.plant if current_user.role == RoleType.REGULAR_ADMIN else None
    
    if report_format.format == 1:
        output, filename = report_generator.generate_format_1(db, plant)
    else:
        output, filename = report_generator.generate_format_2(db, plant)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )