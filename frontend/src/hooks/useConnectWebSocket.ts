import { useCallback, useEffect, useRef, useState } from "react";
import { MessageType } from "./useWebSocket";

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

type UseConnectWebSocketProps = {
  sendMessage: (type: MessageType, content: string) => void;

  isConnected: boolean;
};

export const useConnectWebSocket = ({
  sendMessage,
  isConnected,
}: UseConnectWebSocketProps) => {
  const [transcript, setTranscript] = useState<string>("");
  const [isListening, setIsListening] = useState<boolean>(false);
  const [selectedLanguage, setSelectedLanguage] = useState<string>("ko-KR");
  const recognitionRef = useRef<ISpeechRecognition | null>(null);

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
        sendMessage("speaking", transcript);
      }
    };

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onend = () => {
      setIsListening(false);
      sendMessage("text", "");
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

  const handleStopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.abort();
    }
  };

  const handleClearTranscript = useCallback(() => {
    setTranscript("");
  }, []);

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedLanguage(e.target.value);
  };

  return {
    transcript,
    isListening,
    selectedLanguage,
    setSelectedLanguage,
    handleStartListening,
    handleClearTranscript,
    handleLanguageChange,
    handleStopListening,
  };
};
