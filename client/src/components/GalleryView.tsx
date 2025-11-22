import React from 'react';
import FlashcardViewer from './FlashcardViewer';
import { Deck } from '../types';
import { X } from 'lucide-react';

interface GalleryViewProps {
  deck: Deck;
  onClose: () => void;
  lastIndex: number;
  onSaveProgress: (index: number) => void;
}

const GalleryView: React.FC<GalleryViewProps> = ({ deck, onClose, lastIndex, onSaveProgress }) => {
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center">
      
      {/* Backdrop Blur */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-xl transition-opacity duration-300" 
        onClick={onClose} // Click outside to close
      />

      {/* Content Container */}
      <div className="relative z-10 w-full max-w-5xl px-4 animate-in fade-in zoom-in-95 duration-300">
        
        {/* Header */}
        <div className="absolute -top-16 left-0 right-0 flex justify-between items-center px-4">
          <h2 className="text-2xl font-bold text-white tracking-tight">{deck.deckName}</h2>
          <button 
            onClick={onClose}
            className="p-2 rounded-full bg-white/5 hover:bg-white/10 text-white transition-colors border border-white/5"
          >
            <X size={24} />
          </button>
        </div>

        {/* Viewer */}
        <FlashcardViewer 
          cards={deck.cards} 
          initialIndex={lastIndex}
          onIndexChange={onSaveProgress}
        />
      </div>
    </div>
  );
};

export default GalleryView;
