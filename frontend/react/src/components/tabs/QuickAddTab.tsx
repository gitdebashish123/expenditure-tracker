import { useState, useRef, useEffect, useCallback } from "react";
import { api } from "@/api/client";
import { useMonth } from "@/context/MonthContext";
import { CATEGORY_ICONS } from "@/utils/categories";
import { fmtInr } from "@/utils/formatInr";
import { ExpenseRowSwipeable } from "@/components/shared/ExpenseRowSwipeable";
import type { Expense, ExpenseTemplate, DailyMantra } from "@/types";
import { Loader2, Zap, MessageCircle } from "lucide-react";
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

interface Props {
  onExpenseAdded?: () => void;
}

// ── Manual entry fallback — shown when /expenses/parse fails for any reason ──

interface ManualEntryFallbackProps {
  date:      string;
  onSaved:   (exp: Expense) => void;
  onDismiss: () => void;
}

function ManualEntryFallback({ date, onSaved, onDismiss }: ManualEntryFallbackProps) {
  const [vendor,   setVendor]   = useState("");
  const [amount,   setAmount]   = useState("");
  const [category, setCategory] = useState("Food");
  const [note,     setNote]     = useState("");
  const [saving,   setSaving]   = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const amt = parseFloat(amount);
    if (!vendor.trim() || !amt || amt <= 0) return;
    setSaving(true);
    try {
      const { data } = await api.post<{ expense: Expense }>("/expenses/manual", {
        vendor:       vendor.trim(),
        amount:       amt,
        category,
        note:         note.trim() || undefined,
        expense_date: date,
      });
      onSaved(data.expense);
    } catch {
      // leave form open so user can retry
    } finally {
      setSaving(false);
    }
  };

  const inputCls =
    "w-full bg-dark-card2 border border-white/10 rounded-xl px-3 py-2 " +
    "text-white text-sm focus:border-accent focus:outline-none transition-colors";

  return (
    <div
      className="mt-4 p-4 rounded-2xl border-l-4"
      style={{ background: 'var(--card)', borderColor: 'var(--warning)' }}
    >
      <p className="text-xs font-syne font-bold uppercase tracking-widest mb-1"
         style={{ color: 'var(--warning)' }}>
        AI parser unavailable
      </p>
      <p className="text-xs mb-3" style={{ color: 'var(--text-sub)' }}>
        Enter the expense manually below.
      </p>
      <form onSubmit={handleSubmit} className="space-y-2">
        <input
          value={vendor}
          onChange={e => setVendor(e.target.value)}
          placeholder="Vendor / description"
          className={inputCls}
          aria-label="Vendor"
        />
        <div className="flex gap-2">
          <input
            type="number"
            min="0"
            step="any"
            value={amount}
            onChange={e => setAmount(e.target.value)}
            placeholder="Amount (₹)"
            className={`${inputCls} flex-1`}
            aria-label="Amount"
          />
          <select
            value={category}
            onChange={e => setCategory(e.target.value)}
            className={`${inputCls} flex-1`}
            aria-label="Category"
          >
            {Object.keys(CATEGORY_ICONS).map(c => (
              <option key={c} value={c}>{CATEGORY_ICONS[c]} {c}</option>
            ))}
          </select>
        </div>
        <input
          value={note}
          onChange={e => setNote(e.target.value)}
          placeholder="Note (optional)"
          className={inputCls}
          aria-label="Note"
        />
        <div className="flex gap-2 pt-1">
          <button
            type="submit"
            disabled={saving || !vendor.trim() || !amount}
            className="flex-1 py-2.5 rounded-xl text-sm font-syne font-semibold
                       disabled:opacity-50 transition-opacity"
            style={{ background: 'var(--warning)', color: '#000' }}
          >
            {saving ? "Saving…" : "Save Manually"}
          </button>
          <button
            type="button"
            onClick={onDismiss}
            className="px-4 py-2.5 rounded-xl text-sm transition-colors"
            style={{ background: 'var(--card2)', color: 'var(--text-sub)' }}
          >
            Dismiss
          </button>
        </div>
      </form>
    </div>
  );
}

