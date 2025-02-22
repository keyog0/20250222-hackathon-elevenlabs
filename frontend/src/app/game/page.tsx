"use client";
import { SelectPerson, STT } from "@/components";
import { MyConversation } from "@/components/MyConversation";
import { characterInfo, manCharacterInfo } from "@/constants/selectCharacter";
import { useEffect, useState } from "react";
import { monologue } from "@/constants/monologue";

const monologue1 = monologue[1];

export default function Home() {
  const [selectedCharacter, setSelectedCharacter] = useState("");
  const [selectMainCharacter, setSelectMainCharacter] = useState(true);
  const [showSelectPerson, setShowSelectPerson] = useState(false);
  const [showMyConversation, setShowMyConversation] = useState(false);
  const [scene, setScene] = useState(-1);
  const [monologueStep, setMonologueStep] = useState(0);

  const nextScene = () => {
    setScene((p) => p + 1);
  };

  const handleSelectCharacter = (character: string) => {
    setSelectedCharacter(character);
  };

  const handleDisableMainCharacter = () => {
    setSelectMainCharacter(false);
    setShowMyConversation(true);
    setScene(0);
  };

  const handleEnableMainCharacter = () => {
    setSelectMainCharacter(true);
  };

  const handleNextMonologueStep = () => {
    setMonologueStep((p) => p + 1);
  };

  const handleDisableSelectPerson = () => {
    setShowSelectPerson(false);
    handleNextMonologueStep();
  };

  const handleEnableSelectPerson = () => {
    setShowSelectPerson(true);
  };

  useEffect(() => {
    if (monologueStep === 2) {
      handleEnableSelectPerson();
    }
  }, [monologueStep]);

  return (
    <main className="flex min-h-screen flex-col items-center justify-between bg-white">
      <div className="z-10 w-full items-center justify-between font-mono text-sm">
        {/* <h1 className="text-4xl font-bold mb-8 text-center">Test</h1> */}
        {scene >= 0 && (
          <STT
            step={scene}
            onNextScene={nextScene}
            selectedCharacter={selectedCharacter}
          />
        )}
        {showSelectPerson && (
          <SelectPerson
            type="sub"
            list={characterInfo}
            onDisable={handleDisableSelectPerson}
            onEnable={handleEnableSelectPerson}
            onSelect={handleSelectCharacter}
          />
        )}
        {selectMainCharacter && (
          <SelectPerson
            type="main"
            list={manCharacterInfo}
            onDisable={handleDisableMainCharacter}
            onEnable={handleEnableMainCharacter}
          />
        )}
      </div>
      {showMyConversation && (
        <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-1/2 z-10">
          <div className="flex flex-col items-center justify-center w-full gap-4">
            <MyConversation
              transcript={monologue1[monologueStep]}
              extraButton={
                <button
                  className="absolute bottom-2 right-2 w-40 h-12 rounded-lg bg-blue-500 text-white"
                  onClick={() => {
                    handleEnableSelectPerson();
                    setShowMyConversation(false);
                  }}
                >
                  캐릭터 선택
                </button>
              }
            />
          </div>
        </div>
      )}
    </main>
  );
}
