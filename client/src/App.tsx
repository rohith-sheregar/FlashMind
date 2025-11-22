import React, { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Landing from "./pages/Landing";
import FlashcardGenerator from "./pages/FlashcardGenerator";
import StudyMode from "./pages/StudyMode";
import AuthPage from "./pages/AuthPage";
import { useStore } from "./store/useStore";
import api from "./services/api";

const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const user = useStore((state) => state.user);
  if (!user) {
    return <Navigate to="/auth" replace />;
  }
  return children;
};

function App() {
  const setUser = useStore((state) => state.setUser);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem("token");
      if (token) {
        try {
          const response = await api.get("/auth/me");
          setUser(response.data);
        } catch (error) {
          console.error("Auth check failed:", error);
          localStorage.removeItem("token");
          setUser(null);
        }
      }
    };
    checkAuth();
  }, [setUser]);

  return (
    <div className="min-h-screen bg-gray-900 text-white font-sans">
      <Routes>
        <Route path="/" element={<Navigate to="/auth" replace />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route
          path="/flashcards"
          element={
            <ProtectedRoute>
              <FlashcardGenerator onBack={() => { }} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/study"
          element={
            <ProtectedRoute>
              <StudyMode />
            </ProtectedRoute>
          }
        />
      </Routes>
    </div>
  );
}

export default App;
