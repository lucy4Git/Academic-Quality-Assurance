"""ORM model package."""

from app.adip.models.candidate import ADIPExtractionCandidate
from app.adip.models.chunk import ADIPDocumentChunk
from app.adip.models.document import ADIPDocument
from app.adip.models.provenance import ADIPProvenanceAnchor
from app.models.acquisition_job import AcquisitionJob, JobStatus
from app.models.acquisition_log import AcquisitionLog
from app.models.acquisition_source import AcquisitionSource
from app.models.document_version import DocumentVersion
from app.models.downloaded_document import DownloadedDocument
from app.models.extraction_run import ExtractionRun
from app.models.extraction_candidate import ExtractionCandidate
from app.models.audit_comment import AuditComment
from app.models.audit_evidence import AuditEvidence
from app.models.audit_finding import AuditFinding
from app.models.audit_history import AuditHistory
from app.models.accreditation import Accreditation, AccreditationBody
from app.models.audit_run import AuditRun
from app.models.base import Base
from app.models.campus import Campus
from app.models.contact import Contact
from app.models.department import Department
from app.models.document_record import DocumentRecord
from app.models.enums import (
    AgentType,
    AuditPriority,
    AuditRunStatus,
    AuditStatus,
    ChecklistItemStatus,
    FileCategory,
    FindingSeverity,
    FindingType,
    ModuleAuditStatus,
    NotificationType,
    ProcessingStatus,
    ProgrammeLevel,
    ReviewBatchStatus,
    ReviewItemStatus,
    UploadState,
    UserRole,
    WorkflowStatus,
)
from app.models.faculty import Faculty
from app.models.file import File
from app.models.file_version import FileVersion
from app.models.graduate_attribute import GraduateAttribute
from app.models.institution import Institution
from app.models.institution_document import InstitutionDocument
from app.models.institution_qualification import Qualification
from app.models.learning_outcome import LearningOutcome
from app.models.module import Module
from app.models.knowledge_review import KnowledgeReviewBatch, KnowledgeReviewItem
from app.models.module_audit import AuditChecklistItem, ModuleAudit
from app.models.notification import Notification
from app.models.policy import Policy, PolicyVersion
from app.models.programme import Programme
from app.models.school import School
from app.models.user import User

__all__ = [
    "ADIPDocument",
    "ADIPDocumentChunk",
    "ADIPExtractionCandidate",
    "ADIPProvenanceAnchor",
    "Accreditation",
    "AccreditationBody",
    "AcquisitionJob",
    "AcquisitionLog",
    "AcquisitionSource",
    "DocumentVersion",
    "DownloadedDocument",
    "ExtractionRun",
    "ExtractionCandidate",
    "JobStatus",
    "AgentType",
    "Campus",
    "Contact",
    "GraduateAttribute",
    "InstitutionDocument",
    "LearningOutcome",
    "Policy",
    "PolicyVersion",
    "Qualification",
    "School",
    "AuditChecklistItem",
    "AuditComment",
    "AuditEvidence",
    "AuditFinding",
    "AuditHistory",
    "AuditPriority",
    "AuditRun",
    "AuditRunStatus",
    "AuditStatus",
    "Base",
    "ChecklistItemStatus",
    "Department",
    "DocumentRecord",
    "Faculty",
    "File",
    "FileCategory",
    "FileVersion",
    "FindingSeverity",
    "FindingType",
    "Institution",
    "KnowledgeReviewBatch",
    "KnowledgeReviewItem",
    "Module",
    "ModuleAudit",
    "ModuleAuditStatus",
    "Notification",
    "NotificationType",
    "ProcessingStatus",
    "Programme",
    "ReviewBatchStatus",
    "ReviewItemStatus",
    "ProgrammeLevel",
    "UploadState",
    "User",
    "UserRole",
    "WorkflowStatus",
]
