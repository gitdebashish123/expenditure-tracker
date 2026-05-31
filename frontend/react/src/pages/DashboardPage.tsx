import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { MonthProvider } from "@/context/MonthContext";
import { Header } from "@/components/layout/Header";
import { BottomNav } from "@/components/layout/BottomNav";
import { OnboardingWizard } from "@/components/onboarding/OnboardingWizard";
import { QuickAddTab } from "@/components/tabs/QuickAddTab";
import { FixedTab } from "@/components/tabs/FixedTab";
import { OverviewTab } from "@/components/tabs/OverviewTab";
import { HistoryTab } from "@/components/tabs/HistoryTab";
import { SettingsTab } from "@/components/tabs/SettingsTab";
import { AdminTab } from "@/components/tabs/AdminTab";

/**
 * DashboardPage — main app shell with tab navigation
 *
 * Streamlit ref: the main app body after authentication in frontend/app.py
 *
 * Tab order matches Streamlit:
 *   today    → QuickAddTab  ✅ T2.3
 *   fixed    → FixedTab     ✅ T2.4
 *   overview → OverviewTab  ✅ T2.5
 *   history  → HistoryTab   ✅ T2.6
 *   settings → SettingsTab  ✅ T2.7
 *   admin    → AdminTab     ✅ T2.8 (admin only)
 */

type Tab = "today" | "fixed" | "overview" | "history" | "settings" | "admin";

const TAB_PATH_MAP: Record<Tab, string> = {
  today:    "/",
  fixed:    "/fixed",
  overview: "/overview",
  history:  "/history",
  settings: "/settings",
  admin:    "/admin",
};

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
      <div className="min-h-screen pb-20 sm:pb-0"
           style={{ backgroundColor: 'var(--bg)' }}>
        <Header />
        <BottomNav
          activeTab={TAB_PATH_MAP[tab]}
          onTabChange={handleTabChange}
        />
        <main className="max-w-2xl mx-auto px-4 py-4">
          {tab === "today"    && <QuickAddTab />}
          {tab === "fixed"    && <FixedTab />}
          {tab === "overview" && <OverviewTab />}
          {tab === "history"  && <HistoryTab />}
          {tab === "settings" && <SettingsTab />}
          {tab === "admin" && user.is_admin && <AdminTab />}
        </main>
      </div>
    </MonthProvider>
  );
}
