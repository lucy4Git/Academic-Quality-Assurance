"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";

type Step = 1 | 2 | 3;

const QA_TASKS = [
  { id: "review_module", label: "Review module/course folders" },
  { id: "find_missing_docs", label: "Find missing QA documents" },
  { id: "check_outcomes", label: "Check learning outcomes" },
  { id: "review_assessments", label: "Review assessments" },
  { id: "check_memos", label: "Check assessment memoranda" },
  { id: "review_moderation", label: "Review moderation evidence" },
  { id: "check_attendance", label: "Check attendance evidence" },
  { id: "review_evidence", label: "Review evidence completeness" },
  { id: "resolve_findings", label: "Resolve QA findings" },
  { id: "generate_reports", label: "Generate QA reports" },
];

const EVIDENCE_TYPES = [
  { id: "module_guides", label: "Module guides" },
  { id: "learning_outcomes", label: "Learning outcomes" },
  { id: "teaching_plans", label: "Teaching plans/content" },
  { id: "assessments", label: "Assessments" },
  { id: "memos", label: "Memoranda/marking guides" },
  { id: "rubrics", label: "Rubrics" },
  { id: "internal_moderation", label: "Internal moderation reports" },
  { id: "external_moderation", label: "External moderation reports" },
  { id: "attendance_records", label: "Attendance records" },
  { id: "results", label: "Results" },
  { id: "supporting_qa", label: "Supporting QA evidence" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [step, setStep] = useState<Step>(1);
  const [selectedTasks, setSelectedTasks] = useState<Set<string>>(new Set());
  const [selectedEvidenceTypes, setSelectedEvidenceTypes] = useState<Set<string>>(new Set());
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  const handleToggleTask = (taskId: string) => {
    const newTasks = new Set(selectedTasks);
    if (newTasks.has(taskId)) {
      newTasks.delete(taskId);
    } else {
      newTasks.add(taskId);
    }
    setSelectedTasks(newTasks);
  };

  const handleToggleEvidenceType = (typeId: string) => {
    const newTypes = new Set(selectedEvidenceTypes);
    if (newTypes.has(typeId)) {
      newTypes.delete(typeId);
    } else {
      newTypes.add(typeId);
    }
    setSelectedEvidenceTypes(newTypes);
  };

  const handleFinish = async () => {
    if (selectedTasks.size === 0) {
      toast.error("Please select at least one QA task");
      return;
    }
    if (selectedEvidenceTypes.size === 0) {
      toast.error("Please select at least one evidence type");
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await fetch("/api/proxy/onboarding/preferences", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          qa_interests: Array.from(selectedTasks),
          evidence_types: Array.from(selectedEvidenceTypes),
        }),
      });

      if (!res.ok) {
        const data = await res.json() as { detail?: string };
        throw new Error(data.detail || "Failed to save preferences");
      }

      toast.success("Setup complete!");
      router.push("/dashboard");
    } catch (err) {
      console.error("Onboarding error:", err);
      toast.error(err instanceof Error ? err.message : "Failed to save preferences");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto px-4 py-8">
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome to AQAA</h1>
          <p className="text-gray-600">Let&apos;s personalize your experience</p>
          <div className="mt-4 flex gap-2">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`h-2 flex-1 rounded-full transition-colors ${
                  s <= step ? "bg-blue-600" : "bg-gray-200"
                }`}
              />
            ))}
          </div>
        </div>

        {step === 1 && (
          <div>
            <h2 className="text-xl font-semibold mb-4">How do you work with academic quality?</h2>
            <p className="text-gray-600 mb-4">Your focus: <strong>{
              user.persona === "quality_assurance_officer"
                ? "Quality Assurance Officer"
                : user.persona === "lecturer"
                ? "Lecturer"
                : "Unknown"
            }</strong></p>
            <p className="text-sm text-gray-500 mb-6">
              This determines which tools and recommendations you&apos;ll see first in your workspace.
            </p>
            <div className="flex gap-4">
              <Button variant="outline" onClick={() => setStep(2)} className="flex-1">
                Next
              </Button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div>
            <h2 className="text-xl font-semibold mb-4">What would you like AQAA to help you with?</h2>
            <p className="text-sm text-gray-500 mb-6">Select all that apply</p>
            <div className="space-y-3 mb-6">
              {QA_TASKS.map((task) => (
                <div key={task.id} className="flex items-center gap-3">
                  <Checkbox
                    id={task.id}
                    checked={selectedTasks.has(task.id)}
                    onCheckedChange={() => handleToggleTask(task.id)}
                  />
                  <Label htmlFor={task.id} className="cursor-pointer">
                    {task.label}
                  </Label>
                </div>
              ))}
            </div>
            <div className="flex gap-4">
              <Button variant="outline" onClick={() => setStep(1)} className="flex-1">
                Back
              </Button>
              <Button onClick={() => setStep(3)} className="flex-1">
                Next
              </Button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div>
            <h2 className="text-xl font-semibold mb-4">What evidence do you normally work with?</h2>
            <p className="text-sm text-gray-500 mb-6">Select all that apply</p>
            <div className="space-y-3 mb-6">
              {EVIDENCE_TYPES.map((type) => (
                <div key={type.id} className="flex items-center gap-3">
                  <Checkbox
                    id={type.id}
                    checked={selectedEvidenceTypes.has(type.id)}
                    onCheckedChange={() => handleToggleEvidenceType(type.id)}
                  />
                  <Label htmlFor={type.id} className="cursor-pointer">
                    {type.label}
                  </Label>
                </div>
              ))}
            </div>
            <div className="flex gap-4">
              <Button variant="outline" onClick={() => setStep(2)} className="flex-1">
                Back
              </Button>
              <Button
                onClick={handleFinish}
                disabled={isSubmitting}
                className="flex-1"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Finishing...
                  </>
                ) : (
                  "Finish Setup"
                )}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
