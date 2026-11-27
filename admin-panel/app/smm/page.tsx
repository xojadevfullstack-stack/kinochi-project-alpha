"use client";

import { useEffect, useRef, useState } from "react";
import { API_URL, fetchApi } from "@/lib/api";
import { cleanMediaCode, formatSmmStatusLabel, isLatestRequest, shouldPollProgress } from "@/lib/smmHelpers.mjs";

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
  admin_telegram_id: string | null;
};

type PlatformState = { enabled: boolean; status: string; post_id?: string | null; error?: string | null };

type SmmJob = {
  id: number;
  media_type: "movie" | "series" | "episode";
  movie_code: string;
  title: string;
  clip_mode?: "scene" | "facts";
  hook_text?: string | null;
  start_sec: number;
  duration_sec: number;
  clip_path: string | null;
  caption: string | null;
  status: string;
  progress_pct?: number;
  progress_stage?: string | null;
  platforms_status: Record<string, PlatformState>;
};

type SmmProgressSnapshot = {
  cycle1: {
    in_progress: number;
    queued: number;
    published: number;
    needs_review: number;
    current_item: { id: number; title: string; source: string; media_type: string } | null;
  };
  cycle2: {
    generating: number;
    waiting_approval: number;
    scheduled: number;
    publishing: number;
    completed: number;
    failed: number;
    active_jobs: { id: number; media_type: string; movie_code: string; title: string; status: string; progress_pct: number; progress_stage: string }[];
  };
  worker?: {
    enabled?: boolean;
    running?: boolean;
    has_smm_session?: boolean;
    last_tick_at?: string | null;
    last_error?: string | null;
  };
};

const ALL_PLATFORMS = ["telegram", "instagram", "facebook", "youtube", "tiktok"] as const;
const STATUS_TABS = ["all", "generating", "waiting_approval", "scheduled", "publishing", "completed", "failed", "rejected"] as const;

