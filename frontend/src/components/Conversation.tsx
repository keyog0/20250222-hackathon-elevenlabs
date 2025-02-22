import React from "react";
import { TextAnimate } from "./magicui/text-animate";
import { ArrowTurnDownRightIcon } from "@heroicons/react/24/outline";
import { cn } from "@/lib/utils";
import { WebSocketMessage } from "@/hooks/useWebSocket";

type Props = {
  messages: WebSocketMessage[];
};
const Conversation = ({ messages }: Props) => {
  return (
    <div
      className={cn(
        "absolute bottom-10 left-0 right-0 flex flex-col gap-4 justify-center items-center px-4 sm:px-20"
      )}
    >
      <OtherConversation messages={messages} />
    </div>
  );
};

// ================================================

const OtherConversation = ({ messages }: Pick<Props, "messages">) => {
  return (
    <div className="min-h-[150px] p-4 border rounded bg-gray-50 text-black relative w-full text-xl">
      {messages[messages.length - 1] ? (
        <TextAnimate animation="blurInUp" by="character" once>
          {messages[messages.length - 1].content}
        </TextAnimate>
      ) : (
        "음성 입력을 시작하려면 버튼을 클릭하세요."
      )}
      <button
        className={cn(
          "absolute bottom-2 right-2 flex justify-center items-center size-6"
        )}
      >
        <ArrowTurnDownRightIcon className="size-4" />
      </button>
    </div>
  );
};

export default Conversation;
