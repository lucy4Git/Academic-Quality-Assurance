/**
 * TypeScript types for the Knowledge Review Centre.
 */

export type ReviewBatchStatus =
  | "open"
  | "in_review"
  | "approved"
  | "exported"
  | "closed";

export type ReviewItemStatus =
  | "pending_review"
  | "approved"
  | "rejected"
  | "edited"
  | "quarantined"
  | "imported";

export interface KnowledgeReviewBatch {
  id: string;
  batch_name: string;
  institution_id: string;
  ikp_version: string;
  academic_year: string;
  faculty_scope: string | null;
  status: ReviewBatchStatus;
  source_extraction_path: string | null;
  total_items: number;
  approved_count: number;
  rejected_count: number;
  pending_count: number;
  created_by: string | null;
  reviewed_by: string | null;
  closed_at: string | null;
  exported_at: string | null;
  export_path: string | null;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeReviewBatchSummary {
  id: string;
  batch_name: string;
  institution_id: string;
  ikp_version: string;
  academic_year: string;
  faculty_scope: string | null;
  status: ReviewBatchStatus;
  total_items: number;
  approved_count: number;
  rejected_count: number;
  pending_count: number;
  created_at: string;
}

export interface KnowledgeReviewItem {
  id: string;
  batch_id: string;
  institution_id: string;
  candidate_id: string | null;
  entity_type: string;
  entity_key: string;
  field_name: string;
  extracted_value: string;
  edited_value: string | null;
  confidence_score: number;
  extraction_method: string | null;
  source_document: string | null;
  page_number: number | null;
  provenance_anchor_id: string | null;
  status: ReviewItemStatus;
  reviewer_id: string | null;
  decision_reason: string | null;
  reviewed_at: string | null;
  academic_year: string | null;
  ikp_version: string | null;
  created_at: string;
  updated_at: string;
}

export interface BatchFromADIPRequest {
  institution_id: string;
  batch_name: string;
  ikp_version: string;
  academic_year: string;
  faculty_scope?: string;
  source_extraction_dir?: string;
}

export interface ApproveItemRequest {
  decision_reason?: string;
}

export interface RejectItemRequest {
  decision_reason: string;
}

export interface EditItemRequest {
  edited_value: string;
  decision_reason?: string;
}

export interface ApproveAllEligibleResult {
  newly_approved: number;
}

export interface ExportResult {
  export_path: string;
  total_approved: number;
  programmes_count: number;
  modules_count: number;
  admission_requirements_count: number;
}
