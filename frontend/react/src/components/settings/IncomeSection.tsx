import { useEffect, useState } from "react";
import { api } from "@/api/client";
import { useMonth } from "@/context/MonthContext";
import type { IncomeEntry } from "@/types";
import { Save } from "lucide-react";

/**
 * IncomeSection — monthly take-home income form
 *
 * Streamlit ref: settings_section("💰", "My Take-home", ...) in with tab5:
 * POST /income { source, amount, note, month_key }
 * Loads existing income for selected month on mount and on month change.
 *
 * Source is a dropdown of common income types.
 * "Other" reveals a free-text field (backward-compatible: if the saved source
 * doesn't match a preset option it pre-selects "Other" and fills customSource).
 */

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

  const [selectSource, setSelectSource] = useState("Salary");
  const [customSource, setCustomSource] = useState("");
  const [amount, setAmount] = useState<number>(0);
  const [note,   setNote]   = useState("");
  const [saving, setSaving] = useState(false);
  const [saved,  setSaved]  = useState(false);

  // Derived: the value actually submitted to the API
  const effectiveSource =
    selectSource === "Other" ? (customSource.trim() || "Other") : selectSource;

  // Load existing income for the selected month
  useEffect(() => {
    api.get<IncomeEntry>(`/income/${selMonth}`)
      .then(r => {
        const saved = r.data.source ?? "Salary";
        setSelectSource(getSelectValue(saved));
        setCustomSource(getSelectValue(saved) === "Other" ? saved : "");
        setAmount(r.data.amount ?? 0);
        setNote(r.data.note ?? "");
      })
      .catch(() => {
        setSelectSource("Salary");
        setCustomSource("");
        setAmount(0);
        setNote("");
      });
  }, [selMonth]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
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
    } finally {
      setSaving(false);
    }
  };

  const inputCls =
    "bg-dark-card2 border border-white/10 rounded-xl px-4 py-3 text-white " +
    "text-sm placeholder-white/30 focus:border-accent focus:outline-none transition-colors";

  return (
    <section>
      {/* Section header */}
      <div className="mb-4">
        <h2 className="font-syne font-bold text-white">💰 My Take-home</h2>
        <p className="text-sm mt-0.5" style={{ color: "var(--text-sub)" }}>
          Your salary or income credited this month.
        </p>
        <div className="border-b border-white/10 mt-3" />
      </div>

      <form onSubmit={handleSave} className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          {/* Source dropdown */}
          <select
            value={selectSource}
            onChange={e => setSelectSource(e.target.value)}
            className={inputCls}
          >
            {INCOME_SOURCES.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <input
            type="number"
            min="0"
            step="1"
            value={amount || ""}
            onChange={e => setAmount(Number(e.target.value))}
            placeholder="Amount (₹)"
            className={inputCls}
          />
        </div>

        {/* Free-text override when "Other" is selected */}
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
          placeholder="Note (optional, e.g. Includes bonus)"
          className={`w-full ${inputCls}`}
        />
        <button
          type="submit"
          disabled={saving}
          className="flex items-center gap-2 bg-gradient-to-r from-accent to-accent2
                     text-white font-semibold px-6 py-2.5 rounded-xl text-sm
                     disabled:opacity-50 transition-opacity"
        >
          <Save size={14} />
          {saving ? "Saving…" : saved ? "✅ Saved!" : "Save"}
        </button>
      </form>
    </section>
  );
}
