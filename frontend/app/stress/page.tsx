"use client";

import { AppShell } from "../../src/components/AppShell";
import { useEffect, useRef, useState } from "react";
import { Play, Pause, Coffee, CalendarClock, Wind } from "lucide-react";

const PHASES = [
  { name: "Breathe in", duration: 4 },
  { name: "Hold", duration: 7 },
  { name: "Breathe out", duration: 8 },
] as const;

export default function StressPage() {
  const [running, setRunning] = useState(false);
  const [phase, setPhase] = useState(0);
  const [count, setCount] = useState<number>(PHASES[0].duration);
  const ref = useRef<number | null>(null);

  useEffect(() => {
    if (!running) return;
    ref.current = window.setInterval(() => {
      setCount((c) => {
        if (c > 1) return c - 1;
        setPhase((p) => {
          const next = (p + 1) % PHASES.length;
          setCount(PHASES[next].duration);
          return next;
        });
        return PHASES[(phase + 1) % PHASES.length].duration;
      });
    }, 1000);
    return () => {
      if (ref.current) window.clearInterval(ref.current);
    };
  }, [running, phase]);

  const scale = phase === 0 ? 1.4 : phase === 1 ? 1.4 : 0.85;

  return (
    <AppShell stressScore={34}>
      <div className="px-6 md:px-12 py-10 max-w-5xl mx-auto">
        <header className="mb-10">
          <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Stress · score 34/100</p>
          <h1 className="text-4xl md:text-5xl mt-2">Take a slow breath.</h1>
          <p className="text-muted-foreground mt-3 max-w-xl">
            Atlas noticed three rapid-fire questions in the last 12 minutes. That's often a signal of rising stress. Try
            the 4-7-8 cycle below.
          </p>
        </header>

        <div className="grid lg:grid-cols-[1fr,1fr] gap-8">
          <section className="rounded-3xl border border-border bg-card p-10 flex flex-col items-center text-center">
            <Wind className="h-5 w-5 text-muted-foreground mb-2" />
            <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">4-7-8 breathing</p>

            <div className="relative my-10 h-64 w-64 grid place-items-center">
              <div
                className="absolute inset-0 rounded-full bg-[var(--color-leaf)]/15 transition-transform duration-1000 ease-in-out"
                style={{ transform: `scale(${running ? scale : 1})` }}
              />
              <div
                className="absolute inset-6 rounded-full bg-[var(--color-leaf)]/25 transition-transform duration-1000 ease-in-out"
                style={{ transform: `scale(${running ? scale * 0.95 : 1})` }}
              />
              <div className="relative z-10">
                <div className="font-display text-6xl">{count}</div>
                <div className="text-xs uppercase tracking-[0.22em] text-muted-foreground mt-1">
                  {PHASES[phase].name}
                </div>
              </div>
            </div>

            <button
              onClick={() => setRunning((r) => !r)}
              className="inline-flex items-center gap-2 rounded-full bg-primary text-primary-foreground px-6 py-3 text-sm hover:opacity-90"
            >
              {running ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              {running ? "Pause" : "Begin cycle"}
            </button>
          </section>

          <section className="space-y-4">
            <div className="rounded-2xl border border-border bg-card p-6">
              <Coffee className="h-5 w-5 text-[var(--color-ember)] mb-3" />
              <h3 className="font-display text-2xl mb-2">Take a 12-minute break</h3>
              <p className="text-sm text-muted-foreground">
                Walk away from the screen. Make tea. Let your eyes find the horizon. Atlas will pause your timer.
              </p>
              <button className="mt-4 text-sm text-foreground underline underline-offset-4">Start break →</button>
            </div>

            <div className="rounded-2xl border border-border bg-card p-6">
              <CalendarClock className="h-5 w-5 text-[var(--color-leaf)] mb-3" />
              <h3 className="font-display text-2xl mb-2">Reshuffle today's plan</h3>
              <p className="text-sm text-muted-foreground">
                Move the Thermodynamics quiz to tomorrow morning when you're sharper. The schedule will re-balance
                automatically.
              </p>
              <button className="mt-4 text-sm text-foreground underline underline-offset-4">Reshuffle →</button>
            </div>

            <div className="rounded-2xl border border-border bg-accent/30 p-6">
              <p className="text-[11px] uppercase tracking-[0.22em] text-accent-foreground/70 mb-2">A note from Atlas</p>
              <p className="text-sm text-foreground italic leading-relaxed">
                &quot;You've been showing up daily for 8 days straight. Progress isn't always about intensity — it's
                about not breaking the chain.&quot;
              </p>
            </div>
          </section>
        </div>
      </div>
    </AppShell>
  );
}
