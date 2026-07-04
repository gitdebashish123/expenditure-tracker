# Wallet Mantra — Android Readiness Assessment
**Date**: 2026-07-01
**Author**: Debashish (reviewed with Claude)
**Status**: Pre-Android — web app in good shape, gaps to close before Play Store submission

---

## Honest summary

The product and backend are closer to Android-ready than most side projects ever reach.
The core concept is differentiated, the data model is stable, and the API is
production-grade. However, several correctness gaps, missing mobile UX primitives, and
Play Store prerequisites need to be addressed before submission.

---

## What's actually ready

### Backend — fully app-ready
- FastAPI with JWT auth, Railway deployment, Cloudflare custom domain.
- Per-user data isolation, rate limiting, security headers.
- An Android app would consume the same API identically to the web app.
- **No backend rewrite needed.**

### Data model — stable
- Expenses, fixed templates, pools, income, budgets, categories — all well-normalised.
- No structural changes needed to support mobile.

### Core product loop — complete
- Expense logging (AI parser + manual fallback), Fixed tab checklist, Overview,
  History, Settings — battle-tested through daily use.

---

## What's not ready — matters more on mobile than web

### 1. Open spec backlog (correctness issues)
Several specs are correctness fixes that are more jarring on mobile (no "refresh the
page" reflex for users):

| Spec | Issue | Priority |
|------|-------|----------|
| 27 | Insight staleness — `toggle_paid` still not invalidating cache | **Must close** |
| 28 | Parser fallback — AI outage leaves expense entry broken | **Must close** |
| 29 | Day-1 awareness — mantra/insight/story wrong on first of month | **Must close** |
| 30 | User-type AI classification — new/inconsistent/consistent branches | Should close |
| 31 | Logo + celebration animation | Nice to have |

### 2. App is not a PWA yet
- No service worker, no offline capability, no proper web app manifest.
- `generate_icons.py` exists in `public/icons/` but was **never run** — no actual
  icon files present.
- A raw WebView without PWA groundwork = no splash screen, no app icon, browser
  chrome showing, no offline state. Users notice immediately.

### 3. Mobile-specific UX gaps not visible on desktop
- **No haptic feedback** on tick/untick in Fixed tab — expected on Android.
- **No pull-to-refresh** — mobile users pull down instinctively; its absence feels
  broken when data is stale.
- **KPI carousel scroll-snap** was rebuilt for Safari (Spec 21) — needs testing on
  real Android Chrome (different scroll engine behaviour).
- **Bottom navigation inset** — the 5-tab bottom nav doesn't account for Android's
  gesture navigation bar (swipe-home area), which can overlap fixed-position navs.
- **Android IME / keyboard behaviour** — the natural-language expense input was tuned
  for iOS keyboard. Android autocorrect and input method editors behave differently,
  especially for numeric fields.

### 4. No crash reporting or analytics
- No Firebase Crashlytics, no Sentry, no client-side error tracking.
- On the web, backend logs provide visibility. A mobile app needs client-side
  error reporting before Play Store — otherwise production crashes are invisible.

### 5. Play Store prerequisites not started
- [ ] Privacy policy at a **public hosted URL** (`PRIVACY.md` exists but needs to be
      a live web page).
- [ ] Data safety form (what you collect, how stored, whether shared with third parties).
- [ ] Store listing: screenshots, feature graphic, app description, short description.
- [ ] Target API level — Android 14 / API 34 required for new apps as of 2024.
- [ ] **Signing keystore** — generate and back this up securely. Losing it means you
      can never update the app on the Play Store.

---

## The two paths to Android

### Path A — PWA + Capacitor wrap (recommended)
**Timeline: 2–4 weeks after spec backlog is closed**

Convert the web app to a proper PWA, then wrap with
[Capacitor](https://capacitorjs.com/) for Play Store distribution.

**Steps:**
1. Run `generate_icons.py` to produce `icon-192.png` / `icon-512.png`.
2. Add `manifest.json` to `public/` (name, icons, theme colour, display: standalone).
3. Add a service worker for basic offline state (at minimum a "you're offline" page).
4. Add `<meta name="theme-color">` and viewport config to `index.html`.
5. Install Capacitor: `npm install @capacitor/core @capacitor/android`.
6. `npx cap init` → `npx cap add android`.
7. Add Capacitor plugins as needed:
   - `@capacitor/haptics` — for tick/untick feedback.
   - `@capacitor/push-notifications` — for due-bill reminders (future).
   - `@capacitor/status-bar` — for Android status bar colour.
8. Handle gesture nav inset via `env(safe-area-inset-bottom)` in CSS.
9. Build: `npm run build` → `npx cap copy android` → open in Android Studio → generate signed APK/AAB.

**Pros:** one codebase, all web work carries over, Capacitor gives native API access.
**Cons:** not pixel-perfect native feel; some complex animations may be janky on
lower-end Android devices.

### Path B — React Native rewrite
**Timeline: 4–6 months minimum**

Full native Android (and iOS) app in React Native or Expo, sharing business logic
with the web app but rewriting all UI components.

**Pros:** best performance ceiling, best platform feel, true native.
**Cons:** rewrite 40+ components from scratch, lose all CSS/Tailwind work, two
codebases to maintain.

**→ Recommended only if committed to App Store + Play Store as primary distribution
and willing to invest the rewrite time.**

---

## Recommended sequence before Play Store submission

```
1. Close specs 27, 28, 29, 30  (correctness + day-1 awareness)
2. Run generate_icons.py        (produce real icon assets)
3. Add web app manifest          (manifest.json in public/)
4. Add service worker            (offline state, at minimum)
5. Fix bottom nav inset          (env safe-area-inset-bottom)
6. Add pull-to-refresh           (Today + Fixed + Overview)
7. Test on real Android device   (Chrome scroll-snap, IME, gesture nav)
8. Add Sentry or Crashlytics     (client-side error reporting)
9. Install Capacitor             (cap init, cap add android)
10. Add haptics                  (Capacitor haptics plugin on tick/untick)
11. Host privacy policy          (convert PRIVACY.md to a live URL)
12. Generate signing keystore    (back up securely — losing it = permanent)
13. Complete Play Store listing  (screenshots, description, data safety form)
14. Internal test track → Closed testing → Open testing → Production
```

---

## The one question to answer first

**Who is the second user?**

Right now Wallet Mantra is effectively a single-user app tuned to one person's
income/spend pattern. The backend supports multiple users, but every AI prompt and
insight is calibrated to your specific financial profile.

Before Android, get **3–5 beta users** with different financial profiles testing
on the web app first. The day-1 bug was only caught because you used it yourself
on July 1 — there will be more edge cases that only surface with different income
levels, different category patterns, or different usage rhythms.

That beta phase also validates whether Path A (PWA wrap) is good enough or whether
the mobile experience is too compromised to ship as a WebView.

---

## Key files / references

| Resource | Path / URL |
|----------|------------|
| Backend API | `backend/main.py` |
| Frontend entry | `frontend/react/src/main.tsx` |
| Public assets | `frontend/react/public/` |
| Icon generator | `frontend/react/public/icons/generate_icons.py` |
| Privacy policy (draft) | `PRIVACY.md` |
| Capacitor docs | https://capacitorjs.com/docs/getting-started |
| Play Store requirements | https://developer.android.com/distribute/play-policies |
| Signed APK guide | https://developer.android.com/studio/publish/app-signing |
