import { useState, useRef } from "react";
import { api } from "@/api/client";
import type { Expense } from "@/types";
import { fmtInr } from "@/utils/formatInr";
import { Pencil } from "lucide-react";

interface Props {
  item:           Expense;
  onToggle:       () => void;
  onAmountChange: () => void;  // signals parent to re-fetch after amount edit
}

/**
 * FixedExpenseRow — single fixed expense row with optimistic tick toggle
 * and inline amount editing for the current month's instance.
 *
 * Streamlit ref: tick button + vendor + amount row inside by_cat loop in with tab2:
 *
 * Key improvement: tick toggles INSTANTLY (optimistic UI).
 * Pencil icon reveals an inline amount field — edits this month's instance only
 * (template is not affected; use Settings → Monthly Bills to change future months).
 */
export function FixedExpenseRow({ item, onToggle, onAmountChange }: Props) {
  const [editing, setEditing]   = useState(false);
  const [amt, setAmt]           = useState(item.amount);
  const [saving, setSaving]     = useState(false);
  const inputRef                = useRef<HTMLInputElement>(null);

  const startEdit = () => {
    setAmt(item.amount);
    setEditing(true);
    // Focus the input after it renders
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const commitEdit = async () => {
    if (amt === item.amount) { setEditing(false); return; }
    setSaving(true);
    try {
      await api.patch(`/fixed/${item.id}/amount`, null, { params: { amount: amt } });
      setEditing(false);
      onAmountChange();
    } finally {
      setSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") commitEdit();
    if (e.key === "Escape") setEditing(false);
  };

  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-white/5">

      {/* Tick button — optimistic, updates UI before backend confirms */}
      <button
        onClick={onToggle}
        className={`w-6 h-6 rounded-full border-2 flex items-center justify-center
                    flex-shrink-0 transition-all duration-150 ${
          item.paid
            ? "bg-emerald-500 border-emerald-500 text-white"
            : "border-white/20 hover:border-indigo-400"
        }`}
        aria-label={item.paid ? "Mark unpaid" : "Mark paid"}
      >
        {item.paid && <span className="text-[10px] font-bold">✓</span>}
      </button>

      {/* Vendor name — muted when paid, no strikethrough */}
      <span
        className="flex-1 text-sm transition-all duration-200"
        style={{ color: item.paid ? "var(--text-muted)" : "white" }}
      >
        {item.vendor}
        {item.note && item.note !== "Auto-seeded fixed expense" && (
          <span className="ml-2 text-xs" style={{ color: "var(--text-muted)" }}>
            · {item.note}
          </span>
        )}
      </span>

      {/* Amount — inline editable on pencil tap */}
      {editing ? (
        <input
          ref={inputRef}
          type="text"
          inputMode="decimal"
          value={amt}
          onChange={e => setAmt(parseFloat(e.target.value) || 0)}
          onBlur={commitEdit}
          onKeyDown={handleKeyDown}
          disabled={saving}
          className="w-24 bg-dark-bg border border-indigo-400 rounded-lg px-2 py-1
                     text-white text-sm text-right focus:outline-none
                     [appearance:textfield]
                     [&::-webkit-outer-spin-button]:appearance-none
                     [&::-webkit-inner-spin-button]:appearance-none"
          aria-label="Edit amount"
        />
      ) : (
        <span className={`font-syne font-semibold text-sm flex-shrink-0 ${
          item.paid ? "text-emerald-400" : ""
        }`}
        style={!item.paid ? { color: "var(--text-sub)" } : {}}>
          {fmtInr(item.amount)}
        </span>
      )}

      {/* Pencil — only shown when not editing */}
      {!editing && (
        <button
          onClick={startEdit}
          className="flex-shrink-0 transition-colors hover:text-indigo-400"
          style={{ color: "var(--text-muted)" }}
          aria-label="Edit amount for this month"
        >
          <Pencil size={12} />
        </button>
      )}
    </div>
  );
}
