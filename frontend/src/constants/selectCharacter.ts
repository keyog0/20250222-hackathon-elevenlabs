export const characterFullUrls = {
  KANG_LISA: "./assets/character/full/강리사_전신.png",
  KIM_JENNIE: "./assets/character/full/김제니_전신.png",
  LEE_JISOO: "./assets/character/full/이지수_전신.png",
  JUNG_ROSIE: "./assets/character/full/정로제_전신.png",
} as const;

export const characterInfo = {
  KANG_LISA: {
    name: "강리사",
    faster: 430,
    url: "./assets/character/full/강리사_전신.png",
  },
  KIM_JENNIE: {
    name: "김제니",
    faster: 600,
    url: "./assets/character/full/김제니_전신.png",
  },
  LEE_JISOO: {
    name: "이지수",
    faster: 500,
    url: "./assets/character/full/이지수_전신.png",
  },
  JUNG_ROSIE: {
    name: "정로제",
    faster: 530,
    url: "./assets/character/full/정로제_전신.png",
  },
};

export const manCharacterInfo = {
  A: {
    name: "남자A",
    faster: 430,
    url: "./assets/character/main/남자A.png",
  },
  B: {
    name: "남자B",
    faster: 600,
    url: "./assets/character/main/남자B.png",
  },
  C: {
    name: "남자C",
    faster: 500,
    url: "./assets/character/main/남자C.png",
  },
  D: {
    name: "남자D",
    faster: 530,
    url: "./assets/character/main/남자D.png",
  },
};

export type CharacterFullUrlType = keyof typeof characterFullUrls;
export type CharacterInfoType = keyof typeof characterInfo;

export type ManCharacterInfoType = keyof typeof manCharacterInfo;

export const characterNames = {
  KANG_LISA: "강리사",
  KIM_JENNIE: "김제니",
  LEE_JISOO: "이지수",
  JUNG_ROSIE: "정로제",
} as const;

export type CharacterNameType = keyof typeof characterNames;
