import { useState } from "react";
import { Routes, Route } from "react-router-dom";
import AuthPage from "./components/AuthPage";
import FlashcardGenerator from "./pages/FlashcardGenerator";
import StudyMode from "./pages/StudyMode";
import StudySelection from "./pages/StudySelection";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return !!localStorage.getItem("token");
  });

  const handleAuthSuccess = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return <AuthPage onAuthSuccess={handleAuthSuccess} />;
  }

  return (
    <Routes>
      <Route path="/" element={<FlashcardGenerator onLogout={handleLogout} />} />
      <Route path="/study" element={<StudySelection />} />
      <Route path="/study/:deckId" element={<StudyMode />} />
    </Routes>
  );
}

export default App;
