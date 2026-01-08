from fastapi import APIRouter, Depends

from schemas.image import FoodRecognitionResponse
from services.image_service import ImageService

router = APIRouter()


def get_image_service() -> ImageService:
    """获取图片服务实例"""
    return ImageService()


@router.post("/recognize", response_model=FoodRecognitionResponse)
async def recognize_food(
    image_path: str,
    image_service: ImageService = Depends(get_image_service)
):
    """
    识别图片中的食物
    
    Args:
        image_path: 图片路径
        
    Returns:
        识别结果
    """
    try:
        food_name = image_service.recognize_food(image_path)
        return {
            "success": True,
            "food_name": food_name
        }
    except Exception as e:
        return {
            "success": False,
            "food_name": "",
            "message": str(e)
        }
