"""
API 路由
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import StreamingResponse
import json

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from rag_system import RecipeRAGSystem
from .food import get_food_name
router = APIRouter()

# 由于RecipeRAGSystem现在是单例模式，我们不需要维护全局实例
# 直接在需要时获取单例实例即可

def get_rag_system():
    """获取 RAG 系统实例 - 现在返回单例实例"""
    return RecipeRAGSystem()


class QuestionRequest(BaseModel):
    question: str
    image_name: Optional[str] = None


class SearchRequest(BaseModel):
    category: str
    query: Optional[str] = ""


class AnswerResponse(BaseModel):
    answer: str
    route_type: str
    documents: List[dict]


@router.get("/stats")
async def get_statistics(rag: RecipeRAGSystem = Depends(get_rag_system)):
    """获取知识库统计信息"""
    try:
        stats = rag.get_statistics()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    # 如果上传了图片，先解析图片有什么蔬菜，然后获取，蔬菜类型的食谱
    foodName = ''
    if request.image_name:
        # 解析图片，获取蔬菜类型
        image_path = Path("uploads") / request.image_name
        if not image_path.exists():
            raise HTTPException(status_code=400, detail="图片不存在")
        # 这里调用API获取食物名称
        print("开始解析图片")
        foodName = get_food_name(image_path)
        print("解析到的食物名称:", foodName)
    if request.question.strip() == "":
        raise HTTPException(status_code=400, detail="问题不能为空")
    print("解析到的食物名称:", foodName)
    if foodName == "没有食材":
        raise HTTPException(status_code=400, detail="图片中没有食材")
    foodName = "我有"+foodName+","
    """提问接口"""
    try:
        rag = RecipeRAGSystem()  # 获取单例实例
        # 确保只在非流式模式下调用
        result = rag.ask_question(foodName + request.question, stream=True)
        return result
    except Exception as e:
        print("提问接口出问题了,问题是")
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask_stream")
async def ask_question_stream(request: QuestionRequest):
    """流式提问接口"""
    try:
        rag = RecipeRAGSystem()
        
        foodName = ''
        if request.image_name:
            image_path = Path("uploads") / request.image_name
            if not image_path.exists():
                raise HTTPException(status_code=400, detail="图片不存在")
            print("开始解析图片")
            foodName = get_food_name(image_path)
            print("解析到的食物名称:", foodName)
        else:print("没有图片")
        if foodName == "没有食材":
            raise HTTPException(status_code=400, detail="图片中没有食材")
        
        question = request.question
        if foodName:
            question = "我有" + foodName + "," + question
        
        def generate_stream():
            stream_generator = rag.ask_question(question, stream=True)
            
            for chunk in stream_generator:
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        print("流式提问接口出问题了,问题是")
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_by_category(request: SearchRequest, rag: RecipeRAGSystem = Depends(get_rag_system)):
    """按分类搜索菜品"""
    try:
        dishes = rag.search_by_category(request.category, request.query)
        return {
            "success": True,
            "data": {
                "category": request.category,
                "dishes": dishes
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_categories():
    """获取支持的分类列表"""
    try:
        from rag_modules import DataPreparationModule
        categories = DataPreparationModule.get_supported_categories()
        return {
            "success": True,
            "data": categories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/difficulties")
async def get_difficulties():
    """获取支持的难度列表"""
    try:
        from rag_modules import DataPreparationModule
        difficulties = DataPreparationModule.get_supported_difficulties()
        return {
            "success": True,
            "data": difficulties
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))