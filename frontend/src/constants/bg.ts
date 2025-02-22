export const backgroundUrls = {
  CAFE: "./assets/bg/cafe.png",
  CAFE_2: "./assets/bg/cafe_2.png",
  DEPARTMENT_STORE: "./assets/bg/department_store.png",
  HOME: "./assets/bg/home.png",
  IZAKAYA: "./assets/bg/izakaya.png",
  MUSEUM: "./assets/bg/museum.png",
  MUSICAL_THEATER: "./assets/bg/musical_theater.png",
  PARK_2: "./assets/bg/park_2.png",
  PUB: "./assets/bg/pub.png",
  RUNNING_PARK: "./assets/bg/running_park.png",
  WEDDING_HALL: "./assets/bg/wedding_hall.png",
} as const;

export const backgroundLabel = {
  CAFE: "카페",
  CAFE_2: "카페2",
  DEPARTMENT_STORE: "백화점",
  HOME: "집",
  IZAKAYA: "이자카야",
  MUSEUM: "미술관",
  MUSICAL_THEATER: "뮤지컬",
  PARK_2: "파크2",
  PUB: "펍",
  RUNNING_PARK: "한강공원",
  WEDDING_HALL: "결혼식장",
};
export type BackgroundUrlType = keyof typeof backgroundUrls;
