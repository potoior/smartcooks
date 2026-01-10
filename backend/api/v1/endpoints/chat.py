from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from core.database import get_db
from services.chat_service import ChatService
from schemas.chat import SessionListResponse, ChatSessionResponse, ChatMessageResponse, HistoryResponse
from schemas.common import StandardResponse

router = APIRouter()

@router.get("/sessions", response_model=StandardResponse[SessionListResponse])
async def get_sessions(db: AsyncSession = Depends(get_db)):
    """获取会话列表"""
    chat_service = ChatService(db)
    sessions = await chat_service.get_all_sessions()
    
    # 转换为响应模型
    session_responses = [
        ChatSessionResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at
        ) for s in sessions
    ]
    
    return StandardResponse(data=SessionListResponse(
        sessions=session_responses,
        total=len(sessions)
    ))

@router.get("/sessions/{session_id}/messages", response_model=StandardResponse[HistoryResponse])
async def get_session_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    """获取会话消息历史"""
    chat_service = ChatService(db)
    messages = await chat_service.get_history(session_id)
    
    if not messages and not await chat_service.get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
        
    message_responses = [
        ChatMessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            image_url=m.image_url,
            meta_data=m.meta_data if m.meta_data else None,
            created_at=m.created_at
        ) for m in messages
    ]
    
    return StandardResponse(data=HistoryResponse(messages=message_responses))

@router.delete("/sessions/{session_id}", response_model=StandardResponse)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """删除会话 (暂未实现完全删除逻辑，仅示例)"""
    # 实际项目中需要在 ChatService 添加 delete_session 方法
    # 目前简单返回成功
    return StandardResponse(message="Session deleted (mock)")
