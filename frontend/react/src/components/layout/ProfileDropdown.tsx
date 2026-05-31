import { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Key, Lock, LogOut } from "lucide-react";

/**
 * ProfileDropdown — avatar button with dropdown menu
 *
 * Streamlit ref: st.popover in frontend/app.py
 * Shows user initial in a gradient circle.
 * Dropdown: email, Change Password (→ /account), Privacy Notice, Sign Out.
 * Closes on outside click.
 */
export function ProfileDropdown() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on click outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const initial = user?.email?.[0]?.toUpperCase() ?? "?";

  return (
    <div ref={ref} className="relative">
      {/* Avatar button */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-9 h-9 rounded-xl bg-gradient-to-br from-accent to-accent2
                   flex items-center justify-center font-syne font-bold text-white text-sm
                   hover:opacity-90 transition-opacity"
        aria-label="Profile menu"
      >
        {initial}
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute right-0 top-11 w-56 bg-dark-card border border-white/10
                        rounded-2xl shadow-2xl p-2 z-50">
          {/* User info */}
          <div className="px-3 py-2 border-b border-white/10 mb-1">
            <p className="text-white/40 text-xs">Signed in as</p>
            <p className="text-white text-sm font-medium truncate">{user?.email}</p>
          </div>

          {/* Change Password — navigates to /account */}
          <Link
            to="/account"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-white/70
                       hover:text-white hover:bg-white/5 text-sm transition-colors"
          >
            <Key size={14} /> Change Password
          </Link>

          {/* Privacy Notice */}
          <a
            href="https://github.com/gitdebashish123/expenditure-tracker/blob/main/PRIVACY.md"
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-white/70
                       hover:text-white hover:bg-white/5 text-sm transition-colors"
          >
            <Lock size={14} /> Privacy Notice
          </a>

          <hr className="border-white/10 my-1" />

          {/* Sign Out */}
          <button
            onClick={logout}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-white/70
                       hover:text-red-400 hover:bg-red-500/10 text-sm transition-colors"
          >
            <LogOut size={14} /> Sign Out
          </button>
        </div>
      )}
    </div>
  );
}
