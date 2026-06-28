import { useEffect, useState, useCallback, useRef } from "react";
import { Activity, ChevronDown } from "lucide-react";
import { api } from "@/api/client";
import { useMonth } from "@/context/MonthContext";
import { fmtInr } from "@/utils/formatInr";
import { fmtDate } from "@/utils/formatDate";
import { CATEGORY_ICONS, FIXED_CATEGORIES } from "@/utils/categories";
import { BalanceBreakdown } from "@/components/shared/BalanceBreakdown";
import { SpendDonut } from "@/components/shared/SpendDonut";
import { SignalCard, SpendingSignalsModal } from "@/components/shared/SpendingSignalsModal";
import { useToast } from "@/context/ToastContext";
import type { Summary, ProjectionItem, DueReminder, MonthlyStory, TinyWin, PeaceOfMind } from "@/types";
import { InsightsScenarioA, InsightsScenarioB, InsightsScenarioC, InsightsScenarioD } from "@/components/shared/InsightsSection";

/**
 * OverviewTab — full financial dashboard for the selected month
 *
 * Streamlit ref: with tab3: in frontend/app.py
 *
 * Sections:
 *   1. KPI carousel (swipeable, 3 cards: Remaining / Income / Bills Paid)
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
  months:      string[];
  categories:  Record<string, Record<string, number>>;
  days_tracked: Record<string, number>;
}

// ── Sub-components ─────────────────────────────────────────────────────────────

const RANK_COLOURS = ["#f59e0b", "#94a3b8", "#b45309", "#6366f1", "#6366f1"];

const DONUT_FILTERS = [
  { value: "variable" as const, label: "Variable"    },
  { value: "fixed"    as const, label: "Fixed Bills"  },
  { value: "all"      as const, label: "All"          },
];

const getContextBadge = (tx: TopSpend, rank: number): { label: string; colour: string } | null => {
  if (rank === 1) return { label: "🏆 Biggest Purchase", colour: "#f59e0b" };
  if (["Savings", "Investments", "Mutual Fund"].includes(tx.category))
    return { label: "📈 Investment", colour: "#818cf8" };
  if (["Course", "Education"].includes(tx.category))
    return { label: "📚 Learning", colour: "#818cf8" };
  if (["Travel", "Medical", "Rent", "Cook", "Milk", "Electricity"].includes(tx.category))
    return { label: "🚗 Essential", colour: "#94a3b8" };
  if (tx.category === "Gifts")
    return { label: "❤️ Special Moment", colour: "#f472b6" };
  if (rank === 2) return { label: "👑 Top Spend", colour: "#f59e0b" };
  return null;
};

const VENDOR_INITIAL_PALETTE = [
  "#6366f1", "#8b5cf6", "#ec4899", "#f59e0b", "#14b8a6", "#3b82f6", "#f87171", "#34d399",
];

function vendorInitialColour(name: string) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = name.charCodeAt(i) + ((h << 5) - h);
  return VENDOR_INITIAL_PALETTE[Math.abs(h) % VENDOR_INITIAL_PALETTE.length];
}

function TopSpendRow({ rank, item, varTotal }: { rank: number; item: TopSpend; varTotal: number }) {
  const catIcon = CATEGORY_ICONS[item.category];
  const useFallback = !catIcon || catIcon === "📦";
  const badge = getContextBadge(item, rank);
  const pctOfVar = varTotal > 0 ? Math.round(item.amount / varTotal * 100) : null;
  const initials = item.vendor.slice(0, 2).toUpperCase();
  const bgColour = vendorInitialColour(item.vendor);

  return (
    <div className="flex items-center gap-3 py-3 border-b border-white/5">
      {/* Rank indicator — gold background for rank 1 */}
      <span
        className="font-syne font-extrabold text-base w-7 h-7 flex items-center justify-center rounded-lg flex-shrink-0"
        style={{
          color:      rank === 1 ? "#111"    : RANK_COLOURS[rank - 1],
          background: rank === 1 ? "#f59e0b" : "transparent",
        }}
      >
        {rank}
      </span>

      {/* Category icon — or vendor initial avatar for Miscellaneous */}
      <div
        className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
        style={useFallback
          ? { background: bgColour + "33", border: `1px solid ${bgColour}55` }
          : { background: "var(--card2)" }
        }
      >
        {useFallback
          ? <span className="text-[11px] font-syne font-bold" style={{ color: bgColour }}>{initials}</span>
          : <span className="text-lg">{catIcon}</span>
        }
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

      {/* Amount + % of spending + context badge */}
      <div className="flex flex-col items-end gap-0.5 flex-shrink-0">
        <span className="font-syne font-bold text-red-400 text-sm">
          {fmtInr(item.amount)}
        </span>
        {pctOfVar !== null && (
          <span className="text-[10px]" style={{ color: "var(--text-sub)" }}>
            {pctOfVar}% of spending
          </span>
        )}
        {badge && (
          <span className="text-[10px] font-medium" style={{ color: badge.colour }}>
            {badge.label}
          </span>
        )}
      </div>
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

