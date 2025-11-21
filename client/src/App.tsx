import { BrowserRouter, Routes, Route } from "react-router-dom";
import FileDropzone from "./components/FileDropzone";
import StudyMode from "./pages/StudyMode";
import Login from "./pages/Login"; // <-- ADD THIS

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Default landing page */}
        <Route path="/" element={<FileDropzone />} />

        {/* Login page */}
        <Route path="/login" element={<Login />} />

        {/* Study page with dynamic deckId */}
        <Route path="/study/:deckId" element={<StudyMode />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
