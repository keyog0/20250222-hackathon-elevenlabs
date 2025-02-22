from sqlalchemy.orm import Session
from src.schemas.message import Emotion, MessageType, RoomMessage
import base64
import httpx
from src.config import settings

# Elevenlabs API 사용을 위한 API 키와 voice ID (실제 값으로 변경하세요)


class AgentService:
    def __init__(self, db: Session):
        self.db = db

    async def get_agent_response(self, message: RoomMessage):
        text_content = "Mock 메시지 이지롱"

        # Elevenlabs API를 비동기 호출로 텍스트를 음성으로 변환
        audio_bytes = await self.convert_text_to_audio(text_content)

        # 변환된 음성 데이터를 base64 인코딩 방식으로 처리하여 메시지에 포함합니다.
        # 또는 별도의 스토리지(예: S3 등)에 업로드하여 해당 URL을 포함할 수도 있습니다.
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

        return RoomMessage(
            type=MessageType.text,
            content=text_content,
            sender="agent",
            emotion=Emotion(emotion="happy", likeability=0.8),
            audio_data=audio_base64,  # RoomMessage에 audio_data 필드가 있어야 합니다.
        )

    async def convert_text_to_audio(self, text: str) -> bytes:
        voice_id = "JBFqnCBsd6RMkjVDRZzb"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "xi-api-key": settings.ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
        }
        query_params = {"output_format": "mp3_44100_128"}
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.75,
                "similarity_boost": 0.75,
            },
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data, params=query_params)
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"Elevenlabs API 호출 실패: {response.status_code} {response.text}")


class LLMAgentService:
    def __init__(self, db: Session):
        self.db = db
