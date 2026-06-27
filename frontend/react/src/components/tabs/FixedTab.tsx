import { useEffect, useState, useCallback } from "react";
import { api } from "@/api/client";
import { useMonth } from "@/context/MonthContext";
import { CATEGORY_ICONS } from "@/utils/categories";
import { fmtInr } from "@/utils/formatInr";
import { FixedExpenseRow } from "./FixedExpenseRow";
import { PoolCard } from "./PoolCard";
import type { Expense, Pool, DueReminder } from "@/types";
import { Bell } from "lucide-react";

/**
 * FixedTab — monthly bills checklist + essential pools
 *
 * Streamlit ref: with tab2: in frontend/app.py
 *
 * Three sections:
 *   1. Due reminders (current month only) — overdue bill banners
 *   2. Fixed expenses — grouped by category, tick to mark paid
 *   3. Essential Pools — variable-amount bills, add payments inline
 *
 * Key improvement over Streamlit:
 *   Optimistic UI: tick toggles instantly, syncs backend in background.
 *   Streamlit did full page rerun on every PATCH /fixed/{id}/toggle (visible flicker).
 */

function FixedTabSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-1.5 bg-white/10 rounded-full w-full" />
      {[1, 2, 3, 4].map(i => (
        <div key={i} className="flex items-center gap-3 py-3 border-b border-white/5">
          <div className="w-6 h-6 rounded-full bg-white/10 flex-shrink-0" />
          <div className="flex-1 h-4 bg-white/10 rounded" />
          <div className="w-16 h-4 bg-white/10 rounded" />
        </div>
      ))}
    </div>
  );
}

