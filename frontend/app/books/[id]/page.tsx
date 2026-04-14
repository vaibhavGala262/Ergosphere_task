import Link from "next/link";

import { BookCard } from "@/components/book-card";
import { api } from "@/lib/api";

export default async function BookDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [book, recommendations] = await Promise.all([api.getBook(id), api.recommendBooks(id)]);

  return (
    <div className="space-y-8">
      <section className="rounded-[34px] border border-white/10 bg-panel/75 p-8 shadow-glow">
        <Link href="/" className="text-sm text-accent">
          Back to dashboard
        </Link>
        <div className="mt-5 flex flex-wrap items-start justify-between gap-6">
          <div className="max-w-3xl">
            <p className="text-xs uppercase tracking-[0.32em] text-muted">{book.genre || "General"}</p>
            <h2 className="mt-3 text-4xl font-semibold text-text">{book.title}</h2>
            <p className="mt-2 text-base text-muted">by {book.author}</p>
          </div>
          <div className="rounded-[24px] bg-accent/15 px-5 py-4 text-right">
            <p className="text-xs uppercase tracking-[0.28em] text-muted">Rating</p>
            <p className="mt-2 text-3xl font-semibold text-accent">{book.rating.toFixed(1)}</p>
          </div>
        </div>
        <div className="mt-8 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <article className="rounded-[26px] border border-white/10 bg-canvas/40 p-6">
            <h3 className="text-lg font-semibold text-text">Full Description</h3>
            <p className="mt-4 text-sm leading-7 text-muted">{book.description}</p>
          </article>
          <div className="space-y-6">
            <article className="rounded-[26px] border border-white/10 bg-canvas/40 p-6">
              <h3 className="text-lg font-semibold text-text">AI Summary</h3>
              <p className="mt-4 whitespace-pre-line text-sm leading-7 text-muted">{book.ai_summary || "Pending summary."}</p>
            </article>
            <article className="grid gap-4 rounded-[26px] border border-white/10 bg-canvas/40 p-6 sm:grid-cols-2">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-muted">Genre</p>
                <p className="mt-2 text-base text-text">{book.genre || "General"}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-muted">Sentiment</p>
                <p className="mt-2 text-base text-text">{book.sentiment || "Neutral"}</p>
              </div>
            </article>
          </div>
        </div>
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-2xl font-semibold text-text">Recommendations</h3>
          <a href={book.url} target="_blank" rel="noreferrer" className="text-sm text-accent">
            Source page
          </a>
        </div>
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {recommendations.map((item) => (
            <BookCard key={item.id} book={item} />
          ))}
        </div>
      </section>
    </div>
  );
}
