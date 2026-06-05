"use client";

import { AppShell } from "../../src/components/AppShell";
import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  ChevronRight,
  RotateCcw,
  RefreshCw,
  FileText,
  Eye,
  EyeOff,
  CheckCircle2,
  ListOrdered,
} from "lucide-react";

type Question = { q: string; a: string; diff: string };

const QUESTION_COUNT_OPTIONS = [3, 5, 7, 10, 15];

function QuizPageInner() {
  const searchParams = useSearchParams();
  const docFilter = searchParams.get("doc");

  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);
  const [reveal, setReveal] = useState(false);
  const [numQuestions, setNumQuestions] = useState(5);
  // Track which questions have been revealed (for the "done" state)
  const [answeredSet, setAnsweredSet] = useState<Set<number>>(new Set());
  // Show the setup screen before quiz starts
  const [setupDone, setSetupDone] = useState(false);

  const generateQuiz = async (count: number = numQuestions) => {
    setLoading(true);
    setError("");
    setQuestions([]);
    setCurrentIndex(0);
    setReveal(false);
    setAnsweredSet(new Set());

    try {
      const res = await fetch("http://localhost:8000/quiz/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          num_questions: count,
          source_file: docFilter ?? null,
        }),
      });
      const data = await res.json();
      if (data.status === "success" && data.quiz) {
        setQuestions(data.quiz);
      } else {
        setError(data.message || "Failed to generate quiz.");
      }
    } catch {
      setError("Error connecting to backend.");
    } finally {
      setLoading(false);
    }
  };

  // Only auto-generate if no docFilter (general quiz) or setup already done
  useEffect(() => {
    if (!docFilter) {
      setSetupDone(true);
      generateQuiz();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const q = questions[currentIndex];
  const isLastQuestion = currentIndex === questions.length - 1;

  const handleNext = () => {
    if (isLastQuestion) {
      // Restart
      setCurrentIndex(0);
      setReveal(false);
      setAnsweredSet(new Set());
    } else {
      setAnsweredSet((prev) => new Set(prev).add(currentIndex));
      setReveal(false);
      setCurrentIndex((n) => n + 1);
    }
  };

  const handleReveal = () => {
    setReveal((r) => !r);
    if (!reveal) {
      setAnsweredSet((prev) => new Set(prev).add(currentIndex));
    }
  };

  const handleNewQuiz = () => {
    setSetupDone(false);
    setQuestions([]);
    setError("");
    setCurrentIndex(0);
    setReveal(false);
    setAnsweredSet(new Set());
  };

  // ── Setup screen (only shown when a docFilter is present) ──────────────────
  if (docFilter && !setupDone && !loading) {
    return (
      <AppShell>
        <div className="px-6 md:px-12 py-10 max-w-3xl mx-auto">
          <header className="mb-8">
            <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Quiz Me</p>
            <h1 className="text-4xl md:text-5xl mt-2 font-display font-bold">Set Up Your Quiz</h1>
            <div className="flex items-center gap-1.5 mt-2">
              <FileText className="h-3.5 w-3.5 text-primary" />
              <span className="text-[12px] text-primary font-medium truncate">{docFilter}</span>
            </div>
          </header>

          <div className="rounded-3xl border border-border bg-card p-8 space-y-8">
            {/* Question count picker */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <ListOrdered className="h-4 w-4 text-primary" />
                <span className="font-display text-sm font-bold tracking-tight">
                  How many questions?
                </span>
              </div>
              <div className="flex flex-wrap gap-3">
                {QUESTION_COUNT_OPTIONS.map((n) => (
                  <button
                    key={n}
                    onClick={() => setNumQuestions(n)}
                    className={`h-12 w-16 rounded-2xl font-display text-lg font-bold border-2 transition-all ${
                      numQuestions === n
                        ? "border-primary bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                        : "border-border bg-secondary text-foreground hover:border-primary/50"
                    }`}
                  >
                    {n}
                  </button>
                ))}
              </div>
              <p className="text-[11px] text-muted-foreground mt-3">
                Questions will be generated from chunks of <strong>{docFilter}</strong>.
              </p>
            </div>

            {/* Start button */}
            <button
              onClick={() => {
                setSetupDone(true);
                generateQuiz(numQuestions);
              }}
              className="w-full py-4 rounded-2xl bg-primary text-primary-foreground font-display font-bold text-base hover:opacity-90 transition-all shadow-lg shadow-primary/20"
            >
              Generate {numQuestions} Questions →
            </button>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="px-6 md:px-12 py-10 max-w-3xl mx-auto">

        {/* Header */}
        <header className="mb-8 flex items-end justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Quiz Me</p>
            <h1 className="text-4xl md:text-5xl mt-2 font-display font-bold">
              {loading ? (
                "Generating Quiz"
              ) : questions.length > 0 ? (
                <>
                  Question {currentIndex + 1}
                  <span className="text-muted-foreground">/{questions.length}</span>
                </>
              ) : (
                "Quiz"
              )}
            </h1>
            {docFilter && (
              <div className="flex items-center gap-1.5 mt-2">
                <FileText className="h-3.5 w-3.5 text-primary" />
                <span className="text-[12px] text-primary font-medium truncate max-w-xs">
                  {docFilter}
                </span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-3">
            {docFilter && (
              <button
                onClick={handleNewQuiz}
                disabled={loading}
                className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-primary disabled:opacity-50 transition-colors"
              >
                <ListOrdered className="h-4 w-4" />
                Change count
              </button>
            )}
            <button
              onClick={() => generateQuiz(numQuestions)}
              disabled={loading}
              className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-primary disabled:opacity-50 transition-colors"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              New Quiz
            </button>
          </div>
        </header>

        {/* Loading */}
        {loading && (
          <div className="rounded-3xl border border-border bg-card p-12 text-center">
            <RefreshCw className="h-8 w-8 mx-auto animate-spin text-primary mb-4" />
            <p className="text-muted-foreground text-sm">
              {docFilter
                ? `Generating ${numQuestions} questions from ${docFilter}…`
                : "Analysing your documents and generating questions…"}
            </p>
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="rounded-3xl border border-border bg-destructive/10 p-12 text-center">
            <p className="text-destructive text-sm mb-4">{error}</p>
            <button
              onClick={() => generateQuiz(numQuestions)}
              className="px-5 py-2.5 bg-destructive text-destructive-foreground rounded-xl text-sm font-medium hover:opacity-90 transition-all"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Quiz card */}
        {!loading && !error && questions.length > 0 && q && (
          <>
            {/* Progress bar */}
            <div className="h-1.5 w-full rounded-full bg-secondary overflow-hidden mb-2">
              <div
                className="h-full bg-primary rounded-full transition-all duration-500"
                style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
              />
            </div>
            <div className="flex justify-between text-[11px] text-muted-foreground font-display mb-6">
              <span>{answeredSet.size} answered</span>
              <span>{questions.length - answeredSet.size} remaining</span>
            </div>

            <div className="rounded-3xl border border-border bg-card p-8">
              {/* Difficulty badge */}
              <span
                className={`inline-block rounded-full px-3 py-0.5 text-[10px] font-display font-bold uppercase tracking-wider mb-5 ${
                  q.diff === "Easy"
                    ? "bg-emerald-100 text-emerald-700"
                    : q.diff === "Medium"
                    ? "bg-amber-100 text-amber-700"
                    : "bg-rose-100 text-rose-700"
                }`}
              >
                {q.diff}
              </span>

              {/* Question */}
              <h2 className="text-2xl md:text-3xl font-display font-bold text-foreground leading-snug mb-6">
                {q.q}
              </h2>

              {/* Answer textarea */}
              <textarea
                placeholder="Write your answer here…"
                className="w-full min-h-28 rounded-2xl border border-border bg-secondary/40 p-4 text-[15px] outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all resize-none"
              />

              {/* Reveal answer panel */}
              {reveal && (
                <div className="mt-5 rounded-2xl bg-emerald-50 border border-emerald-200 p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    <p className="text-[11px] font-display font-bold uppercase tracking-widest text-emerald-700">
                      Correct Answer
                    </p>
                  </div>
                  <p className="text-[15px] leading-relaxed text-foreground">{q.a}</p>
                </div>
              )}

              {/* Controls */}
              <div className="mt-6 flex items-center justify-between gap-3">
                {/* Reveal button — prominent */}
                <button
                  onClick={handleReveal}
                  className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium border-2 transition-all ${
                    reveal
                      ? "border-emerald-300 bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                      : "border-primary/30 bg-primary/5 text-primary hover:bg-primary/10"
                  }`}
                >
                  {reveal ? (
                    <>
                      <EyeOff className="h-4 w-4" />
                      Hide Answer
                    </>
                  ) : (
                    <>
                      <Eye className="h-4 w-4" />
                      Reveal Correct Answer
                    </>
                  )}
                </button>

                {/* Next / Restart */}
                <button
                  onClick={handleNext}
                  className="inline-flex items-center gap-2 rounded-xl bg-primary text-primary-foreground px-5 py-2.5 text-sm font-medium hover:opacity-90 transition-all shadow-md shadow-primary/20"
                >
                  {isLastQuestion ? (
                    <>
                      <RotateCcw className="h-4 w-4" />
                      Restart
                    </>
                  ) : (
                    <>
                      Next
                      <ChevronRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Question dots navigator */}
            <div className="mt-6 flex flex-wrap justify-center gap-2">
              {questions.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setReveal(false);
                    setCurrentIndex(idx);
                  }}
                  className={`h-8 w-8 rounded-full text-[11px] font-display font-bold transition-all ${
                    idx === currentIndex
                      ? "bg-primary text-primary-foreground shadow-md shadow-primary/20"
                      : answeredSet.has(idx)
                      ? "bg-emerald-100 text-emerald-700 border border-emerald-200"
                      : "bg-secondary text-muted-foreground hover:bg-secondary/80"
                  }`}
                >
                  {idx + 1}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}

export default function QuizPage() {
  return (
    <Suspense fallback={null}>
      <QuizPageInner />
    </Suspense>
  );
}
