from pydantic import BaseModel
from typing import Optional


class FoodRecognitionResponse(BaseModel):
    success: bool
    food_name: str
    message: Optional[str] = None
