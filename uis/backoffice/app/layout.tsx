import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import IncidentNav from "@/components/IncidentNav";
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
  title: "TrackFlow Backoffice",
  description: "TrackFlow operations snapshot and commercial knowledge assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full bg-slate-950 antialiased`}
    >
      <body className="flex min-h-full flex-col text-slate-100">
        <header className="border-b border-slate-800 bg-slate-900 px-4 py-3 md:px-8">
          <p className="mx-auto max-w-6xl text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">
            TrackFlow Backoffice · Internal Operations
          </p>
        </header>
        <IncidentNav />
        {children}
      </body>
    </html>
  );
}
