import os
import re
import aiofiles
from fastapi import UploadFile, HTTPException
from pathlib import Path
from .config import settings
import uuid


class FileValidator:
    @staticmethod
    def validate_cin_filename(filename: str) -> bool:
        return bool(re.match(r'^[A-Za-z]{1,2}[0-9]+\.(jpg|jpeg|png)$', filename))

    @staticmethod
    def validate_picture_filename(filename: str) -> bool:
        return bool(re.match(r'^[A-Za-z]{1,2}[0-9]+_i\.(jpg|jpeg|png)$', filename))

    @staticmethod
    def validate_grey_card_filename(filename: str) -> bool:
        return bool(re.match(r'^[0-9]+-[A-Za-z]-[0-9]+\.(jpg|jpeg|png)$', filename))


class FileStorage:
    def __init__(self):
        self.base_dir = Path(settings.UPLOADS_DIR)
        self.max_files_per_folder = settings.MAX_FILES_PER_FOLDER

    def _get_storage_path(self, plant_name: str, file_type: str) -> Path:
        """Get the appropriate storage path based on plant name and file type."""
        base_path = self.base_dir / plant_name / file_type
        
        # Create directories if they don't exist
        if not base_path.exists():
            base_path.mkdir(parents=True, exist_ok=True)
        
        # Find the appropriate numbered folder
        for i in range(1, 10000):  # Reasonable upper limit
            folder_path = base_path / str(i)
            
            if not folder_path.exists():
                folder_path.mkdir(exist_ok=True)
                return folder_path
            
            # Count files in the folder
            file_count = sum(1 for _ in folder_path.glob('*'))
            if file_count < self.max_files_per_folder:
                return folder_path
        
        # If we get here, all folders are full (unlikely)
        raise HTTPException(status_code=500, detail="Storage capacity reached")

    async def save_file(self, file: UploadFile, plant_name: str, file_type: str) -> str:
        """Save a file to the appropriate location and return the path."""
        # Validate file type
        if file_type == "cin" and not FileValidator.validate_cin_filename(file.filename):
            raise HTTPException(status_code=400, detail="Invalid CIN filename format")
        elif file_type == "pic" and not FileValidator.validate_picture_filename(file.filename):
            raise HTTPException(status_code=400, detail="Invalid picture filename format")
        elif file_type == "grey_card" and not FileValidator.validate_grey_card_filename(file.filename):
            raise HTTPException(status_code=400, detail="Invalid grey card filename format")
        
        # Get storage path
        storage_path = self._get_storage_path(plant_name, file_type)
        
        # Generate a unique filename to avoid collisions
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = storage_path / unique_filename
        
        # Save the file
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        # Return the relative path from the base uploads directory
        return str(file_path.relative_to(self.base_dir))


file_storage = FileStorage()