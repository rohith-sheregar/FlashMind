import React from 'react';
import { Deck } from '../types'; // Ensure you have this type defined
import { Play } from 'lucide-react';

interface DeckPreviewProps {
  deck: Deck;
  onClick: (deck: Deck) => void;
}

const DeckPreview: React.FC<DeckPreviewProps> = ({ deck, onClick }) => {
  return (
    <div 
      onClick={() => onClick(deck)}
      className="group relative w-56 h-36 flex-shrink-0 cursor-pointer transition-transform duration-300 hover:-translate-y-2 mx-4"
    >
      {/* Bottom Layer (Static) */}
      <div className="absolute inset-0 bg-gray-800 rounded-xl transform rotate-6 translate-x-2 translate-y-2 border border-white/5 opacity-60 group-hover:rotate-12 transition-transform duration-500" />
      
      {/* Middle Layer (Static) */}
      <div className="absolute inset-0 bg-gray-800 rounded-xl transform rotate-3 translate-x-1 translate-y-1 border border-white/5 opacity-80 group-hover:rotate-6 transition-transform duration-500" />
      
      {/* Top Layer (Active) */}
      <div className="absolute inset-0 bg-gradient-to-br from-gray-900 to-black border border-white/10 rounded-xl p-5 flex flex-col justify-between shadow-2xl group-hover:border-cyan-500/50 transition-colors duration-300 relative overflow-hidden">
        
        {/* Hover Glow */}
        <div className="absolute -top-10 -right-10 w-20 h-20 bg-cyan-500/20 blur-2xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

        <div className="flex justify-between items-start z-10">
          <div className="h-1 w-8 bg-cyan-500 rounded-full" />
          <Play className="w-4 h-4 text-white/30 group-hover:text-cyan-400 transition-colors" />
        </div>

        <div className="z-10">
          <h3 className="text-white font-semibold truncate tracking-wide">{deck.deckName}</h3>
          <p className="text-white/40 text-xs mt-1">{deck.cards.length} Cards</p>
        </div>
      </div>
    </div>
  );
};

export default DeckPreview;