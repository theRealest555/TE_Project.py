from pydantic_settings import BaseSettings
from pydantic import validator
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    APP_NAME: str = "TE Project"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File uploads
    UPLOADS_DIR: str = "uploads"
    MAX_FILES_PER_FOLDER: int = 100
    
    @validator("UPLOADS_DIR")
    def validate_uploads_dir(cls, v):
        path = Path(v)
        if not path.exists():
            path.mkdir(parents=True)
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()