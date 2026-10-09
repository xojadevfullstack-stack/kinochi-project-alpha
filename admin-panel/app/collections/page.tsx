"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import Image from "next/image";

type Collection = {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
  poster_url?: string | null;
  banner_url?: string | null;
  is_franchise: boolean;
  is_active: boolean;
  sort_order: number;
  items_count: number;
};

type CollectionItem = {
  id: number;
  collection_id: number;
  movie_id?: number | null;
  series_id?: number | null;
  chronological_order: number;
  release_order: number;
  timeline_event_desc?: string | null;
  is_locked: boolean;
  movie?: {
    id: number;
    title: string;
    code: string;
    release_year?: number | null;
  } | null;
  series?: {
    id: number;
    title: string;
  } | null;
};

export default function CollectionsAdminPage() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(true);

  // Collection modal state
  const [showColModal, setShowColModal] = useState(false);
  const [editingColId, setEditingColId] = useState<number | null>(null);
  const [colForm, setColForm] = useState({
    name: "",
    slug: "",
    description: "",
    poster_url: "",
    banner_url: "",
    is_franchise: true,
    is_active: true,
    sort_order: 0,
  });

  // Items manager modal state
  const [selectedCol, setSelectedCol] = useState<Collection | null>(null);
  const [colItems, setColItems] = useState<CollectionItem[]>([]);
  const [loadingItems, setLoadingItems] = useState(false);
  const [addItemForm, setAddItemForm] = useState({
    movie_code_or_id: "",
    chronological_order: 1,
    release_order: 1,
    timeline_event_desc: "",
    is_locked: true,
  });

  useEffect(() => {
    loadCollections();
  }, []);

  const loadCollections = async () => {
    try {
      const data = await fetchApi("/collections");
      setCollections(data);
    } catch (e: any) {
      alert("Yuklashda xato: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleColSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingColId) {
        await fetchApi(`/collections/${editingColId}`, {
          method: "PUT",
          body: JSON.stringify(colForm),
        });
      } else {
        await fetchApi("/collections", {
          method: "POST",
          body: JSON.stringify(colForm),
        });
      }
      setShowColModal(false);
      setEditingColId(null);
      setColForm({
        name: "",
        slug: "",
        description: "",
        poster_url: "",
        banner_url: "",
        is_franchise: true,
        is_active: true,
        sort_order: 0,
      });
      loadCollections();
    } catch (e: any) {
      alert("Saqlashda xato: " + e.message);
    }
  };

  const handleDeleteCol = async (id: number) => {
    if (!confirm("Haqiqatan ham bu to'plamni o'chirmoqchimisiz?")) return;
    try {
      await fetchApi(`/collections/${id}`, { method: "DELETE" });
      loadCollections();
    } catch (e: any) {
      alert("O'chirishda xato: " + e.message);
    }
  };

  const openManageItems = async (col: Collection) => {
    setSelectedCol(col);
    setLoadingItems(true);
    try {
      const data = await fetchApi(`/collections/${col.slug}`);
      setColItems(data.items || []);
      const nextOrder = (data.items?.length || 0) + 1;
      setAddItemForm({
        movie_code_or_id: "",
        chronological_order: nextOrder,
        release_order: nextOrder,
        timeline_event_desc: "",
        is_locked: true,
      });
    } catch (e: any) {
      alert("Qismlarni yuklashda xato: " + e.message);
    } finally {
      setLoadingItems(false);
    }
  };

  const handleToggleLock = async (item: CollectionItem) => {
    try {
      const updated = await fetchApi(`/collections/items/${item.id}`, {
        method: "PUT",
        body: JSON.stringify({ is_locked: !item.is_locked }),
      });
      setColItems((prev) =>
        prev.map((it) => (it.id === item.id ? { ...it, is_locked: !item.is_locked } : it))
      );
    } catch (e: any) {
      alert("Statusni o'zgartirishda xato: " + e.message);
    }
  };

  const handleDeleteItem = async (itemId: number) => {
    if (!confirm("Bu filmni to'plamdan olib tashlamoqchimisiz?")) return;
    try {
      await fetchApi(`/collections/items/${itemId}`, { method: "DELETE" });
      setColItems((prev) => prev.filter((it) => it.id !== itemId));
      loadCollections();
    } catch (e: any) {
      alert("O'chirishda xato: " + e.message);
    }
  };

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCol) return;
    try {
      let movieId: number | null = null;
      const cleanInput = addItemForm.movie_code_or_id.trim();

      // Look up movie by code or ID
      try {
        const found = await fetchApi(`/movies/code/${cleanInput}`);
        movieId = found.id;
      } catch (err) {
        if (!isNaN(Number(cleanInput))) {
          movieId = Number(cleanInput);
        } else {
          throw new Error("Bunday kodli film topilmadi");
        }
      }

      await fetchApi(`/collections/${selectedCol.id}/items`, {
        method: "POST",
        body: JSON.stringify({
          movie_id: movieId,
          chronological_order: Number(addItemForm.chronological_order),
          release_order: Number(addItemForm.release_order),
          timeline_event_desc: addItemForm.timeline_event_desc || null,
          is_locked: addItemForm.is_locked,
        }),
      });

      // Reload items
      openManageItems(selectedCol);
      loadCollections();
    } catch (e: any) {
      alert("Qo'shishda xato: " + e.message);
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-white/5">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-black text-white">
            Xronologiyalar & Film Olamlari
          </h1>
          <p className="text-text-secondary text-sm mt-1">
            MCU, DC, Garri Potter, Transformerlar va shaxsiy to'plamlar xronologiyasini boshqarish
          </p>
        </div>
        <button
          onClick={() => {
            setEditingColId(null);
            setColForm({
              name: "",
              slug: "",
              description: "",
              poster_url: "",
              banner_url: "",
              is_franchise: true,
              is_active: true,
              sort_order: 0,
            });
            setShowColModal(true);
          }}
          className="flex items-center gap-2 bg-primary-container hover:bg-inverse-primary text-white font-bold text-sm px-4 py-2.5 rounded-xl transition-all shadow-lg shadow-primary-container/20 cursor-pointer"
        >
          <span className="material-symbols-outlined text-lg">add</span>
          <span>Yangi To'plam Qo'shish</span>
        </button>
      </div>

      {/* Collections Table */}
      {loading ? (
        <div className="text-center py-16 text-text-secondary">Yuklanmoqda...</div>
      ) : collections.length === 0 ? (
        <div className="text-center py-16 text-text-secondary">To'plamlar mavjud emas</div>
      ) : (
        <div className="bg-surface-container-lowest border border-white/5 rounded-2xl overflow-hidden shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="border-b border-white/5 bg-white/[0.02] text-text-secondary font-bold text-xs uppercase tracking-wider">
                  <th className="py-3.5 px-4">To'plam</th>
                  <th className="py-3.5 px-4">Slug</th>
                  <th className="py-3.5 px-4">Qismlar soni</th>
                  <th className="py-3.5 px-4">Turi</th>
                  <th className="py-3.5 px-4">Holat</th>
                  <th className="py-3.5 px-4 text-right">Amallar</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {collections.map((col) => (
                  <tr key={col.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-4 flex items-center gap-3">
                      <div className="w-10 h-14 rounded-lg bg-surface-container-high overflow-hidden relative shrink-0 border border-white/10">
                        {col.poster_url || col.banner_url ? (
                          <Image
                            src={col.poster_url || col.banner_url || ""}
                            alt={col.name}
                            fill
                            sizes="40px"
                            className="object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-white/20">
                            <span className="material-symbols-outlined text-lg">movie</span>
                          </div>
                        )}
                      </div>
                      <div>
                        <div className="font-bold text-white text-base">{col.name}</div>
                        <div className="text-xs text-text-secondary line-clamp-1 max-w-sm">
                          {col.description || "Tavsif berilmagan"}
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-text-secondary">{col.slug}</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 bg-primary-container/20 text-primary-container font-extrabold px-2.5 py-1 rounded-lg border border-primary-container/30 text-xs">
                        🎬 {col.items_count} ta film
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-xs text-white/80">
                        {col.is_franchise ? "🌌 Franchisa" : "📂 To'plam"}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                          col.is_active
                            ? "bg-emerald-500/20 text-emerald-400"
                            : "bg-red-500/20 text-red-400"
                        }`}
                      >
                        {col.is_active ? "Faol" : "Nofaol"}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="inline-flex items-center gap-1.5">
                        <button
                          onClick={() => openManageItems(col)}
                          className="px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white text-xs font-bold transition-all flex items-center gap-1"
                          title="Xronologiyani tartiblash"
                        >
                          <span className="material-symbols-outlined text-sm">view_timeline</span>
                          <span>Xronologiya ({col.items_count})</span>
                        </button>
                        <button
                          onClick={() => {
                            setEditingColId(col.id);
                            setColForm({
                              name: col.name,
                              slug: col.slug,
                              description: col.description || "",
                              poster_url: col.poster_url || "",
                              banner_url: col.banner_url || "",
                              is_franchise: col.is_franchise,
                              is_active: col.is_active,
                              sort_order: col.sort_order,
                            });
                            setShowColModal(true);
                          }}
                          className="p-1.5 rounded-lg bg-white/5 hover:bg-white/15 text-text-secondary hover:text-white transition-all"
                          title="Tahrirlash"
                        >
                          <span className="material-symbols-outlined text-lg">edit</span>
                        </button>
                        <button
                          onClick={() => handleDeleteCol(col.id)}
                          className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-all"
                          title="O'chirish"
                        >
                          <span className="material-symbols-outlined text-lg">delete</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Collection Create/Edit Modal */}
      {showColModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-surface-container-lowest border border-white/10 rounded-2xl w-full max-w-lg p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-5">
              <h3 className="font-bold text-lg text-white">
                {editingColId ? "To'plamni Tahrirlash" : "Yangi To'plam"}
              </h3>
              <button
                onClick={() => setShowColModal(false)}
                className="text-text-secondary hover:text-white"
              >
                <span className="material-symbols-outlined text-xl">close</span>
              </button>
            </div>

            <form onSubmit={handleColSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-text-secondary mb-1">Nomi</label>
                <input
                  type="text"
                  required
                  value={colForm.name}
                  onChange={(e) => setColForm({ ...colForm, name: e.target.value })}
                  placeholder="Masalan: Marvel Kinokoinoti (MCU)"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-3.5 py-2 text-white text-sm focus:border-primary-container outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-text-secondary mb-1">
                  Slug (Unikal identifikator)
                </label>
                <input
                  type="text"
                  required
                  value={colForm.slug}
                  onChange={(e) => setColForm({ ...colForm, slug: e.target.value })}
                  placeholder="Masalan: mcu yoki harry-potter"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-3.5 py-2 text-white text-sm font-mono focus:border-primary-container outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-text-secondary mb-1">Tavsif</label>
                <textarea
                  rows={3}
                  value={colForm.description}
                  onChange={(e) => setColForm({ ...colForm, description: e.target.value })}
                  placeholder="Koinot haqida qisqacha ma'lumot..."
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-3.5 py-2 text-white text-sm focus:border-primary-container outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-text-secondary mb-1">
                    Poster URL
                  </label>
                  <input
                    type="url"
                    value={colForm.poster_url}
                    onChange={(e) => setColForm({ ...colForm, poster_url: e.target.value })}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-white text-xs outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-text-secondary mb-1">
                    Banner URL
                  </label>
                  <input
                    type="url"
                    value={colForm.banner_url}
                    onChange={(e) => setColForm({ ...colForm, banner_url: e.target.value })}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-white text-xs outline-none"
                  />
                </div>
              </div>

              <div className="flex items-center gap-6 pt-2">
                <label className="flex items-center gap-2 cursor-pointer text-sm">
                  <input
                    type="checkbox"
                    checked={colForm.is_franchise}
                    onChange={(e) => setColForm({ ...colForm, is_franchise: e.target.checked })}
                    className="rounded bg-white/10 border-white/20 text-primary-container"
                  />
                  <span>Kinoxronologiya (Franchisa)</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-sm">
                  <input
                    type="checkbox"
                    checked={colForm.is_active}
                    onChange={(e) => setColForm({ ...colForm, is_active: e.target.checked })}
                    className="rounded bg-white/10 border-white/20 text-primary-container"
                  />
                  <span>Faol</span>
                </label>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/10">
                <button
                  type="button"
                  onClick={() => setShowColModal(false)}
                  className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/15 text-white text-sm font-semibold"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-primary-container hover:bg-inverse-primary text-white text-sm font-bold shadow-lg"
                >
                  Saqlash
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Items Manager Modal */}
      {selectedCol && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-surface-container-lowest border border-white/10 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-5 border-b border-white/10 flex items-center justify-between shrink-0">
              <div>
                <h3 className="font-bold text-lg text-white">
                  {selectedCol.name} — Xronologiya Tartibi
                </h3>
                <p className="text-xs text-text-secondary mt-0.5">
                  Filmlarni voqealar xronologiyasi bo'yicha ko'rish, qulflash yoki yangi qism
                  qo'shish
                </p>
              </div>
              <button
                onClick={() => setSelectedCol(null)}
                className="text-text-secondary hover:text-white p-1"
              >
                <span className="material-symbols-outlined text-2xl">close</span>
              </button>
            </div>

            {/* Scrollable Items List */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              {loadingItems ? (
                <div className="text-center py-8 text-text-secondary">Yuklanmoqda...</div>
              ) : colItems.length === 0 ? (
                <div className="text-center py-8 text-text-secondary">
                  Bu to'plamda hali film mavjud emas.
                </div>
              ) : (
                <div className="space-y-2.5">
                  {colItems.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between gap-4 p-3 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/5 transition-colors"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-8 h-8 rounded-lg bg-primary-container/20 text-primary-container font-black text-sm flex items-center justify-center shrink-0">
                          #{item.chronological_order}
                        </div>
                        <div className="min-w-0">
                          <div className="font-bold text-white text-sm truncate">
                            {item.movie?.title || item.series?.title || "Noma'lum kontent"}
                          </div>
                          <div className="text-xs text-text-secondary flex items-center gap-2">
                            {item.movie?.code && (
                              <span className="font-mono text-[11px] text-white/50">
                                #{item.movie.code}
                              </span>
                            )}
                            <span>(Chiqarilgan: #{item.release_order})</span>
                            {item.timeline_event_desc && (
                              <span className="text-amber-400/90 truncate max-w-xs">
                                ⏳ {item.timeline_event_desc}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        {/* Lock / Unlock button */}
                        <button
                          type="button"
                          onClick={() => handleToggleLock(item)}
                          className={`px-2.5 py-1 rounded-lg text-xs font-bold flex items-center gap-1 transition-all ${
                            item.is_locked
                              ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                              : "bg-white/5 text-text-secondary hover:text-white"
                          }`}
                          title={
                            item.is_locked
                              ? "Qulflangan: Skraper/avtopilot bu tartibni o'zgartirmaydi"
                              : "Ochiq: Avtopilot qayta tartiblashi mumkin"
                          }
                        >
                          <span className="material-symbols-outlined text-sm">
                            {item.is_locked ? "lock" : "lock_open"}
                          </span>
                          <span>{item.is_locked ? "Qulflangan" : "Avto"}</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => handleDeleteItem(item.id)}
                          className="p-1 rounded-lg text-red-400 hover:bg-red-500/20 transition-colors"
                          title="Olib tashlash"
                        >
                          <span className="material-symbols-outlined text-lg">close</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Add Item Form */}
              <div className="mt-6 pt-5 border-t border-white/10">
                <h4 className="font-bold text-sm text-white mb-3 flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-primary-container text-lg">
                    add_circle
                  </span>
                  <span>Ushbu xronologiyaga film qo'shish</span>
                </h4>
                <form
                  onSubmit={handleAddItem}
                  className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-end"
                >
                  <div className="sm:col-span-4">
                    <label className="block text-[11px] font-bold text-text-secondary mb-1">
                      Kino kodi yoki ID
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="Masalan: BYVC33 yoki 313"
                      value={addItemForm.movie_code_or_id}
                      onChange={(e) =>
                        setAddItemForm({ ...addItemForm, movie_code_or_id: e.target.value })
                      }
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-white text-xs outline-none focus:border-primary-container"
                    />
                  </div>

                  <div className="sm:col-span-2">
                    <label className="block text-[11px] font-bold text-text-secondary mb-1">
                      Xronologik #
                    </label>
                    <input
                      type="number"
                      min={1}
                      required
                      value={addItemForm.chronological_order}
                      onChange={(e) =>
                        setAddItemForm({
                          ...addItemForm,
                          chronological_order: parseInt(e.target.value) || 1,
                        })
                      }
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-white text-xs outline-none"
                    />
                  </div>

                  <div className="sm:col-span-2">
                    <label className="block text-[11px] font-bold text-text-secondary mb-1">
                      Premyera #
                    </label>
                    <input
                      type="number"
                      min={1}
                      required
                      value={addItemForm.release_order}
                      onChange={(e) =>
                        setAddItemForm({
                          ...addItemForm,
                          release_order: parseInt(e.target.value) || 1,
                        })
                      }
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-white text-xs outline-none"
                    />
                  </div>

                  <div className="sm:col-span-3">
                    <label className="block text-[11px] font-bold text-text-secondary mb-1">
                      Voqea davri (Lore)
                    </label>
                    <input
                      type="text"
                      placeholder="Masalan: 1942: 2-Jahon Urushi"
                      value={addItemForm.timeline_event_desc}
                      onChange={(e) =>
                        setAddItemForm({ ...addItemForm, timeline_event_desc: e.target.value })
                      }
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-white text-xs outline-none"
                    />
                  </div>

                  <div className="sm:col-span-1">
                    <button
                      type="submit"
                      className="w-full bg-primary-container hover:bg-inverse-primary text-white py-2 px-3 rounded-xl font-bold text-xs transition-all shadow-md flex items-center justify-center h-[38px] cursor-pointer"
                      title="Qo'shish"
                    >
                      <span className="material-symbols-outlined text-base">add</span>
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
