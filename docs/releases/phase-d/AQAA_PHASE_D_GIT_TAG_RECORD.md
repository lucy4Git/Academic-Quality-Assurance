# AQAA Phase D — Git Tag Record

**Date:** 2026-07-17
**Tag:** `v0.9.0-phase-d`
**Type:** Annotated tag

---

## Commit Chain

| Role | Hash | Message |
|------|------|---------|
| Core release implementation | `c1cec9c04f1a30d2a88eb16ad8d0db213f7c93b2` | `release: preserve AQAA Phase D AI-native operating system baseline` |
| Release metadata completion | `389e1e2` | `docs: add git tag record for v0.9.0-phase-d` |

The tag `v0.9.0-phase-d` is the authoritative pointer to the final preserved release commit.
The tag message and the tag object itself are the source of truth for what is included.

---

## Tag Details

| Field | Value |
|-------|-------|
| Tag name | `v0.9.0-phase-d` |
| Tag type | Annotated |
| Core release commit | `c1cec9c04f1a30d2a88eb16ad8d0db213f7c93b2` |
| Final preserved release commit | `389e1e2` (integrity correction — see below) |
| Tag target | Final preserved release commit |
| Tagger | AQAA Engineering |
| Date | 2026-07-17 |
| Branch | `recovery/semantic-grounding-and-audit-centre` |

---

## Tag Message

```
AQAA Phase D completion baseline.

Includes:
- AI-native universal workspace
- conversation persistence
- contextual orchestration
- semantic attachment grounding
- findings lifecycle integration
- regulatory framework engine integration
- multi-tenant security controls
- complete Phase D preservation documentation
- Phase D regression baseline
```

---

## Commit Summaries

**Core release commit (`c1cec9c`):**
`release: preserve AQAA Phase D AI-native operating system baseline`
— 62 files, 7,120 insertions, 41 deletions

**Release metadata completion commit (`389e1e2`):**
`docs: add git tag record for v0.9.0-phase-d`
— 1 file, 104 insertions

**Integrity correction commit:**
`chore: release-integrity — retag v0.9.0-phase-d to final preservation commit`
— Updates metadata files; moves tag to final preserved state; fixes schema_inventory BOM

---

## Verification

```bash
# Resolve tag to commit
git rev-list -n 1 v0.9.0-phase-d
# → final preserved release commit hash

# Show tag details
git show v0.9.0-phase-d --format="%H %d %s" --no-patch

# List all tags
git tag --list
# → v0.9.0-phase-d (and prior tags)
```

---

## Checkout Instructions

To restore or inspect the Phase D baseline:

```bash
# Check out Phase D baseline (detached HEAD)
git checkout v0.9.0-phase-d

# Create a branch from the Phase D tag
git checkout -b phase-d-hotfix v0.9.0-phase-d

# Return to development branch
git checkout recovery/semantic-grounding-and-audit-centre
```

---

## Push Instructions (when authorised)

```bash
# Push tag to remote
git push origin v0.9.0-phase-d

# Push tag + branch together
git push origin recovery/semantic-grounding-and-audit-centre v0.9.0-phase-d
```

**Note:** Tag was NOT pushed during Phase D preservation. Push requires an authorised remote and explicit instruction.

---

## Prior Tags

| Tag | Purpose |
|-----|---------|
| `v1.0.0-rc4` | Previous release candidate (Phase C or earlier) |
| `v0.9.0-phase-d` | **Phase D baseline** (this tag) |
