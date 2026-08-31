"use client";

import { useMemo, useState } from "react";
import { ArrowLeft, ArrowRight, Check, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Choice = { label: string; signal: string; interest: string };
type Question = { eyebrow: string; title: string; description: string; choices: Choice[] };

const QUESTIONS: Question[] = [
  {
    eyebrow: "Your work",
    title: "What do you mainly use academic quality assurance for?",
    description: "Choose the closest fit. You can adjust your work focus later.",
    choices: [
      { label: "Reviewing module or course evidence", signal: "review_evidence", interest: "review_module" },
      { label: "Preparing my own module or course evidence", signal: "prepare_evidence", interest: "prepare_folder" },
      { label: "Checking compliance and readiness", signal: "check_compliance", interest: "check_compliance" },
      { label: "Responding to quality findings", signal: "respond_findings", interest: "resolve_findings" },
    ],
  },
  {
    eyebrow: "Your activities",
    title: "Which activity do you perform most often?",
    description: "AQAA uses this only to tailor the workspace—not to grant access.",
    choices: [
      { label: "Review other people's quality evidence", signal: "review_others", interest: "review_evidence" },
      { label: "Identify missing or incomplete documents", signal: "identify_missing", interest: "find_missing_docs" },
      { label: "Prepare teaching and module evidence", signal: "teaching_evidence", interest: "prepare_evidence" },
      { label: "Upload assessments and memoranda", signal: "upload_documents", interest: "prepare_assessment" },
    ],
  },
  {
    eyebrow: "First outcome",
    title: "What would you like AQAA to help with first?",
    description: "Your answer personalises starter prompts and evidence guidance.",
    choices: [
      { label: "Conduct a quality review", signal: "conduct_review", interest: "review_module" },
      { label: "Find evidence gaps", signal: "find_gaps", interest: "find_missing_docs" },
      { label: "Prepare a complete module folder", signal: "prepare_folder", interest: "prepare_folder" },
      { label: "Resolve existing findings", signal: "resolve_findings", interest: "resolve_findings" },
    ],
  },
  {
    eyebrow: "Work focus",
    title: "Which statement sounds more like your day-to-day work?",
    description: "This final answer helps AQAA avoid making an ambiguous classification.",
    choices: [
      { label: "I review quality evidence and make findings", signal: "make_findings", interest: "review_evidence" },
      { label: "I prepare evidence and respond to findings", signal: "module_owner", interest: "prepare_evidence" },
    ],
  },
];

export default function OnboardingPage() {
  const { user } = useAuth();
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<number, Choice>>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ persona: string; reason?: string } | null>(null);
  const selected = answers[step];
  const progress = useMemo(() => result ? 100 : ((step + 1) / QUESTIONS.length) * 100, [result, step]);

  if (!user) return <div className="grid min-h-[70vh] place-items-center text-sm text-muted-foreground">Preparing your workspace…</div>;

  const finish = async () => {
    setSubmitting(true);
    try {
      const chosen = Object.values(answers);
      const response = await fetch("/api/proxy/onboarding/preferences", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          qa_interests: chosen.map((answer) => answer.interest),
          evidence_types: ["module_guides", "assessments", "moderation_evidence"],
          work_focus_signals: chosen.map((answer) => answer.signal),
        }),
      });
      const data = await response.json() as { persona?: string; classification_reason?: string; detail?: string };
      if (!response.ok || !data.persona) throw new Error(data.detail || "AQAA could not tailor your workspace.");
      setResult({ persona: data.persona, reason: data.classification_reason });
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "AQAA could not tailor your workspace.");
    } finally {
      setSubmitting(false);
    }
  };

  if (result) {
    const qa = result.persona === "quality_assurance_officer";
    return (
      <div className="mx-auto flex min-h-[calc(100vh-8rem)] max-w-2xl items-center px-4 py-10">
        <section className="w-full rounded-[2rem] border border-primary/15 bg-gradient-to-b from-primary/[0.06] to-background p-8 text-center shadow-[0_24px_80px_-48px_hsl(var(--primary))] sm:p-12">
          <div className="mx-auto mb-6 grid h-14 w-14 place-items-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/20"><Sparkles className="h-6 w-6" /></div>
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-primary">Workspace tailored</p>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            {qa ? "Ready for quality review." : "Ready for module preparation."}
          </h1>
          <p className="mx-auto mt-4 max-w-lg text-base leading-7 text-muted-foreground">
            AQAA has tailored your conversation starters, evidence guidance, and workflows for a <strong className="text-foreground">{qa ? "Quality Assurance Officer" : "Lecturer"}</strong> focus.
          </p>
          <p className="mt-5 text-xs text-muted-foreground">Your security role remains Generic User. Work focus never changes permissions.</p>
          <Button onClick={() => window.location.assign("/workspace")} className="mt-8 h-12 rounded-xl px-7">Start with AQAA <ArrowRight className="ml-2 h-4 w-4" /></Button>
        </section>
      </div>
    );
  }

  const question = QUESTIONS[step];
  return (
    <div className="mx-auto min-h-[calc(100vh-8rem)] max-w-3xl px-4 py-8 sm:py-14">
      <div className="mb-10 flex items-center gap-3">
        <div className="grid h-9 w-9 place-items-center rounded-xl bg-primary text-xs font-bold text-primary-foreground">AQ</div>
        <div><p className="text-sm font-semibold">Tailor your AQAA workspace</p><p className="text-xs text-muted-foreground">About two minutes</p></div>
      </div>
      <div className="mb-10 h-1 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-primary transition-all duration-500 motion-reduce:transition-none" style={{ width: `${progress}%` }} /></div>
      <main>
        <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-primary">{question.eyebrow} · {step + 1} of {QUESTIONS.length}</p>
        <h1 className="max-w-2xl text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">{question.title}</h1>
        <p className="mt-3 text-base text-muted-foreground">{question.description}</p>
        <div className="mt-8 grid gap-3" role="radiogroup" aria-label={question.title}>
          {question.choices.map((choice) => {
            const active = selected?.signal === choice.signal;
            return <button key={choice.signal} type="button" role="radio" aria-checked={active} onClick={() => setAnswers((current) => ({ ...current, [step]: choice }))} className={cn("group flex min-h-16 items-center gap-4 rounded-2xl border px-5 py-4 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2", active ? "border-primary bg-primary/[0.06] shadow-sm" : "border-border/70 bg-card hover:border-primary/40 hover:bg-muted/30")}>
              <span className={cn("grid h-6 w-6 shrink-0 place-items-center rounded-full border", active ? "border-primary bg-primary text-primary-foreground" : "border-muted-foreground/30")}>{active && <Check className="h-3.5 w-3.5" />}</span>
              <span className="font-medium">{choice.label}</span>
            </button>;
          })}
        </div>
        <div className="mt-9 flex items-center justify-between">
          <Button variant="ghost" disabled={step === 0 || submitting} onClick={() => setStep((current) => current - 1)}><ArrowLeft className="mr-2 h-4 w-4" />Back</Button>
          <Button disabled={!selected || submitting} onClick={() => step === QUESTIONS.length - 1 ? void finish() : setStep((current) => current + 1)} className="min-w-32">
            {submitting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Tailoring…</> : step === QUESTIONS.length - 1 ? "Tailor workspace" : <>Continue<ArrowRight className="ml-2 h-4 w-4" /></>}
          </Button>
        </div>
      </main>
    </div>
  );
}
