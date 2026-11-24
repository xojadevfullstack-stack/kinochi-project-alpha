import Link from "next/link";
import { notFound } from "next/navigation";
import { Metadata } from "next";
import { getPublicConfig } from "@/lib/api";

const LEGAL_DOCS: Record<
  string,
  {
    title: string;
    badge: string;
    sections: { heading: string; paragraphs?: string[]; list?: string[] }[];
  }
> = {
  rules: {
    title: "Foydalanish qoidalari",
    badge: "Rasmiy hujjat",
    sections: [
      {
        heading: "1. Umumiy qoidalar",
        paragraphs: [
          "MediaPlus veb-portali foydalanuvchilarga kino san'ati asarlari, seriallar va animatsion filmlar haqida to'liq ma'lumot olish, sharhlar yozish, reyting berish hamda katalog ma'lumotlarini o'rganish imkonini beruvchi axborot katalogidir.",
        ],
      },
      {
        heading: "2. Haqiqiy arxitektura va video oqimi",
        paragraphs: [
          "MediaPlus o'z veb-serverlarida hech qanday noqonuniy video fayllarni saqlamaydi yoki to'g'ridan-to'g'ri noqonuniy oqim uzatmaydi. Media materiallarni tomosha qilish barcha xavfsizlik va shifrlash talablariga muvofiq rasmiy Telegram ekotizimi va bot orqali tashkil etilgan.",
        ],
      },
      {
        heading: "3. Foydalanuvchilar majburiyati",
        paragraphs: [
          "Platformada qoldirilgan barcha izohlar va sharhlar madaniy me'yorlarga hamda qonunchilik talablariga mos bo'lishi shart. Haqorat, tuhmat yoki spam o'z ichiga olgan faoliyat cheklanishi mumkin.",
        ],
      },
    ],
  },
  dmca: {
    title: "DMCA va Mualliflik huquqi",
    badge: "Huquqiy himoya",
    sections: [
      {
        heading: "Mualliflik huquqi egalariga (DMCA)",
        paragraphs: [
          "MediaPlus raqamli huquqlar va intellektual mulk egalarining qonuniy manfaatlarini to'liq hurmat qiladi. Veb-saytda aks etgan posterlar, treylerlar va meta-ma'lumotlar ochiq axborot manbalaridan (TMDb, YouTube) olinadi.",
        ],
      },
      {
        heading: "Murojaat tartibi",
        paragraphs: [
          "Agar siz mualliflik huquqi egasi bo'lsangiz va platformadagi biron bir ma'lumot huquqlaringizni buzmoqda deb hisoblasangiz, quyidagi ma'lumotlarni yuboring:",
        ],
        list: [
          "Huquq egasi yoki rasmiy vakilning tasdiqlovchi hujjati;",
          "Nizoli sahifaning aniq manzili (URL havolasi);",
          "To'g'ridan-to'g'ri bog'lanish uchun rasmiy elektron pochta yoki kontakt.",
        ],
      },
      {
        heading: "Ko'rib chiqish muddati",
        paragraphs: [
          "Asosli murojaatlar 24 soat ichida ko'rib chiqiladi va tegishli chora ko'riladi.",
        ],
      },
    ],
  },
  privacy: {
    title: "Maxfiylik siyosati",
    badge: "Xavfsizlik",
    sections: [
      {
        heading: "Shaxsiy ma'lumotlarni himoya qilish",
        paragraphs: [
          "Biz foydalanuvchilarimizning shaxsiy ma'lumotlari xavfsizligiga jiddiy e'tibor qaratamiz. Kirish Telegram orqali HMAC kriptografik tekshiruvi yordamida amalga oshiriladi.",
        ],
      },
      {
        heading: "Qanday ma'lumotlar saqlanadi?",
        paragraphs: [
          "Faqatgina xizmat ishlashi uchun zarur minimal parametrlar: Telegram ID, ism, tomosha tarixi va saqlangan obunalar ro'yxati.",
          "Shaxsiy ma'lumotlar uchinchi shaxslarga sotilmaydi yoki topshirilmaydi.",
        ],
      },
    ],
  },
  about: {
    title: "Reklama va MediaPlus haqida",
    badge: "Hamkorlik",
    sections: [
      {
        heading: "MediaPlus nima?",
        paragraphs: [
          "MediaPlus — zamonaviy kinosevarlar uchun yaratilgan yuqori tezlikdagi multimedia katalogi va Telegram bot ekotizimidir.",
        ],
      },
      {
        heading: "Asosiy afzalliklar va hamkorlik",
        list: [
          "Tezkor kashfiyot: Kinolar, seriallar, anime, doramalar va multfilmlar uchun aqlli qidiruv;",
          "Haqiqiy reytinglar: IMDb va foydalanuvchilarning real baholari;",
          "Reklama va hamkorlik masalalari bo'yicha rasmiy Telegram botimiz orqali bog'lanishingiz mumkin.",
        ],
      },
    ],
  },
};

