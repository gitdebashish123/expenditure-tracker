import { useEffect, useRef, useState } from "react";
import { fmtInr } from "@/utils/formatInr";

interface Balance {
  total_income: number;
  fixed_paid_total: number;
  fixed_unpaid_total: number;
  remaining: number;
}

interface ChipProps {
  label: string;
  target: number;
  colour: string;
}

function useCountUp(target: number, duration = 600): number {
  const [value, setValue] = useState(0);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    const start = performance.now();
    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(target * eased));
      if (progress < 1) rafRef.current = requestAnimationFrame(animate);
    };
    setValue(0);
    rafRef.current = requestAnimationFrame(animate);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [target, duration]);

  return value;
}

function Chip({ label, target, colour }: ChipProps) {
  const value = useCountUp(target);
  return (
    <div className="flex flex-col items-center flex-1 min-w-0 px-1">
      <span
        className="text-[9px] uppercase tracking-widest truncate w-full text-center"
        style={{ color: "var(--text-muted)" }}
      >
        {label}
      </span>
      <span
        className="font-syne font-bold text-xs mt-0.5 truncate w-full text-center"
        style={{ color: colour }}
      >
        {fmtInr(value)}
      </span>
    </div>
  );
}

interface Props {
  balance: Balance;
}

export function SummaryStrip({ balance }: Props) {
  const chips = [
    { label: "Remaining", target: balance.remaining,        colour: balance.remaining >= 0 ? "#34d399" : "#f87171" },
    { label: "Income",    target: balance.total_income,     colour: "#6366f1" },
    { label: "Fixed Paid",target: balance.fixed_paid_total, colour: "#f59e0b" },
  ];

  return (
    <div className="flex items-center divide-x"
         style={{ borderColor: "var(--border)" }}>
      {chips.map(c => (
        <Chip key={c.label} label={c.label} target={c.target} colour={c.colour} />
      ))}
    </div>
  );
}