const COMPARATIVE_TERMS = ["% from", "last month", "compared to", "jumped", "increased by", "decreased by"];
function isSafeInsight(text: string, isFirstMonth: boolean): boolean {
  if (!isFirstMonth) return true;
  return !COMPARATIVE_TERMS.some(term => text.toLowerCase().includes(term));
}

// ── Main component ─────────────────────────────────────────────────────────────

export function OverviewTab({ onTabChange }: { onTabChange?: (path: string) => void }) {
  const { selMonth } = useMonth();
  const { toast } = useToast();

  const [summary,      setSummary]      = useState<Summary | null>(null);
  const [projections,  setProjections]  = useState<ProjectionItem[]>([]);
  const [topSpends,    setTopSpends]    = useState<TopSpend[]>([]);
  const [mom,          setMom]          = useState<MoMData | null>(null);
  const [dueReminders, setDueReminders] = useState<DueReminder[]>([]);
  const [story,        setStory]        = useState<string | null>(null);
  const [tinyWin,      setTinyWin]      = useState<string | null>(null);
  const [prevSummary,  setPrevSummary]  = useState<Summary | null>(null);
  const [pom,          setPom]          = useState<PeaceOfMind | null>(null);
  const [monthlyInsight, setMonthlyInsight] = useState<string | null>(null);
  const [loading,           setLoading]          = useState(true);
  const [donutFilter,       setDonutFilter]       = useState<"variable" | "fixed" | "all">("variable");
  const [showPomBreakdown,  setShowPomBreakdown]  = useState(false);
  const [showSignalsModal,  setShowSignalsModal]  = useState(false);
  const [activeKpiIndex,    setActiveKpiIndex]    = useState(0);
  const carouselRef       = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    setLoading(true);
    const [year, month] = selMonth.split("-").map(Number);
    const prevDate = new Date(year, month - 2, 1); // month-2 because JS months are 0-indexed
    const prevMonthKey = `${prevDate.getFullYear()}-${String(prevDate.getMonth() + 1).padStart(2, "0")}`;
    try {
      const [sum, proj, top, momData, reminders, storyResult, tinyWinResult, prevSum, pomResult, insightResult] = await Promise.all([
        api.get<Summary>(`/summary/${selMonth}`).then(r => r.data),
        api.get<ProjectionItem[]>(`/insights/projection/${selMonth}`).then(r => r.data),
        api.get<TopSpend[]>(`/insights/top-spends/${selMonth}?limit=5`).then(r => r.data),
        api.get<MoMData>(`/insights/mom/${selMonth}`).then(r => r.data),
        // Correct path is /fixed/due-reminders/ (not /insights/due-reminders/)
        api.get<DueReminder[]>(`/fixed/due-reminders/${selMonth}`).then(r => r.data).catch((): DueReminder[] => []),
        api.get<MonthlyStory>(`/insights/story/${selMonth}`).then(r => r.data.story).catch(() => null),
        api.get<TinyWin>(`/insights/tiny-win/${selMonth}`).then(r => r.data.win).catch(() => null),
        api.get<Summary>(`/summary/${prevMonthKey}`).then(r => r.data).catch(() => null),
        api.get<PeaceOfMind>(`/insights/peace-of-mind/${selMonth}`).then(r => r.data).catch(() => null),
        api.get<{ insight: string | null }>(`/insights/monthly-insight/${selMonth}`).then(r => r.data.insight).catch(() => null),
      ]);
      setSummary(sum);
      setProjections(proj);
      setTopSpends(top);
      setMom(momData);
      setDueReminders(reminders);
      setStory(storyResult);
      setTinyWin(tinyWinResult);
      setPrevSummary(prevSum);
      setPom(pomResult);
      setMonthlyInsight(insightResult);
    } catch {
      // leave state as null — empty state renders
    } finally {
      setLoading(false);
    }
  }, [selMonth]);

  useEffect(() => { load(); }, [load]);

  const navigateTo = useCallback((index: number) => {
    setActiveKpiIndex(Math.max(0, Math.min(2, index)));
  }, []);

  const handleScroll = useCallback(() => {
    const el = carouselRef.current;
    if (!el) return;
    const slideWidth = el.querySelector('.kpi-slide')?.clientWidth ?? el.clientWidth;
    const index = Math.round(el.scrollLeft / slideWidth);
    setActiveKpiIndex(Math.max(0, Math.min(2, index)));
  }, []);

  const scrollToCard = useCallback((index: number) => {
    const el = carouselRef.current;
    if (!el) return;
    const slide = el.children[index] as HTMLElement | undefined;
    if (slide) {
      el.scrollTo({ left: slide.offsetLeft, behavior: 'smooth' });
    }
  }, []);


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
  const isFirstMonth = prevSummary === null;

  const isConsecutiveMonth = (current: string, prior: string): boolean => {
    const [cy, cm] = current.split("-").map(Number);
    const [py, pm] = prior.split("-").map(Number);
    const expectedPriorMonth = cm === 1 ? 12 : cm - 1;
    const expectedPriorYear  = cm === 1 ? cy - 1 : cy;
    return py === expectedPriorYear && pm === expectedPriorMonth;
  };

  const kpiCards = [
    {
      id: "remaining",
      label: "Remaining",
      icon: "💰",
      value: fmtInr(balance.remaining),
      subtitle: "Left for the month",
      pending: null as string | null,
    },
    {
      id: "income",
      label: "Income",
      icon: "💼",
      value: fmtInr(balance.total_income),
      subtitle: "Total this month",
      pending: null as string | null,
    },
    {
      id: "bills",
      label: "Bills Paid",
      icon: "✅",
      value: fmtInr(balance.fixed_paid_total),
      subtitle: `Out of ${fmtInr(balance.fixed_paid_total + balance.fixed_unpaid_total)}`,
      pending: balance.fixed_unpaid_total > 0
        ? `${fmtInr(balance.fixed_unpaid_total)} still pending`
        : null,
    },
  ];

  return (
    <div className="space-y-6">

      {/* ── Section 0: KPI Carousel ─────────────────────────── */}
      <section>
        <div className="kpi-carousel-wrapper">

          {/* Mobile: native scroll-snap carousel */}
          <div
            ref={carouselRef}
            className="kpi-scroller md:hidden"
            onScroll={handleScroll}
          >
            {kpiCards.map((card) => (
              <div key={card.id} className={`kpi-slide kpi-card-${card.id}`}>
                <div className="kpi-accent" />
                <span className="kpi-watermark">WM</span>
                <div className="kpi-slide-header">
                  <span className="kpi-slide-icon">{card.icon}</span>
                  <span className="kpi-card-label">{card.label}</span>
                </div>
                <p className="kpi-card-value">{card.value}</p>
                <p className="kpi-card-sub">{card.subtitle}</p>
                {card.pending && <p className="kpi-card-pending">{card.pending}</p>}
              </div>
            ))}
          </div>

          {/* Dot indicators — mobile only */}
          <div className="kpi-dots md:hidden">
            {kpiCards.map((card, i) => (
              <button
                key={card.id}
                className={`kpi-dot ${i === activeKpiIndex ? "active" : ""}`}
                onClick={() => scrollToCard(i)}
                aria-label={`View ${card.label}`}
              />
            ))}
          </div>

          {/* Desktop: all 3 cards side by side */}
          <div className="kpi-desktop-row hidden md:flex">
            {kpiCards.map((card, i) => (
              <div
                key={card.id}
                className={`kpi-card-shell kpi-card-${card.id} ${i === activeKpiIndex ? "active" : "side"}`}
                style={{ padding: "14px 20px" }}
                onClick={() => navigateTo(i)}
              >
                <div className="kpi-accent" />
                <span className="kpi-watermark" style={{ fontSize: 18, top: 10, right: 14 }}>WM</span>
                <div className="kpi-slide-header" style={{ marginBottom: 10 }}>
                  <span className="kpi-slide-icon" style={{ fontSize: 14 }}>{card.icon}</span>
                  <span className="kpi-card-label" style={{ fontSize: 10 }}>{card.label}</span>
                </div>
                <p className="kpi-card-value" style={{ fontSize: 24 }}>{card.value}</p>
                <p className="kpi-card-sub" style={{ fontSize: 10, marginTop: 3 }}>{card.subtitle}</p>
                {card.pending && (
                  <p className="kpi-card-pending" style={{ fontSize: 10, marginTop: 2 }}>{card.pending}</p>
                )}
              </div>
            ))}
          </div>

        </div>
      </section>

      {/* ── Section 0b: This Month's Story ───────────────── */}
      {story && (
        <section>
          <div
            className="rounded-2xl border p-5 flex items-start gap-4 overflow-hidden"
            style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
          >
            {/* Dynamic month badge */}
            <div
              className="flex-shrink-0 flex flex-col items-center justify-center rounded-xl border px-3 py-2 text-center"
              style={{ background: "var(--card2)", borderColor: "var(--border-lg)", minWidth: 52 }}
            >
              <p
                className="text-[10px] font-syne font-bold uppercase tracking-widest"
                style={{ color: "var(--accent)" }}
              >
                {new Date(selMonth + "-01").toLocaleString("en-IN", { month: "short" })}
              </p>
              <p className="text-sm font-bold leading-tight" style={{ color: "var(--text)" }}>
                {selMonth.split("-")[0]}
              </p>
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5 mb-2">
                <span style={{ color: "#f59e0b" }}>✦</span>
                <p
                  className="text-[10px] font-syne font-bold tracking-widest"
                  style={{ color: "var(--text-sub)", lineHeight: 1.6, paddingBottom: 4 }}
                >
                  {new Date(selMonth + "-01").toLocaleString("en-IN", { month: "long" })} in one sentence
                </p>
              </div>
              <p className="text-sm leading-relaxed" style={{ color: "var(--text)" }}>
                {story}
              </p>
            </div>
          </div>
        </section>
      )}

      {/* ── Sections 3+4: Monthly Breakdown + Spend by Category (side-by-side) ── */}
      <div className="grid grid-cols-1 pair:grid-cols-2 gap-4">

        {/* ── Section 1: Monthly breakdown bar + Insight ───── */}
        <section className="h-full flex flex-col gap-3">
          <BalanceBreakdown balance={balance} />

          {monthlyInsight && isSafeInsight(monthlyInsight, isFirstMonth) && (
            <div
              className="flex-1 rounded-2xl border p-4"
              style={{ borderColor: "var(--border)", background: "var(--card)" }}
            >
              <p className="text-[11px] font-semibold tracking-wide mb-2" style={{ color: "var(--accent)" }}>
                ✨ Insight
              </p>
              <p className="text-[13px] leading-relaxed" style={{ color: "var(--text)" }}>
                {monthlyInsight}
              </p>
            </div>
          )}
        </section>

        {/* ── Section 2: Spend donut + Category Winner ──────── */}
        {summary.categories.length > 0 && (
          <section className="h-full">
            <div
              className="rounded-2xl border p-4 h-full"
              style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
            >
              {/* Header + filter tabs */}
              <div className="flex items-center justify-between mb-3">
                <h2 className="section-heading">
                  Spend by category
                </h2>
                <div className="relative">
                  <select
                    value={donutFilter}
                    onChange={e => setDonutFilter(e.target.value as "variable" | "fixed" | "all")}
                    className="appearance-none text-xs pl-2.5 pr-6 py-1 rounded-lg border cursor-pointer"
                    style={{
                      background:  "var(--card2)",
                      borderColor: "var(--border-lg)",
                      color:       "var(--text)",
                    }}
                  >
                    {DONUT_FILTERS.map(f => (
                      <option key={f.value} value={f.value}>{f.label}</option>
                    ))}
                  </select>
                  <ChevronDown
                    size={11}
                    className="absolute right-1.5 top-1/2 -translate-y-1/2 pointer-events-none"
                    style={{ color: "var(--text-sub)" }}
                  />
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
                const eligibleCats = varCats.filter(c => c.category !== 'Miscellaneous');
                const top = eligibleCats.length > 0
                  ? [...eligibleCats].sort((a, b) => b.spent - a.spent)[0]
                  : null;

                if (!top) {
                  return (
                    <div
                      className="mt-3 pt-3 border-t"
                      style={{ borderColor: "var(--border)" }}
                    >
                      <p className="section-heading mb-2">
                        Category winner
                      </p>
                      <div className="flex items-center gap-3">
                        <span className="text-2xl flex-shrink-0">🏅</span>
                        <div>
                          <p className="text-sm font-syne font-bold" style={{ color: "var(--text)" }}>
                            No clear winner this month
                          </p>
                          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                            Most spending was uncategorized. Try reviewing your transaction categories.
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                }

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
                    className="mt-3 pt-3 border-t"
                    style={{ borderColor: "var(--border)" }}
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

      {/* ── Sections 5+6: Peace of Mind + Spending Signals (side-by-side) ── */}
      <div className="grid grid-cols-1 pair:grid-cols-2 gap-4">

        {/* ── Section 5: Peace of Mind Score ───────────────── */}
        {pom && (() => {
          const radius     = 33;
          const circ       = 2 * Math.PI * radius;
          const filled     = (pom.score / 100) * circ;
          const dialColour = pom.score >= 70 ? "#34d399" : pom.score >= 40 ? "#f59e0b" : "#f87171";
          const posFactors = (pom.factors ?? []).filter(f => f.points >= 0);
          const negFactors = (pom.factors ?? []).filter(f => f.points < 0);

          return (
            <section className="h-full">
              <div
                className="rounded-2xl border p-4 h-full"
                style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
              >
                <p className="text-[10px] font-syne font-bold tracking-widest mb-3"
                   style={{ color: "var(--text-sub)" }}>
                  🧘 Peace of mind
                </p>

                {/* Dial + right column */}
                <div className="flex items-start gap-4">
                  {/* SVG dial with score centred */}
                  <div className="relative flex-shrink-0" style={{ width: 88, height: 88 }}>
                    <svg width="88" height="88" viewBox="0 0 88 88">
                      <circle cx="44" cy="44" r={radius} fill="none"
                        stroke="var(--border-lg)" strokeWidth="9" />
                      <circle cx="44" cy="44" r={radius} fill="none"
                        stroke={dialColour} strokeWidth="9"
                        strokeDasharray={`${filled} ${circ}`}
                        strokeDashoffset={circ * 0.25}
                        strokeLinecap="round"
                        transform="rotate(-90 44 44)" />
                    </svg>
                    <div style={{ position: "absolute", inset: 0, display: "flex",
                                  flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
                      <span className="font-syne font-extrabold text-xl leading-none"
                            style={{ color: dialColour }}>
                        {pom.score}
                      </span>
                      <span className="text-[9px]" style={{ color: "var(--text-sub)" }}>/100</span>
                    </div>
                  </div>

                  {/* Summary + delta + factors */}
                  <div className="flex-1 min-w-0">
                    {pom.summary && (
                      <p className="text-xs leading-relaxed mb-2" style={{ color: "var(--text-sub)" }}>
                        {pom.summary}
                      </p>
                    )}
                    {pom.delta != null && (
                      <p className="text-[11px] font-medium mb-2"
                         style={{ color: pom.delta >= 0 ? "#34d399" : "#f87171" }}>
                        {pom.delta >= 0
                          ? `↑ ${pom.delta} pts vs yesterday`
                          : `↓ ${Math.abs(pom.delta)} pts vs yesterday`}
                      </p>
                    )}
                    <div className="space-y-1">
                      {[...posFactors, ...negFactors].map((f, i) => (
                        <div key={i} className="flex items-center justify-between text-[11px]">
                          <span style={{ color: "var(--text-sub)" }}>{f.label}</span>
                          <span className="font-semibold font-syne"
                                style={{ color: f.points >= 0 ? "#34d399" : "#f87171" }}>
                            {f.points >= 0 ? `+${f.points}` : f.points}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Why this score? expand */}
                <div className="mt-3 border-t pt-3" style={{ borderColor: "var(--border-lg)" }}>
                  <button
                    onClick={() => setShowPomBreakdown(v => !v)}
                    className="text-xs font-syne font-semibold transition-opacity hover:opacity-70"
                    style={{ color: "var(--accent)" }}
                  >
                    {showPomBreakdown ? "↑ Hide" : "Why this score? ↓"}
                  </button>
                  {showPomBreakdown && (
                    <p className="text-xs mt-2 leading-relaxed" style={{ color: "var(--text-sub)" }}>
                      Score = 50 base + bills completion (up to +25) + positive balance (+15) + tracking (+10), minus overspend and pending bill deductions.
                    </p>
                  )}
                </div>
              </div>
            </section>
          );
        })()}

        {/* ── Section 6: Spending Signals ─────────────────── */}
        {projections.length > 0 && (() => {
          const withRatio = projections
            .filter(p => p.limit > 0)
            .map(p => ({ ...p, ratio: p.spent / p.limit }));
          const sorted = [...withRatio].sort((a, b) => b.ratio - a.ratio);
          const top = sorted[0];
          const mid = sorted[1];
          const low = [...withRatio]
            .filter(p => p.spent > 0)
            .sort((a, b) => a.ratio - b.ratio)[0];
          const budgetSignals = [top, mid, low].filter(Boolean);

          return (
            <section className="h-full">
              <div className="flex items-center justify-between mb-4">
                <h2 className="section-heading">
                  📡 Spending signals
                </h2>
                <button
                  className="text-xs"
                  style={{ color: "var(--text-sub)" }}
                  onClick={() => setShowSignalsModal(true)}
                >
                  View all →
                </button>
              </div>
              <div className="space-y-3">
                {budgetSignals.map(p => (
                  <SignalCard key={p.category} p={p} />
                ))}
              </div>
            </section>
          );
        })()}

      </div>

      {/* ── Section 7: Coming Up (due bills + month-end balance) ─── */}
      <section>
        <h2 className="section-heading mb-4">
          🔔 Coming up
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
                const sorted = [...dueReminders].sort((a, b) => a.days_overdue - b.days_overdue);
                const next = sorted.find(r => r.days_overdue <= 0) ?? sorted[sorted.length - 1];
                return (
                  <div className="flex items-center gap-3">
                    <span className="text-xl">📅</span>
                    <div className="flex-1">
                      <p className="text-sm font-medium" style={{ color: "var(--text)" }}>
                        {next.vendor}
                      </p>
                      <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                        {next.days_overdue < 0
                          ? `Due in ${Math.abs(next.days_overdue)} day(s)`
                          : next.days_overdue === 0
                          ? "Due today"
                          : `${next.days_overdue} day(s) overdue`}
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

      {/* ── Section 8: Money Moments ─────────────────────── */}
      {topSpends.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-heading">
              💎 Money moments
            </h2>
            <button
              className="text-xs"
              style={{ color: "var(--accent)" }}
              onClick={() => onTabChange ? onTabChange("/history") : toast("See all transactions in the History tab →")}
            >
              View all →
            </button>
          </div>

          {balance.variable_total > 0 && (
            <p className="text-[11px] mb-3" style={{ color: "var(--text-sub)" }}>
              Largest {topSpends.length} purchases contributed{" "}
              <span style={{ color: "var(--text)", fontWeight: 600 }}>
                {Math.round(topSpends.reduce((s, t) => s + t.amount, 0) / balance.variable_total * 100)}%
              </span>{" "}
              of this month's spending.
            </p>
          )}

          <div className="space-y-0">
            {topSpends.map((t, i) => (
              <TopSpendRow key={i} rank={i + 1} item={t} varTotal={balance.variable_total} />
            ))}
          </div>
        </section>
      )}

      {/* ── Section 9: Tracking summary / What Changed? ─── */}
      {mom && (() => {
        const curr = mom.months[mom.months.length - 1];
        const prev = mom.months.length >= 2 ? mom.months[mom.months.length - 2] : null;
        const isFirstMonth    = !prev;
        const isConsecutive   = prev ? isConsecutiveMonth(curr, prev) : false;
        const currDaysTracked = mom.days_tracked?.[curr] ?? 0;
        const prevDaysTracked = prev ? (mom.days_tracked?.[prev] ?? 0) : 0;
        const isQualityData   = prevDaysTracked >= 10;

        const scenario =
          isFirstMonth                   ? "A" :
          isConsecutive && isQualityData ? "B" :
          isConsecutive                  ? "D" :
          "C";

        return (
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="section-heading">
                {scenario === "A" ? "🌱 Getting started"     :
                 scenario === "B" ? "📊 What changed?"       :
                 scenario === "C" ? "📅 Spending highlights"  :
                                    "📋 Tracking summary"}
              </h2>
              {scenario === "B" && prev && (
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                  vs {new Date(prev + "-01").toLocaleString("en-IN", { month: "short" })}
                </span>
              )}
            </div>

            {scenario === "A" && <InsightsScenarioA summary={summary} />}
            {scenario === "B" && prev && (
              <InsightsScenarioB
                mom={mom}
                summary={summary}
                curr={curr}
                prev={prev}
                onViewAll={() => toast("See all transactions in the History tab →")}
              />
            )}
            {scenario === "C" && prev && <InsightsScenarioC summary={summary} prev={prev} />}
            {scenario === "D" && (
              <InsightsScenarioD currDays={currDaysTracked} prevDays={prevDaysTracked} />
            )}
          </section>
        );
      })()}

      {/* ── Section 10: Financial Pulse ──────────────────── */}
      {mom && (() => {
        const [year, month] = selMonth.split("-").map(Number);
        const today = new Date();
        const isCurrentMonth =
          today.getFullYear() === year && (today.getMonth() + 1) === month;
        const daysInMonth = new Date(year, month, 0).getDate();
        const daysElapsed = isCurrentMonth ? Math.max(today.getDate(), 1) : daysInMonth;

        const fixedTotal  = balance.fixed_paid_total + balance.fixed_unpaid_total;
        const unpaidFrac  = fixedTotal > 0 ? balance.fixed_unpaid_total / fixedTotal : 0;
        const stabilityColour =
          balance.fixed_unpaid_total === 0 ? "#34d399" :
          unpaidFrac < 0.30               ? "#f59e0b" : "#f87171";
        const stabilityDesc =
          balance.fixed_unpaid_total === 0 ? "All fixed obligations complete."       :
          unpaidFrac < 0.30               ? "Fixed obligations are nearly complete." : "Fixed obligations pending.";

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

        const savingsPct = balance.total_income > 0
          ? ((balance.savings_total ?? 0) / balance.total_income) * 100
          : -1;
        const savingsColour =
          savingsPct < 0   ? "#94a3b8" :
          savingsPct >= 20 ? "#34d399" :
          savingsPct >= 10 ? "#f59e0b" : "#f87171";

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
          { icon: "🛡️", name: "Stability",   desc: stabilityDesc,   colour: stabilityColour },
          { icon: "🔥", name: "Lifestyle",   desc: lifestyleDesc,   colour: lifestyleColour },
          { icon: "🐷", name: "Savings",     desc: savingsDesc,     colour: savingsColour   },
          { icon: "🎯", name: "Consistency", desc: consistencyDesc, colour: "#34d399"       },
        ];

        return (
          <section>
            <div
              className="rounded-2xl border overflow-hidden"
              style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
            >
              <div
                className="px-4 py-3 flex items-center gap-2 border-b"
                style={{ borderColor: "var(--border-lg)" }}
              >
                <Activity size={13} strokeWidth={2.5} style={{ color: "#34d399" }} />
                <p
                  className="text-[10px] font-syne font-bold tracking-widest"
                  style={{ color: "var(--text-sub)", lineHeight: 1.6 }}
                >
                  💓 Financial pulse
                </p>
              </div>
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
                      style={{ borderColor: "var(--border-lg)", minHeight: 120 }}
                    >
                      <span className="text-xl">{s.icon}</span>
                      <p className="text-sm font-syne font-semibold mt-2" style={{ color: s.colour }}>
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

      {/* ── Section 11: Tiny Win ─────────────────────────── */}
      {tinyWin && (
        <section>
          <div
            className="rounded-2xl p-4 border flex items-center gap-4"
            style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
          >
            <span className="text-2xl flex-shrink-0">🌱</span>
            <div>
              <p
                className="text-[10px] font-syne font-bold tracking-widest mb-1"
                style={{ color: "#f59e0b" }}
              >
                🎉 Tiny win
              </p>
              <p className="text-sm leading-relaxed" style={{ color: "var(--text)" }}>
                {tinyWin}
              </p>
            </div>
          </div>
        </section>
      )}

      <SpendingSignalsModal
        open={showSignalsModal}
        onClose={() => setShowSignalsModal(false)}
        projections={projections}
      />

    </div>
  );
}
