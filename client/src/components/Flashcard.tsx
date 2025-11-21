import React from "react";
import { IFlashcard } from "../types";

interface FlashcardProps {
  data: IFlashcard;
  isFlipped: boolean;
  onFlip: () => void;
}

export const Flashcard: React.FC<FlashcardProps> = ({
  data,
  isFlipped,
  onFlip,
}) => {
  return (
    <div
      className="w-full max-w-2xl h-[400px] perspective-1000 cursor-pointer group"
      onClick={onFlip}
    >
      <div
        className={`relative w-full h-full duration-500 transform-style-3d transition-all ${
          isFlipped ? "rotate-y-180" : ""
        }`}
      >
        {/* Front */}
        <div className="absolute inset-0 backface-hidden bg-white rounded-2xl shadow-xl border border-slate-100 flex flex-col items-center justify-center p-12 text-center">
          <span className="absolute top-6 left-6 text-xs font-bold tracking-wider text-indigo-600 uppercase">
            Question
          </span>
          <h3 className="text-2xl font-medium text-slate-800">
            {data.question}
          </h3>
          <div className="absolute bottom-6 text-sm text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity">
            Click to flip
          </div>
        </div>

        {/* Back */}
        <div className="absolute inset-0 backface-hidden rotate-y-180 bg-indigo-50 rounded-2xl shadow-xl border border-indigo-100 flex flex-col items-center justify-center p-12 text-center">
          <span className="absolute top-6 left-6 text-xs font-bold tracking-wider text-indigo-600 uppercase">
            Answer
          </span>
          <p className="text-xl text-slate-700 leading-relaxed overflow-y-auto">
            {data.answer}
          </p>
        </div>
      </div>
    </div>
  );
};
