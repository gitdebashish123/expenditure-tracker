import { useEffect, useState, useCallback } from "react";
import { Activity, Zap } from "lucide-react";
import { api } from "@/api/client";
import { useMonth } from "@/context/MonthContext";
import { fmtInr } from "@/utils/formatInr";
import { fmtDate } from "@/utils/formatDate";
import { CATEGORY_ICONS, FIXED_CATEGORIES } from "@/utils/categories";
import { BalanceBreakdown } from "@/components/shared/BalanceBreakdown";
import { SpendDonut } from "@/components/shared/SpendDonut";
import { BudgetHealthCard } from "@/components/shared/BudgetHealthCard";
import { useToast } from "@/context/ToastContext";
import type { Summary, ProjectionItem, DueReminder, MonthlyStory, TinyWin } from "@/types";

/**
 * OverviewTab — full financial dashboard for the selected month
 *
 * Streamlit ref: with tab3: in frontend/app.py
 *
 * Sections:
 *   1. Balance summary cards (3-col grid)
 *   2. Balance breakdown stacked bar
 *   3. Spend donut chart (bonus — not in Streamlit)
 *   4. Budget health projection cards
 *   5. Top spends #1–5
 *   6. Month-over-Month table
 *
 * Key improvements over Streamlit:
 *   - Recharts charts replace custom HTML div constructions
 *   - Animated progress bars on budget health cards
 *   - MoM table scrolls horizontally on mobile
 *   - Balance cards use CSS grid — Streamlit st.columns collapses on mobile
 */

// ── Local types ────────────────────────────────────────────────────────────────

interface TopSpend {
  vendor:   string;
  amount:   number;
  category: string;
  date:     string;
  note:     string | null;
}

interface MoMData {
  months:     string[];
  categories: Record<string, Record<string, number>>;
}

// ── Sub-components ─────────────────────────────────────────────────────────────

const RANK_COLOURS = ["#f59e0b", "#94a3b8", "#b45309", "#6366f1", "#6366f1"];

const DONUT_FILTERS = [
  { value: "variable" as const, label: "Day-to-day"  },
  { value: "fixed"    as const, label: "Fixed Bills"  },
  { value: "all"      as const, label: "All"          },
];

function TopSpendRow({ rank, item }: { rank: number; item: TopSpend }) {
  const icon = CATEGORY_ICONS[item.category] ?? "📦";
  return (
    <div className="flex items-center gap-3 py-3 border-b border-white/5">
      {/* Rank number */}
      <span
        className="font-syne font-extrabold text-lg w-7 text-center flex-shrink-0"
        style={{ color: RANK_COLOURS[rank - 1] }}
      >
        #{rank}
      </span>

      {/* Category icon */}
      <div className="w-9 h-9 bg-dark-card2 rounded-xl flex items-center justify-center
                      text-lg flex-shrink-0">
        {icon}
      </div>

      {/* Vendor + category + date */}
      <div className="flex-1 min-w-0">
        <p className="text-white text-sm font-medium truncate">
          {item.vendor}
          {item.note && (
            <span className="ml-2 text-xs" style={{ color: "var(--text-muted)" }}>
              · {item.note}
            </span>
          )}
        </p>
        <p className="text-xs" style={{ color: "var(--text-sub)" }}>
          {item.category} · {fmtDate(item.date)}
        </p>
      </div>

      {/* Amount */}
      <span className="font-syne font-bold text-red-400 flex-shrink-0 text-sm">
        {fmtInr(item.amount)}
      </span>
    </div>
  );
}

function OverviewSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {/* 3 balance cards */}
      <div className="grid grid-cols-3 gap-3">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-20 bg-white/5 rounded-2xl" />
        ))}
      </div>
      {/* Breakdown bar */}
      <div className="h-16 bg-white/5 rounded-2xl" />
      {/* Donut placeholder */}
      <div className="h-48 bg-white/5 rounded-2xl" />
      {/* Budget health cards */}
      {[1, 2, 3].map(i => (
        <div key={i} className="h-16 bg-white/5 rounded-2xl" />
      ))}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

