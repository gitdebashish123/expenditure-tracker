import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider }    from "@/context/AuthContext";
import { ThemeProvider }   from "@/context/ThemeContext";
import { ToastProvider }   from "@/context/ToastContext";
import { ProtectedRoute }  from "@/components/layout/ProtectedRoute";
import { LoginPage }       from "@/pages/LoginPage";
import { DashboardPage }   from "@/pages/DashboardPage";
import { AccountPage }     from "@/pages/AccountPage";

/**
 * Root application component
 *
 * Provider order:
 *   ThemeProvider  → sets dark/light class on <html>
 *     AuthProvider → manages JWT token + user state
 *       ToastProvider → in-app notification stack (replaces st.toast)
 *         BrowserRouter → React Router
 *
 * Routes:
 *   /login    → LoginPage   (public)
 *   /         → DashboardPage (protected — main app)
 *   /account  → AccountPage   (protected — change password, delete account)
 *   *         → redirect to /
 */
export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ToastProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <DashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/account"
                element={
                  <ProtectedRoute>
                    <AccountPage />
                  </ProtectedRoute>
                }
              />
              {/* Catch-all → redirect to home */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </ToastProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
