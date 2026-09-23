import type { Metadata, Viewport } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";
import AdminShell from "@/components/AdminShell";

const inter = Inter({ subsets: ["latin", "cyrillic"], variable: '--font-inter' });
const outfit = Outfit({ subsets: ["latin"], variable: '--font-outfit' });

export const metadata: Metadata = {
  title: "Kinochi Admin Panel",
  description: "Admin panel for Kinochi Bot",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
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
            border-color: rgba(229, 9, 20, 0.3);
          }

          .data-table-row {
            transition: background-color 0.2s ease;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
          }
          
          .data-table-row:hover {
            background-color: rgba(255, 255, 255, 0.05);
          }

          /* Custom mobile-friendly scrollbar for tables */
          .custom-scrollbar::-webkit-scrollbar {
            height: 6px;
            width: 6px;
          }
          .custom-scrollbar::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.02);
            border-radius: 9999px;
          }
          .custom-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 9999px;
          }
          .custom-scrollbar::-webkit-scrollbar-thumb:hover {
            background: rgba(229, 9, 20, 0.4);
          }
        `}</style>
      </head>
      <body className={`${inter.variable} ${outfit.variable} bg-background-obsidian text-text-primary min-h-screen antialiased font-sans`}>
        <AdminShell>
          {children}
        </AdminShell>
      </body>
    </html>
  );
}
