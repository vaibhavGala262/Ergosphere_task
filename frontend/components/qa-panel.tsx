"use client";

import { LoaderCircle, Sparkles } from "lucide-react";
import { FormEvent, useState } from "react";

import { api } from "@/lib/api";
import { QueryResponse } from "@/lib/types";

type Toast = { type: "success" | "error"; message: string } | null;

export function QAPanel() {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [sessionId, setSessionId] = useState("");
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<Toast>(null);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setToast(null);
    try {
      const next = await api.query(question, sessionId);
      setResponse(next);
      setSessionId(next.session_id);
      setToast({ type: "success", message: next.cached ? "Answer loaded from cache." : "Fresh answer generated." });
    } catch (error) {
      setToast({ type: "error", message: error instanceof Error ? error.message : "Something went wrong." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
      <section className="rounded-[32px] border border-white/10 bg-panel/80 p-8 shadow-glow">
        <div className="mb-6 flex items-center gap-3">
          <div className="rounded-2xl bg-accent/15 p-3 text-accent">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-2xl font-semibold text-text">Ask across your book corpus</h2>
            <p className="text-sm text-muted">RAG retrieval, citation grounding, and response caching are wired in.</p>
          </div>
        </div>
        <form onSubmit={submit} className="space-y-4">
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Which books explore grief and recovery through friendship?"
            className="min-h-40 w-full rounded-[24px] border border-white/10 bg-canvas/80 px-5 py-4 text-sm text-text outline-none transition focus:border-accent/70"
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-full bg-accent px-5 py-3 text-sm font-medium text-slate-950 transition hover:brightness-110 disabled:opacity-60"
          >
            {loading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
            Ask AI
          </button>
        </form>
        {toast ? (
          <div
            className={`mt-5 rounded-2xl px-4 py-3 text-sm ${
              toast.type === "success" ? "bg-emerald-500/15 text-emerald-200" : "bg-rose-500/15 text-rose-200"
            }`}
          >
            {toast.message}
          </div>
        ) : null}
      </section>

      <section className="rounded-[32px] border border-white/10 bg-panel/80 p-8">
        <h3 className="text-lg font-semibold text-text">Answer</h3>
        {loading ? (
          <div className="mt-6 space-y-3">
            <div className="h-4 animate-pulse rounded bg-white/10" />
            <div className="h-4 animate-pulse rounded bg-white/10" />
            <div className="h-4 animate-pulse rounded bg-white/10" />
          </div>
        ) : response ? (
          <div className="mt-6 space-y-5">
            <p className="text-sm leading-7 text-muted">{response.answer}</p>
            <div className="space-y-3">
              {response.sources.map((source) => (
                <a
                  key={`${source.title}-${source.url}`}
                  href={source.url}
                  target="_blank"
                  rel="noreferrer"
                  className="block rounded-2xl border border-white/10 bg-canvas/60 p-4 transition hover:border-accent/60"
                >
                  <p className="font-medium text-text">{source.title}</p>
                  <p className="text-xs uppercase tracking-[0.24em] text-muted">{source.author}</p>
                  <p className="mt-2 text-sm text-muted">{source.excerpt}...</p>
                </a>
              ))}
            </div>
          </div>
        ) : (
          <p className="mt-6 text-sm text-muted">Responses and citations will appear here.</p>
        )}
      </section>
    </div>
  );
}
