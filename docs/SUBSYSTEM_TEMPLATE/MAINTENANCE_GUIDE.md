# [Subsystem Name] — Maintenance Guide

**Subsystem:** [Name]  
**Document Type:** Maintenance Guide  
**Version:** 1.0.0  
**Last Updated:** YYYY-MM-DD

---

## Routine Maintenance Tasks

| Task | Frequency | Procedure |
|------|-----------|-----------|
| [Task] | Daily/Weekly/Monthly | [Steps] |

---

## Monitoring Indicators

| Indicator | Expected Value | Alert Threshold | Action If Breached |
|-----------|---------------|-----------------|-------------------|
| [metric] | [normal] | [threshold] | [action] |

---

## Common Operational Problems

### Problem 1 — [Symptom]
**Symptoms:** [What you observe]  
**Cause:** [Why it happens]  
**Resolution:**
```bash
# Commands to resolve
```

### Problem 2 — [Symptom]
[Same structure]

---

## Backup and Recovery

[Describe backup requirements and recovery procedures specific to this subsystem]

---

## Upgrade Procedure

When upgrading dependencies or the subsystem itself:

1. [ ] Read the changelog for the dependency being upgraded
2. [ ] Run tests: `python -m pytest -q`
3. [ ] Check for deprecation warnings
4. [ ] Update this document if behaviour changes
5. [ ] Update `CHANGELOG.md`

---

## Deprecation Plan

[If this subsystem will be replaced or deprecated, document the migration path here]

---

## Contacts

| Role | Responsibility | Contact |
|------|---------------|---------|
| Engineering Lead | Code changes | [contact] |
| QA Officer | Policy questions | [contact] |
