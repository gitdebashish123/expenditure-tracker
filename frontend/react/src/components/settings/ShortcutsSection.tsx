import { useEffect, useState, useCallback } from "react";
import { api } from "@/api/client";
import { CATEGORY_ICONS, VAR_CATEGORIES } from "@/utils/categories";
import type { ExpenseTemplate } from "@/types";
import { Trash2, Save, Plus } from "lucide-react";

/**
 * ShortcutsSection — quick-add favourite expense templates
 *
 * Streamlit ref: settings_section("⚡", "Saved Shortcuts", ...) in with tab5:
 * Templates appear as chips in QuickAddTab (tap to log instantly).
 *
 * Features:
 *   - Inline edit: name, category, amount per row
 *   - Delete shortcut
 *   - Add new shortcut form (3-col grid)
 */

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
      <input
        type="number"
        min="0"
        step="50"
        value={amt}
        onChange={e => setAmt(Number(e.target.value))}
        className={`w-20 ${inputCls}`}
      />
      <button
        onClick={() => onSave({ name, category: cat, amount: amt, vendor: name })}
        className="text-indigo-400 hover:text-indigo-200 transition-colors"
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

// ── ShortcutsSection — main exported component ───────────────────────────────

export function ShortcutsSection() {
  const [shortcuts, setShortcuts] = useState<ExpenseTemplate[]>([]);
  const [newName,   setNewName]   = useState("");
  const [newAmt,    setNewAmt]    = useState<number>(0);
  const [newCat,    setNewCat]    = useState(VAR_CATEGORIES[0]);
  const [adding,    setAdding]    = useState(false);

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
        <h2 className="font-syne font-bold text-white">⚡ Saved Shortcuts</h2>
        <p className="text-sm mt-0.5" style={{ color: "var(--text-sub)" }}>
          Expenses you log frequently. Appear as chips in Today tab.
        </p>
        <div className="border-b border-white/10 mt-3" />
      </div>

      {shortcuts.length === 0 && (
        <p className="text-sm mb-4" style={{ color: "var(--text-muted)" }}>
          No shortcuts yet. Add one below.
        </p>
      )}

      {/* Existing shortcuts */}
      {shortcuts.map(t => (
        <ShortcutEditRow
          key={t.id}
          template={t}
          onDelete={() => handleDelete(t.id)}
          onSave={updates => handleSave(t, updates)}
        />
      ))}

      {shortcuts.length > 0 && (
        <p className="text-xs mt-1 mb-4" style={{ color: "var(--text-muted)" }}>
          {shortcuts.length} shortcut(s) · sorted by most used
        </p>
      )}

      {/* Add shortcut form */}
      <form onSubmit={handleAdd} className="grid grid-cols-3 gap-2">
        <input
          value={newName}
          onChange={e => setNewName(e.target.value)}
          placeholder="e.g. Petrol, Cook"
          className={inputCls}
        />
        <input
          type="number"
          min="0"
          step="50"
          value={newAmt || ""}
          onChange={e => setNewAmt(Number(e.target.value))}
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
          className="col-span-3 flex items-center justify-center gap-2
                     bg-dark-card border border-white/10 hover:bg-white/5
                     py-2.5 rounded-xl text-sm disabled:opacity-40 transition-colors"
          style={{ color: "var(--text-sub)" }}
        >
          <Plus size={14} />
          {adding ? "Adding…" : "Add Shortcut"}
        </button>
      </form>
    </section>
  );
}
