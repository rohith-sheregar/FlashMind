import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import { useStore } from "../store/useStore";
import { Sparkles, ArrowRight, Mail, Lock, User, Loader2, CheckCircle } from "lucide-react";

const AuthPage: React.FC = () => {
    const [isLogin, setIsLogin] = useState(true);
    const [username, setUsername] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();
    const setUser = useStore((state) => state.setUser);

    const validateForm = () => {
        if (!username.trim()) return "Username is required.";
        if (!password) return "Password is required.";

        if (!isLogin) {
            if (!email.trim()) return "Email is required.";

            // Email validation
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) return "Please enter a valid email address.";

            // Username validation (alphanumeric only)
            const usernameRegex = /^[a-zA-Z0-9]+$/;
            if (!usernameRegex.test(username)) return "Username must contain only letters and numbers (no spaces or special characters).";

            // Password validation
            if (password.length < 6) return "Password must be at least 6 characters long.";
            if (/\s/.test(password)) return "Password must not contain spaces.";

            // Confirm password
            if (password !== confirmPassword) return "Passwords do not match.";
        }

        return null;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");

        const validationError = validateForm();
        if (validationError) {
            setError(validationError);
            return;
        }

        setIsLoading(true);

        try {
            if (isLogin) {
                // Login - MUST use x-www-form-urlencoded for OAuth2PasswordRequestForm
                const formData = new URLSearchParams();
                formData.append('username', username);
                formData.append('password', password);

                const response = await api.post("/auth/login", formData, {
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                });

                const { access_token, user } = response.data;
                localStorage.setItem("token", access_token);
                setUser(user);
                navigate("/flashcards");
            } else {
                // Signup - Uses JSON
                await api.post("/auth/signup", {
                    username,
                    email,
                    password,
                });
                // Auto login after signup
                const formData = new URLSearchParams();
                formData.append('username', username);
                formData.append('password', password);

                const loginResponse = await api.post("/auth/login", formData, {
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                });

                const { access_token, user } = loginResponse.data;
                localStorage.setItem("token", access_token);
                setUser(user);
                navigate("/flashcards");
            }
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || "An error occurred. Please try again.");
        } finally {
            setIsLoading(false);
        }
    };

    // Custom particle component
    const Particles = () => (
        <div className="pointer-events-none absolute inset-0 opacity-40">
            {Array.from({ length: 30 }).map((_, i) => (
                <div
                    key={i}
                    className="absolute w-1 h-1 bg-white/20 rounded-full animate-float"
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
        <div className="min-h-screen w-full relative overflow-hidden font-inter bg-[#0d0f17] flex items-center justify-center p-4">
            {/* Background Effects */}
            <Particles />
            <div className="absolute w-[600px] h-[600px] bg-purple-600/10 blur-[150px] rounded-full -top-20 -left-20 animate-blob"></div>
            <div className="absolute w-[600px] h-[600px] bg-blue-600/10 blur-[150px] rounded-full bottom-0 right-0 animate-blob animation-delay-2000"></div>

            {/* Auth Card */}
            <div className="relative z-10 w-full max-w-md">
                {/* Logo Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl shadow-lg mb-4">
                        <Sparkles className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-3xl font-extrabold text-white tracking-tight">
                        {isLogin ? "Welcome Back" : "Join FlashMind"}
                    </h1>
                    <p className="text-gray-400 mt-2">
                        {isLogin
                            ? "Sign in to continue your learning journey"
                            : "Start creating AI-powered flashcards today"}
                    </p>
                </div>

                {/* Form Container */}
                <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/20 text-red-200 p-4 rounded-xl mb-6 text-sm flex items-center">
                            <span className="mr-2">⚠️</span> {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        {!isLogin && (
                            <div className="space-y-1">
                                <label className="text-sm font-medium text-gray-300 ml-1">Email</label>
                                <div className="relative group">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <Mail className="h-5 w-5 text-gray-500 group-focus-within:text-indigo-400 transition-colors" />
                                    </div>
                                    <input
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="w-full bg-gray-900/50 border border-gray-700 rounded-xl py-3 pl-10 pr-4 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all"
                                        placeholder="name@example.com"
                                        required
                                    />
                                </div>
                            </div>
                        )}

                        <div className="space-y-1">
                            <label className="text-sm font-medium text-gray-300 ml-1">Username</label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <User className="h-5 w-5 text-gray-500 group-focus-within:text-indigo-400 transition-colors" />
                                </div>
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="w-full bg-gray-900/50 border border-gray-700 rounded-xl py-3 pl-10 pr-4 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all"
                                    placeholder="Enter your username"
                                    required
                                />
                            </div>
                        </div>

                        <div className="space-y-1">
                            <label className="text-sm font-medium text-gray-300 ml-1">Password</label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Lock className="h-5 w-5 text-gray-500 group-focus-within:text-indigo-400 transition-colors" />
                                </div>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full bg-gray-900/50 border border-gray-700 rounded-xl py-3 pl-10 pr-4 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all"
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                        </div>

                        {!isLogin && (
                            <div className="space-y-1">
                                <label className="text-sm font-medium text-gray-300 ml-1">Confirm Password</label>
                                <div className="relative group">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <CheckCircle className="h-5 w-5 text-gray-500 group-focus-within:text-indigo-400 transition-colors" />
                                    </div>
                                    <input
                                        type="password"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        className="w-full bg-gray-900/50 border border-gray-700 rounded-xl py-3 pl-10 pr-4 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all"
                                        placeholder="Confirm your password"
                                        required
                                    />
                                </div>
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold py-3.5 px-4 rounded-xl transition-all duration-200 transform hover:-translate-y-0.5 hover:shadow-lg hover:shadow-indigo-500/25 flex items-center justify-center disabled:opacity-70 disabled:cursor-not-allowed"
                        >
                            {isLoading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <>
                                    {isLogin ? "Sign In" : "Create Account"}
                                    <ArrowRight className="ml-2 w-5 h-5" />
                                </>
                            )}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <p className="text-gray-400 text-sm">
                            {isLogin ? "Don't have an account?" : "Already have an account?"}
                            <button
                                onClick={() => {
                                    setIsLogin(!isLogin);
                                    setError("");
                                    setConfirmPassword("");
                                }}
                                className="ml-2 text-indigo-400 hover:text-indigo-300 font-semibold transition-colors focus:outline-none"
                            >
                                {isLogin ? "Sign Up" : "Log In"}
                            </button>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AuthPage;
