export const backgroundAudioUrls = {
  CAFE: "./assets/audios/cafe.mp3",
  CAFE_2: "./assets/audios/cafe.mp3",
  DEPARTMENT_STORE: "./assets/audios/department_store.mp3",
  HOME: "./assets/audios/home.mp3",
  IZAKAYA: "./assets/audios/izakaya.mp3",
  MUSEUM: "./assets/audios/museum.mp3",
  MUSICAL_THEATER: "./assets/audios/musical_theater.mp3",
  PARK_2: "./assets/audios/park_2.mp3",
  PUB: "./assets/audios/pub.mp3",
  RUNNING_PARK: "./assets/audios/running_park.mp3",
  WEDDING_HALL: "./assets/audios/wedding_hall.mp3",
} as const;

export type BackgroundAudioUrlType = keyof typeof backgroundAudioUrls;
