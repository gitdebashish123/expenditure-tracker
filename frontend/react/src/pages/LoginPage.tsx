import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Mail, Lock, Sparkles, CheckCircle, XCircle, Eye, EyeOff, Sun, Bookmark, HeartHandshake } from "lucide-react";
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
  const [showPw, setShowPw] = useState(false);

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
    "placeholder-white/30 focus:outline-none transition-colors text-sm";

  return (
    <div className="login-split">

      {/* Left visual panel — desktop/tablet only (hidden < 900px) */}
      <div className="login-visual">

        <div className="login-brand-row login-fadein d1">
          <img
            src="/wallet-mantra-logo.png"
            alt="Wallet Mantra"
            className="login-logo-mark"
            style={{ width: 56, height: 56 }}
          />
          <div>
            <h1 className="font-syne text-xl font-bold text-white tracking-tight">
              Wallet Mantra
            </h1>
            <p className="text-xs text-white/50 mt-0.5">Beyond expense tracking</p>
          </div>
        </div>

        <h2 className="login-hero-headline login-fadein d1">
          Your <span className="text-indigo-400">AI</span> money companion
        </h2>

        <div className="text-left space-y-0.5 login-fadein d1">
          <p className="text-sm text-white/70">Build awareness.</p>
          <p className="text-sm text-white/70">Reduce impulse spending.</p>
          <p className="text-sm text-white/70">
            Save <span className="text-emerald-400 font-medium">consistently.</span>
          </p>
        </div>

        {/* Feature list — five rows, gold-outline icon chips (Spec 35 Item 2) */}
        <div className="login-feature-list login-fadein d1">
          {[
            { Icon: Sparkles, label: "Tara, your AI money companion" },
            { Icon: Sun, label: "Daily mantra & monthly story" },
            { Icon: Bookmark, label: "Fixed commitments & reminders" },
            { Icon: HeartHandshake, label: "Insights & peace-of-mind score" },
            { Icon: Lock, label: "Private & secure" },
          ].map(({ Icon, label }) => (
            <div key={label} className="login-feature">
              <span className="login-feature-chip"><Icon size={16} style={{ color: "var(--gold)" }} /></span>
              <span className="text-sm text-white/70">{label}</span>
            </div>
          ))}
        </div>

        {/* Insight strip — illustrative sample data only (D2/D4) */}
        <div className="login-fadein d2">
          <div className="login-insight-strip">
            <div className="login-insight-card">
              <span className="text-xs text-white/50">Saved this month</span>
              <span className="text-emerald-400 font-semibold">+₹8,450</span>
            </div>
            <div className="login-insight-card">
              <span className="text-xs text-white/50">Peace of mind</span>
              <span className="text-indigo-400 font-semibold">Excellent</span>
            </div>
            <div className="login-insight-card">
              <span className="text-xs text-white/50">Insight</span>
              <span style={{ color: "var(--gold)" }} className="font-semibold">−18% on Food</span>
            </div>
          </div>
          <p className="text-center text-[10px] text-white/30 mt-1">Illustrative preview data</p>
        </div>

        {/* Framed preview card — fixed 16:10 aspect ratio, never full-bleed */}
        <div className="login-preview-card login-fadein d2">
          <video autoPlay loop muted playsInline preload="auto" aria-hidden="true">
            <source src="/wallet-mantra-glimpse.mp4" type="video/mp4" />
          </video>
          <span className="login-preview-pill">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <polygon points="6 4 20 12 6 20" />
            </svg>
            Product preview
          </span>
        </div>

        {/* Rotating quote — in-flow at the bottom of the column */}
        <div className="login-quote-flow" aria-live="polite">
          <p className="login-quote">
            "A budget is telling your money where to go, instead of wondering where it went."
          </p>
          <p className="login-quote">
            "Small daily savings build into your biggest financial wins."
          </p>
          <p className="login-quote">
            "Track it once, and watch every rupee start working for you."
          </p>
        </div>
      </div>

      {/* Right panel — sign in / register form */}
      <div className="login-form-panel">
      <div className="w-full max-w-md relative login-form-card">

        {/* Logo — mobile only (left panel is hidden < 900px) */}
        <div className="text-center mb-8 login-fadein d1">
          <img
            src="/wallet-mantra-logo.png"
            alt="Wallet Mantra"
            className="login-logo-mark-sm mx-auto mb-3 md:hidden"
          />
          <h1 className="font-syne text-2xl font-bold tracking-tight md:hidden" style={{ color: 'var(--text)' }}>
            Wallet Mantra
          </h1>
          <p className="text-sm mt-1 md:hidden" style={{ color: 'var(--text-muted)' }}>
            Beyond expense tracking
          </p>
          <h2 className="font-syne text-2xl font-bold tracking-tight hidden md:block" style={{ color: 'var(--text)' }}>
            Welcome back
          </h2>
          <p className="text-sm mt-1 hidden md:block" style={{ color: 'var(--text-muted)' }}>
            Sign in to Wallet Mantra
          </p>
        </div>

        {/* Feedback banners + forms */}
        <div className="login-fadein d2">

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
            <div>
              <label htmlFor="login-email" className="block text-xs text-white/50 mb-1">
                Email
              </label>
              <div className="login-field">
                <Mail size={16} />
                <input
                  id="login-email"
                  type="email"
                  placeholder="your@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={inputCls}
                  autoComplete="email"
                  autoFocus
                />
                {email.length > 0 && (
                  emailValid
                    ? <CheckCircle size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-emerald-400 pointer-events-none" />
                    : <XCircle   size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-red-400   pointer-events-none" />
                )}
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <label htmlFor="login-pw" className="block text-xs text-white/50">
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => setShowForgotMsg(v => !v)}
                  className="text-xs text-indigo-400/70 hover:text-indigo-300 transition-colors"
                >
                  Forgot password?
                </button>
              </div>
              <div className="login-field">
                <Lock size={16} />
                <input
                  id="login-pw"
                  type={showPw ? "text" : "password"}
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={inputCls}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30
                             hover:text-white/60 transition-colors"
                  aria-label={showPw ? "Hide password" : "Show password"}
                >
                  {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="login-cta-gold w-full font-syne font-semibold py-3 rounded-xl disabled:opacity-50 transition-colors"
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
              className="login-cta-gold w-full font-syne font-semibold py-3 rounded-xl disabled:opacity-50 transition-colors"
            >
              {loading ? "Creating…" : "Create Account"}
            </button>
          </form>
        )}

        </div>
        {/* end glass card */}

        {/* Forgot-password dismissible message — outside the form, mode-gated */}
        {mode === "login" && showForgotMsg && (
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

        {/* Trust footer strip */}
        <div className="flex justify-center gap-2 mt-4 pt-3 border-t border-white/10">
          <span className="flex items-center gap-1.5 text-[11px] text-white/55">
            <Lock size={11} style={{ color: "var(--gold)" }} />
            Your data stays private and encrypted
          </span>
        </div>

        {/* Privacy notice — matches Streamlit footer */}
        <p className="text-center text-xs text-white/20 mt-6">
          By signing in you acknowledge our{" "}
          <a
            href="/privacy.html"
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-400 hover:text-indigo-300"
          >
            Privacy notice
          </a>
        </p>

      </div>
      </div>
    </div>
  );
}
