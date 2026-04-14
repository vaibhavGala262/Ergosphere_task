import Link from "next/link";

import { QAPanel } from "@/components/qa-panel";

export default function QAPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-muted">RAG Q&A</p>
          <h2 className="mt-2 text-3xl font-semibold text-text">Grounded answers with citation-aware retrieval</h2>
        </div>
        <Link href="/" className="text-sm text-accent">
          Back to dashboard
        </Link>
      </div>
      <QAPanel />
    </div>
  );
}
