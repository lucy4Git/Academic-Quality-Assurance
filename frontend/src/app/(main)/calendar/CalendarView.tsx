"use client";

import { useState } from "react";
import Link from "next/link";
import { CalendarDays, ChevronLeft, ChevronRight, Clock } from "lucide-react";

import { PageHeader } from "@/components/common/PageHeader";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useWorkflows } from "@/hooks/useWorkflow";
import { WORKFLOW_STATUS_COLOURS, type WorkflowItem } from "@/types";

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

function getDaysInMonth(year: number, month: number) {
  return new Date(year, month + 1, 0).getDate();
}

function getFirstDayOfMonth(year: number, month: number) {
  return new Date(year, month, 1).getDay();
}

export function CalendarView() {
  const today = new Date();
  const [viewYear, setViewYear] = useState(today.getFullYear());
  const [viewMonth, setViewMonth] = useState(today.getMonth());

  const { data, isLoading } = useWorkflows();

  // Build map: "YYYY-MM-DD" → WorkflowItem[]
  const dueDayMap = new Map<string, WorkflowItem[]>();
  for (const item of data ?? []) {
    if (!item.due_date) continue;
    const d = new Date(item.due_date);
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    if (!dueDayMap.has(key)) dueDayMap.set(key, []);
    dueDayMap.get(key)!.push(item);
  }

  // Audits with no due date
  const noDueDate = (data ?? []).filter((item: WorkflowItem) => !item.due_date);

  function prevMonth() {
    if (viewMonth === 0) { setViewMonth(11); setViewYear(y => y - 1); }
    else setViewMonth(m => m - 1);
  }
  function nextMonth() {
    if (viewMonth === 11) { setViewMonth(0); setViewYear(y => y + 1); }
    else setViewMonth(m => m + 1);
  }

  const daysInMonth = getDaysInMonth(viewYear, viewMonth);
  const firstDay = getFirstDayOfMonth(viewYear, viewMonth);
  const cells = Array.from({ length: firstDay + daysInMonth }, (_, i) => i - firstDay + 1);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-80 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Audit Calendar"
        subtitle="Due dates for assigned audits"
      />

      <div className="grid lg:grid-cols-[1fr_280px] gap-6">
        {/* Calendar grid */}
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          {/* Month navigation */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-border">
            <Button size="sm" variant="ghost" onClick={prevMonth}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <p className="text-sm font-semibold">{MONTHS[viewMonth]} {viewYear}</p>
            <Button size="sm" variant="ghost" onClick={nextMonth}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>

          {/* Day headers */}
          <div className="grid grid-cols-7 border-b border-border">
            {DAYS.map((d) => (
              <div key={d} className="py-2 text-center text-[11px] font-medium uppercase text-muted-foreground">
                {d}
              </div>
            ))}
          </div>

          {/* Day cells */}
          <div className="grid grid-cols-7">
            {cells.map((day, idx) => {
              if (day < 1) {
                return <div key={`empty-${idx}`} className="border-b border-r border-border h-20 bg-muted/10" />;
              }
              const key = `${viewYear}-${String(viewMonth + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
              const dayItems = dueDayMap.get(key) ?? [];
              const isToday = day === today.getDate() && viewMonth === today.getMonth() && viewYear === today.getFullYear();

              return (
                <div
                  key={key}
                  className={cn(
                    "border-b border-r border-border h-20 p-1 flex flex-col gap-0.5 overflow-hidden",
                    isToday && "bg-primary/5",
                  )}
                >
                  <span className={cn(
                    "text-[11px] font-medium self-end",
                    isToday ? "flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground text-[10px]" : "text-muted-foreground",
                  )}>
                    {day}
                  </span>
                  {dayItems.slice(0, 2).map((item: WorkflowItem) => (
                    <Link
                      key={item.id}
                      href={`/workflow/${item.id}`}
                      className={cn(
                        "truncate rounded px-1 py-0.5 text-[10px] font-medium border",
                        WORKFLOW_STATUS_COLOURS[item.workflow_status],
                      )}
                    >
                      {item.academic_year}
                    </Link>
                  ))}
                  {dayItems.length > 2 && (
                    <span className="text-[10px] text-muted-foreground pl-1">+{dayItems.length - 2} more</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* No due date sidebar */}
        <div className="rounded-xl border border-border bg-card">
          <div className="border-b border-border px-4 py-3">
            <p className="text-sm font-medium flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              No Due Date
              {noDueDate.length > 0 && (
                <span className="ml-1 rounded-full bg-muted px-2 py-0.5 text-xs font-normal text-muted-foreground">
                  {noDueDate.length}
                </span>
              )}
            </p>
          </div>
          <div className="p-3 space-y-2">
            {noDueDate.length === 0 && (
              <p className="text-xs text-muted-foreground">All audits have due dates.</p>
            )}
            {noDueDate.map((item: WorkflowItem) => (
              <Link
                key={item.id}
                href={`/workflow/${item.id}`}
                className="block rounded-lg border border-border px-3 py-2 text-xs hover:bg-muted/40 transition-colors"
              >
                <p className="font-medium text-foreground">{item.academic_year}</p>
                <p className={cn(
                  "mt-0.5 inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold",
                  WORKFLOW_STATUS_COLOURS[item.workflow_status],
                )}>
                  {item.workflow_status.replace(/_/g, " ")}
                </p>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
