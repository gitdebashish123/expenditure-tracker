import { useEffect, useState, useCallback } from "react";
import { api } from "@/api/client";
import { CATEGORY_ICONS, FIXED_CATEGORIES } from "@/utils/categories";
import type { FixedExpenseTemplate } from "@/types";
import { ChevronDown, ChevronUp, Trash2, Save, Plus } from "lucide-react";

/**
 * BillsSection — fixed template management + add new bill form
 *
 * Streamlit ref: settings_section("📋", "Monthly Bills", ...) in with tab5:
 *
 * Three parts:
 *   1. Fixed templates grouped by category — expandable, inline edit per row
 *   2. Pool templates — flat list with remove button
 *   3. "Add a new bill" accordion — name, category, fixed/variable radio, amount
 *
 * Key improvement: "No, it varies" caption appears instantly on radio change.
 * Streamlit needed a full rerun for conditional UI inside st.form.
 */

// ── TemplateEditRow — inline edit for a single fixed template ─────────────────

function TemplateEditRow({
  template: t,
  onDelete,
  onSaved,
}: {
  template:  FixedExpenseTemplate;
  onDelete:  () => void;
  onSaved:   () => void;
}) {
  const [name,   setName]   = useState(t.name);
  const [amt,    setAmt]    = useState(t.amount);
  const [dueDay, setDueDay] = useState(t.due_day ?? 0);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put(`/fixed-templates/${t.id}`, {
        name:    name.trim(),
        amount:  amt,
        due_day: dueDay > 0 ? dueDay : null,
      });
      onSaved();
    } finally {
      setSaving(false);
    }
  };

  const inputCls =
    "bg-dark-bg border border-white/10 rounded-lg px-2.5 py-1.5 text-white " +
    "text-xs focus:border-accent focus:outline-none transition-colors";

  return (
    <div className="flex items-center gap-2 px-3 py-2">
      <input
        value={name}
        onChange={e => setName(e.target.value)}
        className={`flex-1 ${inputCls}`}
      />
      <input
        type="number"
        min="0"
        step="100"
        value={amt}
        onChange={e => setAmt(Number(e.target.value))}
        className={`w-24 ${inputCls}`}
      />
      <select
        value={dueDay}
        onChange={e => setDueDay(Number(e.target.value))}
        className={`w-28 ${inputCls}`}
      >
        <option value={0}>No reminder</option>
        {Array.from({ length: 28 }, (_, i) => i + 1).map(d => (
          <option key={d} value={d}>{d}th of month</option>
        ))}
      </select>
      <button
        onClick={handleSave}
        disabled={saving}
        className="text-indigo-400 hover:text-indigo-200 disabled:opacity-40 transition-colors"
        aria-label="Save"
      >
        <Save size={13} />
      </button>
      <button
        onClick={onDelete}
        className="hover:text-red-400 transition-colors"
        style={{ color: "var(--text-muted)" }}
        aria-label="Delete"
      >
        <Trash2 size={13} />
      </button>
    </div>
  );
}

// ── FixedTemplateCategoryGroup — collapsible group of fixed templates ─────────

