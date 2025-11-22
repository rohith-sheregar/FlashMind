import { create } from "zustand";
import { IDeck } from "../types";

interface User {
  id: number;
  username: string;
  email: string;
}

interface AppState {
  user: User | null;
  currentDeck: IDeck | null;
  isGenerating: boolean;

  // Actions
  setUser: (user: User | null) => void;
  logout: () => void;
  setCurrentDeck: (_deck: IDeck | null) => void;
  setIsGenerating: (_isGenerating: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
  user: null,
  currentDeck: null,
  isGenerating: false,
  setUser: (user) => set({ user }),
  logout: () => {
    localStorage.removeItem("token");
    set({ user: null, currentDeck: null });
  },
  setCurrentDeck: (nextDeck) => set({ currentDeck: nextDeck }),
  setIsGenerating: (nextState) => set({ isGenerating: nextState }),
}));
