import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

/**
 * Wraps routes that require authentication.
 * Redirects to /login if no user is present.
 * Shows a blank dark screen while restoring session from localStorage.
 */
export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  // Still checking localStorage token — show blank dark screen (no flash)
  if (loading) {
    return <div className="min-h-screen bg-dark-bg" />;
  }

  // No token or invalid token — redirect to login
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
