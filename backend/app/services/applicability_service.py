"""Applicability Engine — Phase C.

Resolves which framework versions, standards, criteria, and evidence
requirements apply to a given academic entity. Rules are evaluated using a
safe declarative condition tree (no code execution).

Condition tree schema:
  {
    "operator": "AND" | "OR",
    "conditions": [
      {"field": "programme.qualification_type", "op": "eq",  "value": "B.Eng"},
      {"field": "institution.country",           "op": "eq",  "value": "ZA"},
      {"field": "programme.nqf_level",           "op": "in",  "value": [7, 8]},
      {"field": "module.is_capstone",            "op": "eq",  "value": true},
    ]
  }

Supported ops: eq, neq, in, not_in, gt, gte, lt, lte, contains, starts_with
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.applicability_rule import ApplicabilityRule
from app.models.enums import ApplicabilityTargetType, VersionStatus
from app.models.framework_version import FrameworkVersion
from app.models.quality_framework import QualityFramework

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Safe rule evaluator
# ---------------------------------------------------------------------------

_SAFE_OPS: dict[str, Any] = {
    "eq": lambda a, b: a == b,
    "neq": lambda a, b: a != b,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
    "gt": lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
    "contains": lambda a, b: b in str(a),
    "starts_with": lambda a, b: str(a).startswith(str(b)),
}


def _get_field(entity_attrs: dict[str, Any], dotted_field: str) -> Any:
    """Navigate dotted field path into a flat attribute dict.

    The dict is expected to have keys like 'programme.nqf_level' already
    resolved by the caller, or the service builds it from the entity object.
    We support one level of nesting for simplicity.
    """
    return entity_attrs.get(dotted_field)


def _eval_condition(condition: dict[str, Any], entity_attrs: dict[str, Any]) -> bool:
    """Evaluate a single leaf condition against entity attributes."""
    field_path = condition.get("field", "")
    op_name = condition.get("op", "eq")
    expected = condition.get("value")

    actual = _get_field(entity_attrs, field_path)
    if actual is None:
        # Unknown field → condition cannot be satisfied
        return False

    op_fn = _SAFE_OPS.get(op_name)
    if op_fn is None:
        log.warning("Unknown rule op '%s' — treating as false", op_name)
        return False

    try:
        return bool(op_fn(actual, expected))
    except Exception:
        return False


def _eval_tree(node: dict[str, Any], entity_attrs: dict[str, Any]) -> bool:
    """Recursively evaluate a condition tree node."""
    if "operator" in node:
        op = node["operator"].upper()
        children = node.get("conditions", [])
        if op == "AND":
            return all(_eval_tree(c, entity_attrs) for c in children)
        elif op == "OR":
            return any(_eval_tree(c, entity_attrs) for c in children)
        else:
            log.warning("Unknown logical operator '%s'", op)
            return False
    else:
        # Leaf condition
        return _eval_condition(node, entity_attrs)


def evaluate_rule(
    rule: ApplicabilityRule,
    entity_attrs: dict[str, Any],
    evaluation_date: date | None = None,
) -> bool:
    """Return True if the rule matches the entity attributes.

    Checks effective_from/to against evaluation_date (defaults to today).
    """
    today = evaluation_date or date.today()

    if not rule.is_active:
        return False
    if rule.effective_from and rule.effective_from > today:
        return False
    if rule.effective_to and rule.effective_to < today:
        return False

    if not rule.rule_conditions:
        # No conditions → universally applicable (include) or excluded
        return True

    try:
        tree = json.loads(rule.rule_conditions)
    except (json.JSONDecodeError, ValueError):
        log.warning("ApplicabilityRule %s has invalid JSON conditions", rule.id)
        return False

    return _eval_tree(tree, entity_attrs)


# ---------------------------------------------------------------------------
# Resolution result
# ---------------------------------------------------------------------------

@dataclass
class ApplicabilityResolution:
    """Full applicability resolution result for a single entity."""

    applicable_framework_versions: list[FrameworkVersion] = field(default_factory=list)
    exclusions: list[tuple[FrameworkVersion, str]] = field(default_factory=list)  # (version, reason)
    matched_rules: list[ApplicabilityRule] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)  # notes about missing data

    @property
    def framework_version_ids(self) -> list:
        return [v.id for v in self.applicable_framework_versions]


# ---------------------------------------------------------------------------
# Main resolution service
# ---------------------------------------------------------------------------

async def resolve_applicable_frameworks(
    db: AsyncSession,
    *,
    institution_id,
    target_entity_type: ApplicabilityTargetType,
    entity_attrs: dict[str, Any],
    evaluation_date: date | None = None,
) -> ApplicabilityResolution:
    """Resolve all applicable framework versions for the given entity.

    Algorithm:
    1. Load all ACTIVE framework versions visible to this institution
       (public/shared OR institution-specific).
    2. For each version, load its applicability rules.
    3. Apply inclusion rules — entity must match at least one inclusion rule.
    4. Apply exclusion rules — if any match, the version is excluded.
    5. Return sorted result with match provenance.
    """
    today = evaluation_date or date.today()

    # Load active framework versions with their rules
    stmt = (
        select(FrameworkVersion)
        .join(QualityFramework, FrameworkVersion.framework_id == QualityFramework.id)
        .where(FrameworkVersion.status == VersionStatus.ACTIVE)
        .where(
            (QualityFramework.institution_id == institution_id)
            | (QualityFramework.institution_id.is_(None))
        )
        .options(
            selectinload(FrameworkVersion.applicability_rules),
            selectinload(FrameworkVersion.framework),
        )
    )
    result = await db.execute(stmt)
    all_versions: list[FrameworkVersion] = list(result.scalars().all())

    applicable: list[FrameworkVersion] = []
    exclusions: list[tuple[FrameworkVersion, str]] = []
    matched_rules: list[ApplicabilityRule] = []

    for version in all_versions:
        # Check effective dates on the version itself
        if version.effective_from and version.effective_from > today:
            continue
        if version.effective_to and version.effective_to < today:
            continue

        # Filter to rules for this target entity type (or ANY)
        rules = [
            r for r in version.applicability_rules
            if r.target_entity_type in (
                target_entity_type.value,
                ApplicabilityTargetType.ANY.value,
            )
        ]

        if not rules:
            # No rules configured → framework applies universally
            applicable.append(version)
            continue

        inclusion_rules = [r for r in rules if r.is_inclusion_rule]
        exclusion_rules = [r for r in rules if r.is_exclusion_rule]

        # Check exclusions first (higher priority)
        excluded = False
        for rule in sorted(exclusion_rules, key=lambda r: r.priority):
            if evaluate_rule(rule, entity_attrs, today):
                exclusions.append((version, rule.rule_name))
                excluded = True
                break

        if excluded:
            continue

        # Check inclusions — at least one must match
        if inclusion_rules:
            included = False
            for rule in sorted(inclusion_rules, key=lambda r: r.priority):
                if evaluate_rule(rule, entity_attrs, today):
                    matched_rules.append(rule)
                    included = True
                    break
            if included:
                applicable.append(version)
        else:
            # No inclusion rules → included by default (exclusion-only framework)
            applicable.append(version)

    return ApplicabilityResolution(
        applicable_framework_versions=applicable,
        exclusions=exclusions,
        matched_rules=matched_rules,
    )
