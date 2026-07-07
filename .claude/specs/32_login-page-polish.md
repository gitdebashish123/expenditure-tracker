# Spec 32 — Login Page Polish: Form UX, Value Prop, Privacy Notice URL
**Date**: 2026-07-01
**Status**: ✅ Implemented — all 7 items landed and verified live (2026-07-04). See `.claude/plans/32-login-page-polish.md` and `.claude/blocked/32-followups-for-reevaluation.md` for two bugs found and fixed during implementation that weren't anticipated by this spec.
**Branch**: `feature/sprint06261-ui-enhancement` *(confirm active branch before starting)*
**Follows**: `31_brand-logo-and-celebration.md`
**Source**: External login-page design review (Jul 2026) cross-checked against actual
codebase. Approved interactive mockup (desktop split + mobile, no biometrics, no
remember me, forgot password right-aligned below Sign In button).

---

## Context

The current `LoginPage.tsx` already has the right structure (split layout,
rotating quotes, video panel, real logo, Mail/Lock field icons, error specificity,
live `PasswordStrengthBar` on register). This spec adds the remaining polish layer
confirmed through the mockup review sessions:

**What's NOT in this spec (deliberately excluded after honest review):**
- Biometric / Face ID — no infrastructure; deferred post-Android.
- Remember me — deferred.
- Social proof / ratings — no real user data yet; would be misleading.
- "Bank-level security / 256-bit encryption" claims — inaccurate for current arch.

---

## Item 1 — Value proposition copy + tagline (`LoginPage.tsx`)

**Current:** left panel shows only "Wallet Mantra" wordmark with no supporting copy.
The right panel heading says "Welcome back / Sign in to Wallet Mantra."

**Changes (left visual panel, desktop only):**
- Add `✨ Your AI money companion` badge below the wordmark.
- Add value proposition strapline below the badge:

```tsx
<div className="text-left mt-4 space-y-0.5">
  <p className="text-sm text-white/70">Build awareness.</p>
  <p className="text-sm text-white/70">Reduce impulse spending.</p>
  <p className="text-sm text-white/70">
    Save <span className="text-emerald-400 font-medium">consistently.</span>
  </p>
</div>
```

- Add AI companion badge above the strapline:

```tsx
<span className="inline-flex items-center gap-1 text-xs text-indigo-300
                 bg-indigo-500/15 border border-indigo-500/30 rounded-full px-3 py-1 mt-3">
  <Sparkles size={11} /> Your AI money companion
</span>
```

Import `Sparkles` from `lucide-react` (already a project dependency).

**Right panel heading** — keep "Welcome back / Sign in to Wallet Mantra" as is
(already correct from the previous login page work).

**Acceptance:** on desktop, the left panel shows the logo, wordmark, AI badge, and
the three-line value proposition. On mobile (left panel hidden), the form panel shows
the logo, wordmark, and tagline only — no value prop strapline (too tall for mobile).

---

## Item 2 — Persistent form labels (`LoginPage.tsx`)

**Current:** login form uses `placeholder`-only fields — label disappears when
typing begins. This is an accessibility and usability gap (user forgets which field
is which mid-entry, especially when autocomplete fires).

**Change:** add visible `<label>` elements above each login-mode field:

```tsx
{mode === "login" && (
  <form onSubmit={handleLogin} className="space-y-3">
    <div>
      <label htmlFor="login-email" className="block text-xs text-white/50 mb-1">
        Email
      </label>
      <div className="login-field">
        <Mail size={16} />
        <input
          id="login-email"
          type="email"
          placeholder="youremail@example.com"
          ...
        />
        {/* inline validation icon — Item 3 */}
      </div>
    </div>
    <div>
      <label htmlFor="login-pw" className="block text-xs text-white/50 mb-1">
        Password
      </label>
      <div className="login-field">
        <Lock size={16} />
        <input id="login-pw" type="password" placeholder="Password" ... />
        {/* show/hide toggle — Item 4 */}
      </div>
    </div>
    ...
  </form>
)}
```

