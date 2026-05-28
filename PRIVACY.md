# SpendSense — Privacy Notice

*Plain English. No legal jargon. Reading time: under 2 minutes.*

---

## 1. What We Store

When you use SpendSense, we store only what you explicitly enter:

- **Expense entries** — vendor name, amount, category, date, and any note you add
- **Income entries** — amount and month
- **Budget limits** — your spending caps per category
- **Account credentials** — your email address and a bcrypt-hashed password (we never store your password in plaintext — it is hashed before saving and cannot be reversed)
- **Last login timestamp** — so you can spot unexpected access

That is the complete list. Nothing else is stored.

---

## 2. What We Do NOT Store

- Your full name, phone number, or address
- Payment card details or bank account numbers
- Device information, browser fingerprints, or IP addresses
- Your location
- Any data you did not explicitly type into the app

---

## 3. What Goes to Anthropic API

SpendSense uses Claude (by Anthropic) to parse natural language expense input.

**When you type something like "zomato 350, ola 120" in the Quick Add box**, that text is sent to Anthropic's Claude API to identify the vendor, amount, and category.

- Only the raw expense text you type is sent — not your email, balance, income, or any other account data
- Anthropic's privacy policy applies to that processing: https://www.anthropic.com/privacy
- If you prefer not to send data to Anthropic, use the manual expense entry form instead (no AI parsing)

---

## 4. Data Retention

- Your data is stored for as long as your account exists
- When you delete your account, all your data is permanently and immediately deleted — expenses, income entries, budget settings, templates, and your user record
- There is no "soft delete" or recycle bin — deletion is final
- Backups are taken periodically for disaster recovery; deleted user data is removed from backups in the next backup cycle (typically within 7 days)

---

## 5. How to Export or Delete Your Data

You are always in control of your data:

**Export your data:**
Settings → My Data → Download This Month (or Download Full History)
This gives you a CSV file with all your expense records.

**Delete your account:**
Settings → My Account → Danger Zone → Delete My Account
Type DELETE to confirm. Everything is deleted immediately and permanently.

---

## 6. Who Can See Your Data

- **Only you** — all database queries are scoped to your user ID. No user can access another user's expenses, income, or settings under any circumstances.
- **The app administrator** can see basic account metadata (email address, registration date, last login) for operational purposes such as user support. The administrator cannot access your expense data, income amounts, or budget settings without direct database access.
- **No third parties** receive your data except Anthropic (see Section 3 above) and Railway (the hosting platform, which stores the encrypted database volume but has no application-level access to your data).

---

## 7. Security

- All connections use HTTPS — data is encrypted in transit
- Passwords are hashed using bcrypt (a deliberately slow algorithm that resists brute-force attacks)
- JWT tokens expire after 8 hours — you are automatically logged out
- Each user's data is isolated at the query level — there is no way to retrieve another user's data through the API

---

## 8. Contact

If you have questions about your data or this privacy notice:

- Raise an issue on the GitHub repository: https://github.com/gitdebashish123/expenditure-tracker
- Or contact the administrator directly

---

*Last updated: May 2026*
*This notice applies to the SpendSense instance hosted at https://frontend-production-22a3.up.railway.app*
