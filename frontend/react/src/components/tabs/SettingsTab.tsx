import { IncomeSection }    from "@/components/settings/IncomeSection";
import { BillsSection }     from "@/components/settings/BillsSection";
import { CapsSection }      from "@/components/settings/CapsSection";
import { ShortcutsSection } from "@/components/settings/ShortcutsSection";
import { ExportSection }    from "@/components/settings/ExportSection";

/**
 * SettingsTab — operational configuration for the current user
 *
 * Streamlit ref: with tab5: in frontend/app.py
 *
 * Five sections (My Account is a separate /account route done in T2.8):
 *   1. IncomeSection    — monthly take-home income
 *   2. BillsSection     — fixed template CRUD + pool templates + add bill form
 *   3. CapsSection      — monthly spending limits per category
 *   4. ShortcutsSection — quick-add favourite expense templates
 *   5. ExportSection    — CSV download (month + full history)
 */
export function SettingsTab() {
  return (
    <div className="space-y-10 pb-8">
      <IncomeSection />
      <BillsSection />
      <CapsSection />
      <ShortcutsSection />
      <ExportSection />
    </div>
  );
}
