"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  AlertTriangle,
  Brain,
  ClipboardList,
  Database,
  FileText,
  Loader2,
  Send,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type CorpusChunk = {
  index: number;
  chunk_id?: string;
  source: string;
  content: string;
  similarity: number | null;
};

type Risk = {
  label: string;
  reason: string;
};

type SystemResult = {
  status: string;
  response: string;
  sources?: string[];
  chunks?: CorpusChunk[];
  risk?: Risk;
  response_time_seconds?: number;
};

type CompareResponse = {
  status: string;
  conversation_id?: number;
  systems: {
    s0: SystemResult;
    corpus: SystemResult;
    s1: SystemResult;
    s2: SystemResult;
  };
};

type StoredMessage = {
  id: number;
  role: "user" | "assistant" | "system";
  content: string;
  metadata?: CompareResponse;
  created_at: string;
};

type StoredConversation = {
  id: number;
  title: string;
  messages: StoredMessage[];
};

type ResultRow = {
  id: string;
  question: string;
  time: string;
  systems?: CompareResponse["systems"];
  error?: string;
};

type CompareSettings = {
  topK: number;
  similarityThreshold: number;
  temperature: number;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const columns = [
  {
    key: "s0",
    title: "S0",
    subtitle: "Basic chatbot",
    icon: Brain,
    color: "text-slate-700",
    border: "border-slate-200",
    accent: "bg-slate-100",
  },
  {
    key: "corpus",
    title: "Research Corpus",
    subtitle: "Retrieved chunks",
    icon: Database,
    color: "text-amber-700",
    border: "border-amber-200",
    accent: "bg-amber-100",
  },
  {
    key: "s1",
    title: "S1",
    subtitle: "Basic RAG",
    icon: Sparkles,
    color: "text-blue-700",
    border: "border-blue-200",
    accent: "bg-blue-100",
  },
  {
    key: "s2",
    title: "S2",
    subtitle: "Safety-aware RAG",
    icon: ShieldCheck,
    color: "text-emerald-700",
    border: "border-emerald-200",
    accent: "bg-emerald-100",
  },
] as const;

function SettingSlider({
  label,
  value,
  min,
  max,
  step,
  onChange,
  format = String,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
  format?: (value: number) => string;
}) {
  return (
    <label className="grid gap-1.5 min-w-[150px]">
      <span className="flex items-center justify-between gap-3 font-display text-[10px] font-bold uppercase tracking-wide text-muted-foreground">
        {label}
        <span className="text-foreground">{format(value)}</span>
      </span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="accent-primary"
      />
    </label>
  );
}

function SourceList({ sources }: { sources?: string[] }) {
  if (!sources?.length) return null;

  return (
    <div className="mt-3 flex flex-wrap gap-1.5">
      {sources.slice(0, 3).map((source) => (
        <span
          key={source}
          className="inline-flex max-w-full items-center gap-1 rounded-md bg-secondary px-2 py-1 text-[10px] font-medium text-muted-foreground"
        >
          <FileText className="h-3 w-3 shrink-0" />
          <span className="truncate">{source}</span>
        </span>
      ))}
      {sources.length > 3 && (
        <span className="rounded-md bg-secondary px-2 py-1 text-[10px] font-medium text-muted-foreground">
          +{sources.length - 3}
        </span>
      )}
    </div>
  );
}

function ChunkList({ chunks }: { chunks?: CorpusChunk[] }) {
  if (!chunks?.length) {
    return (
      <p className="mt-4 rounded-md border border-dashed border-border bg-secondary/40 p-3 text-xs leading-relaxed text-muted-foreground">
        No chunks retrieved yet.
      </p>
    );
  }

  return (
    <div className="mt-4 space-y-2">
      {chunks.slice(0, 5).map((chunk) => {
        const match = chunk.similarity !== null ? Math.round(chunk.similarity * 100) : null;
        return (
          <details key={`${chunk.chunk_id}-${chunk.index}`} className="rounded-md border border-border bg-card">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-2 px-3 py-2 text-xs font-semibold">
              <span className="min-w-0 truncate">
                {chunk.chunk_id ?? `C${chunk.index}`} · {chunk.source}
              </span>
              {match !== null && (
                <span className="shrink-0 rounded bg-secondary px-1.5 py-0.5 font-display text-[10px] text-muted-foreground">
                  {match}%
                </span>
              )}
            </summary>
            <p className="border-t border-border px-3 py-2 font-mono text-[11px] leading-relaxed text-foreground/70">
              {chunk.content}
            </p>
          </details>
        );
      })}
    </div>
  );
}

function SystemPanel({
  config,
  result,
  loading,
}: {
  config: (typeof columns)[number];
  result?: SystemResult;
  loading: boolean;
}) {
  const Icon = config.icon;
  const isCorpus = config.key === "corpus";
  const isSafety = config.key === "s2";

  return (
    <section className={`flex min-h-[420px] min-w-[280px] flex-col rounded-lg border ${config.border} bg-card`}>
      <div className="flex items-center gap-3 border-b border-border px-4 py-3">
        <div className={`grid h-9 w-9 place-items-center rounded-md ${config.accent} ${config.color}`}>
          <Icon className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <h2 className="font-display text-sm font-bold tracking-normal">{config.title}</h2>
          <p className="text-xs text-muted-foreground">{config.subtitle}</p>
          {result?.response_time_seconds !== undefined && (
            <p className="mt-0.5 font-mono text-[10px] text-muted-foreground">
              {result.response_time_seconds.toFixed(2)}s
            </p>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {loading && (
          <div className="flex h-full min-h-52 items-center justify-center text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
          </div>
        )}

        {!loading && !result && (
          <div className="flex h-full min-h-52 flex-col items-center justify-center gap-2 text-center text-muted-foreground">
            <ClipboardList className="h-6 w-6" />
            <p className="text-sm">Waiting for a question.</p>
          </div>
        )}

        {!loading && result && (
          <>
            {isSafety && result.risk && (
              <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 p-3">
                <div className="flex items-center gap-2 font-display text-[11px] font-bold uppercase tracking-wide text-emerald-700">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  {result.risk.label}
                </div>
                <p className="mt-1 text-xs leading-relaxed text-emerald-900/75">{result.risk.reason}</p>
              </div>
            )}

            {result.status === "error" && (
              <div className="mb-4 flex gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-xs text-destructive">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <span>{result.response}</span>
              </div>
            )}

            <div className="prose prose-sm max-w-none text-[13px] leading-relaxed text-foreground/85 prose-headings:font-display prose-headings:tracking-normal">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{result.response || "No response."}</ReactMarkdown>
            </div>

            <SourceList sources={result.sources} />
            {(isCorpus || isSafety || config.key === "s1") && <ChunkList chunks={result.chunks} />}
          </>
        )}
      </div>
    </section>
  );
}

export function ChatView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const docFilter = searchParams.get("doc");
  const selectedConversationId = searchParams.get("conversation");
  const [input, setInput] = useState("");
  const [settings, setSettings] = useState<CompareSettings>({
    topK: 5,
    similarityThreshold: 0,
    temperature: 0.3,
  });
  const [rows, setRows] = useState<ResultRow[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [loadingConversation, setLoadingConversation] = useState(false);
  const [loadingRowId, setLoadingRowId] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [rows, loadingRowId]);

  useEffect(() => {
    if (!selectedConversationId) {
      setConversationId(null);
      setRows([]);
      return;
    }

    const id = Number(selectedConversationId);
    if (!Number.isInteger(id)) {
      setConversationId(null);
      setRows([]);
      return;
    }

    const loadConversation = async () => {
      setLoadingConversation(true);
      try {
        const response = await fetch(`${API_URL}/conversations/${id}`, {
          cache: "no-store",
        });
        if (!response.ok) throw new Error("Conversation not found");
        const conversation: StoredConversation = await response.json();
        const restoredRows: ResultRow[] = [];

        for (let index = 0; index < conversation.messages.length; index += 1) {
          const userMessage = conversation.messages[index];
          if (userMessage.role !== "user") continue;
          const assistantMessage = conversation.messages
            .slice(index + 1)
            .find((message) => message.role === "assistant");
          const timestamp = new Date(userMessage.created_at);
          restoredRows.push({
            id: String(userMessage.id),
            question: userMessage.content,
            time: `${timestamp.getHours()}:${String(timestamp.getMinutes()).padStart(2, "0")}`,
            systems: assistantMessage?.metadata?.systems,
          });
        }

        setConversationId(conversation.id);
        setRows(restoredRows);
      } catch {
        setConversationId(null);
        setRows([]);
      } finally {
        setLoadingConversation(false);
      }
    };

    loadConversation();
  }, [selectedConversationId]);

  const ask = async (event?: FormEvent) => {
    event?.preventDefault();
    const question = input.trim();
    if (!question || loadingRowId) return;

    const now = new Date();
    const rowId = crypto.randomUUID();
    const row: ResultRow = {
      id: rowId,
      question,
      time: `${now.getHours()}:${String(now.getMinutes()).padStart(2, "0")}`,
    };

    setRows((current) => [...current, row]);
    setInput("");
    setLoadingRowId(rowId);

    try {
      const response = await fetch(`${API_URL}/chat/compare-systems`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: question,
          top_k: settings.topK,
          similarity_threshold: settings.similarityThreshold,
          temperature: settings.temperature,
          source_file: docFilter ?? null,
          conversation_id: conversationId,
        }),
      });
      const data: CompareResponse = await response.json();
      if (!response.ok) {
        throw new Error("The backend could not process this question.");
      }
      if (data.conversation_id) {
        setConversationId(data.conversation_id);
        router.replace(`/?conversation=${data.conversation_id}`, { scroll: false });
        window.dispatchEvent(new Event("conversation-updated"));
      }
      setRows((current) =>
        current.map((item) =>
          item.id === rowId
            ? { ...item, systems: data.systems }
            : item,
        ),
      );
    } catch {
      setRows((current) =>
        current.map((item) =>
          item.id === rowId
            ? { ...item, error: "Could not connect to the backend comparison endpoint." }
            : item,
        ),
      );
    } finally {
      setLoadingRowId(null);
    }
  };

  const latestRow = rows.at(-1);
  const loading = latestRow ? loadingRowId === latestRow.id : false;

  return (
    <div className="flex h-full min-w-0 flex-col bg-secondary">
      <header className="shrink-0 border-b border-border bg-card px-4 py-4 md:px-8">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <div className="grid h-9 w-9 place-items-center rounded-md bg-primary text-primary-foreground">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <div>
                <h1 className="font-display text-lg font-bold tracking-normal">MindBridge-RAG Evaluation</h1>
                <p className="text-xs text-muted-foreground">S0 · Corpus · S1 · S2</p>
              </div>
            </div>
            {docFilter && (
              <div className="mt-2 inline-flex items-center gap-1.5 rounded-md bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary">
                <FileText className="h-3.5 w-3.5" />
                {docFilter}
              </div>
            )}
          </div>

          <div className="grid gap-3 sm:grid-cols-3 xl:w-[560px]">
            <SettingSlider
              label="Top K"
              value={settings.topK}
              min={1}
              max={20}
              step={1}
              onChange={(topK) => setSettings((current) => ({ ...current, topK }))}
            />
            <SettingSlider
              label="Similarity"
              value={settings.similarityThreshold}
              min={0}
              max={1}
              step={0.05}
              format={(value) => value.toFixed(2)}
              onChange={(similarityThreshold) =>
                setSettings((current) => ({ ...current, similarityThreshold }))
              }
            />
            <SettingSlider
              label="Temp"
              value={settings.temperature}
              min={0}
              max={1.5}
              step={0.05}
              format={(value) => value.toFixed(2)}
              onChange={(temperature) => setSettings((current) => ({ ...current, temperature }))}
            />
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto p-4 md:p-6">
        <div className="mx-auto flex max-w-[1800px] flex-col gap-4">
          {latestRow && (
            <div className="rounded-lg border border-border bg-card px-4 py-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-sm font-semibold text-foreground">{latestRow.question}</p>
                <span className="font-display text-[10px] font-bold uppercase tracking-wide text-muted-foreground">
                  {latestRow.time}
                </span>
              </div>
              {latestRow.error && (
                <p className="mt-2 text-xs text-destructive">{latestRow.error}</p>
              )}
            </div>
          )}

          {!latestRow && !loadingConversation && (
            <div className="rounded-lg border border-border bg-card p-6">
              <p className="text-sm font-semibold">Ask a benchmark-style student question to compare all systems.</p>
              <p className="mt-1 text-xs text-muted-foreground">
                The four columns match the required project comparison: S0, research corpus, S1, and S2.
              </p>
            </div>
          )}

          {loadingConversation && (
            <div className="flex min-h-40 items-center justify-center text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
            </div>
          )}

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-4">
            {columns.map((column) => (
              <SystemPanel
                key={column.key}
                config={column}
                result={latestRow?.systems?.[column.key]}
                loading={loading}
              />
            ))}
          </div>

          {rows.length > 1 && (
            <div className="rounded-lg border border-border bg-card p-4">
              <h2 className="font-display text-xs font-bold uppercase tracking-wide text-muted-foreground">
                Previous Questions
              </h2>
              <div className="mt-3 grid gap-2">
                {rows.slice(0, -1).reverse().map((row) => (
                  <button
                    key={row.id}
                    type="button"
                    onClick={() => setRows((current) => [...current.filter((item) => item.id !== row.id), row])}
                    className="rounded-md bg-secondary px-3 py-2 text-left text-xs font-medium text-foreground/80 hover:bg-secondary/70"
                  >
                    {row.question}
                  </button>
                ))}
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>
      </main>

      <form onSubmit={ask} className="shrink-0 border-t border-border bg-card p-4 md:px-8">
        <div className="mx-auto flex max-w-[1800px] items-end gap-3">
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                ask();
              }
            }}
            rows={2}
            placeholder="Ask a student wellbeing or academic support question..."
            className="min-h-14 flex-1 resize-none rounded-lg border border-border bg-secondary/60 px-4 py-3 text-sm outline-none transition focus:border-primary focus:ring-1 focus:ring-primary"
          />
          <button
            type="submit"
            disabled={!input.trim() || Boolean(loadingRowId)}
            className="grid h-14 w-14 shrink-0 place-items-center rounded-lg bg-primary text-primary-foreground shadow-sm transition hover:opacity-90 disabled:opacity-40"
            title="Send"
          >
            {loadingRowId ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
          </button>
        </div>
      </form>
    </div>
  );
}
