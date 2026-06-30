import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Mail, Lock } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { PasswordStrengthBar } from "@/components/shared/PasswordStrengthBar";

/**
 * Login / Register page
 *
 * Streamlit reference: show_login_page() in frontend/app.py
 *
 * Key improvements over Streamlit:
 * - PasswordStrengthBar updates live on every keystroke (no form submit needed)
 * - Token stored in localStorage — survives browser refresh
 * - Email regex validated client-side before API call
 * - Single page with mode toggle (no separate Streamlit "show_register" session state)
 */
export function LoginPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showForgotMsg, setShowForgotMsg] = useState(false);

  const emailValid = /^[^@]+@[^@]+\.[^@]+$/.test(email);

  const switchMode = (next: "login" | "register") => {
    setMode(next);
    setError(null);
    setSuccess(null);
    setShowForgotMsg(false);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please enter your email and password.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
      navigate("/");
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } }).response?.status;
      if (status === 401) setError("Invalid email or password.");
      else if (status === 403) setError("Account disabled — contact administrator.");
      else setError("Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) { setError("Please fill in all fields."); return; }
    if (!emailValid)          { setError("Please enter a valid email address."); return; }
    if (password.length < 8)  { setError("Password must be at least 8 characters."); return; }
    if (password !== confirm)  { setError("Passwords do not match."); return; }

    setLoading(true);
    setError(null);
    try {
      await register(email, password);
      // Set success THEN switch mode manually — switchMode() would wipe the message
      setSuccess("\u2705 Account created! Please sign in.");
      setMode("login");
      setError(null);
      setPassword("");
      setConfirm("");
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(detail ?? "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  const inputCls =
    "w-full bg-dark-card2 border border-white/10 rounded-xl px-4 py-3 text-white " +
    "placeholder-white/30 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent " +
    "transition-colors text-sm";

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden"
         style={{ backgroundColor: 'var(--bg)' }}>

      {/* Background video — muted product glimpse loop */}
      <div className="login-video-bg" aria-hidden="true">
        <video autoPlay loop muted playsInline preload="auto">
          <source src="/wallet-mantra-glimpse.mp4" type="video/mp4" />
        </video>
      </div>
      <div className="login-scrim" aria-hidden="true" />
      <span className="login-muted-pill">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
          <line x1="23" y1="9" x2="17" y2="15" />
          <line x1="17" y1="9" x2="23" y2="15" />
        </svg>
        Muted
      </span>

      <div className="w-full max-w-sm relative" style={{ zIndex: 2 }}>

        {/* Logo */}
        <div className="text-center mb-8 login-fadein d1">
          <img
            src="/wallet-mantra-logo.png"
            alt="Wallet Mantra"
            className="login-logo-mark mx-auto mb-3"
          />
          <h1 className="font-syne text-2xl font-bold text-white tracking-tight"
              style={{ textShadow: '0 2px 12px rgba(0,0,0,0.6)' }}>
            Wallet Mantra
          </h1>
          <p className="text-sm text-white/40 mt-1">
            Beyond expense tracking
          </p>
        </div>

        {/* Feedback banners + forms — glass card over the video */}
        <div className="login-fadein d2 login-glass-card">

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm">
            {success}
          </div>
        )}

        {/* Login form */}
        {mode === "login" && (
          <form onSubmit={handleLogin} className="space-y-3">
            <div className="login-field">
              <Mail size={16} />
              <input
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={inputCls}
                autoComplete="email"
                autoFocus
              />
            </div>
            <div className="login-field">
              <Lock size={16} />
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={inputCls}
                autoComplete="current-password"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-accent to-accent2 text-white font-syne font-semibold py-3 rounded-xl disabled:opacity-50 transition-opacity"
            >
              {loading ? "Signing in…" : "Sign In"}
            </button>
          </form>
        )}

        {/* Register form */}
        {mode === "register" && (
          <form onSubmit={handleRegister} className="space-y-3">
            <input
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputCls}
              autoComplete="email"
              autoFocus
            />
            <div>
              <input
                type="password"
                placeholder="Password (min 8 characters)"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={inputCls}
                autoComplete="new-password"
              />
              {/* Live strength bar — updates on every keystroke */}
              <PasswordStrengthBar password={password} />
            </div>
            <input
              type="password"
              placeholder="Confirm Password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              className={inputCls}
              autoComplete="new-password"
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-accent to-accent2 text-white font-syne font-semibold py-3 rounded-xl disabled:opacity-50 transition-opacity"
            >
              {loading ? "Creating…" : "Create Account"}
            </button>
          </form>
        )}

        </div>
        {/* end glass card */}

        {/* Forgot password — login mode only */}
        {mode === "login" && (
          <>
            <button
              type="button"
              onClick={() => setShowForgotMsg(v => !v)}
              className="mt-2 w-full text-sm text-indigo-400/70 hover:text-indigo-300 transition-colors py-1"
            >
              Forgot password?
            </button>
            {showForgotMsg && (
              <div className="mt-1 p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/30
                              text-indigo-300 text-sm flex items-start justify-between gap-2">
                <span>To reset your password, please contact your administrator.</span>
                <button
                  type="button"
                  onClick={() => setShowForgotMsg(false)}
                  className="text-indigo-400/60 hover:text-indigo-300 flex-shrink-0 leading-none"
                  aria-label="Dismiss"
                >
                  ×
                </button>
              </div>
            )}
          </>
        )}

        {/* Mode toggle */}
        <button
          onClick={() => switchMode(mode === "login" ? "register" : "login")}
          className="mt-4 w-full text-sm py-2 transition-colors"
          style={{ color: "var(--text-muted)" }}
        >
          {mode === "login" ? (
            <>Don't have an account?{" "}
              <span className="text-indigo-400 hover:text-indigo-300 font-medium">Create one</span>
            </>
          ) : (
            <>Already have an account?{" "}
              <span className="text-indigo-400 hover:text-indigo-300 font-medium">Sign In</span>
            </>
          )}
        </button>

        {/* Privacy notice — matches Streamlit footer */}
        <p className="text-center text-xs text-white/20 mt-6">
          By signing in you acknowledge our{" "}
          <a
            href="https://github.com/gitdebashish123/expenditure-tracker/blob/main/PRIVACY.md"
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-400 hover:text-indigo-300"
          >
            Privacy Notice
          </a>
        </p>

      </div>
    </div>
  );
}
