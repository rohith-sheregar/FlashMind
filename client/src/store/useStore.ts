import { create } from "zustand";
import { IDeck } from "../types";

interface AppState {
  currentDeck: IDeck | null;
  isGenerating: boolean;

  // Actions
  setCurrentDeck: (deck: IDeck | null) => void;
  setIsGenerating: (isGen: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
  currentDeck: null,
  isGenerating: false,
  setCurrentDeck: (deck) => set({ currentDeck: deck }),
  setIsGenerating: (isGen) => set({ isGenerating: isGen }),
}));
