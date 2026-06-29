import { useEffect, useState, useCallback } from "react";
import { api } from "@/api/client";
import { CATEGORY_ICONS, FIXED_CATEGORIES } from "@/utils/categories";
import type { FixedExpenseTemplate } from "@/types";
import { ChevronDown, ChevronUp, Trash2, Save, Plus, Check } from "lucide-react";
import { CurrencyInput } from "@/components/shared/CurrencyInput";
import { fmtInr } from "@/utils/formatInr";
import { suggestCategory } from "@/utils/categoryKeywords";

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
  const [name,       setName]       = useState(t.name);
  const [amt,        setAmt]        = useState(t.amount);
  const [dueDay,     setDueDay]     = useState(t.due_day ?? 0);
  const [saving,     setSaving]     = useState(false);
  const [confirmDel, setConfirmDel] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put(`/fixed-templates/${t.id}`, {
        name:    name.trim(),
        amount:  amt,
        due_day: dueDay > 0 ? dueDay : null,
      });
      // Signal FixedTab to re-fetch — backend has already synced seeded expense rows
      window.dispatchEvent(new CustomEvent("fixedTemplateUpdated"));
      onSaved();
    } finally {
      setSaving(false);
    }
  };

  const inputCls =
    "bg-dark-bg border border-white/10 rounded-lg px-2.5 py-1.5 text-white " +
    "text-xs focus:border-accent focus:outline-none transition-colors";

  return (
    // Mobile: name spans full width; amount + due-day on row 2; icons right-aligned
    // Desktop (sm+): original single flex row
    <div className="grid grid-cols-[1fr_auto] gap-x-2 gap-y-2
                    sm:flex sm:items-center sm:gap-2 px-3 py-2">
      {/* Name — full width on mobile, flex-1 on desktop */}
      <input
        value={name}
        onChange={e => setName(e.target.value)}
        className={`col-span-2 sm:flex-1 min-w-0 ${inputCls}`}
      />
      {/* Amount — col 1 on mobile */}
      <CurrencyInput
        value={amt}
        onChange={v => setAmt(v)}
        className={`${inputCls}`}
      />
      {/* Due-day — col 2 on mobile (full width in its cell), w-28 on desktop */}
      <select
        value={dueDay}
        onChange={e => setDueDay(Number(e.target.value))}
        className={`sm:w-28 ${inputCls}`}
      >
        <option value={0}>No reminder</option>
        {Array.from({ length: 28 }, (_, i) => i + 1).map(d => (
          <option key={d} value={d}>{d}th of month</option>
        ))}
      </select>
      {/* Action icons — right-aligned below on mobile, inline on desktop */}
      <div className="flex gap-1 items-center justify-end col-start-2 sm:contents">
        <button
          onClick={handleSave}
          disabled={saving}
          className="w-10 h-10 flex items-center justify-center rounded-lg
                     text-indigo-400 hover:text-indigo-200 disabled:opacity-40 transition-colors"
          aria-label="Save"
        >
          {saving ? <Check size={14} /> : <Save size={14} />}
        </button>
        {confirmDel ? (
          <div className="flex items-center gap-1.5 text-xs">
            <span style={{ color: "var(--text-sub)" }}>Remove?</span>
            <button
              onClick={() => { setConfirmDel(false); onDelete(); }}
              className="text-red-400 hover:text-red-300 font-semibold transition-colors"
            >Yes</button>
            <button
              onClick={() => setConfirmDel(false)}
              className="transition-colors"
              style={{ color: "var(--text-muted)" }}
            >No</button>
          </div>
        ) : (
          <button
            onClick={() => setConfirmDel(true)}
            className="w-10 h-10 flex items-center justify-center rounded-lg
                       hover:text-red-400 hover:bg-red-500/10 transition-colors"
            style={{ color: "var(--text-muted)" }}
            aria-label="Delete"
          >
            <Trash2 size={14} />
          </button>
        )}
      </div>
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
  const groupTotal = items.reduce((s, t) => s + t.amount, 0);

  return (
    <div className="border border-white/10 rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm
                   hover:bg-white/5 transition-colors"
      >
        <span style={{ color: "var(--text-sub)" }}>
          {icon} {category}{" "}
          <span style={{ color: "var(--text-muted)" }}>({items.length} item{items.length === 1 ? '' : 's'})</span>
          <span className="ml-2 text-xs" style={{ color: "var(--text-sub)" }}>
            · {fmtInr(groupTotal)}/mo
          </span>
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
  const [templates,     setTemplates]     = useState<FixedExpenseTemplate[]>([]);
  const [addOpen,       setAddOpen]       = useState(false);
  const [confirmPoolId, setConfirmPoolId] = useState<number | null>(null);

  // Add bill form state
  const [newName,      setNewName]      = useState("");
  const [newCat,       setNewCat]       = useState(FIXED_CATEGORIES[0]);
  const [newKind,      setNewKind]      = useState<"fixed" | "pool">("fixed");
  const [newAmt,       setNewAmt]       = useState<number>(0);
  const [addError,     setAddError]     = useState<string | null>(null);
  const [adding,       setAdding]       = useState(false);
  const [catAutoSet,   setCatAutoSet]   = useState(false);
  const [userOverrode, setUserOverrode] = useState(false);

  const load = useCallback(() => {
    api.get<FixedExpenseTemplate[]>("/fixed-templates")
      .then(r => setTemplates(r.data))
      .catch(() => {});
  }, []);

  useEffect(() => { load(); }, [load]);

  const activeFixed = templates.filter(t => t.is_active && t.template_type === "fixed");
  const activePools = templates.filter(t => t.is_active && t.template_type === "pool");
  const fixedTotal  = activeFixed.reduce((s, t) => s + t.amount, 0);

  // Group fixed templates by category
  const byCat = activeFixed.reduce<Record<string, FixedExpenseTemplate[]>>((acc, t) => {
    (acc[t.category] ??= []).push(t);
    return acc;
  }, {});

  const handleDelete = async (id: number) => {
    await api.delete(`/fixed-templates/${id}`);
    setTemplates(prev => prev.filter(t => t.id !== id));
  };

  const handleNewNameChange = (value: string) => {
    const suggested = suggestCategory(value);
    const autoSet = !!suggested && !userOverrode;
    setNewName(value);
    if (value === "") {
      setNewCat(FIXED_CATEGORIES[0]);
      setCatAutoSet(false);
      setUserOverrode(false);
    } else if (autoSet) {
      setNewCat(suggested!);
      setCatAutoSet(true);
    } else {
      setCatAutoSet(false);
    }
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
        amount:        newAmt,
        template_type: newKind,
      });
      setNewName(""); setNewAmt(0); setNewKind("fixed");
      setCatAutoSet(false); setUserOverrode(false);
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
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-syne font-bold text-white">📋 Monthly commitments</h2>
            <p className="text-sm mt-0.5" style={{ color: "var(--text-sub)" }}>
              Fixed = same every month. Variable = amount changes (like electric bill).
            </p>
          </div>
          <button
            onClick={() => setAddOpen(o => !o)}
            className="flex-shrink-0 text-xs font-semibold px-3 py-1.5 rounded-lg
                       border border-accent/40 text-indigo-300 hover:bg-accent/10
                       transition-colors"
          >
            + Add commitment
          </button>
        </div>
        <div className="border-b border-white/10 mt-3" />
      </div>

      {/* Add commitment form — shown inline right below header */}
      {addOpen && (
        <form
          onSubmit={handleAddBill}
          className="mb-4 p-4 border border-white/10 rounded-2xl space-y-3"
        >
          <div className="grid grid-cols-2 gap-3 pt-3">
            <input
              value={newName}
              onChange={e => handleNewNameChange(e.target.value)}
              placeholder="e.g. Rent, Car Loan, Netflix"
              className={`col-span-2 ${inputCls}`}
            />
            <select
              value={newCat}
              onChange={e => { setNewCat(e.target.value); setCatAutoSet(false); setUserOverrode(true); }}
              className={inputCls}
            >
              {FIXED_CATEGORIES.map(c => (
                <option key={c} value={c}>{CATEGORY_ICONS[c]} {c}</option>
              ))}
            </select>
            <CurrencyInput
              value={newAmt}
              onChange={v => setNewAmt(v)}
              placeholder={newKind === "fixed" ? "Monthly amount (₹)" : "Typical amount (₹)"}
              className={inputCls}
            />
          </div>
          {catAutoSet && (
            <p className="text-xs -mt-1" style={{ color: "var(--text-muted)" }}>
              ✨ Category suggested based on name — tap the dropdown to change
            </p>
          )}

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
            {newKind === "pool" && (
              <p className="text-xs mt-1" style={{ color: "var(--text-sub)" }}>
                You'll add the actual amount once it's paid.
              </p>
            )}
          </div>

          {addError && <p className="text-red-400 text-xs">{addError}</p>}

          <div className="flex gap-2">
            <button
              type="submit"
              disabled={adding}
              className="flex-1 bg-gradient-to-r from-accent to-accent2 text-white
                         font-semibold py-2.5 rounded-xl text-sm disabled:opacity-50
                         transition-opacity"
            >
              {adding ? "Adding…" : "＋ Add commitment"}
            </button>
            <button
              type="button"
              onClick={() => { setAddOpen(false); setNewName(""); setNewAmt(0); setNewKind("fixed"); setCatAutoSet(false); setUserOverrode(false); setNewCat(FIXED_CATEGORIES[0]); setAddError(null); }}
              className="px-4 py-2.5 rounded-xl text-sm bg-dark-card
                         text-white/50 hover:text-white transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Fixed templates by category */}
      {Object.keys(byCat).length > 0 && (
        <div className="mb-4">
          {fixedTotal > 0 && (
            <div className="flex justify-between items-center px-4 py-2 mb-3
                            bg-indigo-500/5 border border-indigo-500/15 rounded-xl">
              <span className="text-xs font-semibold uppercase tracking-widest"
                    style={{ color: "var(--text-sub)" }}>
                Fixed total
              </span>
              <span className="font-syne font-bold text-indigo-300 text-sm">
                {fmtInr(fixedTotal)}/mo
              </span>
            </div>
          )}
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
                {confirmPoolId === t.id ? (
                  <div className="flex items-center gap-1.5 text-xs">
                    <span style={{ color: "var(--text-sub)" }}>Remove?</span>
                    <button
                      onClick={() => { handleDelete(t.id); setConfirmPoolId(null); }}
                      className="text-red-400 hover:text-red-300 font-semibold transition-colors"
                    >Yes</button>
                    <button
                      onClick={() => setConfirmPoolId(null)}
                      className="transition-colors"
                      style={{ color: "var(--text-muted)" }}
                    >No</button>
                  </div>
                ) : (
                  <button
                    onClick={() => setConfirmPoolId(t.id)}
                    className="w-10 h-10 flex items-center justify-center rounded-lg
                               hover:text-red-400 hover:bg-red-500/10 transition-colors"
                    style={{ color: "var(--text-muted)" }}
                    aria-label="Remove"
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

    </section>
  );
}
