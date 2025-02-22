from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from src.core.database import get_session
from src.service.chat.agent import AgentService

agent_router = APIRouter(prefix="/chat/agent")


@agent_router.post("/{room_id}/messages")
async def send_message(room_id: str, message: str, db: Session = Depends(get_session)):
    agent_service = AgentService(db)
    messages = await agent_service.get_agent_response(room_id, message)
    return messages


@agent_router.post("/{room_id}/upload")
async def upload_file(room_id: str, file: UploadFile = File(...), db: Session = Depends(get_session)):
    agent_service = AgentService(db)
    file_url = await agent_service.save_file(file, room_id)
    return {"file_url": file_url}
