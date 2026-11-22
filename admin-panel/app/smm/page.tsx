"use client";

import { useEffect, useState } from "react";
import { API_URL, fetchApi } from "@/lib/api";

type SmmSettings = {
  mode: "SEMI_AUTO" | "FULL_AUTO";
  clip_duration_sec: number;
  daily_limit: number;
  schedule_hours: string[];
  enabled_platforms: string[];
  auto_pick_from_catalog: boolean;
  copyright_shield: boolean;
  bot_username: string;
  telegram_channel_id: string | null;
};

type PlatformState = { enabled: boolean; status: string; post_id?: string | null; error?: string | null };

type SmmJob = {
  id: number;
  media_type: "movie" | "series";
  movie_code: string;
  title: string;
  start_sec: number;
  duration_sec: number;
  clip_path: string | null;
  caption: string | null;
  status: string;
  platforms_status: Record<string, PlatformState>;
};

const ALL_PLATFORMS = ["telegram", "instagram", "facebook", "youtube", "tiktok"] as const;
const STATUS_TABS = ["all", "waiting_approval", "scheduled", "publishing", "completed", "failed", "rejected"] as const;

export default function SmmStudioPage() {
  const [settings, setSettings] = useState<SmmSettings | null>(null);
  const [jobs, setJobs] = useState<SmmJob[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);
  const [recutStart, setRecutStart] = useState<Record<number, string>>({});
  const [newJob, setNewJob] = useState({ movie_code: "", title: "", start_sec: "300", duration_sec: "45" });

  const baseHost = API_URL.replace(/\/api\/v1\/?$/, "");

  const loadAll = async (statusVal = filter) => {
    try {
      const [cfg, list] = await Promise.all([
        fetchApi("/smm/settings"),
        fetchApi(`/smm/jobs?status=${statusVal}`),
      ]);
      setSettings(cfg);
      setJobs(Array.isArray(list) ? list : []);
    } catch (e: unknown) {
      setNotice(e instanceof Error ? e.message : "Ma'lumotlarni yuklashda xatolik");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll(filter);
  }, [filter]);

  const saveSettings = async (patch: Partial<SmmSettings>) => {
    try {
      const updated = await fetchApi("/smm/settings", { method: "PUT", body: JSON.stringify(patch) });
      setSettings(updated);
      setNotice("Sozlamalar saqlandi");
    } catch (e: unknown) {
      setNotice(e instanceof Error ? e.message : "Saqlashda xato");
    }
  };

  const togglePlatform = (plat: string) => {
    if (!settings) return;
    const exists = settings.enabled_platforms.includes(plat);
    const next = exists ? settings.enabled_platforms.filter((p) => p !== plat) : [...settings.enabled_platforms, plat];
    saveSettings({ enabled_platforms: next });
  };

  const createJob = async () => {
    if (!newJob.movie_code.trim() || !newJob.title.trim()) return;
    await fetchApi("/smm/jobs", {
      method: "POST",
      body: JSON.stringify({
        media_type: "movie",
        movie_code: newJob.movie_code.trim(),
        title: newJob.title.trim(),
        start_sec: Number(newJob.start_sec) || 0,
        duration_sec: Number(newJob.duration_sec) || 45,
      }),
    });
    setNewJob({ movie_code: "", title: "", start_sec: "300", duration_sec: "45" });
    await loadAll();
  };

  const runAction = async (id: number, action: "approve" | "reject" | "recut", body?: object) => {
    await fetchApi(`/smm/jobs/${id}/${action}`, { method: "POST", body: body ? JSON.stringify(body) : undefined });
    await loadAll();
  };

  if (loading) return <div className="p-6 text-text-secondary">SMM Studio yuklanmoqda...</div>;

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <span className="material-symbols-outlined text-[#E50914]">movie_edit</span>
            SMM Video Autopilot Studio
          </h1>
          <p className="text-sm text-text-secondary mt-1">9:16 Reels / Shorts kesish, reklama blur va 5 tarmoqqa avto-post</p>
        </div>

        {settings && (
          <div className="flex items-center gap-2 bg-surface-container-lowest p-1.5 rounded-xl border border-white/10">
            {(["SEMI_AUTO", "FULL_AUTO"] as const).map((m) => (
              <button
                key={m}
                onClick={() => saveSettings({ mode: m })}
                className={`px-4 py-2 rounded-lg text-xs font-bold transition ${
                  settings.mode === m ? "bg-[#E50914] text-white" : "text-text-secondary hover:text-white"
                }`}
              >
                {m === "SEMI_AUTO" ? "Yarim-Avtomat (Ruxsat bilan)" : "100% Avtonom"}
              </button>
            ))}
          </div>
        )}
      </div>

      {notice && <div className="px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-sm text-white">{notice}</div>}

      {settings && (
        <div className="glass-panel rounded-2xl p-4 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <label className="text-xs text-text-secondary">
              Kunlik limit
              <input
                type="number"
                value={settings.daily_limit}
                onChange={(e) => setSettings({ ...settings, daily_limit: Number(e.target.value) })}
                className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white"
              />
            </label>
            <label className="text-xs text-text-secondary">
              Klip davomiyligi (s)
              <input
                type="number"
                value={settings.clip_duration_sec}
                onChange={(e) => setSettings({ ...settings, clip_duration_sec: Number(e.target.value) })}
                className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white"
              />
            </label>
            <label className="text-xs text-text-secondary">
              Telegram Kanal ID
              <input
                type="text"
                placeholder="-100..."
                value={settings.telegram_channel_id || ""}
                onChange={(e) => setSettings({ ...settings, telegram_channel_id: e.target.value })}
                className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white"
              />
            </label>
            <div className="flex items-end">
              <button
                onClick={() => saveSettings({ daily_limit: settings.daily_limit, clip_duration_sec: settings.clip_duration_sec, telegram_channel_id: settings.telegram_channel_id })}
                className="w-full py-2 px-4 rounded-lg bg-[#E50914] hover:bg-red-700 text-white text-sm font-semibold"
              >
                Saqlash
              </button>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-white/5">
            <span className="text-xs text-text-secondary mr-2">Faol tarmoqlar:</span>
            {ALL_PLATFORMS.map((p) => {
              const active = settings.enabled_platforms.includes(p);
              return (
                <button
                  key={p}
                  onClick={() => togglePlatform(p)}
                  className={`px-3 py-1 rounded-full text-xs font-medium capitalize border ${
                    active ? "bg-[#E50914] border-[#E50914] text-white" : "border-white/15 text-text-secondary"
                  }`}
                >
                  {p}
                </button>
              );
            })}
          </div>
        </div>
      )}

      <div className="glass-panel rounded-2xl p-4 grid grid-cols-1 sm:grid-cols-5 gap-3">
        <input placeholder="Kino kodi (#889)" value={newJob.movie_code} onChange={(e) => setNewJob({ ...newJob, movie_code: e.target.value })} className="bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white" />
        <input placeholder="Kino nomi (faqat admin ko'radi)" value={newJob.title} onChange={(e) => setNewJob({ ...newJob, title: e.target.value })} className="bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white sm:col-span-2" />
        <input placeholder="Boshlanish (s)" value={newJob.start_sec} onChange={(e) => setNewJob({ ...newJob, start_sec: e.target.value })} className="bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white" />
        <button onClick={createJob} className="py-2 px-4 rounded-lg bg-[#E50914] hover:bg-red-700 text-white text-sm font-semibold">+ Navbatga qo'shish</button>
      </div>

      <div className="flex flex-wrap gap-2">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${filter === tab ? "bg-[#E50914] text-white" : "bg-white/5 text-text-secondary hover:text-white"}`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {jobs.map((job) => (
          <div key={job.id} className="metric-card rounded-2xl p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-[#E50914] text-white">#{job.movie_code}</span>
              <span className="text-xs text-text-secondary uppercase">{job.status}</span>
            </div>
            <h3 className="text-sm font-semibold text-white truncate">{job.title}</h3>
            {job.clip_path ? (
              <video src={`${baseHost}/${job.clip_path}`} controls className="w-full max-h-72 rounded-xl bg-black object-contain" />
            ) : (
              <div className="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-xs text-text-secondary">
                Video klip Render worker tomonidan kesilishi kutilmoqda...
              </div>
            )}
            <div className="text-xs text-text-secondary">Vaqt: {job.start_sec}s (+{job.duration_sec}s)</div>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(job.platforms_status || {}).map(([plat, st]) => (
                <span key={plat} className={`text-[10px] px-2 py-0.5 rounded-full border ${st.status === "published" ? "border-emerald-500 text-emerald-400" : st.status === "failed" ? "border-[#E50914] text-red-400" : "border-white/15 text-text-secondary"}`}>
                  {plat}: {st.status}
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <input placeholder="Yangi soniya" value={recutStart[job.id] ?? String(job.start_sec)} onChange={(e) => setRecutStart({ ...recutStart, [job.id]: e.target.value })} className="w-24 bg-black/40 border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white" />
              <button onClick={() => runAction(job.id, "recut", { start_sec: Number(recutStart[job.id] ?? job.start_sec), duration_sec: job.duration_sec })} className="px-2.5 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-xs text-white">Qayta kesish</button>
            </div>
            <div className="grid grid-cols-3 gap-2 pt-1">
              <button disabled={!job.clip_path} onClick={() => runAction(job.id, "approve", { publish_now: false })} className="py-1.5 rounded-lg bg-white/10 hover:bg-white/20 disabled:opacity-40 disabled:cursor-not-allowed text-xs text-white font-medium">Tasdiqlash</button>
              <button disabled={!job.clip_path} onClick={() => runAction(job.id, "approve", { publish_now: true })} className="py-1.5 rounded-lg bg-[#E50914] hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed text-xs text-white font-semibold">Hozir chiqar</button>
              <button onClick={() => runAction(job.id, "reject")} className="py-1.5 rounded-lg bg-black/40 hover:bg-white/10 text-xs text-text-secondary">Rad etish</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
