from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import json


from src.service.chat.agent import AgentService
from src.schemas.message import MessageType, RoomMessage
from src.service.chat.connection import ConnectionManager
from src.core.database import get_session

websocket_router = APIRouter(prefix="/chat/room")

manager = ConnectionManager()


@websocket_router.websocket("")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_session)):
    room_id = "123"
    user_id = "456"

    agent_service = AgentService(db)
    try:
        await manager.connect(websocket, room_id)
        await manager.broadcast(
            RoomMessage(
                type=MessageType.system,
                content=f"{user_id}님이 입장하셨습니다.",
                sender="system",
            ).model_dump(),
            room_id,
        )

        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message = RoomMessage(**message_data)

            if message.type in [MessageType.text, MessageType.file]:
                # 브로드캐스트
                await manager.broadcast(
                    RoomMessage(
                        type=message.type,
                        content=message.content,
                        file_url=message.file_url,
                        sender="user",
                    ).model_dump(),
                    room_id,
                )

                if message.is_speaking:
                    continue
                else:
                    agent_response = await agent_service.get_agent_response(message)
                    await manager.broadcast(agent_response.model_dump(), room_id)

    except WebSocketDisconnect:
        await manager.broadcast(
            RoomMessage(
                type=MessageType.system,
                content=f"{user_id}님이 퇴장하셨습니다.",
                sender="system",
            ).model_dump(),
            room_id,
        )
        await manager.disconnect(websocket, room_id, user_id)
