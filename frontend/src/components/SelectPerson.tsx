/* eslint-disable @next/next/no-img-element */
"use client";
import React, { useState } from "react";

type Props = {
  type: "main" | "sub";
  list: Record<string, { name: string; url: string; faster: number }>;
  onDisable?: () => void;
  onEnable?: () => void;
  onSelect?: (key: string) => void;
};

export const SelectPerson = ({ type, list, onDisable, onSelect }: Props) => {
  const [selected, setSelected] = useState<string | null>(null);

  const handleSelect = (key: string) => {
    console.log("캐릭터 선택 : ", key, selected);
    setSelected(key);
    onSelect?.(key);
    onDisable?.();
  };

  return (
    <div className="h-full w-full overflow-hidden absolute flex gap-10 inset-0 p-40 bg-black/40 z-[20]">
      {Object.entries(list)
        .sort((a, b) => a[1].faster - b[1].faster)
        .map(([key, user]) => (
          <div
            key={key}
            onClick={() => handleSelect(key)}
            className=" rounded-lg flex-1 cursor-pointer hover:bg-white/10 transition-all duration-200 ease-in-out hover:scale-[103%]"
          >
            <img
              src={user.url}
              alt={key}
              className="w-full h-full object-cover"
            />
            {type === "sub" && (
              <p className="text-white text-center text-2xl text-bold">
                {user.faster + " group"}
              </p>
            )}
          </div>
        ))}
    </div>
  );
};
