import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/api/client";
import { PasswordStrengthBar } from "@/components/shared/PasswordStrengthBar";
import { ArrowLeft, Key, AlertTriangle } from "lucide-react";

/**
 * AccountPage — Change Password + Delete Account
 *
 * Streamlit ref: Change Password expander + Danger Zone expander
 *   inside with tab5: in frontend/app.py
 *
 * Improvement over Streamlit:
 *   - Dedicated /account route — bookmarkable, accessible from ProfileDropdown
 *   - PasswordStrengthBar updates live on every keystroke
 *   - Delete confirmation is a two-step inline flow (button → input → confirm)
 *   - No page rerun needed for any interaction
 */
export function AccountPage() {
  const { user, logout } = useAuth();

  // ── Change password state ────────────────────────────────────────────────
  const [curPw,     setCurPw]     = useState("");
  const [newPw,     setNewPw]     = useState("");
  const [confPw,    setConfPw]    = useState("");
  const [pwError,   setPwError]   = useState<string | null>(null);
  const [pwSuccess, setPwSuccess] = useState(false);
  const [pwLoading, setPwLoading] = useState(false);

  // ── Delete account state ─────────────────────────────────────────────────
  const [delConfirm,    setDelConfirm]    = useState("");
  const [delError,      setDelError]      = useState<string | null>(null);
  const [delLoading,    setDelLoading]    = useState(false);
  const [showDelDialog, setShowDelDialog] = useState(false);

  // ── Handlers ─────────────────────────────────────────────────────────────

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwError(null);
    if (!curPw || !newPw || !confPw) {
      setPwError("Please fill in all fields.");
      return;
    }
    if (newPw.length < 8) {
      setPwError("New password must be at least 8 characters.");
      return;
    }
    if (newPw !== confPw) {
      setPwError("New passwords do not match.");
      return;
    }
    setPwLoading(true);
    try {
      await api.put("/auth/password", {
        current_password: curPw,
        new_password:     newPw,
      });
      setPwSuccess(true);
      setCurPw(""); setNewPw(""); setConfPw("");
      setTimeout(() => setPwSuccess(false), 3000);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })
        .response?.data?.detail;
      setPwError(detail ?? "Password change failed. Check your current password.");
    } finally {
      setPwLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (delConfirm !== "DELETE") {
      setDelError("Please type DELETE (all caps) to confirm.");
      return;
    }
    setDelLoading(true);
    try {
      await api.delete("/auth/account", { data: { confirmation: "DELETE" } });
      logout();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })
        .response?.data?.detail;
      setDelError(detail ?? "Deletion failed.");
      setDelLoading(false);
    }
  };

  const lastLogin = user?.last_login
    ? new Date(user.last_login).toLocaleString("en-IN", {
        day: "numeric", month: "short", year: "numeric",
        hour: "2-digit", minute: "2-digit",
      })
    : "First login";

  const inputCls =
    "w-full bg-dark-card2 border border-white/10 rounded-xl px-4 py-3 " +
    "text-white text-sm placeholder-white/30 focus:border-accent " +
    "focus:outline-none transition-colors";

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    // ⚠️ inline style not bg-dark-bg class — CSS vars must propagate here
    <div className="min-h-screen" style={{ backgroundColor: "var(--bg)" }}>
      <div className="max-w-lg mx-auto px-4 py-6">

        {/* Back navigation */}
        <Link
          to="/"
          className="flex items-center gap-2 text-sm mb-6 transition-colors hover:text-white"
          style={{ color: "var(--text-sub)" }}
        >
          <ArrowLeft size={16} /> Back to app
        </Link>

        {/* Page title */}
        <h1 className="font-syne font-bold text-white text-xl mb-1">My Account</h1>
        <p className="text-sm mb-6" style={{ color: "var(--text-sub)" }}>
          Signed in as{" "}
          <span className="text-white font-medium">{user?.email}</span>
          {" · "}Last login: {lastLogin}
        </p>

        {/* ── Change Password card ──────────────────────── */}
        <div className="bg-dark-card border border-white/10 rounded-2xl p-5 mb-4">
          <div className="flex items-center gap-2 mb-4">
            <Key size={16} className="text-indigo-400" />
            <h2 className="font-syne font-semibold text-white">Change Password</h2>
          </div>

          {/* Success */}
          {pwSuccess && (
            <div className="mb-4 p-3 rounded-xl bg-emerald-500/10 border
                            border-emerald-500/30 text-emerald-300 text-sm">
              ✅ Password changed successfully.
            </div>
          )}

          {/* Error */}
          {pwError && (
            <div className="mb-4 p-3 rounded-xl bg-red-500/10 border
                            border-red-500/30 text-red-300 text-sm">
              {pwError}
            </div>
          )}

          <form onSubmit={handlePasswordChange} className="space-y-3">
            <input
              type="password"
              placeholder="Current password"
              value={curPw}
              onChange={e => setCurPw(e.target.value)}
              autoComplete="current-password"
              className={inputCls}
            />

            <div>
              <input
                type="password"
                placeholder="New password (min 8 characters)"
                value={newPw}
                onChange={e => setNewPw(e.target.value)}
                autoComplete="new-password"
                className={inputCls}
              />
              {/* Live strength bar — updates on every keystroke */}
              <PasswordStrengthBar password={newPw} />
            </div>

            <input
              type="password"
              placeholder="Confirm new password"
              value={confPw}
              onChange={e => setConfPw(e.target.value)}
              autoComplete="new-password"
              className={inputCls}
            />

            <button
              type="submit"
              disabled={pwLoading}
              className="w-full bg-gradient-to-r from-accent to-accent2 text-white
                         font-syne font-semibold py-3 rounded-xl text-sm
                         disabled:opacity-50 transition-opacity"
            >
              {pwLoading ? "Changing…" : "🔒 Change Password"}
            </button>
          </form>
        </div>

        {/* ── Danger Zone card ──────────────────────────── */}
        <div className="bg-red-500/5 border border-red-500/20 rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle size={16} className="text-red-400" />
            <h2 className="font-syne font-semibold text-red-400">Danger Zone</h2>
          </div>
          <p className="text-sm mb-4" style={{ color: "var(--text-sub)" }}>
            Permanently delete your account and all data. This cannot be undone.
          </p>

          {!showDelDialog ? (
            <button
              onClick={() => setShowDelDialog(true)}
              className="w-full border border-red-500/40 text-red-400
                         hover:bg-red-500/10 py-2.5 rounded-xl text-sm
                         font-semibold transition-colors"
            >
              Delete My Account
            </button>
          ) : (
            <div className="space-y-3">
              {delError && (
                <div className="p-3 rounded-xl bg-red-500/10 border
                                border-red-500/30 text-red-300 text-sm">
                  {delError}
                </div>
              )}

              <p className="text-sm" style={{ color: "var(--text-sub)" }}>
                Type{" "}
                <code className="text-red-400 bg-red-500/10 px-1.5 py-0.5 rounded text-xs">
                  DELETE
                </code>{" "}
                to confirm:
              </p>

              <input
                value={delConfirm}
                onChange={e => setDelConfirm(e.target.value)}
                placeholder="DELETE"
                className="w-full bg-dark-card2 border border-red-500/30 rounded-xl
                           px-4 py-3 text-white text-sm placeholder-white/30
                           focus:border-red-500 focus:outline-none transition-colors"
              />

              <div className="flex gap-3">
                <button
                  onClick={handleDeleteAccount}
                  disabled={delLoading || delConfirm !== "DELETE"}
                  className="flex-1 bg-red-500 hover:bg-red-600 text-white
                             font-semibold py-2.5 rounded-xl text-sm
                             disabled:opacity-40 transition-colors"
                >
                  {delLoading ? "Deleting…" : "Delete Account"}
                </button>
                <button
                  onClick={() => {
                    setShowDelDialog(false);
                    setDelConfirm("");
                    setDelError(null);
                  }}
                  className="flex-1 bg-dark-card2 py-2.5 rounded-xl text-sm
                             transition-colors hover:bg-white/10"
                  style={{ color: "var(--text-sub)" }}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Privacy notice */}
        <p className="text-center text-xs mt-6" style={{ color: "var(--text-muted)" }}>
          <a
            href="https://github.com/gitdebashish123/expenditure-tracker/blob/main/PRIVACY.md"
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-400 hover:text-indigo-300"
          >
            Privacy Notice
          </a>
          {" · "}Your data is private and isolated to your account.
        </p>

      </div>
    </div>
  );
}
