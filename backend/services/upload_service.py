from pathlib import Path
from typing import List
import uuid
import shutil
from fastapi import UploadFile, HTTPException


class UploadService:
    """上传服务层"""
    
    def __init__(self):
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        self.allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def validate_file(self, file: UploadFile) -> bool:
        """
        验证文件类型和大小
        
        Args:
            file: 上传的文件
            
        Returns:
            是否有效
        """
        if not file.filename:
            return False
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            return False
        
        return True
    
    async def upload_image(self, file: UploadFile) -> dict:
        """
        上传图片
        
        Args:
            file: 上传的图片文件
            
        Returns:
            上传结果
        """
        if not self.validate_file(file):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型。支持的类型: {', '.join(self.allowed_extensions)}"
            )
        
        try:
            file_ext = Path(file.filename).suffix.lower()
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = self.upload_dir / unique_filename
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                file_path.unlink()
                raise HTTPException(
                    status_code=400,
                    detail=f"文件大小超过限制（最大 {self.max_file_size // (1024*1024)}MB）"
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
    
    def delete_image(self, filename: str) -> dict:
        """
        删除上传的图片
        
        Args:
            filename: 要删除的文件名
            
        Returns:
            删除结果
        """
        file_path = self.upload_dir / filename
        
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
    
    def list_images(self) -> dict:
        """
        获取已上传的图片列表
        
        Returns:
            图片列表
        """
        try:
            images = []
            for file_path in self.upload_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in self.allowed_extensions:
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
