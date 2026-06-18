import { Sun, Moon } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";
import { MonthSelector } from "@/components/shared/MonthSelector";
import { ProfileDropdown } from "./ProfileDropdown";

/**
 * Header — sticky top bar
 *
 * Streamlit ref: col_title / col_theme / col_logout / col_month block in frontend/app.py
 *
 * Layout:
 *   Left:   Wallet Mantra logo + tagline
 *   Centre: MonthSelector (hidden on mobile — shown below header row)
 *   Right:  Theme toggle + ProfileDropdown
 *
 * Mobile: MonthSelector renders full-width below the header row
 * Desktop (sm+): MonthSelector is inline in the centre
 */
export function Header() {
  const { theme, toggle } = useTheme();

  return (
    <header className="sticky top-0 z-40 bg-dark-bg/95 backdrop-blur-sm border-b border-white/5 px-4 py-3">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between gap-3">

          {/* Logo */}
          <div className="flex-shrink-0">
            <h1 className="font-syne font-bold text-white text-lg leading-none tracking-tight">
              💸 Wallet Mantra
            </h1>
            <p className="text-xs mt-0.5" style={{ color: 'var(--text-sub)' }}>
              Beyond expense tracking
            </p>
          </div>

          {/* Month selector — desktop only (centre) */}
          <div className="hidden sm:block flex-1 flex justify-center">
            <MonthSelector />
          </div>

          {/* Right controls */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={toggle}
              className="w-9 h-9 rounded-xl bg-dark-card2 flex items-center justify-center
                         text-white/60 hover:text-white transition-colors"
              aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            >
              {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <ProfileDropdown />
          </div>
        </div>

        {/* Month selector — mobile only (full width below header row) */}
        <div className="sm:hidden mt-2">
          <MonthSelector />
        </div>
      </div>
    </header>
  );
}