Keep the register form as-is (it already uses placeholder labels which is
acceptable for the secondary form mode).

---

## Item 3 — Inline email validation indicator (`LoginPage.tsx`)

**Current:** `emailValid` is computed but never shown to the user. The error only
surfaces after a failed submit attempt.

**Change:** render a small icon on the right side of the email field, visible as
soon as the user has typed something:

```tsx
{email.length > 0 && (
  emailValid
    ? <CheckCircle size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-emerald-400 pointer-events-none" />
    : <XCircle   size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-red-400   pointer-events-none" />
)}
```

The `login-field` wrapper is already `position: relative` (from the `login-field`
CSS class), so absolute-positioned icons work without wrapper changes.

Import `CheckCircle` and `XCircle` from `lucide-react`.

**Acceptance:** typing a partial email (no `@`) shows a red ✗; a complete valid
address shows a green ✓. No icon shown when the field is empty. Does not affect
submit validation logic.

---

## Item 4 — Password show/hide toggle (`LoginPage.tsx`)

**Current:** the password field has a `<Lock>` icon on the left but no way to
reveal what's been typed. On mobile, autocorrect / IME can silently mangle
passwords; failed logins result.

**Change:** add a toggle button on the right of the password field:

```tsx
const [showPw, setShowPw] = useState(false);

// in the password field:
<div className="login-field">
  <Lock size={16} />
  <input
    id="login-pw"
    type={showPw ? "text" : "password"}
    placeholder="Password"
    value={password}
    onChange={(e) => setPassword(e.target.value)}
    className={inputCls}
    autoComplete="current-password"
  />
  <button
    type="button"
    onClick={() => setShowPw(v => !v)}
    className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30
               hover:text-white/60 transition-colors"
    aria-label={showPw ? "Hide password" : "Show password"}
  >
    {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
  </button>
</div>
```

Import `Eye` and `EyeOff` from `lucide-react`.

**Scope:** login form only. The register form already has a `PasswordStrengthBar`
and confirm field — adding show/hide there is a separate consideration.

**Acceptance:** clicking the eye icon in the password field toggles between masked
and visible text. The `aria-label` updates to reflect the current state.

---

## Item 5 — Forgot password: move below Sign In, right-align (`LoginPage.tsx`)

**Current:** "Forgot password?" is a `w-full` centred button rendered *outside*
and *after* the `<form>` block (`mt-2 w-full text-center`). It sits below the form
card as a standalone element.

**Changes (two parts):**

**5a — Move inside the form, below the submit button:**

```tsx
<form onSubmit={handleLogin} className="space-y-3">
  {/* email field */}
  {/* password field */}
  <button type="submit" disabled={loading} className="w-full ...">
    {loading ? "Signing in…" : "Sign In"}
  </button>

  {/* Forgot password — right-aligned, below Sign In */}
  <div className="flex justify-end">
    <button
      type="button"
      onClick={() => setShowForgotMsg(v => !v)}
      className="text-xs text-indigo-400/70 hover:text-indigo-300 transition-colors py-1"
    >
      Forgot password?
    </button>
  </div>
</form>
```

**5b — Remove** the existing standalone `{mode === "login" && (<> <button ... Forgot password?> ...)}` block that currently lives outside the form — it's superseded.

The `showForgotMsg` state and its dismissible message panel are retained — they move
inside the form alongside the new button position.

**Acceptance:** on the login form, "Forgot password?" appears right-aligned,
directly below the Sign In button, inside the form. It is not centred. It is not
above the Sign In button.

---

## Item 6 — Honest trust footer strip (login panel + mobile) (`LoginPage.tsx`)

**Current:** the bottom of the login right panel has a single small privacy link only.
No trust signals are present.

**Add** a three-item trust strip above the privacy notice:

