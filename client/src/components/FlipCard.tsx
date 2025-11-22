import React, { useState } from 'react';

const cardContent = {
  front: "What is the primary function of the Golgi apparatus?",
  back: "It modifies, sorts, and packages proteins and lipids for secretion or delivery to other organelles."
};

const FlipCard: React.FC = () => {
  const [isFlipped, setIsFlipped] = useState(false);

  const handleFlip = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent stack hover jitter when clicking
    setIsFlipped(!isFlipped);
  };

  return (
    <div className="flip-card group/card" onClick={handleFlip}>
      <div className={`flip-inner ${isFlipped ? 'is-flipped' : ''}`}>
        
        {/* FRONT SIDE - Premium Glass + Blue/Cyan Gradient */}
        <div className="flip-face flip-front relative overflow-hidden">
          {/* Dynamic Background */}
          <div className="absolute inset-0 bg-gradient-to-b from-slate-900 via-[#0f172a] to-[#1e1b4b] opacity-95"></div>
          
          {/* Top Highlight Gradient */}
          <div className="absolute top-0 left-0 right-0 h-1/2 bg-gradient-to-b from-cyan-500/10 to-transparent"></div>
          
          {/* Content Container */}
          <div className="relative z-10 flex flex-col h-full justify-center items-center text-center p-8 border border-white/10 rounded-2xl">
            
            {/* Floating Badge */}
            <div className="bg-white/5 backdrop-blur-md border border-white/10 px-3 py-1 rounded-full text-[10px] font-bold tracking-widest text-cyan-400 uppercase mb-6 shadow-lg">
              Question
            </div>

            <h3 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-300 leading-relaxed drop-shadow-sm">
              {cardContent.front}
            </h3>
            
            <div className="mt-auto text-xs text-cyan-200/60 font-medium tracking-wide flex items-center gap-2">
               <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
               Click to Flip
            </div>
          </div>
        </div>

        {/* BACK SIDE - Premium Violet Gradient */}
        <div className="flip-face flip-back relative overflow-hidden">
           {/* Dynamic Background */}
           <div className="absolute inset-0 bg-gradient-to-br from-[#1e1b4b] to-[#312e81] opacity-95"></div>
           
           {/* Bottom Highlight */}
           <div className="absolute bottom-0 left-0 right-0 h-2/3 bg-gradient-to-t from-indigo-500/10 to-transparent"></div>

          <div className="relative z-10 flex flex-col h-full justify-center items-center text-center p-8 border border-indigo-400/20 rounded-2xl">
            
            <div className="bg-indigo-500/20 backdrop-blur-md border border-indigo-500/30 px-3 py-1 rounded-full text-[10px] font-bold tracking-widest text-indigo-300 uppercase mb-6">
              Answer
            </div>

            <p className="text-lg text-indigo-100 leading-relaxed font-light">
              {cardContent.back}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FlipCard;