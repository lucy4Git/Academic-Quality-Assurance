"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Bell, UserCheck, Clock, AlertTriangle, Paperclip, FileX,
  RotateCcw, CheckCircle, XCircle, CheckSquare, MessageSquare,
  CheckCheck,
} from "lucide-react";

import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { cn, formatDateTime } from "@/lib/utils";
import { useNotifications, useMarkNotificationRead, useMarkAllNotificationsRead } from "@/hooks/useNotifications";
import type { Notification, NotificationType } from "@/types";

const TYPE_ICONS: Record<NotificationType, React.ElementType> = {
  audit_assigned: UserCheck,
  due_soon: Clock,
  overdue: AlertTriangle,
  evidence_uploaded: Paperclip,
  evidence_missing: FileX,
  audit_returned: RotateCcw,
  audit_approved: CheckCircle,
  audit_rejected: XCircle,
  audit_completed: CheckSquare,
  new_comment: MessageSquare,
};

const TYPE_COLOURS: Record<NotificationType, string> = {
  audit_assigned: "text-blue-600 bg-blue-50",
  due_soon: "text-amber-600 bg-amber-50",
  overdue: "text-red-600 bg-red-50",
  evidence_uploaded: "text-indigo-600 bg-indigo-50",
  evidence_missing: "text-orange-600 bg-orange-50",
  audit_returned: "text-orange-600 bg-orange-50",
  audit_approved: "text-green-600 bg-green-50",
  audit_rejected: "text-red-600 bg-red-50",
  audit_completed: "text-emerald-600 bg-emerald-50",
  new_comment: "text-slate-600 bg-slate-50",
};

function NotifSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-16 w-full rounded-xl" />)}
    </div>
  );
}

function NotifItem({ notif, onRead }: { notif: Notification; onRead: (id: string) => void }) {
  const Icon = TYPE_ICONS[notif.notification_type] ?? Bell;
  const colour = TYPE_COLOURS[notif.notification_type] ?? "text-slate-600 bg-slate-50";

  const content = (
    <div
      className={cn(
        "flex items-start gap-3 rounded-xl border border-border px-4 py-3 transition-colors cursor-pointer",
        notif.is_read ? "bg-background" : "bg-blue-50/40 border-blue-200",
      )}
      onClick={() => !notif.is_read && onRead(notif.id)}
    >
      <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-full", colour)}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="flex-1 min-w-0">
        <p className={cn("text-sm", notif.is_read ? "text-foreground" : "font-semibold text-foreground")}>
          {notif.title}
        </p>
        <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{notif.body}</p>
        <p className="text-[11px] text-muted-foreground mt-1">{formatDateTime(notif.created_at)}</p>
      </div>
      {!notif.is_read && (
        <div className="h-2 w-2 shrink-0 rounded-full bg-blue-500 mt-1.5" />
      )}
    </div>
  );

  if (notif.audit_id) {
    return (
      <Link href={`/workflow/${notif.audit_id}`} className="block no-underline">
        {content}
      </Link>
    );
  }
  return content;
}

export function NotificationsView() {
  const [unreadOnly, setUnreadOnly] = useState(false);

  const { data, isLoading } = useNotifications({ unread_only: unreadOnly });
  const markReadMut = useMarkNotificationRead();
  const markAllMut = useMarkAllNotificationsRead();

  const unreadCount = (data ?? []).filter((n: Notification) => !n.is_read).length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Notifications"
        subtitle="Your in-app activity feed"
        actions={
          <div className="flex items-center gap-2">
            {unreadCount > 0 && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => markAllMut.mutate()}
                disabled={markAllMut.isPending}
              >
                <CheckCheck className="mr-1.5 h-3.5 w-3.5" />
                Mark all read
              </Button>
            )}
          </div>
        }
      />

      {/* Filter toggle */}
      <div className="flex gap-2">
        <button
          onClick={() => setUnreadOnly(false)}
          className={cn(
            "rounded-full px-4 py-1.5 text-xs font-medium transition-colors",
            !unreadOnly ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-muted/80",
          )}
        >
          All
        </button>
        <button
          onClick={() => setUnreadOnly(true)}
          className={cn(
            "rounded-full px-4 py-1.5 text-xs font-medium transition-colors",
            unreadOnly ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-muted/80",
          )}
        >
          Unread {unreadCount > 0 && `(${unreadCount})`}
        </button>
      </div>

      {isLoading && <NotifSkeleton />}

      {!isLoading && (!data || data.length === 0) && (
        <EmptyState
          title="No notifications"
          description={unreadOnly ? "You have no unread notifications." : "You have no notifications yet."}
          icon={Bell}
        />
      )}

      {!isLoading && data && data.length > 0 && (
        <div className="space-y-2">
          {data.map((notif: Notification) => (
            <NotifItem
              key={notif.id}
              notif={notif}
              onRead={(id) => markReadMut.mutate(id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