function TodaysMantraCard({ refreshKey }: { refreshKey: number }) {
  const { selMonth } = useMonth();
  const { toast } = useToast();
  const [data, setData] = useState<DailyMantra | null>(null);
  const [showWhy, setShowWhy] = useState(false);

  useEffect(() => {
    api.get<DailyMantra>(`/insights/mantra/${selMonth}`)
      .then(r => setData(r.data))
      .catch(() => {}); // fail silently — card simply doesn't render
  }, [selMonth, refreshKey]);

  if (!data) return null;

  const ctx = data.context;
  const fmtRs = (v: number) => `₹${Math.round(v).toLocaleString("en-IN")}`;

  return (
    <section>
      <div
        className="rounded-2xl overflow-hidden border"
        style={{
          background:  'var(--card)',
          borderColor: 'var(--accent)',
          boxShadow:   '0 0 24px -8px var(--accent2)',
        }}
      >
        {/* Top row: content left, avatar right */}
        <div className="flex">
          {/* Left: heading + divider + mantra */}
          <div className="flex-1 p-4">
            <p className="text-xs font-syne font-bold uppercase tracking-widest mb-2"
               style={{ color: 'var(--accent)' }}>
              🪷 Today's Mantra
            </p>
            <div className="h-px w-12 mb-3" style={{ background: 'var(--accent)', opacity: 0.4 }} />
            <p className="text-sm leading-relaxed italic" style={{ color: 'var(--text)' }}>
              {data.mantra}
            </p>
          </div>

          {/* Right: Tara avatar — hidden below 360px so text isn't squeezed */}
          <div
            className="hidden min-[360px]:block flex-shrink-0"
            style={{ width: '100px', alignSelf: 'stretch', position: 'relative', overflow: 'hidden' }}
          >
            <img
              src="/tara.png"
              alt="Tara"
              style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'top center' }}
            />
          </div>
        </div>

        {/* Bottom strip: Ask Tara pill + How Tara calculated this expand */}
        <div className="px-4 pb-4 flex items-center gap-3">
          <button
            onClick={() => toast("Ask Tara is coming soon! 🪷")}
            className="text-xs font-syne font-semibold px-3 py-1.5 rounded-full transition-opacity hover:opacity-80"
            style={{ background: 'var(--accent)', color: '#fff' }}
          >
            Ask Tara
          </button>
          <button
            onClick={() => setShowWhy(v => !v)}
            className="text-xs font-syne font-semibold transition-opacity hover:opacity-80"
            style={{ color: 'var(--accent)' }}
          >
            {showWhy ? "↑ Hide" : "How Tara calculated this ↓"}
          </button>
        </div>

        {/* Expandable context panel */}
        {showWhy && (
          <div
            className="mx-4 mb-4 rounded-xl p-3 space-y-1 text-xs"
            style={{ background: 'var(--card2, rgba(255,255,255,0.05))', color: 'var(--text-sub)' }}
          >
            <p><span className="font-semibold">Remaining:</span> {fmtRs(ctx.remaining)}</p>
            <p><span className="font-semibold">Days left:</span> {ctx.days_left}</p>
            {ctx.top_category && (
              <p>
                <span className="font-semibold">Top category:</span>{" "}
                {ctx.top_category} ({fmtRs(ctx.top_category_spent)})
                {ctx.top_category_prev_month_spent != null && (
                  <> · last month {fmtRs(ctx.top_category_prev_month_spent)}</>
                )}
              </p>
            )}
            {ctx.fixed_unpaid_total > 0 && (
              <p><span className="font-semibold">Fixed commitments pending:</span> {fmtRs(ctx.fixed_unpaid_total)}</p>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

export function QuickAddTab({ onExpenseAdded }: Props = {}) {
  const { selMonth } = useMonth();
  const today = new Date().toISOString().slice(0, 10);

  // ── NL parse form state ─────────────────────────────────────────────────
  const [text, setText]         = useState("");
  const [date, setDate]         = useState(today);
  const [parsing, setParsing]   = useState(false);
  const [lastResult, setLastResult] = useState<ParseResult | null>(null);
  const [parseError, setParseError] = useState(false);

  // ── Favourites state ────────────────────────────────────────────────────
  const [favourites, setFavourites]   = useState<ExpenseTemplate[]>([]);
  const [loadingFav, setLoadingFav]   = useState<number | null>(null);

  // ── Mantra refresh signal ───────────────────────────────────────────────
  const [mantraRefresh, setMantraRefresh] = useState(0);

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
    setParseError(false);
    try {
      const { data } = await api.post<ParseResult>("/expenses/parse", {
        text: text.trim(),
        date_override: date,
      });
      setLastResult(data);
      setText("");          // clear input after successful parse
      refreshToday();       // update today's entries list
      if (data.saved.length > 0) {
        onExpenseAdded?.();
        setMantraRefresh(k => k + 1);
        toast(
          `${data.saved.length} expense${data.saved.length > 1 ? "s" : ""} saved`,
          { icon: "⚡" }
        );
      }
    } catch {
      setParseError(true);
    } finally {
      setParsing(false);
    }
  };

  const handleFavLog = async (id: number) => {
    setLoadingFav(id);
    try {
      await api.post(`/expense-templates/${id}/log`);
      refreshToday();
      onExpenseAdded?.();
      setMantraRefresh(k => k + 1);
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

      <TodaysMantraCard refreshKey={mantraRefresh} />

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

        {/* Parser fallback — shown when /expenses/parse fails for any reason */}
        {parseError && (
          <ManualEntryFallback
            date={date}
            onSaved={() => {
              setParseError(false);
              refreshToday();
              onExpenseAdded?.();
              setMantraRefresh(k => k + 1);
              toast("Expense saved manually", { icon: "✅" });
            }}
            onDismiss={() => setParseError(false)}
          />
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
          <div className="text-center py-8 space-y-3">
            <div className="text-3xl">🧾</div>
            <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
              Nothing logged today.
            </p>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
              Start your day by logging something small.
            </p>
            <div className="flex gap-2 justify-center flex-wrap mt-2">
              {(["tea 20", "uber 180", "milk 60"] as const).map(suggestion => (
                <button
                  key={suggestion}
                  onClick={() => setText(suggestion)}
                  className="text-xs px-3 py-1.5 rounded-full border transition-colors"
                  style={{
                    borderColor: 'var(--accent)',
                    color:       'var(--accent)',
                    background:  'transparent',
                  }}
                >
                  {suggestion}
                </button>
              ))}
            </div>
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

      {/* Ask Tara FAB — shell only, chat backend not yet built */}
      <button
        onClick={() => toast("Ask Tara is coming soon! 🪷")}
        aria-label="Ask Tara"
        style={{
          position:       'fixed',
          bottom:         '72px',
          right:          '16px',
          width:          '52px',
          height:         '52px',
          borderRadius:   '50%',
          background:     'var(--accent)',
          color:          '#fff',
          display:        'flex',
          alignItems:     'center',
          justifyContent: 'center',
          zIndex:         30,
          border:         'none',
          boxShadow:      '0 4px 16px rgba(0,0,0,0.3)',
          cursor:         'pointer',
        }}
      >
        <MessageCircle size={22} />
      </button>

    </div>
  );
}
