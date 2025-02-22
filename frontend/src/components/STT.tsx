"use client";
import React from "react";
import {
  EllipsisHorizontalCircleIcon,
  MicrophoneIcon,
  XCircleIcon,
} from "@heroicons/react/24/outline";
import { PulsatingButton } from "./magicui/pulsating-button";
import { useConnectWebSocket, useWebSocket } from "@/hooks";
import { WebSocketStatus } from "./WebSocketStatus";

export const STT = () => {
  const {
    sendMessage,
    messages,
    isConnected,
    error: wsError,
  } = useWebSocket(process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws");

  const {
    transcript,
    isListening,
    selectedLanguage,
    handleStartListening,
    handleClearTranscript,
    handleLanguageChange,
    handleStopListening,
  } = useConnectWebSocket({
    sendMessage,
    isConnected,
  });

  const RemoveButton = () => (
    <button
      onClick={handleClearTranscript}
      className="absolute bottom-2 right-2 flex justify-center items-center size-6 bg-gray-500 text-white rounded-full hover:bg-gray-600"
    >
      <XCircleIcon className="size-4" />
    </button>
  );

  return (
    <div className="flex flex-col gap-4 p-4">
      <div className="flex justify-center items-center">
        <PulsatingButton
          className="flex justify-center items-center p-2 bg-pink-600"
          pulseColor={isListening ? "#fff" : "#ff0096"}
          onClick={isListening ? handleStopListening : handleStartListening}
        >
          {isListening ? (
            <EllipsisHorizontalCircleIcon className="size-6" />
          ) : (
            <MicrophoneIcon className="size-6" />
          )}
        </PulsatingButton>
      </div>
      <div className="flex gap-4">
        <select
          value={selectedLanguage}
          onChange={handleLanguageChange}
          className="px-4 py-2 border rounded bg-white"
        >
          <option value="ko-KR">한국어</option>
          <option value="en-US">English</option>
          <option value="ja-JP">日本語</option>
          <option value="zh-CN">中文(简体)</option>
        </select>
      </div>
      <div className="min-h-[100px] p-4 border rounded bg-gray-50 text-black relative">
        {transcript || "음성 입력을 시작하려면 버튼을 클릭하세요."}
        <RemoveButton />
      </div>
      <WebSocketStatus
        isConnected={isConnected}
        messages={messages}
        wsError={wsError}
      />
    </div>
  );
};
