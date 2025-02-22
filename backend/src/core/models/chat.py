from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship

from src.core.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String, index=True)
    user_id = Column(String, index=True)
    content = Column(String)
    message_type = Column(String)  # 'text', 'file'
    file_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
