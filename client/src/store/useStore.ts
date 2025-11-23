import { create } from "zustand";
import { IDeck } from "../types";

interface AppState {
  currentDeck: IDeck | null;
  isGenerating: boolean;

  // Actions
  setCurrentDeck: (_deck: IDeck | null) => void;
  setIsGenerating: (_isGenerating: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
  currentDeck: null,
  isGenerating: false,
  setCurrentDeck: (nextDeck) => set({ currentDeck: nextDeck }),
  setIsGenerating: (nextState) => set({ isGenerating: nextState }),
}));
