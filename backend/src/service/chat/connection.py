# 채팅방 관리를 위한 클래스
from fastapi import WebSocket
from typing import Dict, List, Set
from datetime import datetime


class ConnectionManager:
    def __init__(self):
        # room_id를 키로 하고 WebSocket 연결 리스트를 값으로 가지는 딕셔너리
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.typing_users: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
            self.typing_users[room_id] = set()
        self.active_connections[room_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, room_id: str, user_id: str):
        if websocket in self.active_connections.get(room_id, []):
            self.active_connections[room_id].remove(websocket)
        if user_id in self.typing_users.get(room_id, set()):
            self.typing_users[room_id].remove(user_id)
        if room_id in self.active_connections and not self.active_connections[room_id]:
            del self.active_connections[room_id]
            del self.typing_users[room_id]

    async def broadcast(self, message: dict, room_id: str):
        if room_id in self.active_connections:
            # 리스트를 복사하여 순회함으로써 중간에 항목 제거가 안전하게 작동하도록 함
            for connection in self.active_connections[room_id][:]:
                try:
                    await connection.send_json(message)
                except RuntimeError as e:
                    # 연결이 이미 종료된 경우 해당 연결을 리스트에서 제거
                    print(f"WebSocket 연결 오류 발생: {e}")
                    self.active_connections[room_id].remove(connection)
