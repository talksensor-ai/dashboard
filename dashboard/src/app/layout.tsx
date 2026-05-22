import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin", "cyrillic"],
});

export const metadata: Metadata = {
  title: "Talk Sensor | Контроль Качества",
  description: "AI Аналитика диалогов в кофейне",
  applicationName: "Talk Sensor",
  appleWebApp: {
    capable: true,
    title: "Talk Sensor",
    statusBarStyle: "black-translucent",
  },
  formatDetection: {
    telephone: false,
  },
};

import { Viewport } from 'next';

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#F5F5F7' },
    { media: '(prefers-color-scheme: dark)', color: '#000000' },
  ],
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

import { ThemeProvider } from "@/components/theme-provider"

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ru"
      className={`${inter.variable} font-sans h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full bg-[#F5F5F7] dark:bg-black text-[#1D1D1F] dark:text-[#F5F5F7] selection:bg-[#007AFF]/10 dark:selection:bg-[#007AFF]/20 transition-colors duration-300">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem disableTransitionOnChange>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
