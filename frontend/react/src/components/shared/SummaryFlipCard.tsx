import { useState } from "react";
import { fmtInr } from "@/utils/formatInr";

interface Props {
  label:   string;
  value:   number;
  colour:  string;
}

export function SummaryFlipCard({ label, value, colour }: Props) {
  const [flipped, setFlipped] = useState(false);

  return (
    <div
      className={`flip-card flex-1 rounded-2xl cursor-pointer${flipped ? " flip-card-flipped" : ""}`}
      style={{ height: "80px" }}
      onClick={() => setFlipped(f => !f)}
      role="button"
      tabIndex={0}
      aria-label={`${label}: tap to reveal amount`}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          setFlipped(f => !f);
        }
      }}
    >
      <div className="flip-card-inner rounded-2xl">
        {/* Front — label */}
        <div
          className="flip-card-front rounded-2xl border border-white/10 p-3"
          style={{ backgroundColor: "var(--card)" }}
        >
          <span
            className="text-[10px] font-syne font-bold uppercase tracking-widest text-center"
            style={{ color: "var(--text-sub)" }}
          >
            {label}
          </span>
          <div
            className="w-8 h-0.5 rounded-full mt-1.5"
            style={{ backgroundColor: colour, opacity: 0.6 }}
          />
          <span
            className="text-[8px] mt-1.5 opacity-50"
            style={{ color: "var(--text-muted)" }}
          >
            tap to reveal
          </span>
        </div>

        {/* Back — amount */}
        <div
          className="flip-card-back rounded-2xl border p-3"
          style={{
            backgroundColor: "var(--card2)",
            borderColor: colour + "40",
            borderTopWidth: "2px",
            borderTopColor: colour,
          }}
        >
          <span
            className="font-syne font-bold text-base leading-none"
            style={{ color: colour }}
          >
            {fmtInr(value)}
          </span>
          <span
            className="text-[9px] uppercase tracking-widest mt-1"
            style={{ color: "var(--text-muted)" }}
          >
            {label}
          </span>
        </div>
      </div>
    </div>
  );
}
