import { CATEGORY_ICONS } from "@/utils/categories";
import { fmtInr } from "@/utils/formatInr";

/**
 * MoMTable — Month-over-Month spending table
 *
 * Streamlit ref: table_html in with tab3: (custom HTML table, no horizontal scroll)
 *
 * Improvements:
 *   - overflow-x-auto → scrolls horizontally on mobile
 *   - Latest month column is bold, previous months are muted
 *   - Trend arrows: ↑ red (>10% increase), ↓ green (>10% decrease), → neutral
 *   - Peak spend cell highlighted with red background
 */

interface MoM {
  months: string[];
  categories: Record<string, Record<string, number>>;
}

function fmtMonthLabel(m: string): string {
  const [y, mo] = m.split("-");
  return new Date(Number(y), Number(mo) - 1)
    .toLocaleDateString("en-IN", { month: "short", year: "numeric" });
}

export function MoMTable({ mom }: { mom: MoM }) {
  const { months, categories } = mom;
  if (!months.length || !Object.keys(categories).length) return null;

  return (
    <div className="bg-dark-card border border-white/10 rounded-2xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b border-white/10">
              <th
                className="text-left text-xs px-4 py-2.5 font-semibold whitespace-nowrap"
                style={{ color: "var(--text-sub)" }}
              >
                Category
              </th>
              {months.map(m => (
                <th
                  key={m}
                  className="text-right text-xs px-4 py-2.5 font-semibold whitespace-nowrap"
                  style={{ color: "var(--text-sub)" }}
                >
                  {fmtMonthLabel(m)}
                </th>
              ))}
              <th
                className="text-center text-xs px-4 py-2.5 font-semibold"
                style={{ color: "var(--text-sub)" }}
              >
                Trend
              </th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(categories)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([cat, monthData]) => {
                const vals    = months.map(m => monthData[m] ?? 0);
                const last    = vals[vals.length - 1];
                const prev    = vals[vals.length - 2] ?? 0;
                const chg     = prev > 0 ? ((last - prev) / prev) * 100 : null;
                const maxVal  = Math.max(...vals);

                const trendEl =
                  chg === null         ? <span style={{ color: "var(--text-muted)" }}>—</span>
                  : chg > 10           ? <span className="text-red-400">↑ {Math.round(chg)}%</span>
                  : chg < -10          ? <span className="text-emerald-400">↓ {Math.round(Math.abs(chg))}%</span>
                  :                      <span style={{ color: "var(--text-muted)" }}>→</span>;

                return (
                  <tr key={cat} className="border-b border-white/5">
                    {/* Category label */}
                    <td
                      className="px-4 py-2 text-xs whitespace-nowrap text-white"
                    >
                      {CATEGORY_ICONS[cat] ?? "📦"} {cat}
                    </td>

                    {/* Monthly values */}
                    {vals.map((v, i) => {
                      const isLatest = i === vals.length - 1;
                      const isPeak   = v === maxVal && v > 0 && isLatest;
                      return (
                        <td
                          key={i}
                          className={`px-4 py-2 text-right font-syne text-xs whitespace-nowrap
                                      ${isPeak ? "bg-red-500/10" : ""}`}
                          style={{
                            color:      isLatest ? "var(--text)" : "var(--text-muted)",
                            fontWeight: isLatest ? 700 : 400,
                          }}
                        >
                          {v > 0 ? fmtInr(v) : "—"}
                        </td>
                      );
                    })}

                    {/* Trend */}
                    <td className="px-4 py-2 text-center text-xs">
                      {trendEl}
                    </td>
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
