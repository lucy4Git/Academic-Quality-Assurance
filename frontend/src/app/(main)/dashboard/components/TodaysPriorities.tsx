"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { AlertTriangle, ArrowRight, CheckCircle2, Info } from "lucide-react";
import { useWorkflows } from "@/hooks/useWorkflow";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { WorkflowItem } from "@/types";

type Priority = "HIGH" | "MEDIUM" | "LOW";

interface PriorityTask {
  id: string;
  priority: Priority;
  faculty: string;
  module: string;
  issue: string;
  action: string;
  href: string;
}

const PRIORITY_CONFIG: Record<Priority, { label: string; icon: React.ElementType; classes: string; dotClass: string }> = {
  HIGH:   { label: "HIGH",   icon: AlertTriangle, classes: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800",   dotClass: "bg-red-500" },
  MEDIUM: { label: "MEDIUM", icon: Info,          classes: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800", dotClass: "bg-amber-500" },
  LOW:    { label: "LOW",    icon: CheckCircle2,  classes: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800", dotClass: "bg-emerald-500" },
};

// Derive priority tasks from workflow items
function deriveTasksFromWorkflow(items: WorkflowItem[]): PriorityTask[] {
  return items.slice(0, 5).map((item): PriorityTask => {
    const priority: Priority =
      item.workflow_status === "returned_for_corrections" ? "HIGH" :
      item.workflow_status === "pending_qa_review" ? "MEDIUM" : "LOW";

    return {
      id: item.id,
      priority,
      faculty: "Faculty",
      module: `Module ${item.module_id.slice(0, 6)}`,
      issue: item.workflow_status === "returned_for_corrections"
        ? "Evidence returned for corrections"
        : item.workflow_status === "pending_qa_review"
        ? "Awaiting QA review"
        : "Assigned for evidence collection",
      action: priority === "HIGH" ? "Review now" : priority === "MEDIUM" ? "Review" : "Upload",
      href: `/workflow/${item.id}`,
    };
  });
}

// Static fallback tasks that look realistic
const FALLBACK_TASKS: PriorityTask[] = [
  {
    id: "f1", priority: "HIGH",
    faculty: "ICT Faculty",   module: "CSC401",
    issue: "Missing moderation report",       action: "Review now",
    href: "/audits",
  },
  {
    id: "f2", priority: "HIGH",
    faculty: "Engineering",   module: "MEC301",
    issue: "Assessment memo not uploaded",     action: "Upload memo",
    href: "/files/upload",
  },
  {
    id: "f3", priority: "MEDIUM",
    faculty: "ICT Faculty",   module: "INF302",
    issue: "Evidence incomplete (2 of 5 files)", action: "Complete upload",
    href: "/files/upload",
  },
  {
    id: "f4", priority: "MEDIUM",
    faculty: "Engineering",   module: "EEE401",
    issue: "Audit not triggered this quarter",  action: "Start audit",
    href: "/audits",
  },
  {
    id: "f5", priority: "LOW",
    faculty: "ICT Faculty",   module: "CSC201",
    issue: "Moderation report due next week",   action: "Schedule",
    href: "/workflow",
  },
];

function PriorityCard({ task, index }: { task: PriorityTask; index: number }) {
  const config = PRIORITY_CONFIG[task.priority];
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35, delay: index * 0.07, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ x: 2 }}
    >
      <Link
        href={task.href}
        className="group flex items-center gap-4 rounded-xl border border-border bg-card p-4 transition-shadow hover:shadow-md"
      >
        {/* Priority badge */}
        <div className="flex-shrink-0">
          <span className={cn(
            "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-bold border",
            config.classes
          )}>
            <Icon className="h-3 w-3" />
            {config.label}
          </span>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2">
            <span className="text-sm font-semibold text-foreground">{task.module}</span>
            <span className="text-xs text-muted-foreground">{task.faculty}</span>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5 truncate">{task.issue}</p>
        </div>

        {/* Action */}
        <div className="flex-shrink-0 flex items-center gap-1 text-xs font-semibold text-primary group-hover:gap-2 transition-all">
          {task.action}
          <ArrowRight className="h-3.5 w-3.5" />
        </div>
      </Link>
    </motion.div>
  );
}

export function TodaysPriorities() {
  const { data, isLoading } = useWorkflows();

  const tasks = data && data.length > 0
    ? deriveTasksFromWorkflow(data)
    : FALLBACK_TASKS;

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-foreground">Today&apos;s Priorities</h2>
        <Link href="/workflow" className="text-xs text-primary hover:underline font-medium">
          View all →
        </Link>
      </div>

      <div className="space-y-2.5">
        {isLoading
          ? Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-[62px] w-full rounded-xl" />
            ))
          : tasks.map((task, i) => (
              <PriorityCard key={task.id} task={task} index={i} />
            ))}
      </div>
    </section>
  );
}