```tsx
<div className="flex justify-center gap-4 mt-4 pt-3 border-t border-white/10">
  {[
    { icon: <Lock size={11} />,      label: "Passwords encrypted" },
    { icon: <Shield size={11} />,    label: "Data stays private"  },
    { icon: <UserCheck size={11} />, label: "You're in control"   },
  ].map(({ icon, label }) => (
    <span key={label} className="flex items-center gap-1 text-[10px] text-white/25">
      {icon} {label}
    </span>
  ))}
</div>
```

Import `Shield` and `UserCheck` from `lucide-react`.

**Accuracy rule (do not change):** these three claims are accurate for the current
architecture — bcrypt passwords, JWT-scoped data, export/delete available. Do not
add "Bank-level security," "256-bit encryption," or "Auto Backup" — those claims
are not accurate.

---

## Item 7 — Privacy notice: URL + wording (`LoginPage.tsx` + `ProfileDropdown.tsx`)

**Current state (both files):**
- URL: `https://github.com/gitdebashish123/expenditure-tracker/blob/main/PRIVACY.md`
  (GitHub blob — third-party domain, unpolished, Play Store will reject it).
- Wording: "Privacy Notice" (capital N).

**Changes:**

**7a — Create `public/privacy.html`** (new file):
Convert `PRIVACY.md` content to a minimal, styled HTML page. Serve statically from
Vite's `public/` folder — automatically available at `app.wallet-mantra.com/privacy`
with no backend change, no new route, no extra hosting.

The file should be a clean, readable HTML page matching the app's dark aesthetic —
no frameworks needed, plain `<style>` in `<head>`, `max-width: 680px`, legible body
text. This is out of scope for `LoginPage.tsx` itself — just a file creation task.

**7b — Update both URL references:**

```tsx
// LoginPage.tsx — privacy notice footer:
<a href="/privacy" target="_blank" rel="noopener noreferrer" className="...">
  Privacy notice
</a>

// ProfileDropdown.tsx — dropdown menu item:
<a href="/privacy" target="_blank" rel="noopener noreferrer" onClick={() => setOpen(false)} ...>
  <Lock size={14} /> Privacy notice
</a>
```

**7c — Wording:** lowercase "notice" ("Privacy notice") — sentence case consistent
with Spec 20's heading-consistency rule.

**Acceptance:**
- `/privacy` serves a readable HTML page at `app.wallet-mantra.com/privacy`.
- Both the login-page footer and the profile dropdown point to `/privacy`.
- No GitHub URL anywhere in the frontend.
- Sentence-case "Privacy notice" in both locations.

---

## Files
| Item | File(s) |
|---|---|
| 1 — Value prop + AI badge | `pages/LoginPage.tsx` |
| 2 — Persistent labels | `pages/LoginPage.tsx` |
| 3 — Email validation icon | `pages/LoginPage.tsx` |
| 4 — Password show/hide | `pages/LoginPage.tsx` |
| 5 — Forgot password position | `pages/LoginPage.tsx` |
| 6 — Trust footer strip | `pages/LoginPage.tsx` |
| 7a — Privacy HTML page | `public/privacy.html` (new) |
| 7b/7c — Privacy URL + wording | `pages/LoginPage.tsx`, `components/layout/ProfileDropdown.tsx` |

## New lucide-react imports needed
`Sparkles`, `CheckCircle`, `XCircle`, `Eye`, `EyeOff`, `Shield`, `UserCheck`
(all available in lucide-react, already a project dependency — no install needed).

## Sequencing
Items 1–7 are independent and can land in one commit. Item 7a (`privacy.html`)
should be created first so the link in 7b points to a live page from day one.

## Out of scope
- Register form show/hide toggle (separate consideration).
- Biometrics, remember me, social proof — explicitly deferred per review decision.
- Left visual panel mobile display (hidden below 900px by design — no change).
