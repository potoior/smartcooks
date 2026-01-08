"""
图片上传路由
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uuid
import shutil
from typing import List
import os

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_file(file: UploadFile) -> bool:
    """验证文件类型和大小"""
    if not file.filename:
        return False
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False
    
    return True


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    上传图片
    
    Args:
        file: 上传的图片文件
        
    Returns:
        上传结果，包含图片URL
    """
    if not validate_file(file):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。支持的类型: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    try:
        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            file_path.unlink()
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制（最大 {MAX_FILE_SIZE // (1024*1024)}MB）"
            )
        
        return {
            "success": True,
            "message": "图片上传成功",
            "url": f"/uploads/{unique_filename}",
            "filename": unique_filename,
            "size": file_size
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片上传失败: {str(e)}")


@router.delete("/upload/{filename}")
async def delete_image(filename: str):
    """
    删除上传的图片
    
    Args:
        filename: 要删除的文件名
        
    Returns:
        删除结果
    """
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    try:
        file_path.unlink()
        return {
            "success": True,
            "message": "图片删除成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片删除失败: {str(e)}")


@router.get("/upload/list")
async def list_images():
    """
    获取已上传的图片列表
    
    Returns:
        图片列表
    """
    try:
        images = []
        for file_path in UPLOAD_DIR.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ALLOWED_EXTENSIONS:
                images.append({
                    "filename": file_path.name,
                    "url": f"/uploads/{file_path.name}",
                    "size": file_path.stat().st_size
                })
        
        return {
            "success": True,
            "data": images,
            "count": len(images)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图片列表失败: {str(e)}")
