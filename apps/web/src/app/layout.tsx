// apps/web/src/app/layout.tsx
import type { Metadata } from "next";
import { Suspense } from "react";
import localFont from "next/font/local";
import "./globals.css";
import { ClientToaster } from "./ClientToaster";
import HomeLogoLink from "@/components/layout/HomeLogoLink";

import Link from "next/link";

import ClientBootstrap from "./providers/ClientBootstrap";
import "leaflet/dist/leaflet.css";
import { AuthProvider } from "@/lib/auth/AuthProvider";

import { HeaderAuthButtons } from "@/components/layout/HeaderAuthButtons";

const geistSans = localFont({
  src: [
    { path: "../fonts/Geist-Light.woff2", weight: "300", style: "normal" },
    { path: "../fonts/Geist-Regular.woff2", weight: "400", style: "normal" },
    { path: "../fonts/Geist-Medium.woff2", weight: "500", style: "normal" },
    { path: "../fonts/Geist-Bold.woff2", weight: "700", style: "normal" },
  ],
  variable: "--font-geist-sans",
});

const geistMono = localFont({
  src: [
    { path: "../fonts/GeistMono-Light.woff2", weight: "300", style: "normal" },
    {
      path: "../fonts/GeistMono-Regular.woff2",
      weight: "400",
      style: "normal",
    },
    { path: "../fonts/GeistMono-Medium.woff2", weight: "500", style: "normal" },
    { path: "../fonts/GeistMono-Bold.woff2", weight: "700", style: "normal" },
  ],
  variable: "--font-geist-mono",
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
  title: "KAMI MUSUBI - 静かに、自分を整える場所へ",
  description: "心が少し疲れたとき、ふと立ち寄りたくなる場所がある。あなたの今の気持ちに寄り添う神社を見つけてみませんか。",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja" className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background`}>
      <body className="min-h-dvh flex flex-col bg-background text-foreground">
        <AuthProvider>
          <ClientBootstrap />

          <header className="sticky top-0 z-[100] bg-background/80 backdrop-blur-sm border-b border-border/30">
            <nav className="mx-auto flex max-w-3xl items-center gap-4 px-5 py-4 sm:px-6">
              <HomeLogoLink />

              <div className="ml-auto flex items-center gap-3">
                <Link
                  href="/map"
                  className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border/50 bg-card text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                  aria-label="神社を検索"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <circle cx="11" cy="11" r="8" />
                    <path d="m21 21-4.3-4.3" />
                  </svg>
                </Link>

                <Suspense fallback={null}>
                  <HeaderAuthButtons />
                </Suspense>
              </div>
            </nav>
          </header>

          {/* ページ内容 */}
          <main className="flex-1 min-h-0 overflow-y-auto">{children}</main>

          {/* ここに置く */}
          <ClientToaster />
        </AuthProvider>
      </body>
    </html>
  );
}
