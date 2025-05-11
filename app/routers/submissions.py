from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Submission, User, RoleType
from ..schemas import Submission as SubmissionSchema, SubmissionCreate
from ..dependencies import get_current_admin
from ..storage import file_storage
from slowapi import Limiter
from slowapi.util import get_remote_address
import json

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/submissions",
    tags=["submissions"],
)


@router.post("/", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_submission(
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
    db: Session = Depends(get_db)
):
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
        grey_card_file_path=grey_card_path
    )
    
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    
    return {"id": db_submission.id, "message": "Submission created successfully"}


@router.get("/", response_model=List[SubmissionSchema])
async def read_submissions(
    skip: int = 0,
    limit: int = 100,
    plant: Optional[str] = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    query = db.query(Submission)
    
    # Filter by plant if user is regular admin
    if current_user.role == RoleType.REGULAR_ADMIN:
        query = query.filter(Submission.plant == current_user.plant)
    # Filter by specified plant if provided
    elif plant:
        query = query.filter(Submission.plant == plant)
    
    submissions = query.offset(skip).limit(limit).all()
    return submissions


@router.get("/{submission_id}", response_model=SubmissionSchema)
async def read_submission(
    submission_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
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
    
    return submission