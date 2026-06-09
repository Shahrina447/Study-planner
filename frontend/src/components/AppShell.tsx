"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BookOpen,
  Check,
  FileText,
  HelpCircle,
  MessageSquare,
  Pencil,
  Plus,
  Trash2,
  X,
} from "lucide-react";
import type { FormEvent, ReactNode } from "react";
import { useCallback, useEffect, useState } from "react";

type NavItem = { href: string; label: string; icon: typeof MessageSquare; exact?: boolean };
const nav: NavItem[] = [
  { href: "/", label: "Chat", icon: MessageSquare, exact: true },
  { href: "/quiz", label: "Quiz Me", icon: HelpCircle },
  { href: "/documents", label: "My Documents", icon: FileText },
];

type ConversationSummary = {
  id: number;
  title: string;
  updated_at: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function AppShell({ children }: { children: ReactNode; stressScore?: number }) {
  const pathname = usePathname();
  const router = useRouter();
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);

  const loadConversations = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/conversations`, { cache: "no-store" });
      if (!response.ok) return;
      const data = await response.json();
      setConversations(data.conversations ?? []);
    } catch {
      setConversations([]);
    }
  }, []);

  useEffect(() => {
    loadConversations();
    window.addEventListener("conversation-updated", loadConversations);
    return () => window.removeEventListener("conversation-updated", loadConversations);
  }, [loadConversations]);

  const startEditing = (conversation: ConversationSummary) => {
    setEditingId(conversation.id);
    setEditingTitle(conversation.title);
  };

  const saveTitle = async (event: FormEvent, conversationId: number) => {
    event.preventDefault();
    const title = editingTitle.trim();
    if (!title) return;

    setBusyId(conversationId);
    try {
      const response = await fetch(`${API_URL}/conversations/${conversationId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      });
      if (!response.ok) return;
      setEditingId(null);
      await loadConversations();
    } finally {
      setBusyId(null);
    }
  };

  const deleteConversation = async (conversation: ConversationSummary) => {
    if (!window.confirm(`Delete "${conversation.title}"? This cannot be undone.`)) return;

    setBusyId(conversation.id);
    try {
      const response = await fetch(`${API_URL}/conversations/${conversation.id}`, {
        method: "DELETE",
      });
      if (!response.ok) return;
      const selectedConversationId = new URLSearchParams(window.location.search).get(
        "conversation",
      );
      if (selectedConversationId === String(conversation.id)) {
        router.push("/");
      }
      await loadConversations();
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-secondary text-foreground">
      <aside className="hidden md:flex w-64 flex-col border-r border-border bg-card">
        <div className="p-8 pb-4">
          <div className="flex items-center gap-2.5 mb-10">
            <div className="h-8 w-8 rounded-lg bg-primary text-primary-foreground grid place-items-center">
              <BookOpen className="h-4 w-4" />
            </div>
            <h1 className="font-display text-lg font-bold tracking-tight">Study Planner</h1>
          </div>

          <nav className="space-y-1">
            {nav.map((item) => {
              const active = item.exact ? pathname === item.href : pathname.startsWith(item.href);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                    active
                      ? "bg-secondary text-primary"
                      : "text-muted-foreground hover:bg-secondary/70 hover:text-foreground"
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="min-h-0 flex-1 border-t border-border px-4 py-4">
          <Link
            href="/"
            className="flex items-center justify-center gap-2 rounded-xl bg-primary px-3 py-2.5 text-sm font-semibold text-primary-foreground transition hover:opacity-90"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </Link>

          <p className="mb-2 mt-5 px-2 font-display text-[10px] font-bold uppercase tracking-wide text-muted-foreground">
            Previous Chats
          </p>
          <div className="max-h-full space-y-1 overflow-y-auto pb-4">
            {conversations.map((conversation) => (
              <div
                key={conversation.id}
                className="group flex min-w-0 items-center rounded-lg text-muted-foreground transition hover:bg-secondary hover:text-foreground"
              >
                {editingId === conversation.id ? (
                  <form
                    onSubmit={(event) => saveTitle(event, conversation.id)}
                    className="flex min-w-0 flex-1 items-center gap-1 px-2 py-1.5"
                  >
                    <input
                      autoFocus
                      value={editingTitle}
                      onChange={(event) => setEditingTitle(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === "Escape") setEditingId(null);
                      }}
                      maxLength={120}
                      className="min-w-0 flex-1 rounded border border-border bg-card px-2 py-1 text-xs text-foreground outline-none focus:border-primary"
                    />
                    <button
                      type="submit"
                      disabled={!editingTitle.trim() || busyId === conversation.id}
                      className="rounded p-1 text-primary hover:bg-primary/10 disabled:opacity-40"
                      title="Save title"
                    >
                      <Check className="h-3.5 w-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingId(null)}
                      className="rounded p-1 hover:bg-secondary"
                      title="Cancel"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </form>
                ) : (
                  <>
                    <Link
                      href={`/?conversation=${conversation.id}`}
                      className="min-w-0 flex-1 truncate px-3 py-2 text-xs font-medium"
                      title={conversation.title}
                    >
                      {conversation.title}
                    </Link>
                    <div className="flex shrink-0 items-center pr-1 opacity-0 transition group-hover:opacity-100 group-focus-within:opacity-100">
                      <button
                        type="button"
                        onClick={() => startEditing(conversation)}
                        disabled={busyId === conversation.id}
                        className="rounded p-1.5 hover:bg-card disabled:opacity-40"
                        title="Rename chat"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => deleteConversation(conversation)}
                        disabled={busyId === conversation.id}
                        className="rounded p-1.5 text-destructive hover:bg-destructive/10 disabled:opacity-40"
                        title="Delete chat"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
            {!conversations.length && (
              <p className="px-3 py-2 text-xs text-muted-foreground">No saved chats yet.</p>
            )}
          </div>
        </div>

        <div className="mt-auto p-6">
          <div className="mt-6 flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-primary/10 text-primary grid place-items-center text-xs font-bold border-2 border-card">
              SK
            </div>
            <div>
              <p className="text-sm font-semibold text-foreground">Shahrina Khan</p>
            </div>
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0 pb-16 md:pb-0 h-full overflow-hidden">
        <main className="flex-1 min-w-0 overflow-y-auto">{children}</main>
      </div>

      {/* Bottom Nav Bar on Mobile */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-card border-t border-border flex items-center justify-around z-50">
        {nav.map((item) => {
          const active = item.exact ? pathname === item.href : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center justify-center gap-1 w-20 h-full transition-colors ${
                active
                  ? "text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Icon className="h-5 w-5" />
              <span className="text-[10px] font-medium tracking-tight">{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
