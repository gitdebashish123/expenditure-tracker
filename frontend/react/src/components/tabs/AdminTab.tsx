import { useEffect, useState, useCallback } from "react";
import { api } from "@/api/client";
import { fmtDate } from "@/utils/formatDate";
import { useAuth } from "@/context/AuthContext";
import { Crown, Lock, User, Shield } from "lucide-react";
import type { AdminStats, AdminUser } from "@/types";

/**
 * AdminTab — system stats + user management
 *
 * Streamlit ref: if tab6: with tab6: block in frontend/app.py
 * Only rendered when user.is_admin === true (gated in DashboardPage).
 *
 * Features:
 *   - 3 stats cards: total users, active users, total expenses
 *   - User list with crown/lock/person icon, status dot, last login,
 *     expense count, onboarding badge
 *   - Enable/Disable toggle per non-admin user
 *   - Current user row and admin rows have no action button
 *
 * Key improvement over Streamlit:
 *   - Disable/Enable shows "…" spinner during API call
 *   - Reloads full user list after toggle to reflect latest state
 */

function AdminSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="grid grid-cols-3 gap-3">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-20 bg-white/5 rounded-2xl" />
        ))}
      </div>
      {[1, 2, 3].map(i => (
        <div key={i} className="h-14 bg-white/5 rounded-xl" />
      ))}
    </div>
  );
}

export function AdminTab() {
  const { user: currentUser } = useAuth();

  const [stats,    setStats]    = useState<AdminStats | null>(null);
  const [users,    setUsers]    = useState<AdminUser[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [toggling, setToggling] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [s, u] = await Promise.all([
        api.get<AdminStats>("/admin/stats").then(r => r.data),
        api.get<AdminUser[]>("/admin/users").then(r => r.data),
      ]);
      setStats(s);
      setUsers(u);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleToggle = async (userId: number) => {
    setToggling(userId);
    try {
      await api.patch(`/admin/users/${userId}/toggle-active`);
      await load(); // full reload to reflect latest state
    } finally {
      setToggling(null);
    }
  };

  if (loading) return <AdminSkeleton />;

  return (
    <div className="space-y-6">

      {/* ── Stats cards ─────────────────────────────────── */}
      <section>
        <div className="flex items-center gap-2 mb-3">
          <Shield size={16} className="text-indigo-400" />
          <h2 className="font-syne font-bold text-white">Admin Panel</h2>
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            · Visible to admins only
          </span>
        </div>

        <div className="grid grid-cols-3 gap-3">
          {[
            { label: "Total Users",    value: stats?.total_users    ?? 0 },
            { label: "Active Users",   value: stats?.active_users   ?? 0 },
            { label: "Total Expenses", value: stats?.total_expenses ?? 0 },
          ].map(s => (
            <div
              key={s.label}
              className="bg-dark-card border border-white/10 rounded-2xl p-4 text-center"
            >
              <p className="font-syne font-bold text-white text-2xl">{s.value}</p>
              <p className="text-xs mt-1" style={{ color: "var(--text-sub)" }}>
                {s.label}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── User list ───────────────────────────────────── */}
      <section>
        <p className="text-xs mb-3" style={{ color: "var(--text-sub)" }}>
          {users.length} registered user(s)
        </p>

        <div className="space-y-2">
          {users.map(u => {
            const isSelf = u.id === currentUser?.id;

            // Icon and colour based on user state
            const Icon =
              u.is_admin  ? Crown
              : u.is_active ? User
              : Lock;
            const iconColour =
              u.is_admin  ? "#f59e0b"   // amber — crown for admin
              : u.is_active ? "#34d399" // green — person for active
              : "#ef4444";              // red   — lock for disabled

            return (
              <div
                key={u.id}
                className="flex items-center gap-3 bg-dark-card border border-white/10
                           rounded-xl px-4 py-3"
              >
                {/* Role / status icon */}
                <Icon
                  size={14}
                  style={{ color: iconColour }}
                  className="flex-shrink-0"
                />

                {/* Email + badges + meta */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-white text-sm font-medium truncate">
                      {u.email}
                    </span>
                    {/* Onboarding pending badge */}
                    {!u.onboarding_complete && (
                      <span className="text-[10px] bg-indigo-500/20 text-indigo-300
                                       px-1.5 py-0.5 rounded-full flex-shrink-0">
                        🆕 setup pending
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 mt-0.5 flex-wrap">
                    <span className={`text-xs ${
                      u.is_active ? "text-emerald-400" : "text-red-400"
                    }`}>
                      ● {u.is_active ? "Active" : "Disabled"}
                    </span>
                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                      {u.last_login
                        ? fmtDate(u.last_login.slice(0, 10))
                        : "Never logged in"
                      }
                    </span>
                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                      {u.expense_count} expenses
                    </span>
                  </div>
                </div>

                {/* Action button — hidden for self and other admins */}
                {!isSelf && !u.is_admin && (
                  <button
                    onClick={() => handleToggle(u.id)}
                    disabled={toggling === u.id}
                    className={`flex-shrink-0 text-xs font-semibold px-3 py-1.5
                                rounded-lg transition-colors disabled:opacity-40 ${
                      u.is_active
                        ? "bg-red-500/10 text-red-400 hover:bg-red-500/20"
                        : "bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"
                    }`}
                  >
                    {toggling === u.id
                      ? "…"
                      : u.is_active ? "Disable" : "Enable"
                    }
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </section>

    </div>
  );
}
