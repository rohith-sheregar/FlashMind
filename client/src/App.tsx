import { Routes, Route } from "react-router-dom";
import FileDropzone from "./components/FileDropzone"; // Or your Landing page
import StudyMode from "./pages/StudyMode";

function App() {
  return (
    <Routes>
      <Route path="/" element={<FileDropzone />} />
      {/* THE IMPORTANT PART: :deckId allows /study/2 to work */}
      <Route path="/study/:deckId" element={<StudyMode />} />
    </Routes>
  );
}

export default App;
