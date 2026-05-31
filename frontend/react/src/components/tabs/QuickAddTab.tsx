import { useState, useRef, useEffect, useCallback } from "react";
import { api } from "@/api/client";
import { useMonth } from "@/context/MonthContext";
import { CATEGORY_ICONS } from "@/utils/categories";
import { fmtInr } from "@/utils/formatInr";
import { ExpenseRowSwipeable } from "@/components/shared/ExpenseRowSwipeable";
import type { Expense, ExpenseTemplate } from "@/types";
import { Loader2, Zap } from "lucide-react";
import { useToast } from "@/context/ToastContext";

/**
 * QuickAddTab — primary data entry tab
 *
 * Streamlit ref: with tab1: in frontend/app.py
 *
 * Three sections:
 *   1. NL text input + date → POST /expenses/parse → animated expense cards
 *   2. Favourites chips — horizontal scroll row, tap to log instantly
 *   3. Today's entries — last 10 non-fixed expenses for today, swipe-to-delete
 *
 * Key improvements over Streamlit:
 *   - Input auto-focuses when tab mounts (Streamlit can't auto-focus)
 *   - Animated expense cards after parse (no full page rerun)
 *   - Swipe-to-delete on mobile via clean touch events
 *   - Horizontal scroll chips vs Streamlit's fixed 3-column grid
 */

interface ParseResult {
  saved: Expense[];
  warnings: Array<{ level: string; message: string }>;
  balance: { remaining: number };
}

