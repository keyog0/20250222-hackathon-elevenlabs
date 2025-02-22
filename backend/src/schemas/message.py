from datetime import UTC, datetime
from enum import Enum
import uuid
from pydantic import BaseModel, Field


class Sender(str, Enum):
    user = "user"
    agent = "agent"
    system = "system"


class MessageType(str, Enum):
    system = "system"
    text = "text"
    file = "file"


class Emotion(BaseModel):
    emotion: str
    likeability: float


class RoomMessage(BaseModel):
    message_id: str = Field(default=str(uuid.uuid1()))
    type: MessageType
    is_speaking: bool | None = Field(default=None)
    content: str = Field(default="")
    sender: Sender = Field(default=Sender.user)
    file_url: str | None = Field(default=None)
    audio_data: str | None = Field(default=None)
    emotion: Emotion | None = Field(default=None)
    created_at: str = Field(default=datetime.now(UTC).isoformat())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message_id = str(uuid.uuid1())
        self.created_at = datetime.now(UTC).isoformat()
