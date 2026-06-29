import { useState } from "react";
import { api } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import { FIXED_CATEGORIES, VAR_CATEGORIES, CATEGORY_ICONS } from "@/utils/categories";
import { suggestCategory } from "@/utils/categoryKeywords";
import { fmtInr } from "@/utils/formatInr";
import { CurrencyInput } from "@/components/shared/CurrencyInput";

/**
 * OnboardingWizard — 3-step first-time setup overlay
 *
 * Streamlit ref: show_onboarding_wizard() in frontend/app.py
 * Shown when user.onboarding_complete === false (new users only).
 *
 * Key improvements over Streamlit:
 * - Smooth animated step progress bar (no full page rerun between steps)
 * - Bill list updates live after each "Add Bill" click without overlay re-mount
 * - "No, it varies" caption appears instantly on radio change
 * - All three steps are stateful — back-navigation preserves entered data
 *
 * Steps:
 *   1. Monthly income (source + amount + note)
 *   2. Monthly bills (name, category, fixed/variable, amount) — repeatable
 *   3. Spending caps (per VAR_CATEGORY budget limits)
 *
 * Completion: POST /auth/complete-onboarding → refreshUser() → overlay dismisses
 */

interface AddedBill {
  name: string;
  category: string;
  amount: number;
  type: "fixed" | "pool";
}

const DEFAULT_CAPS: Record<string, number> = {
  Food: 5000,
  Groceries: 8000,
  Travel: 3000,
  Shopping: 3000,
  Entertainment: 2000,
  Medical: 2000,
};

