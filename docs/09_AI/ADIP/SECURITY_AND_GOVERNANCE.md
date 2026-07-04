# ADIP — Security and Governance (Layer 10)

**Document ID:** ADIP-SEC-001  
**Version:** 1.0.0  
**Status:** Architecture Design  
**Last Updated:** 2026-06-29

---

## 1. Security Model

ADIP inherits AQAA's multi-tenant security model and extends it for document intelligence operations.

### 1.1 Tenant Isolation

Every ADIP entity is institution-scoped:

| Table/Index | Isolation Key |
|-------------|-------------|
| `adip_document_records` | `institution_id` |
| `adip_extraction_chunks` | `institution_id` |
| `adip_knowledge_candidates` | `institution_id` |
| `adip_provenance_anchors` | `institution_id` |
| Qdrant collections | One collection per institution: `adip_chunks_tut`, `adip_chunks_up`, etc. |
| File storage paths | `adip/{institution_id}/...` (path prefix enforced at storage layer) |

**System Admin** may query across institutions for platform-level analytics.  
All other roles are strictly scoped to their `institution_id`.

### 1.2 RBAC for ADIP Operations

| Operation | Minimum Role |
|-----------|-------------|
| View document list for own institution | LECTURER |
| Upload document | PROGRAMME_COORDINATOR |
| Submit URL for ingestion | QUALITY_ASSURANCE_OFFICER |
| View extraction results | QUALITY_ASSURANCE_OFFICER |
| Access human review queue | QUALITY_ASSURANCE_OFFICER |
| Approve/reject knowledge candidates | QUALITY_ASSURANCE_OFFICER |
| Delete document from registry | SYSTEM_ADMIN |
| Cross-institution document query | SYSTEM_ADMIN |
| Manage institution-specific classification rules | SYSTEM_ADMIN |
| Submit bulk ZIP ingestion | QUALITY_ASSURANCE_OFFICER |

### 1.3 Document Access Control

Documents stored in ADIP are access-controlled at three levels:

| Access Level | Who Can Access | Example |
|-------------|---------------|---------|
| `public` | Any authenticated user of the institution | Institution website capture |
| `institution_admin` | QA Officer and above | Prospectus PDFs, policy documents |
| `sensitive` | QA Officer and above, with specific permission | Examination papers, moderation records |
| `restricted` | System Admin only | Certificates, transcripts containing PII |

---

## 2. Immutable Source Snapshots

**Rule:** Original source documents are never modified or deleted after registration.

**Implementation:**
- Write-once storage path pattern: `adip/{institution_id}/{year}/{content_hash_prefix}/{uuid}.ext`
- After write: storage path set to read-only (file system permission)
- Deletion only via formal data deletion request (POPIA compliance process)
- Deletion creates a tombstone record (document ID preserved, file removed, reason logged)

**Why immutable:**
- Source documents serve as legal evidence in accreditation disputes
- "What did AQAA believe in 2025?" requires the 2025 source document to still exist
- AI agents cite sources by document ID — broken source links undermine citation integrity

---

## 3. Audit Log

Every ADIP operation is logged in the `adip_audit_log` table:

```json
{
  "id": "UUID",
  "institution_id": "UUID",
  "actor_id": "UUID (user or system)",
  "action": "document_registered | document_classified | extraction_completed | candidate_approved | candidate_rejected | candidate_quarantined | source_deleted",
  "document_id": "UUID",
  "details": {},
  "timestamp": "2026-06-29T10:00:00Z",
  "ip_address": "10.0.0.1"
}
```

The audit log is append-only (no updates or deletes). It is the authoritative record of all ADIP activity.

---

## 4. Sensitive Data Handling

### 4.1 Personal Information in Documents

ADIP may encounter PII in uploaded documents (student names in attendance registers, examiner names in moderation reports, lecturers' credentials in CVs).

**POPIA compliance controls:**

| PII Type | ADIP Action |
|---------|------------|
| Student names in attendance registers | Index as metadata only; not included in full-text search results visible to non-authorised users |
| Student numbers | Store but mask in UI: `S123456` → `S*****6` for lecturer role |
| Examiner names in moderation reports | Index normally (relevant to QA) |
| CVs/personal qualifications | Restricted access level; not indexed in public search |
| Examination question papers | Sensitive access level; date-restricted access |

### 4.2 Examination Paper Security

Pre-release examination papers (not yet published) receive special handling:
- Access level: `restricted` until the examination date passes
- Access level auto-changes to `institution_admin` after `examination_date + 1 year`
- Never included in vector search results accessible to students

---

## 5. Data Retention

| Data Category | Retention Period | Archival |
|--------------|-----------------|---------|
| Source documents (institutional knowledge) | 7 years minimum | Archive to cold storage after 3 years |
| Source documents (QA evidence) | 7 years minimum | Archive after 5 years |
| Extraction chunks and tables | 7 years | Archive with source document |
| Provenance anchors | Indefinite | Never deleted |
| Audit logs | Indefinite | Never deleted |
| Human review queue (completed) | 3 years | Then delete decision log but keep anchor |
| Quarantined documents | 2 years | Delete after 2 years if not rescued |

**Data deletion on institution offboarding:**
When an institution leaves AQAA, all their data is:
1. Exported as a complete ADIP package (institutional data portability — POPIA requirement)
2. Deleted from live systems
3. Tombstoned in audit log with reason `institution_offboarded`
4. Source files retained in cold storage per regulatory minimums

---

## 6. Version Control

Every document registered in ADIP is versioned:

| Version Field | Meaning |
|-------------|---------|
| `version: 1` | First registration of this content hash |
| `version: 2` | Updated document registered (same source URL, different content) |
| `is_current_version: true/false` | Only the latest version serves as the "active" knowledge source |

**Version trigger rules:**
- Same URL + same hash → no new version (duplicate, skip)
- Same URL + different hash → new version (content changed)
- Different URL + same hash → alternative source (no new version; link to existing)
- Different URL + different hash → new document (not a version, fresh registration)

---

## 7. Compliance Reporting

ADIP generates compliance reports for institutional governance:

| Report | Frequency | Recipient |
|--------|-----------|---------|
| Documents ingested this month | Monthly | QA Officer |
| Human review queue status | Weekly | QA Officer |
| Data completeness by IKP layer | Quarterly | System Admin |
| Provenance gap report (missing sources) | Quarterly | System Admin |
| Quarantined items requiring investigation | On-event | QA Officer |
| Data retention compliance status | Annual | System Admin |
