import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { CATEGORY_ICONS } from "@/utils/categories";
import { fmtInr } from "@/utils/formatInr";

/**
 * SpendDonut — category spending donut chart
 *
 * Bonus component — no equivalent in Streamlit.
 * Streamlit used custom HTML category rows without a chart.
 * Uses Recharts PieChart with innerRadius for a donut shape.
 */

const CHART_COLOURS = [
  "#6366f1", "#8b5cf6", "#ec4899", "#f59e0b",
  "#34d399", "#06b6d4", "#f87171", "#a3e635",
];

interface Props {
  categories: Array<{ category: string; spent: number }>;
}

export function SpendDonut({ categories }: Props) {
  const data = categories.filter(c => c.spent > 0).slice(0, 8);
  if (data.length === 0) return null;

  return (
    <div className="bg-dark-card border border-white/10 rounded-2xl p-4">
      <ResponsiveContainer width="100%" height={180}>
        <PieChart>
          <Pie
            data={data}
            dataKey="spent"
            nameKey="category"
            cx="50%"
            cy="50%"
            innerRadius={48}
            outerRadius={78}
            paddingAngle={2}
            strokeWidth={0}
          >
            {data.map((_, i) => (
              <Cell
                key={i}
                fill={CHART_COLOURS[i % CHART_COLOURS.length]}
              />
            ))}
          </Pie>
          <Tooltip
            formatter={(v: number) => [fmtInr(v), "Spent"]}
            contentStyle={{
              background: "#1a1a28",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 12,
              color: "white",
              fontSize: 12,
            }}
            labelStyle={{ color: "white" }}
            itemStyle={{ color: "white" }}
          />
        </PieChart>
      </ResponsiveContainer>

      {/* Legend grid */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-2 mt-2">
        {data.map((c, i) => (
          <div key={c.category} className="flex items-center gap-2 text-xs min-w-0">
            <span
              className="w-2 h-2 rounded-full flex-shrink-0"
              style={{ background: CHART_COLOURS[i % CHART_COLOURS.length] }}
            />
            <span className="truncate" style={{ color: "var(--text-sub)" }}>
              {CATEGORY_ICONS[c.category] ?? "📦"} {c.category}
            </span>
            <span className="ml-auto flex-shrink-0" style={{ color: "var(--text-muted)" }}>
              {fmtInr(c.spent)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
