import type { Metadata } from "next";
import ScrollObserver from "@/app/components/ScrollObserver";
import "./globals.css";


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
    <html lang="en">
      <body className="grain-overlay font-sans antialiased">
        <ScrollObserver />
        {children}
      </body>
    </html>
  );
}

