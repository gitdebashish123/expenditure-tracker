import type { ProjectionItem } from "@/types";
import { fmtInr } from "@/utils/formatInr";
import { CATEGORY_ICONS } from "@/utils/categories";

function getSignalState(ratio: number, spent: number, limit: number) {
  if (ratio > 1)    return { badge: `Over by ${fmtInr(spent - limit)}`, colour: "#f87171", bg: "#2e1414" };
  if (ratio >= 0.8) return { badge: "Almost full",                       colour: "#f59e0b", bg: "#2e200a" };
  return                   { badge: "On track",                          colour: "#34d399", bg: "#0e2419" };
}

export function SignalCard({ p }: { p: ProjectionItem }) {
  const ratio = p.limit > 0 ? p.spent / p.limit : 0;
  const pct   = Math.round(ratio * 100);
  const sig   = getSignalState(ratio, p.spent, p.limit);
  const icon  = CATEGORY_ICONS[p.category] ?? "📦";
  const dailyRate =
    p.days_left > 0 && p.spent <= p.limit
      ? `${fmtInr(p.daily_rate)}/day left`
      : p.spent > p.limit
      ? `${fmtInr(p.spent - p.limit)} over`
      : null;

  return (
    <div
      className="rounded-2xl p-4"
      style={{ background: sig.bg, border: `1px solid ${sig.colour}30` }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-white truncate">
            {icon} {p.category}
          </p>
          <p className="text-xs mt-0.5 font-medium" style={{ color: sig.colour }}>
            {sig.badge}
          </p>
          <p className="text-xs mt-1" style={{ color: "var(--text-sub)" }}>
            {fmtInr(p.spent)} of {fmtInr(p.limit)}
          </p>
        </div>
        <div className="text-right flex-shrink-0">
          <p className="font-syne font-bold text-lg" style={{ color: sig.colour }}>
            {pct}%
          </p>
          {dailyRate && (
            <p className="text-[10px]" style={{ color: "var(--text-sub)" }}>
              {dailyRate}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export function SpendingSignalsModal({
  open,
  onClose,
  projections,
}: {
  open: boolean;
  onClose: () => void;
  projections: ProjectionItem[];
}) {
  if (!open) return null;
  return (
    <>
      {/* Backdrop */}
      <div
        style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 50 }}
        onClick={onClose}
      />
      {/* Sheet */}
      <div
        style={{
          position:    "fixed",
          bottom:      0,
          left:        0,
          right:       0,
          maxHeight:   "85vh",
          overflowY:   "auto",
          zIndex:      51,
          background:  "var(--card)",
          borderRadius: "1.25rem 1.25rem 0 0",
        }}
      >
        {/* Drag handle */}
        <div className="flex justify-center pt-3 pb-1">
          <div className="w-10 h-1 rounded-full bg-white/20" />
        </div>
        <div className="px-4 pb-8">
          <h2
            className="text-xs font-syne font-bold uppercase tracking-widest mb-4 mt-2"
            style={{ color: "var(--text-sub)" }}
          >
            Spending Signals
          </h2>
          <div className="space-y-3">
            {projections
              .filter(p => p.limit > 0)
              .map(p => (
                <SignalCard key={p.category} p={p} />
              ))}
          </div>
        </div>
      </div>
    </>
  );
}
