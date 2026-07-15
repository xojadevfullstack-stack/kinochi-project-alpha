import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

const inter = Inter({ subsets: ["latin", "cyrillic"], variable: '--font-inter' });
const outfit = Outfit({ subsets: ["latin"], variable: '--font-outfit' });

export const metadata: Metadata = {
  title: "Kinochi Admin Panel",
  description: "Admin panel for Kinochi Bot",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
        <style>{`
          .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
          }
          .glass-panel {
            backdrop-filter: blur(16px);
            background-color: rgba(26, 9, 8, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.05);
          }
          
          .metric-card {
            background: linear-gradient(145deg, rgba(46, 26, 24, 0.8) 0%, rgba(26, 9, 8, 0.9) 100%);
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: all 0.3s ease;
          }
          
          .metric-card:hover {
            transform: translateY(-4px);
            border-color: rgba(229, 9, 20, 0.3);
            box-shadow: 0 8px 32px rgba(229, 9, 20, 0.15);
          }

          .data-table-row {
            transition: background-color 0.2s ease;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
          }
          
          .data-table-row:hover {
            background-color: rgba(255, 255, 255, 0.05);
          }
        `}</style>
      </head>
      <body className={`${inter.variable} ${outfit.variable} bg-background-obsidian text-text-primary min-h-screen flex antialiased font-sans`}>
        <Sidebar />
        <main className="ml-[280px] flex-1 min-h-screen p-margin-desktop bg-background-obsidian relative overflow-y-auto">
          {/* Subtle Background Glow */}
          <div className="absolute top-0 left-1/4 w-[800px] h-[400px] bg-primary-container/5 rounded-full blur-[120px] pointer-events-none -z-10"></div>
          {children}
        </main>
      </body>
    </html>
  );
}
