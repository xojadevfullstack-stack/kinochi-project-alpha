import type { Metadata } from "next";
import { Inter, Outfit, Space_Grotesk, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "cyrillic"], variable: '--font-inter' });
const outfit = Outfit({ subsets: ["latin"], variable: '--font-outfit' });
const spaceGrotesk = Space_Grotesk({ subsets: ["latin"], variable: '--font-space-grotesk' });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: '--font-jetbrains-mono' });

export const metadata: Metadata = {
  title: "Kinochi - Premium Cinema",
  description: "Kinochi Telegram boti orqali eng sara kinolarni tomosha qiling.",
  openGraph: {
    title: "Kinochi - Premium Cinema",
    description: "Kinochi Telegram boti orqali eng sara kinolarni bepul tomosha qiling. Eng katta kino katalogi.",
    url: "https://kinochi.uz",
    siteName: "Kinochi",
    images: [
      {
        url: "https://kinochi.uz/default-og-image.jpg", 
        width: 1200,
        height: 630,
        alt: "Kinochi - Bosh sahifa",
      },
    ],
    locale: "uz_UZ",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="uz" className="dark">
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
        <style>{`
          .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
          }
          .hide-scrollbar::-webkit-scrollbar {
            display: none;
          }
          .hide-scrollbar {
            -ms-overflow-style: none;
            scrollbar-width: none;
          }
        `}</style>
      </head>
      <body className={`${inter.variable} ${outfit.variable} ${spaceGrotesk.variable} ${jetbrainsMono.variable} bg-background-obsidian text-text-primary font-body-md text-body-md antialiased overflow-x-hidden`}>
        {/* TopNavBar */}
        <nav className="fixed top-0 w-full z-50 flex justify-between items-center px-gutter py-4 bg-background-obsidian/80 backdrop-blur-lg border-b border-white/10 shadow-2xl shadow-primary-container/20 transition-all duration-300 ease-out">
          <div className="flex items-center gap-8">
            <a className="font-display-hero-mobile text-[32px] sm:text-display-hero-mobile text-primary-container tracking-tighter" href="/">Kinochi</a>
            {/* Navigation Links (Desktop) */}
            <div className="hidden md:flex items-center gap-6">
              <a className="text-primary-container font-bold border-b-2 border-primary-container pb-1 transition-all duration-300 ease-out hover:scale-105 hover:bg-white/5 px-2 rounded-t-sm" href="/">Asosiy</a>
              <a className="text-on-secondary-container hover:text-text-primary transition-colors hover:scale-105 hover:bg-white/5 px-2 py-1 rounded-sm" href="/movies">Kinolar</a>
              <a className="text-on-secondary-container hover:text-text-primary transition-colors hover:scale-105 hover:bg-white/5 px-2 py-1 rounded-sm" href="/series">Seriallar</a>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {/* Search Bar */}
            <div className="hidden md:flex items-center bg-white/10 rounded-full px-4 py-2 border border-transparent focus-within:border-white/30 transition-colors">
              <span className="material-symbols-outlined text-text-secondary mr-2" data-icon="search">search</span>
              <input className="bg-transparent border-none focus:ring-0 text-text-primary text-sm placeholder:text-text-secondary w-48 outline-none" placeholder="Qidirish..." type="text"/>
            </div>
            {/* Trailing Icon Action */}
            <button className="text-on-secondary-container hover:text-text-primary transition-colors hover:scale-105 p-2 rounded-full hover:bg-white/5">
              <span className="material-symbols-outlined" data-icon="notifications">notifications</span>
            </button>
            {/* Profile Image Placeholder */}
            <div className="w-10 h-10 rounded-full overflow-hidden border border-white/10 ml-2 hover:border-primary-container transition-colors cursor-pointer bg-white/5 flex items-center justify-center">
              <span className="material-symbols-outlined text-text-secondary">person</span>
            </div>
          </div>
        </nav>

        <main className="min-h-screen">
          {children}
        </main>
        
        {/* Simple Footer */}
        <footer className="border-t border-white/10 mt-12 py-8 text-center text-text-secondary text-sm">
          <p>© {new Date().getFullYear()} Kinochi. Barcha huquqlar himoyalangan.</p>
        </footer>
      </body>
    </html>
  );
}
