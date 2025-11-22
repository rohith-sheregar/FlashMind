import React, { useState, useEffect, useRef } from 'react';
import { Flashcard } from '../types';
import FlipCard from './FlipCard'; // REUSING EXISTING COMPONENT
import { ChevronLeft, ChevronRight, Volume2, Square } from 'lucide-react';

interface FlashcardViewerProps {
  cards: Flashcard[];
  initialIndex?: number;
  onIndexChange?: (index: number) => void; // For parent to track state
}

const FlashcardViewer: React.FC<FlashcardViewerProps> = ({ cards, initialIndex = 0, onIndexChange }) => {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [isSpeaking, setIsSpeaking] = useState(false);
  
  // Speech Synthesis Reference
  const synth = useRef<SpeechSynthesis>(window.speechSynthesis);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  // Stop audio when unmounting or changing cards
  useEffect(() => {
    return () => {
      if (synth.current.speaking) synth.current.cancel();
    };
  }, []);

  useEffect(() => {
    // Stop audio if user switches card manually while speaking
    if (synth.current.speaking) {
      synth.current.cancel();
      setIsSpeaking(false);
    }
    if (onIndexChange) onIndexChange(currentIndex);
  }, [currentIndex, onIndexChange]);

  const toggleSpeech = (e: React.MouseEvent) => {
    e.stopPropagation();

    if (isSpeaking) {
      synth.current.cancel();
      setIsSpeaking(false);
    } else {
      // Create new utterance for current card front
      const text = cards[currentIndex].front;
      const utterance = new SpeechSynthesisUtterance(text);
      
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      
      utteranceRef.current = utterance;
      synth.current.speak(utterance);
      setIsSpeaking(true);
    }
  };

  const nextCard = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (currentIndex < cards.length - 1) setCurrentIndex(prev => prev + 1);
  };

  const prevCard = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (currentIndex > 0) setCurrentIndex(prev => prev - 1);
  };

  // Safe guard for empty decks
  if (!cards || cards.length === 0) return <div className="text-white">No cards available.</div>;

  const currentCard = cards[currentIndex];

  return (
    <div className="flex flex-col items-center justify-center w-full max-w-3xl mx-auto">
      
      {/* Main Card Area - Reusing FlipCard */}
      <div className="w-full h-96 mb-8 [perspective:1000px]">
        {/* NOTE: Adjust props 'front'/'back' if your existing FlipCard uses different names like 'question'/'answer' */}
        <FlipCard 
          front={currentCard.front} 
          back={currentCard.back} 
        />
      </div>

      {/* Controls */}
      <div className="flex items-center gap-6 bg-black/50 backdrop-blur-xl border border-white/10 px-8 py-4 rounded-full shadow-2xl">
        
        <button 
          onClick={prevCard} 
          disabled={currentIndex === 0}
          className="p-2 rounded-full text-white/70 hover:text-white hover:bg-white/10 disabled:opacity-30 transition-all"
        >
          <ChevronLeft size={28} />
        </button>

        <div className="flex flex-col items-center w-24">
          <span className="text-white font-mono text-lg">{currentIndex + 1} / {cards.length}</span>
        </div>

        {/* Speaker Toggle */}
        <button 
          onClick={toggleSpeech}
          className={`p-3 rounded-full transition-all duration-300 ${
            isSpeaking 
              ? 'bg-red-500/20 text-red-400 ring-1 ring-red-500/50' 
              : 'bg-cyan-500/10 text-cyan-400 hover:bg-cyan-500/20'
          }`}
        >
          {isSpeaking ? <Square size={20} fill="currentColor" /> : <Volume2 size={24} />}
        </button>

        <button 
          onClick={nextCard} 
          disabled={currentIndex === cards.length - 1}
          className="p-2 rounded-full text-white/70 hover:text-white hover:bg-white/10 disabled:opacity-30 transition-all"
        >
          <ChevronRight size={28} />
        </button>
      </div>
    </div>
  );
};

export default FlashcardViewer;