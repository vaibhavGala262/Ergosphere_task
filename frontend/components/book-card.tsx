import Link from "next/link";

import { Book } from "@/lib/types";

export function BookCard({ book }: { book: Book }) {
  return (
    <Link
      href={`/books/${book.id}`}
      className="group overflow-hidden rounded-[28px] border border-white/10 bg-panel/80 p-6 shadow-glow transition hover:-translate-y-1 hover:border-accent/60"
    >
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-muted">{book.genre || "Unclassified"}</p>
          <h3 className="mt-2 text-xl font-semibold text-text">{book.title}</h3>
          <p className="mt-1 text-sm text-muted">{book.author}</p>
        </div>
        <div className="rounded-full bg-accent/15 px-3 py-1 text-sm text-accent">{book.rating.toFixed(1)}</div>
      </div>
      <p className="line-clamp-4 text-sm leading-6 text-muted">{book.description_preview}</p>
      <div className="mt-6 flex items-center justify-between text-xs text-muted">
        <span>{book.sentiment || "Neutral tone"}</span>
        <span className="transition group-hover:text-accent">Open insights</span>
      </div>
    </Link>
  );
}
