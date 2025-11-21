import { Routes, Route } from "react-router-dom";
import FileDropzone from "./components/FileDropzone"; // Or your Landing page
import StudyMode from "./pages/StudyMode";
import Login from "./pages/Login"; // <-- ADD THIS

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
      <Route path="/" element={<FileDropzone />} />
      {/* THE IMPORTANT PART: :deckId allows /study/2 to work */}
      <Route path="/study/:deckId" element={<StudyMode />} />
    </Routes>
  );
}

export default App;
