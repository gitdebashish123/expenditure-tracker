import { useState } from "react";
import { api } from "@/api/client";
import { CATEGORY_ICONS } from "@/utils/categories";
import { fmtInr } from "@/utils/formatInr";
import type { Pool } from "@/types";
import { Plus, Trash2, ChevronDown, ChevronUp } from "lucide-react";

interface Props {
  pool: Pool;
  selMonth: string;
  onChanged: () => void;
}

/**
 * PoolCard — expandable card for a variable-amount recurring bill
 *
 * Streamlit ref: pool header + entry list + add-payment form inside pools loop in with tab2:
 *
 * Shows:
 *   - Pool header with name, category, paid/unpaid status (tap to expand/collapse)
 *   - Entry list: each payment with tick toggle + amount + delete
 *   - Inline "Add Payment" form: label + amount → POST /pools/{id}/entries/{month}
 *   - Pool total footer when entries exist
 *
 * Key improvement over Streamlit: add-payment form is inline, no full rerun needed.
 * Starts expanded by default so the add-payment form is immediately visible.
 */
export function PoolCard({ pool, selMonth, onChanged }: Props) {
  const [expanded, setExpanded] = useState(true);
  const [label, setLabel]       = useState("");
  const [amount, setAmount]     = useState<number>(0);
  const [adding, setAdding]     = useState(false);

  const icon = CATEGORY_ICONS[pool.category] ?? "📦";

  const totalPaid  = pool.paid_total;
  const totalUnpaid = pool.unpaid_total;
  const grandTotal  = totalPaid + totalUnpaid;

  // Status label shown in header
  const poolStatus =
    pool.entry_count === 0
      ? "⚠️ No entries yet"
      : totalUnpaid === 0
      ? `✅ ${fmtInr(totalPaid)} paid`
      : `${fmtInr(totalPaid)} paid · ${fmtInr(totalUnpaid)} unpaid`;

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!label.trim() || amount <= 0) return;
    setAdding(true);
    try {
      await api.post(`/pools/${pool.id}/entries/${selMonth}`, {
        label: label.trim(),
        amount,
      });
      setLabel("");
      setAmount(0);
      onChanged();
    } finally {
      setAdding(false);
    }
  };

  const handleToggle = async (entryId: number) => {
    await api.patch(`/pools/entries/${entryId}/toggle`);
    onChanged();
  };

  const handleDelete = async (entryId: number) => {
    await api.delete(`/pools/entries/${entryId}`);
    onChanged();
  };

  return (
    <div className="bg-dark-card border border-white/10 rounded-2xl overflow-hidden">

      {/* Pool header — tap to expand / collapse */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center justify-between px-4 py-3
                   hover:bg-white/5 transition-colors"
      >
        <span className="font-syne font-semibold text-white text-sm">
          {icon} {pool.name}
        </span>
        <div className="flex items-center gap-2">
          <span className="text-xs" style={{ color: 'var(--text-sub)' }}>
            {poolStatus}
          </span>
          {expanded
            ? <ChevronUp size={14} style={{ color: 'var(--text-muted)' }} />
            : <ChevronDown size={14} style={{ color: 'var(--text-muted)' }} />
          }
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-2 border-t border-white/5">

          {/* Existing entries */}
          {pool.entries.length > 0 && (
            <div className="pt-2 space-y-1">
              {pool.entries.map(entry => (
                <div
                  key={entry.id}
                  className="flex items-center gap-3 py-1.5 border-b border-white/5"
                >
                  {/* Paid tick */}
                  <button
                    onClick={() => handleToggle(entry.id)}
                    className={`w-5 h-5 rounded-full border-2 flex items-center justify-center
                                flex-shrink-0 transition-all ${
                      entry.paid
                        ? "bg-emerald-500 border-emerald-500 text-white"
                        : "border-white/20 hover:border-indigo-400"
                    }`}
                    aria-label={entry.paid ? "Mark unpaid" : "Mark paid"}
                  >
                    {entry.paid && <span className="text-[9px] font-bold">✓</span>}
                  </button>

                  {/* Label + note */}
                  <span className={`flex-1 text-sm ${
                    entry.paid ? "line-through" : "text-white"
                  }`}
                  style={entry.paid ? { color: 'var(--text-muted)' } : {}}>
                    {entry.label}
                    {entry.note && (
                      <span className="ml-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                        · {entry.note}
                      </span>
                    )}
                  </span>

                  {/* Amount */}
                  <span className={`font-syne font-semibold text-sm ${
                    entry.paid ? "text-emerald-400" : ""
                  }`}
                  style={!entry.paid ? { color: 'var(--text-sub)' } : {}}>
                    {fmtInr(entry.amount)}
                  </span>

                  {/* Delete */}
                  <button
                    onClick={() => handleDelete(entry.id)}
                    className="hover:text-red-400 transition-colors flex-shrink-0"
                    style={{ color: 'var(--text-muted)' }}
                    aria-label="Remove entry"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Add Payment form */}
          <form onSubmit={handleAdd} className="flex gap-2 pt-2">
            <input
              value={label}
              onChange={e => setLabel(e.target.value)}
              placeholder="Label (e.g. Home, Self)"
              className="flex-1 bg-dark-card2 border border-white/10 rounded-lg
                         px-3 py-2 text-white text-sm placeholder-white/30
                         focus:border-accent focus:outline-none"
            />
            <input
              type="number"
              min="0"
              step="1"
              value={amount || ""}
              onChange={e => setAmount(Number(e.target.value))}
              placeholder="₹"
              className="w-24 bg-dark-card2 border border-white/10 rounded-lg
                         px-3 py-2 text-white text-sm
                         focus:border-accent focus:outline-none"
            />
            <button
              type="submit"
              disabled={adding || !label.trim() || amount <= 0}
              className="flex items-center gap-1 px-3 py-2 rounded-lg text-sm
                         bg-accent/20 hover:bg-accent/40 text-indigo-300
                         disabled:opacity-40 transition-colors"
            >
              <Plus size={14} />
              {adding ? "…" : "Add"}
            </button>
          </form>

          {/* Pool total footer */}
          {grandTotal > 0 && (
            <div className="flex justify-between pt-2 border-t border-white/5">
              <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                {pool.entry_count} payment(s)
              </span>
              <span className="font-syne font-bold text-xs text-white">
                {fmtInr(grandTotal)} total ·{" "}
                <span className="text-emerald-400">{fmtInr(totalPaid)} paid</span>
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
