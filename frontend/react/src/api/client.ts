import axios from "axios";

// VITE_API_BASE is set in .env or Railway env vars
// Falls back to localhost:8000 — the FastAPI backend
// Streamlit also talks to the same backend on :8000
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export const api = axios.create({ baseURL: API_BASE });

// Inject JWT token on every request from localStorage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401: clear token and redirect to /login
// This matches Streamlit behaviour: api() returns None and triggers st.rerun() to login page
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);
