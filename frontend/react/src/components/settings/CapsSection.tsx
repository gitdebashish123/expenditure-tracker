import { useEffect, useState, useRef } from "react";
import { api } from "@/api/client";
import { useMonth } from "@/context/MonthContext";
import { CATEGORY_ICONS, VAR_CATEGORIES } from "@/utils/categories";
import { fmtInr } from "@/utils/formatInr";
import type { BudgetLimit, Summary } from "@/types";
import { CurrencyInput } from "@/components/shared/CurrencyInput";

export function CapsSection() {
  const { selMonth } = useMonth();

  const [budgets,    setBudgets]    = useState<BudgetLimit[]>([]);
  const [catSpent,   setCatSpent]   = useState<Record<string, number>>({});
  const [updates,    setUpdates]    = useState<Record<string, number>>({});
  const [savedCat,   setSavedCat]   = useState<string | null>(null);
  const [newCat,     setNewCat]     = useState("");
  const [newLimit,   setNewLimit]   = useState<number>(0);
  const [addingSave, setAddingSave] = useState(false);
  const [addOpen,    setAddOpen]    = useState(false);
  const [showAllCaps, setShowAllCaps] = useState(false);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    api.get<BudgetLimit[]>("/budgets")
      .then(r => {
        setBudgets(r.data);
        setUpdates(Object.fromEntries(r.data.map(b => [b.category, b.limit_amount])));
      })
      .catch(() => {});

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

  const handleCapChange = (category: string, value: number) => {
    setUpdates(prev => ({ ...prev, [category]: value }));
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        await api.put("/budget", { category, limit_amount: value });
        setSavedCat(category);
        setTimeout(() => setSavedCat(null), 2000);
      } catch { /* silent */ }
    }, 600);
  };

  return (
    <section>
      {/* Section header */}
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-syne font-bold text-white">🎯 Spending Caps</h2>
            <p className="text-sm mt-0.5" style={{ color: "var(--text-sub)" }}>
              Monthly limit per category. You'll get a warning when you're close.
            </p>
          </div>
          {availableCats.length > 0 && (
            <button
              onClick={() => setAddOpen(o => !o)}
              className="flex-shrink-0 text-xs font-semibold px-3 py-1.5 rounded-lg
                         border border-accent/40 text-indigo-300 hover:bg-accent/10
                         transition-colors"
            >
              + Set cap
            </button>
          )}
        </div>
        <div className="border-b border-white/10 mt-3" />
      </div>

      {/* Add-cap form (revealed by "+ Set cap") */}
      {addOpen && availableCats.length > 0 && (
        <div className="mb-4 flex gap-3">
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
          <CurrencyInput
            value={newLimit}
            onChange={v => setNewLimit(v)}
            placeholder="₹ limit"
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
                setAddOpen(false);
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
      )}

      {/* Cap cards — 2-per-row grid, first 2 visible; expand via "View all" */}
      <div className="grid grid-cols-2 gap-3">
        {(showAllCaps ? budgets : budgets.slice(0, 2)).map(b => {
          const spent  = catSpent[b.category] ?? 0;
          const limit  = updates[b.category]  ?? b.limit_amount;
          const pct    = limit > 0 ? (spent / limit) * 100 : 0;
          const colour =
            pct >= 100 ? "#ef4444"
            : pct >= 80 ? "#f59e0b"
            : "#34d399";
          const stateCue = pct >= 100 ? "Over" : pct >= 80 ? "Near" : "On track";

          return (
            <div
              key={b.category}
              className="bg-dark-card2 border border-white/10 rounded-xl p-3 space-y-2"
            >
              {/* Row 1: name + % + state cue */}
              <div className="flex items-center justify-between gap-1">
                <span className="text-white text-xs font-medium truncate">
                  {CATEGORY_ICONS[b.category] ?? "📦"} {b.category}
                </span>
                <span className="text-xs font-semibold flex-shrink-0" style={{ color: colour }}>
                  {pct.toFixed(0)}%
                  {savedCat === b.category && (
                    <span className="ml-1 text-emerald-400">✓</span>
                  )}
                </span>
              </div>

              {/* Row 2: spent / cap + state cue label */}
              <div className="flex items-center justify-between gap-1">
                <span className="text-xs truncate" style={{ color: "var(--text-muted)" }}>
                  {fmtInr(spent)} / {fmtInr(limit)}
                </span>
                <span className="text-xs flex-shrink-0" style={{ color: colour }}>
                  {stateCue}
                </span>
              </div>

              {/* Progress bar */}
              <div className="h-1 rounded-full bg-white/10 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(pct, 100)}%`, background: colour }}
                />
              </div>

              {/* Editable cap amount */}
              <CurrencyInput
                value={updates[b.category] ?? 0}
                onChange={v => handleCapChange(b.category, v)}
                className="w-full bg-dark-bg border border-white/10 rounded-lg
                           px-2.5 py-1.5 text-white text-xs
                           focus:border-accent focus:outline-none transition-colors"
              />
            </div>
          );
        })}
      </div>

      {budgets.length > 2 && (
        <button
          onClick={() => setShowAllCaps(v => !v)}
          className="mt-3 text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          {showAllCaps ? "▲ Hide" : `View all cap limits → (${budgets.length - 2} more)`}
        </button>
      )}
    </section>
  );
}
