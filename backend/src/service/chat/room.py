from datetime import UTC, datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile
import aiofiles
import os

from src.core.models.chat import ChatMessage


class ChatMessageService:
    def __init__(self, db: Session):
        self.db = db

    async def save_message(
        self, room_id: str, user_id: str, content: str, message_type: str = "text", file_url: Optional[str] = None
    ) -> ChatMessage:
        message = ChatMessage(
            room_id=room_id, user_id=user_id, content=content, message_type=message_type, file_url=file_url
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    async def get_message_history(self, room_id: str, limit: int = 50) -> List[ChatMessage]:
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.room_id == room_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )

    async def save_file(self, file: UploadFile, room_id: str) -> str:
        file_path = f"uploads/chat/{room_id}/{file.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        async with aiofiles.open(file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)

        return f"/files/{file_path}"
