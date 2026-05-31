import { fmtInr } from "@/utils/formatInr";

interface Balance {
  total_income: number;
  fixed_paid_total: number;
  fixed_unpaid_total: number;
  variable_total: number;
  remaining: number;
}

/**
 * BalanceBreakdown — horizontal stacked bar showing monthly allocation
 *
 * Streamlit ref: gauge_html div with custom HTML segments in with tab3:
 * Replaces the fragile inline-HTML approach with a clean flex div.
 *
 * Segments (left to right):
 *   Indigo       → Fixed Paid
 *   Faded indigo → Fixed Pending
 *   Red          → Variable spent
 *   Green        → Remaining (clamped to 0 if negative)
 */
export function BalanceBreakdown({ balance }: { balance: Balance }) {
  const inc = Math.max(balance.total_income, 1); // avoid divide-by-zero

  const segments = [
    {
      label:  "Fixed Paid",
      value:  balance.fixed_paid_total,
      colour: "#6366f1",
    },
    {
      label:  "Pending",
      value:  balance.fixed_unpaid_total,
      colour: "rgba(99,102,241,0.3)",
    },
    {
      label:  "Variable",
      value:  balance.variable_total,
      colour: "#f87171",
    },
    {
      label:  "Remaining",
      value:  Math.max(balance.remaining, 0),
      colour: "rgba(52,211,153,0.4)",
    },
  ];

  return (
    <div className="bg-dark-card border border-white/10 rounded-2xl p-4">
      <p
        className="text-xs uppercase tracking-widest mb-3"
        style={{ color: "var(--text-sub)" }}
      >
        Monthly Breakdown
      </p>

      {/* Stacked bar */}
      <div className="flex h-7 rounded-lg overflow-hidden gap-px">
        {segments.map(s => {
          const pct = Math.min((s.value / inc) * 100, 100);
          if (pct < 0.5) return null;
          return (
            <div
              key={s.label}
              className="flex items-center justify-center text-white text-[10px]
                         font-semibold transition-all duration-700 overflow-hidden"
              style={{ width: `${pct}%`, background: s.colour, minWidth: 0 }}
            >
              {pct > 8 ? `${Math.round(pct)}%` : ""}
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-x-4 gap-y-1.5 mt-3">
        {segments.map(s => (
          <span
            key={s.label}
            className="flex items-center gap-1.5 text-xs"
            style={{ color: "var(--text-sub)" }}
          >
            <span
              className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
              style={{ background: s.colour }}
            />
            {s.label} {fmtInr(s.value)}
          </span>
        ))}
      </div>
    </div>
  );
}
