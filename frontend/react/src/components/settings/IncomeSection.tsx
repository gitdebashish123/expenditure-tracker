import { useEffect, useState, useCallback } from "react";
import { api } from "@/api/client";
import { useMonth } from "@/context/MonthContext";
import { fmtInr } from "@/utils/formatInr";
import { Save, Trash2 } from "lucide-react";
import { CurrencyInput } from "@/components/shared/CurrencyInput";

interface IncomeRow {
  id: number;
  source: string;
  amount: number;
  note: string | null;
}

const INCOME_SOURCES = [
  "Salary",
  "Freelance",
  "Dividend",
  "FD/RD Interest",
  "Rental",
  "Bonus",
  "Other",
] as const;

function getSelectValue(savedSource: string): string {
  return (INCOME_SOURCES as readonly string[]).includes(savedSource)
    ? savedSource
    : "Other";
}

export function IncomeSection() {
  const { selMonth } = useMonth();

  const [entries,      setEntries]      = useState<IncomeRow[]>([]);
  const [loading,      setLoading]      = useState(true);
  const [confirmId,    setConfirmId]    = useState<number | null>(null);

  // Add-new-source form
  const [showAddForm,  setShowAddForm]  = useState(false);
  const [selectSource, setSelectSource] = useState("Salary");
  const [customSource, setCustomSource] = useState("");
  const [amount,       setAmount]       = useState<number>(0);
  const [note,         setNote]         = useState("");
  const [saving,       setSaving]       = useState(false);
  const [saved,        setSaved]        = useState(false);

  const effectiveSource =
    selectSource === "Other" ? (customSource.trim() || "Other") : selectSource;

  const loadEntries = useCallback(() => {
    setLoading(true);
    api.get<IncomeRow[]>(`/income/${selMonth}/all`)
      .then(r => setEntries(r.data))
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  }, [selMonth]);

  useEffect(() => {
    loadEntries();
    // Reset add form when month changes
    setShowAddForm(false);
    setSelectSource("Salary");
    setCustomSource("");
    setAmount(0);
    setNote("");
  }, [loadEntries, selMonth]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!amount || amount <= 0) return;
    setSaving(true);
    try {
      await api.post("/income", {
        source:    effectiveSource,
        amount,
        note:      note.trim() || null,
        month_key: selMonth,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      setShowAddForm(false);
      setSelectSource("Salary");
      setCustomSource("");
      setAmount(0);
      setNote("");
      loadEntries();
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    setEntries(prev => prev.filter(e => e.id !== id));
    try {
      await api.delete(`/income/${id}`);
    } catch {
      loadEntries(); // restore on failure
    }
  };

  const totalIncome = entries.reduce((s, e) => s + e.amount, 0);

  const inputCls =
    "bg-dark-card2 border border-white/10 rounded-xl px-4 py-3 text-white " +
    "text-sm placeholder-white/30 focus:border-accent focus:outline-none transition-colors";

  return (
    <section>
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-syne font-bold text-white">💰 My Take-home</h2>
            <p className="text-sm mt-0.5" style={{ color: "var(--text-sub)" }}>
              All income credited this month. Add salary, dividends, bonuses, etc.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setShowAddForm(o => !o)}
            className="flex-shrink-0 text-xs font-semibold px-3 py-1.5 rounded-lg
                       border border-accent/40 text-indigo-300 hover:bg-accent/10
                       transition-colors"
          >
            + Add Income
          </button>
        </div>
        <div className="border-b border-white/10 mt-3" />
      </div>

      {/* Existing income entries */}
      {!loading && entries.length > 0 && (
        <div className="space-y-2 mb-4">
          {entries.map(entry => (
            <div
              key={entry.id}
              className="flex items-center justify-between px-4 py-3
                         bg-dark-card2 border border-white/10 rounded-xl"
            >
              <div className="min-w-0">
                <p className="text-sm text-white font-medium">{entry.source}</p>
                {entry.note && (
                  <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                    {entry.note}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                <span className="font-syne font-semibold text-sm text-emerald-400">
                  +{fmtInr(entry.amount)}
                </span>
                {confirmId === entry.id ? (
                  <div className="flex items-center gap-1.5 text-xs">
                    <span style={{ color: "var(--text-sub)" }}>Remove?</span>
                    <button
                      onClick={() => { handleDelete(entry.id); setConfirmId(null); }}
                      className="text-red-400 hover:text-red-300 font-semibold transition-colors"
                    >Yes</button>
                    <button
                      onClick={() => setConfirmId(null)}
                      className="transition-colors"
                      style={{ color: "var(--text-muted)" }}
                    >No</button>
                  </div>
                ) : (
                  <button
                    onClick={() => setConfirmId(entry.id)}
                    className="w-10 h-10 flex items-center justify-center rounded-lg
                               hover:text-red-400 hover:bg-red-500/10 transition-colors"
                    style={{ color: "var(--text-muted)" }}
                    aria-label={`Remove ${entry.source}`}
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            </div>
          ))}

          {/* Total row */}
          <div className="flex justify-between items-center px-4 py-2
                          bg-emerald-500/5 border border-emerald-500/20 rounded-xl">
            <span className="text-xs font-semibold uppercase tracking-widest"
                  style={{ color: "var(--text-sub)" }}>
              Total Income
              <span className="normal-case tracking-normal font-normal ml-1.5"
                    style={{ color: "var(--text-muted)" }}>
                · {entries.length} source{entries.length !== 1 ? "s" : ""}
              </span>
            </span>
            <span className="font-syne font-bold text-emerald-400">
              {fmtInr(totalIncome)}
            </span>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && entries.length === 0 && (
        <p className="text-sm mb-4" style={{ color: "var(--text-muted)" }}>
          No income recorded for {selMonth} yet.
        </p>
      )}

      {/* Add income form */}
      {showAddForm && (
        <form onSubmit={handleSave} className="space-y-3 mt-2">
          <div className="grid grid-cols-2 gap-3">
            <select
              value={selectSource}
              onChange={e => setSelectSource(e.target.value)}
              className={inputCls}
            >
              {INCOME_SOURCES.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <CurrencyInput
              value={amount}
              onChange={v => setAmount(v)}
              placeholder="Amount (₹)"
              className={inputCls}
              autoFocus
            />
          </div>

          {selectSource === "Other" && (
            <input
              value={customSource}
              onChange={e => setCustomSource(e.target.value)}
              placeholder="Specify income source…"
              className={`w-full ${inputCls}`}
            />
          )}

          <input
            value={note}
            onChange={e => setNote(e.target.value)}
            placeholder="Note (optional)"
            className={`w-full ${inputCls}`}
          />

          <div className="flex gap-2">
            <button
              type="submit"
              disabled={saving || !amount || amount <= 0}
              className="flex items-center gap-2 bg-gradient-to-r from-accent to-accent2
                         text-white font-semibold px-6 py-2.5 rounded-xl text-sm
                         disabled:opacity-50 transition-opacity"
            >
              <Save size={14} />
              {saving ? "Saving…" : saved ? "✅ Saved!" : "Save"}
            </button>
            <button
              type="button"
              onClick={() => setShowAddForm(false)}
              className="px-4 py-2.5 rounded-xl text-sm transition-colors
                         bg-dark-card text-white/50 hover:text-white"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
