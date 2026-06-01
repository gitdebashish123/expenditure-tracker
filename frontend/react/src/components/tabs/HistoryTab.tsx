import { useEffect, useState, useCallback, useMemo } from "react";
import { api } from "@/api/client";
import { useMonth } from "@/context/MonthContext";
import { fmtInr } from "@/utils/formatInr";
import { fmtDate } from "@/utils/formatDate";
import { CATEGORY_ICONS, VAR_CATEGORIES } from "@/utils/categories";
import type { Expense } from "@/types";
import { Pencil, Trash2, Check, X, Search } from "lucide-react";

/**
 * HistoryTab — full transaction ledger for the selected month
 *
 * Streamlit ref: with tab4: in frontend/app.py
 *
 * Features:
 *   - Search bar (bonus — not in Streamlit, no full-rerun needed in React)
 *   - "Include Fixed" toggle
 *   - "Bulk Select" toggle + bulk delete
 *   - Date-grouped list, descending, with daily totals
 *   - Sticky date headers on scroll
 *   - Inline edit form (replaces row, saves in-place)
 *   - Delete per row
 *
 * Key improvements over Streamlit:
 *   - Sticky date headers (Streamlit renders flat list)
 *   - Edit slides in without full page rerun
 *   - Bulk select via checkboxes (no key collision issues)
 *   - Search filter works instantly on every keystroke
 */

// ── Sub-component: normal expense row ────────────────────────────────────────

interface HistoryRowProps {
  expense:        Expense;
  bulkMode:       boolean;
  selected:       boolean;
  onToggleSelect: () => void;
  onEdit:         () => void;
  onDelete:       () => void;
}

function ExpenseHistoryRow({
  expense, bulkMode, selected, onToggleSelect, onEdit, onDelete,
}: HistoryRowProps) {
  const icon = CATEGORY_ICONS[expense.category] ?? "📦";

  return (
    <div
      className={`flex items-center gap-3 px-2 py-2.5 rounded-xl border-b border-white/5
                  transition-colors ${selected ? "bg-indigo-500/10" : ""}`}
    >
      {/* Bulk select checkbox — only for variable expenses */}
      {bulkMode && !expense.is_fixed && (
        <input
          type="checkbox"
          checked={selected}
          onChange={onToggleSelect}
          className="accent-indigo-500 w-4 h-4 flex-shrink-0 cursor-pointer"
        />
      )}

      {/* Category icon */}
      <div className="w-9 h-9 bg-dark-card2 rounded-xl flex items-center justify-center
                      text-lg flex-shrink-0">
        {icon}
      </div>

      {/* Vendor + category */}
      <div className="flex-1 min-w-0">
        <p className="text-white text-sm font-medium truncate">
          {expense.vendor}
          {expense.note && (
            <span className="ml-2 text-xs" style={{ color: "var(--text-muted)" }}>
              · {expense.note}
            </span>
          )}
        </p>
        <p className="text-xs" style={{ color: "var(--text-sub)" }}>
          {expense.category}
          {expense.is_fixed && (
            <span className="ml-2" style={{ color: "var(--text-muted)" }}>
              · Fixed
            </span>
          )}
        </p>
      </div>

      {/* Amount */}
      <span className="font-syne font-semibold text-red-400 text-sm flex-shrink-0">
        -{fmtInr(expense.amount)}
      </span>

      {/* Edit + Delete — hidden in bulk mode and for fixed expenses */}
      {!bulkMode && !expense.is_fixed && (
        <div className="flex items-center gap-1 flex-shrink-0">
          <button
            onClick={onEdit}
            className="w-7 h-7 flex items-center justify-center rounded-lg
                       hover:text-indigo-400 hover:bg-indigo-500/10 transition-colors"
            style={{ color: "var(--text-muted)" }}
            aria-label={`Edit ${expense.vendor}`}
          >
            <Pencil size={12} />
          </button>
          <button
            onClick={onDelete}
            className="w-7 h-7 flex items-center justify-center rounded-lg
                       hover:text-red-400 hover:bg-red-500/10 transition-colors"
            style={{ color: "var(--text-muted)" }}
            aria-label={`Delete ${expense.vendor}`}
          >
            <Trash2 size={12} />
          </button>
        </div>
      )}
    </div>
  );
}

// ── Sub-component: inline edit form ──────────────────────────────────────────

interface EditProps {
  expense:  Expense;
  onSave:   (updates: Partial<Expense>) => Promise<void>;
  onCancel: () => void;
}

