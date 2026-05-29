"""One-shot patch: replace st.tabs line with conditional admin tab version."""
import re, pathlib

p = pathlib.Path("frontend/app.py")
txt = p.read_text(encoding="utf-8")

# Find and replace the tabs line
pattern = r'tab1, tab2, tab3, tab4, tab5 = st\.tabs\(\[.*?\]\)'
replacement = (
    '_tab_labels = ["\u26a1 Quick Add", "\U0001f4cc Fixed", "\U0001f4ca Dashboard", "\U0001f4cb Expenses", "\u2699\ufe0f Settings"]\n'
    'if st.session_state.user_is_admin:\n'
    '    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(_tab_labels + ["\U0001f6e1\ufe0f Admin"])\n'
    'else:\n'
    '    tab1, tab2, tab3, tab4, tab5 = st.tabs(_tab_labels)\n'
    '    tab6 = None'
)

new_txt, count = re.subn(pattern, replacement, txt)
if count:
    p.write_text(new_txt, encoding="utf-8")
    print(f"Patched {count} occurrence(s)")
else:
    for i, line in enumerate(txt.splitlines()):
        if "st.tabs" in line:
            print(f"Line {i+1}: {repr(line)}")
    print("Pattern not matched")
