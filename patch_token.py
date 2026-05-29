import pathlib, re

p = pathlib.Path("frontend/app.py")
txt = p.read_text(encoding="utf-8")

old = (
    "me = api(\"GET\", \"/auth/me\")\n"
    "if me and st.session_state.user_email is None:\n"
    "    # Restore user info if session state was lost (e.g. after hot reload)\n"
    "    st.session_state.user_email = me.get(\"email\")\n"
    "# Always sync is_admin and onboarding_complete from server \u2014 not gated on user_email being None\n"
    "# so it reflects the real DB value on every page load and after login rerun\n"
    "if me:\n"
    "    st.session_state.user_is_admin       = me.get(\"is_admin\", False)\n"
    "    st.session_state.onboarding_complete = me.get(\"onboarding_complete\", True)\n"
)

new = (
    "me = api(\"GET\", \"/auth/me\")\n"
    "if me and st.session_state.user_email is None:\n"
    "    # Restore user info if session state was lost (e.g. after hot reload)\n"
    "    st.session_state.user_email = me.get(\"email\")\n"
    "# Always sync is_admin and onboarding_complete from server on every page load\n"
    "# so the Admin tab appears immediately after login without requiring a reload\n"
    "if me:\n"
    "    st.session_state.user_is_admin       = me.get(\"is_admin\", False)\n"
    "    st.session_state.onboarding_complete = me.get(\"onboarding_complete\", True)\n"
)

if old in txt:
    txt = txt.replace(old, new, 1)
    p.write_text(txt, encoding="utf-8")
    print("Patched: token block comment updated")
else:
    # Show current token block area
    for i, line in enumerate(txt.splitlines()):
        if "api(\"GET\", \"/auth/me\")" in line:
            lines = txt.splitlines()
            print("\n".join(f"{i+j}: {lines[i+j-1]}" for j in range(12)))
            break
    print("Pattern not matched - showing context above")