function EditExpenseRow({ expense, onSave, onCancel }: EditProps) {
  const [vendor,   setVendor]   = useState(expense.vendor);
  const [amount,   setAmount]   = useState(expense.amount);
  const [category, setCategory] = useState(expense.category);
  const [note,     setNote]     = useState(expense.note ?? "");
  const [saving,   setSaving]   = useState(false);

  const handleSave = async () => {
    if (!vendor.trim() || amount <= 0) return;
    setSaving(true);
    await onSave({ vendor: vendor.trim(), amount, category, note: note.trim() || null });
    setSaving(false);
  };

  const inputCls =
    "bg-dark-bg border border-white/10 rounded-xl px-3 py-2 text-white text-sm " +
    "focus:border-accent focus:outline-none transition-colors";

  return (
    <div className="bg-dark-card2 border border-indigo-500/30 rounded-2xl p-4 space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <input
          value={vendor}
          onChange={e => setVendor(e.target.value)}
          placeholder="Vendor"
          className={inputCls}
        />
        <select
          value={category}
          onChange={e => setCategory(e.target.value)}
          className={inputCls}
        >
          {VAR_CATEGORIES.map(c => (
            <option key={c} value={c}>
              {CATEGORY_ICONS[c]} {c}
            </option>
          ))}
        </select>
        <input
          type="number"
          min="0"
          step="10"
          value={amount}
          onChange={e => setAmount(Number(e.target.value))}
          placeholder="Amount (₹)"
          className={inputCls}
        />
        <input
          value={note}
          onChange={e => setNote(e.target.value)}
          placeholder="Note (optional)"
          className={inputCls}
        />
      </div>
      <div className="flex gap-2">
        <button
          onClick={handleSave}
          disabled={saving || !vendor.trim() || amount <= 0}
          className="flex-1 flex items-center justify-center gap-1.5
                     bg-indigo-600 hover:bg-indigo-500 text-white py-2
                     rounded-xl text-sm font-semibold disabled:opacity-50 transition-colors"
        >
          <Check size={14} />
          {saving ? "Saving…" : "Save"}
        </button>
        <button
          onClick={onCancel}
          className="flex-1 flex items-center justify-center gap-1.5
                     bg-dark-card text-white/60 hover:text-white py-2
                     rounded-xl text-sm transition-colors"
        >
          <X size={14} />
          Cancel
        </button>
      </div>
    </div>
  );
}

// ── Sub-component: loading skeleton ──────────────────────────────────────────

function HistorySkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-10 bg-white/5 rounded-xl" />
      {[1, 2, 3, 4, 5].map(i => (
        <div key={i} className="flex items-center gap-3 py-3 border-b border-white/5">
          <div className="w-9 h-9 bg-white/10 rounded-xl flex-shrink-0" />
          <div className="flex-1 space-y-1.5">
            <div className="h-3.5 bg-white/10 rounded w-2/3" />
            <div className="h-3 bg-white/5 rounded w-1/3" />
          </div>
          <div className="w-16 h-4 bg-white/10 rounded" />
        </div>
      ))}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function HistoryTab() {
  const { selMonth } = useMonth();

  const [expenses,     setExpenses]     = useState<Expense[]>([]);
  const [loading,      setLoading]      = useState(true);
  const [showFixed,    setShowFixed]    = useState(false);
  const [bulkMode,     setBulkMode]     = useState(false);
  const [selected,     setSelected]     = useState<Set<number>>(new Set());
  const [editingId,    setEditingId]    = useState<number | null>(null);
  const [searchQuery,  setSearchQuery]  = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get<Expense[]>(`/expenses/${selMonth}`);
      setExpenses(data);
    } finally {
      setLoading(false);
    }
  }, [selMonth]);

  // Reset selection + edit state when month changes
  useEffect(() => {
    load();
    setSelected(new Set());
    setEditingId(null);
    setSearchQuery("");
  }, [load]);

  // ── Derived: filtered + sorted list ──────────────────────────────────────
  const filtered = useMemo(() => {
    let list = showFixed ? expenses : expenses.filter(e => !e.is_fixed);
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(e =>
        e.vendor.toLowerCase().includes(q) ||
        e.category.toLowerCase().includes(q) ||
        (e.note?.toLowerCase().includes(q) ?? false)
      );
    }
    // Sort descending by date
    return [...list].sort((a, b) => b.date.localeCompare(a.date));
  }, [expenses, showFixed, searchQuery]);

  // ── Derived: grouped by date ──────────────────────────────────────────────
  const grouped = useMemo(() => {
    const map = new Map<string, Expense[]>();
    for (const e of filtered) {
      const d = e.date.slice(0, 10);
      if (!map.has(d)) map.set(d, []);
      map.get(d)!.push(e);
    }
    return [...map.entries()];
  }, [filtered]);

  const totalShown = filtered.reduce((s, e) => s + e.amount, 0);

  // ── Handlers ─────────────────────────────────────────────────────────────

  const handleDelete = async (id: number) => {
    // Optimistic remove
    setExpenses(prev => prev.filter(e => e.id !== id));
    try {
      await api.delete(`/expenses/${id}`);
    } catch {
      load(); // restore on failure
    }
  };

  const handleBulkDelete = async () => {
    if (selected.size === 0) return;
    const ids = [...selected];
    // Optimistic remove
    setExpenses(prev => prev.filter(e => !selected.has(e.id)));
    setSelected(new Set());
    setBulkMode(false);
    try {
      await api.post("/expenses/bulk-delete", { ids });
    } catch {
      load(); // restore on failure
    }
  };

  const toggleSelect = (id: number) => {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const handleSaveEdit = async (id: number, updates: Partial<Expense>) => {
    await api.patch(`/expenses/${id}`, updates);
    setExpenses(prev =>
      prev.map(e => e.id === id ? { ...e, ...updates } : e)
    );
    setEditingId(null);
  };

  // ── Render ────────────────────────────────────────────────────────────────

  if (loading) return <HistorySkeleton />;

  return (
    <div className="space-y-4">

      {/* ── Controls ──────────────────────────────────────── */}
      <div className="space-y-2">

        {/* Search bar — bonus feature not in Streamlit */}
        <div className="relative">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2"
            style={{ color: "var(--text-muted)" }}
          />
          <input
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search vendor, category, note…"
            className="w-full bg-dark-card2 border border-white/10 rounded-xl
                       pl-9 pr-4 py-2.5 text-white text-sm placeholder-white/30
                       focus:border-accent focus:outline-none"
          />
        </div>

        {/* Toggle row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <label
              className="flex items-center gap-2 text-sm cursor-pointer"
              style={{ color: "var(--text-sub)" }}
            >
              <input
                type="checkbox"
                checked={showFixed}
                onChange={e => setShowFixed(e.target.checked)}
                className="accent-indigo-500 w-4 h-4"
              />
              Include Fixed
            </label>
            <label
              className="flex items-center gap-2 text-sm cursor-pointer"
              style={{ color: "var(--text-sub)" }}
            >
              <input
                type="checkbox"
                checked={bulkMode}
                onChange={e => {
                  setBulkMode(e.target.checked);
                  setSelected(new Set());
                }}
                className="accent-indigo-500 w-4 h-4"
              />
              Bulk Select
            </label>
          </div>
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            {filtered.length} · {fmtInr(totalShown)}
          </span>
        </div>
      </div>

      {/* ── Bulk delete action bar ────────────────────────── */}
      {bulkMode && selected.size > 0 && (
        <div className="flex items-center justify-between
                        bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3">
          <span className="text-red-300 text-sm">{selected.size} selected</span>
          <button
            onClick={handleBulkDelete}
            className="flex items-center gap-1.5 text-red-300 hover:text-red-100
                       text-sm font-semibold transition-colors"
          >
            <Trash2 size={14} /> Delete selected
          </button>
        </div>
      )}

      {/* ── Expense list ─────────────────────────────────── */}
      {grouped.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-4xl mb-3">📋</div>
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>
            {searchQuery
              ? "No matches found."
              : "No transactions this month."}
          </p>
          {!searchQuery && (
            <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
              Log expenses in the{" "}
              <span className="text-indigo-400">Today</span> tab.
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-5">
          {grouped.map(([date, items]) => {
            const dayTotal = items.reduce((s, e) => s + e.amount, 0);
            return (
              <div key={date}>
                {/* Sticky date header */}
                <div
                  className="flex justify-between items-center mb-2 sticky
                             py-1 z-10 backdrop-blur-sm"
                  style={{
                    top:             "0",
                    backgroundColor: "var(--bg)",
                  }}
                >
                  <span className="text-xs font-semibold"
                        style={{ color: "var(--text-sub)" }}>
                    {fmtDate(date)}
                  </span>
                  <span className="text-xs"
                        style={{ color: "var(--text-sub)" }}>
                    {fmtInr(dayTotal)}
                  </span>
                </div>

                {/* Rows for this date */}
                <div className="space-y-0">
                  {items.map(expense =>
                    editingId === expense.id ? (
                      <EditExpenseRow
                        key={expense.id}
                        expense={expense}
                        onSave={updates => handleSaveEdit(expense.id, updates)}
                        onCancel={() => setEditingId(null)}
                      />
                    ) : (
                      <ExpenseHistoryRow
                        key={expense.id}
                        expense={expense}
                        bulkMode={bulkMode}
                        selected={selected.has(expense.id)}
                        onToggleSelect={() => toggleSelect(expense.id)}
                        onEdit={() => setEditingId(expense.id)}
                        onDelete={() => handleDelete(expense.id)}
                      />
                    )
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}
