import React, { useRef, useState, useEffect } from 'react';
import FlipCard from './FlipCard';
import { FileText, CheckCircle } from 'lucide-react';

interface CardStackProps {
  initialTiltX: number;
  initialTiltY: number;
}

const CardStack: React.FC<CardStackProps> = ({ initialTiltX, initialTiltY }) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [rotation, setRotation] = useState({ x: initialTiltX, y: initialTiltY });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e: MouseEvent) => {
    if (cardRef.current) {
      const rect = cardRef.current.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;

      const deltaX = e.clientX - centerX;
      const deltaY = e.clientY - centerY;

      // Enhanced tilt sensitivity for a more "fluid" feel
      const maxTilt = 12; 
      const newX = -(deltaY / rect.height) * maxTilt; 
      const newY = (deltaX / rect.width) * maxTilt;   

      setRotation({
        x: newX + initialTiltX,
        y: newY + initialTiltY,
      });
    }
  };

  useEffect(() => {
    document.addEventListener('mousemove', handleMouseMove);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
    };
  }, [initialTiltX, initialTiltY]);

  // --- SENIOR DEV VISUAL LOGIC ---
  // We calculate transforms dynamically to mix the "Tilt" (Container) with the "Fan" (Children)
  // This avoids CSS conflicts and ensures 60FPS transitions.

  return (
    <div
      ref={cardRef}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="card-stack w-[300px] h-[420px] lg:w-[360px] lg:h-[500px] transition-all duration-700 ease-out will-change-transform cursor-pointer"
      style={{
        transform: `perspective(1200px) rotateX(${isHovered ? rotation.x / 2 : rotation.x}deg) rotateY(${isHovered ? rotation.y / 2 : rotation.y}deg) scale(${isHovered ? 1.05 : 1})`,
      }}
    >
      
      {/* LAYER 1: BOTTOM CARD (Deep Indigo) */}
      <div
        className="card-layer"
        style={{
          // On hover: Move down-left and rotate more (-12deg) to "fan" out
          transform: isHovered 
            ? 'translate3d(-40px, 30px, -60px) rotateZ(-12deg)' 
            : 'translate3d(-20px, 20px, -60px) rotateZ(-6deg)',
          zIndex: 1,
          transitionDelay: '0ms'
        }}
      >
        <div className="card-surface p-6 bg-gradient-to-br from-indigo-950 to-slate-900 border-indigo-800/30">
          <div className="flex items-center justify-between text-indigo-300/50 font-medium text-sm mb-4">
             <span>Flashcard #1</span>
             <FileText className="w-4 h-4" />
          </div>
          <div className="h-2 w-24 bg-indigo-800/20 rounded-full mb-3"></div>
          <div className="h-2 w-16 bg-indigo-800/20 rounded-full"></div>
          
          {/* Decorative gradient orb */}
          <div className="absolute bottom-0 right-0 w-32 h-32 bg-indigo-600/20 blur-3xl rounded-full"></div>
        </div>
      </div>

      {/* LAYER 2: MIDDLE CARD (Electric Violet) */}
      <div
        className="card-layer"
        style={{
          // On hover: Move slightly down-left and rotate (-6deg)
          transform: isHovered 
            ? 'translate3d(-20px, 15px, -30px) rotateZ(-6deg)' 
            : 'translate3d(-10px, 10px, -30px) rotateZ(-3deg)',
          zIndex: 2,
          transitionDelay: '50ms'
        }}
      >
        <div className="card-surface p-6 bg-gradient-to-br from-violet-950 to-purple-900 border-violet-700/30">
           <div className="flex items-center justify-between text-violet-300/50 font-medium text-sm mb-4">
             <span>Flashcard #2</span>
             <CheckCircle className="w-4 h-4" />
          </div>
          <div className="h-2 w-32 bg-violet-700/20 rounded-full mb-3"></div>
          <div className="h-2 w-20 bg-violet-700/20 rounded-full"></div>

           {/* Decorative gradient orb */}
           <div className="absolute bottom-0 right-0 w-32 h-32 bg-purple-500/20 blur-3xl rounded-full"></div>
        </div>
      </div>

      {/* LAYER 3: TOP INTERACTIVE CARD (Cyan/Blue) */}
      <div
        className="card-layer"
        style={{
          // On hover: Lift up towards viewer (Z axis) and straighten out
          transform: isHovered 
            ? 'translate3d(0, -10px, 20px) rotateZ(0deg)' 
            : 'translate3d(0, 0, 0) rotateZ(0deg)',
          zIndex: 3,
          transitionDelay: '100ms'
        }}
      >
        <FlipCard />
      </div>

      {/* Global Glow behind the stack */}
      <div 
        className={`absolute inset-0 -m-4 rounded-[2.5rem] bg-indigo-500/20 blur-[60px] transition-opacity duration-700 pointer-events-none ${isHovered ? 'opacity-60' : 'opacity-20'}`}
        style={{ zIndex: 0 }}
      />
      
    </div>
  );
};

export default CardStack;