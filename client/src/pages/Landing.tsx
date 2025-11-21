import React from "react";
import FileDropzone from "../components/FileDropzone";

interface LandingProps {
  onNavigate: () => void;
}

const Landing: React.FC<LandingProps> = ({ onNavigate }) => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
      <div className="text-center mb-10">
        <h1 className="text-5xl font-extrabold text-slate-900 mb-4">
          FlashMind 🧠
        </h1>
        <p className="text-xl text-slate-600">
          Turn your documents into flashcards in seconds.
        </p>
      </div>

      {/* File uploader */}
      <div className="w-full max-w-2xl">
        <FileDropzone />
      </div>

      {/* Navigation button to study mode */}
      <button
        onClick={onNavigate}
        className="mt-8 px-6 py-3 bg-indigo-600 text-white rounded-xl shadow hover:bg-indigo-700 transition"
      >
        Go to Study Mode
      </button>
    </div>
  );
};

export default Landing;
