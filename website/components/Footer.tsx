import Link from "next/link";

export default function Footer() {
  const botUsername = process.env.NEXT_PUBLIC_BOT_USERNAME || "MediaPlusOfficialBot";
  const channelUrl = process.env.NEXT_PUBLIC_CHANNEL_URL || "https://t.me/kinochilar_uz";

  return (
    <footer className="cv-auto w-full bg-white dark:bg-[#08090C] border-t border-slate-200 dark:border-white/10 pt-10 pb-28 xl:pb-10 mt-12">
      <div className="max-w-container-max mx-auto px-gutter">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-8">
          {/* Brand Column */}
          <div className="col-span-2">
            <Link href="/" className="inline-flex items-center gap-2 mb-3 group">
              <img
                src="/logo-mediaplus-icon.png"
                alt="MediaPlus"
                decoding="async"
                className="w-8 h-8 rounded-xl shrink-0 object-cover shadow-md shadow-brand-red/30"
              />
              <span className="font-heading font-extrabold text-xl text-slate-900 dark:text-white tracking-tight">
                MEDIA<span className="text-[#D20A13] dark:text-[#E50914]">PLUS</span>
              </span>
            </Link>
            <p className="text-xs text-slate-600 dark:text-gray-400 leading-relaxed max-w-sm mb-4">
              O&apos;zbekistondagi eng yirik va qulay multimedia platformasi. Kinolar, seriallar, anime, doramalar va multfilmlar o&apos;zbek tilida, yuqori sifatda (Full HD/4K) va reklamasiz.
            </p>
            <div className="flex flex-wrap items-center gap-2.5">
              <a
                href={`https://t.me/${botUsername}`}
                target="_blank"
                rel="noopener noreferrer"
                className="footer-social-btn inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer"
              >
                <span className="material-symbols-outlined text-[15px]">send</span>
                <span>Telegram Bot</span>
              </a>
              <a
                href={channelUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="footer-social-btn inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer"
              >
                <span className="material-symbols-outlined text-[15px]">campaign</span>
                <span>Kanal</span>
              </a>
            </div>
          </div>

          {/* Bo'limlar */}
          <div>
            <h4 className="font-heading font-bold text-xs uppercase tracking-wider text-slate-900 dark:text-white mb-3 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#E50914]" />
              <span>Bo&apos;limlar</span>
            </h4>
            <ul className="space-y-2 text-xs text-slate-600 dark:text-gray-400">
              <li><Link href="/movies" className="hover:text-[#D20A13] dark:hover:text-[#E50914] transition">Kinolar</Link></li>
              <li><Link href="/series" className="hover:text-[#D20A13] dark:hover:text-[#E50914] transition">Seriallar</Link></li>
              <li><Link href="/anime" className="hover:text-[#D20A13] dark:hover:text-[#E50914] transition">Animelar</Link></li>
              <li><Link href="/doramas" className="hover:text-[#D20A13] dark:hover:text-[#E50914] transition">Doramalar</Link></li>
              <li><Link href="/cartoons" className="hover:text-[#D20A13] dark:hover:text-[#E50914] transition">Multfilmlar</Link></li>
              <li><Link href="/premieres" className="hover:text-[#D20A13] dark:hover:text-[#E50914] transition">Premyeralar</Link></li>
            </ul>
          </div>

          {/* Xizmatlar */}
          <div>
            <h4 className="font-heading font-bold text-xs uppercase tracking-wider text-slate-900 dark:text-white mb-3 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#E50914]" />
              <span>Xizmatlar</span>
            </h4>
            <ul className="space-y-2 text-xs text-slate-600 dark:text-gray-400">
              <li><Link href="/collections" className="hover:text-[#D20A13] dark:hover:text-[#E50914] transition">To&apos;plamlar</Link></li>
              <li><Link href="/catalog" className="hover:text-[#D20A13] dark:hover:text-[#E50914] transition">Janrlar va Bo&apos;limlar</Link></li>
              <li><Link href="/subscriptions" className="hover:text-[#D20A13] dark:hover:text-[#E50914] transition">Sevimlilar (Obunalar)</Link></li>
              <li><Link href="/requests" className="hover:text-[#D20A13] dark:hover:text-[#E50914] transition">Kino buyurtma berish</Link></li>
              <li><Link href="/notifications" className="hover:text-[#D20A13] dark:hover:text-[#E50914] transition">Bildirishnomalar</Link></li>
              <li><Link href="/profile" className="hover:text-[#D20A13] dark:hover:text-[#E50914] transition">Mening profilim</Link></li>
            </ul>
          </div>

          {/* Ma'lumot & Qoidalar */}
          <div>
            <h4 className="font-heading font-bold text-xs uppercase tracking-wider text-slate-900 dark:text-white mb-3 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#E50914]" />
              <span>Ma&apos;lumot</span>
            </h4>
            <ul className="space-y-2 text-xs text-slate-600 dark:text-gray-400">
              <li><Link href="/legal/rules" className="hover:text-[#D20A13] dark:hover:text-[#E50914] transition">Foydalanish shartlari</Link></li>
              <li><Link href="/legal/dmca" className="hover:text-[#D20A13] dark:hover:text-[#E50914] transition">Mualliflik huquqi (DMCA)</Link></li>
              <li><Link href="/legal/privacy" className="hover:text-[#D20A13] dark:hover:text-[#E50914] transition">Maxfiylik siyosati</Link></li>
              <li><Link href="/legal/about" className="hover:text-[#D20A13] dark:hover:text-[#E50914] transition">Reklama va hamkorlik</Link></li>
              <li>
                <span className="badge-18plus inline-block px-2 py-0.5 rounded-md text-[10px] font-bold">
                  18+ Ogohlantirish
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Copyright Bottom Bar */}
        <div className="pt-6 border-t border-slate-200 dark:border-white/10 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-slate-500 dark:text-gray-500">
          <p>© {new Date().getFullYear()} MEDIAPLUS. Barcha huquqlar himoyalangan.</p>
          <p className="text-center sm:text-right">Materiallar faqat shaxsiy tanishuv uchun taqdim etiladi.</p>
        </div>
      </div>
    </footer>
  );
}
