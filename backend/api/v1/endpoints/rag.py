from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import json

from schemas.rag import QuestionRequest, SearchRequest, AnswerResponse
from services.rag_service import RAGService

router = APIRouter()


def get_rag_service() -> RAGService:
    """获取 RAG 服务实例"""
    return RAGService()


@router.get("/stats")
async def get_statistics(rag_service: RAGService = Depends(get_rag_service)):
    """获取知识库统计信息"""
    try:
        stats = rag_service.get_statistics()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest, rag_service: RAGService = Depends(get_rag_service)):
    """提问接口"""
    try:
        question = rag_service.ask_with_image(request.question, request.image_name)
        result = rag_service.ask_question(question, stream=False)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print("提问接口出问题了,问题是")
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask_stream")
async def ask_question_stream(request: QuestionRequest, rag_service: RAGService = Depends(get_rag_service)):
    """流式提问接口"""
    try:
        question = rag_service.ask_with_image(request.question, request.image_name)
        
        def generate_stream():
            stream_generator = rag_service.ask_question(question, stream=True)
            
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print("流式提问接口出问题了,问题是")
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_by_category(request: SearchRequest, rag_service: RAGService = Depends(get_rag_service)):
    """按分类搜索菜品"""
    try:
        dishes = rag_service.search_by_category(request.category, request.query)
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
async def get_categories(rag_service: RAGService = Depends(get_rag_service)):
    """获取支持的分类列表"""
    try:
        categories = rag_service.get_categories()
        return {
            "success": True,
            "data": categories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/difficulties")
async def get_difficulties(rag_service: RAGService = Depends(get_rag_service)):
    """获取支持的难度列表"""
    try:
        difficulties = rag_service.get_difficulties()
        return {
            "success": True,
            "data": difficulties
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
