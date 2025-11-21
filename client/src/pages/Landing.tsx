import React, { useState } from "react";
import { Brain, Image, FileText, Sparkles, ArrowRight, Upload, Zap } from "lucide-react";

interface LandingProps {
  onNavigate: (_view: 'flashcards' | 'images') => void;
}

const Landing: React.FC<LandingProps> = ({ onNavigate }) => {
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 relative overflow-hidden">
      {/* Background Animation */}
      <div className="absolute inset-0">
        <div className="absolute top-20 left-20 w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob"></div>
        <div className="absolute top-40 right-20 w-72 h-72 bg-yellow-300 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-40 w-72 h-72 bg-pink-300 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-4000"></div>
      </div>

      {/* Header */}
      <header className="relative z-10 flex items-center justify-between p-6">
        <div className="flex items-center space-x-3">
          {/* Logo placeholder area */}
          <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div className="flex flex-col">
            <h1 className="text-2xl font-bold text-gray-900">Flashmind</h1>
            <span className="text-xs text-gray-500">AI Flashcard Studio</span>
          </div>
        </div>
        <div className="text-sm text-gray-500">
          AI-Powered Learning Platform
        </div>
      </header>

      {/* Main Content */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-[calc(100vh-120px)] p-4">
        {/* Hero Section */}
        <div className="text-center mb-16 max-w-4xl">
          <div className="inline-flex items-center bg-white/80 backdrop-blur-sm rounded-full px-4 py-2 mb-6 shadow-lg border border-white/20">
            <Zap className="w-4 h-4 text-indigo-500 mr-2" />
            <span className="text-sm font-medium text-gray-700">Powered by Advanced AI</span>
          </div>
          
          <h1 className="text-6xl md:text-7xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 mb-6 leading-tight">
            Transform Learning
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-600 mb-4 leading-relaxed">
            Turn any document into interactive flashcards with the power of AI
          </p>
          
          <p className="text-lg text-gray-500 max-w-2xl mx-auto">
            Upload PDFs, images, documents, and more. Our AI generates up to 90 high-quality flashcards 
            to accelerate your learning journey.
          </p>
        </div>

        {/* Feature Cards */}
        <div className="grid md:grid-cols-2 gap-8 max-w-4xl w-full">
          {/* Generate Flashcards Card */}
          <div
            className={`group relative overflow-hidden bg-white/80 backdrop-blur-lg rounded-3xl p-8 shadow-xl border border-white/20 cursor-pointer transition-all duration-500 hover:scale-105 ${
              hoveredCard === 'flashcards' ? 'shadow-2xl' : ''
            }`}
            onMouseEnter={() => setHoveredCard('flashcards')}
            onMouseLeave={() => setHoveredCard(null)}
            onClick={() => onNavigate('flashcards')}
          >
            {/* Animated Background */}
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
            
            {/* Floating Elements */}
            <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-all duration-500 transform translate-x-2 group-hover:translate-x-0">
              <ArrowRight className="w-6 h-6 text-indigo-500" />
            </div>

            <div className="relative z-10">
              {/* Icon */}
              <div className="w-16 h-16 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <Brain className="w-8 h-8 text-white" />
              </div>

              {/* Content */}
              <h3 className="text-2xl font-bold text-gray-900 mb-4 group-hover:text-indigo-600 transition-colors">
                Generate Flashcards
              </h3>
              
              <p className="text-gray-600 mb-6 leading-relaxed">
                Upload your study materials and watch as our AI creates intelligent flashcards 
                with questions and answers tailored to your content.
              </p>

              {/* Features */}
              <div className="space-y-2 mb-6">
                <div className="flex items-center text-sm text-gray-500">
                  <FileText className="w-4 h-4 mr-2 text-indigo-500" />
                  PDF, DOCX, TXT, MD, RTF, PPT support
                </div>
                <div className="flex items-center text-sm text-gray-500">
                  <Upload className="w-4 h-4 mr-2 text-indigo-500" />
                  Up to 90 flashcards per document
                </div>
                <div className="flex items-center text-sm text-gray-500">
                  <Zap className="w-4 h-4 mr-2 text-indigo-500" />
                  Real-time generation & preview
                </div>
              </div>

              {/* CTA */}
              <div className="flex items-center text-indigo-600 font-medium group-hover:text-indigo-700 transition-colors">
                Start Creating
                <ArrowRight className="w-4 h-4 ml-2 transform group-hover:translate-x-1 transition-transform" />
              </div>
            </div>

            {/* Hover Effect Overlay */}
            <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          </div>

          {/* Generate Images Card */}
          <div
            className={`group relative overflow-hidden bg-white/80 backdrop-blur-lg rounded-3xl p-8 shadow-xl border border-white/20 cursor-pointer transition-all duration-500 hover:scale-105 ${
              hoveredCard === 'images' ? 'shadow-2xl' : ''
            }`}
            onMouseEnter={() => setHoveredCard('images')}
            onMouseLeave={() => setHoveredCard(null)}
            onClick={() => onNavigate('images')}
          >
            {/* Animated Background */}
            <div className="absolute inset-0 bg-gradient-to-br from-pink-500/10 to-orange-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
            
            {/* Floating Elements */}
            <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-all duration-500 transform translate-x-2 group-hover:translate-x-0">
              <ArrowRight className="w-6 h-6 text-pink-500" />
            </div>

            <div className="relative z-10">
              {/* Icon */}
              <div className="w-16 h-16 bg-gradient-to-r from-pink-500 to-orange-500 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <Image className="w-8 h-8 text-white" />
              </div>

              {/* Content */}
              <h3 className="text-2xl font-bold text-gray-900 mb-4 group-hover:text-pink-600 transition-colors">
                Generate Images
              </h3>
              
              <p className="text-gray-600 mb-6 leading-relaxed">
                Create visual learning aids and diagrams from your text content. 
                Perfect for visual learners and complex concepts.
              </p>

              {/* Features */}
              <div className="space-y-2 mb-6">
                <div className="flex items-center text-sm text-gray-500">
                  <Sparkles className="w-4 h-4 mr-2 text-pink-500" />
                  AI-generated illustrations
                </div>
                <div className="flex items-center text-sm text-gray-500">
                  <Brain className="w-4 h-4 mr-2 text-pink-500" />
                  Concept visualization
                </div>
                <div className="flex items-center text-sm text-gray-500 opacity-50">
                  <Zap className="w-4 h-4 mr-2 text-pink-500" />
                  Coming Soon
                </div>
              </div>

              {/* CTA */}
              <div className="flex items-center text-pink-600 font-medium opacity-50">
                Coming Soon
                <ArrowRight className="w-4 h-4 ml-2" />
              </div>
            </div>

            {/* Hover Effect Overlay */}
            <div className="absolute inset-0 bg-gradient-to-r from-pink-500/5 to-orange-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <p className="text-gray-500 mb-4">
            Join thousands of students already using FlashMind
          </p>
          <div className="flex items-center justify-center space-x-8 text-sm text-gray-400">
            <div className="flex items-center">
              <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
              95% Accuracy Rate
            </div>
            <div className="flex items-center">
              <div className="w-2 h-2 bg-blue-400 rounded-full mr-2"></div>
              Real-time Processing
            </div>
            <div className="flex items-center">
              <div className="w-2 h-2 bg-purple-400 rounded-full mr-2"></div>
              Multiple Formats
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Landing;
