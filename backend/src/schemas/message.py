from datetime import UTC, datetime
from enum import Enum
import uuid
from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Any


class Sender(str, Enum):
    user = "user"
    agent = "agent"
    system = "system"


class MessageType(str, Enum):
    system = "system"
    text = "text"
    file = "file"


class EmotionState(BaseModel):
    """Detailed emotion state from agent"""
    joy: float = Field(default=0.0, ge=-1.0, le=1.0)
    trust: float = Field(default=0.0, ge=-1.0, le=1.0)
    fear: float = Field(default=0.0, ge=-1.0, le=1.0)
    surprise: float = Field(default=0.0, ge=-1.0, le=1.0)
    sadness: float = Field(default=0.0, ge=-1.0, le=1.0)
    disgust: float = Field(default=0.0, ge=-1.0, le=1.0)
    anger: float = Field(default=0.0, ge=-1.0, le=1.0)
    anticipation: float = Field(default=0.0, ge=-1.0, le=1.0)

    @classmethod
    def threshold_emotion(cls, value: float) -> float:
        """Apply threshold to emotion value"""
        if abs(value) < 0.1:  # 작은 변화는 무시
            return 0.0
        if value > 1.0:
            return 1.0
        if value < -1.0:
            return -1.0
        return value

    def __init__(self, **data):
        # Apply threshold to emotion values
        thresholded_data = {
            k: self.threshold_emotion(v) 
            for k, v in data.items()
        }
        super().__init__(**thresholded_data)


class Emotion(BaseModel):
    """Basic emotion info for display"""
    emotion: str
    likeability: float
    emotion_state: Optional[EmotionState] = None


class ScenarioInfo(BaseModel):
    """Current scenario information"""
    title: str
    description: str
    goals: List[str]
    current_progress: float = 0.0


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
    
    # Additional agent-specific fields
    scenario_info: Optional[ScenarioInfo] = None
    metadata: Optional[Dict[str, Any]] = None
    tips: Optional[str] = None  # Relationship tips
    requires_user_action: Optional[bool] = False  # For scenario transitions or important decisions

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message_id = str(uuid.uuid1())
        self.created_at = datetime.now(UTC).isoformat()
