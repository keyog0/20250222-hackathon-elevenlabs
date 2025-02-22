import { useEffect, useRef, useState, useCallback } from "react";

// MessageType 유니온 타입
export type MessageType = "system" | "speaking" | "text" | "file";

// WebSocket 메시지 타입 정의
export interface WebSocketMessage {
  type: MessageType;
  content: string;
  created_at?: string;
  is_speaking: boolean;
  file_url?: string;
  message_id?: string;
  sender: "agent" | "user" | "system";
}

// WebSocket 훅의 반환 타입
interface UseWebSocketReturn {
  sendMessage: (type: MessageType, content: string) => void;
  messages: WebSocketMessage[];
  isConnected: boolean;
  error: string | null;
}

// WebSocket 커스텀 훅
export const useWebSocket = (url: string): UseWebSocketReturn => {
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    // WebSocket 연결 초기화
    ws.current = new WebSocket(url);

    // 연결 이벤트 핸들러
    ws.current.onopen = () => {
      setIsConnected(true);
      setError(null);
      console.log("WebSocket 연결됨");
    };

    // 메시지 수신 핸들러
    ws.current.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        if (message.sender === "user") return;
        setMessages((prev) => [...prev, message]);
        console.log("메시지 수신:", message);
      } catch (err) {
        setError("메시지 파싱 오류");
        console.error("메시지 파싱 오류:", err);
      }
    };

    // 에러 핸들러
    ws.current.onerror = (event) => {
      setError("WebSocket 연결 오류");
      setIsConnected(false);
      console.error("WebSocket 오류:", event);
    };

    // 연결 종료 핸들러
    ws.current.onclose = () => {
      setIsConnected(false);
      console.log("WebSocket 연결 종료");
    };

    // 컴포넌트 언마운트 시 연결 정리
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [url]);

  // 메시지 전송 함수
  const sendMessage = useCallback((type: MessageType, content: string) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      const message: WebSocketMessage = {
        is_speaking: type === "speaking",
        type: type === "speaking" ? "text" : type,
        content,
        sender: "user",
      };
      ws.current.send(JSON.stringify(message));
      console.log("메시지 전송:", message);
    } else {
      setError("WebSocket이 연결되어 있지 않습니다.");
      console.error("WebSocket 연결되지 않음");
    }
  }, []);

  return { sendMessage, messages, isConnected, error };
};
