import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, ChevronLeft, ChevronRight, RotateCw } from "lucide-react";
import api from "../services/api";

// Define the shape of the data we expect from the API
interface Card {
  front: string;
  back: string;
}

interface DeckResponse {
  id: number;
  title: string;
  cards: Card[];
}

const StudyMode = () => {
  // 1. Get the ID from the URL (e.g., /study/2 or /study/uuid-...)
  const { deckId } = useParams<{ deckId: string }>();

  const [deck, setDeck] = useState<DeckResponse | null>(null);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDeck = async () => {
      try {
        console.log(`🔍 Fetching Deck ID: ${deckId}...`);
        // 2. Fetch from Backend
        const response = await api.get(`/decks/${deckId}`);

        console.log("✅ Data Received:", response.data);
        setDeck(response.data);
      } catch (err: any) {
        console.error("❌ Fetch Error:", err);
        setError("Could not load deck. Check backend logs.");
      } finally {
        setLoading(false);
      }
    };

    if (deckId) fetchDeck();
  }, [deckId]);

  // --- RENDER STATES ---

  if (loading)
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <div className="animate-pulse text-xl font-semibold text-indigo-600">
          Loading Flashcards...
        </div>
      </div>
    );

  if (error)
    return (
      <div className="flex h-screen items-center justify-center bg-red-50 text-red-600">
        {error}
      </div>
    );

  if (!deck || deck.cards.length === 0)
    return (
      <div className="flex flex-col h-screen items-center justify-center bg-slate-50">
        <p className="text-xl text-slate-600">This deck has no cards.</p>
        <Link to="/" className="mt-4 text-indigo-600 hover:underline">
          Go Back Home
        </Link>
      </div>
    );

  // --- MAIN UI ---

  const currentCard = deck.cards[currentCardIndex];

  const nextCard = () => {
    setIsFlipped(false);
    setCurrentCardIndex((prev) => (prev + 1) % deck.cards.length);
  };

  const prevCard = () => {
    setIsFlipped(false);
    setCurrentCardIndex(
      (prev) => (prev - 1 + deck.cards.length) % deck.cards.length
    );
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col">
      {/* Header */}
      <div className="bg-white shadow-sm p-4 flex items-center justify-between">
        <Link
          to="/"
          className="flex items-center text-slate-600 hover:text-indigo-600 transition"
        >
          <ArrowLeft size={20} className="mr-2" />
          Back to Upload
        </Link>
        <h1 className="font-bold text-lg text-slate-800">{deck.title}</h1>
        <div className="text-sm text-slate-500">
          Card {currentCardIndex + 1} / {deck.cards.length}
        </div>
      </div>

      {/* Flashcard Area */}
      <div className="flex-1 flex flex-col items-center justify-center p-6">
        {/* The Card Container */}
        <div
          className="relative w-full max-w-2xl aspect-video cursor-pointer group perspective-1000"
          onClick={() => setIsFlipped(!isFlipped)}
        >
          <div
            className={`
            relative w-full h-full duration-500 preserve-3d transition-all shadow-xl rounded-2xl bg-white
            ${isFlipped ? "rotate-y-180" : ""}
          `}
          >
            {/* FRONT */}
            <div className="absolute w-full h-full backface-hidden p-8 flex flex-col items-center justify-center text-center">
              <span className="absolute top-4 left-4 text-xs font-bold tracking-wider text-slate-400 uppercase">
                Question
              </span>
              <h2 className="text-2xl md:text-3xl font-medium text-slate-800 leading-relaxed">
                {currentCard.front}
              </h2>
              <div className="absolute bottom-4 text-slate-400 text-sm flex items-center gap-2">
                <RotateCw size={16} /> Click to flip
              </div>
            </div>

            {/* BACK */}
            <div className="absolute w-full h-full backface-hidden rotate-y-180 bg-indigo-600 text-white rounded-2xl p-8 flex flex-col items-center justify-center text-center">
              <span className="absolute top-4 left-4 text-xs font-bold tracking-wider text-indigo-200 uppercase">
                Answer
              </span>
              <p className="text-xl md:text-2xl leading-relaxed">
                {currentCard.back}
              </p>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="mt-8 flex items-center gap-6">
          <button
            onClick={prevCard}
            className="p-3 rounded-full bg-white shadow hover:bg-slate-50 text-slate-700 transition"
          >
            <ChevronLeft size={24} />
          </button>

          <button
            onClick={nextCard}
            className="p-3 rounded-full bg-white shadow hover:bg-slate-50 text-slate-700 transition"
          >
            <ChevronRight size={24} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default StudyMode;
