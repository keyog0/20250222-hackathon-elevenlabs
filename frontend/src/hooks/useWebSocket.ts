import { useEffect, useRef, useState, useCallback } from "react";

// MessageType 유니온 타입
export type MessageType = "system" | "speaking" | "text" | "file";

// EmotionState 인터페이스
interface EmotionState {
  anger: number;
  anticipation: number;
  disgust: number;
  fear: number;
  joy: number;
  sadness: number;
  surprise: number;
  trust: number;
}

// Emotion 인터페이스
interface Emotion {
  emotion: string;
  emotion_state: EmotionState;
  likeability: number;
}

// ScenarioInfo 인터페이스
interface ScenarioInfo {
  current_progress: number;
  description: string;
  goals: string[];
  title: string;
}

// WebSocket 메시지 타입 정의
export interface WebSocketMessage {
  audio_data: string | null;
  content: string;
  created_at: string;
  emotion: Emotion;
  file_url: string | null;
  is_speaking: boolean | null;
  message_id: string;
  metadata: string | null;
  requires_user_action: boolean;
  scenario_info: ScenarioInfo;
  sender: "agent" | "user";
  tips: string | null;
  type: "text" | string;
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
      const message: Partial<WebSocketMessage> = {
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