export function FixedTab() {
  const { selMonth, isCurrent } = useMonth();

  const [reminders, setReminders] = useState<DueReminder[]>([]);
  const [fixedExps, setFixedExps] = useState<Expense[]>([]);
  const [pools, setPools]         = useState<Pool[]>([]);
  const [loading, setLoading]     = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [rem, fixed, poolData] = await Promise.all([
        // Due reminders only relevant for current month
        isCurrent
          ? api.get<DueReminder[]>(`/fixed/due-reminders/${selMonth}`).then(r => r.data)
          : Promise.resolve<DueReminder[]>([]),
        api.get<Expense[]>(`/fixed/${selMonth}`).then(r => r.data),
        api.get<Pool[]>(`/pools/${selMonth}`).then(r => r.data),
      ]);
      setReminders(rem);
      setFixedExps(fixed);
      setPools(poolData);
    } finally {
      setLoading(false);
    }
  }, [selMonth, isCurrent]);

  useEffect(() => { load(); }, [load]);

  // Re-fetch when a template is edited in Settings (dispatched by BillsSection)
  useEffect(() => {
    const handler = () => load();
    window.addEventListener("fixedTemplateUpdated", handler);
    return () => window.removeEventListener("fixedTemplateUpdated", handler);
  }, [load]);

  // Optimistic toggle — UI updates immediately, backend syncs in background
  // Streamlit: PATCH + full st.rerun() = visible flicker on every tick
  const togglePaid = async (id: number) => {
    setFixedExps(prev =>
      prev.map(e => e.id === id ? { ...e, paid: !e.paid } : e)
    );
    try {
      await api.patch(`/fixed/${id}/toggle`);
    } catch {
      // Revert on failure
      setFixedExps(prev =>
        prev.map(e => e.id === id ? { ...e, paid: !e.paid } : e)
      );
    }
  };

  if (loading) return <FixedTabSkeleton />;

  // ── Derived values ──────────────────────────────────────────────────────
  const paidTotal   = fixedExps.reduce((s, e) => s + (e.paid  ? e.amount : 0), 0);
  const unpaidTotal = fixedExps.reduce((s, e) => s + (!e.paid ? e.amount : 0), 0);
  const grandTotal  = paidTotal + unpaidTotal;
  const paidCount   = fixedExps.filter(e => e.paid).length;
  const pct         = grandTotal > 0 ? Math.round(paidTotal / grandTotal * 100) : 0;

  // Group fixed expenses by category, sorted alphabetically
  const byCategory = fixedExps.reduce<Record<string, Expense[]>>((acc, e) => {
    (acc[e.category] ??= []).push(e);
    return acc;
  }, {});

  const isEmpty = fixedExps.length === 0 && pools.length === 0;

  return (
    <div className="space-y-6">

      {/* ── Section 1: Due Reminders ────────────────────── */}
      {reminders.length > 0 && (
        <div className="space-y-2">
          {reminders.map((r, i) => (
            <div
              key={i}
              className="flex items-start gap-3 p-3 rounded-xl
                         bg-red-500/10 border-l-4 border-red-500 text-red-300 text-sm"
            >
              <Bell size={14} className="flex-shrink-0 mt-0.5" />
              <span>
                <b>{r.vendor}</b> {fmtInr(r.amount)} —{" "}
                {r.days_overdue < 0
                  ? `due on the ${r.due_day}th (Due in ${Math.abs(r.days_overdue)} day(s))`
                  : r.days_overdue === 0
                  ? "due today"
                  : `was due on the ${r.due_day}th (${r.days_overdue}d overdue)`}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* ── Section 2: Fixed Expenses ───────────────────── */}
      {fixedExps.length > 0 && (
        <section>
          {/* Summary header */}
          <div className="flex justify-between text-sm mb-2">
            <span style={{ color: 'var(--text-sub)' }}>
              {paidCount} of {fixedExps.length} paid · {fmtInr(paidTotal)} done
            </span>
            <span className="text-red-400">{fmtInr(unpaidTotal)} pending</span>
          </div>

          {/* Progress bar */}
          <div className="h-1.5 bg-white/5 rounded-full mb-5 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${pct}%`,
                background: "linear-gradient(90deg, #34d399, #6366f1)",
              }}
            />
          </div>

          {/* Grouped by category */}
          {Object.entries(byCategory)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([cat, items]) => (
              <div key={cat} className="mb-5">
                {/* Category group header */}
                <p className="text-xs font-syne font-bold uppercase tracking-widest mb-2"
                   style={{ color: 'var(--text-muted)' }}>
                  {CATEGORY_ICONS[cat] ?? "📦"} {cat} ·{" "}
                  {fmtInr(items.reduce((s, e) => s + e.amount, 0))}
                </p>
                <div className="space-y-0">
                  {items.map(item => (
                    <FixedExpenseRow
                      key={item.id}
                      item={item}
                      onToggle={() => togglePaid(item.id)}
                      onAmountChange={load}
                    />
                  ))}
                </div>
              </div>
            ))
          }
        </section>
      )}

      {/* ── Section 3: Essential Pools ──────────────────── */}
      {pools.length > 0 && (
        <section>
          <h2 className="text-xs font-syne font-bold uppercase tracking-widest mb-1"
              style={{ color: 'var(--text-sub)' }}>
            Essential Pools
          </h2>
          <p className="text-xs mb-4" style={{ color: 'var(--text-muted)' }}>
            Bills with variable amount — add each payment as it happens.
          </p>
          <div className="space-y-3">
            {pools.map(pool => (
              <PoolCard
                key={pool.id}
                pool={pool}
                selMonth={selMonth}
                onChanged={load}
              />
            ))}
          </div>
        </section>
      )}

      {/* ── Empty state ─────────────────────────────────── */}
      {isEmpty && (
        <div className="text-center py-16">
          <div className="text-4xl mb-3">📋</div>
          <p className="text-sm mb-1" style={{ color: 'var(--text-muted)' }}>
            No bills set up yet.
          </p>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
            Go to{" "}
            <span className="text-indigo-400">Settings → Monthly Bills</span>
            {" "}to add your rent, EMI, and subscriptions.
          </p>
        </div>
      )}

    </div>
  );
}
