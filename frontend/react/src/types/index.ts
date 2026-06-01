// All TypeScript types matching the FastAPI backend models
// Reference: design/TRACK_2_REACT_MIGRATION_PROMPT.md — Data Models section

export interface User {
  id: number;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  last_login: string | null;
  onboarding_complete: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface Expense {
  id: number;
  date: string; // "YYYY-MM-DD"
  vendor: string;
  amount: number;
  category: string;
  note: string | null;
  is_fixed: boolean;
  paid: boolean;
  month_key: string;
  fixed_template_id: number | null;
}

export interface FixedExpense extends Expense {
  is_fixed: true;
}

export interface FixedExpenseTemplate {
  id: number;
  name: string;
  category: string;
  amount: number;
  is_active: boolean;
  sort_order: number;
  due_day: number | null;
  template_type: "fixed" | "pool";
  created_at: string;
}

export interface PoolEntry {
  id: number;
  pool_template_id: number;
  month_key: string;
  label: string;
  amount: number;
  paid: boolean;
  paid_date: string | null;
  note: string | null;
}

export interface Pool {
  id: number;
  name: string;
  category: string;
  entries: PoolEntry[];
  paid_total: number;
  unpaid_total: number;
  entry_count: number;
}

export interface Summary {
  balance: {
    remaining: number;
    total_income: number;
    fixed_paid_total: number;
    fixed_unpaid_total: number;
    variable_total: number;
  };
  categories: Array<{ category: string; spent: number }>;
  warnings: Array<{ level: "warning" | "danger"; message: string }>;
  fixed_progress: { paid: number; total: number };
}

export interface BudgetLimit {
  id: number;
  category: string;
  limit_amount: number;
}

export interface IncomeEntry {
  id: number;
  source: string;
  amount: number;
  month_key: string;
  note: string | null;
}

export interface ExpenseTemplate {
  id: number;
  name: string;
  vendor: string;
  category: string;
  amount: number;
  use_count: number;
}

export interface ProjectionItem {
  category: string;
  spent: number;
  limit: number;
  projected: number;
  pct_spent: number;
  pct_projected: number;
  status: "safe" | "warning" | "danger" | "over";
  days_left: number;
  daily_rate: number;
}

export interface DueReminder {
  vendor: string;
  amount: number;
  due_day: number;
  days_overdue: number;
}

export interface AdminStats {
  total_users: number;
  active_users: number;
  total_expenses: number;
}

export interface AdminUser {
  id: number;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  last_login: string | null;
  onboarding_complete: boolean;
  expense_count: number;
}
