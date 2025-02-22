"use client";
import React, { useEffect, useState, useRef } from "react";
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
import Image from "next/image";
import { memo } from "react";
import { backgroundUrls } from "@/constants/bg";
import { backgroundAudioUrls } from "@/constants/audios";

const assetsByStep = {
  0: {
    bg: backgroundUrls.RUNNING_PARK,
    audio: backgroundAudioUrls.RUNNING_PARK,
  },
  1: {
    bg: backgroundUrls.PUB,
    audio: backgroundAudioUrls.PUB,
  },
} as Record<number, { bg: string; audio: string }>;

type Props = {
  step: number;
  onNextScene: () => void;
  selectedCharacter: string;
};

const feelingImages = {
  1: "/assets/character/김제니_기본_정방형.png",
  2: "/assets/character/김제니_기본_패션.png",
  3: "/assets/character/김제니_무뚝뚝_패션.png",
  4: "/assets/character/김제니_무뚝뚝.png",
  5: "/assets/character/김제니_웃음.png",
  6: "/assets/character/김제니_웃음_패션.png",
  7: "/assets/character/김제니_화남_패션.png",
  8: "/assets/character/김제니_화남.png",
};

const BgAudio = ({ url }: { url: string }) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [audioUrl, setAudioUrl] = useState(() => url);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.load();
      audioRef.current.play();
    }
    setAudioUrl(url);
  }, [url]);

  return (
    <audio ref={audioRef} autoPlay loop>
      <source src={audioUrl} type="audio/mp3" />
    </audio>
  );
};

export const STT = ({ step, selectedCharacter }: Props) => {
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
  const [isCharacterVisible, setIsCharacterVisible] = useState(false);

  const agentChats = messages.filter((i) => i.sender === "agent");

  const a = () => {
    // onNextScene();
    sendMessage("speaking", "안녕하세요");
    sendMessage("text", "");
  };

  useEffect(() => {
    if (selectedCharacter) {
      setIsCharacterVisible(true);
    } else {
      setIsCharacterVisible(false);
    }
  }, [selectedCharacter]);

  return (
    <div
      className="min-h-screen w-full relative"
      style={{
        backgroundImage: `url(${assetsByStep[step].bg})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
        backgroundColor: "rgba(0, 0, 0, 0.5)",
        backgroundBlendMode: "overlay",
      }}
    >
      <BgAudio url={assetsByStep[step].audio} />
      {agentChats?.[agentChats.length - 1]?.audio_data && (
        <audio controls autoPlay>
          <source
            src={
              "data:audio/wav;base64," +
              (agentChats?.[agentChats.length - 1]?.audio_data ?? "").replace(
                /^\/\//,
                ""
              )
            }
            type="audio/wav"
          />
          Your browser does not support the audio element.
        </audio>
      )}

      {selectedCharacter && (
        <>
          <div className="absolute top-4 right-4 bg-white rounded-full p-4">
            <Likeability
              value={
                agentChats?.[agentChats.length - 1]?.emotion.likeability ?? 0
              }
            />
          </div>
          <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-1/2 z-10">
            <div className="flex flex-col items-center justify-center w-full gap-4">
              <MyConversation
                transcript={transcript}
                isConnected={isConnected}
                handleClearTranscript={handleClearTranscript}
              />
              <Mic
                isListening={isListening}
                handleStartListening={handleStartListening}
                handleStopListening={handleStopListening}
              />
              {/* <button onClick={() => a()}>
                {isCharacterVisible ? "off" : "on"}
              </button> */}
            </div>
          </div>
        </>
      )}
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
      {selectedCharacter && (
        <div
          className={cn(
            "pointer-events-none select-none aspect-square absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[1000px] transition-all duration-500",
            {
              "opacity-0": isCharacterVisible,
              "opacity-100": !isCharacterVisible,
            }
          )}
        >
          <Image
            src="/assets/character/김제니_기본_정방형.png"
            alt=""
            width={1200}
            height={1200}
            className="w-full"
          />
        </div>
      )}

      <div
        className={cn(
          "pointer-events-none select-none aspect-square absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[1000px] transition-all duration-500",
          {
            "opacity-0": !isCharacterVisible,
            "opacity-100": isCharacterVisible,
          }
        )}
      >
        <Image
          src="/assets/character/김제니_웃음.png"
          alt=""
          width={1200}
          height={1200}
          className="w-full"
        />
      </div>
      {selectedCharacter && (
        <Conversation messages={messages.filter((i) => i.sender === "agent")} />
      )}
      {/* <WebSocketStatus
        isConnected={isConnected}
        messages={messages}
        wsError={wsError}
      /> */}
    </div>
  );
};

// ================================================

type MicProps = {
  isListening: boolean;
  handleStartListening: () => void;
  handleStopListening: () => void;
};

const Mic = memo(
  ({ isListening, handleStartListening, handleStopListening }: MicProps) => {
    return (
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
    );
  }
);

Mic.displayName = "Mic";

// ================================================

type MyConversationProps = {
  transcript: string;
  isConnected: boolean;
  handleClearTranscript: () => void;
};

const MyConversation = memo(
  ({ transcript, isConnected, handleClearTranscript }: MyConversationProps) => {
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
  }
);

MyConversation.displayName = "MyConversation";
