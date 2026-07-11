import type { Metadata } from "next";
import { Inter, Space_Grotesk, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "cyrillic"], variable: '--font-inter' });
const spaceGrotesk = Space_Grotesk({ subsets: ["latin"], variable: '--font-space-grotesk' });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: '--font-jetbrains-mono' });

export const metadata: Metadata = {
  title: "Kinochi - Eng so'nggi va sara kinolar",
  description: "Kinochi Telegram boti orqali eng sara kinolarni tomosha qiling.",
  openGraph: {
    title: "Kinochi - Eng so'nggi va sara kinolar",
    description: "Kinochi Telegram boti orqali eng sara kinolarni bepul tomosha qiling. Eng katta kino katalogi.",
    url: "https://kinochi.uz",
    siteName: "Kinochi",
    images: [
      {
        url: "https://kinochi.uz/default-og-image.jpg", // Hozircha statik, haqiqiy domen qo'yilganda o'zgartiriladi
        width: 1200,
        height: 630,
        alt: "Kinochi - Bosh sahifa",
      },
    ],
    locale: "uz_UZ",
    type: "website",
  },
};

// DIQQAT: Kelgusida Movie Details sahifasi (app/movie/[code]/page.tsx) yaratilganda,
// u yerda Next.js ning `generateMetadata()` funksiyasidan foydalanib, 
// o'sha kinoning real sarlavhasi (og:title) va posteri (og:image) ni dinamik chiqarish yoddan chiqmasin!

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="uz">
      <body className={`${inter.variable} ${spaceGrotesk.variable} ${jetbrainsMono.variable} font-sans bg-[#0b0c10] text-[#e5e7eb]`}>
        {/* Simple Navbar */}
        <nav className="fixed w-full z-50 glass-panel border-b border-white/5">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex-shrink-0">
                <a href="/" className="text-2xl font-display font-bold text-primary tracking-tighter hover:scale-105 transition-transform duration-300 inline-block">
                  KINOCHI
                </a>
              </div>
              <div className="hidden md:block">
                <div className="ml-10 flex items-baseline space-x-4">
                  <a href="/" className="text-gray-300 hover:text-white hover:bg-white/5 px-3 py-2 rounded-md text-sm font-medium transition-all duration-300 glow-border-hover border border-transparent">Bosh sahifa</a>
                  <a href="/" className="text-gray-300 hover:text-white hover:bg-white/5 px-3 py-2 rounded-md text-sm font-medium transition-all duration-300 glow-border-hover border border-transparent">Kinolar</a>
                  <a href="/series" className="text-gray-300 hover:text-white hover:bg-white/5 px-3 py-2 rounded-md text-sm font-medium transition-all duration-300 glow-border-hover border border-transparent">Seriallar</a>
                </div>
              </div>
            </div>
          </div>
        </nav>

        <main className="min-h-screen">
          {children}
        </main>
        
        {/* Simple Footer */}
        <footer className="border-t border-white/10 mt-12 py-8 text-center text-gray-500 text-sm">
          <p>© {new Date().getFullYear()} Kinochi. Barcha huquqlar himoyalangan.</p>
        </footer>
      </body>
    </html>
  );
}
