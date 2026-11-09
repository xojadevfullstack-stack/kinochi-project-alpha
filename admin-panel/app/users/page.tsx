"use client";

import { useState, useEffect } from "react";
import { fetchApi } from "@/lib/api";

interface UserItem {
  id: number;
  telegram_id: number;
  username: string | null;
  first_name: string | null;
  last_name: string | null;
  is_admin: boolean;
  is_banned: boolean;
  joined_at: string;
  last_active_at: string;
}

export default function UsersAdminPage() {
  const [users, setUsers] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "banned" | "admin">("all");
  const [total, setTotal] = useState(0);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      const res = await fetchApi(`/users?skip=0&limit=100`);
      setUsers(res.items || []);
      setTotal(res.total || 0);
    } catch (e: any) {
      console.error("Error fetching users:", e);
      setErrorMsg(e.message || "Foydalanuvchilarni yuklashda xatolik");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleToggleBan = async (user: UserItem) => {
    const action = user.is_banned ? "unban" : "ban";
    const confirmText = user.is_banned
      ? `Foydalanuvchi @${user.username || user.telegram_id} ni blokdan chiqarishni xohlaysizmi?`
      : `Foydalanuvchi @${user.username || user.telegram_id} ni bloklashni xohlaysizmi?`;

    if (!confirm(confirmText)) return;

    try {
      setActionLoading(user.telegram_id);
      await fetchApi(`/users/${user.telegram_id}/${action}`, {
        method: "POST",
      });
      // Update local state
      setUsers((prev) =>
        prev.map((u) =>
          u.telegram_id === user.telegram_id ? { ...u, is_banned: !u.is_banned } : u
        )
      );
    } catch (err: any) {
      alert("Xatolik: " + err.message);
    } finally {
      setActionLoading(null);
    }
  };

  const filteredUsers = users.filter((u) => {
    if (statusFilter === "active" && u.is_banned) return false;
    if (statusFilter === "banned" && !u.is_banned) return false;
    if (statusFilter === "admin" && !u.is_admin) return false;

    if (!search.trim()) return true;
    const q = search.toLowerCase().trim();
    const tgStr = String(u.telegram_id);
    const un = (u.username || "").toLowerCase();
    const fn = (u.first_name || "").toLowerCase();
    const ln = (u.last_name || "").toLowerCase();
    return tgStr.includes(q) || un.includes(q) || fn.includes(q) || ln.includes(q);
  });

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Title & Stats */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
            Foydalanuvchilar
          </h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">
            Bot va veb-sayt foydalanuvchilari boshqaruvi va moderatsiyasi
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="bg-surface-container-high px-4 py-2 rounded-xl border border-white/5 text-center">
            <span className="text-xs text-text-secondary block">Jami a'zolar</span>
            <span className="text-lg font-bold text-primary-container">{total}</span>
          </div>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="metric-card p-4 rounded-2xl mb-6 space-y-3">
        <div className="relative">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary text-lg">
            search
          </span>
          <input
            type="text"
            placeholder="Telegram ID, @username yoki ism bo'yicha qidirish..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-surface-container-lowest border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-text-primary placeholder:text-text-secondary focus:ring-2 focus:ring-primary-container focus:border-primary-container transition"
          />
        </div>

        {/* Status Filter Tabs (Cinematic Red) */}
        <div className="flex items-center gap-2 flex-wrap pt-1">
          <span className="text-xs text-text-secondary mr-1">Holati:</span>
          {(
            [
              { id: "all", label: `Barchasi (${users.length})` },
              { id: "active", label: `Faol (${users.filter((u) => !u.is_banned).length})` },
              { id: "banned", label: `Bloklangan (${users.filter((u) => u.is_banned).length})` },
              { id: "admin", label: `Adminlar (${users.filter((u) => u.is_admin).length})` },
            ] as const
          ).map((tab) => {
            const isActive = statusFilter === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setStatusFilter(tab.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition border cursor-pointer ${
                  isActive
                    ? "bg-primary-container text-white border-primary-container font-bold shadow-md shadow-primary-container/20"
                    : "bg-surface-container-lowest hover:bg-white/5 text-text-secondary hover:text-white border-white/10"
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {errorMsg && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {errorMsg}
        </div>
      )}

      {/* Users Table */}
      <div className="metric-card rounded-2xl overflow-hidden border border-white/5">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-white/5 bg-white/[0.02] text-xs font-medium text-text-secondary">
                <th className="py-3 px-4">Foydalanuvchi</th>
                <th className="py-3 px-4">Telegram ID</th>
                <th className="py-3 px-4">Holat</th>
                <th className="py-3 px-4">Rol</th>
                <th className="py-3 px-4">Qo'shilgan sana</th>
                <th className="py-3 px-4 text-right">Amallar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-text-secondary">
                    Yuklanmoqda...
                  </td>
                </tr>
              ) : filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-text-secondary">
                    Foydalanuvchilar topilmadi
                  </td>
                </tr>
              ) : (
                filteredUsers.map((u) => {
                  const fullName = [u.first_name, u.last_name].filter(Boolean).join(" ") || "—";
                  return (
                    <tr key={u.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-medium text-text-primary">{fullName}</div>
                        {u.username && (
                          <div className="text-xs text-text-secondary">@{u.username}</div>
                        )}
                      </td>
                      <td className="py-3 px-4 font-mono text-xs text-text-secondary">
                        {u.telegram_id}
                      </td>
                      <td className="py-3 px-4">
                        {u.is_banned ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">
                            Bloklangan
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            Faol
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {u.is_admin ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary-container/10 text-primary-container border border-primary-container/20">
                            Admin
                          </span>
                        ) : (
                          <span className="text-xs text-text-secondary">A'zo</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-xs text-text-secondary">
                        {u.joined_at ? new Date(u.joined_at).toLocaleDateString("uz-UZ") : "—"}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleToggleBan(u)}
                          disabled={actionLoading === u.telegram_id}
                          className={`text-xs px-3 py-1.5 rounded-lg border transition-colors min-h-[32px] inline-flex items-center gap-1.5 ${
                            u.is_banned
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20"
                              : "bg-red-500/10 text-red-400 border-red-500/20 hover:bg-red-500/20"
                          }`}
                        >
                          <span className="material-symbols-outlined text-[15px]">
                            {u.is_banned ? "lock_open" : "block"}
                          </span>
                          {u.is_banned ? "Blokdan chiqarish" : "Bloklash"}
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
