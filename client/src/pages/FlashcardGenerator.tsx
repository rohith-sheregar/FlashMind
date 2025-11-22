import React, { useState, useCallback } from "react";
import { ArrowLeft, Upload, X, Brain, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { Flashcard } from "../components/Flashcard";
import { IFlashcard } from "../types";
import api, { API_URL } from "../services/api";

interface FlashcardGeneratorProps {
  onBack: () => void;
}

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  deckId?: string;
}

const FlashcardGenerator: React.FC<FlashcardGeneratorProps> = ({ onBack }) => {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [flashcards, setFlashcards] = useState<IFlashcard[]>([]);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (type: string) => {
    if (type.includes('pdf')) return '📄';
    if (type.includes('word') || type.includes('document')) return '📝';
    if (type.includes('image')) return '🖼️';
    if (type.includes('text')) return '📃';
    if (type.includes('presentation')) return '📊';
    return '📁';
  };

  const handleFileUpload = async (files: FileList) => {
    const newFiles: UploadedFile[] = Array.from(files).map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'uploading',
      progress: 0,
    }));

    setUploadedFiles(prev => [...prev, ...newFiles]);

    // Process each file
    for (const file of Array.from(files)) {
      const fileId = newFiles.find(f => f.name === file.name)?.id;
      if (!fileId) continue;

      try {
        // Update status to uploading
        setUploadedFiles(prev => prev.map(f => 
          f.id === fileId ? { ...f, status: 'uploading', progress: 30 } : f
        ));

        const formData = new FormData();
        formData.append('file', file);

        const response = await api.post('/documents/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });

        // Update status to processing
        setUploadedFiles(prev => prev.map(f => 
          f.id === fileId ? { 
            ...f, 
            status: 'processing', 
            progress: 60,
            deckId: response.data.deck_id 
          } : f
        ));

        // Start streaming flashcards for this deck so they appear one by one
        try {
          const deckId = response.data.deck_id as string;
          const streamBase = API_URL.replace(/\/api$/, "");
          const streamUrl = `${streamBase}/api/documents/stream/${deckId}`;

          const eventSource = new EventSource(streamUrl);

          eventSource.onmessage = (event) => {
            if (!event.data) return;
            try {
              const payload = JSON.parse(event.data);
              const type = payload.type;

              if (type === "status") {
                const status = payload.data?.status as string | undefined;
                const progress = payload.data?.progress as number | undefined;

                setUploadedFiles((prev) =>
                  prev.map((f) =>
                    f.id === fileId
                      ? {
                          ...f,
                          status:
                            status === "completed"
                              ? "completed"
                              : status === "error"
                              ? "error"
                              : "processing",
                          progress: typeof progress === "number" ? progress : f.progress,
                        }
                      : f
                  )
                );
              } else if (type === "card") {
                const card = payload.data;
                if (!card) return;

                const newCard: IFlashcard = {
                  id: `${deckId}-${card.id}`,
                  question: card.question,
                  answer: card.answer,
                  fileId,
                };

                setFlashcards((prev) => [...prev, newCard]);
              } else if (type === "error") {
                setUploadedFiles((prev) =>
                  prev.map((f) =>
                    f.id === fileId ? { ...f, status: "error", progress: 0 } : f
                  )
                );
                eventSource.close();
              } else if (type === "complete") {
                // Finalize progress if not already at 100%
                setUploadedFiles((prev) =>
                  prev.map((f) =>
                    f.id === fileId && f.status !== "error"
                      ? { ...f, status: "completed", progress: 100 }
                      : f
                  )
                );
                eventSource.close();
              }
            } catch {
              // Ignore malformed events
            }
          };

          eventSource.onerror = () => {
            setUploadedFiles((prev) =>
              prev.map((f) =>
                f.id === fileId && f.status === "processing"
                  ? { ...f, status: "error", progress: 0 }
                  : f
              )
            );
            eventSource.close();
          };
        } catch (streamSetupError) {
          console.error("Failed to open flashcard stream:", streamSetupError);
          setUploadedFiles(prev => prev.map(f => 
            f.id === fileId ? { ...f, status: 'error', progress: 0 } : f
          ));
        }

      } catch (uploadError) {
        console.error("Upload failed:", uploadError);
        setUploadedFiles(prev => prev.map(f => 
          f.id === fileId ? { ...f, status: 'error', progress: 0 } : f
        ));
      }
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const removeFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
    setFlashcards(prev => prev.filter(f => f.fileId !== fileId));
  };

  const handleCardFlip = () => {
    setIsFlipped(!isFlipped);
  };

  const nextCard = () => {
    setIsFlipped(false);
    setCurrentCardIndex((prev) => (prev + 1) % flashcards.length);
  };

  const prevCard = () => {
    setIsFlipped(false);
    setCurrentCardIndex((prev) => (prev - 1 + flashcards.length) % flashcards.length);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-lg border-b border-white/20 p-6">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center space-x-4">
            <button
              onClick={onBack}
              type="button"
              aria-label="Go back to landing"
              className="p-2 hover:bg-gray-100 rounded-xl transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </button>
              <div className="flex items-center space-x-3">
                {/* Logo placeholder area */}
                <div className="w-8 h-8 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <Brain className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">Flashmind</h1>
                  <p className="text-sm text-gray-500">Flashcard Generator</p>
                </div>
              </div>
          </div>
          <div className="text-sm text-gray-500">
            {flashcards.length} flashcards generated
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto p-6">
        <div className="grid lg:grid-cols-2 gap-8 h-[calc(100vh-140px)]">
          {/* Left Panel - File Upload */}
          <div className="space-y-6">
            <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 shadow-xl border border-white/20">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload Documents</h2>
              
              {/* Drop Zone */}
              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 ${
                  isDragOver
                    ? 'border-indigo-400 bg-indigo-50'
                    : 'border-gray-300 hover:border-indigo-400 hover:bg-gray-50'
                }`}
              >
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-lg font-medium text-gray-700 mb-2">
                  Drop files here or click to upload
                </p>
                <p className="text-sm text-gray-500 mb-4">
                  Supports PDF, DOCX, TXT, MD, RTF, PPT, and images
                </p>
                <input
                  type="file"
                  multiple
                  accept=".pdf,.docx,.txt,.md,.rtf,.ppt,.pptx,.jpg,.jpeg,.png,.gif"
                  onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors cursor-pointer"
                >
                  Choose Files
                </label>
              </div>
            </div>

            {/* Uploaded Files */}
            {uploadedFiles.length > 0 && (
              <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 shadow-xl border border-white/20">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Uploaded Files</h3>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {uploadedFiles.map((file) => (
                    <div key={file.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-xl">
                      <div className="text-2xl">{getFileIcon(file.type)}</div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                        <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                        
                        {/* Progress Bar */}
                        {file.status !== 'completed' && file.status !== 'error' && (
                          <div className="mt-2">
                            <progress
                              className="progress-track"
                              value={file.progress}
                              max={100}
                            />
                          </div>
                        )}
                      </div>
                      
                      {/* Status Icon */}
                      <div className="flex items-center space-x-2">
                        {file.status === 'uploading' && (
                          <Loader2 className="w-4 h-4 text-indigo-600 animate-spin" />
                        )}
                        {file.status === 'processing' && (
                          <Brain className="w-4 h-4 text-indigo-600 animate-pulse" />
                        )}
                        {file.status === 'completed' && (
                          <CheckCircle2 className="w-4 h-4 text-green-600" />
                        )}
                        {file.status === 'error' && (
                          <AlertCircle className="w-4 h-4 text-red-600" />
                        )}
                        <button
                          onClick={() => removeFile(file.id)}
                          type="button"
                          aria-label={`Remove ${file.name}`}
                          className="p-1 hover:bg-gray-200 rounded-full transition-colors"
                        >
                          <X className="w-3 h-3 text-gray-400" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Panel - Flashcards */}
          <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 shadow-xl border border-white/20">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900">Generated Flashcards</h2>
              {flashcards.length > 0 && (
                <div className="text-sm text-gray-500">
                  {currentCardIndex + 1} of {flashcards.length}
                </div>
              )}
            </div>

            {flashcards.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-96 text-center">
                <Brain className="w-16 h-16 text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-500 mb-2">No flashcards yet</h3>
                <p className="text-sm text-gray-400">
                  Upload a document to start generating flashcards
                </p>
              </div>
            ) : (
              <div className="flex flex-col h-full">
                <div className="flex-1 flex items-center justify-center">
                  <Flashcard
                    data={flashcards[currentCardIndex]}
                    isFlipped={isFlipped}
                    onFlip={handleCardFlip}
                  />
                </div>
                
                {/* Navigation */}
                {flashcards.length > 1 && (
                  <div className="flex items-center justify-center space-x-4 mt-6">
                    <button
                      onClick={prevCard}
                      className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                    >
                      Previous
                    </button>
                    <button
                      onClick={nextCard}
                      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
                    >
                      Next
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FlashcardGenerator;