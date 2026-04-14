"use client";

import { LoaderCircle } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { api } from "@/lib/api";
import { UploadTaskStatus } from "@/lib/types";

export function IngestionPanel() {
  const [pages, setPages] = useState(2);
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState("");
  const [status, setStatus] = useState<UploadTaskStatus | null>(null);
  const [error, setError] = useState("");
  const intervalRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
      }
    };
  }, []);

  async function startIngestion() {
    setLoading(true);
    setError("");
    setStatus(null);
    try {
      const response = await api.uploadBooks(pages);
      setTaskId(response.task_id);
      pollStatus(response.task_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start ingestion");
      setLoading(false);
    }
  }

  function pollStatus(id: string) {
    if (intervalRef.current) {
      window.clearInterval(intervalRef.current);
    }
    intervalRef.current = window.setInterval(async () => {
      try {
        const next = await api.getUploadTaskStatus(id);
        setStatus(next);
        if (next.ready) {
          if (intervalRef.current) {
            window.clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          setLoading(false);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed while checking status");
        if (intervalRef.current) {
          window.clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        setLoading(false);
      }
    }, 2000);
  }

  return (
    <div className="rounded-[26px] border border-white/10 bg-canvas/40 p-5">
      <p className="text-xs uppercase tracking-[0.28em] text-muted">Ingestion</p>
      <p className="mt-2 text-sm text-muted">Scrape books asynchronously with Selenium + Celery.</p>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <label className="text-sm text-muted">
          Pages
          <input
            type="number"
            min={1}
            max={20}
            value={pages}
            onChange={(event) => setPages(Number(event.target.value))}
            className="ml-2 w-20 rounded-xl border border-white/10 bg-panel/70 px-3 py-1 text-sm text-text outline-none"
          />
        </label>
        <button
          type="button"
          onClick={startIngestion}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-full bg-accent px-4 py-2 text-sm font-medium text-slate-950 disabled:opacity-60"
        >
          {loading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
          Start scrape
        </button>
      </div>
      {taskId ? <p className="mt-3 text-xs text-muted">Task ID: {taskId}</p> : null}
      {status ? (
        <p className="mt-2 text-sm text-muted">
          Status: <span className="text-text">{status.status}</span>
          {status.result ? ` | Books saved: ${status.result.books_saved}` : ""}
        </p>
      ) : null}
      {error ? <p className="mt-2 text-sm text-rose-300">{error}</p> : null}
    </div>
  );
}
