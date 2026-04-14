import type { Metadata } from "next";
import "./globals.css";

import { ThemeToggle } from "@/components/theme-toggle";

export const metadata: Metadata = {
  title: "Book Document Intelligence",
  description: "AI-powered book intelligence, retrieval, and recommendation platform."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <main className="mx-auto min-h-screen max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <header className="mb-10 flex flex-col gap-4 rounded-[32px] border border-white/10 bg-panel/70 p-6 backdrop-blur md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.34em] text-muted">Document Intelligence Platform</p>
              <h1 className="mt-2 text-3xl font-semibold text-text">Books, embeddings, RAG, and search in one surface</h1>
            </div>
            <ThemeToggle />
          </header>
          {children}
        </main>
      </body>
    </html>
  );
}
