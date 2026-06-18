# App Rename — SanchaySaathi → Wallet Mantra
**Observed:** June 2026  
**Status:** Open — awaiting implementation

---

## Overview

The current app name **SanchaySaathi** is phonetically and visually close to
**Sanchar Saathi**, a prominent Indian government telecom app (DoT / TRAI). To
avoid brand confusion, user trust issues, and potential trademark concerns, the
app is being renamed to:

> **Wallet Mantra — Beyond expense tracking**

This is a purely cosmetic / branding change. No backend logic, DB schema, or API
contracts change. All changes are limited to display strings, metadata, and
frontend assets.

---

## Scope of Changes

### 1. React Frontend (`frontend/react/`)

| File | Change |
|---|---|
| `index.html` | `<title>` tag → `Wallet Mantra` |
| `public/manifest.json` | `name` and `short_name` fields |
| `src/components/LoginPage.tsx` | App name / tagline in header |
| `src/components/OnboardingWizard.tsx` | Any "SanchaySaathi" references in copy |
| `src/components/DashboardPage.tsx` | Sidebar / header branding |
| `src/components/AccountPage.tsx` | Any app-name references |
| `vite.config.ts` | PWA `manifest` name fields if hardcoded |

Search pattern to catch all occurrences:
```bash
grep -r -i "sancay\|sanchay\|saathi\|spendsense\|spend.sense" frontend/react/src/ --include="*.tsx" --include="*.ts" --include="*.html" --include="*.json"
```

### 2. Root & Config Files

| File | Change |
|---|---|
| `CLAUDE.md` | Project name in heading and description |
| `.claude/CLAUDE.md` | Project name in heading |
| `README.md` (if exists) | Project name and tagline |
| `docker-compose.yml` | `container_name` / labels (cosmetic only) |
| `config.yaml` | Any `app_name` key if present |

### 3. Backend (`backend/`)

| File | Change |
|---|---|
| `main.py` | FastAPI `title=` in `FastAPI(...)` constructor |
| Any email / notification templates | App name in copy |

---

## Acceptance Criteria

1. **No "SanchaySaathi" or "SpendSense"** visible in any rendered UI (browser
   tab, login page, dashboard header, onboarding, PWA install prompt).
2. **Browser tab** shows `Wallet Mantra`.
3. **Login page** displays `Wallet Mantra` as the primary heading and
   `Beyond expense tracking` as the tagline.
4. **PWA manifest** `name` = `"Wallet Mantra"`, `short_name` = `"WalletMantra"`.
5. **FastAPI docs** page (`/docs`) title shows `Wallet Mantra`.
6. **No functional regressions** — all existing features work unchanged.
7. Grep for old names returns zero hits in `frontend/react/src/` and `backend/`.

---

## Out of Scope

- Domain / URL changes (handled separately via DNS/hosting config).
- App icon / logo redesign (separate design task).
- Database volume rename (no user impact; internal Docker volume name is
  cosmetic and risks data loss if renamed carelessly — leave as-is).
- Backend route paths, JWT claims, or API contracts — none change.

---

## Priority

**Medium** — brand safety concern, but no functional impact. Can be batched
into the next available sprint slot.

---

## Notes

- The tagline `Beyond expense tracking` should appear as a subtitle beneath
  the primary `Wallet Mantra` heading on the login/landing screen.
- Keep the tagline out of the `<title>` tag (keep it to `Wallet Mantra` for
  brevity in browser tabs and PWA icons).
- CLAUDE.md files should be updated to reflect the new name so that future
  Claude sessions have correct context.
