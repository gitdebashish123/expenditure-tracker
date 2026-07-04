import { useState, useEffect, useCallback } from "react";
import { useAuth }              from "@/context/AuthContext";
import { MonthProvider }        from "@/context/MonthContext";
import { PrivacyProvider }      from "@/context/PrivacyContext";
import { useMonth }             from "@/context/MonthContext";
import { Header }               from "@/components/layout/Header";
import { BottomNav }            from "@/components/layout/BottomNav";
import { OnboardingWizard }     from "@/components/onboarding/OnboardingWizard";
import { ErrorBoundary }        from "@/components/shared/ErrorBoundary";
import { KpiCarousel }          from "@/components/shared/KpiCarousel";
import type { KpiCard }         from "@/components/shared/KpiCarousel";
import { HeroBalanceCard }      from "@/components/shared/HeroBalanceCard";
import { QuickAddTab }          from "@/components/tabs/QuickAddTab";
import { FixedTab }             from "@/components/tabs/FixedTab";
import { OverviewTab }          from "@/components/tabs/OverviewTab";
import { HistoryTab }           from "@/components/tabs/HistoryTab";
import { SettingsTab }          from "@/components/tabs/SettingsTab";
import { AdminTab }             from "@/components/tabs/AdminTab";
import { api }                  from "@/api/client";
import { fmtInr }               from "@/utils/formatInr";
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
  const [balance,       setBalance]       = useState<Summary["balance"] | null>(null);
  const [fixedProgress, setFixedProgress] = useState<Summary["fixed_progress"] | null>(null);
  const [refreshKey,    setRefreshKey]    = useState(0);

  const fetchSummary = useCallback(() => {
    api.get<Summary>(`/summary/${selMonth}`)
      .then(r => { setBalance(r.data.balance); setFixedProgress(r.data.fixed_progress); })
      .catch(() => {});
  }, [selMonth]);

  useEffect(() => { fetchSummary(); }, [fetchSummary, refreshKey]);

  const bumpRefresh = useCallback(() => setRefreshKey(k => k + 1), []);

  const totalCount = fixedProgress?.total ?? 0;
  const paidCount  = fixedProgress?.paid  ?? 0;
  const fixedCards: KpiCard[] = balance ? [
    {
      id: "fx-left",
      label: "Fixed left",
      value: fmtInr(balance.fixed_unpaid_total),
      subtitle: balance.fixed_unpaid_total === 0 ? "All clear" : `${totalCount - paidCount} pending`,
      accent: "#94a3b8",
      gradientClass: "kpi-card-fixed-left",
    },
    {
      id: "fx-paid",
      label: "Fixed paid",
      value: fmtInr(balance.fixed_paid_total),
      subtitle: `${paidCount} of ${totalCount} items`,
      accent: "#34d399",
      gradientClass: "kpi-card-remaining",
    },
    {
      id: "fx-total",
      label: "Fixed total",
      value: fmtInr(balance.fixed_paid_total + balance.fixed_unpaid_total),
      subtitle: `${totalCount} items this month`,
      accent: "#fbbf24",
      gradientClass: "kpi-card-bills",
    },
  ] : [];

  return (
    <div className="min-h-screen pb-20 sm:pb-0" style={{ backgroundColor: "var(--bg)" }}>
      <Header />
      <BottomNav activeTab={TAB_PATH_MAP[tab]} onTabChange={onTabChange} />

      {/* Today tab: hero card replaces strip/flip-cards */}
      {tab === "today" && balance && (
        <div className="max-w-2xl mx-auto px-4 pt-4">
          <HeroBalanceCard balance={balance} />
        </div>
      )}

      {/* Fixed tab: amber KPI carousel */}
      {tab === "fixed" && balance && (
        <div className="max-w-2xl mx-auto px-4 pt-4">
          <KpiCarousel cards={fixedCards} />
        </div>
      )}

      <main className="max-w-2xl mx-auto px-4 py-4">
        {tab === "today"    && <ErrorBoundary><QuickAddTab onExpenseAdded={bumpRefresh} /></ErrorBoundary>}
        {tab === "fixed"    && <ErrorBoundary><FixedTab onChanged={bumpRefresh} /></ErrorBoundary>}
        {tab === "overview" && <ErrorBoundary><OverviewTab onTabChange={onTabChange} /></ErrorBoundary>}
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
    <PrivacyProvider>
      <MonthProvider>
        <DashboardShell
          tab={tab}
          onTabChange={handleTabChange}
          isAdmin={user.is_admin}
        />
      </MonthProvider>
    </PrivacyProvider>
  );
}
