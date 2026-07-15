"use client";

import Image from "next/image";

export default function Dashboard() {
  return (
    <div className="text-text-primary">
      {/* Header */}
      <header className="flex justify-between items-end mb-8">
        <div>
          <h2 className="font-display text-4xl font-black text-text-primary tracking-tighter">Overview</h2>
          <p className="font-sans text-lg text-text-secondary mt-2">Welcome back, System Controller.</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="glass-panel px-4 py-2 rounded-full flex items-center gap-2 text-text-secondary">
            <span className="material-symbols-outlined text-[20px]">calendar_today</span>
            <span className="font-sans text-sm">{new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
          </div>
        </div>
      </header>

      {/* Metrics Grid */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Metric 1 */}
        <div className="metric-card p-6 rounded-xl flex flex-col justify-between">
          <div className="flex justify-between items-start mb-4">
            <div className="w-12 h-12 rounded-full bg-surface-container-highest flex items-center justify-center text-primary-container">
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>group</span>
            </div>
            <span className="text-[#0072d7] flex items-center font-sans text-xs uppercase tracking-widest font-bold">
              <span className="material-symbols-outlined text-[16px]">arrow_upward</span> 12%
            </span>
          </div>
          <div>
            <p className="font-sans text-xs uppercase tracking-widest font-bold text-text-secondary mb-1">Total Users</p>
            <h3 className="font-display text-3xl font-bold text-text-primary">2.4M</h3>
          </div>
        </div>

        {/* Metric 2 */}
        <div className="metric-card p-6 rounded-xl flex flex-col justify-between">
          <div className="flex justify-between items-start mb-4">
            <div className="w-12 h-12 rounded-full bg-surface-container-highest flex items-center justify-center text-primary-container">
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>movie</span>
            </div>
            <span className="text-[#0072d7] flex items-center font-sans text-xs uppercase tracking-widest font-bold">
              <span className="material-symbols-outlined text-[16px]">arrow_upward</span> 5%
            </span>
          </div>
          <div>
            <p className="font-sans text-xs uppercase tracking-widest font-bold text-text-secondary mb-1">Total Movies</p>
            <h3 className="font-display text-3xl font-bold text-text-primary">8,432</h3>
          </div>
        </div>

        {/* Metric 3 */}
        <div className="metric-card p-6 rounded-xl flex flex-col justify-between">
          <div className="flex justify-between items-start mb-4">
            <div className="w-12 h-12 rounded-full bg-surface-container-highest flex items-center justify-center text-primary-container">
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>tv</span>
            </div>
            <span className="text-on-secondary-container flex items-center font-sans text-xs uppercase tracking-widest font-bold">
              <span className="material-symbols-outlined text-[16px]">horizontal_rule</span> 0%
            </span>
          </div>
          <div>
            <p className="font-sans text-xs uppercase tracking-widest font-bold text-text-secondary mb-1">Total Series</p>
            <h3 className="font-display text-3xl font-bold text-text-primary">1,204</h3>
          </div>
        </div>
      </section>

      {/* Data Table Section */}
      <section className="glass-panel rounded-xl overflow-hidden shadow-2xl">
        <div className="p-6 border-b border-white/5 flex justify-between items-center bg-[#1a0908]/80">
          <h3 className="font-display text-2xl font-bold text-text-primary">Recent Uploads</h3>
          <button className="text-text-secondary hover:text-primary-container transition-colors font-sans text-xs uppercase tracking-widest font-bold flex items-center gap-1">
            View All <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#1a0908]/50 border-b border-white/10">
                <th className="p-4 font-sans text-xs uppercase tracking-widest text-text-secondary font-medium">Title</th>
                <th className="p-4 font-sans text-xs uppercase tracking-widest text-text-secondary font-medium">Type</th>
                <th className="p-4 font-sans text-xs uppercase tracking-widest text-text-secondary font-medium">Status</th>
                <th className="p-4 font-sans text-xs uppercase tracking-widest text-text-secondary font-medium">Date</th>
                <th className="p-4 font-sans text-xs uppercase tracking-widest text-text-secondary font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="font-sans text-base">
              <tr className="data-table-row">
                <td className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-14 bg-surface-container-highest rounded overflow-hidden relative">
                      <Image 
                        className="object-cover" 
                        alt="Poster"
                        fill
                        src="https://lh3.googleusercontent.com/aida-public/AB6AXuBdhd23yUJiQLiylw5M4INBBHUlaJ4IuoqNbthJjpghIl2XX4fDJz-UjNUjO95_IvMej8kwvDSeeUjV-lrP34HvNWOe_gKneuExUrYR1Xiy98ug2OQdqhaERR6YgTbGrNiWunCtLOOJVh7VSrbjbl6lz09TC2rKFKSWxg7--b8TuUy7lYwC7DU89vrQd5lzNHR8ga-Zxn5_aohOQtFC78hG8z11uWQsdl7YiUDO5xATn4V_KDyKWvKirUZgQ37ehFRG5gL6Iz-OUTU" 
                      />
                    </div>
                    <span className="text-text-primary font-medium">Neon Shadows</span>
                  </div>
                </td>
                <td className="p-4 text-text-secondary">Movie</td>
                <td className="p-4">
                  <span className="px-2 py-1 bg-[#0072d7]/20 text-[#0072d7] rounded text-xs uppercase tracking-widest font-bold">PUBLISHED</span>
                </td>
                <td className="p-4 text-text-secondary text-sm">Oct 24, 2024</td>
                <td className="p-4 text-right">
                  <button className="text-text-secondary hover:text-text-primary p-2 rounded-full hover:bg-white/10 transition-colors">
                    <span className="material-symbols-outlined">more_vert</span>
                  </button>
                </td>
              </tr>
              <tr className="data-table-row">
                <td className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-14 bg-surface-container-highest rounded overflow-hidden relative">
                      <Image 
                        className="object-cover" 
                        alt="Poster"
                        fill
                        src="https://lh3.googleusercontent.com/aida-public/AB6AXuDr267LmYz-tNVR9RAECsm8SVGGfyU56yIFmgKbfuAC5Ay7X_DTnnq_klTa4iW10xHwuXyTX9gMwQbBz-uqSyGETVfLaVC9gcLvs2LeIIeeS78qFERFeeg56deinhz1wGVjdgq6olnsP0W1v8x39xTM8g5-UoybuW4Eo04kWvWNY3e5QYXdnpnCfQ9ywCPgXq3W4_XcX2vN5nelHq82a0Ezmu5OLAiykelv5ZodprWQcrl7ooh9VvSrTgMsQSBPiysC9sWQz98znNg" 
                      />
                    </div>
                    <span className="text-text-primary font-medium">The Crown's Shadow</span>
                  </div>
                </td>
                <td className="p-4 text-text-secondary">Series</td>
                <td className="p-4">
                  <span className="px-2 py-1 bg-[#F5C518]/20 text-[#F5C518] rounded text-xs uppercase tracking-widest font-bold">PROCESSING</span>
                </td>
                <td className="p-4 text-text-secondary text-sm">Oct 23, 2024</td>
                <td className="p-4 text-right">
                  <button className="text-text-secondary hover:text-text-primary p-2 rounded-full hover:bg-white/10 transition-colors">
                    <span className="material-symbols-outlined">more_vert</span>
                  </button>
                </td>
              </tr>
              <tr className="data-table-row">
                <td className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-14 bg-surface-container-highest rounded overflow-hidden relative">
                      <Image 
                        className="object-cover" 
                        alt="Poster"
                        fill
                        src="https://lh3.googleusercontent.com/aida-public/AB6AXuCJUHM44j81JazT3jrV8dHkDLrmcUgA6N63AFFr7gh-WuWJovdPKoVlG8p-7uuzhpT2GlRTMQzA2cKUWI8SoU37mXq8kiAwHNGzw2rLPVHCLlRdbDOg6yjsHyB70pvtfmn1LzGjoPlzNpvD3Uk01r9HIRsjqiyfKqmwddS2bLlqNz8IK-9CnuDHv4VvXZkiJYifVo3zGpUW-1vJeSl1W95FWBaKMbvDQEYt_oNCYmb1QzXw-nPrFIS6eKblSHtxdKNyPdnlDXKPIjg" 
                      />
                    </div>
                    <span className="text-text-primary font-medium">Whispers in the Dark</span>
                  </div>
                </td>
                <td className="p-4 text-text-secondary">Movie</td>
                <td className="p-4">
                  <span className="px-2 py-1 bg-surface-container-highest text-text-secondary rounded text-xs uppercase tracking-widest font-bold">DRAFT</span>
                </td>
                <td className="p-4 text-text-secondary text-sm">Oct 21, 2024</td>
                <td className="p-4 text-right">
                  <button className="text-text-secondary hover:text-text-primary p-2 rounded-full hover:bg-white/10 transition-colors">
                    <span className="material-symbols-outlined">more_vert</span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
