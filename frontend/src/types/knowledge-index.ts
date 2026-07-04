/**
 * TypeScript types for the Knowledge Index and Knowledge Search API.
 * Mirrors backend/app/schemas/knowledge_index.py
 */

// ---------------------------------------------------------------------------
// Index request / response
// ---------------------------------------------------------------------------

export interface IndexRequest {
  institution_code: string;
  academic_year?: string;
  ikp_version?: string;
  force_recreate?: boolean;
}

export interface IndexResult {
  collection: string;
  chunks_indexed: number;
  status: string;
  message: string;
}

// ---------------------------------------------------------------------------
// Status
// ---------------------------------------------------------------------------

export interface CollectionStatus {
  collection: string;
  institution_code: string;
  academic_year: string;
  ikp_version: string;
  exists: boolean;
  points_count: number | null;
  vectors_count: number | null;
  dimension: number | null;
  status: string | null;
}

export interface IndexStatusResponse {
  embedding_model: string;
  is_placeholder_embedding: boolean;
  collections: CollectionStatus[];
}

// ---------------------------------------------------------------------------
// Search request / response
// ---------------------------------------------------------------------------

export interface SearchRequest {
  query: string;
  institution_code?: string;
  entity_type?: string;
  top_k?: number;
  min_confidence?: number;
}

export interface SearchResult {
  score: number;
  entity_type: string;
  entity_id: string;
  title: string;
  text: string;
  source_document: string;
  provenance_id: string;
  confidence_score: number;
  institution_code: string;
  academic_year: string;
  ikp_version: string;
}

export interface SearchResponse {
  query: string;
  institution_code: string;
  total_results: number;
  results: SearchResult[];
  embedding_model: string;
  is_placeholder_embedding: boolean;
}
