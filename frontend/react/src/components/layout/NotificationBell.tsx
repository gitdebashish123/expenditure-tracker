import { useEffect, useState, useRef } from "react";
import { Bell } from "lucide-react";
import { api } from "@/api/client";
import { useMonth } from "@/context/MonthContext";
import { CATEGORY_ICONS } from "@/utils/categories";
import { fmtInr } from "@/utils/formatInr";
import type { BudgetLimit, Summary } from "@/types";

interface Alert {
  category: string;
  spent:    number;
  limit:    number;
  pct:      number;
}

export function NotificationBell() {
  const { selMonth } = useMonth();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [open,   setOpen]   = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    Promise.all([
      api.get<BudgetLimit[]>("/budgets"),
      api.get<Summary>(`/summary/${selMonth}`),
    ]).then(([budgetsRes, summaryRes]) => {
      const catSpent = Object.fromEntries(
        summaryRes.data.categories.map(c => [c.category, c.spent])
      );
      const over = budgetsRes.data
        .map(b => {
          const spent = catSpent[b.category] ?? 0;
          const pct   = b.limit_amount > 0 ? (spent / b.limit_amount) * 100 : 0;
          return { category: b.category, spent, limit: b.limit_amount, pct };
        })
        .filter(a => a.pct >= 100);
      setAlerts(over);
    }).catch(() => {});
  }, [selMonth]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(o => !o)}
        className="relative w-9 h-9 rounded-xl bg-dark-card2 flex items-center
                   justify-center text-white/60 hover:text-white transition-colors"
        aria-label={alerts.length ? `${alerts.length} over-budget alert${alerts.length !== 1 ? "s" : ""}` : "Notifications"}
      >
        <Bell size={16} />
        {alerts.length > 0 && (
          <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-500
                           flex items-center justify-center text-[10px] font-bold text-white">
            {alerts.length}
          </span>
        )}
      </button>

      {open && (
        <>
          {/* Scrim */}
          <div className="fixed inset-0 z-[49]" onClick={() => setOpen(false)} />

          {/* Dropdown panel */}
          <div className="absolute right-0 top-11 w-64 bg-dark-card border border-white/10
                          rounded-2xl shadow-2xl p-3 z-50 space-y-1">
            {alerts.length === 0 ? (
              <p className="text-xs text-center py-2" style={{ color: "var(--text-muted)" }}>
                No over-budget alerts this month.
              </p>
            ) : (
              <>
                <p className="text-xs font-semibold uppercase tracking-widest mb-2"
                   style={{ color: "var(--text-muted)" }}>
                  Over budget · {selMonth}
                </p>
                {alerts.map(a => (
                  <div
                    key={a.category}
                    className="flex items-center justify-between px-2 py-1.5
                               bg-red-500/10 border border-red-500/20 rounded-lg"
                  >
                    <span className="text-sm text-white">
                      {CATEGORY_ICONS[a.category] ?? "📦"} {a.category}
                    </span>
                    <span className="text-xs text-red-400 font-semibold">
                      {fmtInr(a.spent)} / {fmtInr(a.limit)}
                    </span>
                  </div>
                ))}
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}
