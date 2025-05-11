from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from ..database import get_db
from ..models import Submission, User, RoleType
from ..schemas import Submission as SubmissionSchema, SubmissionCreate
from ..dependencies import get_current_admin
from ..storage import file_storage
import json

router = APIRouter(
    prefix="/submissions",
    tags=["submissions"],
)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
async def create_submission(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    cin: str = Form(...),
    te_id: str = Form(...),
    date_of_birth: str = Form(...),
    grey_card_number: str = Form(...),
    plant: str = Form(...),
    cin_file: UploadFile = File(...),
    picture_file: UploadFile = File(...),
    grey_card_file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    # Create submission data
    submission_data = {
        "first_name": first_name,
        "last_name": last_name,
        "cin": cin,
        "te_id": te_id,
        "date_of_birth": date_of_birth,
        "grey_card_number": grey_card_number,
        "plant": plant
    }
    
    # Validate submission data using Pydantic model
    try:
        submission_create = SubmissionCreate(**submission_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid submission data: {str(e)}"
        )
    
    # Save files
    try:
        cin_path = await file_storage.save_file(cin_file, plant, "cin")
        picture_path = await file_storage.save_file(picture_file, plant, "pic")
        grey_card_path = await file_storage.save_file(grey_card_file, plant, "grey_card")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File upload error: {str(e)}"
        )
    
    # Create submission in database
    db_submission = Submission(
        **submission_data,
        cin_file_path=cin_path,
        picture_file_path=picture_path,
        grey_card_file_path=grey_card_path,
        admin_id=current_user.id  # Set the admin ID
    )
    
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    
    # Return more comprehensive response
    return {
        "status": "success",
        "message": "Submission created successfully",
        "submission": {
            "id": db_submission.id,
            "first_name": db_submission.first_name,
            "last_name": db_submission.last_name,
            "cin": db_submission.cin,
            "te_id": db_submission.te_id,
            "plant": db_submission.plant,
            "created_at": db_submission.created_at
        }
    }


@router.get("/", response_model=Dict[str, Any])
async def read_submissions(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    plant: Optional[str] = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    query = db.query(Submission)
    
    # Filter by plant if user is regular admin
    if current_user.role == RoleType.REGULAR_ADMIN:
        query = query.filter(Submission.plant == current_user.plant)
    # Filter by specified plant if provided
    elif plant:
        query = query.filter(Submission.plant == plant)
    
    # Get total count for pagination
    total_count = query.count()
    
    # Apply pagination
    submissions = query.offset(skip).limit(limit).all()
    
    # Return enhanced response with pagination info
    return {
        "status": "success",
        "total": total_count,
        "skip": skip,
        "limit": limit,
        "submissions": submissions
    }


@router.get("/{submission_id}", response_model=Dict[str, Any])
async def read_submission(
    request: Request,
    submission_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Check if regular admin has access to this submission
    if current_user.role == RoleType.REGULAR_ADMIN and submission.plant != current_user.plant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this submission"
        )
    
    return {
        "status": "success",
        "submission": submission
    }