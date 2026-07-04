export interface AuditHistory {
  id: string;
  audit_id: string;
  actor_id: string | null;
  event_type: string;
  summary: string;
  detail: string | null;
  created_at: string;
}
