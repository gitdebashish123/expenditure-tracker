import { useEffect, useState, useCallback } from "react";
import { api } from "@/api/client";
import { CATEGORY_ICONS, VAR_CATEGORIES } from "@/utils/categories";
import type { ExpenseTemplate } from "@/types";
import { Trash2, Save, Plus } from "lucide-react";
import { CurrencyInput } from "@/components/shared/CurrencyInput";
import { fmtInr } from "@/utils/formatInr";

// ── ShortcutEditRow — inline edit for a single shortcut ──────────────────────

function ShortcutEditRow({
  template: t,
  onDelete,
  onSave,
}: {
  template: ExpenseTemplate;
  onDelete: () => void;
  onSave:   (updates: Partial<ExpenseTemplate>) => void;
}) {
  const [name, setName] = useState(t.name);
  const [amt,  setAmt]  = useState(t.amount);
  const [cat,  setCat]  = useState(t.category);
  const [confirmDel, setConfirmDel] = useState(false);

  const inputCls =
    "bg-dark-card2 border border-white/10 rounded-lg px-2.5 py-1.5 text-white " +
    "text-xs focus:border-accent focus:outline-none transition-colors";

  return (
    <div className="flex items-center gap-2 py-2 border-b border-white/5">
      <input
        value={name}
        onChange={e => setName(e.target.value)}
        className={`flex-1 ${inputCls}`}
      />
      <select
        value={cat}
        onChange={e => setCat(e.target.value)}
        className={`w-28 ${inputCls}`}
      >
        {VAR_CATEGORIES.map(c => (
          <option key={c} value={c}>{CATEGORY_ICONS[c]} {c}</option>
        ))}
      </select>
      <CurrencyInput
        value={amt}
        onChange={v => setAmt(v)}
        className={`w-20 ${inputCls}`}
      />
      <button
        onClick={() => onSave({ name, category: cat, amount: amt, vendor: name })}
        className="w-10 h-10 flex items-center justify-center rounded-lg
                   text-indigo-400 hover:text-indigo-200 transition-colors"
        aria-label="Save"
      >
        <Save size={14} />
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
  );
}

// ── ShortcutsSection — main exported component ───────────────────────────────

