import { fmtInr } from "@/utils/formatInr";

interface Balance {
  total_income: number;
  fixed_paid_total: number;
  fixed_unpaid_total: number;
  variable_total: number;
  remaining: number;
}

export function BalanceBreakdown({ balance }: { balance: Balance }) {
  const inc = Math.max(balance.total_income, 1);

  const segments: Array<{ label: string; shortLabel: string; value: number; colour: string; legendOnly?: boolean }> = [
    {
      label:      "Fixed Paid",
      shortLabel: "Bills",
      value:      balance.fixed_paid_total,
      colour:     "#6366f1",
    },
    {
      label:      "Fixed Due",
      shortLabel: "Due",
      value:      balance.fixed_unpaid_total,
      colour:     "rgba(99,102,241,0.3)",
    },
    {
      label:      "Variable Spent",
      shortLabel: "Variable",
      value:      balance.variable_total,
      colour:     "#f87171",
    },
    {
      label:      "Balance Left",
      shortLabel: "Balance",
      value:      Math.max(balance.remaining, 0),
      colour:     "rgba(52,211,153,0.4)",
      legendOnly: true,
    },
  ];

  return (
    <div className="bg-dark-card border border-white/10 rounded-2xl p-4">
      <p className="section-heading mb-3">
        Monthly breakdown
      </p>

      {/* Stacked bar */}
      <div className="flex h-7 rounded-lg overflow-hidden gap-px">
        {segments.map(s => {
          const pct = Math.min((s.value / inc) * 100, 100);
          if (pct < 0.5 || s.legendOnly) return null;
          const pctRounded = Math.round(pct);
          const text = pct >= 12
            ? `${s.shortLabel} ${pctRounded}%`
            : pct >= 5
            ? `${pctRounded}%`
            : "";
          return (
            <div
              key={s.label}
              className="flex items-center justify-center transition-all duration-700 overflow-hidden"
              style={{
                width:      `${pct}%`,
                background: s.colour,
                minWidth:   0,
                fontSize:   10,
                color:      "#fff",
                whiteSpace: "nowrap",
                textOverflow: "ellipsis",
                fontWeight: 600,
              }}
            >
              {text}
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
            {s.shortLabel} {fmtInr(s.value)}
          </span>
        ))}
      </div>
    </div>
  );
}
