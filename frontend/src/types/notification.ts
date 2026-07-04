export type NotificationType =
  | "audit_assigned"
  | "due_soon"
  | "overdue"
  | "evidence_uploaded"
  | "evidence_missing"
  | "audit_returned"
  | "audit_approved"
  | "audit_rejected"
  | "audit_completed"
  | "new_comment";

export interface Notification {
  id: string;
  recipient_id: string;
  institution_id: string;
  notification_type: NotificationType;
  title: string;
  body: string;
  is_read: boolean;
  audit_id: string | null;
  created_at: string;
}
