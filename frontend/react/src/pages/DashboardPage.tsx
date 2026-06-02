import { useState, useEffect, useCallback } from "react";
import { useAuth }              from "@/context/AuthContext";
import { MonthProvider }        from "@/context/MonthContext";
import { useMonth }             from "@/context/MonthContext";
import { Header }               from "@/components/layout/Header";
import { BottomNav }            from "@/components/layout/BottomNav";
import { OnboardingWizard }     from "@/components/onboarding/OnboardingWizard";
import { ErrorBoundary }        from "@/components/shared/ErrorBoundary";
import { SummaryStrip }         from "@/components/shared/SummaryStrip";
import { SummaryFlipCard }      from "@/components/shared/SummaryFlipCard";
import { QuickAddTab }          from "@/components/tabs/QuickAddTab";
import { FixedTab }             from "@/components/tabs/FixedTab";
import { OverviewTab }          from "@/components/tabs/OverviewTab";
import { HistoryTab }           from "@/components/tabs/HistoryTab";
import { SettingsTab }          from "@/components/tabs/SettingsTab";
import { AdminTab }             from "@/components/tabs/AdminTab";
import { api }                  from "@/api/client";
import type { Summary }         from "@/types";

type Tab = "today" | "fixed" | "overview" | "history" | "settings" | "admin";

const TAB_PATH_MAP: Record<Tab, string> = {
  today:    "/",
  fixed:    "/fixed",
  overview: "/overview",
  history:  "/history",
  settings: "/settings",
  admin:    "/admin",
};

function DashboardShell({ tab, onTabChange, isAdmin }: {
  tab:         Tab;
  onTabChange: (path: string) => void;
  isAdmin:     boolean;
}) {
  const { selMonth } = useMonth();
  const [balance,    setBalance]    = useState<Summary["balance"] | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchSummary = useCallback(() => {
    api.get<Summary>(`/summary/${selMonth}`)
      .then(r => setBalance(r.data.balance))
      .catch(() => {});
  }, [selMonth]);

  useEffect(() => { fetchSummary(); }, [fetchSummary, refreshKey]);

  const bumpRefresh = useCallback(() => setRefreshKey(k => k + 1), []);

  const showSummary = tab === "today" || tab === "fixed" || tab === "overview";

  // Derived flip-card configs for the 3 cards
  const flipCards = balance ? [
    {
      label:  "Remaining",
      value:  balance.remaining,
      colour: balance.remaining >= 0 ? "#34d399" : "#f87171",
    },
    {
      label:  "Income",
      value:  balance.total_income,
      colour: "#6366f1",
    },
    {
      label:  "Fixed Paid",
      value:  balance.fixed_paid_total,
      colour: "#f59e0b",
    },
  ] : [];

  return (
    <div className="min-h-screen pb-20 sm:pb-0" style={{ backgroundColor: "var(--bg)" }}>
      <Header />
      <BottomNav activeTab={TAB_PATH_MAP[tab]} onTabChange={onTabChange} />

      {showSummary && balance && (
        <>
          {/* Mobile: compact count-up strip */}
          <div
            className="md:hidden sticky z-20 border-b px-4 py-2"
            style={{
              top:             "56px",
              backgroundColor: "var(--bg)",
              borderColor:     "var(--border)",
            }}
          >
            <SummaryStrip balance={balance} />
          </div>

          {/* Desktop: 3 flip cards */}
          <div className="hidden md:flex gap-3 max-w-2xl mx-auto px-4 pt-4">
            {flipCards.map(c => (
              <SummaryFlipCard key={c.label} label={c.label} value={c.value} colour={c.colour} />
            ))}
          </div>
        </>
      )}

      <main className="max-w-2xl mx-auto px-4 py-4">
        {tab === "today"    && <ErrorBoundary><QuickAddTab onExpenseAdded={bumpRefresh} /></ErrorBoundary>}
        {tab === "fixed"    && <ErrorBoundary><FixedTab    /></ErrorBoundary>}
        {tab === "overview" && <ErrorBoundary><OverviewTab /></ErrorBoundary>}
        {tab === "history"  && <ErrorBoundary><HistoryTab  /></ErrorBoundary>}
        {tab === "settings" && <ErrorBoundary><SettingsTab /></ErrorBoundary>}
        {tab === "admin" && isAdmin &&
          <ErrorBoundary><AdminTab /></ErrorBoundary>
        }
      </main>
    </div>
  );
}

export function DashboardPage() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("today");

  if (!user?.onboarding_complete) return <OnboardingWizard />;

  const handleTabChange = (path: string) => {
    const found = Object.entries(TAB_PATH_MAP).find(([, v]) => v === path);
    if (found) setTab(found[0] as Tab);
  };

  return (
    <MonthProvider>
      <DashboardShell
        tab={tab}
        onTabChange={handleTabChange}
        isAdmin={user.is_admin}
      />
    </MonthProvider>
  );
}
