import axios from "axios";

// DIRECT CONNECTION to the Backend
const API_URL = "http://127.0.0.1:8000/api";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
    // DO NOT Add Authorization Headers yet. The backend is public.
  },
  timeout: 30000, // 30s timeout
});

export default api;
