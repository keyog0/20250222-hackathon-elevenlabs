"use client";
import React from "react";

import { TextAnimate } from "./magicui/text-animate";

import { memo } from "react";

type MyConversationProps = {
  transcript: string;
  extraButton?: React.ReactNode;
};

export const MyConversation = memo(
  ({ transcript, extraButton }: MyConversationProps) => {
    return (
      <>
        <div className="min-h-[100px] p-4 rounded-lg bg-gray-500/40 text-white relative w-full flex items-center justify-center text-xl">
          <TextAnimate animation="blurInUp" by="character" once>
            {transcript || "...."}
          </TextAnimate>
          {extraButton}
        </div>
      </>
    );
  }
);

MyConversation.displayName = "MyConversation";
