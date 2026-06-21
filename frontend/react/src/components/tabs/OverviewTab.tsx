import { useEffect, useState, useCallback } from "react";
import { api } from "@/api/client";
import { useMonth } from "@/context/MonthContext";
import { fmtInr } from "@/utils/formatInr";
import { fmtDate } from "@/utils/formatDate";
import { CATEGORY_ICONS, FIXED_CATEGORIES } from "@/utils/categories";
import { BalanceBreakdown } from "@/components/shared/BalanceBreakdown";
import { SpendDonut } from "@/components/shared/SpendDonut";
import { BudgetHealthCard } from "@/components/shared/BudgetHealthCard";
import { MoMTable } from "@/components/shared/MoMTable";
import type { Summary, ProjectionItem } from "@/types";

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

  const [summary,     setSummary]     = useState<Summary | null>(null);
  const [projections, setProjections] = useState<ProjectionItem[]>([]);
  const [topSpends,   setTopSpends]   = useState<TopSpend[]>([]);
  const [mom,         setMom]         = useState<MoMData | null>(null);
  const [loading,     setLoading]     = useState(true);
  const [donutFilter, setDonutFilter] = useState<"variable" | "fixed" | "all">("variable");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [sum, proj, top, momData] = await Promise.all([
        api.get<Summary>(`/summary/${selMonth}`).then(r => r.data),
        api.get<ProjectionItem[]>(`/insights/projection/${selMonth}`).then(r => r.data),
        api.get<TopSpend[]>(`/insights/top-spends/${selMonth}?limit=5`).then(r => r.data),
        api.get<MoMData>(`/insights/mom/${selMonth}`).then(r => r.data),
      ]);
      setSummary(sum);
      setProjections(proj);
      setTopSpends(top);
      setMom(momData);
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

      {/* ── Section 1: Monthly breakdown bar ───────────── */}
      <section>
        <BalanceBreakdown balance={balance} />
      </section>

      {/* ── Section 2: Spend donut (bonus — not in Streamlit) */}
      {summary.categories.length > 0 && (
        <section>
          <div className="mb-3 space-y-2">
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
                  className="text-xs px-3 py-1 rounded-lg border transition-colors"
                  style={{
                    background:   donutFilter === f.value ? "var(--accent-bg)"  : "transparent",
                    borderColor:  donutFilter === f.value ? "var(--accent)"     : "var(--border-lg)",
                    color:        donutFilter === f.value ? "var(--accent)"     : "var(--text)",
                    fontWeight:   donutFilter === f.value ? 600 : 400,
                  }}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>
          <SpendDonut
            categories={summary.categories.filter(c =>
              donutFilter === "all"
                ? true
                : donutFilter === "fixed"
                  ? FIXED_CATEGORIES.includes(c.category)
                  : !FIXED_CATEGORIES.includes(c.category)
            )}
          />
        </section>
      )}

      {/* ── Section 3: Budget health ─────────────────────── */}
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

      {/* ── Section 4: Top spends ────────────────────────── */}
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

      {/* ── Section 5: Month-over-Month table ───────────── */}
      {mom && mom.months.length > 0 && (
        <section>
          <h2
            className="text-xs font-syne font-bold uppercase tracking-widest mb-3"
            style={{ color: "var(--text-sub)" }}
          >
            Month-over-Month
          </h2>
          <MoMTable mom={mom} />
        </section>
      )}

    </div>
  );
}
