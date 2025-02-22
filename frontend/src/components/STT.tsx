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

import Conversation from "./Conversation";
import { TextAnimate } from "./magicui/text-animate";
import { cn } from "@/lib/utils";
import { Likeability } from "./Likeability";

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

  return (
    <div
      className="min-h-screen w-full relative"
      style={{
        backgroundImage:
          "url('https://images.unsplash.com/photo-1511497584788-876760111969?q=80&w=3732&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D')",
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
        backgroundColor: "rgba(0, 0, 0, 0.5)",
        backgroundBlendMode: "overlay",
      }}
    >
      <div className="absolute top-4 right-4 bg-white rounded-full p-4">
        <Likeability />
      </div>
      <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-1/2">
        <div className="flex flex-col items-center justify-center w-full gap-4">
          <MyConversation
            transcript={transcript}
            isConnected={isConnected}
            handleClearTranscript={handleClearTranscript}
          />
          <PulsatingButton
            className="absolute right-3 bottom-3 flex justify-center items-center p-2 bg-pink-600"
            pulseColor={isListening ? "#fff" : "#ff0096"}
            onClick={isListening ? handleStopListening : handleStartListening}
          >
            {isListening ? (
              <EllipsisHorizontalCircleIcon className="size-4" />
            ) : (
              <MicrophoneIcon className="size-4" />
            )}
          </PulsatingButton>
        </div>
      </div>
      <div className="gap-4 hidden">
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
      <Conversation messages={messages.filter((i) => i.sender === "agent")} />
      <WebSocketStatus
        isConnected={isConnected}
        messages={messages}
        wsError={wsError}
      />
    </div>
  );
};

type MyConversationProps = {
  transcript: string;
  isConnected: boolean;
  handleClearTranscript: () => void;
};

// ================================================

const MyConversation = ({
  transcript,
  isConnected,
  handleClearTranscript,
}: MyConversationProps) => {
  return (
    <>
      <div className="min-h-[100px] p-4 rounded-lg bg-gray-500/40 text-white relative w-full flex items-center justify-center text-xl">
        <TextAnimate animation="blurInUp" by="character" once>
          {transcript || "...."}
        </TextAnimate>
        <button
          disabled={!isConnected || !transcript}
          onClick={handleClearTranscript}
          className={cn(
            "absolute bottom-2 right-2 flex justify-center items-center size-6 bg-gray-500 text-white rounded-full ",
            !isConnected || !transcript ? "opacity-50" : "hover:bg-gray-600"
          )}
        >
          <XCircleIcon className="size-4" />
        </button>
      </div>
    </>
  );
};
