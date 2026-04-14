import Link from "next/link";

import { BookCard } from "@/components/book-card";
import { IngestionPanel } from "@/components/ingestion-panel";
import { api } from "@/lib/api";

export default async function DashboardPage({
  searchParams
}: {
  searchParams?: Promise<{ search?: string; genre?: string }>;
}) {
  const params = (await searchParams) ?? {};
  const books = await api.listBooks(params.search ?? "", params.genre ?? "");

  return (
    <div className="space-y-8">
      <section className="grid gap-6 rounded-[36px] border border-white/10 bg-panel/75 p-8 shadow-glow lg:grid-cols-[1.1fr_0.9fr]">
        <div>
          <p className="text-sm uppercase tracking-[0.28em] text-muted">Dashboard</p>
          <h2 className="mt-3 text-4xl font-semibold text-text">Search, inspect, and reason over your book collection.</h2>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-muted">
            The backend handles Selenium ingestion, MySQL persistence, Chroma retrieval, and AI enrichment. This frontend
            keeps discovery fast with a card-driven view, filters, and direct QA access.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/qa" className="rounded-full bg-accent px-5 py-3 text-sm font-medium text-slate-950">
              Open Q&A
            </Link>
          </div>
          <div className="mt-6">
            <IngestionPanel />
          </div>
        </div>
        <form className="grid gap-3 rounded-[28px] border border-white/10 bg-canvas/40 p-5" action="/">
          <label className="text-sm text-muted">
            Search
            <input
              name="search"
              defaultValue={params.search ?? ""}
              placeholder="Title or author"
              className="mt-2 w-full rounded-2xl border border-white/10 bg-panel/70 px-4 py-3 text-sm text-text outline-none"
            />
          </label>
          <label className="text-sm text-muted">
            Genre
            <input
              name="genre"
              defaultValue={params.genre ?? ""}
              placeholder="Fantasy, Mystery..."
              className="mt-2 w-full rounded-2xl border border-white/10 bg-panel/70 px-4 py-3 text-sm text-text outline-none"
            />
          </label>
          <button className="mt-2 rounded-full bg-text px-4 py-3 text-sm font-medium text-canvas" type="submit">
            Apply filters
          </button>
        </form>
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-2xl font-semibold text-text">Books</h2>
          <p className="text-sm text-muted">{books.length} results</p>
        </div>
        {books.length ? (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {books.map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        ) : (
          <div className="rounded-[28px] border border-dashed border-white/10 bg-panel/50 p-10 text-sm text-muted">
            No books yet. Trigger `POST /api/books/upload/` to ingest a catalog.
          </div>
        )}
      </section>
    </div>
  );
}
