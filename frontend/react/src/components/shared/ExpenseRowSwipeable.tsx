import { useRef, useState } from "react";
import { Trash2 } from "lucide-react";
import { CATEGORY_ICONS } from "@/utils/categories";
import { fmtInr } from "@/utils/formatInr";
import type { Expense } from "@/types";

interface Props {
  expense: Expense;
  onDelete: () => void;
}

/**
 * ExpenseRowSwipeable — single expense row with swipe-to-delete
 *
 * Streamlit ref: Today's Entries row in with tab1: of frontend/app.py
 * Streamlit used injected JS for swipe — fragile and unreliable.
 * This uses clean React touch events.
 *
 * Mobile: swipe left 80px → red delete zone reveals → release → calls onDelete
 * Desktop: trash button appears on hover (hidden on mobile)
 */
export function ExpenseRowSwipeable({ expense, onDelete }: Props) {
  const [offsetX, setOffsetX]   = useState(0);
  const startX                  = useRef(0);
  const THRESHOLD               = 80;

  const onTouchStart = (e: React.TouchEvent) => {
    startX.current = e.touches[0].clientX;
  };

  const onTouchMove = (e: React.TouchEvent) => {
    const dx = e.touches[0].clientX - startX.current;
    // Only allow left swipe (negative dx), cap at THRESHOLD
    if (dx < 0) setOffsetX(Math.max(dx, -THRESHOLD));
  };

  const onTouchEnd = () => {
    if (offsetX <= -THRESHOLD) {
      onDelete();
    } else {
      setOffsetX(0); // snap back
    }
  };

  const icon = CATEGORY_ICONS[expense.category] ?? "📦";

  return (
    <div className="relative overflow-hidden rounded-xl">

      {/* Red delete layer — revealed as row slides left */}
      <div className="absolute inset-y-0 right-0 w-20 bg-red-500
                      flex items-center justify-center rounded-r-xl">
        <Trash2 size={18} className="text-white" />
      </div>

      {/* Main row — slides left on swipe */}
      <div
        className="relative bg-dark-card border border-white/5 rounded-xl
                   flex items-center gap-3 px-4 py-3 transition-transform"
        style={{ transform: `translateX(${offsetX}px)` }}
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
      >
        {/* Category icon */}
        <div className="w-9 h-9 rounded-xl bg-dark-card2 flex items-center justify-center
                        text-lg flex-shrink-0">
          {icon}
        </div>

        {/* Vendor + category */}
        <div className="flex-1 min-w-0">
          <p className="text-white text-sm font-medium truncate">
            {expense.vendor}
            {expense.note && (
              <span className="ml-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                · {expense.note}
              </span>
            )}
          </p>
          <p className="text-xs" style={{ color: 'var(--text-sub)' }}>
            {expense.category}
          </p>
        </div>

        {/* Amount */}
        <span className="font-syne font-semibold text-red-400 flex-shrink-0 text-sm">
          -{fmtInr(expense.amount)}
        </span>

        {/* Desktop delete button — hidden on mobile (swipe is used instead) */}
        <button
          onClick={onDelete}
          className="hidden sm:flex w-7 h-7 items-center justify-center rounded-lg
                     hover:text-red-400 hover:bg-red-500/10 flex-shrink-0 transition-colors"
          style={{ color: 'var(--text-muted)' }}
          aria-label={`Delete ${expense.vendor}`}
        >
          <Trash2 size={14} />
        </button>
      </div>
    </div>
  );
}
