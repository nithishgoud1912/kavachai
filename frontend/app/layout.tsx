import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "KavachAI — Sovereign Industrial AI Workbench",
  description:
    "On-premise agentic AI investigation workbench for evidence-backed industrial analysis. All inference runs locally — no data leaves your network.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body className="grain-overlay">{children}</body>
    </html>
  );
}

