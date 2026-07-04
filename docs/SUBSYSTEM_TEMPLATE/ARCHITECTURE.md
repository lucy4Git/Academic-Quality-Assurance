# [Subsystem Name] — Architecture

**Subsystem:** [e.g., Audit Engine, IKP Pipeline, Workflow Engine]  
**Document Type:** Architecture  
**Version:** 1.0.0  
**Status:** Draft | Active | Superseded  
**Last Updated:** YYYY-MM-DD  
**Owner:** Engineering

---

## Overview

[One paragraph describing what this subsystem does and why it exists.]

---

## Scope

### In Scope
- [What this subsystem handles]

### Out of Scope
- [What this subsystem explicitly does not handle]

---

## Architecture Diagram

```
[ASCII or text diagram showing the subsystem's components and how they connect]

Component A
    │
    ▼
Component B ──► Component C
    │
    ▼
Output
```

---

## Components

### Component A — [Name]
**Purpose:** [What it does]  
**File:** `backend/app/[path]`  
**Key classes/functions:**
- `ClassName.method()` — [description]

### Component B — [Name]
[Same structure]

---

## Data Flow

1. [Step 1 — what happens first]
2. [Step 2]
3. [Step 3]
4. [Final output]

---

## Dependencies

| Dependency | Type | Why Required |
|-----------|------|-------------|
| [library/service] | Internal/External | [reason] |

---

## Integration Points

| System | Direction | Protocol | Description |
|--------|-----------|----------|-------------|
| [system] | In/Out/Bidirectional | HTTP/SQL/Event | [description] |

---

## Security Considerations

- [Access control requirements]
- [Data sensitivity]
- [Authentication needed]

---

## Performance Characteristics

| Metric | Expected | Max Acceptable |
|--------|---------|---------------|
| [metric] | [expected] | [max] |

---

## Known Limitations

- [Limitation 1]
- [Limitation 2]

---

## Future Improvements

- [Planned enhancement]

---

## Related Documents

- [Link to Implementation Guide]
- [Link to API docs]
- [Link to ADR]
