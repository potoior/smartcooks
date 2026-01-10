from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class ChatSessionResponse(BaseModel):
    """会话响应模型"""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

class ChatMessageResponse(BaseModel):
    """消息响应模型"""
    id: int
    role: str
    content: str
    image_url: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
    created_at: datetime

class SessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: List[ChatSessionResponse]
    total: int

class HistoryResponse(BaseModel):
    """历史记录响应"""
    messages: List[ChatMessageResponse]
