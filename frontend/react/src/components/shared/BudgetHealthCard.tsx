import { fmtInr } from "@/utils/formatInr";
import { CATEGORY_ICONS } from "@/utils/categories";
import type { ProjectionItem } from "@/types";

/**
 * BudgetHealthCard — single category budget projection card
 *
 * Streamlit ref: projection card loop in with tab3: (STATUS dict + custom HTML)
 * Replaces inline HTML with Tailwind + animated progress bar.
 *
 * Status colours:
 *   safe    → green  (on track)
 *   warning → yellow (>60% spent)
 *   danger  → orange (>80% spent, projected to exceed)
 *   over    → red    (already exceeded)
 */

const STATUS_CONFIG: Record<
  ProjectionItem["status"],
  { dot: string; accent: string; bg: string; label: string }
> = {
  over:    { dot: "🔴", accent: "#ef4444", bg: "rgba(239,68,68,0.08)",  label: ""                               },
  danger:  { dot: "🟠", accent: "#f59e0b", bg: "rgba(245,158,11,0.07)", label: "🔴 Likely to exceed limit"      },
  warning: { dot: "🟡", accent: "#eab308", bg: "rgba(234,179,8,0.06)",  label: "⚠️ Slow down — 80% limit near" },
  safe:    { dot: "🟢", accent: "#34d399", bg: "rgba(52,211,153,0.05)", label: "On track"                       },
};

export function BudgetHealthCard({ projection: p }: { projection: ProjectionItem }) {
  const cfg    = STATUS_CONFIG[p.status] ?? STATUS_CONFIG.safe;
  const barW   = Math.min(p.pct_spent, 100);
  const label  =
    p.status === "over"
      ? `🚫 Limit exceeded — ${fmtInr(p.spent - p.limit)} over`
      : cfg.label || `Projected ${fmtInr(p.projected)}`;
  const daysInfo =
    p.days_left > 0
      ? `${p.days_left}d left · ${fmtInr(p.daily_rate)}/day`
      : "Month complete";

  return (
    <div
      className="rounded-2xl p-4 border-l-4"
      style={{ background: cfg.bg, borderColor: cfg.accent }}
    >
      {/* Header row */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-white font-semibold text-sm">
          {cfg.dot} {CATEGORY_ICONS[p.category] ?? "📦"} {p.category}
        </span>
        <span className="text-xs font-semibold" style={{ color: cfg.accent }}>
          {label}
        </span>
      </div>

      {/* Animated progress bar */}
      <div className="h-1.5 rounded-full mb-2 overflow-hidden bg-white/5">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${barW}%`, background: cfg.accent }}
        />
      </div>

      {/* Footer: spent / limit + days */}
      <div className="flex justify-between text-xs" style={{ color: "var(--text-sub)" }}>
        <span>{fmtInr(p.spent)} spent of {fmtInr(p.limit)}</span>
        <span>{daysInfo}</span>
      </div>
    </div>
  );
}
