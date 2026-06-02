import { fmtInr } from "@/utils/formatInr";

interface Props {
  label:   string;
  value:   number;
  colour:  string;
}

export function SummaryFlipCard({ label, value, colour }: Props) {
  return (
    <div
      className="flip-card flex-1 rounded-2xl cursor-default"
      style={{ height: "80px" }}
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
