import { Zap, Bookmark, LayoutDashboard, List, Settings, Shield } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

/**
 * BottomNav — navigation bar
 *
 * Mobile (< sm): fixed bottom bar with icon + label
 * Desktop (sm+): horizontal tab row below the header
 *
 * Streamlit ref: st.tabs() in frontend/app.py
 * Tab order matches Streamlit: Today | Fixed | Overview | History | Settings | [Admin]
 * Admin tab appended only when user.is_admin === true
 */

type NavItem = {
  to: string;
  icon: React.ElementType;
  label: string;
};

const BASE_NAV: NavItem[] = [
  { to: "/",         icon: Zap,             label: "Today"    },
  { to: "/fixed",    icon: Bookmark,        label: "Fixed"    },
  { to: "/overview", icon: LayoutDashboard, label: "Overview" },
  { to: "/history",  icon: List,            label: "History"  },
  { to: "/settings", icon: Settings,        label: "Settings" },
];

interface Props {
  activeTab: string;
  onTabChange: (path: string) => void;
}

export function BottomNav({ activeTab, onTabChange }: Props) {
  const { user } = useAuth();
  const tabs: NavItem[] = user?.is_admin
    ? [...BASE_NAV, { to: "/admin", icon: Shield, label: "Admin" }]
    : BASE_NAV;

  return (
    <>
      {/* ── Mobile: fixed bottom bar ──────────────────────── */}
      <nav className="fixed bottom-0 left-0 right-0 bg-dark-card border-t border-white/5
                      z-40 sm:hidden">
        <div className="flex items-center justify-around h-16 px-1 max-w-2xl mx-auto">
          {tabs.map(({ to, icon: Icon, label }) => {
            const isActive = activeTab === to;
            return (
              <button
                key={to}
                onClick={() => onTabChange(to)}
                className={`flex flex-col items-center justify-center gap-0.5 px-2 py-2
                            rounded-xl transition-colors min-w-[44px] min-h-[44px]
                            ${isActive ? "text-accent" : "text-white/40 hover:text-white/60"}`}
                aria-label={label}
                aria-current={isActive ? "page" : undefined}
              >
                <Icon size={18} />
                <span className="text-[9px] font-medium">{label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      {/* ── Desktop: horizontal tab row below header ──────── */}
      <div className="desktop-tabs hidden sm:block border-b sticky top-[69px] z-30"
           style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)' }}>
        <div className="max-w-2xl mx-auto px-4">
          <div className="flex items-center gap-1">
            {tabs.map(({ to, icon: Icon, label }) => {
              const isActive = activeTab === to;
              return (
                <button
                  key={to}
                  onClick={() => onTabChange(to)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium
                              border-b-2 transition-colors
                              ${isActive
                                ? 'border-accent text-accent'
                                : 'border-transparent hover:border-accent/30'
                              }`}
                  style={isActive ? {} : { color: 'var(--text-sub)' }}
                  aria-current={isActive ? "page" : undefined}
                >
                  <Icon size={15} />
                  {label}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </>
  );
}
