from fastapi import Depends
from services.rag_service import RAGService
from services.upload_service import UploadService
from services.image_service import ImageService


def get_rag_service() -> RAGService:
    """获取 RAG 服务实例"""
    return RAGService()


def get_upload_service() -> UploadService:
    """获取上传服务实例"""
    return UploadService()


def get_image_service() -> ImageService:
    """获取图片服务实例"""
    return ImageService()
