"use client";

import { useEffect, useState } from "react";
import { AnimatedCircularProgressBar } from "./magicui/animated-circular-progress-bar";

export function Likeability() {
  const [value, setValue] = useState(0);

  useEffect(() => {
    const handleIncrement = (prev: number) => {
      if (prev === 100) {
        return 0;
      }
      return prev + 10;
    };
    setValue(handleIncrement);
    const interval = setInterval(() => setValue(handleIncrement), 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <AnimatedCircularProgressBar
      centerContent={"😍"}
      className="size-20"
      max={100}
      min={0}
      value={value}
      gaugePrimaryColor="pink"
      gaugeSecondaryColor="rgba(0, 0, 0, 0.1)"
    />
  );
}
