from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base


class RoleType(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    REGULAR_ADMIN = "regular_admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    te_id = Column(String, unique=True, index=True)
    role = Column(Enum(RoleType), default=RoleType.REGULAR_ADMIN)
    plant = Column(String)
    must_reset_password = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    submissions = relationship("Submission", back_populates="admin")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    cin = Column(String, index=True)
    te_id = Column(String, index=True)
    date_of_birth = Column(DateTime)
    grey_card_number = Column(String, index=True)
    plant = Column(String, index=True)
    cin_file_path = Column(String)
    picture_file_path = Column(String)
    grey_card_file_path = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    admin_id = Column(Integer, ForeignKey("users.id"))
    
    admin = relationship("User", back_populates="submissions")