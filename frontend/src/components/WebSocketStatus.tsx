import { WebSocketMessage } from "@/hooks/useWebSocket";

type WebSocketMessageProps = {
  isConnected: boolean;
  messages: WebSocketMessage[];
  wsError: string | null;
};

export const WebSocketStatus = ({
  isConnected,
  messages,
  wsError,
}: WebSocketMessageProps) => {
  return (
    <div className="p-4 bg-black/10 fixed top-4 left-4 rounded-lg min-w-[200px]">
      <div className="text-sm">
        <div
          className={`size-2 rounded-full ${
            isConnected ? "bg-green-600" : "bg-red-600"
          }`}
        />
        {wsError && <p className="text-red-600">에러: {wsError}</p>}
      </div>
      <div className="mt-4">
        <h3 className="font-bold mb-2 ">서버 응답:</h3>
        <div className="max-h-40 overflow-y-auto">
          {messages.map((msg, index) => (
            <div key={index} className="p-2 bg-gray-100 rounded mb-2">
              <p className="text-black">{msg.content}</p>
              <small className="text-gray-500">
                {new Date(msg.created_at).toLocaleString()}
              </small>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
