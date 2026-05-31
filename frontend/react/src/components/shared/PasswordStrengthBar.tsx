/**
 * Live password strength indicator
 *
 * Key improvement over Streamlit: updates on every keystroke.
 * In Streamlit, reg_password had to be placed outside st.form() to get
 * live re-renders. In React this works naturally with useState.
 *
 * 4 checks: length≥8, uppercase, digit, special char
 * Score 1 = Weak (red), 2 = Fair (orange), 3 = Good (yellow), 4 = Strong (green)
 */
interface Props {
  password: string;
}

export function PasswordStrengthBar({ password }: Props) {
  if (!password) return null;

  const checks = [
    password.length >= 8,
    /[A-Z]/.test(password),
    /[0-9]/.test(password),
    /[!@#$%^&*]/.test(password),
  ];
  const score = checks.filter(Boolean).length;

  const colours = ["#ef4444", "#f97316", "#eab308", "#22c55e"];
  const labels  = ["Weak", "Fair", "Good", "Strong"];
  const colour  = score > 0 ? colours[score - 1] : "#374151";
  const label   = score > 0 ? labels[score - 1] : "";

  return (
    <div className="mt-1.5">
      <div
        className="h-1 rounded-full transition-all duration-300"
        style={{ width: `${score * 25}%`, background: colour }}
      />
      <p className="text-xs mt-1" style={{ color: colour }}>
        {label}
      </p>
    </div>
  );
}
