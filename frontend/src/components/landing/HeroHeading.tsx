import React from "react";
import { Cover } from "../ui/cover";

export default function HeroHeading() {
  return (
    <section className="text-center px-4">
      <h2 className="text-2xl md:text-4xl lg:text-6xl font-bold max-w-4xl mx-auto mt-6 relative z-20 py-4">
        Your World, <Cover>Reimagined</Cover>
      </h2>
      <p className="text-base md:text-lg font-normal text-neutral-700 dark:text-neutral-200 max-w-2xl mx-auto leading-relaxed">
        Orbitix transforms your travel dreams into unforgettable journeys. 
        Plan, explore, and navigate with an AI-powered guide that anticipates 
        every detail — so you can focus on the adventure.
      </p>
    </section>
  );
}
