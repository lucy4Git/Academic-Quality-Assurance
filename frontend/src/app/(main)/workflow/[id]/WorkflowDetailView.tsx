"use client";

import { useState } from "react";
import {
  GitBranch, User, Calendar, Flag, MessageSquare,
  Send, Pencil, Trash2, CheckCircle, Loader2,
} from "lucide-react";

import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState } from "@/components/common/ErrorState";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn, formatDateTime } from "@/lib/utils";
import { useWorkflow, useAssignAudit, useUpdateWorkflowStatus } from "@/hooks/useWorkflow";
import { useComments, useCreateComment, useUpdateComment, useResolveComment, useDeleteComment } from "@/hooks/useComments";
import { useRole } from "@/hooks/useRole";
import { useAuthStore } from "@/store/auth.store";
import {
  WORKFLOW_STATUS_LABELS,
  WORKFLOW_STATUS_COLOURS,
  PRIORITY_LABELS,
  PRIORITY_COLOURS,
  type WorkflowStatus,
  type AuditPriority,
  type AuditComment,
} from "@/types";

// ---------------------------------------------------------------------------
// Allowed transitions by role
// ---------------------------------------------------------------------------
const QA_TARGET_STATUSES: WorkflowStatus[] = ["approved", "rejected", "returned_for_corrections"];
const COORD_TARGET_STATUSES: WorkflowStatus[] = ["evidence_collection", "pending_qa_review", "assigned", "completed", "archived"];

