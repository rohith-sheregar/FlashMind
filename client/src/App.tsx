import { useState } from "react";
import { Routes, Route } from "react-router-dom";
import AuthPage from "./components/AuthPage";
import FlashcardGenerator from "./pages/FlashcardGenerator";
import StudyMode from "./pages/StudyMode";
import StudySelection from "./pages/StudySelection";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const handleAuthSuccess = () => {
    setIsAuthenticated(true);
  };

  if (!isAuthenticated) {
    return <AuthPage onAuthSuccess={handleAuthSuccess} />;
  }

  return (
    <Routes>
      <Route path="/" element={<FlashcardGenerator />} />
      <Route path="/study" element={<StudySelection />} />
      <Route path="/study/:deckId" element={<StudyMode />} />
    </Routes>
  );
}

export default App;
