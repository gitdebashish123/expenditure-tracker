---
description: Turn a list of bug/UX observations into a structured spec markdown file under .claude/specs/
argument-hint: [free-form list of observations, or a topic to investigate]
---

# Spec: Bug & Enhancement Report

You are creating a new spec document in `.claude/specs/` following the exact
structure used by existing specs in this repo (see `01_post_migration_sprint1_bugs.md`,
`02_react-migration-phase2-bug-fix.md` for reference shape — read at least one
before writing).

## Input

The user's observations: $ARGUMENTS

## Process

1. **Do not guess root causes.** For each observation, actually read the
   relevant files (backend/, frontend/react/src/) before writing anything.
   If you can't find the relevant file, say so in the spec rather than
   inventing a plausible-sounding cause.
2. **Number each issue** in the order given, unless grouping makes more sense
   (related issues can be merged into one numbered item — note this explicitly).
3. For each issue, write these exact sections, in this order:
   - **Symptom** — what the user observed, in their words plus precise detail
   - **Root cause** — the actual mechanism, with real code snippets/line
     references from files you've read, not paraphrase
   - **Affected file(s)** — exact paths
   - **Fix approach** — concrete enough that a future implementation session
     doesn't need to re-investigate, but do not write the actual diff/patch
   - **Acceptance criteria** — testable, specific, written as steps a human
     can verify by using the app
   - **Priority** — High/Medium/Low with a one-line justification
4. End with an **Implementation Order** table: columns `#`, `Issue`, `Priority`,
   `Effort` (rough, e.g. "30 min" / "2h"), `Files`. Order by priority then
   effort (cheap-and-high-priority first).
5. Add a **Files NOT modified by this spec** section if relevant, listing
   anything explicitly out of scope.
6. Header block: title, date (today), status (`Open — awaiting implementation`).
7. **This command only writes the spec.** Do not modify any application code
   or existing files. Do not create a plan. Stop after the spec file is written.

## Output

Save to `.claude/specs/NN_short-slug.md`, where `NN` is the next unused
two-digit prefix in that folder (check existing files first) and `short-slug`
is a few hyphenated words describing the topic.

After writing, show the user the file path and a one-paragraph summary of
how many issues were captured and which ones are High priority. Do not paste
the full spec back into chat — they can open the file.
