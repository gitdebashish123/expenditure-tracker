import { useEffect, useState } from "react";
import { api } from "@/api/client";
import { useMonth } from "@/context/MonthContext";
import { CATEGORY_ICONS, VAR_CATEGORIES } from "@/utils/categories";
import { fmtInr } from "@/utils/formatInr";
import type { BudgetLimit, Summary } from "@/types";
import { Save } from "lucide-react";

/**
 * CapsSection — monthly spending caps per variable category
 *
 * Streamlit ref: settings_section("🎯", "Spending Caps", ...) in with tab5:
 * 2-column grid of number inputs with live spend context colour.
 *
 * Colour coding for spent amount label:
 *   green  → safe (< 80% of cap)
 *   amber  → warning (80–99%)
 *   red    → over (≥ 100%)
 */
export function CapsSection() {
  const { selMonth } = useMonth();

  const [budgets,  setBudgets]  = useState<BudgetLimit[]>([]);
  const [catSpent, setCatSpent] = useState<Record<string, number>>({});
  const [updates,  setUpdates]  = useState<Record<string, number>>({});
  const [saving,     setSaving]     = useState(false);
  const [saved,      setSaved]      = useState(false);
  const [newCat,     setNewCat]     = useState("");
  const [newLimit,   setNewLimit]   = useState<number>(0);
  const [addingSave, setAddingSave] = useState(false);

  useEffect(() => {
    // Load budget limits
    api.get<BudgetLimit[]>("/budgets")
      .then(r => {
        setBudgets(r.data);
        setUpdates(Object.fromEntries(r.data.map(b => [b.category, b.limit_amount])));
      })
      .catch(() => {});

    // Load current month spend per category
    api.get<Summary>(`/summary/${selMonth}`)
      .then(r => {
        setCatSpent(
          Object.fromEntries(r.data.categories.map(c => [c.category, c.spent]))
        );
      })
      .catch(() => {});
  }, [selMonth]);

  const cappedCats    = new Set(budgets.map(b => b.category));
  const availableCats = VAR_CATEGORIES.filter(c => !cappedCats.has(c));

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await Promise.all(
        Object.entries(updates).map(([category, limit_amount]) =>
          api.put("/budget", { category, limit_amount })
        )
      );
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section>
      {/* Section header */}
      <div className="mb-4">
        <h2 className="font-syne font-bold text-white">🎯 Spending Caps</h2>
        <p className="text-sm mt-0.5" style={{ color: "var(--text-sub)" }}>
          Monthly limit per category. You'll get a warning when you're close.
        </p>
        <div className="border-b border-white/10 mt-3" />
      </div>

      <form onSubmit={handleSave}>
        <div className="grid grid-cols-2 gap-4 mb-4">
          {budgets.map(b => {
            const spent  = catSpent[b.category] ?? 0;
            const limit  = updates[b.category]  ?? b.limit_amount;
            const pct    = limit > 0 ? (spent / limit) * 100 : 0;
            const colour =
              pct >= 100 ? "#ef4444"
              : pct >= 80 ? "#f59e0b"
              : "#34d399";

            return (
              <div key={b.category}>
                <div className="flex justify-between items-center mb-1">
                  <label className="text-white text-sm">
                    {CATEGORY_ICONS[b.category] ?? "📦"} {b.category}
                  </label>
                  <span className="text-xs" style={{ color: colour }}>
                    {fmtInr(spent)} spent
                  </span>
                </div>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={updates[b.category] ?? ""}
                  onChange={e =>
                    setUpdates(prev => ({
                      ...prev,
                      [b.category]: Number(e.target.value),
                    }))
                  }
                  className="w-full bg-dark-card2 border border-white/10 rounded-xl
                             px-3 py-2 text-white text-sm
                             focus:border-accent focus:outline-none transition-colors"
                />
              </div>
            );
          })}
        </div>

        <button
          type="submit"
          disabled={saving}
          className="flex items-center gap-2 bg-gradient-to-r from-accent to-accent2
                     text-white font-semibold px-6 py-2.5 rounded-xl text-sm
                     disabled:opacity-50 transition-opacity"
        >
          <Save size={14} />
          {saving ? "Saving…" : saved ? "✅ Saved!" : "Save Spending Caps"}
        </button>
      </form>

      {availableCats.length > 0 && (
        <div className="mt-6 pt-4 border-t border-white/10">
          <p className="text-sm text-white mb-3">➕ Add a category cap</p>
          <div className="flex gap-3">
            <select
              value={newCat}
              onChange={e => setNewCat(e.target.value)}
              className="flex-1 bg-dark-card2 border border-white/10 rounded-xl px-3 py-2
                         text-white text-sm focus:border-accent focus:outline-none"
            >
              <option value="">Select category…</option>
              {availableCats.map(c => (
                <option key={c} value={c}>{CATEGORY_ICONS[c] ?? "📦"} {c}</option>
              ))}
            </select>
            <input
              type="number"
              min="0"
              step="1"
              placeholder="₹ limit"
              value={newLimit || ""}
              onChange={e => setNewLimit(Number(e.target.value))}
              className="w-28 bg-dark-card2 border border-white/10 rounded-xl px-3 py-2
                         text-white text-sm focus:border-accent focus:outline-none"
            />
            <button
              type="button"
              disabled={!newCat || newLimit <= 0 || addingSave}
              onClick={async () => {
                setAddingSave(true);
                try {
                  await api.put("/budget", { category: newCat, limit_amount: newLimit });
                  const r = await api.get<BudgetLimit[]>("/budgets");
                  setBudgets(r.data);
                  setUpdates(Object.fromEntries(r.data.map(b => [b.category, b.limit_amount])));
                  setNewCat("");
                  setNewLimit(0);
                } finally {
                  setAddingSave(false);
                }
              }}
              className="px-4 py-2 bg-accent rounded-xl text-white text-sm font-semibold
                         disabled:opacity-40 transition-opacity"
            >
              {addingSave ? "…" : "Add"}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
