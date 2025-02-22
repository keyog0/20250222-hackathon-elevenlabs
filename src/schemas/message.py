from typing import Optional, Dict, Any
from pydantic import BaseModel

class RoomMessage(BaseModel):
    """Message in a chat room"""
    type: MessageType
    content: str
    sender: str
    emotion: Optional[Emotion] = None
    audio_data: Optional[str] = None
    scenario_info: Optional[ScenarioInfo] = None
    tips: Optional[str] = None
    requires_user_action: bool = False
    metadata: Optional[Dict[str, Any]] = None 