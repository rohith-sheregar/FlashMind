import axios from "axios";

// DIRECT CONNECTION to the Backend
export const API_URL = "http://127.0.0.1:8000/api";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
    // Auth is optional for now; endpoints are public by default.
  },
  timeout: 30000, // 30s timeout
});

export default api;
