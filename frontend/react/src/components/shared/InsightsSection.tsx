import { fmtInr } from "@/utils/formatInr";
import { CATEGORY_ICONS } from "@/utils/categories";
import type { Summary } from "@/types";

interface MoMData {
  months:       string[];
  categories:   Record<string, Record<string, number>>;
  days_tracked: Record<string, number>;
}

export function InsightsScenarioA({ summary }: { summary: Summary }) {
  const totalSpent = summary.categories.reduce((s, c) => s + c.spent, 0);
  const top = [...summary.categories].sort((a, b) => b.spent - a.spent)[0];
  const topPct = totalSpent > 0 && top
    ? Math.round(top.spent / totalSpent * 100)
    : null;
  const expenseCount = summary.expense_count ?? null;

  return (
    <div
      className="rounded-2xl border p-4 space-y-3"
      style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
    >
      <p
        className="text-[10px] font-syne font-bold uppercase tracking-widest"
        style={{ color: "var(--accent)" }}
      >
        Your first month 🎉
      </p>
      <div className="space-y-2">
        {expenseCount !== null && (
          <p className="text-sm" style={{ color: "var(--text)" }}>
            📝 You've logged{" "}
            <span className="font-semibold">{expenseCount} expenses</span> so far.
          </p>
        )}
        {top && topPct !== null && (
          <p className="text-sm" style={{ color: "var(--text)" }}>
            🏷️ <span className="font-semibold">{top.category}</span> accounts for{" "}
            <span className="font-semibold">{topPct}%</span> of your spending.
          </p>
        )}
        <p className="text-sm" style={{ color: "var(--text-sub)" }}>
          📅 Continue tracking to unlock monthly comparisons next month.
        </p>
      </div>
    </div>
  );
}

export function InsightsScenarioB({
  mom, summary, curr, prev, onViewAll,
}: {
  mom: MoMData;
  summary: Summary;
  curr: string;
  prev: string;
  onViewAll: () => void;
}) {
  const SAVINGS_CATS = new Set(["Savings", "Investments"]);
  const prevLabel = new Date(prev + "-01").toLocaleString("en-IN", { month: "short" });

  const fmtMoM = (rawPct: number | null, prevAmt: number): string => {
    if (prevAmt === 0) return "New this month";
    if (rawPct === null) return "—";
    if (Math.abs(rawPct) > 300) return rawPct > 0 ? "↑ New high" : "↓ Major drop";
    return `${rawPct > 0 ? "↑" : "↓"} ${Math.abs(Math.round(rawPct))}%`;
  };

  const changes = Object.entries(mom.categories)
    .map(([cat, byMonth]) => ({
      cat,
      currAmt: byMonth[curr] ?? 0,
      prevAmt: byMonth[prev] ?? 0,
      delta:   (byMonth[curr] ?? 0) - (byMonth[prev] ?? 0),
    }))
    .filter(c => c.prevAmt > 0 || c.currAmt > 0)
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
    .slice(0, 4);

  if (changes.length === 0) return null;

  return (
    <div className="space-y-0">
      {changes.map(({ cat, delta, prevAmt, currAmt }) => {
        const isUp = delta > 0;
        const isSavingsCat = SAVINGS_CATS.has(cat);
        const isPositive = isSavingsCat ? isUp : !isUp;
        const dotColour = isPositive ? "#34d399" : "#f87171";
        const rawPct = prevAmt > 0 ? Math.round((delta / prevAmt) * 100) : null;
        const momStr = fmtMoM(rawPct, prevAmt);
        const label = prevAmt === 0 ? momStr : `${momStr} (${fmtInr(Math.abs(delta))})`;

        return (
          <div key={cat} className="flex items-center gap-3 py-2.5 border-b"
               style={{ borderColor: "var(--border-lg)" }}>
            <span className="text-lg w-5 flex-shrink-0 text-center" style={{ color: dotColour }}>
              {isUp ? "↑" : "↓"}
            </span>
            <span className="flex-1 text-sm" style={{ color: "var(--text)" }}>{cat}</span>
            <div className="text-right">
              <span className="text-sm font-syne font-semibold" style={{ color: dotColour }}>
                {label}
              </span>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                {fmtInr(currAmt)} this month
              </p>
            </div>
          </div>
        );
      })}
      <button
        onClick={onViewAll}
        className="text-xs mt-2 w-full text-right transition-opacity hover:opacity-70"
        style={{ color: "var(--accent)" }}
      >
        View all →
      </button>
    </div>
  );
}

