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
 */
export function IncomeSection() {
  const { selMonth } = useMonth();

  const [source, setSource] = useState("Salary");
  const [amount, setAmount] = useState<number>(0);
  const [note,   setNote]   = useState("");
  const [saving, setSaving] = useState(false);
  const [saved,  setSaved]  = useState(false);

  // Load existing income for the selected month
  useEffect(() => {
    api.get<IncomeEntry>(`/income/${selMonth}`)
      .then(r => {
        setSource(r.data.source ?? "Salary");
        setAmount(r.data.amount ?? 0);
        setNote(r.data.note ?? "");
      })
      .catch(() => {
        // No income set yet — keep form defaults
        setSource("Salary");
        setAmount(0);
        setNote("");
      });
  }, [selMonth]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/income", {
        source:    source.trim() || "Salary",
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
          <input
            value={source}
            onChange={e => setSource(e.target.value)}
            placeholder="e.g. Infosys Salary, Freelance"
            className={inputCls}
          />
          <input
            type="number"
            min="0"
            step="1000"
            value={amount || ""}
            onChange={e => setAmount(Number(e.target.value))}
            placeholder="Amount (₹)"
            className={inputCls}
          />
        </div>
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
