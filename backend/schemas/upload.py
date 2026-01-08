from pydantic import BaseModel
from typing import Optional


class UploadResponse(BaseModel):
    success: bool
    url: Optional[str] = None
    filename: Optional[str] = None
    size: Optional[int] = None
    message: Optional[str] = None


class DeleteResponse(BaseModel):
    success: bool
    message: str


class FileListResponse(BaseModel):
    success: bool
    files: list
