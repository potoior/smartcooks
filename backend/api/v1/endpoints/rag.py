from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import json
from schemas.rag import QuestionRequest, SearchRequest, AnswerResponse
from schemas.common import StandardResponse
from services.rag_service import RAGService
from services.chat_service import ChatService
from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def get_rag_service() -> RAGService:
    """获取 RAG 服务实例"""
    print("DEBUG: Entering get_rag_service")
    service = RAGService()
    print("DEBUG: RAGService instantiated")
    return service


@router.get("/stats", response_model=StandardResponse)
async def get_statistics(rag_service: RAGService = Depends(get_rag_service)):
    """获取知识库统计信息"""
    print("DEBUG: Entering get_statistics endpoint")
    stats = rag_service.get_statistics()
    print("DEBUG: Stats retrieved")
    return StandardResponse(data=stats)


@router.post("/ask", response_model=AnswerResponse)
async def ask_question(
    request: QuestionRequest, 
    rag_service: RAGService = Depends(get_rag_service),
    db: AsyncSession = Depends(get_db)
):
    """提问接口"""
    chat_service = ChatService(db)
    
    # 1. 获取或创建会话
    session_id = request.session_id
    if not session_id:
        session = await chat_service.create_session(title=request.question[:20])
        session_id = session.id
    
    # 2. 保存用户消息
    await chat_service.add_message(
        session_id=session_id,
        role="user",
        content=request.question,
        image_url=request.image_name # 简单起见存文件名，实际应存URL
    )

    # 3. 获取历史记录
    history_dicts = []
    if session_id:
        history_msgs = await chat_service.get_history(session_id)
        # 转换为字典列表，给RAG系统使用 (只取最近10条，避免token溢出)
        for msg in history_msgs[-10:]:
            history_dicts.append({
                "role": msg.role,
                "content": msg.content
            })

    # 4. 执行 RAG
    # 错误由全局异常处理器捕获
    question = rag_service.ask_with_image(request.question, request.image_name)
    result = rag_service.ask_question(question, chat_history=history_dicts, stream=False)
    
    # 5. 保存助手消息
    await chat_service.add_message(
        session_id=session_id,
        role="assistant",
        content=result.answer,
        meta_data={"documents": [d.metadata for d in result.documents]}
    )
    
    # 5. 返回结果（附带 session_id）
    # 注意：AnswerResponse 这里可能需要扩展 session_id 字段，或者我们在前端处理
    # 暂时我们在返回体里动态添加，或者修改 AnswerResponse Schema
    # 假设 AnswerResponse 是 Pydantic，我们需要修改它。
    # 让我先修改 schema 再提交这个代码。但为了原子性，我这里先把逻辑写好。
    # 由于 AnswerResponse 定义在 schemas/rag.py，我必须确保它有 session_id 字段。
    # 我会在下一步修改 Schema。这里先假设它有。
    result.session_id = session_id 
    return result


@router.post("/ask_stream")
async def ask_question_stream(
    request: QuestionRequest, 
    rag_service: RAGService = Depends(get_rag_service),
    db: AsyncSession = Depends(get_db)
):
    """流式提问接口"""
    chat_service = ChatService(db)
    
    # 1. 获取或创建会话
    session_id = request.session_id
    if not session_id:
        session = await chat_service.create_session(title=request.question[:20])
        session_id = session.id

    # 2. 保存用户消息
    await chat_service.add_message(
        session_id=session_id,
        role="user",
        content=request.question,
        image_url=request.image_name
    )

    question = rag_service.ask_with_image(request.question, request.image_name)
    
    # 获取历史记录
    history_dicts = []
    if session_id:
        history_msgs = await chat_service.get_history(session_id)
        for msg in history_msgs[-10:]:
            history_dicts.append({
                "role": msg.role,
                "content": msg.content
            })

    async def generate_stream():
        stream_generator = rag_service.ask_question(question, chat_history=history_dicts, stream=True)
        full_answer = ""
        documents = []
        
        # 发送 session_id 作为第一个事件，或者随 chunk 发送
        # 为了前端兼容，最好在第一个 chunk 或每个 chunk 带上 session_id
        yield f"data: {json.dumps({'session_id': session_id}, ensure_ascii=False)}\n\n"

        print(f"DEBUG: stream_generator type: {type(stream_generator)}")
        async for chunk in stream_generator:
            if chunk.get("answer"):
                full_answer += chunk["answer"]
            if chunk.get("documents"):
                documents = chunk["documents"]
            
            chunk['session_id'] = session_id
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        
        # 流结束，保存助手消息
        # 注意：这里需要创建一个新的 DB session，因为原来的可能已经关闭或不在此上下文
        try:
            from core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                stream_chat_service = ChatService(session)
                await stream_chat_service.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=full_answer,
                    meta_data={"documents": documents if documents else []}
                )
        except Exception as e:
            print(f"Failed to save stream message: {e}")

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/search", response_model=StandardResponse)
async def search_by_category(request: SearchRequest, rag_service: RAGService = Depends(get_rag_service)):
    """按分类搜索菜品"""
    dishes = rag_service.search_by_category(request.category, request.query)
    return StandardResponse(data={
        "category": request.category,
        "dishes": dishes
    })


@router.get("/categories", response_model=StandardResponse)
async def get_categories(rag_service: RAGService = Depends(get_rag_service)):
    """获取支持的分类列表"""
    categories = rag_service.get_categories()
    return StandardResponse(data=categories)


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
