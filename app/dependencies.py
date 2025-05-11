from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from .database import get_db
from .models import User, RoleType
from .security import get_current_user


def get_current_admin(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Verify the user is an admin (either super_admin or regular_admin)
    """
    if current_user.role not in [RoleType.SUPER_ADMIN, RoleType.REGULAR_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


def get_super_admin(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Verify the user is a super_admin
    """
    if current_user.role != RoleType.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required",
        )
    return current_user