export function InsightsScenarioC({
  summary, prev,
}: {
  summary: Summary;
  prev: string;
}) {
  const prevLabel = new Date(prev + "-01")
    .toLocaleString("en-IN", { month: "long", year: "numeric" });
  const top3 = [...summary.categories]
    .sort((a, b) => b.spent - a.spent)
    .slice(0, 3);

  return (
    <div className="space-y-3">
      {/* Gap notice */}
      <div
        className="rounded-2xl border p-4"
        style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
      >
        <p className="text-sm font-medium" style={{ color: "var(--text-sub)" }}>
          📅 Last tracked: <span style={{ color: "var(--text)" }}>{prevLabel}</span>
        </p>
        <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
          Monthly comparisons work best with consecutive months.
        </p>
      </div>

      {/* Current month top spending */}
      {top3.length > 0 && (
        <div>
          <p
            className="text-[10px] font-syne font-bold uppercase tracking-widest mb-2"
            style={{ color: "var(--text-sub)" }}
          >
            This month's top spending
          </p>
          <div className="space-y-0">
            {top3.map(c => (
              <div key={c.category} className="flex items-center gap-3 py-2.5 border-b"
                   style={{ borderColor: "var(--border-lg)" }}>
                <span className="text-lg w-5 flex-shrink-0 text-center">
                  {CATEGORY_ICONS[c.category] ?? "📦"}
                </span>
                <span className="flex-1 text-sm" style={{ color: "var(--text)" }}>
                  {c.category}
                </span>
                <span className="text-sm font-syne font-semibold" style={{ color: "var(--text)" }}>
                  {fmtInr(c.spent)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function InsightsScenarioD({
  currDays, prevDays,
}: {
  currDays: number;
  prevDays: number;
}) {
  const bothSparse = currDays < 10 && prevDays < 10;

  const today         = new Date();
  const daysInMonth   = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
  const daysRemaining = daysInMonth - today.getDate();
  // Shown only when last month's tracking was sparse (<7 days) AND
  // there are days left in the current month to course-correct (>3 days).
  const showDisclaimer = prevDays < 7 && daysRemaining > 3;

  return (
    <div
      className="rounded-2xl border p-4 space-y-2"
      style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
    >
      {bothSparse ? (
        <p className="text-sm" style={{ color: "var(--text-sub)" }}>
          Keep logging expenses to build your financial picture.
        </p>
      ) : (
        <>
          <div className="flex items-center justify-between">
            <p className="text-sm" style={{ color: "var(--text-sub)" }}>
              📊 Tracked this month
            </p>
            <p className="text-sm font-syne font-semibold" style={{ color: "var(--text)" }}>
              {currDays} days
            </p>
          </div>
          <div className="flex items-center justify-between">
            <p className="text-sm" style={{ color: "var(--text-sub)" }}>
              Last month
            </p>
            <p className="text-sm font-syne font-semibold" style={{ color: "#f59e0b" }}>
              {prevDays} days
            </p>
          </div>
          {showDisclaimer && (
            <p className="text-xs pt-1" style={{ color: "var(--text-muted)" }}>
              Monthly comparisons become more accurate with consistent daily tracking.
            </p>
          )}
        </>
      )}
    </div>
  );
}

export { type MoMData };
