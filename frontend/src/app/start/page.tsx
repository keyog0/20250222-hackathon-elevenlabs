"use client";

import { useRouter } from "next/navigation";

export default function StartPage() {
  const router = useRouter();

  const goToGame = () => {
    router.push("/game");
  };

  return (
    <div className="flex flex-col gap-4 items-center justify-between h-screen py-40">
      <h1 className="text-4xl font-bold mb-8 text-center">TEST</h1>

      <div className="flex flex-col gap-4 items-center">
        <button
          className="w-40 h-12 rounded-lg bg-blue-500 text-white"
          onClick={goToGame}
        >
          게임시작
        </button>
        <button className="w-40 h-12 rounded-lg bg-blue-500 text-white">
          이어하기
        </button>
        <button className="w-40 h-12 rounded-lg bg-blue-500 text-white">
          설정
        </button>
        <button className="w-40 h-12 rounded-lg bg-blue-500 text-white">
          종료
        </button>
      </div>
    </div>
  );
}
