import React from "react";
import { ArrowRight, Sparkles } from "lucide-react";
import CardStack from "../components/CardStack";
import { useNavigate } from "react-router-dom";

const Landing: React.FC = () => {
  const navigate = useNavigate();

  // Custom particle component for better rendering/caching
  const Particles = () => (
    <div className="pointer-events-none absolute inset-0 opacity-70">
      {Array.from({ length: 40 }).map((_, i) => (
        <div
          key={i}
          className="absolute w-1 h-1 bg-white/30 rounded-full animate-float"
          style={{
            top: `${Math.random() * 100}%`,
            left: `${Math.random() * 100}%`,
            animationDuration: `${5 + Math.random() * 7}s`,
            animationDelay: `${Math.random() * 6}s`,
            opacity: Math.random() * 0.4 + 0.2,
          }}
        ></div>
      ))}
    </div>
  );

  return (
    // CHANGE 1: 'h-screen' instead of 'min-h-screen' locks it to viewport height
    // CHANGE 2: 'overflow-hidden' ensures no scrollbars appear
    <div className="h-screen w-full relative overflow-hidden font-inter bg-[#0d0f17]">

      {/* Background Gradients and Particles */}
      <Particles />

      {/* Large Glowing Blobs (Soft, Dark Futuristic Feel) */}
      <div className="absolute w-[800px] h-[800px] bg-purple-600/10 blur-[200px] rounded-full -top-40 -left-60 transform translate-z-0 animate-blob animation-delay-2000"></div>
      <div className="absolute w-[800px] h-[800px] bg-blue-600/10 blur-[200px] rounded-full bottom-0 right-0 transform translate-z-0 animate-blob animation-delay-4000"></div>

      {/* Main Content Container */}
      {/* CHANGE 3: 'h-full' ensures the container fills the screen exactly */}
      {/* CHANGE 4: Adjusted padding (pt-16) so nav doesn't overlap, but content stays centered */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 h-full flex flex-col items-center justify-center pt-16">

        {/* Navigation Bar (Simple top bar) */}
        <nav className="absolute top-0 left-0 right-0 max-w-7xl mx-auto px-6 py-6 flex justify-between items-center z-30">
          <div className="flex items-center gap-3">
            {/* Logo */}
            <div className="w-10 h-10 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl text-white flex items-center justify-center text-lg font-bold shadow-lg">
              <Sparkles className="w-5 h-5" />
            </div>
            <span className="text-white text-xl font-extrabold tracking-wider">FlashMind</span>
          </div>

          {/* Sign In CTA */}
          <button
            onClick={() => navigate("/auth")}
            className="text-white border border-white/20 px-5 py-2 rounded-xl text-sm font-medium transition-colors hover:bg-white/10"
          >
            Sign In
          </button>
        </nav>


        {/* HERO SECTION CORE */}
        {/* CHANGE 5: Removed 'mt-12' to allow true vertical centering */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-8 lg:gap-16 w-full">

          {/* LEFT SIDE TEXT */}
          <div className="flex-1 text-center md:text-left">
            <h1 className="text-5xl md:text-7xl font-extrabold text-white leading-tight mb-6 tracking-tight">
              AI-Powered Study,
              <br />
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
                Instantly Transcribed.
              </span>
            </h1>

            <p className="text-gray-300 text-lg max-w-lg mb-10 mx-auto md:mx-0">
              Upload documents, PDFs, or notes and watch them convert into interactive, study-ready flashcard decks in seconds.
            </p>

            {/* CTA Button */}
            <button
              onClick={() => navigate("/flashcards")}
              className="group bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-8 py-4 rounded-xl text-lg font-semibold flex items-center justify-center mx-auto md:mx-0 transition-all duration-300 hover:shadow-[0_0_40px_rgba(99,102,241,0.6)] transform hover:-translate-y-1"
            >
              Start Creating Flashcards
              <ArrowRight className="w-6 h-6 ml-2 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>

          {/* RIGHT SIDE 3D CARD STACK */}
          <div className="flex-1 flex justify-center items-center w-full max-w-md md:max-w-none">
            <CardStack initialTiltX={5} initialTiltY={-8} />
          </div>

        </div>
      </div>
    </div>
  );
};

export default Landing;