export function generateStaticParams() {
  return Object.keys(LEGAL_DOCS).map((doc) => ({ doc }));
}

export async function generateMetadata({
  params,
}: {
  params: { doc: string };
}): Promise<Metadata> {
  const item = LEGAL_DOCS[params.doc];
  if (!item) return { title: "Sahifa topilmadi | MediaPlus" };
  return { title: `${item.title} | MediaPlus` };
}

export default async function LegalDocPage({ params }: { params: { doc: string } }) {
  const doc = LEGAL_DOCS[params.doc];
  if (!doc) notFound();

  const { bot_username: botUsername } = await getPublicConfig();

  return (
    <div className="min-h-screen bg-transparent text-slate-900 dark:text-text-primary pt-4 pb-20 px-gutter">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex flex-wrap gap-2">
          {Object.entries(LEGAL_DOCS).map(([key, info]) => {
            const active = key === params.doc;
            return (
              <Link
                key={key}
                href={`/legal/${key}`}
                className={`px-3.5 py-1.5 rounded-full text-xs font-semibold border transition ${
                  active
                    ? "bg-[#D20A13] dark:bg-[#E50914] border-[#D20A13] dark:border-[#E50914] text-white"
                    : "bg-white dark:bg-white/5 border-slate-200 dark:border-white/10 text-slate-700 dark:text-gray-300 hover:border-[#E50914]"
                }`}
              >
                {info.title}
              </Link>
            );
          })}
        </div>

        <article className="callout-card rounded-3xl bg-white dark:bg-[#0E1117]/90 border border-slate-200 dark:border-white/10 p-6 sm:p-10 shadow-sm dark:shadow-2xl space-y-6">
          <div className="border-b border-slate-200 dark:border-white/10 pb-4">
            <span className="inline-block px-3 py-1 rounded-full bg-red-50 dark:bg-[#E50914]/15 border border-red-200 dark:border-[#E50914]/30 text-[#D20A13] dark:text-[#E50914] text-[11px] font-bold uppercase tracking-wider mb-3">
              {doc.badge}
            </span>
            <h1 className="font-heading text-2xl sm:text-4xl font-black text-slate-900 dark:text-white tracking-tight">
              {doc.title}
            </h1>
          </div>

          <div className="space-y-5 text-sm leading-relaxed text-slate-700 dark:text-gray-300">
            {doc.sections.map((sec) => (
              <section key={sec.heading} className="space-y-2">
                <h2 className="text-base font-bold text-slate-900 dark:text-white">
                  {sec.heading}
                </h2>
                {sec.paragraphs?.map((p, idx) => (
                  <p key={idx}>{p}</p>
                ))}
                {sec.list && (
                  <ul className="list-disc pl-5 space-y-1 text-slate-600 dark:text-gray-300">
                    {sec.list.map((li, idx) => (
                      <li key={idx}>{li}</li>
                    ))}
                  </ul>
                )}
              </section>
            ))}
          </div>

          <div className="pt-4 border-t border-slate-200 dark:border-white/10 flex flex-wrap items-center justify-between gap-3">
            <Link
              href="/requests"
              className="text-xs font-bold text-[#D20A13] dark:text-[#E50914] hover:underline"
            >
              Kino buyurtma berish →
            </Link>
            <a
              href={`https://t.me/${botUsername}`}
              target="_blank"
              rel="noopener noreferrer"
              className="footer-social-btn inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold"
            >
              <span className="material-symbols-outlined text-[16px]">send</span>
              <span>Rasmiy Telegram Bot</span>
            </a>
          </div>
        </article>
      </div>
    </div>
  );
}
