# ADIP — Document Source Layer (Layer 1) and Document Registry (Layer 2)

**Document ID:** ADIP-L1-L2-001  
**Version:** 1.0.0  
**Status:** Architecture Design  
**Last Updated:** 2026-06-29

---

## 1. Overview

The Document Source Layer is ADIP's entry point. Every document that AQAA processes — whether a TUT prospectus PDF, an HTML faculty page, a ZIP evidence pack, or a lecturer-uploaded marking guide — enters ADIP through this layer.

The Document Registry Layer immediately follows: every accepted document is registered with a unique identity, content hash, storage reference, and tenant ownership before any further processing.

---

## 2. Source Types

ADIP accepts documents from six source types:

### 2.1 Direct File Upload
**Trigger:** API call with multipart form data  
**Context:** Institutional admin uploads a prospectus PDF; lecturer uploads evidence  
**Formats:** Any format in ADIP's supported list  
**Auth required:** Yes — `institution_id` from authenticated user  
**Endpoint (planned):** `POST /api/v1/adip/upload`

```
Request:
  file: binary
  source_type: "file_upload"
  document_category: "prospectus" | "evidence" | "policy" | ...
  institution_id: UUID (from auth context)
  description: string (optional)
  academic_year: string (optional)
```

### 2.2 URL Ingestion
**Trigger:** ADIP URL ingestion job with a URL and fetch instructions  
**Context:** ADIP engineer submits `https://www.tut.ac.za/ict/computer-science/` for ingestion  
**Method:** HTTP GET → content saved as HTML + full rendered snapshot  
**Auth required:** ADIP admin role  
**Endpoint (planned):** `POST /api/v1/adip/ingest-url`

```
Request:
  url: string (HTTPS required)
  institution_id: UUID
  render_javascript: boolean (false for static, true for dynamic pages)
  document_category: string
  follow_links: false (no recursive crawling — explicit submission only)
```

### 2.3 Web Page Capture
**Trigger:** ADIP captures a rendered page (JavaScript-heavy sites)  
**Method:** Playwright headless Chromium → HTML + screenshot  
**Use case:** Institution websites that load content dynamically (React SPAs, etc.)  
**Stored artefacts:** Raw HTML, rendered screenshot, extracted text

### 2.4 Bulk ZIP Ingestion
**Trigger:** Admin uploads a ZIP archive  
**Context:** Institution submits an evidence pack as a ZIP; ADIP unpacks and processes each file  
**Method:** Unzip → classify each file → process individually through ADIP pipeline  
**Endpoint (planned):** `POST /api/v1/adip/upload-zip`

ZIP structure conventions:
```
evidence_pack_2026.zip
├── module_CS101/
│   ├── assessment_brief.pdf
│   ├── marking_guide.docx
│   └── moderation_report.xlsx
└── module_CS201/
    └── ...
```

ADIP infers metadata from directory names if they follow the `module_{CODE}/` convention.

### 2.5 Institutional Repository Import
**Trigger:** ADIP connects to an institution's document repository (SharePoint, Google Drive, Moodle)  
**Method:** REST API or OAuth integration  
**Status:** Planned (Phase 7) — architecture reserved, not implemented  
**Notes:** Will require institution-specific connector per platform

### 2.6 Manual Admin Entry
**Trigger:** ADIP admin manually enters structured data without a source document  
**Context:** Data known from direct institutional contact but not in any document  
**Confidence:** 0.82 (manual_entry) if reviewer identified; 0.50 if unattributed  
**Endpoint (planned):** `POST /api/v1/adip/manual-entry`

---

## 3. Document Registry

Every accepted source produces one **DocumentRecord** in the ADIP registry.

### 3.1 DocumentRecord Schema

```json
{
  "id": "UUID",
  "institution_id": "UUID",
  "source_type": "file_upload | url_ingestion | web_capture | zip_item | repo_import | manual_entry",
  "original_filename": "Part6_ICT_Prospectus.pdf",
  "content_hash_sha256": "abc123...",
  "file_size_bytes": 1342000,
  "mime_type": "application/pdf",
  "storage_path": "adip/{institution_id}/{year}/{uuid}.pdf",
  "source_url": "https://www.tut.ac.za/media/.../Part6_ICT_Prospectus.pdf",
  "document_category": "prospectus",
  "document_type": null,
  "academic_year": "2026",
  "language": "en",
  "page_count": null,
  "processing_state": "pending",
  "registered_at": "2026-06-29T10:00:00Z",
  "registered_by": "UUID (user or system)",
  "last_processed_at": null,
  "version": 1,
  "is_official_source": true,
  "is_immutable": true,
  "retention_policy": "7_years",
  "access_level": "institution_admin"
}
```

### 3.2 Content Hash and Deduplication

Every document is SHA-256 hashed on receipt. Before registration:
1. Check if `content_hash_sha256` already exists for this `institution_id`
2. If yes → **duplicate detected**:
   - If source URL differs → link as "alternative source" for same content
   - If same source URL → reject as exact duplicate (return existing record ID)
   - If same content hash, different academic year → register as new version (increment `version`)
3. If no → register as new document

### 3.3 Immutable Source Storage

All source documents are stored immutably:
- Path: `adip/{institution_id}/{year}/{sha256_prefix}/{uuid}{ext}`
- Write-once: after writing, no process may overwrite or delete the file
- Deletion only via institution data deletion request (POPIA compliance) through ADIP admin

### 3.4 Version Tracking

When AQAA receives an updated version of a document (e.g., the 2027 TUT ICT Prospectus):
```
DocumentRecord (Part6_ICT_Prospectus.pdf, 2026, version=1) → status: SUPERSEDED
DocumentRecord (Part6_ICT_Prospectus.pdf, 2027, version=2) → status: ACTIVE
```

All extracted data from version 1 is preserved. AI agents can query specific versions.

---

## 4. Ingestion Rate Limits and Queue Management

| Source Type | Rate Limit | Queue | Priority |
|-------------|-----------|-------|---------|
| Direct file upload (user) | 50 MB per file, 20 files per hour | Synchronous for < 5 MB; async for larger | High |
| URL ingestion (admin) | 10 URLs per minute | Async background job | Medium |
| ZIP ingestion | 500 MB per archive | Async background job | Medium |
| Repository import | Configurable per connector | Batch nightly | Low |

---

## 5. Source Layer Security

- All uploads require authenticated user with `institution_id` binding
- URL ingestion restricted to ADIP Admin role (system-level)
- Source documents stored with institution-scoped path — cross-institution file access impossible via storage path guessing
- MIME type validation on upload (magic byte check, not just extension)
- Max file size enforced: 200 MB for ADIP (larger than 50 MB evidence limit — prospectus PDFs may be large)
- ZIP bomb protection: max uncompressed ratio 100:1, max total uncompressed 2 GB

---

## 6. Source Layer Output

After successful registration, the Source Layer emits a **DocumentIngestionEvent**:
```json
{
  "event_type": "document_registered",
  "document_id": "UUID",
  "institution_id": "UUID",
  "source_type": "file_upload",
  "mime_type": "application/pdf",
  "storage_path": "adip/...",
  "registered_at": "2026-06-29T10:00:00Z"
}
```

This event triggers the Classification Engine (Layer 3).
