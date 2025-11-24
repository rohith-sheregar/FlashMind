import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, ChevronLeft, ChevronRight, RotateCw, Volume2 } from "lucide-react";
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
        const response = await api.get(`/decks/${deckId}`);
        setDeck(response.data);
      } catch (err: unknown) {
        console.error("Failed to load deck:", err);
        const fallbackMessage =
          typeof err === "object" &&
            err !== null &&
            "message" in err &&
            typeof (err as { message?: string }).message === "string"
            ? (err as { message: string }).message
            : "Could not load deck. Check backend logs.";
        setError(fallbackMessage);
      } finally {
        setLoading(false);
      }
    };

    if (deckId) fetchDeck();
  }, [deckId]);

  // --- QUIZ STATE ---
  const [showQuiz, setShowQuiz] = useState(false);
  const [quizData, setQuizData] = useState<any>(null);
  const [quizLoading, setQuizLoading] = useState(false);
  const [cardsReviewed, setCardsReviewed] = useState(0);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [quizResult, setQuizResult] = useState<"correct" | "incorrect" | null>(null);

  // --- QUIZ LOGIC ---
  // --- QUIZ LOGIC ---
  const handleGenerateQuiz = async () => {
    setQuizLoading(true);
    setShowQuiz(true);

    // Get last 5 cards for context (or random ones if we wanted)
    // For now, let's just take the current card + 4 previous ones to make context
    const recentCards = [];
    for (let i = 0; i < 5; i++) {
      const idx = (currentCardIndex - i + deck!.cards.length) % deck!.cards.length;
      recentCards.push(deck!.cards[idx]);
    }

    console.log("Generating quiz with cards:", recentCards);

    try {
      const response = await api.post("/quiz/generate", { cards: recentCards });
      console.log("Quiz generation response:", response.data);
      setQuizData(response.data);
    } catch (error) {
      console.error("Failed to generate quiz:", error);
      // setShowQuiz(false); // Keep popup open to show error
    } finally {
      setQuizLoading(false);
    }
  };

  const handleNextCard = async () => {
    const nextIndex = (currentCardIndex + 1) % deck!.cards.length;
    setCardsReviewed(cardsReviewed + 1);
    setCurrentCardIndex(nextIndex);
    setIsFlipped(false);
  };

  const handleQuizAnswer = (option: string) => {
    setSelectedOption(option);
    if (option === quizData.correct_answer) {
      setQuizResult("correct");
    } else {
      setQuizResult("incorrect");
    }
  };

  const closeQuiz = () => {
    setShowQuiz(false);
    setQuizData(null);
    setSelectedOption(null);
    setQuizResult(null);
    setCurrentCardIndex((prev) => (prev + 1) % deck!.cards.length);
    setIsFlipped(false);
  };

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

  const prevCard = () => {
    setIsFlipped(false);
    setCurrentCardIndex(
      (prev) => (prev - 1 + deck.cards.length) % deck.cards.length
    );
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
    <div className="min-h-screen bg-slate-100 flex flex-col relative">
      {/* Quiz Overlay */}
      {showQuiz && (
        <div className="absolute inset-0 z-50 bg-slate-900/90 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-3xl w-full p-8 shadow-2xl">
            {quizLoading ? (
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
                <p className="text-slate-600 font-medium">Generating Quiz...</p>
              </div>
            ) : quizData ? (
              <div>
                <h2 className="text-2xl font-bold text-slate-800 mb-6">Quick Quiz!</h2>
                <p className="text-lg text-slate-700 mb-6">{quizData.question}</p>

                <div className="space-y-3 mb-8">
                  {Object.entries(quizData.options).map(([key, value]) => (
                    <button
                      key={key}
                      onClick={() => !quizResult && handleQuizAnswer(key)}
                      disabled={!!quizResult}
                      className={`w-full text-left p-4 rounded-xl border-2 transition-all
                        ${selectedOption === key
                          ? quizResult === "correct"
                            ? "border-green-500 bg-green-50 text-green-700"
                            : "border-red-500 bg-red-50 text-red-700"
                          : "border-slate-200 hover:border-indigo-300 hover:bg-slate-50"
                        }
                        ${quizResult && key === quizData.correct_answer ? "border-green-500 bg-green-50 text-green-700" : ""}
                      `}
                    >
                      <span className="font-bold mr-2">{key})</span> {value as string}
                    </button>
                  ))}
                </div>

                {quizResult && (
                  <div className="flex items-center justify-between animate-in fade-in slide-in-from-bottom-4">
                    <p className={`font-bold ${quizResult === "correct" ? "text-green-600" : "text-red-600"}`}>
                      {quizResult === "correct" ? "🎉 Correct! Well done." : "Incorrect. The correct answer was " + quizData.correct_answer}
                    </p>
                    <button
                      onClick={closeQuiz}
                      className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
                    >
                      Continue Studying
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center">
                <p className="text-red-500 mb-4">Failed to load quiz.</p>
                <button
                  onClick={() => setShowQuiz(false)}
                  className="px-4 py-2 bg-slate-200 rounded-lg hover:bg-slate-300"
                >
                  Skip Quiz
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-white shadow-sm p-4 flex items-center justify-between">
        <Link
          to="/study"
          className="flex items-center text-slate-600 hover:text-indigo-600 transition"
        >
          <ArrowLeft size={20} className="mr-2" />
          Back to Library
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
            relative w-full h-full duration-500 transform-style-3d transition-all shadow-xl rounded-2xl bg-white
            ${isFlipped ? "rotate-y-180" : ""}
          `}
          >
            {/* FRONT */}
            <div className="absolute w-full h-full backface-hidden p-8 flex flex-col items-center justify-center text-center">
              <div className="absolute top-4 left-4 flex items-center gap-2">
                <span className="text-xs font-bold tracking-wider text-slate-400 uppercase">
                  Question
                </span>
                <button
                  onClick={(e) => speakText(currentCard.front, e)}
                  className="p-1 hover:bg-slate-100 rounded-full transition-colors"
                  title="Listen"
                >
                  <Volume2 size={16} className="text-slate-400 hover:text-indigo-600" />
                </button>
              </div>
              <h2 className="text-2xl md:text-3xl font-medium text-slate-800 leading-relaxed">
                {currentCard.front}
              </h2>
              <div className="absolute bottom-4 text-slate-400 text-sm flex items-center gap-2">
                <RotateCw size={16} /> Click to flip
              </div>
            </div>

            {/* BACK */}
            <div className="absolute w-full h-full backface-hidden rotate-y-180 bg-indigo-600 text-white rounded-2xl p-8 flex flex-col items-center justify-center text-center">
              <div className="absolute top-4 left-4 flex items-center gap-2">
                <span className="text-xs font-bold tracking-wider text-indigo-200 uppercase">
                  Answer
                </span>
                <button
                  onClick={(e) => speakText(currentCard.back, e)}
                  className="p-1 hover:bg-white/10 rounded-full transition-colors"
                  title="Listen"
                >
                  <Volume2 size={16} className="text-indigo-200 hover:text-white" />
                </button>
              </div>
              <p className="text-xl md:text-2xl leading-relaxed">
                {currentCard.back}
              </p>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="mt-8 flex flex-col items-center gap-4">
          <div className="flex items-center gap-6">
            <button
              onClick={prevCard}
              className="p-3 rounded-full bg-white shadow hover:bg-slate-50 text-slate-700 transition"
            >
              <ChevronLeft size={24} />
            </button>

            <button
              onClick={handleNextCard}
              className="p-3 rounded-full bg-white shadow hover:bg-slate-50 text-slate-700 transition"
            >
              <ChevronRight size={24} />
            </button>
          </div>

          <button
            onClick={handleGenerateQuiz}
            disabled={quizLoading}
            className="px-6 py-2 bg-indigo-100 text-indigo-700 rounded-full font-medium hover:bg-indigo-200 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {quizLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-indigo-700 border-t-transparent rounded-full animate-spin"></div>
                Generating...
              </>
            ) : (
              <>
                <RotateCw size={16} />
                Generate Quiz
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default StudyMode;
