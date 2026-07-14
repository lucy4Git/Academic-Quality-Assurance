"""Phase C — Regulatory and Quality Framework Engine tables.

Creates:
  regulatory_authorities
  quality_frameworks
  framework_versions
  framework_standards
  framework_criteria
  evidence_requirements
  applicability_rules
  evidence_mappings
  framework_assessment_runs
  criterion_assessment_results
  cross_framework_mappings

Extends:
  audit_findings — adds nullable regulatory FK columns

Revision ID: a1b2c3d4e5f7
Revises: 7a8b9c0d1e2f
Create Date: 2026-07-14 09:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "a1b2c3d4e5f7"
down_revision = "7a8b9c0d1e2f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # regulatory_authorities
    # ------------------------------------------------------------------
    op.create_table(
        "regulatory_authorities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("institution_id", UUID(as_uuid=True),
                  sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("short_name", sa.String(40), nullable=True),
        sa.Column("authority_type", sa.String(40), nullable=False),
        sa.Column("jurisdiction", sa.String(100), nullable=True),
        sa.Column("country", sa.String(60), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("official_website", sa.String(500), nullable=True),
        sa.Column("contact_information", sa.Text, nullable=True),
        sa.Column("is_external", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_internal", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("code", name="uq_regulatory_authorities_code"),
    )
    op.create_index("ix_regulatory_authorities_code", "regulatory_authorities", ["code"])
    op.create_index("ix_regulatory_authorities_institution_id", "regulatory_authorities", ["institution_id"])
    op.create_index("ix_regulatory_authorities_authority_type", "regulatory_authorities", ["authority_type"])

    # ------------------------------------------------------------------
    # quality_frameworks
    # ------------------------------------------------------------------
    op.create_table(
        "quality_frameworks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("authority_id", UUID(as_uuid=True),
                  sa.ForeignKey("regulatory_authorities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("institution_id", UUID(as_uuid=True),
                  sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("framework_type", sa.String(50), nullable=False),
        sa.Column("scope", sa.String(30), nullable=False),
        sa.Column("jurisdiction", sa.String(100), nullable=True),
        sa.Column("is_mandatory", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_public", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_quality_frameworks_authority_id", "quality_frameworks", ["authority_id"])
    op.create_index("ix_quality_frameworks_institution_id", "quality_frameworks", ["institution_id"])
    op.create_index("ix_quality_frameworks_code", "quality_frameworks", ["code"])
    op.create_index("ix_quality_frameworks_framework_type", "quality_frameworks", ["framework_type"])

    # ------------------------------------------------------------------
    # framework_versions
    # ------------------------------------------------------------------
    op.create_table(
        "framework_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("framework_id", UUID(as_uuid=True),
                  sa.ForeignKey("quality_frameworks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.String(30), nullable=False),
        sa.Column("version_label", sa.String(100), nullable=True),
        sa.Column("publication_date", sa.Date, nullable=True),
        sa.Column("effective_from", sa.Date, nullable=True),
        sa.Column("effective_to", sa.Date, nullable=True),
        sa.Column("review_date", sa.Date, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("supersedes_version_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_document_id", UUID(as_uuid=True),
                  sa.ForeignKey("files.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("change_summary", sa.Text, nullable=True),
        sa.Column("approved_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_framework_versions_framework_id", "framework_versions", ["framework_id"])
    op.create_index("ix_framework_versions_status", "framework_versions", ["status"])
    op.create_index("ix_framework_versions_effective_from", "framework_versions", ["effective_from"])
    op.create_index("ix_framework_versions_effective_to", "framework_versions", ["effective_to"])

    # ------------------------------------------------------------------
    # framework_standards
    # ------------------------------------------------------------------
    op.create_table(
        "framework_standards",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("framework_version_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_standard_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_standards.id", ondelete="CASCADE"), nullable=True),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("sequence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("weight", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("is_mandatory", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("citation_reference", sa.String(500), nullable=True),
        sa.Column("created_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_framework_standards_framework_version_id", "framework_standards", ["framework_version_id"])
    op.create_index("ix_framework_standards_parent_standard_id", "framework_standards", ["parent_standard_id"])

    # ------------------------------------------------------------------
    # framework_criteria
    # ------------------------------------------------------------------
    op.create_table(
        "framework_criteria",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("standard_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_standards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_criterion_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_criteria.id", ondelete="CASCADE"), nullable=True),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("evaluation_guidance", sa.Text, nullable=True),
        sa.Column("sequence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("weight", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("threshold", sa.Float, nullable=True),
        sa.Column("is_mandatory", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("requires_human_review", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("evaluation_method", sa.String(30), nullable=False, server_default="document_presence"),
        sa.Column("citation_reference", sa.String(500), nullable=True),
        sa.Column("created_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_framework_criteria_standard_id", "framework_criteria", ["standard_id"])

    # ------------------------------------------------------------------
    # evidence_requirements
    # ------------------------------------------------------------------
    op.create_table(
        "evidence_requirements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("criterion_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_criteria.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("evidence_type", sa.String(30), nullable=False, server_default="document"),
        sa.Column("document_category", sa.String(40), nullable=True),
        sa.Column("minimum_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("maximum_age_days", sa.Integer, nullable=True),
        sa.Column("requires_signature", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("requires_approval", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("requires_date", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("requires_version", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_mandatory", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("quality_threshold", sa.Float, nullable=True),
        sa.Column("validation_rule", sa.Text, nullable=True),
        sa.Column("accepted_file_types", sa.String(200), nullable=True),
        sa.Column("created_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_evidence_requirements_criterion_id", "evidence_requirements", ["criterion_id"])
    op.create_index("ix_evidence_requirements_document_category", "evidence_requirements", ["document_category"])

    # ------------------------------------------------------------------
    # applicability_rules
    # ------------------------------------------------------------------
    op.create_table(
        "applicability_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("framework_version_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("standard_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_standards.id", ondelete="SET NULL"), nullable=True),
        sa.Column("criterion_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_criteria.id", ondelete="SET NULL"), nullable=True),
        sa.Column("rule_name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("target_entity_type", sa.String(30), nullable=False),
        sa.Column("rule_conditions", sa.Text, nullable=True),
        sa.Column("priority", sa.Integer, nullable=False, server_default="100"),
        sa.Column("is_inclusion_rule", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_exclusion_rule", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("effective_from", sa.Date, nullable=True),
        sa.Column("effective_to", sa.Date, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_applicability_rules_framework_version_id", "applicability_rules", ["framework_version_id"])
    op.create_index("ix_applicability_rules_target_entity_type", "applicability_rules", ["target_entity_type"])

    # ------------------------------------------------------------------
    # evidence_mappings
    # ------------------------------------------------------------------
    op.create_table(
        "evidence_mappings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("institution_id", UUID(as_uuid=True),
                  sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("framework_version_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("standard_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_standards.id", ondelete="SET NULL"), nullable=True),
        sa.Column("criterion_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_criteria.id", ondelete="SET NULL"), nullable=True),
        sa.Column("evidence_requirement_id", UUID(as_uuid=True),
                  sa.ForeignKey("evidence_requirements.id", ondelete="SET NULL"), nullable=True),
        sa.Column("file_id", UUID(as_uuid=True),
                  sa.ForeignKey("files.id", ondelete="SET NULL"), nullable=True),
        sa.Column("programme_id", UUID(as_uuid=True),
                  sa.ForeignKey("programmes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("module_id", UUID(as_uuid=True),
                  sa.ForeignKey("modules.id", ondelete="SET NULL"), nullable=True),
        sa.Column("mapping_source", sa.String(30), nullable=False, server_default="manual"),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("validation_status", sa.String(20), nullable=False, server_default="proposed"),
        sa.Column("validated_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("validation_note", sa.Text, nullable=True),
        sa.Column("created_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_evidence_mappings_institution_id", "evidence_mappings", ["institution_id"])
    op.create_index("ix_evidence_mappings_framework_version_id", "evidence_mappings", ["framework_version_id"])
    op.create_index("ix_evidence_mappings_criterion_id", "evidence_mappings", ["criterion_id"])
    op.create_index("ix_evidence_mappings_evidence_requirement_id", "evidence_mappings", ["evidence_requirement_id"])
    op.create_index("ix_evidence_mappings_validation_status", "evidence_mappings", ["validation_status"])

    # ------------------------------------------------------------------
    # framework_assessment_runs
    # ------------------------------------------------------------------
    op.create_table(
        "framework_assessment_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("institution_id", UUID(as_uuid=True),
                  sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("framework_version_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("target_entity_type", sa.String(30), nullable=False),
        sa.Column("target_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_scope", sa.String(200), nullable=True),
        sa.Column("assessment_period", sa.String(100), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="queued"),
        sa.Column("started_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("overall_score", sa.Float, nullable=True),
        sa.Column("mandatory_compliance_score", sa.Float, nullable=True),
        sa.Column("evidence_coverage_score", sa.Float, nullable=True),
        sa.Column("quality_score", sa.Float, nullable=True),
        sa.Column("risk_level", sa.String(20), nullable=True),
        sa.Column("readiness_status", sa.String(30), nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("limitations", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("criteria_total", sa.Integer, nullable=True),
        sa.Column("criteria_met", sa.Integer, nullable=True),
        sa.Column("criteria_unmet", sa.Integer, nullable=True),
        sa.Column("mandatory_failures", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_framework_assessment_runs_institution_id", "framework_assessment_runs", ["institution_id"])
    op.create_index("ix_framework_assessment_runs_framework_version_id", "framework_assessment_runs", ["framework_version_id"])
    op.create_index("ix_framework_assessment_runs_target_entity_id", "framework_assessment_runs", ["target_entity_id"])
    op.create_index("ix_framework_assessment_runs_status", "framework_assessment_runs", ["status"])

    # ------------------------------------------------------------------
    # criterion_assessment_results
    # ------------------------------------------------------------------
    op.create_table(
        "criterion_assessment_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("assessment_run_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_assessment_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("criterion_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_criteria.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("evidence_requirement_id", UUID(as_uuid=True),
                  sa.ForeignKey("evidence_requirements.id", ondelete="SET NULL"), nullable=True),
        sa.Column("evidence_found", sa.Integer, nullable=False, server_default="0"),
        sa.Column("evidence_missing", sa.Integer, nullable=False, server_default="0"),
        sa.Column("evidence_ids", sa.Text, nullable=True),
        sa.Column("deterministic_result", sa.Boolean, nullable=True),
        sa.Column("semantic_result", sa.Boolean, nullable=True),
        sa.Column("human_review_result", sa.Boolean, nullable=True),
        sa.Column("requires_human_review", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_met", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_mandatory", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("evaluation_method", sa.String(30), nullable=True),
        sa.Column("citation_reference", sa.String(500), nullable=True),
        sa.Column("explanation", sa.Text, nullable=True),
        sa.Column("recommendation", sa.Text, nullable=True),
        sa.Column("finding_id", UUID(as_uuid=True),
                  sa.ForeignKey("audit_findings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_criterion_assessment_results_assessment_run_id", "criterion_assessment_results", ["assessment_run_id"])
    op.create_index("ix_criterion_assessment_results_criterion_id", "criterion_assessment_results", ["criterion_id"])

    # ------------------------------------------------------------------
    # cross_framework_mappings
    # ------------------------------------------------------------------
    op.create_table(
        "cross_framework_mappings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("framework_version_a_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("standard_a_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_standards.id", ondelete="CASCADE"), nullable=True),
        sa.Column("criterion_a_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_criteria.id", ondelete="CASCADE"), nullable=True),
        sa.Column("framework_version_b_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("standard_b_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_standards.id", ondelete="CASCADE"), nullable=True),
        sa.Column("criterion_b_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_criteria.id", ondelete="CASCADE"), nullable=True),
        sa.Column("relation", sa.String(30), nullable=False),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("human_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("verified_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_cross_framework_mappings_version_a", "cross_framework_mappings", ["framework_version_a_id"])
    op.create_index("ix_cross_framework_mappings_version_b", "cross_framework_mappings", ["framework_version_b_id"])
    op.create_index("ix_cross_framework_mappings_relation", "cross_framework_mappings", ["relation"])

    # ------------------------------------------------------------------
    # Extend audit_findings — nullable regulatory FK columns (Phase C)
    # Existing rows are unaffected; new columns are all nullable.
    # ------------------------------------------------------------------
    op.add_column("audit_findings",
        sa.Column("regulatory_authority_id", UUID(as_uuid=True),
                  sa.ForeignKey("regulatory_authorities.id", ondelete="SET NULL"), nullable=True))
    op.add_column("audit_findings",
        sa.Column("framework_version_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_versions.id", ondelete="SET NULL"), nullable=True))
    op.add_column("audit_findings",
        sa.Column("standard_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_standards.id", ondelete="SET NULL"), nullable=True))
    op.add_column("audit_findings",
        sa.Column("criterion_id", UUID(as_uuid=True),
                  sa.ForeignKey("framework_criteria.id", ondelete="SET NULL"), nullable=True))
    op.add_column("audit_findings",
        sa.Column("evidence_requirement_id", UUID(as_uuid=True),
                  sa.ForeignKey("evidence_requirements.id", ondelete="SET NULL"), nullable=True))
    op.add_column("audit_findings",
        sa.Column("citation_reference", sa.String(500), nullable=True))
    op.add_column("audit_findings",
        sa.Column("regulatory_risk", sa.String(20), nullable=True))

    op.create_index("ix_audit_findings_regulatory_authority_id", "audit_findings", ["regulatory_authority_id"])
    op.create_index("ix_audit_findings_framework_version_id", "audit_findings", ["framework_version_id"])


def downgrade() -> None:
    # Remove Phase C columns from audit_findings
    op.drop_index("ix_audit_findings_framework_version_id", table_name="audit_findings")
    op.drop_index("ix_audit_findings_regulatory_authority_id", table_name="audit_findings")
    op.drop_column("audit_findings", "regulatory_risk")
    op.drop_column("audit_findings", "citation_reference")
    op.drop_column("audit_findings", "evidence_requirement_id")
    op.drop_column("audit_findings", "criterion_id")
    op.drop_column("audit_findings", "standard_id")
    op.drop_column("audit_findings", "framework_version_id")
    op.drop_column("audit_findings", "regulatory_authority_id")

    # Drop Phase C tables (reverse dependency order)
    op.drop_table("cross_framework_mappings")
    op.drop_table("criterion_assessment_results")
    op.drop_table("framework_assessment_runs")
    op.drop_table("evidence_mappings")
    op.drop_table("applicability_rules")
    op.drop_table("evidence_requirements")
    op.drop_table("framework_criteria")
    op.drop_table("framework_standards")
    op.drop_table("framework_versions")
    op.drop_table("quality_frameworks")
    op.drop_table("regulatory_authorities")
