import React, { useState } from "react";
import { useNavigate } from "react-router-dom"; // <--- Import for redirection
import {
  Upload,
  Loader2,
  CheckCircle,
  AlertCircle,
  BookOpen,
} from "lucide-react";
import api from "../services/api";

const FileDropzone: React.FC = () => {
  const [status, setStatus] = useState<
    "idle" | "uploading" | "success" | "error"
  >("idle");
  const [message, setMessage] = useState("");
  const [deckId, setDeckId] = useState<string | null>(null);

  const navigate = useNavigate(); // <--- Hook for navigation

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;

    const file = e.target.files[0];
    setStatus("uploading");
    setMessage("Uploading and initializing AI...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await api.post("/documents/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      // 1. Save the ID we got from the backend
      setDeckId(response.data.deck_id);
      setStatus("success");
      setMessage("Flashcards generated successfully!");
    } catch (error: unknown) {
      console.error("Upload failed:", error);
      setStatus("error");
      setMessage(
        error instanceof Error ? error.message : "Connection Failed. Is the Backend running?"
      );
    }
  };

  // 2. Function to handle the button click
  const handleStartStudying = () => {
    if (deckId) {
      navigate(`/study/${deckId}`);
    }
  };

  return (
    <div className="p-8 max-w-xl mx-auto bg-white rounded-xl shadow-lg border border-slate-100 mt-10">
      <h2 className="text-2xl font-bold text-slate-800 mb-2">FlashMind AI</h2>
      <p className="text-slate-500 mb-6">
        Upload your notes to generate a study deck.
      </p>

      {/* SUCCESS STATE - SHOW STUDY BUTTON */}
      {status === "success" ? (
        <div className="flex flex-col items-center justify-center p-8 border-2 border-green-100 bg-green-50 rounded-xl animate-in fade-in zoom-in">
          <CheckCircle className="w-16 h-16 text-green-500 mb-4" />
          <h3 className="text-xl font-bold text-green-700 mb-2">Deck Ready!</h3>
          <p className="text-green-600 text-center mb-6">
            Your flashcards have been created.
          </p>

          <button
            onClick={handleStartStudying}
            className="flex items-center gap-2 px-8 py-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg shadow-lg transition-all transform hover:scale-105"
          >
            <BookOpen size={20} />
            Start Studying Now
          </button>
        </div>
      ) : (
        /* UPLOAD STATE */
        <div
          className={`
          relative border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center text-center transition-all h-64
          ${
            status === "uploading"
              ? "border-blue-400 bg-blue-50"
              : "border-slate-300 hover:border-indigo-500 hover:bg-slate-50"
          }
        `}
        >
          {status === "uploading" ? (
            <div className="flex flex-col items-center animate-pulse text-blue-600">
              <Loader2 className="w-12 h-12 animate-spin mb-4" />
              <span className="font-semibold text-lg">
                Consulting the AI...
              </span>
              <span className="text-sm mt-2 opacity-75">
                This may take 10-20 seconds
              </span>
            </div>
          ) : status === "error" ? (
            <div className="flex flex-col items-center text-red-500">
              <AlertCircle className="w-12 h-12 mb-2" />
              <span className="font-semibold">{message}</span>
              <button
                onClick={() => setStatus("idle")}
                className="mt-4 text-sm underline hover:text-red-700"
              >
                Try Again
              </button>
            </div>
          ) : (
            /* IDLE STATE */
            <>
              <Upload className="w-12 h-12 text-indigo-400 mb-4" />
              <p className="text-lg font-medium text-slate-700">
                Click to upload document
              </p>
              <p className="text-sm text-slate-400 mt-2">
                PDF or DOCX (Max 10MB)
              </p>
              <input
                type="file"
                onChange={handleFileChange}
                accept=".pdf,.docx,.txt"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default FileDropzone;
