"""
One-shot rename: SpendSense → SanchaySaathi across all React migration docs.

Usage (run from anywhere inside the project):
    cd /Users/debashish/Desktop/ai-projects/expenditure-tracker
    python3 design/react-migration/_rename_sanchaySaathi.py
"""
import pathlib

ROOT   = pathlib.Path(__file__).parent.parent.parent   # expenditure-tracker/
DESIGN = ROOT / "design"

TARGET_FILES = [
    DESIGN / "TRACK_2_REACT_MIGRATION_PROMPT.md",
    DESIGN / "react-migration" / "T2.1-T2.2_scaffold_auth_shell.md",
    DESIGN / "react-migration" / "T2.3_quick_add_tab.md",
    DESIGN / "react-migration" / "T2.4_fixed_tab.md",
    DESIGN / "react-migration" / "T2.5_overview_dashboard_tab.md",
    DESIGN / "react-migration" / "T2.6_history_tab.md",
    DESIGN / "react-migration" / "T2.7_settings_tab.md",
    DESIGN / "react-migration" / "T2.8_account_admin.md",
    DESIGN / "react-migration" / "T2.9-T2.10_pwa_docker_railway.md",
]

# Order matters: longest / most specific first to avoid partial re-replacement
REPLACEMENTS = [
    # App name — all capitalisation variants
    ("SpendSense",                                      "SanchaySaathi"),
    ("spendsense",                                      "sanchaySaathi"),

    # Taglines — every variant used across the files
    ("Your personal salary tracker",                    "Your companion for smart daily budgeting"),
    ("Personal salary tracker",                         "Your companion for smart daily budgeting"),
    ("Personal salary & expense tracker",               "Your companion for smart daily budgeting"),
    ("Personal Expenditure Tracker",                    "Your companion for smart daily budgeting"),
    ("Personal expense tracker",                        "Your companion for smart daily budgeting"),

    # PWA manifest description field (already covered by tagline above, but be explicit)
    ('"description": "Personal salary & expense tracker"',
     '"description": "Your companion for smart daily budgeting"'),

    # CSV export filenames in code snippets
    ("spendsense_",                                     "sanchaySaathi_"),

    # HTML <title> tag
    ("<title>SpendSense</title>",                       "<title>SanchaySaathi</title>"),

    # JS string literals — window.document.title assignments
    ("'SpendSense'",                                    "'SanchaySaathi'"),
    ('"SpendSense"',                                    '"SanchaySaathi"'),
]

print("\nSanchaySaathi rename — processing files...\n")
total_files_changed = 0

for fpath in TARGET_FILES:
    if not fpath.exists():
        print(f"  MISSING  {fpath.name}")
        continue

    original = fpath.read_text(encoding="utf-8")
    updated  = original

    for old, new in REPLACEMENTS:
        updated = updated.replace(old, new)

    if updated != original:
        fpath.write_text(updated, encoding="utf-8")
        # Count lines changed for reporting
        orig_lines  = original.splitlines()
        new_lines   = updated.splitlines()
        diff_count  = sum(1 for a, b in zip(orig_lines, new_lines) if a != b)
        print(f"  UPDATED  {fpath.name}  ({diff_count} line(s) changed)")
        total_files_changed += 1
    else:
        print(f"  ok       {fpath.name}  (no occurrences)")

print(f"\n✅  Done. {total_files_changed} file(s) updated.\n")
