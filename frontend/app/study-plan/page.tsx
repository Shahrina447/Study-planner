import { AppShell } from "../../src/components/AppShell";
import { CheckCircle2, Circle, Clock, Flame } from "lucide-react";

export const metadata = {
  title: "Study Plan — MindBridge-RAG",
  description: "Today's topics, deadlines, and adaptive scheduling.",
};

const today = [
  { time: "09:00", title: "Waves — standing wave derivations", duration: "45m", status: "done", topic: "Physics" },
  { time: "10:15", title: "Linear Algebra — eigenvectors revision", duration: "60m", status: "active", topic: "Maths" },
  { time: "13:00", title: "Quiz: Thermodynamics (20 Qs)", duration: "30m", status: "todo", topic: "Physics" },
  { time: "16:30", title: "Organic Chemistry — reaction mechanisms", duration: "50m", status: "todo", topic: "Chemistry" },
];

const deadlines = [
  { name: "Mid-semester · Physics", days: 4, progress: 72 },
  { name: "Lab report · Chemistry", days: 7, progress: 30 },
  { name: "Maths assignment 4", days: 11, progress: 12 },
];

export default function StudyPlanPage() {
  return (
    <AppShell>
      <div className="px-6 md:px-12 py-10 max-w-6xl mx-auto">
        <header className="mb-10">
          <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Wednesday · June 3</p>
          <h1 className="text-4xl md:text-5xl mt-2">Today, gently.</h1>
          <p className="text-muted-foreground mt-3 max-w-xl">
            Four focus blocks. 3h 5m of deep work. MindBridge-RAG spaced them around your peak hours and reserved a long break
            after lunch.
          </p>
        </header>

        <div className="grid lg:grid-cols-[1fr,320px] gap-8">
          <section>
            <h2 className="text-xs uppercase tracking-[0.22em] text-muted-foreground mb-4">Schedule</h2>
            <div className="space-y-3">
              {today.map((s) => (
                <div
                  key={s.time}
                  className={`flex gap-4 rounded-2xl border p-4 transition-all ${
                    s.status === "active"
                      ? "border-[var(--color-leaf)]/40 bg-[var(--color-leaf)]/5"
                      : "border-border bg-card"
                  }`}
                >
                  <div className="w-14 shrink-0 text-right">
                    <div className="font-mono text-sm">{s.time}</div>
                    <div className="text-[10px] text-muted-foreground mt-0.5">{s.duration}</div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      {s.status === "done" ? (
                        <CheckCircle2 className="h-4 w-4 text-[var(--color-leaf)]" />
                      ) : s.status === "active" ? (
                        <Flame className="h-4 w-4 text-[var(--color-ember)]" />
                      ) : (
                        <Circle className="h-4 w-4 text-muted-foreground" />
                      )}
                      <span
                        className={`text-[15px] ${s.status === "done" ? "line-through text-muted-foreground" : "text-foreground"}`}
                      >
                        {s.title}
                      </span>
                    </div>
                    <span className="ml-6 text-[11px] text-muted-foreground">{s.topic}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <aside>
            <h2 className="text-xs uppercase tracking-[0.22em] text-muted-foreground mb-4">Upcoming</h2>
            <div className="space-y-4">
              {deadlines.map((d) => (
                <div key={d.name} className="rounded-2xl bg-card border border-border p-4">
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-sm text-foreground">{d.name}</span>
                    <span className="text-[11px] font-mono text-muted-foreground inline-flex items-center gap-1">
                      <Clock className="h-3 w-3" /> {d.days}d
                    </span>
                  </div>
                  <div className="mt-3 h-1.5 rounded-full bg-secondary overflow-hidden">
                    <div className="h-full bg-primary rounded-full" style={{ width: `${d.progress}%` }} />
                  </div>
                  <div className="mt-1.5 text-[10px] text-muted-foreground">{d.progress}% ready</div>
                </div>
              ))}
            </div>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}
