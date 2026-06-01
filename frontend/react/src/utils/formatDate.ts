/**
 * Relative date formatting — ported from fmt_date() in frontend/app.py
 * Returns "Today", "Yesterday", "28 May", or "28 May 2024"
 */
export function fmtDate(dateStr: string): string {
  const d = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);

  if (d.toDateString() === today.toDateString()) return "Today";
  if (d.toDateString() === yesterday.toDateString()) return "Yesterday";

  const opts: Intl.DateTimeFormatOptions =
    d.getFullYear() === today.getFullYear()
      ? { day: "numeric", month: "short" }
      : { day: "numeric", month: "short", year: "numeric" };

  return d.toLocaleDateString("en-IN", opts);
}

/**
 * Format a YYYY-MM month key as "May 2026"
 * Used in month selector and tab headers
 */
export function fmtMonth(monthKey: string): string {
  const [y, m] = monthKey.split("-");
  return new Date(Number(y), Number(m) - 1).toLocaleDateString("en-IN", {
    month: "long",
    year: "numeric",
  });
}