export function QuickAddTab() {
  const { selMonth } = useMonth();
  const today = new Date().toISOString().slice(0, 10);

  // ── NL parse form state ─────────────────────────────────────────────────
  const [text, setText]         = useState("");
  const [date, setDate]         = useState(today);
  const [parsing, setParsing]   = useState(false);
  const [lastResult, setLastResult] = useState<ParseResult | null>(null);

  // ── Favourites state ────────────────────────────────────────────────────
  const [favourites, setFavourites]   = useState<ExpenseTemplate[]>([]);
  const [loadingFav, setLoadingFav]   = useState<number | null>(null);

  // ── Today's entries state ───────────────────────────────────────────────
  const [todayExpenses, setTodayExpenses] = useState<Expense[]>([]);

  const inputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  // Auto-focus the text input when the tab mounts
  // Streamlit can't do this — requires a page refresh workaround
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Fetch today's entries — called after parse and after fav log
  const refreshToday = useCallback(() => {
    api.get<Expense[]>(`/expenses/${selMonth}`)
      .then(r => {
        setTodayExpenses(
          r.data
            .filter(e => e.date === today && !e.is_fixed)
            .slice(0, 10)
        );
      })
      .catch(() => {}); // silently fail — list just won't update
  }, [selMonth, today]);

  // Load favourites and today's entries on mount and when month changes
  useEffect(() => {
    api.get<ExpenseTemplate[]>("/expense-templates")
      .then(r => setFavourites(r.data))
      .catch(() => {});
    refreshToday();
  }, [selMonth, refreshToday]);

  // ── Handlers ────────────────────────────────────────────────────────────

  const handleParse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    setParsing(true);
    setLastResult(null);
    try {
      const { data } = await api.post<ParseResult>("/expenses/parse", {
        text: text.trim(),
        date_override: date,
      });
      setLastResult(data);
      setText("");          // clear input after successful parse
      refreshToday();       // update today's entries list
      if (data.saved.length > 0) {
        toast(
          `${data.saved.length} expense${data.saved.length > 1 ? "s" : ""} saved`,
          { icon: "⚡" }
        );
      }
    } catch {
      toast("Failed to parse expenses. Try again.", { type: "error" });
    } finally {
      setParsing(false);
    }
  };

  const handleFavLog = async (id: number) => {
    setLoadingFav(id);
    try {
      await api.post(`/expense-templates/${id}/log`);
      refreshToday();
      toast("Logged!", { icon: "⚡" });
    } catch {
      toast("Failed to log shortcut.", { type: "error" });
    } finally {
      setLoadingFav(null);
    }
  };

  const handleDelete = async (id: number) => {
    // Optimistic remove from list
    setTodayExpenses(prev => prev.filter(e => e.id !== id));
    try {
      await api.delete(`/expenses/${id}`);
    } catch {
      refreshToday(); // restore if delete failed
    }
  };

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">

      {/* ── Section 1: NL Input Form ───────────────────── */}
      <section>
        <h2 className="text-xs font-syne font-bold uppercase tracking-widest mb-3"
            style={{ color: 'var(--text-sub)' }}>
          Log Expenses
        </h2>
        <p className="text-xs mb-3" style={{ color: 'var(--text-sub)' }}>
          Type like:{" "}
          <code className="bg-dark-card2 px-2 py-0.5 rounded text-indigo-400 text-xs">
            zomato 500, ola 200, bigbasket 1200
          </code>
        </p>

        <form onSubmit={handleParse} className="space-y-3">
          <input
            ref={inputRef}
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder="e.g. zomato 500, ola 200, bigbasket 1200"
            className="w-full bg-dark-card2 border border-white/10 rounded-xl px-4 py-3
                       text-white placeholder-white/30 focus:border-accent focus:outline-none
                       focus:ring-1 focus:ring-accent transition-colors"
          />
          <div className="flex gap-3">
            <input
              type="date"
              value={date}
              onChange={e => setDate(e.target.value)}
              className="bg-dark-card2 border border-white/10 rounded-xl px-3 py-2
                         text-white text-sm focus:border-accent focus:outline-none"
            />
            <button
              type="submit"
              disabled={parsing || !text.trim()}
              className="flex-1 flex items-center justify-center gap-2
                         bg-gradient-to-r from-accent to-accent2 text-white
                         font-syne font-semibold py-2.5 rounded-xl
                         disabled:opacity-50 transition-opacity"
            >
              {parsing
                ? <Loader2 size={16} className="animate-spin" />
                : <Zap size={16} />
              }
              {parsing ? "Parsing…" : "Add Expenses"}
            </button>
          </div>
        </form>

        {/* Parse result — expense cards + balance update */}
        {lastResult && (
          <div className="mt-4 space-y-3">

            {/* Warnings */}
            {lastResult.warnings.map((w, i) => (
              <div
                key={i}
                className={`p-3 rounded-xl text-sm border-l-4 ${
                  w.level === "danger"
                    ? "bg-red-500/10 border-red-500 text-red-300"
                    : "bg-amber-500/10 border-amber-500 text-amber-300"
                }`}
              >
                {w.message}
              </div>
            ))}

            {/* Saved expense cards — animated fade in */}
            {lastResult.saved.length > 0 && (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {lastResult.saved.map(item => (
                  <div
                    key={item.id}
                    className="bg-dark-card border border-white/10 rounded-2xl p-4
                               text-center animate-fade-in"
                  >
                    <div className="text-2xl mb-1">
                      {CATEGORY_ICONS[item.category] ?? "📦"}
                    </div>
                    <div className="text-white font-medium text-sm truncate">
                      {item.vendor}
                    </div>
                    <div className="font-syne font-bold text-red-400 text-lg">
                      {fmtInr(item.amount)}
                    </div>
                    <div className="text-xs" style={{ color: 'var(--text-sub)' }}>
                      {item.category}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Updated balance */}
            {lastResult.balance && (
              <div className="bg-dark-card border border-white/10 rounded-2xl p-4 text-center">
                <p className="text-xs mb-1" style={{ color: 'var(--text-sub)' }}>
                  Updated Remaining Balance
                </p>
                <p className={`font-syne font-bold text-2xl ${
                  lastResult.balance.remaining >= 0
                    ? "text-emerald-400"
                    : "text-red-400"
                }`}>
                  {fmtInr(lastResult.balance.remaining)}
                </p>
              </div>
            )}
          </div>
        )}
      </section>

      {/* ── Section 2: Favourites ───────────────────────── */}
      {favourites.length > 0 && (
        <section>
          <h2 className="text-xs font-syne font-bold uppercase tracking-widest mb-2"
              style={{ color: 'var(--text-sub)' }}>
            Quick Add Favourites
          </h2>
          <p className="text-xs mb-3" style={{ color: 'var(--text-sub)' }}>
            Tap to log instantly
          </p>

          {/* Horizontal scroll row — better than Streamlit's fixed 3-col grid on narrow screens */}
          <div className="flex gap-2 overflow-x-auto pb-2 -mx-4 px-4 scrollbar-hide">
            {favourites.map(tmpl => (
              <button
                key={tmpl.id}
                onClick={() => handleFavLog(tmpl.id)}
                disabled={loadingFav === tmpl.id}
                className="flex-shrink-0 flex flex-col items-center gap-1
                           bg-dark-card2 border border-white/10 rounded-2xl
                           px-4 py-3 min-w-[80px]
                           disabled:opacity-50 hover:border-accent/50 transition-colors"
              >
                <span className="text-xl">
                  {CATEGORY_ICONS[tmpl.category] ?? "📦"}
                </span>
                <span className="text-white text-xs font-medium leading-tight text-center">
                  {tmpl.name}
                </span>
                <span className="font-syne font-semibold text-xs text-red-400">
                  {fmtInr(tmpl.amount)}
                </span>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* ── Section 3: Today's Entries ──────────────────── */}
      <section>
        <h2 className="text-xs font-syne font-bold uppercase tracking-widest mb-3"
            style={{ color: 'var(--text-sub)' }}>
          Today's Entries
        </h2>

        {todayExpenses.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Nothing logged today.
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
              Type something like:{" "}
              <span className="text-indigo-400">zomato 350, ola 120</span>
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            {todayExpenses.map(e => (
              <ExpenseRowSwipeable
                key={e.id}
                expense={e}
                onDelete={() => handleDelete(e.id)}
              />
            ))}
          </div>
        )}
      </section>

    </div>
  );
}
