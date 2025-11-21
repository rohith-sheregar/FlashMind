// src/pages/Login.tsx
import React, { useState } from "react";

type LoginResponse = {
  token?: string;
  message?: string;
  success: boolean;
};

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setInfo(null);

    if (!email.trim() || !password) {
      setError("Please enter both email and password.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data: LoginResponse = await res.json();

      if (!res.ok || !data.success) {
        setError(data.message || "Login failed");
      } else {
        // Save token depending on remember
        if (data.token) {
          if (remember) localStorage.setItem("token", data.token);
          else sessionStorage.setItem("token", data.token);
        }
        setInfo("Login successful — redirecting...");
        // Replace with your navigation / redirect
        setTimeout(() => {
          window.location.href = "/"; // go to landing or study mode
        }, 700);
      }
    } catch (err) {
      console.error(err);
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center bg-gray-50"
      // example referencing your uploaded image path as decorative background:
      // (Your environment may not serve this path directly; this is a reference)
      style={{
        backgroundImage:
          "linear-gradient(180deg, rgba(99,102,241,0.06), rgba(99,102,241,0.02)), url('/mnt/data/Screenshot 2025-11-21 122710.png')",
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      <main className="max-w-md w-full p-8 bg-white/90 backdrop-blur-md rounded-2xl shadow-xl border border-gray-100">
        <header className="mb-6 text-center">
          <div className="mx-auto w-16 h-16 rounded-full flex items-center justify-center bg-gradient-to-tr from-indigo-500 to-violet-400 text-white text-2xl font-bold shadow">
            S
          </div>
          <h1 className="mt-4 text-2xl font-semibold text-gray-800">Welcome back</h1>
          <p className="mt-1 text-sm text-gray-500">
            Sign in to continue to your study dashboard
          </p>
        </header>

        <form onSubmit={handleSubmit} className="space-y-4" aria-describedby="form-help">
          {error && (
            <div role="alert" className="text-sm text-red-700 bg-red-50 p-2 rounded">
              {error}
            </div>
          )}
          {info && (
            <div role="status" className="text-sm text-green-700 bg-green-50 p-2 rounded">
              {info}
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-1 block w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-300 outline-none"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="mt-1 block w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-300 outline-none"
              placeholder="••••••••"
            />
            <div className="flex justify-end mt-1">
              <a href="/forgot" className="text-xs text-indigo-600 hover:underline">
                Forgot password?
              </a>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <label className="inline-flex items-center text-sm select-none">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="form-checkbox h-4 w-4 text-indigo-600 rounded"
              />
              <span className="ml-2 text-gray-700">Remember me</span>
            </label>

            <div>
              <a href="/signup" className="text-sm text-gray-600 hover:underline">
                Create account
              </a>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 rounded-lg text-white font-semibold bg-gradient-to-r from-indigo-600 to-violet-500 hover:from-indigo-700 hover:to-violet-600 focus:outline-none focus:ring-4 focus:ring-indigo-200 disabled:opacity-60"
            aria-busy={loading}
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>

          <div className="flex items-center my-2">
            <div className="flex-1 h-px bg-gray-200" />
            <div className="px-3 text-sm text-gray-500">or continue with</div>
            <div className="flex-1 h-px bg-gray-200" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => alert("Social login placeholder")}
              className="flex items-center justify-center gap-2 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none"
            >
              {/* Google icon svg */}
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
                <path d="M21 12.2c0-.7-.1-1.4-.3-2H12v3.8h5.1c-.2 1-.8 1.9-1.6 2.5v2h2.6c1.6-1.4 2.5-3.6 2.5-6.3z" fill="#4285F4"/>
                <path d="M12 22c2.7 0 4.9-.9 6.6-2.4l-2.6-2c-1 .7-2.4 1.2-4 1.2-3 0-5.6-2-6.5-4.7H3v2.9C4 20.2 7.7 22 12 22z" fill="#34A853"/>
                <path d="M5.5 13.1A7.6 7.6 0 015 12c0-.4.1-.9.1-1.3V8.1H3.1A10 10 0 003 12c0 1.2.2 2.4.6 3.5L5.5 13.1z" fill="#FBBC05"/>
                <path d="M12 6.5c1.4 0 2.6.5 3.5 1.4l2.6-2.6C16.9 3.9 14.8 3 12 3 7.7 3 4 4.8 3.1 8.1L5.5 10c.9-2.7 3.5-4.5 6.5-4.5z" fill="#EA4335"/>
              </svg>
              Google
            </button>
            <button
              type="button"
              onClick={() => alert("Guest login")}
              className="flex items-center justify-center gap-2 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none"
            >
              Guest
            </button>
          </div>
        </form>

        <footer className="mt-6 text-center text-xs text-gray-400">
          <p id="form-help">Your credentials are sent over HTTPS and stored securely.</p>
        </footer>
      </main>
    </div>
  );
}
