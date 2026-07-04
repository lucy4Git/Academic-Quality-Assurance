export interface AuditComment {
  id: string;
  audit_id: string;
  author_id: string | null;
  institution_id: string;
  body: string;
  is_edited: boolean;
  is_resolved: boolean;
  created_at: string;
  updated_at: string;
}
