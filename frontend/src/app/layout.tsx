import type { Metadata } from "next";
import { Geist, Geist_Mono, Press_Start_2P } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const pressStart2P = Press_Start_2P({
  weight: "400",
  variable: "--font-press-start",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PokéSim Battle | Premium Simulator",
  description: "Experience authentic Pokémon battles with strategic movesets and modern aesthetics.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${pressStart2P.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        {children}
        <footer className="fixed bottom-0 left-0 right-0 py-1.5 px-4 bg-black/40 backdrop-blur-sm text-[8px] md:text-[10px] text-gray-500/80 text-center z-[100] pointer-events-none select-none tracking-wider">
          Pokémon and all related names are trademarks of Nintendo, Game Freak, and Creatures. This is a non-commercial fan-made project.
        </footer>
      </body>
    </html>
  );
}
