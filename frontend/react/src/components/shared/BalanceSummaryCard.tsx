import { fmtInr } from "@/utils/formatInr";

interface Props {
  label: string;
  value: number;
  sub: string;
  accent?: boolean;
  highlight?: "success" | "danger";
}

/**
 * BalanceSummaryCard — one of the three top balance cards
 *
 * Streamlit ref: bal-card divs in the balance-grid section of frontend/app.py
 *
 * accent=true  → indigo gradient background (used for "Remaining")
 * highlight    → overrides value colour: success=green, danger=red
 */
export function BalanceSummaryCard({ label, value, sub, accent, highlight }: Props) {
  const valueColour =
    highlight === "success" ? "#34d399"
    : highlight === "danger" ? "#f87171"
    : "var(--text)";

  return (
    <div
      className={`rounded-2xl p-3 sm:p-4 border ${
        accent
          ? "bg-gradient-to-br from-indigo-600 to-purple-600 border-transparent"
          : "bg-dark-card border-white/10"
      }`}
    >
      <p
        className="text-[10px] uppercase tracking-widest mb-1 truncate"
        style={{ color: accent ? "rgba(255,255,255,0.7)" : "var(--text-sub)" }}
      >
        {label}
      </p>
      <p
        className="font-syne font-bold text-base sm:text-lg leading-none"
        style={{ color: valueColour }}
      >
        {fmtInr(value)}
      </p>
      <p
        className="text-[10px] mt-1 truncate"
        style={{ color: accent ? "rgba(255,255,255,0.5)" : "var(--text-muted)" }}
      >
        {sub}
      </p>
    </div>
  );
}
