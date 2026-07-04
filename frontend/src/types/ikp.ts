/**
 * TypeScript types for the IKP Management API.
 * Mirrors backend/app/ikp/ikp_schemas.py.
 */

export interface IkpPackageSummary {
  institution_code: string;
  academic_year: string;
  ikp_version: string;
  chunk_count: number;
  entity_type_breakdown: Record<string, number>;
  avg_confidence: number;
  min_confidence: number;
  max_confidence: number;
  qdrant_indexed: boolean;
  qdrant_collection: string | null;
  has_extracted_output: boolean;
}

export interface IkpChunk {
  chunk_id: string;
  entity_type: string;
  entity_key: string;
  text: string;
  source_document: string;
  confidence_score: number;
  academic_year: string;
  ikp_version: string;
  institution_code: string;
}

export interface IkpChunkPage {
  total: number;
  skip: number;
  limit: number;
  chunks: IkpChunk[];
}

export interface IkpReindexRequest {
  force_recreate: boolean;
}

export interface IkpReindexResult {
  collection: string;
  chunks_indexed: number;
  status: string;
  message: string;
}

export interface IkpCreateReviewBatchRequest {
  batch_name: string;
  institution_id: string;
  faculty_scope?: string | null;
}

export interface IkpCreateReviewBatchResult {
  batch_id: string;
  batch_name: string;
  status: string;
  total_items: number;
}
