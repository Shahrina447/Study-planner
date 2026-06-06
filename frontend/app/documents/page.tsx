"use client";

import { AppShell } from "../../src/components/AppShell";
import {
  UploadCloud,
  FileText,
  Trash2,
  CheckCircle2,
  Loader2,
  MessageSquare,
  HelpCircle,
  RefreshCw,
  BookOpen,
} from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type IndexedDoc = {
  filename: string;
  chunks: number;
  indexed_at: string | null;
};

type UploadingDoc = {
  filename: string;
  status: "uploading" | "error";
};

export default function DocumentsPage() {
  const [indexed, setIndexed] = useState<IndexedDoc[]>([]);
  const [uploading, setUploading] = useState<UploadingDoc[]>([]);
  const [loading, setLoading] = useState(true);

  // ── fetch indexed docs from backend ──────────────────────────────────────
  const fetchDocs = useCallback(async () => {
    try {
      const res = await fetch(`${API}/documents`);
      const data = await res.json();
      setIndexed(data.documents ?? []);
    } catch {
      // backend not reachable — keep whatever we have
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

  // ── upload ────────────────────────────────────────────────────────────────
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    // reset input so same file can be re-uploaded
    e.target.value = "";

    setUploading((prev) => [
      { filename: file.name, status: "uploading" },
      ...prev,
    ]);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API}/upload`, { method: "POST", body: formData });
      const data = await res.json();
      if (data.status === "success") {
        // refresh the indexed list
        await fetchDocs();
      }
      setUploading((prev) => prev.filter((u) => u.filename !== file.name));
    } catch {
      setUploading((prev) =>
        prev.map((u) =>
          u.filename === file.name ? { ...u, status: "error" } : u
        )
      );
    }
  };

  // ── delete ────────────────────────────────────────────────────────────────
  const handleDelete = async (filename: string) => {
    try {
      await fetch(`${API}/documents/${encodeURIComponent(filename)}`, {
        method: "DELETE",
      });
      setIndexed((prev) => prev.filter((d) => d.filename !== filename));
    } catch {
      // silently fail
    }
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return "—";
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const totalChunks = indexed.reduce((sum, d) => sum + d.chunks, 0);
  const allDocs = [
    ...uploading,
    ...indexed.map((d) => ({ ...d, status: "indexed" as const })),
  ];

  return (
    <AppShell>
      <div className="px-6 md:px-12 py-10 max-w-4xl mx-auto">

        {/* Header */}
        <header className="mb-8">
          <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Library</p>
          <h1 className="text-4xl md:text-5xl mt-2 font-display font-bold">Your Knowledge Base</h1>
          <p className="text-muted-foreground mt-3 max-w-xl text-sm leading-relaxed">
            Upload syllabi, lecture slides, or past papers. Every file is chunked, embedded, and indexed — so your chat and quiz answers come from your own materials.
          </p>
        </header>

        {/* Stats row */}
        {indexed.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            <div className="rounded-2xl bg-card border border-border px-5 py-4">
              <p className="text-[11px] uppercase tracking-widest text-muted-foreground font-display">Documents</p>
              <p className="text-3xl font-display font-bold mt-1">{indexed.length}</p>
            </div>
            <div className="rounded-2xl bg-card border border-border px-5 py-4">
              <p className="text-[11px] uppercase tracking-widest text-muted-foreground font-display">Total Chunks</p>
              <p className="text-3xl font-display font-bold mt-1">{totalChunks.toLocaleString()}</p>
            </div>
            <div className="rounded-2xl bg-primary/10 border border-primary/20 px-5 py-4 flex flex-col justify-between gap-3 sm:gap-0">
              <p className="text-[11px] uppercase tracking-widest text-primary font-display font-bold">Ready to use</p>
              <div className="flex gap-2 mt-2">
                <Link
                  href="/"
                  className="flex-1 flex items-center justify-center gap-1.5 rounded-xl bg-primary text-primary-foreground text-[11px] font-display font-bold uppercase tracking-tight py-2 hover:opacity-90 transition-all"
                >
                  <MessageSquare className="h-3 w-3" /> Chat
                </Link>
                <Link
                  href="/quiz"
                  className="flex-1 flex items-center justify-center gap-1.5 rounded-xl bg-secondary text-foreground text-[11px] font-display font-bold uppercase tracking-tight py-2 hover:bg-secondary/80 transition-all"
                >
                  <HelpCircle className="h-3 w-3" /> Quiz
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* Upload drop zone */}
        <label
          className={`block rounded-3xl border-2 border-dashed border-border bg-card hover:bg-accent/20 hover:border-primary/40 transition-all p-10 text-center cursor-pointer mb-8 ${
            uploading.length > 0 ? "opacity-60 pointer-events-none" : ""
          }`}
        >
          <UploadCloud className="h-8 w-8 mx-auto text-muted-foreground mb-3" />
          <p className="text-foreground font-medium text-sm">
            {uploading.length > 0 ? "Indexing…" : "Drop a file or click to upload"}
          </p>
          <p className="text-xs text-muted-foreground mt-1">PDF · TXT · DOCX</p>
          <input
            type="file"
            accept=".pdf,.txt,.docx"
            className="hidden"
            onChange={handleUpload}
            disabled={uploading.length > 0}
          />
        </label>

        {/* Document list */}
        {loading ? (
          <div className="flex items-center justify-center gap-2 py-16 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-sm">Loading your library…</span>
          </div>
        ) : allDocs.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
            <div className="h-14 w-14 rounded-2xl bg-secondary grid place-items-center">
              <BookOpen className="h-7 w-7 text-muted-foreground" />
            </div>
            <p className="font-display text-sm font-bold text-foreground/70">No documents yet</p>
            <p className="text-xs text-muted-foreground max-w-xs">
              Upload your first document above to start chatting with your notes.
            </p>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-xs uppercase tracking-[0.22em] text-muted-foreground font-display">
                Indexed documents · {indexed.length}
              </h2>
              <button
                onClick={fetchDocs}
                className="flex items-center gap-1.5 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
              >
                <RefreshCw className="h-3 w-3" /> Refresh
              </button>
            </div>

            <div className="rounded-2xl border border-border bg-card overflow-hidden divide-y divide-border">
              {allDocs.map((doc) => {
                const isUploading = doc.status === "uploading";
                const isError = doc.status === "error";
                const isIndexed = doc.status === "indexed";

                return (
                  <div
                    key={doc.filename}
                    className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-5 py-4 hover:bg-accent/10 transition-colors"
                  >
                    {/* Left: Icon & Info */}
                    <div className="flex items-center gap-4 min-w-0">
                      <div className={`h-10 w-10 rounded-xl grid place-items-center shrink-0 ${
                        isIndexed ? "bg-primary/10 text-primary" : "bg-secondary text-muted-foreground"
                      }`}>
                        <FileText className="h-5 w-5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[14px] font-medium text-foreground truncate">
                          {doc.filename}
                        </p>
                        <p className="text-[11px] text-muted-foreground mt-0.5 font-mono">
                          {isIndexed
                            ? `${(doc as IndexedDoc).chunks} chunks · indexed ${formatDate((doc as IndexedDoc).indexed_at)}`
                            : isUploading
                            ? "Uploading and indexing…"
                            : "Upload failed"}
                        </p>
                      </div>
                    </div>

                    {/* Right: Status & Actions */}
                    <div className="flex items-center justify-between sm:justify-end gap-2 shrink-0">
                      {isIndexed && (
                        <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-emerald-600 bg-emerald-50 border border-emerald-200 rounded-full px-2.5 py-1">
                          <CheckCircle2 className="h-3.5 w-3.5" /> Indexed
                        </span>
                      )}
                      {isUploading && (
                        <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-amber-600 bg-amber-50 border border-amber-200 rounded-full px-2.5 py-1">
                          <Loader2 className="h-3.5 w-3.5 animate-spin" /> Indexing
                        </span>
                      )}
                      {isError && (
                        <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-rose-600 bg-rose-50 border border-rose-200 rounded-full px-2.5 py-1">
                          Error
                        </span>
                      )}

                      {isIndexed && (
                        <div className="flex items-center gap-1">
                          <Link
                            href={`/?doc=${encodeURIComponent(doc.filename)}`}
                            className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition-colors text-[11px] font-display font-bold"
                            title="Chat with this document"
                          >
                            <MessageSquare className="h-3.5 w-3.5" />
                            <span>Chat</span>
                          </Link>
                          <Link
                            href={`/quiz?doc=${encodeURIComponent(doc.filename)}`}
                            className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-secondary hover:bg-secondary/80 text-foreground transition-colors text-[11px] font-display font-bold"
                            title="Quiz from this document"
                          >
                            <HelpCircle className="h-3.5 w-3.5" />
                            <span>Quiz</span>
                          </Link>
                          <button
                            onClick={() => handleDelete(doc.filename)}
                            className="p-1.5 text-muted-foreground hover:text-destructive transition-colors rounded-lg hover:bg-destructive/10"
                            title="Remove from index"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Call to action */}
            {indexed.length > 0 && (
              <div className="mt-6 rounded-2xl bg-primary/5 border border-primary/20 p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-foreground">
                    {indexed.length} document{indexed.length > 1 ? "s" : ""} ready
                  </p>
                  <p className="text-[12px] text-muted-foreground mt-0.5">
                    Start a conversation or generate a quiz from your indexed materials.
                  </p>
                </div>
                <div className="flex gap-2 shrink-0 w-full sm:w-auto">
                  <Link
                    href="/"
                    className="flex-1 sm:flex-initial flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-display font-bold uppercase tracking-tight hover:opacity-90 transition-all"
                  >
                    <MessageSquare className="h-3.5 w-3.5" /> Chat now
                  </Link>
                  <Link
                    href="/quiz"
                    className="flex-1 sm:flex-initial flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-card border border-border text-foreground text-xs font-display font-bold uppercase tracking-tight hover:bg-secondary transition-all"
                  >
                    <HelpCircle className="h-3.5 w-3.5" /> Take quiz
                  </Link>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}