export function OnboardingWizard() {
  const { refreshUser } = useAuth();

  const [step, setStep]       = useState(1);
  const [loading, setLoading] = useState(false);

  // Step 1 state — income
  const [incomeAmt, setIncomeAmt]   = useState<number>(0);
  const [incomeNote, setIncomeNote] = useState("");

  // Step 2 state — bills
  const [billName, setBillName]   = useState("");
  const [billCat, setBillCat]     = useState(FIXED_CATEGORIES[0]);
  const [billKind, setBillKind]   = useState<"fixed" | "pool">("fixed");
  const [billAmt, setBillAmt]     = useState<number>(0);
  const [billErr, setBillErr]     = useState<string | null>(null);
  const [addedBills, setAddedBills] = useState<AddedBill[]>([]);
  const [billCatAutoSet,      setBillCatAutoSet]      = useState(false);
  const [billCatUserOverrode, setBillCatUserOverrode] = useState(false);

  // Step 3 state — spending caps
  const [caps, setCaps] = useState<Record<string, string>>(
    Object.fromEntries(Object.entries(DEFAULT_CAPS).map(([k, v]) => [k, String(v)]))
  );

  // ── Actions ──────────────────────────────────────────────────────────────

  const complete = async () => {
    setLoading(true);
    try {
      await api.post("/auth/complete-onboarding");
      await refreshUser(); // sets user.onboarding_complete = true → wizard unmounts
    } finally {
      setLoading(false);
    }
  };

  const saveIncome = async (skip = false) => {
    if (!skip && incomeAmt > 0) {
      await api.post("/income", {
        source: "Salary",
        amount: incomeAmt,
        note: incomeNote.trim() || null,
      });
    }
    setStep(2);
  };

  const addBill = async () => {
    setBillErr(null);
    if (!billName.trim()) {
      setBillErr("Please enter a bill name.");
      return;
    }
    if (billKind === "fixed" && billAmt <= 0) {
      setBillErr("Please enter the monthly amount for fixed bills.");
      return;
    }
    await api.post("/fixed-templates", {
      name:          billName.trim(),
      category:      billCat,
      amount:        billAmt,   // 0 is valid for pool templates
      template_type: billKind,
    });
    setAddedBills((prev) => [
      ...prev,
      { name: billName.trim(), category: billCat, amount: billAmt, type: billKind },
    ]);
    // Reset bill form for next entry
    setBillName("");
    setBillAmt(0);
    setBillKind("fixed");
    setBillCat(FIXED_CATEGORIES[0]);
    setBillCatAutoSet(false);
    setBillCatUserOverrode(false);
  };

  const saveCaps = async (skip = false) => {
    if (!skip) {
      await Promise.all(
        Object.entries(caps)
          .filter(([, raw]) => Number(raw) > 0)
          .map(([category, raw]) =>
            api.put("/budget", { category, limit_amount: Number(raw) })
          )
      );
    }
    await complete();
  };

  // ── UI helpers ────────────────────────────────────────────────────────────

  const ALL_BILL_CATEGORIES = [...FIXED_CATEGORIES, ...VAR_CATEGORIES];

  const inputCls =
    "w-full bg-dark-card2 border border-white/10 rounded-xl px-4 py-3 text-white " +
    "placeholder-white/30 focus:border-accent focus:outline-none text-sm";

  const btnPrimary =
    "flex-1 bg-gradient-to-r from-accent to-accent2 text-white " +
    "font-syne font-semibold py-3 rounded-xl disabled:opacity-50 text-sm";

  const btnSecondary =
    "flex-1 bg-dark-card2 text-white/60 font-semibold py-3 rounded-xl text-sm";

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="fixed inset-0 bg-dark-bg z-50 overflow-y-auto">
      <div className="min-h-full flex items-start justify-center py-10 px-4">
        <div className="w-full max-w-md">

          {/* Header */}
          <div className="text-center mb-6">
            <div className="text-4xl mb-3">🚀</div>
            <h2 className="font-syne text-xl font-bold text-white tracking-tight">
              Welcome to Wallet Mantra!
            </h2>
            <p className="text-white/40 text-sm mt-1">
              Let's set up your account in 3 quick steps.
            </p>
          </div>

          {/* Progress bar — 3 segments, fills as steps complete */}
          <div className="flex gap-2 mb-8">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className="flex-1 h-1 rounded-full transition-all duration-500"
                style={{
                  background:
                    s < step
                      ? "#6366f1"          // completed — solid accent
                      : s === step
                      ? "#8b5cf6"          // current — lighter accent
                      : "rgba(255,255,255,0.1)", // future — muted
                }}
              />
            ))}
          </div>

          {/* ── Step 1: Income ─────────────────────────────── */}
          {step === 1 && (
            <div className="space-y-4">
              <div>
                <h3 className="font-syne font-semibold text-white mb-1">
                  💰 Step 1 of 3 — Your Monthly Take-home
                </h3>
                <p className="text-white/50 text-sm">
                  What's your salary or take-home income this month?
                </p>
              </div>

              <CurrencyInput
                value={incomeAmt}
                onChange={v => setIncomeAmt(v)}
                placeholder="Amount (₹)"
                className={inputCls}
              />
              <input
                value={incomeNote}
                onChange={(e) => setIncomeNote(e.target.value)}
                placeholder="Note (optional, e.g. June salary)"
                className={inputCls}
              />

              <div className="flex gap-3">
                <button onClick={() => saveIncome(false)} className={btnPrimary}>
                  Save & Continue
                </button>
                <button onClick={() => saveIncome(true)} className={btnSecondary}>
                  Skip
                </button>
              </div>
            </div>
          )}

          {/* ── Step 2: Bills ──────────────────────────────── */}
          {step === 2 && (
            <div className="space-y-4">
              <div>
                <h3 className="font-syne font-semibold text-white mb-1">
                  📋 Step 2 of 3 — Your Monthly commitments
                </h3>
                <p className="text-white/50 text-sm">
                  Add rent, EMI, subscriptions. You can add more later in Settings.
                </p>
              </div>

              {/* Live bill list — updates after each Add Bill click */}
              {addedBills.length > 0 && (
                <div className="bg-dark-card2 rounded-xl p-3 border border-white/10 space-y-2">
                  <p className="text-white/40 text-xs font-medium">
                    {addedBills.length} commitment{addedBills.length === 1 ? '' : 's'} added
                  </p>
                  {addedBills.map((b, i) => (
                    <div key={i} className="flex justify-between items-center text-sm">
                      <span className="text-white">
                        {CATEGORY_ICONS[b.category] ?? "📦"} {b.name}
                      </span>
                      <span className="text-white/40">
                        {b.type === "pool" ? "variable" : fmtInr(b.amount)}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Bill form */}
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <input
                    value={billName}
                    onChange={(e) => {
                      const val = e.target.value;
                      setBillName(val);
                      if (!val) {
                        setBillCat(FIXED_CATEGORIES[0]);
                        setBillCatAutoSet(false);
                        setBillCatUserOverrode(false);
                        return;
                      }
                      if (!billCatUserOverrode) {
                        const suggested = suggestCategory(val);
                        if (suggested) {
                          setBillCat(suggested);
                          setBillCatAutoSet(true);
                        } else {
                          setBillCatAutoSet(false);
                        }
                      }
                    }}
                    placeholder="e.g. Rent, Car Loan, Netflix"
                    className={`col-span-2 ${inputCls}`}
                  />
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-white/60 text-xs">Category</span>
                      {billCatAutoSet && (
                        <span style={{ fontSize: 10, opacity: 0.55 }}>✨ suggested</span>
                      )}
                    </div>
                    <select
                      value={billCat}
                      onChange={(e) => {
                        setBillCat(e.target.value);
                        setBillCatAutoSet(false);
                        setBillCatUserOverrode(true);
                      }}
                      className="w-full bg-dark-card2 border border-white/10 rounded-xl px-3 py-3
                                 text-white text-sm focus:border-accent focus:outline-none"
                    >
                      {ALL_BILL_CATEGORIES.map((c) => (
                        <option key={c} value={c}>
                          {CATEGORY_ICONS[c]} {c}
                        </option>
                      ))}
                    </select>
                  </div>
                  <CurrencyInput
                    value={billAmt}
                    onChange={v => setBillAmt(v)}
                    placeholder={
                      billKind === "fixed" ? "Amount (₹)" : "Typical amount (optional)"
                    }
                    className="bg-dark-card2 border border-white/10 rounded-xl px-3 py-3
                               text-white text-sm placeholder-white/30 focus:border-accent focus:outline-none"
                  />
                </div>

                {/* Fixed / Variable radio */}
                <div>
                  <p className="text-white/60 text-sm mb-2">
                    Is the amount the same every month?
                  </p>
                  <div className="space-y-2">
                    {(["fixed", "pool"] as const).map((kind) => (
                      <label key={kind} className="flex items-center gap-3 cursor-pointer">
                        <input
                          type="radio"
                          name="billKind"
                          value={kind}
                          checked={billKind === kind}
                          onChange={() => setBillKind(kind)}
                          className="accent-indigo-500 w-4 h-4"
                        />
                        <span className="text-white text-sm">
                          {kind === "fixed" ? "Yes, always the same" : "No, it varies"}
                        </span>
                      </label>
                    ))}
                  </div>
                  {/* Caption appears instantly on radio change — key improvement over Streamlit */}
                  {billKind === "pool" && (
                    <p className="text-white/40 text-xs mt-2">
                      You'll add the actual amount once it's paid.
                    </p>
                  )}
                </div>

                {billErr && (
                  <p className="text-red-400 text-sm">{billErr}</p>
                )}
              </div>

              <div className="flex gap-2">
                <button
                  onClick={addBill}
                  className="flex-1 bg-dark-card2 border border-white/10 text-white
                             py-3 rounded-xl text-sm font-medium hover:bg-white/5 transition-colors"
                >
                  ＋ Add commitment
                </button>
                <button
                  onClick={() => setStep(3)}
                  className="flex-1 bg-gradient-to-r from-accent to-accent2
                             text-white py-3 rounded-xl text-sm font-syne font-semibold"
                >
                  Done & Continue
                </button>
                <button
                  onClick={() => setStep(3)}
                  className="flex-1 bg-dark-card2 text-white/50 py-3 rounded-xl text-sm"
                >
                  Skip
                </button>
              </div>
            </div>
          )}

          {/* ── Step 3: Spending Caps ──────────────────────── */}
          {step === 3 && (
            <div className="space-y-4">
              <div>
                <h3 className="font-syne font-semibold text-white mb-1">
                  🎯 Step 3 of 3 — Spending Caps
                </h3>
                <p className="text-white/50 text-sm">
                  Set monthly limits for variable spending. Adjust anytime in Settings.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {Object.entries(caps).map(([cat, val]) => (
                  <div key={cat}>
                    <label className="text-white/60 text-xs mb-1 block">
                      {CATEGORY_ICONS[cat] ?? "📦"} {cat}
                    </label>
                    <div style={{ position: 'relative' }}>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={val}
                        onFocus={(e) => e.target.select()}
                        onChange={(e) =>
                          setCaps((prev) => ({
                            ...prev,
                            [cat]: e.target.value.replace(/\D/g, ""),
                          }))
                        }
                        placeholder="Set cap limit"
                        className="w-full bg-dark-card2 border border-white/10 rounded-xl
                                   px-3 py-2 pr-8 text-white text-sm placeholder-white/30
                                   focus:border-accent focus:outline-none"
                      />
                      {val !== "" && (
                        <button
                          type="button"
                          onClick={() => setCaps((prev) => ({ ...prev, [cat]: "" }))}
                          style={{
                            position: 'absolute', right: 8, top: '50%',
                            transform: 'translateY(-50%)',
                            color: 'rgba(255,255,255,0.3)',
                            fontSize: 14, lineHeight: 1, background: 'none', border: 'none',
                            cursor: 'pointer', padding: '2px 4px',
                          }}
                          aria-label={`Clear ${cat} cap`}
                        >
                          ×
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => saveCaps(false)}
                  disabled={loading}
                  className={btnPrimary}
                >
                  {loading ? "Saving…" : "🚀 Let's Go!"}
                </button>
                <button
                  onClick={() => saveCaps(true)}
                  disabled={loading}
                  className={btnSecondary}
                >
                  Skip
                </button>
              </div>
            </div>
          )}

          {/* Skip all — available from any step */}
          <button
            onClick={complete}
            disabled={loading}
            className="mt-6 w-full text-white/30 hover:text-white/60 text-sm
                       transition-colors py-2 disabled:opacity-40"
          >
            Skip setup, go straight to the app
          </button>

        </div>
      </div>
    </div>
  );
}