export function OverviewTab() {
  const { selMonth } = useMonth();
  const { toast } = useToast();

  const [summary,      setSummary]      = useState<Summary | null>(null);
  const [projections,  setProjections]  = useState<ProjectionItem[]>([]);
  const [topSpends,    setTopSpends]    = useState<TopSpend[]>([]);
  const [mom,          setMom]          = useState<MoMData | null>(null);
  const [dueReminders, setDueReminders] = useState<DueReminder[]>([]);
  const [story,        setStory]        = useState<string | null>(null);
  const [tinyWin,      setTinyWin]      = useState<string | null>(null);
  const [loading,           setLoading]          = useState(true);
  const [donutFilter,       setDonutFilter]       = useState<"variable" | "fixed" | "all">("variable");
  const [showPomBreakdown,  setShowPomBreakdown]  = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [sum, proj, top, momData, reminders, storyResult, tinyWinResult] = await Promise.all([
        api.get<Summary>(`/summary/${selMonth}`).then(r => r.data),
        api.get<ProjectionItem[]>(`/insights/projection/${selMonth}`).then(r => r.data),
        api.get<TopSpend[]>(`/insights/top-spends/${selMonth}?limit=5`).then(r => r.data),
        api.get<MoMData>(`/insights/mom/${selMonth}`).then(r => r.data),
        // Correct path is /fixed/due-reminders/ (not /insights/due-reminders/)
        api.get<DueReminder[]>(`/fixed/due-reminders/${selMonth}`).then(r => r.data).catch((): DueReminder[] => []),
        api.get<MonthlyStory>(`/insights/story/${selMonth}`).then(r => r.data.story).catch(() => null),
        api.get<TinyWin>(`/insights/tiny-win/${selMonth}`).then(r => r.data.win).catch(() => null),
      ]);
      setSummary(sum);
      setProjections(proj);
      setTopSpends(top);
      setMom(momData);
      setDueReminders(reminders);
      setStory(storyResult);
      setTinyWin(tinyWinResult);
    } catch {
      // leave state as null — empty state renders
    } finally {
      setLoading(false);
    }
  }, [selMonth]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <OverviewSkeleton />;

  // Empty state — no data for this month
  if (!summary) {
    return (
      <div className="text-center py-16">
        <div className="text-4xl mb-3">📊</div>
        <p className="text-sm mb-1" style={{ color: "var(--text-muted)" }}>
          No data yet this month.
        </p>
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          Head to{" "}
          <span className="text-indigo-400">Today</span>
          {" "}to log expenses or{" "}
          <span className="text-indigo-400">Settings → My Take-home</span>
          {" "}to record income.
        </p>
      </div>
    );
  }

  const { balance } = summary;

  return (
    <div className="space-y-6">

      {/* ── Section 0: Financial Snapshot ────────────────── */}
      <section>
        <h2
          className="text-xs font-syne font-bold uppercase tracking-widest mb-3"
          style={{ color: "var(--text-sub)" }}
        >
          Financial Snapshot
        </h2>
        <div className="grid grid-cols-2 gap-3">
          {[
            {
              label:  "Remaining",
              value:  balance.remaining,
              icon:   "💰",
              colour: balance.remaining >= 0 ? "#34d399" : "#f87171",
            },
            {
              label:  "Income",
              value:  balance.total_income,
              icon:   "💼",
              colour: "#6366f1",
            },
            {
              label:  "Fixed Paid",
              value:  balance.fixed_paid_total,
              icon:   "✅",
              colour: "#f59e0b",
            },
            {
              label:  balance.fixed_unpaid_total === 0 ? "All Bills Clear ✓" : "Pending Bills",
              value:  balance.fixed_unpaid_total,
              icon:   balance.fixed_unpaid_total === 0 ? "🎉" : "⏳",
              colour: balance.fixed_unpaid_total === 0 ? "#34d399" : "#f87171",
            },
          ].map(tile => (
            <div
              key={tile.label}
              className="rounded-2xl p-4 border"
              style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
            >
              <div className="flex items-center gap-1.5 mb-2">
                <span className="text-base">{tile.icon}</span>
                <p
                  className="text-[10px] font-syne font-bold uppercase tracking-widest"
                  style={{ color: "var(--text-sub)" }}
                >
                  {tile.label}
                </p>
              </div>
              <p className="text-lg font-syne font-bold" style={{ color: tile.colour }}>
                {fmtInr(tile.value)}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Section 0b: This Month's Story ───────────────── */}
      {story && (
        <section>
          <div
            className="rounded-2xl border p-5 flex items-start gap-4 overflow-hidden"
            style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5 mb-2">
                <span style={{ color: "#f59e0b" }}>✦</span>
                <p
                  className="text-[10px] font-syne font-bold uppercase tracking-widest"
                  style={{ color: "var(--text-sub)" }}
                >
                  {new Date(selMonth + "-01").toLocaleString("en-IN", { month: "long" })} in one sentence
                </p>
              </div>
              <p className="text-sm leading-relaxed" style={{ color: "var(--text)" }}>
                {story}
              </p>
            </div>
            {/* Decorative illustration */}
            <div
              className="hidden sm:flex flex-col items-center justify-center flex-shrink-0
                         text-4xl leading-none select-none opacity-50"
              style={{ width: 72, height: 72 }}
              aria-hidden="true"
            >
              <span>📅</span>
              <span className="text-xl mt-1">✨</span>
            </div>
          </div>
        </section>
      )}

      {/* ── Sections 1+2: Monthly Breakdown + Spend by Category (side-by-side) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">

        {/* ── Section 1: Monthly breakdown bar + Insight ───── */}
        <section>
          <BalanceBreakdown balance={balance} />

          {/* Insight row — variable spend % vs historical avg from mom data */}
          {balance.total_income > 0 && (() => {
            const varPct = Math.round(balance.variable_total / balance.total_income * 100);
            const priorVars = mom?.months.slice(0, -1).map(m =>
              Object.entries(mom.categories)
                .filter(([cat]) => !FIXED_CATEGORIES.includes(cat))
                .reduce((s, [, byM]) => s + (byM[m] ?? 0), 0)
            ) ?? [];
            const avgVarPct = priorVars.length > 0
              ? Math.round(priorVars.reduce((a, b) => a + b, 0) / priorVars.length / balance.total_income * 100)
              : null;
            return (
              <div
                className="mt-3 flex gap-2.5 p-3 rounded-xl"
                style={{ background: "var(--card2)", border: "1px solid var(--border)" }}
              >
                <Zap size={14} style={{ color: "#f59e0b", flexShrink: 0, marginTop: 1 }} />
                <div>
                  <p
                    className="text-[10px] font-syne font-bold uppercase tracking-widest mb-1"
                    style={{ color: "var(--text-sub)" }}
                  >
                    Insight
                  </p>
                  <p className="text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>
                    Variable spending consumed {varPct}% of income this month.
                    {avgVarPct !== null &&
                      ` Your average over the last ${priorVars.length} month${priorVars.length > 1 ? "s" : ""} is ${avgVarPct}%.`}
                  </p>
                </div>
              </div>
            );
          })()}
        </section>

        {/* ── Section 2: Spend donut + Category Winner ──────── */}
        {summary.categories.length > 0 && (
          <section>
            <div
              className="rounded-2xl border p-4"
              style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
            >
              {/* Header + filter tabs */}
              <div className="flex items-center justify-between mb-3">
                <h2
                  className="text-xs font-syne font-bold uppercase tracking-widest"
                  style={{ color: "var(--text-sub)" }}
                >
                  Spend by Category
                </h2>
                <div className="flex gap-1.5">
                  {DONUT_FILTERS.map(f => (
                    <button
                      key={f.value}
                      onClick={() => setDonutFilter(f.value)}
                      className="text-xs px-2.5 py-1 rounded-lg border transition-colors"
                      style={{
                        background:  donutFilter === f.value ? "var(--accent-bg)" : "transparent",
                        borderColor: donutFilter === f.value ? "var(--accent)"    : "var(--border-lg)",
                        color:       donutFilter === f.value ? "var(--accent)"    : "var(--text)",
                        fontWeight:  donutFilter === f.value ? 600 : 400,
                      }}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Donut (left) + category list (right) */}
              <SpendDonut
                sidebar
                categories={summary.categories.filter(c =>
                  donutFilter === "all"
                    ? true
                    : donutFilter === "fixed"
                      ? FIXED_CATEGORIES.includes(c.category)
                      : !FIXED_CATEGORIES.includes(c.category)
                )}
              />

              {/* ── Category Winner ─────────────────────────── */}
              {(() => {
                const varCats = summary.categories.filter(c => !FIXED_CATEGORIES.includes(c.category));
                if (varCats.length === 0) return null;
                const top = [...varCats].sort((a, b) => b.spent - a.spent)[0];
                const pctOfVar = balance.variable_total > 0
                  ? Math.round(top.spent / balance.variable_total * 100)
                  : 0;
                const curr = mom?.months[mom.months.length - 1];
                const prev = mom && mom.months.length >= 2 ? mom.months[mom.months.length - 2] : null;
                const topCurr = curr ? (mom?.categories[top.category]?.[curr] ?? 0) : 0;
                const topPrev = prev ? (mom?.categories[top.category]?.[prev] ?? 0) : 0;
                const momPct  = topPrev > 0
                  ? Math.round((topCurr - topPrev) / topPrev * 100)
                  : null;
                const prevLabel = prev
                  ? new Date(prev + "-01").toLocaleString("en-IN", { month: "short" })
                  : null;

                return (
                  <div
                    className="mt-4 pt-4 border-t"
                    style={{ borderColor: "var(--border-lg)" }}
                  >
                    <p
                      className="text-[10px] font-syne font-bold uppercase tracking-widest mb-2"
                      style={{ color: "var(--text-sub)" }}
                    >
                      Category Winner
                    </p>
                    <div className="flex items-center gap-3">
                      <span className="text-2xl flex-shrink-0">🏆</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-syne font-bold" style={{ color: "var(--text)" }}>
                          {top.category}
                        </p>
                        <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                          {fmtInr(top.spent)} spent ({pctOfVar}% of variable expenses)
                        </p>
                      </div>
                      {momPct !== null && prevLabel && (
                        <div className="text-right flex-shrink-0">
                          <p className="text-sm font-syne font-bold" style={{ color: "var(--text-sub)" }}>
                            {momPct >= 0 ? "↑" : "↓"} {Math.abs(momPct)}%
                          </p>
                          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                            vs {prevLabel}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })()}
            </div>
          </section>
        )}

      </div>

      {/* ── Section 5: Top spends ─────────────────────────── */}
      {topSpends.length > 0 && (
        <section>
          <h2
            className="text-xs font-syne font-bold uppercase tracking-widest mb-3"
            style={{ color: "var(--text-sub)" }}
          >
            Top Spends This Month
          </h2>
          <div className="space-y-0">
            {topSpends.map((t, i) => (
              <TopSpendRow key={i} rank={i + 1} item={t} />
            ))}
          </div>
        </section>
      )}

      {/* ── Section 6: Financial Pulse ───────────────────── */}
      {summary && (() => {
        const [year, month] = selMonth.split("-").map(Number);
        const today = new Date();
        const isCurrentMonth =
          today.getFullYear() === year && (today.getMonth() + 1) === month;
        const daysInMonth = new Date(year, month, 0).getDate();
        const daysElapsed = isCurrentMonth ? Math.max(today.getDate(), 1) : daysInMonth;

        // Stability signal — fixed obligations completion
        const fixedTotal  = balance.fixed_paid_total + balance.fixed_unpaid_total;
        const unpaidFrac  = fixedTotal > 0 ? balance.fixed_unpaid_total / fixedTotal : 0;
        const stabilityColour =
          balance.fixed_unpaid_total === 0 ? "#34d399" :
          unpaidFrac < 0.30               ? "#f59e0b" : "#f87171";
        const stabilityDesc =
          balance.fixed_unpaid_total === 0 ? "All fixed obligations complete."          :
          unpaidFrac < 0.30               ? "Fixed obligations are nearly complete."    : "Fixed obligations pending.";

        // Lifestyle signal — food spend + variable pace vs previous month
        const prevMonthIdx = mom ? mom.months.indexOf(selMonth) - 1 : -1;
        const prevMonthKey = mom && prevMonthIdx >= 0 ? mom.months[prevMonthIdx] : null;
        const foodCurr = mom?.categories["Food"]?.[selMonth] ?? 0;
        const foodPrev = prevMonthKey ? (mom?.categories["Food"]?.[prevMonthKey] ?? 0) : 0;
        const foodPct  = foodPrev > 0 ? (foodCurr / foodPrev) * 100 : null;
        const dailyRate = daysElapsed > 0 ? balance.variable_total / daysElapsed : 0;
        const prevDaysInMonth = prevMonthKey
          ? new Date(Number(prevMonthKey.split("-")[0]), Number(prevMonthKey.split("-")[1]), 0).getDate()
          : 0;
        const varPrevTotal = prevMonthKey
          ? Object.entries(mom?.categories ?? {})
              .filter(([cat]) => !FIXED_CATEGORIES.includes(cat))
              .reduce((s, [, byM]) => s + (byM[prevMonthKey!] ?? 0), 0)
          : 0;
        const prevDailyRate = prevDaysInMonth > 0 ? varPrevTotal / prevDaysInMonth : 0;
        const pacePct = prevDailyRate > 0 ? (dailyRate / prevDailyRate) * 100 : null;
        const noLifestyleData = foodPct == null && pacePct == null;
        const lifestyleColour =
          noLifestyleData                                                             ? "#94a3b8" :
          (foodPct != null && foodPct > 130) || (pacePct != null && pacePct > 130)  ? "#f87171" :
          (foodPct != null && foodPct > 100) || (pacePct != null && pacePct > 100)  ? "#f59e0b" :
          "#34d399";

        // Savings signal — savings_total as % of income
        const savingsPct = balance.total_income > 0
          ? ((balance.savings_total ?? 0) / balance.total_income) * 100
          : -1;
        const savingsColour =
          savingsPct < 0   ? "#94a3b8" :
          savingsPct >= 20 ? "#34d399" :
          savingsPct >= 10 ? "#f59e0b" : "#f87171";

        // Consistency signal — proxy until real streak data is available
        // TODO: replace with real streak
        const daysTracked = new Date().getDate();

        const lifestyleDesc =
          noLifestyleData                                                            ? "No prior data to compare."            :
          (foodPct != null && foodPct > 130) || (pacePct != null && pacePct > 130) ? "Food spending accelerated this month." :
          (foodPct != null && foodPct > 100) || (pacePct != null && pacePct > 100) ? "Food and spending above normal."       :
          "Spending pace is on track.";
        const savingsDesc =
          savingsPct < 0   ? "No income recorded."                              :
          savingsPct >= 20 ? `${Math.round(savingsPct)}% of income protected.` :
          savingsPct >= 10 ? "Savings moderate this month."                     :
          "Savings below target.";
        const consistencyDesc = `Tracked expenses on ${daysTracked} days this month.`;

        const signals = [
          { icon: "🛡️", name: "Stability",   desc: stabilityDesc,   colour: stabilityColour  },
          { icon: "🔥", name: "Lifestyle",   desc: lifestyleDesc,   colour: lifestyleColour  },
          { icon: "🐷", name: "Savings",     desc: savingsDesc,     colour: savingsColour    },
          { icon: "🎯", name: "Consistency", desc: consistencyDesc, colour: "#34d399"        },
        ];

        return (
          <section>
            <div
              className="rounded-2xl border overflow-hidden"
              style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
            >
              {/* Header */}
              <div
                className="px-4 py-3 flex items-center gap-2 border-b"
                style={{ borderColor: "var(--border-lg)" }}
              >
                <Activity size={13} strokeWidth={2.5} style={{ color: "#34d399" }} />
                <p
                  className="text-[10px] font-syne font-bold uppercase tracking-widest"
                  style={{ color: "var(--text-sub)" }}
                >
                  Financial Pulse
                </p>
              </div>
              {/* 4-column signal grid — 2 cols on mobile, 4 on sm+ */}
              <div className="grid grid-cols-2 sm:grid-cols-4">
                {signals.map((s, i) => {
                  const rightBorder =
                    i === 0 || i === 2 ? "border-r" :
                    i === 1            ? "sm:border-r" : "";
                  const bottomBorder = i < 2 ? "border-b sm:border-b-0" : "";
                  return (
                    <div
                      key={s.name}
                      className={`p-4 ${rightBorder} ${bottomBorder}`}
                      style={{ borderColor: "var(--border-lg)" }}
                    >
                      <span className="text-xl">{s.icon}</span>
                      <p
                        className="text-sm font-syne font-semibold mt-2"
                        style={{ color: s.colour }}
                      >
                        {s.name}
                      </p>
                      <p className="text-xs mt-1 leading-relaxed" style={{ color: "var(--text-muted)" }}>
                        {s.desc}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>
        );
      })()}

      {/* ── Section 7: Upcoming Reality ──────────────────── */}
      <section>
        <h2
          className="text-xs font-syne font-bold uppercase tracking-widest mb-3"
          style={{ color: "var(--text-sub)" }}
        >
          Upcoming Reality
        </h2>
        <div
          className="rounded-2xl border overflow-hidden"
          style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
        >
          {/* Next due bill row */}
          <div className="p-4">
            {dueReminders.length === 0 ? (
              <p className="text-sm font-medium" style={{ color: "#34d399" }}>
                🎉 All bills paid this month
              </p>
            ) : (
              (() => {
                const next = [...dueReminders].sort(
                  (a, b) => a.days_overdue - b.days_overdue
                )[0];
                return (
                  <div className="flex items-center gap-3">
                    <span className="text-xl">📅</span>
                    <div className="flex-1">
                      <p className="text-sm font-medium" style={{ color: "var(--text)" }}>
                        {next.vendor}
                      </p>
                      <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                        {next.days_overdue < 0
                          ? `Due in ${Math.abs(next.days_overdue)} day${Math.abs(next.days_overdue) > 1 ? "s" : ""}`
                          : next.days_overdue === 0
                          ? "Due today"
                          : `${next.days_overdue} day${next.days_overdue > 1 ? "s" : ""} overdue`}
                      </p>
                    </div>
                    <span
                      className="font-syne font-bold text-sm flex-shrink-0"
                      style={{ color: "#f87171" }}
                    >
                      {fmtInr(next.amount)}
                    </span>
                  </div>
                );
              })()
            )}
          </div>

          {/* Divider */}
          <div className="h-px mx-4" style={{ background: "var(--border-lg)" }} />

          {/* Month-end estimate */}
          <div className="p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                Expected month-end balance
              </p>
              <p
                className="font-syne font-bold text-sm"
                style={{
                  color:
                    balance.remaining - balance.fixed_unpaid_total >= 0
                      ? "#34d399"
                      : "#f87171",
                }}
              >
                {fmtInr(balance.remaining - balance.fixed_unpaid_total)}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Section 8: What Changed? ─────────────────────── */}
      {mom && (() => {
        const SAVINGS_CATS = new Set(["Savings", "Investments"]);

        // ── Scenario 2: first month — no prior data, show spending highlights ──
        if (mom.months.length < 2) {
          const highlights = [...summary.categories]
            .filter(c => c.spent > 0)
            .sort((a, b) => b.spent - a.spent)
            .slice(0, 3);
          if (highlights.length === 0) return null;
          return (
            <section>
              <h2
                className="text-xs font-syne font-bold uppercase tracking-widest mb-1"
                style={{ color: "var(--text-sub)" }}
              >
                Spending Highlights
              </h2>
              <p className="text-xs mb-3" style={{ color: "var(--text-muted)" }}>
                Your first month — no prior comparison yet
              </p>
              <div className="space-y-0">
                {highlights.map(({ category, spent }) => (
                  <div key={category} className="flex items-center gap-3 py-2.5 border-b"
                       style={{ borderColor: "var(--border-lg)" }}>
                    <span className="text-lg w-5 flex-shrink-0 text-center">
                      {CATEGORY_ICONS[category] ?? "📦"}
                    </span>
                    <span className="flex-1 text-sm" style={{ color: "var(--text)" }}>
                      {category}
                    </span>
                    <span className="text-sm font-syne font-semibold"
                          style={{ color: "var(--text)" }}>
                      {fmtInr(spent)}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          );
        }

        const curr = mom.months[mom.months.length - 1];
        const prev = mom.months[mom.months.length - 2];
        const prevLabel = new Date(prev + "-01").toLocaleString("en-IN", { month: "short" });

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

        // ── Scenario 3: exactly 1 prior month — ₹ delta only, no percentage ──
        if (mom.months.length === 2) {
          return (
            <section>
              <h2
                className="text-xs font-syne font-bold uppercase tracking-widest mb-1"
                style={{ color: "var(--text-sub)" }}
              >
                What Changed?
              </h2>
              <p className="text-xs mb-3" style={{ color: "var(--text-muted)" }}>
                vs {prevLabel}
              </p>
              <div className="space-y-0">
                {changes.map(({ cat, delta, prevAmt, currAmt }) => {
                  const isUp = delta > 0;
                  const isSavingsCat = SAVINGS_CATS.has(cat);
                  const isPositive = isSavingsCat ? isUp : !isUp;
                  const dotColour = isPositive ? "#34d399" : "#f87171";
                  const icon = isUp ? "↑" : "↓";
                  const label = currAmt > 0 && prevAmt === 0
                    ? "New this month"
                    : `${icon} ${fmtInr(Math.abs(delta))}`;

                  return (
                    <div key={cat} className="flex items-center gap-3 py-2.5 border-b"
                         style={{ borderColor: "var(--border-lg)" }}>
                      <span className="text-lg w-5 flex-shrink-0 text-center"
                            style={{ color: currAmt > 0 && prevAmt === 0 ? "var(--text-muted)" : dotColour }}>
                        {currAmt > 0 && prevAmt === 0 ? "✦" : icon}
                      </span>
                      <span className="flex-1 text-sm" style={{ color: "var(--text)" }}>
                        {cat}
                      </span>
                      <div className="text-right">
                        <span className="text-sm font-syne font-semibold"
                              style={{ color: currAmt > 0 && prevAmt === 0 ? "var(--text-muted)" : dotColour }}>
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
                  onClick={() => toast("Full breakdown coming soon.")}
                  className="text-xs mt-2 w-full text-right transition-opacity hover:opacity-70"
                  style={{ color: "var(--accent)" }}
                >
                  View all →
                </button>
              </div>
            </section>
          );
        }

        // ── Scenario 1: 2+ prior months — full comparison with percentage ──
        return (
          <section>
            <h2
              className="text-xs font-syne font-bold uppercase tracking-widest mb-1"
              style={{ color: "var(--text-sub)" }}
            >
              What Changed?
            </h2>
            <p className="text-xs mb-3" style={{ color: "var(--text-muted)" }}>
              vs {prevLabel}
            </p>
            <div className="space-y-0">
              {changes.map(({ cat, delta, prevAmt, currAmt }) => {
                const isUp = delta > 0;
                const isSavingsCat = SAVINGS_CATS.has(cat);
                const isPositive = isSavingsCat ? isUp : !isUp;
                const dotColour = isPositive ? "#34d399" : "#f87171";
                const icon = isUp ? "↑" : "↓";
                const pct = prevAmt > 0
                  ? Math.abs(Math.round((delta / prevAmt) * 100))
                  : null;
                const label = pct != null
                  ? `${icon} ${pct}% (${fmtInr(Math.abs(delta))})`
                  : `${icon} ${fmtInr(Math.abs(delta))}`;

                return (
                  <div key={cat} className="flex items-center gap-3 py-2.5 border-b"
                       style={{ borderColor: "var(--border-lg)" }}>
                    <span className="text-lg w-5 flex-shrink-0 text-center"
                          style={{ color: dotColour }}>
                      {icon}
                    </span>
                    <span className="flex-1 text-sm" style={{ color: "var(--text)" }}>
                      {cat}
                    </span>
                    <div className="text-right">
                      <span className="text-sm font-syne font-semibold"
                            style={{ color: dotColour }}>
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
                onClick={() => toast("Full breakdown coming soon.")}
                className="text-xs mt-2 w-full text-right transition-opacity hover:opacity-70"
                style={{ color: "var(--accent)" }}
              >
                View all →
              </button>
            </div>
          </section>
        );
      })()}

      {/* ── Section 9: Peace of Mind Score ───────────────── */}
      {summary.peace_of_mind && (() => {
        const pom = summary.peace_of_mind!;
        const scoreColour = pom.score >= 80 ? "#34d399" : pom.score >= 60 ? "#6366f1" : pom.score >= 40 ? "#f59e0b" : "#f87171";

        const breakdown = [
          { key: "bills",    label: "Bills paid",   max: 35, pts: pom.breakdown.bills },
          { key: "buffer",   label: "Buffer",        max: 30, pts: pom.breakdown.buffer },
          { key: "pace",     label: "Spending pace", max: 20, pts: pom.breakdown.pace },
          { key: "tracking", label: "Tracking",      max: 15, pts: pom.breakdown.tracking, note: "placeholder" },
        ];

        return (
          <section>
            <div
              className="rounded-2xl border p-4"
              style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p
                    className="text-[10px] font-syne font-bold uppercase tracking-widest mb-1"
                    style={{ color: "var(--text-sub)" }}
                  >
                    Peace of Mind
                  </p>
                  <p className="text-3xl font-syne font-extrabold leading-none" style={{ color: scoreColour }}>
                    {pom.score}
                    <span className="text-base font-normal ml-0.5" style={{ color: "var(--text-muted)" }}>/100</span>
                  </p>
                  <p className="text-sm mt-1" style={{ color: "var(--text-sub)" }}>{pom.label}</p>
                </div>
                <button
                  onClick={() => setShowPomBreakdown(v => !v)}
                  className="text-xs font-syne font-semibold transition-opacity hover:opacity-70"
                  style={{ color: "var(--accent)" }}
                >
                  {showPomBreakdown ? "↑ Hide" : "Why this score? ↓"}
                </button>
              </div>

              {showPomBreakdown && (
                <div className="mt-4 space-y-2 border-t pt-3" style={{ borderColor: "var(--border-lg)" }}>
                  {breakdown.map(b => (
                    <div key={b.key} className="flex items-center justify-between text-xs">
                      <span style={{ color: "var(--text-sub)" }}>
                        {b.label}
                        {b.note && <span style={{ color: "var(--text-muted)" }}> (placeholder)</span>}
                      </span>
                      <span className="font-syne font-semibold" style={{ color: b.pts === b.max ? "#34d399" : "var(--text)" }}>
                        {b.pts}/{b.max}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        );
      })()}

      {/* ── Section 10: Budget health ─────────────────────── */}
      {projections.length > 0 && (
        <section>
          <h2
            className="text-xs font-syne font-bold uppercase tracking-widest mb-3"
            style={{ color: "var(--text-sub)" }}
          >
            Budget Health
          </h2>
          <div className="space-y-3">
            {projections.map(p => (
              <BudgetHealthCard key={p.category} projection={p} />
            ))}
          </div>
        </section>
      )}

      {/* ── Section 11: Tiny Win ─────────────────────────── */}
      {tinyWin && (
        <section>
          <div
            className="rounded-2xl p-4 border flex items-center gap-4"
            style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
          >
            <span className="text-2xl flex-shrink-0">🏆</span>
            <div>
              <p
                className="text-[10px] font-syne font-bold uppercase tracking-widest mb-1"
                style={{ color: "#f59e0b" }}
              >
                Tiny Win
              </p>
              <p className="text-sm leading-relaxed" style={{ color: "var(--text)" }}>
                {tinyWin}
              </p>
            </div>
          </div>
        </section>
      )}

    </div>
  );
}
