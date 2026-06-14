import { createContext, useContext, useEffect, useState } from "react";
import { api } from "@/api/client";
import { useToast } from "@/context/ToastContext";
import { useInactivityTimer } from "@/hooks/useInactivityTimer";
import type { User } from "@/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue>({} as AuthContextValue);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  // On mount: restore session from localStorage token
  // Equivalent to Streamlit's token validation block that calls GET /auth/me on every page load
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      api
        .get<User>("/auth/me")
        .then((r) => setUser(r.data))
        .catch(() => {
          // Token invalid or expired — clear it
          localStorage.removeItem("token");
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const { data } = await api.post<{ access_token: string }>("/auth/login", {
      email,
      password,
    });
    localStorage.setItem("token", data.access_token);
    // Fetch full user object — includes is_admin, onboarding_complete
    // Matches Streamlit: sets user_email, user_is_admin, onboarding_complete in session_state
    const me = await api.get<User>("/auth/me");
    setUser(me.data);
  };

  const register = async (email: string, password: string) => {
    await api.post("/auth/register", { email, password });
    // Caller redirects to login — same as Streamlit registration flow
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
    window.location.href = "/login";
  };

  // Called by OnboardingWizard after completing setup
  // Refreshes user object so onboarding_complete becomes true
  const refreshUser = async () => {
    const me = await api.get<User>("/auth/me");
    setUser(me.data);
  };

  // Auto-logout after 5 minutes of inactivity; warn at 4 minutes
  useInactivityTimer({
    enabled:   !!user,
    warningMs: 4 * 60 * 1000,
    timeoutMs: 5 * 60 * 1000,
    onWarn:    () => toast(
      "Your session expires in 1 minute — click anywhere to stay logged in",
      { type: "warning", icon: "⏱️" }
    ),
    onTimeout: logout,
  });

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
