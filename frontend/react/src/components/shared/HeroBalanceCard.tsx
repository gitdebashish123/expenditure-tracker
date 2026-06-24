import type { Summary } from "@/types";
import { fmtInr } from "@/utils/formatInr";
import { Wallet } from "lucide-react";

interface Props { balance: Summary["balance"]; }

export function HeroBalanceCard({ balance }: Props) {
  const today = new Date();
  const daysInMonth  = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
  const daysLeft     = Math.max(daysInMonth - today.getDate(), 0);
  const dailyBudget  = daysLeft > 0 ? balance.remaining / daysLeft : 0;
  const subLabel     = balance.remaining > 0 && dailyBudget > 500
    ? `Comfortable for the next ${daysLeft} day${daysLeft !== 1 ? "s" : ""}`
    : `₹${Math.round(dailyBudget).toLocaleString("en-IN")}/day remaining`;

  return (
    <div className="space-y-3">

      {/* Main hero card */}
      <div
        className="rounded-2xl p-5 border"
        style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
      >
        <div className="flex items-start gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: "rgba(52,211,153,0.15)" }}
          >
            <Wallet size={20} style={{ color: "#34d399" }} />
          </div>
          <div>
            <p
              className="text-[10px] font-syne font-bold uppercase tracking-widest mb-1"
              style={{ color: "var(--text-sub)" }}
            >
              Remaining this month
            </p>
            <p
              className="text-3xl font-syne font-extrabold leading-none"
              style={{ color: balance.remaining >= 0 ? "#34d399" : "#f87171" }}
            >
              {fmtInr(balance.remaining)}
            </p>
            <p className="text-xs mt-1.5" style={{ color: "var(--text-muted)" }}>
              {subLabel}
            </p>
          </div>
        </div>
      </div>

      {/* 3 chips — Income, Fixed Paid, Pending Bills */}
      <div className="grid grid-cols-3 gap-2">
        {[
          { label: "Income",        value: balance.total_income,       colour: "#6366f1" },
          { label: "Fixed Paid",    value: balance.fixed_paid_total,   colour: "#34d399" },
          { label: "Pending Bills", value: balance.fixed_unpaid_total, colour: "#f59e0b" },
        ].map(chip => (
          <div
            key={chip.label}
            className="rounded-xl p-3 text-center border"
            style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
          >
            <p
              className="text-[9px] font-syne font-bold uppercase tracking-wider mb-1"
              style={{ color: "var(--text-muted)" }}
            >
              {chip.label}
            </p>
            <p className="text-sm font-syne font-bold" style={{ color: chip.colour }}>
              {fmtInr(chip.value)}
            </p>
          </div>
        ))}
      </div>

    </div>
  );
}
