import type { Metadata } from "next";
import { Inter, Outfit, Space_Grotesk, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";

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
        <Navbar />

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
