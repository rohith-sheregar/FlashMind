import React, { useState, useEffect } from "react";
import { RotateCw, Volume2 } from "lucide-react";
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
  const [isAnimating, setIsAnimating] = useState(false);
  const [cardHeight, setCardHeight] = useState('400px');

  // Dynamically adjust card height based on content
  useEffect(() => {
    const questionLength = data.question?.length || 0;
    const answerLength = data.answer?.length || 0;
    const maxLength = Math.max(questionLength, answerLength);
    
    if (maxLength > 200) {
      setCardHeight('500px');
    } else if (maxLength > 100) {
      setCardHeight('450px');
    } else {
      setCardHeight('400px');
    }
  }, [data]);

  const handleFlip = () => {
    setIsAnimating(true);
    onFlip();
    setTimeout(() => setIsAnimating(false), 300);
  };

  const speakText = (text: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.8;
      utterance.pitch = 1;
      speechSynthesis.speak(utterance);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        className="perspective-1000 cursor-pointer group"
        style={{ height: cardHeight }}
        onClick={handleFlip}
      >
        <div
          className={`relative w-full h-full duration-700 transform-style-3d transition-all ease-in-out ${
            isFlipped ? "rotate-y-180" : ""
          } ${isAnimating ? 'scale-105' : ''}`}
        >
          {/* Front - Question */}
          <div className="absolute inset-0 backface-hidden bg-gradient-to-br from-white to-gray-50 rounded-3xl shadow-2xl border border-gray-100 flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-100">
              <span className="text-xs font-bold tracking-wider text-indigo-600 uppercase bg-indigo-50 px-3 py-1 rounded-full">
                Question
              </span>
              <div className="flex items-center space-x-2">
                <button
                  onClick={(e) => speakText(data.question || '', e)}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors opacity-0 group-hover:opacity-100"
                >
                  <Volume2 className="w-4 h-4 text-gray-500" />
                </button>
                <RotateCw className="w-4 h-4 text-gray-400" />
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 flex items-center justify-center p-8">
              <h3 className="text-2xl md:text-3xl font-medium text-gray-800 leading-relaxed text-center">
                {data.question}
              </h3>
            </div>

            {/* Footer */}
            <div className="p-6 text-center">
              <div className="text-sm text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center space-x-2">
                <RotateCw className="w-4 h-4" />
                <span>Click to reveal answer</span>
              </div>
            </div>
          </div>

          {/* Back - Answer */}
          <div className="absolute inset-0 backface-hidden rotate-y-180 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-3xl shadow-2xl border border-indigo-400 flex flex-col text-white">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-indigo-400/30">
              <span className="text-xs font-bold tracking-wider text-indigo-100 uppercase bg-white/20 px-3 py-1 rounded-full">
                Answer
              </span>
              <div className="flex items-center space-x-2">
                <button
                  onClick={(e) => speakText(data.answer || '', e)}
                  className="p-2 hover:bg-white/10 rounded-full transition-colors opacity-0 group-hover:opacity-100"
                >
                  <Volume2 className="w-4 h-4 text-indigo-100" />
                </button>
                <RotateCw className="w-4 h-4 text-indigo-200" />
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 flex items-center justify-center p-8">
              <div className="max-h-full overflow-y-auto">
                <p className="text-xl md:text-2xl leading-relaxed text-center font-light">
                  {data.answer}
                </p>
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 text-center">
              <div className="text-sm text-indigo-200 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center space-x-2">
                <RotateCw className="w-4 h-4" />
                <span>Click to see question</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Card Info */}
      <div className="mt-4 text-center">
        <div className="inline-flex items-center space-x-4 text-sm text-gray-500">
          <div className="flex items-center space-x-1">
            <div className={`w-2 h-2 rounded-full ${isFlipped ? 'bg-purple-500' : 'bg-indigo-500'}`}></div>
            <span>{isFlipped ? 'Answer' : 'Question'}</span>
          </div>
          <div className="w-px h-4 bg-gray-300"></div>
          <span>Card {data.id}</span>
        </div>
      </div>
    </div>
  );
};
