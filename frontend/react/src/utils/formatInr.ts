/**
 * Indian lakh number format: 15,00,000 not 1,500,000
 * Ported from Streamlit: fmt_inr() in frontend/app.py
 *
 * Examples:
 *   fmtInr(1500)    → "₹1,500"
 *   fmtInr(150000)  → "₹1,50,000"
 *   fmtInr(1500000) → "₹15,00,000"
 *   fmtInr(-500)    → "-₹500"
 */
export function fmtInr(amount: number | null | undefined): string {
  if (amount == null) return "₹0";
  const neg = amount < 0;
  const a = Math.abs(Math.round(amount));
  const s = String(a);

  if (s.length <= 3) return (neg ? "-₹" : "₹") + s;

  const last3 = s.slice(-3);
  let rest = s.slice(0, -3);
  const parts: string[] = [];
  while (rest.length > 2) {
    parts.unshift(rest.slice(-2));
    rest = rest.slice(0, -2);
  }
  if (rest) parts.unshift(rest);

  return (neg ? "-₹" : "₹") + parts.join(",") + "," + last3;
}