function FixedTemplateCategoryGroup({
  category,
  items,
  onDelete,
  onSaved,
}: {
  category: string;
  items:    FixedExpenseTemplate[];
  onDelete: (id: number) => void;
  onSaved:  () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const icon = CATEGORY_ICONS[category] ?? "📦";

  return (
    <div className="border border-white/10 rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm
                   hover:bg-white/5 transition-colors"
      >
        <span style={{ color: "var(--text-sub)" }}>
          {icon} {category}{" "}
          <span style={{ color: "var(--text-muted)" }}>({items.length} bills)</span>
        </span>
        {expanded
          ? <ChevronUp size={13} style={{ color: "var(--text-muted)" }} />
          : <ChevronDown size={13} style={{ color: "var(--text-muted)" }} />
        }
      </button>

      {expanded && (
        <div className="border-t border-white/10 divide-y divide-white/5">
          {items.map(t => (
            <TemplateEditRow
              key={t.id}
              template={t}
              onDelete={() => onDelete(t.id)}
              onSaved={onSaved}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ── BillsSection — main exported component ───────────────────────────────────

export function BillsSection() {
  const [templates, setTemplates] = useState<FixedExpenseTemplate[]>([]);
  const [addOpen,   setAddOpen]   = useState(false);

  // Add bill form state
  const [newName,  setNewName]  = useState("");
  const [newCat,   setNewCat]   = useState(FIXED_CATEGORIES[0]);
  const [newKind,  setNewKind]  = useState<"fixed" | "pool">("fixed");
  const [newAmt,   setNewAmt]   = useState<number>(0);
  const [addError, setAddError] = useState<string | null>(null);
  const [adding,   setAdding]   = useState(false);

  const load = useCallback(() => {
    api.get<FixedExpenseTemplate[]>("/fixed-templates")
      .then(r => setTemplates(r.data))
      .catch(() => {});
  }, []);

  useEffect(() => { load(); }, [load]);

  const activeFixed = templates.filter(t => t.is_active && t.template_type === "fixed");
  const activePools = templates.filter(t => t.is_active && t.template_type === "pool");

  // Group fixed templates by category
  const byCat = activeFixed.reduce<Record<string, FixedExpenseTemplate[]>>((acc, t) => {
    (acc[t.category] ??= []).push(t);
    return acc;
  }, {});

  const handleDelete = async (id: number) => {
    await api.delete(`/fixed-templates/${id}`);
    setTemplates(prev => prev.filter(t => t.id !== id));
  };

  const handleAddBill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) { setAddError("Please enter a bill name."); return; }
    if (newKind === "fixed" && newAmt <= 0) {
      setAddError("Please enter the monthly amount for fixed bills.");
      return;
    }
    setAddError(null);
    setAdding(true);
    try {
      await api.post("/fixed-templates", {
        name:          newName.trim(),
        category:      newCat,
        amount:        newAmt,   // pools send 0 if unknown — backend now accepts it
        template_type: newKind,
      });
      setNewName(""); setNewAmt(0); setNewKind("fixed");
      setAddOpen(false);
      load();
    } finally {
      setAdding(false);
    }
  };

  const inputCls =
    "bg-dark-bg border border-white/10 rounded-xl px-3 py-2.5 text-white " +
    "text-sm placeholder-white/30 focus:border-accent focus:outline-none transition-colors";

  return (
    <section>
      {/* Section header */}
      <div className="mb-4">
        <h2 className="font-syne font-bold text-white">📋 Monthly Bills</h2>
        <p className="text-sm mt-0.5" style={{ color: "var(--text-sub)" }}>
          Fixed = same every month. Variable = amount changes (like electric bill).
        </p>
        <div className="border-b border-white/10 mt-3" />
      </div>

      {/* Fixed templates by category */}
      {Object.keys(byCat).length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-semibold uppercase tracking-widest mb-3"
             style={{ color: "var(--text-muted)" }}>
            Same amount every month
          </p>
          <div className="space-y-2">
            {Object.entries(byCat)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([cat, items]) => (
                <FixedTemplateCategoryGroup
                  key={cat}
                  category={cat}
                  items={items}
                  onDelete={handleDelete}
                  onSaved={load}
                />
              ))}
          </div>
        </div>
      )}

      {/* Pool templates */}
      {activePools.length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-semibold uppercase tracking-widest mb-3"
             style={{ color: "var(--text-muted)" }}>
            Amount changes each month
          </p>
          <div className="space-y-2">
            {activePools.map(t => (
              <div
                key={t.id}
                className="flex items-center justify-between bg-dark-card2
                           border border-white/10 rounded-xl px-4 py-3"
              >
                <div>
                  <span className="text-white text-sm font-medium">
                    {CATEGORY_ICONS[t.category] ?? "📦"} {t.name}
                  </span>
                  <span className="text-xs ml-2" style={{ color: "var(--text-sub)" }}>
                    {t.category} · Add payments in Fixed tab
                  </span>
                </div>
                <button
                  onClick={() => handleDelete(t.id)}
                  className="hover:text-red-400 transition-colors"
                  style={{ color: "var(--text-muted)" }}
                  aria-label="Remove"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add new bill accordion */}
      <div className="border border-white/10 rounded-2xl overflow-hidden">
        <button
          onClick={() => setAddOpen(o => !o)}
          className="w-full flex items-center justify-between px-4 py-3 text-sm
                     hover:bg-white/5 transition-colors"
          style={{ color: "var(--text-sub)" }}
        >
          <span className="flex items-center gap-2">
            <Plus size={14} /> Add a new bill
          </span>
          {addOpen
            ? <ChevronUp size={14} style={{ color: "var(--text-muted)" }} />
            : <ChevronDown size={14} style={{ color: "var(--text-muted)" }} />
          }
        </button>

        {addOpen && (
          <form
            onSubmit={handleAddBill}
            className="px-4 pb-4 space-y-3 border-t border-white/10"
          >
            <div className="grid grid-cols-2 gap-3 pt-3">
              <input
                value={newName}
                onChange={e => setNewName(e.target.value)}
                placeholder="e.g. Rent, Car Loan, Netflix"
                className={`col-span-2 ${inputCls}`}
              />
              <select
                value={newCat}
                onChange={e => setNewCat(e.target.value)}
                className={inputCls}
              >
                {FIXED_CATEGORIES.map(c => (
                  <option key={c} value={c}>{CATEGORY_ICONS[c]} {c}</option>
                ))}
              </select>
              <input
                type="number"
                min="0"
                step="100"
                value={newAmt || ""}
                onChange={e => setNewAmt(Number(e.target.value))}
                placeholder={
                  newKind === "fixed" ? "Monthly amount (₹)" : "Typical amount (₹)"
                }
                className={inputCls}
              />
            </div>

            {/* Fixed / variable radio */}
            <div>
              <p className="text-xs mb-2" style={{ color: "var(--text-muted)" }}>
                Is the amount the same every month?
              </p>
              {(["fixed", "pool"] as const).map(kind => (
                <label key={kind} className="flex items-center gap-2 mb-1.5 cursor-pointer">
                  <input
                    type="radio"
                    name="newKind"
                    value={kind}
                    checked={newKind === kind}
                    onChange={() => setNewKind(kind)}
                    className="accent-indigo-500"
                  />
                  <span className="text-white text-sm">
                    {kind === "fixed" ? "Yes, always the same" : "No, it varies"}
                  </span>
                </label>
              ))}
              {/* Caption appears instantly — key improvement over Streamlit */}
              {newKind === "pool" && (
                <p className="text-xs mt-1" style={{ color: "var(--text-sub)" }}>
                  You'll add the actual amount once it's paid.
                </p>
              )}
            </div>

            {addError && (
              <p className="text-red-400 text-xs">{addError}</p>
            )}

            <button
              type="submit"
              disabled={adding}
              className="w-full bg-gradient-to-r from-accent to-accent2 text-white
                         font-semibold py-2.5 rounded-xl text-sm disabled:opacity-50
                         transition-opacity"
            >
              {adding ? "Adding…" : "＋ Add Bill"}
            </button>
          </form>
        )}
      </div>
    </section>
  );
}
