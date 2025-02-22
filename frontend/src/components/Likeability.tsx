"use client";

import { useEffect, useState } from "react";
import { AnimatedCircularProgressBar } from "./magicui/animated-circular-progress-bar";

type Props = {
  value: number;
};

export function Likeability({ value: propsValue }: Props) {
  const [value, setValue] = useState(() => propsValue);

  useEffect(() => {
    setValue(propsValue);
  }, [propsValue]);

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
