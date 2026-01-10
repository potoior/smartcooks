import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from models.chat import ChatSession, ChatMessage

class ChatService:
    """聊天服务 - 处理会话和消息的持久化"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, title: str = "新对话") -> ChatSession:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        session = ChatSession(id=session_id, title=title)
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """获取会话详情"""
        result = await self.db.execute(select(ChatSession).where(ChatSession.id == session_id))
        return result.scalar_one_or_none()
    
    async def get_all_sessions(self) -> List[ChatSession]:
        """获取所有会话列表（按时间倒序）"""
        result = await self.db.execute(select(ChatSession).order_by(desc(ChatSession.updated_at)))
        return result.scalars().all()

    async def add_message(self, session_id: str, role: str, content: str, image_url: str = None, meta_data: dict = None) -> ChatMessage:
        """添加消息"""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            image_url=image_url,
            meta_data=meta_data
        )
        self.db.add(message)
        
        # 更新会话时间
        session = await self.get_session(session_id)
        if session:
            session.updated_at = func.now() # 使用数据库当前时间
            
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_history(self, session_id: str) -> List[ChatMessage]:
        """获取会话历史消息"""
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        )
        return result.scalars().all()