function wfBadge(status: WorkflowStatus) {
  return (
    <span className={cn(
      "inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold",
      WORKFLOW_STATUS_COLOURS[status],
    )}>
      {WORKFLOW_STATUS_LABELS[status]}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Comment thread
// ---------------------------------------------------------------------------

function CommentItem({
  comment,
  currentUserId,
  isQA,
  auditId,
}: {
  comment: AuditComment;
  currentUserId: string | undefined;
  isQA: boolean;
  auditId: string;
}) {
  const [editing, setEditing] = useState(false);
  const [editBody, setEditBody] = useState(comment.body);

  const updateMut = useUpdateComment(auditId);
  const resolveMut = useResolveComment(auditId);
  const deleteMut = useDeleteComment(auditId);

  const isOwn = currentUserId && comment.author_id === currentUserId;

  return (
    <div className={cn(
      "rounded-lg border p-3 text-sm space-y-1",
      comment.is_resolved ? "bg-muted/30 opacity-70" : "bg-background",
    )}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          {editing ? (
            <div className="space-y-2">
              <textarea
                rows={3}
                value={editBody}
                onChange={(e) => setEditBody(e.target.value)}
                className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  disabled={updateMut.isPending}
                  onClick={async () => {
                    await updateMut.mutateAsync({ id: comment.id, body: editBody });
                    setEditing(false);
                  }}
                >
                  {updateMut.isPending && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
                  Save
                </Button>
                <Button size="sm" variant="outline" onClick={() => setEditing(false)}>Cancel</Button>
              </div>
            </div>
          ) : (
            <p className="text-foreground whitespace-pre-wrap">{comment.body}</p>
          )}
          <p className="text-[11px] text-muted-foreground mt-1">
            {formatDateTime(comment.created_at)}
            {comment.is_edited && " · edited"}
            {comment.is_resolved && " · resolved"}
          </p>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {isQA && !comment.is_resolved && (
            <button
              onClick={() => resolveMut.mutate(comment.id)}
              title="Resolve"
              className="text-muted-foreground hover:text-green-600 transition-colors"
            >
              <CheckCircle className="h-3.5 w-3.5" />
            </button>
          )}
          {isOwn && !editing && (
            <button
              onClick={() => { setEditBody(comment.body); setEditing(true); }}
              title="Edit"
              className="text-muted-foreground hover:text-primary transition-colors"
            >
              <Pencil className="h-3.5 w-3.5" />
            </button>
          )}
          {isOwn && (
            <button
              onClick={() => deleteMut.mutate(comment.id)}
              title="Delete"
              className="text-muted-foreground hover:text-destructive transition-colors"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

export function WorkflowDetailView({ id }: { id: string }) {
  const { user } = useAuthStore();
  const { isQAOfficer, isCoordinator, isStudent, isSysAdmin } = useRole();

  const { data: workflow, isLoading, isError, refetch } = useWorkflow(id);
  const { data: comments } = useComments(id);

  const assignMut = useAssignAudit();
  const statusMut = useUpdateWorkflowStatus();
  const createCommentMut = useCreateComment(id);

  const [newComment, setNewComment] = useState("");
  const [assignToId, setAssignToId] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [priority, setPriority] = useState<AuditPriority | "">("");
  const [remarks, setRemarks] = useState("");
  const [targetStatus, setTargetStatus] = useState<WorkflowStatus | "">("");

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-20 rounded-xl" />)}
        </div>
        <Skeleton className="h-48 rounded-xl" />
      </div>
    );
  }
  if (isError || !workflow) {
    return <ErrorState title="Workflow not found" onRetry={() => refetch()} />;
  }

  const allowedStatuses: WorkflowStatus[] = isSysAdmin
    ? Object.keys(WORKFLOW_STATUS_LABELS) as WorkflowStatus[]
    : isQAOfficer
      ? QA_TARGET_STATUSES
      : isCoordinator
        ? COORD_TARGET_STATUSES
        : [];

  async function handleStatusChange() {
    if (!targetStatus) return;
    await statusMut.mutateAsync({
      audit_id: id,
      new_status: targetStatus,
      remarks: remarks || null,
    });
    setTargetStatus("");
    setRemarks("");
  }

  async function handleAssign() {
    if (!assignToId) return;
    await assignMut.mutateAsync({
      audit_id: id,
      assigned_to_id: assignToId,
      due_date: dueDate || null,
      priority: (priority as AuditPriority) || null,
      remarks: remarks || null,
    });
    setAssignToId("");
    setDueDate("");
    setPriority("");
    setRemarks("");
  }

  async function handleComment() {
    if (!newComment.trim()) return;
    await createCommentMut.mutateAsync(newComment.trim());
    setNewComment("");
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Audit Workflow"
        subtitle={`Academic Year: ${workflow.academic_year}`}
      />

      {/* Status summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          {
            label: "Workflow Status",
            value: wfBadge(workflow.workflow_status),
          },
          {
            label: "Priority",
            value: workflow.priority
              ? <span className={cn("text-sm font-semibold", PRIORITY_COLOURS[workflow.priority])}>{PRIORITY_LABELS[workflow.priority]}</span>
              : <span className="text-sm text-muted-foreground">—</span>,
          },
          {
            label: "Due Date",
            value: <span className="text-sm font-medium">{workflow.due_date ? formatDateTime(workflow.due_date) : "—"}</span>,
          },
          {
            label: "Compliance",
            value: (
              <span className={cn(
                "text-2xl font-bold tabular-nums",
                workflow.compliance_percentage >= 90 ? "text-green-600"
                  : workflow.compliance_percentage >= 70 ? "text-amber-600"
                  : "text-red-600",
              )}>
                {workflow.compliance_percentage.toFixed(0)}%
              </span>
            ),
          },
        ].map(({ label, value }) => (
          <div key={label} className="rounded-xl border border-border bg-card p-4 flex flex-col gap-2">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
            {value}
          </div>
        ))}
      </div>

      {/* Assignment info */}
      {(workflow.assigned_to_id || workflow.assigned_by_id) && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <User className="h-4 w-4" /> Assignment
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-xs text-muted-foreground">Assigned To</p>
              <p className="font-medium text-foreground">{workflow.assigned_to_id ?? "—"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Assigned By</p>
              <p className="font-medium text-foreground">{workflow.assigned_by_id ?? "—"}</p>
            </div>
            {workflow.assigned_date && (
              <div>
                <p className="text-xs text-muted-foreground">Assigned Date</p>
                <p>{formatDateTime(workflow.assigned_date)}</p>
              </div>
            )}
            {workflow.assignment_remarks && (
              <div className="col-span-2">
                <p className="text-xs text-muted-foreground">Remarks</p>
                <p className="text-foreground">{workflow.assignment_remarks}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Actions panel */}
      {!isStudent && (
        <div className="grid sm:grid-cols-2 gap-4">
          {/* Change Status */}
          {allowedStatuses.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Flag className="h-4 w-4" /> Change Status
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <select
                  value={targetStatus}
                  onChange={(e) => setTargetStatus(e.target.value as WorkflowStatus)}
                  className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="">Select new status…</option>
                  {allowedStatuses.map((s) => (
                    <option key={s} value={s}>{WORKFLOW_STATUS_LABELS[s]}</option>
                  ))}
                </select>
                <input
                  type="text"
                  placeholder="Remarks (optional)"
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                  className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                />
                <Button
                  size="sm"
                  className="w-full"
                  disabled={!targetStatus || statusMut.isPending}
                  onClick={handleStatusChange}
                >
                  {statusMut.isPending && <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />}
                  Update Status
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Assign audit */}
          {isCoordinator && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <User className="h-4 w-4" /> Assign Audit
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <input
                  type="text"
                  placeholder="Assignee User ID (UUID)"
                  value={assignToId}
                  onChange={(e) => setAssignToId(e.target.value)}
                  className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm font-mono"
                />
                <input
                  type="datetime-local"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                />
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as AuditPriority | "")}
                  className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="">Priority (optional)</option>
                  {(["low", "medium", "high", "critical"] as AuditPriority[]).map((p) => (
                    <option key={p} value={p}>{PRIORITY_LABELS[p]}</option>
                  ))}
                </select>
                <Button
                  size="sm"
                  className="w-full"
                  disabled={!assignToId || assignMut.isPending}
                  onClick={handleAssign}
                >
                  {assignMut.isPending && <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />}
                  Assign
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Comments */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <MessageSquare className="h-4 w-4" /> Comments
            {comments && comments.length > 0 && (
              <span className="ml-1 rounded-full bg-muted px-2 py-0.5 text-xs font-normal text-muted-foreground">
                {comments.length}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {comments && comments.length > 0 ? (
            <div className="space-y-2">
              {comments.map((c: AuditComment) => (
                <CommentItem
                  key={c.id}
                  comment={c}
                  currentUserId={user?.id}
                  isQA={isQAOfficer}
                  auditId={id}
                />
              ))}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">No comments yet. Be the first to comment.</p>
          )}

          {!isStudent && (
            <div className="flex gap-2 pt-2">
              <textarea
                rows={2}
                placeholder="Add a comment…"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              />
              <Button
                size="sm"
                disabled={!newComment.trim() || createCommentMut.isPending}
                onClick={handleComment}
                className="self-end"
              >
                {createCommentMut.isPending
                  ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  : <Send className="h-3.5 w-3.5" />}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
