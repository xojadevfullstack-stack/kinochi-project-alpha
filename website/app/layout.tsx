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
      <body className={`${inter.variable} ${spaceGrotesk.variable} ${jetbrainsMono.variable} font-sans bg-background text-white selection:bg-primary/30 selection:text-white`}>
        {/* Premium Navbar */}
        <nav className="fixed w-full z-50 bg-[#09090B]/80 backdrop-blur-md border-b border-white/5">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              {/* Logo */}
              <div className="flex-shrink-0">
                <a href="/" className="text-2xl font-display font-black text-primary tracking-tighter hover:opacity-80 transition-opacity">
                  KINOCHI
                </a>
              </div>
              
              {/* Desktop Menu */}
              <div className="hidden md:flex flex-1 justify-center">
                <div className="flex space-x-8">
                  <a href="/" className="text-white hover:text-primary px-3 py-2 text-sm font-medium transition-colors border-b-2 border-primary">Bosh sahifa</a>
                  <a href="/movies" className="text-gray-400 hover:text-white px-3 py-2 text-sm font-medium transition-colors border-b-2 border-transparent hover:border-white/30">Kinolar</a>
                  <a href="/series" className="text-gray-400 hover:text-white px-3 py-2 text-sm font-medium transition-colors border-b-2 border-transparent hover:border-white/30">Seriallar</a>
                </div>
              </div>

              {/* Right Icons */}
              <div className="flex items-center space-x-4">
                <button className="text-gray-400 hover:text-white transition-colors">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </nav>

        <main className="min-h-screen pt-16">
          {children}
        </main>
        
        {/* Premium Footer */}
        <footer className="border-t border-white/5 bg-[#09090B] pt-12 pb-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col items-center">
            <a href="/" className="text-2xl font-display font-black text-primary tracking-tighter mb-6">
              KINOCHI
            </a>
            <div className="flex space-x-6 text-sm text-gray-400 mb-8">
              <a href="#" className="hover:text-white transition-colors">Biz haqimizda</a>
              <a href="#" className="hover:text-white transition-colors">Maxfiylik siyosati</a>
              <a href="#" className="hover:text-white transition-colors">Yordam</a>
            </div>
            <p className="text-gray-600 text-xs">
              © {new Date().getFullYear()} KINOCHI Streaming Platform. Barcha huquqlar himoyalangan.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