export default function SmmStudioPage() {
  const [settings, setSettings] = useState<SmmSettings | null>(null);
  const [jobs, setJobs] = useState<SmmJob[]>([]);
  const [progress, setProgress] = useState<SmmProgressSnapshot | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);
  const [recutStart, setRecutStart] = useState<Record<number, string>>({});
  const [brokenVideo, setBrokenVideo] = useState<Record<number, boolean>>({});
  const [newJob, setNewJob] = useState({ media_type: "movie" as "movie" | "episode", movie_code: "", title: "", hook_text: "", start_sec: "300", duration_sec: "28" });
  const loadSeqRef = useRef(0);

  const loadAll = async (statusVal = filter) => {
    const seq = ++loadSeqRef.current;
    try {
      const [cfg, list, prog] = await Promise.all([
        fetchApi("/smm/settings"),
        fetchApi(`/smm/jobs?status=${statusVal}`),
        fetchApi("/smm/progress").catch(() => null),
      ]);
      if (!isLatestRequest(seq, loadSeqRef.current)) return;
      setSettings(cfg);
      setJobs(Array.isArray(list) ? list : []);
      if (prog) setProgress(prog);
    } catch (e: unknown) {
      if (isLatestRequest(seq, loadSeqRef.current)) {
        setNotice(e instanceof Error ? e.message : "Ma'lumotlarni yuklashda xatolik");
      }
    } finally {
      if (isLatestRequest(seq, loadSeqRef.current)) setLoading(false);
    }
  };

  useEffect(() => {
    loadAll(filter);
  }, [filter]);

  useEffect(() => {
    const active = shouldPollProgress(progress, jobs);
    const ms = active ? 4000 : 15000;
    const timer = setInterval(() => {
      loadAll(filter);
    }, ms);
    return () => clearInterval(timer);
  }, [filter, progress, jobs]);

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
    const code = cleanMediaCode(newJob.movie_code);
    const title = newJob.title.trim();
    if (!code || !title) {
      setNotice("Kino/Qism kodi va nomini kiriting");
      return;
    }
    try {
      await fetchApi("/smm/jobs", {
        method: "POST",
        body: JSON.stringify({
          media_type: newJob.media_type,
          movie_code: code,
          title,
          hook_text: newJob.hook_text.trim() || null,
          start_sec: Number(newJob.start_sec) || 0,
          duration_sec: Number(newJob.duration_sec) || settings?.clip_duration_sec || 28,
          generate: true,
        }),
      });
      setNewJob({ media_type: "movie", movie_code: "", title: "", hook_text: "", start_sec: "300", duration_sec: String(settings?.clip_duration_sec || 28) });
      setNotice(`#${code} klipp tayyorlash navbatiga qo'shildi`);
      await loadAll();
    } catch (e: unknown) {
      setNotice(e instanceof Error ? e.message : "Vazifa yaratishda xatolik");
    }
  };

  const runAction = async (id: number, action: "approve" | "reject" | "recut", body?: { start_sec?: number; duration_sec?: number; publish_now?: boolean }) => {
    try {
      if (action === "recut" && typeof body?.start_sec === "number") {
        setJobs((prev) => prev.map((j) => (j.id === id ? { ...j, start_sec: body.start_sec!, status: "generating", progress_pct: 0 } : j)));
        setBrokenVideo((prev) => ({ ...prev, [id]: false }));
      }
      await fetchApi(`/smm/jobs/${id}/${action}`, { method: "POST", body: body ? JSON.stringify(body) : undefined });
      setNotice(`Vazifa #${id} bo'yicha amal bajarildi`);
      await loadAll();
    } catch (e: unknown) {
      setNotice(e instanceof Error ? e.message : "Amalni bajarishda xatolik");
    }
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

      {progress && (
        <div className="glass-panel rounded-2xl p-4 space-y-3 border border-white/10">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="space-y-0.5">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <span className="inline-block w-2 h-2 rounded-full bg-[#E50914] animate-pulse" />
                Jonli Progress (1-sikl Autopilot &amp; 2-sikl SMM Worker)
              </h2>
              {progress.worker && (
                <div className="text-[11px] text-text-secondary">
                  Render Worker: <b className={progress.worker.enabled && progress.worker.running ? "text-emerald-400" : "text-[#E50914]"}>{progress.worker.enabled ? (progress.worker.running ? "Faol" : "To'xtagan") : "O'chiq (SMM_AUTOPILOT_ENABLED != true)"}</b>
                  {" | "}SMM Session: <b className="text-white">{progress.worker.has_smm_session ? "Bor" : "Yo'q"}</b>
                  {progress.worker.last_error ? ` | Xato: ${progress.worker.last_error}` : ""}
                </div>
              )}
            </div>
            <button onClick={() => loadAll(filter)} className="px-3 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-xs text-white">
              Yangilash
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="rounded-xl bg-black/30 border border-white/10 p-3 space-y-1.5">
              <div className="text-xs font-semibold text-white">1-sikl: Katalog Autopilot</div>
              <div className="text-xs text-text-secondary">
                Navbatda: <b className="text-white">{progress.cycle1.queued}</b> | Nashr qilingan: <b className="text-white">{progress.cycle1.published}</b> | Karantin: <b className="text-white">{progress.cycle1.needs_review}</b>
              </div>
              {progress.cycle1.current_item ? (
                <div className="text-xs text-emerald-400">
                  Hozir yuklanmoqda: {progress.cycle1.current_item.title} ({progress.cycle1.current_item.source})
                </div>
              ) : (
                <div className="text-xs text-text-secondary">Hozircha faol yuklash yo&apos;q</div>
              )}
            </div>
            <div className="rounded-xl bg-black/30 border border-white/10 p-3 space-y-1.5">
              <div className="text-xs font-semibold text-white">2-sikl: SMM Klipp Tayyorlash</div>
              <div className="text-xs text-text-secondary">
                Kesilmoqda: <b className="text-white">{progress.cycle2.generating}</b> | Tasdiqda: <b className="text-white">{progress.cycle2.waiting_approval}</b> | Navbatda: <b className="text-white">{progress.cycle2.scheduled}</b> | Tayyor: <b className="text-white">{progress.cycle2.completed}</b>
              </div>
              {progress.cycle2.active_jobs.length > 0 ? (
                <div className="space-y-2 pt-1">
                  {progress.cycle2.active_jobs.map((aj) => (
                    <div key={aj.id} className="space-y-1">
                      <div className="flex justify-between text-[11px] text-white">
                        <span className="truncate">#{aj.movie_code} {aj.title} — {aj.progress_stage || formatSmmStatusLabel(aj.status)}</span>
                        <span>{aj.progress_pct}%</span>
                      </div>
                      <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden">
                        <div className="h-full bg-[#E50914] transition-all" style={{ width: `${Math.max(5, aj.progress_pct)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-xs text-text-secondary">Hozircha faol klipp kesish jarayoni yo&apos;q</div>
              )}
            </div>
          </div>
        </div>
      )}

      {settings && (
        <div className="glass-panel rounded-2xl p-4 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
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
            <label className="text-xs text-text-secondary">
              Admin Telegram ID (preview)
              <input
                type="text"
                placeholder="123456789 (bo'sh = ADMIN_IDS)"
                value={settings.admin_telegram_id || ""}
                onChange={(e) => setSettings({ ...settings, admin_telegram_id: e.target.value })}
                className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white"
              />
            </label>
            <div className="flex items-end">
              <button
                onClick={() => saveSettings({ daily_limit: settings.daily_limit, clip_duration_sec: settings.clip_duration_sec, telegram_channel_id: settings.telegram_channel_id, admin_telegram_id: settings.admin_telegram_id || null })}
                className="w-full py-2 px-4 rounded-lg bg-[#E50914] hover:bg-red-700 text-white text-sm font-semibold"
              >
                Saqlash
              </button>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-white/5">
            <div className="flex flex-wrap items-center gap-2">
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
            <label className="flex items-center gap-2 text-xs text-text-secondary cursor-pointer">
              <input
                type="checkbox"
                checked={settings.copyright_shield}
                onChange={(e) => saveSettings({ copyright_shield: e.target.checked })}
                className="accent-[#E50914]"
              />
              Copyright Shield (tezlik/rang)
            </label>
          </div>
        </div>
      )}

      <div className="glass-panel rounded-2xl p-4 grid grid-cols-1 sm:grid-cols-6 gap-3">
        <select
          value={newJob.media_type}
          onChange={(e) => setNewJob({ ...newJob, media_type: e.target.value as "movie" | "episode" })}
          className="bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white"
        >
          <option value="movie">Kino</option>
          <option value="episode">Serial qismi</option>
        </select>
        <input placeholder="Kod (#3956)" value={newJob.movie_code} onChange={(e) => setNewJob({ ...newJob, movie_code: e.target.value })} className="bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white" />
        <input placeholder="Nomi (faqat admin ko'radi)" value={newJob.title} onChange={(e) => setNewJob({ ...newJob, title: e.target.value })} className="bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white sm:col-span-2" />
        <input placeholder="Hook matn (ixtiyoriy)" value={newJob.hook_text} onChange={(e) => setNewJob({ ...newJob, hook_text: e.target.value })} className="bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white" />
        <button onClick={createJob} className="py-2 px-4 rounded-lg bg-[#E50914] hover:bg-red-700 text-white text-sm font-semibold">+ Navbatga qo&apos;shish</button>
      </div>

      <div className="flex flex-wrap gap-2">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${filter === tab ? "bg-[#E50914] text-white" : "bg-white/5 text-text-secondary hover:text-white"}`}
          >
            {formatSmmStatusLabel(tab)}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {jobs.map((job) => (
          <div key={job.id} className="metric-card rounded-2xl p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-[#E50914] text-white">#{job.movie_code}</span>
              <span className="text-xs text-text-secondary uppercase">{formatSmmStatusLabel(job.status)}</span>
            </div>
            <h3 className="text-sm font-semibold text-white truncate">{job.title}</h3>
            {job.hook_text && <div className="text-[11px] text-white/80 italic truncate">&ldquo;{job.hook_text}&rdquo;</div>}
            {job.clip_path && !brokenVideo[job.id] ? (
              <video
                src={`${API_URL}/smm/jobs/${job.id}/video`}
                controls
                onError={() => setBrokenVideo((prev) => ({ ...prev, [job.id]: true }))}
                className="w-full max-h-72 rounded-xl bg-black object-contain"
              />
            ) : (
              <div className="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-xs text-text-secondary space-y-1.5">
                <div>
                  {brokenVideo[job.id]
                    ? "Video fayli serverda topilmadi — 'Qayta kesish' tugmasini bosing."
                    : job.progress_stage || "Video klip Render worker tomonidan kesilishi kutilmoqda..."}
                </div>
                {job.status === "generating" && (
                  <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden">
                    <div className="h-full bg-[#E50914] transition-all" style={{ width: `${Math.max(5, job.progress_pct || 0)}%` }} />
                  </div>
                )}
              </div>
            )}
            <div className="text-xs text-text-secondary">Vaqt: {job.start_sec}s (+{job.duration_sec}s)</div>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(job.platforms_status || {}).map(([plat, st]) => (
                <span
                  key={plat}
                  title={st.error || st.status}
                  className={`text-[10px] px-2 py-0.5 rounded-full border ${st.status === "published" ? "border-emerald-500 text-emerald-400" : st.status === "failed" ? "border-[#E50914] text-red-400" : "border-white/15 text-text-secondary"}`}
                >
                  {plat}: {st.status}
                </span>
              ))}
            </div>
            {Object.entries(job.platforms_status || {}).some(([, st]) => st.status === "failed" && st.error) && (
              <div className="rounded-lg bg-black/40 border border-[#E50914]/40 px-2.5 py-2 space-y-1 text-[11px] text-red-300">
                {Object.entries(job.platforms_status || {}).map(([plat, st]) =>
                  st.status === "failed" && st.error ? (
                    <div key={plat} className="break-words">
                      <b className="uppercase">{plat}:</b> {st.error}
                    </div>
                  ) : null
                )}
              </div>
            )}
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
