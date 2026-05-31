import { useEffect, useState } from "react";
import { api } from "@/api/client";
import { useMonth } from "@/context/MonthContext";
import { fmtMonth } from "@/utils/formatDate";

/**
 * MonthSelector — global month dropdown
 *
 * Streamlit ref: selectbox("Month", all_months, ...) in frontend/app.py
 * Fetches available months from GET /months, always includes current month.
 * Selecting a past month updates MonthContext — all tabs re-fetch accordingly.
 */
export function MonthSelector() {
  const { selMonth, setSelMonth } = useMonth();
  const [months, setMonths] = useState<string[]>([]);

  useEffect(() => {
    const current = new Date().toISOString().slice(0, 7);
    api.get<string[]>("/months")
      .then((r) => {
        const all = Array.from(new Set([current, ...r.data])).sort().reverse();
        setMonths(all);
      })
      .catch(() => {
        setMonths([new Date().toISOString().slice(0, 7)]);
      });
  }, []);

  return (
    <select
      value={selMonth}
      onChange={(e) => setSelMonth(e.target.value)}
      className="bg-dark-card2 border border-white/10 rounded-xl px-3 py-2 text-white text-sm
                 focus:border-accent focus:outline-none cursor-pointer"
    >
      {months.map((m) => (
        <option key={m} value={m}>
          {fmtMonth(m)}
        </option>
      ))}
    </select>
  );
}
