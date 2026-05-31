import type { Expense } from "@/types";
import { fmtInr } from "@/utils/formatInr";

interface Props {
  item: Expense;
  onToggle: () => void;
}

/**
 * FixedExpenseRow — single fixed expense row with optimistic tick toggle
 *
 * Streamlit ref: tick button + vendor + amount row inside by_cat loop in with tab2:
 *
 * Key improvement: tick toggles INSTANTLY (optimistic UI).
 * Streamlit required a full page rerun on every PATCH /fixed/{id}/toggle.
 */
export function FixedExpenseRow({ item, onToggle }: Props) {
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

      {/* Vendor name — strikethrough when paid */}
      <span className={`flex-1 text-sm transition-all duration-200 ${
        item.paid ? "line-through" : "text-white"
      }`}
      style={item.paid ? { color: 'var(--text-muted)' } : {}}>
        {item.vendor}
        {item.note && (
          <span className="ml-2 text-xs" style={{ color: 'var(--text-muted)' }}>
            · {item.note}
          </span>
        )}
      </span>

      {/* Amount — green when paid */}
      <span className={`font-syne font-semibold text-sm flex-shrink-0 ${
        item.paid ? "text-emerald-400" : ""
      }`}
      style={!item.paid ? { color: 'var(--text-sub)' } : {}}>
        {fmtInr(item.amount)}
      </span>
    </div>
  );
}
