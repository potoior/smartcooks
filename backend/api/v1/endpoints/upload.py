from fastapi import APIRouter, UploadFile, File, Depends

from schemas.upload import UploadResponse, DeleteResponse, FileListResponse
from services.upload_service import UploadService

router = APIRouter()


def get_upload_service() -> UploadService:
    """获取上传服务实例"""
    return UploadService()


@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    upload_service: UploadService = Depends(get_upload_service)
):
    """
    上传图片
    
    Args:
        file: 上传的图片文件
        
    Returns:
        上传结果，包含图片URL
    """
    result = await upload_service.upload_image(file)
    return result


@router.delete("/upload/{filename}", response_model=DeleteResponse)
async def delete_image(
    filename: str,
    upload_service: UploadService = Depends(get_upload_service)
):
    """
    删除上传的图片
    
    Args:
        filename: 要删除的文件名
        
    Returns:
        删除结果
    """
    result = upload_service.delete_image(filename)
    return result


@router.get("/upload/list", response_model=FileListResponse)
async def list_images(upload_service: UploadService = Depends(get_upload_service)):
    """
    获取已上传的图片列表
    
    Returns:
        图片列表
    """
    result = upload_service.list_images()
    return result
