---
description: Convert a spec under .claude/specs/ into a precise implementation plan under .claude/plans/
argument-hint: <path to spec file, e.g. .claude/specs/04_foo.md>
---

# Spec → Implementation Plan

You are converting a spec document into an implementation plan, following
the structure of existing plans in `.claude/plans/` (read
`02-react-migration-phase2-bug-fix-v3.md` for reference shape before writing).

## Input

Spec file: $ARGUMENTS

## Process

1. Read the full spec file given. If no path was given, ask which spec to use
   (list the files in `.claude/specs/` as options).
2. For **each numbered issue** in the spec, read the actual current state of
   every affected file mentioned — do not rely on the spec's description of
   the code, verify it against what's on disk right now, since the spec may
   be stale if other changes landed since it was written. If the code has
   diverged from what the spec describes, flag this clearly in the plan
   instead of silently planning against outdated assumptions.
3. Write each item with these exact sections:
   - **Scope** — Frontend-only / Backend-only / Backend + Frontend
   - **Files** — exact paths, with line numbers where the change goes
   - **Root cause** — restated precisely against the current code (cite the
     real line/snippet you just read)
   - **What to do** — concrete, in enough detail that someone could execute
     it without re-deriving the approach; include before/after snippets
     where it clarifies the change, but this is still a plan, not a diff —
     do not actually edit any files
4. **Order items smallest-blast-radius-first** (trivial/isolated changes
   before ones touching shared state, DB schema, or multiple files), not
   necessarily the spec's original order. Note when an item depends on
   another item being done first.
5. Header block: title, link back to the spec path, date (today), branch
   name if the spec or CLAUDE.md mentions one in progress (ask if unclear
   rather than guessing).
6. **This command only writes the plan.** Do not modify any application code.
   Stop after the plan file is written — do not proceed to implementation
   even if the plan looks simple.

## Output

Save to `.claude/plans/NN-short-slug.md`, matching the spec's number where
possible, incrementing a `-v2`/`-v3` suffix if a plan for this spec already
exists (check first — don't silently overwrite).

After writing, show the file path and a short summary: total items, how many
need backend changes, and which item should be tackled first per the ordering.
