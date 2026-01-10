from fastapi import APIRouter

from api.v1.endpoints import rag, upload, image, chat

api_router = APIRouter()

api_router.include_router(rag.router, prefix="/rag", tags=["RAG"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(upload.router, prefix="", tags=["Upload"])
api_router.include_router(image.router, prefix="/image", tags=["Image"])
