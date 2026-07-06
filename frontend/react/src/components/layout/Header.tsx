import { Sun, Moon } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";
import { MonthSelector } from "@/components/shared/MonthSelector";
import { ProfileDropdown } from "./ProfileDropdown";
import { NotificationBell } from "./NotificationBell";

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
            <h1 className="font-syne font-bold text-white text-lg leading-none tracking-tight
                           flex items-center gap-2">
              <img
                src={theme === "dark" ? "/wallet-mantra-logo.png" : "/wallet-mantra-logo-light.png"}
                alt=""
                aria-hidden="true"
                className="h-8 w-8 flex-shrink-0 object-contain"
              />
              Wallet Mantra
            </h1>
          </div>

          {/* Month selector — desktop only (centre) */}
          <div className="flex-1 flex justify-center">
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
            <NotificationBell />
            <ProfileDropdown />
          </div>
        </div>

      </div>
    </header>
  );
}
