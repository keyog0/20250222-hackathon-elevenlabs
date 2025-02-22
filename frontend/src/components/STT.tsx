"use client";
import React, { useState, useRef, useEffect } from "react";
import { useWebSocket } from "../utils/websocket";

// SpeechRecognition 타입 정의
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResultList {
  readonly length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  readonly length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface ISpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  abort(): void;
  start(): void;
  stop(): void;
  onresult: (event: SpeechRecognitionEvent) => void;
  onstart: () => void;
  onend: () => void;
  onerror: (event: Event) => void;
}

declare global {
  interface Window {
    SpeechRecognition: new () => ISpeechRecognition;
    webkitSpeechRecognition: new () => ISpeechRecognition;
  }
}

export const STT = () => {
  const [transcript, setTranscript] = useState<string>("");
  const [isListening, setIsListening] = useState<boolean>(false);
  const [selectedLanguage, setSelectedLanguage] = useState<string>("ko-KR");
  const recognitionRef = useRef<ISpeechRecognition | null>(null);

  // WebSocket 연결
  const {
    sendMessage,
    messages,
    isConnected,
    error: wsError,
  } = useWebSocket(process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws");

  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.error("이 브라우저는 음성 인식을 지원하지 않습니다.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = selectedLanguage;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const transcript = event.results[0][0].transcript;
      setTranscript((prev) => prev + " " + transcript);

      // WebSocket을 통해 서버로 음성 인식 결과 전송
      if (isConnected) {
        sendMessage(transcript);
      }
    };

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.abort();
    };
  }, [selectedLanguage, isConnected, sendMessage]);

  const handleStartListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.start();
    }
  };

  const handleClearTranscript = () => {
    setTranscript("");
  };

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedLanguage(e.target.value);
  };

  return (
    <div className="flex flex-col gap-4 p-4">
      <div className="flex gap-4">
        <button
          onClick={handleStartListening}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          {isListening ? "듣는 중..." : "음성 입력 시작"}
        </button>
        <button
          onClick={handleClearTranscript}
          className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
        >
          지우기
        </button>
        <select
          value={selectedLanguage}
          onChange={handleLanguageChange}
          className="px-4 py-2 border rounded"
        >
          <option value="ko-KR">한국어</option>
          <option value="en-US">English</option>
          <option value="ja-JP">日本語</option>
          <option value="zh-CN">中文(简体)</option>
        </select>
      </div>
      <div className="min-h-[100px] p-4 border rounded bg-gray-50 text-black">
        {transcript || "음성 입력을 시작하려면 버튼을 클릭하세요."}
      </div>
      {/* WebSocket 상태 표시 */}
      <div className="text-sm">
        <p className={isConnected ? "text-green-600" : "text-red-600"}>
          {isConnected ? "서버 연결됨" : "서버 연결 안됨"}
        </p>
        {wsError && <p className="text-red-600">에러: {wsError}</p>}
      </div>
      {/* 서버로부터 받은 메시지 표시 */}
      <div className="mt-4">
        <h3 className="font-bold mb-2 ">서버 응답:</h3>
        <div className="max-h-40 overflow-y-auto">
          {messages.map((msg, index) => (
            <div key={index} className="p-2 bg-gray-100 rounded mb-2">
              <p className="text-black">{msg.content}</p>
              <small className="text-gray-500">
                {new Date(msg.timestamp).toLocaleString()}
              </small>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
