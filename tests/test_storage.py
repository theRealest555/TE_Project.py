import pytest
import os
import uuid
import shutil
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, UploadFile
from pathlib import Path

from app.storage import FileStorage, FileValidator
from app.config import settings


class TestFileValidator:
    def test_validate_cin_filename(self):
        # Valid CIN filenames
        assert FileValidator.validate_cin_filename("AB12345.jpg") is True
        assert FileValidator.validate_cin_filename("C67890.png") is True
        
        # Invalid CIN filenames
        assert FileValidator.validate_cin_filename("AB12345.pdf") is False
        assert FileValidator.validate_cin_filename("12345.jpg") is False
        assert FileValidator.validate_cin_filename("ABC12345.jpg") is False
        assert FileValidator.validate_cin_filename("invalid_format.jpg") is False

    def test_validate_picture_filename(self):
        # Valid picture filenames
        assert FileValidator.validate_picture_filename("AB12345_i.jpg") is True
        assert FileValidator.validate_picture_filename("C67890_i.png") is True
        
        # Invalid picture filenames
        assert FileValidator.validate_picture_filename("AB12345.jpg") is False
        assert FileValidator.validate_picture_filename("12345_i.jpg") is False
        assert FileValidator.validate_picture_filename("AB12345_i.pdf") is False
        assert FileValidator.validate_picture_filename("invalid_format_i.jpg") is False

    def test_validate_grey_card_filename(self):
        # Valid grey card filenames
        assert FileValidator.validate_grey_card_filename("12345-A-67890.jpg") is True
        assert FileValidator.validate_grey_card_filename("67890-B-12345.png") is True
        
        # Invalid grey card filenames
        assert FileValidator.validate_grey_card_filename("12345A67890.jpg") is False
        assert FileValidator.validate_grey_card_filename("12345-A-67890.pdf") is False
        assert FileValidator.validate_grey_card_filename("A12345-A-67890.jpg") is False
        assert FileValidator.validate_grey_card_filename("invalid-format.jpg") is False


class TestFileStorage:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # Setup - Create a test uploads directory
        self.test_uploads_dir = Path("test_uploads")
        settings.UPLOADS_DIR = str(self.test_uploads_dir)
        settings.MAX_FILES_PER_FOLDER = 5
        
        # Create the test directory
        self.test_uploads_dir.mkdir(exist_ok=True)
        
        # Initialize the FileStorage instance
        self.file_storage = FileStorage()
        
        # Run the test
        yield
        
        # Teardown - Remove the test uploads directory
        if self.test_uploads_dir.exists():
            shutil.rmtree(self.test_uploads_dir)

    def test_get_storage_path(self):
        # Test getting storage path for a new plant/file type
        plant_name = "test_plant"
        file_type = "cin"
        
        path = self.file_storage._get_storage_path(plant_name, file_type)
        
        # Check that the path is correctly structured
        assert path == self.test_uploads_dir / plant_name / file_type / "1"
        assert path.exists()
        
        # Test that calling again returns same path when folder isn't full
        path2 = self.file_storage._get_storage_path(plant_name, file_type)
        assert path == path2
        
        # Test that a new folder is created when the current one is full
        # Add dummy files to fill the folder
        for i in range(settings.MAX_FILES_PER_FOLDER):
            dummy_file = path / f"dummy_{i}.txt"
            dummy_file.touch()
        
        # Now get the path again
        path3 = self.file_storage._get_storage_path(plant_name, file_type)
        assert path3 == self.test_uploads_dir / plant_name / file_type / "2"
        assert path3.exists()

    @pytest.mark.asyncio
    async def test_save_file_success(self):
        # Mock file content
        content = b"test file content"
        
        # Create mock upload file
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "AB12345.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.read.return_value = content
        mock_file.seek = AsyncMock()
        
        # Mock UUID to have deterministic output
        mock_uuid = "1234567890abcdef1234567890abcdef"
        # Mock aiofiles.open to avoid actual file operations
        mock_open = AsyncMock()
        mock_context = AsyncMock()
        mock_open.__aenter__.return_value = mock_context
        with patch("aiofiles.open", return_value=mock_open):
            with patch("uuid.uuid4", return_value=MagicMock(hex=mock_uuid)):
                # Call save_file
                plant_name = "test_plant"
                file_type = "cin"
                file_path = await self.file_storage.save_file(mock_file, plant_name, file_type)
        
        # Check the returned path is correct
        expected_path = f"{plant_name}/{file_type}/1/{mock_uuid}.jpg"
        assert file_path == expected_path
        
        # Check that file was "saved" correctly
        # We're mocking aiofiles, so we can't check the actual file content
        mock_file.read.assert_called_once()
        mock_file.seek.assert_called_once_with(0)
        mock_context.write.assert_called_once_with(content)

    @pytest.mark.asyncio
    async def test_save_file_file_too_large(self):
        # Mock file content that exceeds the max size
        content = b"x" * (5 * 1024 * 1024 + 1)  # 5MB + 1 byte
        
        # Create mock upload file
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "AB12345.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.read.return_value = content
        mock_file.seek = AsyncMock()
        
        # Call save_file and expect an exception
        with pytest.raises(HTTPException) as excinfo:
            await self.file_storage.save_file(mock_file, "test_plant", "cin")
        
        assert excinfo.value.status_code == 400
        assert "File too large" in excinfo.value.detail

    @pytest.mark.asyncio
    async def test_save_file_invalid_type(self):
        # Mock file content
        content = b"test file content"
        
        # Create mock upload file with invalid content type
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "AB12345.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read.return_value = content
        mock_file.seek = AsyncMock()
        
        # Call save_file and expect an exception
        with pytest.raises(HTTPException) as excinfo:
            await self.file_storage.save_file(mock_file, "test_plant", "cin")
        
        assert excinfo.value.status_code == 400
        assert "Invalid file type" in excinfo.value.detail

    @pytest.mark.asyncio
    async def test_save_file_invalid_filename(self):
        # Mock file content
        content = b"test file content"
        
        # Create mock upload file with invalid filename for the file type
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "invalid_name.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.read.return_value = content
        mock_file.seek = AsyncMock()
        
        # Call save_file and expect an exception
        with pytest.raises(HTTPException) as excinfo:
            await self.file_storage.save_file(mock_file, "test_plant", "cin")
        
        assert excinfo.value.status_code == 400
        assert "Invalid CIN filename format" in excinfo.value.detail

    @pytest.mark.asyncio
    async def test_save_file_with_aiofiles(self):
        # Mock file content
        content = b"test file content"
        
        # Create mock upload file
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "AB12345.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.read.return_value = content
        mock_file.seek = AsyncMock()
        
        # Mock aiofiles.open to avoid actual file operations
        mock_open = AsyncMock()
        mock_context = AsyncMock()
        mock_open.__aenter__.return_value = mock_context
        
        with patch("aiofiles.open", return_value=mock_open):
            with patch("uuid.uuid4", return_value=MagicMock(hex="1234567890abcdef1234567890abcdef")):
                # Call save_file
                file_path = await self.file_storage.save_file(mock_file, "test_plant", "cin")
        
        # Check that aiofiles.open was called correctly
        mock_context.write.assert_called_once_with(content)