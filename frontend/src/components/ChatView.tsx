"use client";

import { useState, useRef, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import {
  Send,
  Paperclip,
  Copy,
  BookOpen,
  Zap,
  Settings2,
  X,
  Brain,
  Database,
  GitCompare,
  ChevronDown,
  FileText,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// ─── Types ────────────────────────────────────────────────────────────────────

type ResponseMode = "ai" | "corpus" | "compare";

type CorpusChunk = {
  index: number;
  source: string;
  content: string;
  similarity: number | null;
};

type Message = {
  id: string;
  role: "user" | "bot";
  text?: string;
  // compare mode
  aiText?: string;
  corpusText?: string;
  chunks?: CorpusChunk[];
  mode?: ResponseMode;
  sources?: string[];
  time: string;
};

// ─── Settings Panel ───────────────────────────────────────────────────────────

type RAGSettings = {
  topK: number;
  similarityThreshold: number;
  temperature: number;
  mode: ResponseMode;
};

function SettingsPanel({
  settings,
  onChange,
  onClose,
}: {
  settings: RAGSettings;
  onChange: (s: RAGSettings) => void;
  onClose: () => void;
}) {
  const modes: { id: ResponseMode; label: string; icon: typeof Brain; desc: string }[] = [
    { id: "ai", label: "AI Response", icon: Brain, desc: "Mistral synthesises an answer from retrieved chunks" },
    { id: "corpus", label: "Corpus Only", icon: Database, desc: "One unified answer synthesised from all your documents, with inline citations" },
    { id: "compare", label: "Compare", icon: GitCompare, desc: "Side-by-side: AI answer vs raw corpus passages" },
  ];

  return (
    <div className="flex flex-col bg-card border border-border rounded-2xl shadow-lg overflow-hidden h-full">
      <div className="flex items-center justify-between px-5 py-4 border-b border-border">
        <div className="flex items-center gap-2">
          <Settings2 className="h-4 w-4 text-primary" />
          <span className="font-display text-sm font-bold tracking-tight">RAG Settings</span>
        </div>
        <button
          onClick={onClose}
          className="h-7 w-7 rounded-lg hover:bg-secondary flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-7">
        {/* Response Mode */}
        <div>
          <label className="font-display text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground block mb-3">
            Response Mode
          </label>
          <div className="space-y-2">
            {modes.map((m) => {
              const Icon = m.icon;
              const active = settings.mode === m.id;
              return (
                <button
                  key={m.id}
                  onClick={() => onChange({ ...settings, mode: m.id })}
                  className={`w-full flex items-start gap-3 p-3 rounded-xl border text-left transition-all ${
                    active
                      ? "border-primary bg-primary/5 text-foreground"
                      : "border-border hover:border-primary/40 text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Icon className={`h-4 w-4 mt-0.5 shrink-0 ${active ? "text-primary" : ""}`} />
                  <div>
                    <p className="text-xs font-semibold">{m.label}</p>
                    <p className="text-[11px] opacity-70 mt-0.5 leading-tight">{m.desc}</p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Top-K */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="font-display text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">
              Top-K Chunks
            </label>
            <span className="font-display text-xs font-bold text-primary tabular-nums">
              {settings.topK}
            </span>
          </div>
          <input
            type="range"
            min={1}
            max={20}
            step={1}
            value={settings.topK}
            onChange={(e) => onChange({ ...settings, topK: Number(e.target.value) })}
            className="w-full accent-primary h-1.5 rounded-full cursor-pointer"
          />
          <div className="flex justify-between mt-1">
            <span className="font-display text-[9px] text-muted-foreground">1</span>
            <span className="font-display text-[9px] text-muted-foreground">20</span>
          </div>
          <p className="text-[11px] text-muted-foreground mt-1.5 leading-snug">
            Number of document chunks retrieved from the vector store per query.
          </p>
        </div>

        {/* Similarity Threshold */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="font-display text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">
              Similarity Threshold
            </label>
            <span className="font-display text-xs font-bold text-primary tabular-nums">
              {settings.similarityThreshold.toFixed(2)}
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={settings.similarityThreshold}
            onChange={(e) =>
              onChange({ ...settings, similarityThreshold: Number(e.target.value) })
            }
            className="w-full accent-primary h-1.5 rounded-full cursor-pointer"
          />
          <div className="flex justify-between mt-1">
            <span className="font-display text-[9px] text-muted-foreground">0.00</span>
            <span className="font-display text-[9px] text-muted-foreground">1.00</span>
          </div>
          <p className="text-[11px] text-muted-foreground mt-1.5 leading-snug">
            Minimum cosine similarity required for a chunk to be included. Higher = more relevant only.
          </p>
        </div>

        {/* Temperature */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="font-display text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">
              Temperature
            </label>
            <span className="font-display text-xs font-bold text-primary tabular-nums">
              {(settings.temperature ?? 0.3).toFixed(2)}
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={1.5}
            step={0.05}
            value={settings.temperature ?? 0.3}
            onChange={(e) => onChange({ ...settings, temperature: Number(e.target.value) })}
            className="w-full accent-primary h-1.5 rounded-full cursor-pointer"
          />
          <div className="flex justify-between mt-1">
            <span className="font-display text-[9px] text-muted-foreground">0.00 · Precise</span>
            <span className="font-display text-[9px] text-muted-foreground">1.50 · Creative</span>
          </div>
          <p className="text-[11px] text-muted-foreground mt-1.5 leading-snug">
            Controls how creative or focused the AI response is. Lower = more factual, higher = more varied.
          </p>
        </div>

        {/* Summary */}
        <div className="rounded-xl bg-secondary/50 border border-border p-3 space-y-1.5">
          <p className="font-display text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground mb-2">
            Current Config
          </p>
          <div className="flex justify-between text-[12px]">
            <span className="text-muted-foreground">Mode</span>
            <span className="font-semibold text-foreground capitalize">{settings.mode}</span>
          </div>
          <div className="flex justify-between text-[12px]">
            <span className="text-muted-foreground">Top-K</span>
            <span className="font-semibold text-foreground">{settings.topK} chunks</span>
          </div>
          <div className="flex justify-between text-[12px]">
            <span className="text-muted-foreground">Min. Similarity</span>
            <span className="font-semibold text-foreground">{settings.similarityThreshold.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-[12px]">
            <span className="text-muted-foreground">Temperature</span>
            <span className="font-semibold text-foreground">{(settings.temperature ?? 0.3).toFixed(2)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Compare View ─────────────────────────────────────────────────────────────

function CompareView({ aiText, corpusText, chunks }: { aiText: string; corpusText: string; chunks?: CorpusChunk[] }) {
  const [activeTab, setActiveTab] = useState<"ai" | "corpus">("ai");
  const [expandedChunk, setExpandedChunk] = useState<number | null>(null);

  return (
    <div className="w-full">
      {/* Tab switcher */}
      <div className="flex gap-1 p-1 bg-secondary/70 rounded-xl mb-4">
        <button
          onClick={() => setActiveTab("ai")}
          className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-[12px] font-display font-bold uppercase tracking-wide transition-all ${
            activeTab === "ai"
              ? "bg-card shadow-sm text-violet-600 border border-violet-200/60"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <Brain className="h-3.5 w-3.5" />
          AI Synthesis
        </button>
        <button
          onClick={() => setActiveTab("corpus")}
          className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-[12px] font-display font-bold uppercase tracking-wide transition-all ${
            activeTab === "corpus"
              ? "bg-card shadow-sm text-amber-600 border border-amber-200/60"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <Database className="h-3.5 w-3.5" />
          From Documents
        </button>
      </div>

      {/* AI Tab */}
      {activeTab === "ai" && (
        <div className="rounded-2xl bg-gradient-to-br from-violet-50 to-violet-50/30 border border-violet-200/60 p-5">
          <div className="flex items-center gap-2 mb-3">
            <div className="h-6 w-6 rounded-lg bg-violet-500 text-white grid place-items-center">
              <Brain className="h-3.5 w-3.5" />
            </div>
            <span className="font-display text-[11px] font-bold uppercase tracking-widest text-violet-600">
              AI-Synthesised Answer
            </span>
          </div>
          <div className="prose prose-sm dark:prose-invert max-w-none text-[14px] leading-relaxed text-foreground/85">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{aiText}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* Corpus Tab */}
      {activeTab === "corpus" && (
        <div className="space-y-3">
          {/* Unified corpus answer */}
          <div className="rounded-2xl bg-gradient-to-br from-amber-50 to-amber-50/30 border border-amber-200/60 p-5">
            <div className="flex items-center gap-2 mb-3">
              <div className="h-6 w-6 rounded-lg bg-amber-500 text-white grid place-items-center">
                <Database className="h-3.5 w-3.5" />
              </div>
              <span className="font-display text-[11px] font-bold uppercase tracking-widest text-amber-600">
                Answer from Your Documents
              </span>
            </div>
            <div className="prose prose-sm dark:prose-invert max-w-none text-[14px] leading-relaxed text-foreground/85">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{corpusText}</ReactMarkdown>
            </div>
          </div>

          {/* Source passages — collapsible */}
          {chunks && chunks.length > 0 && (
            <div>
              <p className="font-display text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground px-1 mb-2">
                Source passages ({chunks.length})
              </p>
              <div className="space-y-2">
                {chunks.map((chunk) => {
                  const isExpanded = expandedChunk === chunk.index;
                  const matchPct = chunk.similarity !== null ? Math.round(chunk.similarity * 100) : null;
                  const matchColor =
                    chunk.similarity === null ? ""
                    : chunk.similarity >= 0.7 ? "text-emerald-600 bg-emerald-50 border-emerald-200"
                    : chunk.similarity >= 0.4 ? "text-amber-600 bg-amber-50 border-amber-200"
                    : "text-rose-600 bg-rose-50 border-rose-200";

                  return (
                    <div key={chunk.index} className="rounded-xl border border-border bg-card overflow-hidden">
                      <button
                        onClick={() => setExpandedChunk(isExpanded ? null : chunk.index)}
                        className="w-full flex items-center justify-between gap-3 px-4 py-3 hover:bg-secondary/40 transition-colors text-left"
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          <span className="h-5 w-5 rounded-md bg-secondary grid place-items-center font-display text-[10px] font-bold text-muted-foreground shrink-0">
                            {chunk.index}
                          </span>
                          <span className="text-[12px] text-foreground/80 truncate font-medium">
                            {chunk.source.replace(/\.pdf$/i, "")}
                          </span>
                          {matchPct !== null && (
                            <span className={`font-display text-[10px] font-bold px-2 py-0.5 rounded-full border shrink-0 ${matchColor}`}>
                              {matchPct}% match
                            </span>
                          )}
                        </div>
                        <div className={`h-5 w-5 rounded-full border grid place-items-center shrink-0 transition-transform ${isExpanded ? "rotate-180 border-primary text-primary" : "border-border text-muted-foreground"}`}>
                          <ChevronDown className="h-3 w-3" />
                        </div>
                      </button>
                      {isExpanded && (
                        <div className="px-4 pb-4 pt-1 border-t border-border/50">
                          <p className="text-[13px] leading-relaxed text-foreground/75 font-mono whitespace-pre-wrap">
                            {chunk.content}
                          </p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Bot Message ──────────────────────────────────────────────────────────────

function BotMessage({ message }: { message: Message }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    const text = message.mode === "compare" ? (message.aiText ?? "") : (message.text ?? "");
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };

  const modeLabel =
    message.mode === "ai"
      ? { label: "AI", icon: Brain, color: "text-violet-500" }
      : message.mode === "corpus"
      ? { label: "Corpus", icon: Database, color: "text-amber-500" }
      : message.mode === "compare"
      ? { label: "Compare", icon: GitCompare, color: "text-primary" }
      : null;

  return (
    <div className="flex gap-4">
      <div className="h-9 w-9 shrink-0 rounded-xl bg-primary/10 text-primary grid place-items-center">
        <Zap className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        {/* Source badge + mode pill */}
        <div className="flex flex-wrap items-center gap-2 mb-2">
          {message.sources && message.sources.length > 0 && (
            <div className="inline-flex items-center gap-2 rounded-md bg-secondary text-foreground/80 px-2.5 py-1 text-[11px] font-mono">
              <BookOpen className="h-3 w-3" />
              <span>{message.sources[0]}</span>
              {message.sources.length > 1 && (
                <span className="opacity-60">+{message.sources.length - 1} more</span>
              )}
            </div>
          )}
          {modeLabel && (
            <div className={`inline-flex items-center gap-1.5 rounded-md bg-secondary px-2.5 py-1 text-[11px] font-display font-bold uppercase tracking-tight ${modeLabel.color}`}>
              <modeLabel.icon className="h-3 w-3" />
              {modeLabel.label}
            </div>
          )}
        </div>

        {/* Content */}
        {message.mode === "compare" ? (
          <div className="rounded-2xl rounded-tl-sm bg-secondary/60 border border-border/60 p-5">
            <CompareView
              aiText={message.aiText ?? ""}
              corpusText={message.corpusText ?? ""}
              chunks={message.chunks}
            />
            <div className="mt-4 flex items-center gap-4 font-display text-[10px] font-bold uppercase tracking-widest text-muted-foreground border-t border-border/40 pt-3">
              <span>{message.time}</span>
              <button onClick={handleCopy} className="inline-flex items-center gap-1 hover:text-foreground transition-colors">
                <Copy className="h-3 w-3" /> {copied ? "Copied!" : "Copy AI"}
              </button>
            </div>
          </div>
        ) : (
          <div className={`rounded-2xl rounded-tl-sm border p-5 ${
            message.mode === "corpus"
              ? "bg-gradient-to-br from-amber-50 to-amber-50/30 border-amber-200/60"
              : "bg-secondary/60 border-border/60"
          }`}>
            {message.mode === "corpus" && (
              <div className="flex items-center gap-2 mb-3">
                <div className="h-6 w-6 rounded-lg bg-amber-500 text-white grid place-items-center">
                  <Database className="h-3.5 w-3.5" />
                </div>
                <span className="font-display text-[11px] font-bold uppercase tracking-widest text-amber-600">
                  Answer from Your Documents
                </span>
              </div>
            )}
            <div className="prose prose-sm dark:prose-invert max-w-none text-[15px] leading-relaxed text-foreground/85">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.text ?? ""}</ReactMarkdown>
            </div>
            <div className="mt-4 flex items-center gap-4 font-display text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
              <span>{message.time}</span>
              <button onClick={handleCopy} className="inline-flex items-center gap-1 hover:text-foreground transition-colors">
                <Copy className="h-3 w-3" /> {copied ? "Copied!" : "Copy"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── ChatView ─────────────────────────────────────────────────────────────────

const seed: Message[] = [];

export function ChatView() {
  const searchParams = useSearchParams();
  const docFilter = searchParams.get("doc"); // e.g. "StudyPlan_v7.pdf"

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [ragSettings, setRagSettings] = useState<RAGSettings>({
    topK: 5,
    similarityThreshold: 0.0,
    temperature: 0.3,
    mode: "ai",
  });
  // Track the last user question so we can re-fetch on mode change
  const lastQuestionRef = useRef<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  const modeBadge = {
    ai: { label: "AI", color: "bg-violet-100 text-violet-700" },
    corpus: { label: "Corpus", color: "bg-amber-100 text-amber-700" },
    compare: { label: "Compare", color: "bg-primary/10 text-primary" },
  }[ragSettings.mode];

  /** Core fetch — does NOT add a user bubble, just appends a bot reply */
  const fetchResponse = async (text: string, settingsOverride: RAGSettings) => {
    const now = new Date();
    const time = `${now.getHours()}:${String(now.getMinutes()).padStart(2, "0")}`;
    setTyping(true);

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          top_k: settingsOverride.topK,
          similarity_threshold: settingsOverride.similarityThreshold,
          temperature: settingsOverride.temperature ?? 0.3,
          mode: settingsOverride.mode,
          source_file: docFilter ?? null,
        }),
      });

      const data = await response.json();

      if (settingsOverride.mode === "compare") {
        setMessages((m) => [
          ...m,
          {
            id: crypto.randomUUID(),
            role: "bot",
            mode: "compare",
            aiText: data.ai_response ?? "No AI response.",
            corpusText: data.corpus_response ?? "",
            chunks: data.chunks ?? [],
            sources: data.sources ?? [],
            time,
          },
        ]);
      } else {
        setMessages((m) => [
          ...m,
          {
            id: crypto.randomUUID(),
            role: "bot",
            mode: settingsOverride.mode,
            text: data.response ?? "Sorry, I couldn't process that.",
            sources: data.sources ?? [],
            time,
          },
        ]);
      }
    } catch {
      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "bot",
          mode: settingsOverride.mode,
          text: "Error connecting to the study assistant backend.",
          time,
        },
      ]);
    } finally {
      setTyping(false);
    }
  };

  /** Called when user submits a new question */
  const send = async (text: string) => {
    if (!text.trim()) return;
    const now = new Date();
    const time = `${now.getHours()}:${String(now.getMinutes()).padStart(2, "0")}`;
    lastQuestionRef.current = text;
    setMessages((m) => [...m, { id: crypto.randomUUID(), role: "user", text, time }]);
    setInput("");
    await fetchResponse(text, ragSettings);
  };

  /** Called when mode changes — re-fetches last question silently */
  const switchMode = (newMode: ResponseMode) => {
    const newSettings = { ...ragSettings, mode: newMode };
    setRagSettings(newSettings);
    if (lastQuestionRef.current && !typing) {
      fetchResponse(lastQuestionRef.current, newSettings);
    }
  };

  /** Called from settings panel for any setting change */
  const handleSettingsChange = (newSettings: RAGSettings) => {
    setRagSettings(newSettings);
    // If mode changed and there's a prior question, re-fetch
    if (newSettings.mode !== ragSettings.mode && lastQuestionRef.current && !typing) {
      fetchResponse(lastQuestionRef.current, newSettings);
    }
  };

  return (
    <div className="flex flex-col h-screen min-w-0">
      {/* Top bar */}
      <header className="h-20 flex items-center justify-between px-6 md:px-10 border-b border-border bg-card shrink-0">
        <div>
          <h1 className="font-display text-xl font-bold tracking-tight">Good morning, Shahrina.</h1>
          {docFilter && (
            <div className="flex items-center gap-1.5 mt-0.5">
              <FileText className="h-3 w-3 text-primary" />
              <span className="text-[11px] text-primary font-medium truncate max-w-[260px]">
                Scoped to: {docFilter}
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-3">
          {/* Mode indicator */}
          <span className={`font-display text-[10px] font-bold px-3 py-1.5 rounded-full uppercase tracking-tight ${modeBadge.color}`}>
            {modeBadge.label} Mode
          </span>
          {/* Settings toggle */}
          <button
            onClick={() => setShowSettings((v) => !v)}
            className={`h-9 w-9 rounded-xl flex items-center justify-center transition-colors ${
              showSettings
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-muted-foreground hover:text-foreground"
            }`}
            title="RAG Settings"
          >
            <Settings2 className="h-4 w-4" />
          </button>
          <div className="hidden md:flex items-center gap-2 px-4 py-1.5 bg-secondary rounded-full">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span className="font-display text-xs font-bold text-foreground/70 uppercase tracking-tight">
              RAG &bull; Mistral
            </span>
          </div>
        </div>
      </header>

      {/* Dashboard surface */}
      <div className="flex-1 flex flex-col lg:flex-row p-4 md:p-6 gap-6 overflow-hidden">
        {/* Chat centerpiece */}
        <section className="flex-[2.5] flex flex-col bg-card rounded-2xl border border-border shadow-sm overflow-hidden min-w-0">
          <div className="flex-1 overflow-y-auto p-6 md:p-8">
            {/* Messages */}
            <div className="space-y-6">
              {messages.map((m) =>
                m.role === "user" ? (
                  <div key={m.id} className="flex justify-end">
                    <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-primary text-primary-foreground px-4 py-3">
                      <p className="text-[15px] leading-relaxed">{m.text}</p>
                      <p className="font-display text-[10px] mt-1 text-primary-foreground/70 text-right">
                        {m.time}
                      </p>
                    </div>
                  </div>
                ) : (
                  <BotMessage key={m.id} message={m} />
                ),
              )}

              {typing && (
                <div className="flex gap-4">
                  <div className="h-9 w-9 shrink-0 rounded-xl bg-primary/10 text-primary grid place-items-center">
                    <Zap className="h-5 w-5" />
                  </div>
                  <div className="rounded-2xl rounded-tl-sm bg-secondary/60 border border-border/60 px-4 py-3 flex gap-1 items-center">
                    <span className="h-2 w-2 rounded-full bg-muted-foreground/50 animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="h-2 w-2 rounded-full bg-muted-foreground/50 animate-bounce" style={{ animationDelay: "120ms" }} />
                    <span className="h-2 w-2 rounded-full bg-muted-foreground/50 animate-bounce" style={{ animationDelay: "240ms" }} />
                  </div>
                </div>
              )}

              {messages.length === 0 && !typing && (
                <div className="flex flex-col items-center justify-center h-48 text-center gap-3">
                  <div className="h-12 w-12 rounded-2xl bg-primary/10 text-primary grid place-items-center">
                    <BookOpen className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="font-display text-sm font-bold text-foreground/70">
                      {docFilter ? `Chatting with ${docFilter}` : "Ask anything from your notes"}
                    </p>
                    <p className="text-[12px] text-muted-foreground mt-1">
                      {docFilter
                        ? "Questions will be answered using only this document."
                        : "Use the settings panel to switch modes and tune retrieval parameters."}
                    </p>
                  </div>
                </div>
              )}

              <div ref={endRef} />
            </div>
          </div>

          {/* Composer */}
          <div className="p-6 pt-0">
            {/* Quick mode switcher strip */}
            <div className="flex gap-2 mb-3">
              {(["ai", "corpus", "compare"] as ResponseMode[]).map((m) => {
                const Icon = m === "ai" ? Brain : m === "corpus" ? Database : GitCompare;
                const labels = { ai: "AI", corpus: "Corpus", compare: "Compare" };
                return (
                  <button
                    key={m}
                    onClick={() => switchMode(m)}
                    disabled={typing}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[11px] font-display font-bold uppercase tracking-tight transition-all disabled:opacity-50 ${
                      ragSettings.mode === m
                        ? "bg-primary text-primary-foreground shadow-sm"
                        : "bg-secondary text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    <Icon className="h-3 w-3" />
                    {labels[m]}
                  </button>
                );
              })}
              <span className="ml-auto font-display text-[10px] text-muted-foreground self-center">
                K={ragSettings.topK} · sim≥{ragSettings.similarityThreshold.toFixed(2)}
              </span>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                send(input);
              }}
              className="relative flex items-center"
            >
              <Paperclip className="absolute left-4 h-5 w-5 text-muted-foreground pointer-events-none" />
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send(input);
                  }
                }}
                rows={1}
                placeholder="Ask anything from your notes…"
                className="w-full h-14 pl-12 pr-16 bg-secondary/60 border border-border rounded-2xl text-sm resize-none outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all py-4"
              />
              <button
                type="submit"
                disabled={!input.trim() || typing}
                className="absolute right-3 w-10 h-10 bg-primary text-primary-foreground rounded-xl flex items-center justify-center hover:opacity-90 transition-all shadow-lg shadow-primary/20 disabled:opacity-40 disabled:shadow-none"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
            <p className="font-display text-center text-[10px] text-muted-foreground mt-3 uppercase tracking-tight">
              Study Planner grounds every claim with citations from your uploads.
            </p>
          </div>
        </section>

        {/* Settings Panel */}
        {showSettings && (
          <aside className="w-full lg:w-72 shrink-0">
            <SettingsPanel
              settings={ragSettings}
              onChange={handleSettingsChange}
              onClose={() => setShowSettings(false)}
            />
          </aside>
        )}
      </div>
    </div>
  );
}
