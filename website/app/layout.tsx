import type { Metadata } from "next";
import { Inter, Outfit, Space_Grotesk, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import BottomNav from "@/components/BottomNav";
import FloatingBackButton from "@/components/FloatingBackButton";
import SubheaderTabs from "@/components/SubheaderTabs";
import Breadcrumb from "@/components/Breadcrumb";
import { BreadcrumbProvider } from "@/components/BreadcrumbContext";
import Footer from "@/components/Footer";
import TelegramInit from "@/components/TelegramInit";
import { fetchApi } from "@/lib/api";
import { AuthProvider } from "@/lib/auth/AuthProvider";
import TopRouteLoader from "@/components/TopRouteLoader";
import Script from "next/script";

const inter = Inter({ subsets: ["latin", "cyrillic"], variable: '--font-inter' });
const outfit = Outfit({ subsets: ["latin"], variable: '--font-outfit' });
const spaceGrotesk = Space_Grotesk({ subsets: ["latin"], variable: '--font-space-grotesk' });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: '--font-jetbrains-mono' });

export const metadata: Metadata = {
  title: "MediaPlus - Eng so'nggi kinolar va seriallar",
  description: "Telegram tarmog'idagi eng katta va qulay kino bazasi",
  openGraph: {
    title: "MediaPlus - Eng so'nggi kinolar va seriallar",
    description: "MediaPlus orqali eng sara kinolarni bepul tomosha qiling. Eng katta kino katalogi.",
    url: "https://kinochi-project-alpha.vercel.app",
    siteName: "MediaPlus",
    images: [
      {
        url: "https://kinochi-project-alpha.vercel.app/default-og-image.jpg", 
        width: 1200,
        height: 630,
        alt: "MediaPlus - Bosh sahifa",
      },
    ],
    locale: "uz_UZ",
    type: "website",
  },
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  let pages: any[] = [];
  try {
    const data = await fetchApi("/pages/");
    pages = data.items || data || [];
  } catch (e) {
    console.error("Failed to fetch pages for layout:", e);
  }

  return (
    <html lang="uz" className="dark" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var d=document.documentElement,n=navigator,c=n.connection||n.mozConnection||n.webkitConnection,m=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;if((c&&c.saveData)||(typeof n.deviceMemory==='number'&&n.deviceMemory<=2)||(typeof n.hardwareConcurrency==='number'&&n.hardwareConcurrency<=2)||m){d.classList.add('low-end-device');}var t=localStorage.getItem('kinochi_theme');if(t==='light'){d.classList.remove('dark');d.classList.add('light');}else{d.classList.add('dark');d.classList.remove('light');}}catch(e){}})();`,
          }}
        />
        <Script src="https://telegram.org/js/telegram-web-app.js" strategy="beforeInteractive" />
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
      </head>
      <body className={`${inter.variable} ${outfit.variable} ${spaceGrotesk.variable} ${jetbrainsMono.variable} pure-minimal bg-background-obsidian text-text-primary font-body-md text-body-md antialiased overflow-x-hidden`} suppressHydrationWarning>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{if(document.documentElement.classList.contains('light')){document.body.classList.add('light-theme');}}catch(e){}})();`,
          }}
        />
        <AuthProvider>
          <BreadcrumbProvider>
            <TopRouteLoader />
            <TelegramInit />
            <Navbar pages={pages} />

            <main className="min-h-screen pb-20 xl:pb-0">
              <SubheaderTabs />
              <Breadcrumb />
              {children}
            </main>
            
            <BottomNav />
            <FloatingBackButton />
            <Footer />
          </BreadcrumbProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
