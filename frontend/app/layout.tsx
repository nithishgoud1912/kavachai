import type { Metadata } from "next";
import { Playfair_Display } from "next/font/google";
import ScrollObserver from "@/app/components/ScrollObserver";
import "./globals.css";

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  display: "swap",
  weight: ["400", "500", "600", "700", "800", "900"],
});

export const metadata: Metadata = {
  title: "KavachAI — Sovereign Industrial AI Workbench",
  description:
    "On-premise agentic AI investigation workbench for evidence-backed industrial analysis. All inference runs locally — no data leaves your network.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={playfair.variable}>
      <body className="grain-overlay font-sans antialiased">
        <ScrollObserver />
        {children}
      </body>
    </html>
  );
}

