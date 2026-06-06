"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { MessageSquare, Calendar, HelpCircle, Heart, FileText, BookOpen } from "lucide-react";
import type { ReactNode } from "react";

type NavItem = { href: string; label: string; icon: typeof MessageSquare; exact?: boolean };
const nav: NavItem[] = [
  { href: "/", label: "Chat", icon: MessageSquare, exact: true },
  { href: "/quiz", label: "Quiz Me", icon: HelpCircle },
  { href: "/documents", label: "My Documents", icon: FileText },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

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