export function ShortcutsSection() {
  const [shortcuts, setShortcuts] = useState<ExpenseTemplate[]>([]);
  const [newName,   setNewName]   = useState("");
  const [newAmt,    setNewAmt]    = useState<number>(0);
  const [newCat,    setNewCat]    = useState(VAR_CATEGORIES[0]);
  const [adding,    setAdding]    = useState(false);
  const [addOpen,   setAddOpen]   = useState(false);
  const [viewAll,   setViewAll]   = useState(false);

  const load = useCallback(() => {
    api.get<ExpenseTemplate[]>("/expense-templates")
      .then(r => setShortcuts(r.data))
      .catch(() => {});
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim() || newAmt <= 0) return;
    setAdding(true);
    try {
      await api.post("/expense-templates", {
        name:     newName.trim(),
        vendor:   newName.trim(),
        category: newCat,
        amount:   newAmt,
      });
      setNewName(""); setNewAmt(0);
      setAddOpen(false);
      load();
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (id: number) => {
    await api.delete(`/expense-templates/${id}`);
    setShortcuts(prev => prev.filter(s => s.id !== id));
  };

  const handleSave = async (t: ExpenseTemplate, updates: Partial<ExpenseTemplate>) => {
    await api.put(`/expense-templates/${t.id}`, updates);
    setShortcuts(prev => prev.map(s => s.id === t.id ? { ...s, ...updates } : s));
  };

  const inputCls =
    "bg-dark-card2 border border-white/10 rounded-xl px-3 py-2.5 text-white " +
    "text-sm placeholder-white/30 focus:border-accent focus:outline-none transition-colors";

  return (
    <section>
      {/* Section header */}
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-syne font-bold text-white">⚡ Saved Shortcuts</h2>
            <p className="text-sm mt-0.5" style={{ color: "var(--text-sub)" }}>
              Expenses you log frequently. Appear as chips in Today tab.
            </p>
          </div>
          <button
            onClick={() => setAddOpen(o => !o)}
            className="flex-shrink-0 text-xs font-semibold px-3 py-1.5 rounded-lg
                       border border-accent/40 text-indigo-300 hover:bg-accent/10
                       transition-colors"
          >
            + Add shortcut
          </button>
        </div>
        <div className="border-b border-white/10 mt-3" />
      </div>

      {/* Empty state */}
      {shortcuts.length === 0 && (
        <p className="text-sm mb-4" style={{ color: "var(--text-muted)" }}>
          No shortcuts yet. Add one with the button above.
        </p>
      )}

      {/* Horizontally-scrollable icon tiles */}
      {shortcuts.length > 0 && (
        <div className="flex gap-3 overflow-x-auto pb-2 mb-3" style={{ scrollbarWidth: "none" }}>
          {shortcuts.map(t => (
            <button
              key={t.id}
              onClick={() => setViewAll(true)}
              className="flex-shrink-0 flex flex-col items-center gap-1
                         bg-dark-card2 border border-white/10 rounded-xl px-4 py-3
                         min-w-[80px] hover:bg-white/5 transition-colors"
            >
              <span className="text-xl">{CATEGORY_ICONS[t.category] ?? "📦"}</span>
              <span className="text-xs text-white font-medium truncate max-w-[72px]">{t.name}</span>
              <span className="text-xs" style={{ color: "var(--text-sub)" }}>
                {fmtInr(t.amount)}
              </span>
            </button>
          ))}
          {/* Dashed "+" add tile */}
          <button
            onClick={() => setAddOpen(true)}
            className="flex-shrink-0 flex flex-col items-center justify-center
                       border-2 border-dashed border-white/20 rounded-xl px-4 py-3
                       min-w-[64px] min-h-[80px] hover:border-accent/40
                       hover:text-indigo-300 transition-colors"
            style={{ color: "var(--text-muted)" }}
            aria-label="Add shortcut"
          >
            <Plus size={18} />
          </button>
        </div>
      )}

      {/* View all toggle link */}
      {shortcuts.length > 0 && !viewAll && (
        <button
          onClick={() => setViewAll(true)}
          className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors mb-3"
        >
          View all shortcuts →
        </button>
      )}

      {/* Expanded edit list */}
      {viewAll && (
        <div className="mt-1 border-t border-white/10 pt-3 mb-3">
          {shortcuts.map(t => (
            <ShortcutEditRow
              key={t.id}
              template={t}
              onDelete={() => handleDelete(t.id)}
              onSave={updates => handleSave(t, updates)}
            />
          ))}
          <button
            onClick={() => setViewAll(false)}
            className="mt-3 text-xs transition-colors"
            style={{ color: "var(--text-muted)" }}
          >
            ▲ Hide
          </button>
        </div>
      )}

      {/* Add shortcut form (revealed by "+ Add shortcut" or dashed tile) */}
      {addOpen && (
        <form onSubmit={handleAdd} className="mt-3 grid grid-cols-3 gap-2">
          <input
            value={newName}
            onChange={e => setNewName(e.target.value)}
            placeholder="e.g. Petrol, Cook"
            className={inputCls}
            autoFocus
          />
          <CurrencyInput
            value={newAmt}
            onChange={v => setNewAmt(v)}
            placeholder="Amount (₹)"
            className={inputCls}
          />
          <select
            value={newCat}
            onChange={e => setNewCat(e.target.value)}
            className={inputCls}
          >
            {VAR_CATEGORIES.map(c => (
              <option key={c} value={c}>{CATEGORY_ICONS[c]} {c}</option>
            ))}
          </select>
          <button
            type="submit"
            disabled={adding || !newName.trim() || newAmt <= 0}
            className="col-span-2 flex items-center justify-center gap-2
                       bg-dark-card border border-white/10 hover:bg-white/5
                       py-2.5 rounded-xl text-sm disabled:opacity-40 transition-colors"
            style={{ color: "var(--text-sub)" }}
          >
            <Plus size={14} />
            {adding ? "Adding…" : "Add Shortcut"}
          </button>
          <button
            type="button"
            onClick={() => setAddOpen(false)}
            className="flex items-center justify-center py-2.5 rounded-xl text-sm
                       bg-dark-card border border-white/10 hover:bg-white/5 transition-colors"
            style={{ color: "var(--text-muted)" }}
          >
            Cancel
          </button>
        </form>
      )}
    </section>
  );
}
