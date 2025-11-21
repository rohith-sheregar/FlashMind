import React, { useState } from "react";
import { Routes, Route } from "react-router-dom";
import AuthPage from "./components/AuthPage";
import Landing from "./pages/Landing";
import FlashcardGenerator from "./pages/FlashcardGenerator";
import StudyMode from "./pages/StudyMode";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentView, setCurrentView] = useState<'landing' | 'flashcards' | 'images'>('landing');

  const handleAuthSuccess = () => {
    setIsAuthenticated(true);
  };

  const handleNavigate = (feature: 'flashcards' | 'images') => {
    if (feature === 'flashcards') {
      setCurrentView('flashcards');
    } else {
      // For now, images feature is not implemented
      alert('Image generation feature coming soon!');
    }
  };

  const handleBack = () => {
    setCurrentView('landing');
  };

  if (!isAuthenticated) {
    return <AuthPage onAuthSuccess={handleAuthSuccess} />;
  }

  return (
    <Routes>
      <Route 
        path="/" 
        element={
          currentView === 'landing' ? (
            <Landing onNavigate={handleNavigate} />
          ) : currentView === 'flashcards' ? (
            <FlashcardGenerator onBack={handleBack} />
          ) : (
            <Landing onNavigate={handleNavigate} />
          )
        } 
      />
      <Route path="/study/:deckId" element={<StudyMode />} />
    </Routes>
  );
}

export default App;
