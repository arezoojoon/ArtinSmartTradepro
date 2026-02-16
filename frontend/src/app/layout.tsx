import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Artin Smart Trade - AI Trade Operating System",
  description: "The World's First AI Trade OS. Automate B2B sales, generate leads, and close deals on WhatsApp 24/7. Powered by Gemini Vision & Voice.",
  manifest: "/manifest.json",
  keywords: ["AI Trading", "B2B Automation", "Lead Generation", "Trade OS", "WhatsApp Business"],
  authors: [{ name: "Artin Smart Trade" }],
  openGraph: {
    title: "Artin Smart Trade - AI Trade Operating System",
    description: "Automate your B2B sales with AI-powered lead generation and WhatsApp automation",
    type: "website",
    url: "https://trade.artinsmartagent.com",
  },
  twitter: {
    card: "summary_large_image",
    title: "Artin Smart Trade - AI Trade Operating System",
    description: "The World's First AI Trade OS for B2B automation",
  },
};

export const viewport: Viewport = {
  themeColor: "#0a192f",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

import { AuthProvider } from "@/context/AuthContext";
import { Toaster } from "@/components/ui/toaster";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <AuthProvider>
          {children}
          <Toaster />
        </AuthProvider>
      </body>
    </html>
  );
}
