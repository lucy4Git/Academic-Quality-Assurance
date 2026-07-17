# AQAA Phase D — Runtime Flow Map

**Date:** 2026-07-17

---

## 1. Natural-Language Request Flow

```mermaid
sequenceDiagram
    participant Browser
    participant Proxy as Next.js Proxy
    participant Backend as FastAPI
    participant Planner as Request Planner
    participant Context as Context Engine
    participant RAG as Advanced RAG
    participant LLM as LLM Provider

    Browser->>Proxy: POST /api/proxy/ai-assistant/ask-stream
    Proxy->>Backend: POST /api/v1/ai-assistant/ask-stream (Bearer token)
    Backend->>Planner: detect_intent(query)
    Planner-->>Backend: intent, requires_confirmation
    Backend->>Context: resolve(query, session)
    Context-->>Backend: module_id, programme_id
    Backend->>Browser: SSE: context event
    Backend->>RAG: advanced_ask(query, institution_id, injected_chunks)
    RAG->>Qdrant: vector search (institution-filtered)
    Qdrant-->>RAG: ranked chunks
    RAG->>LLM: prompt + chunks
    LLM-->>RAG: stream tokens
    RAG-->>Backend: stream
    Backend->>Browser: SSE: token events
    Backend->>Browser: SSE: sources event
    Backend->>Backend: persist message + structured_blocks + citations
    Backend->>Browser: SSE: done event
```

---

## 2. Context-Resolution Flow

```mermaid
flowchart TD
    Q[User query] --> CE[Context Engine]
    CE --> Hint{hint in request?}
    Hint -- yes --> UseHint[use hint module_id]
    Hint -- no --> TextScan[scan query for module codes]
    TextScan --> Found{found?}
    Found -- yes --> UseFound[resolve module from DB]
    Found -- no --> Session[use last session context]
    Session --> Fallback{session has module?}
    Fallback -- yes --> UseSession[use session module_id]
    Fallback -- no --> NoCtx[module_id = null]
    UseHint & UseFound & UseSession & NoCtx --> Emit[emit SSE context event]
```

---

## 3. Attachment-Grounding Flow

```mermaid
flowchart TD
    Req[POST ask-stream with attached_file_ids] --> Gate{module context set?}
    Gate -- no --> Err[toast: Select a module]
    Gate -- yes --> Loop[for each file_id]
    Loop --> Stage1[ATTACHMENT_REQUESTED]
    Stage1 --> DB[get_file_content from DB + storage]
    DB --> Stage2[ATTACHMENT_FOUND]
    Stage2 --> MIME[detect MIME type]
    MIME --> Stage3[ATTACHMENT_LOADED]
    Stage3 --> Parser{is_supported MIME?}
    Parser -- yes --> Extract[parser.extract → text]
    Parser -- no --> Decode[decode as UTF-8]
    Extract & Decode --> Stage4[ATTACHMENT_PARSED]
    Stage4 --> Chunk[build injected_chunk dict]
    Chunk --> Stage5[ATTACHMENT_USED]
    Stage5 --> Report[file_status.success = true]
    DB & Extract --> ErrPath[exception caught]
    ErrPath --> Stage6[ATTACHMENT_FAILED]
    Stage6 --> Log[log file_id, stage, exc_type]
    Report & Log --> Summary[build attachment_report]
    Summary --> Status{used_count?}
    Status -- 0 --> Failed[status = failed]
    Status -- partial --> Partial[status = partial]
    Status -- all --> Success[status = success]
    Failed & Partial & Success --> AttachSSE[emit attachment SSE event]
    AttachSSE --> RAG[advanced_ask with injected_chunks]
    RAG --> SkipQdrant[bypasses Qdrant vector search]
```

---

## 4. Module-Audit Flow

```mermaid
sequenceDiagram
    participant User
    participant API as FastAPI
    participant Agent as Audit Agent
    participant DB as PostgreSQL

    User->>API: POST /api/v1/audits/modules/{module_id}/trigger
    API->>DB: create AuditRun (status=pending)
    API-->>User: 202 Accepted {run_id}
    API->>Agent: background_task(run_id)
    Agent->>DB: update status=running
    Agent->>Agent: analyse module folder, evidence, moderation...
    Agent->>DB: insert AuditFinding records
    Agent->>DB: update status=completed
    User->>API: GET /api/v1/audits/{run_id}
    API-->>User: 200 {status:completed, findings:[...]}
```

---

## 5. Findings Lifecycle Flow

```mermaid
stateDiagram-v2
    [*] --> open: audit creates finding
    open --> acknowledged: LECTURER acknowledges
    acknowledged --> in_progress: LECTURER starts work
    in_progress --> submitted: LECTURER submits
    submitted --> approved: QA_OFFICER approves
    submitted --> rejected: QA_OFFICER rejects
    rejected --> in_progress: LECTURER resubmits
    approved --> closed: QA_OFFICER closes
    closed --> reopened: QA_OFFICER reopens
    reopened --> in_progress: LECTURER restarts
```

---

## 6. Regulatory-Readiness Flow

```mermaid
flowchart LR
    Q[Query mentions regulation] --> RE[Regulatory Engine]
    RE --> FW[Load quality_frameworks]
    FW --> SS{source_status?}
    SS -- active --> Direct[cite directly]
    SS -- draft --> Caveat[cite with draft caveat]
    SS -- superseded --> Warn[cite with superseded warning]
    SS -- null --> Unknown[mark status unknown]
    Direct & Caveat & Warn & Unknown --> NoAuto{auto-equivalence?}
    NoAuto -- never --> Stream[stream response with citations]
```

---

## 7. Conversation-Persistence Flow

```mermaid
sequenceDiagram
    participant Backend
    participant DB as PostgreSQL

    Backend->>Backend: stream SSE to client
    Backend->>Backend: collect full_text, structured_blocks, citations
    Backend->>DB: INSERT ai_chat_messages (user message)
    Backend->>DB: INSERT ai_chat_messages (assistant message)
    Backend->>DB: store attached_file_ids JSONB
    Backend->>DB: store structured_blocks JSONB
    Backend->>DB: store citations JSONB
    Note over Backend,DB: all in single transaction after stream ends
```

---

## 8. Artifact-Generation Flow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant DB

    User->>API: POST /conversations/{id}/artifacts {title, type, content}
    API->>DB: INSERT ai_artifacts (status=saved, version=1)
    API-->>User: 201 {id, title, type, version_number:1, status:saved}
    User->>API: PATCH /artifacts/{id} {title: new name}
    API->>DB: UPDATE ai_artifacts SET title, version_number+1
    API-->>User: 200 {version_number:2}
    User->>API: POST /artifacts/{id}/archive
    API->>DB: UPDATE status=archived
    User->>API: GET /artifacts/{id}/export?format=json
    API-->>User: 200 application/json artifact payload
```

---

## 9. Citation-Generation Flow

```mermaid
flowchart TD
    Chunks[ranked_chunks from RAG] --> Map[map to source dicts]
    Map --> Fields[entity_type, entity_id, entity_key, title, text,\nsource_document, confidence_score,\nrelevance_score, institution_id]
    Fields --> SSE[emit sources SSE event]
    SSE --> Persist[store in ai_chat_messages.citations JSONB]
    Persist --> Restore[available on GET /sessions/{id}]
```

---

## 10. Tenant-Isolation Enforcement Flow

```mermaid
flowchart TD
    Req[Authenticated request] --> User[current_user from JWT]
    User --> IID[institution_id from user]
    IID --> Type{endpoint type}
    Type -- module/programme --> Filter[WHERE institution_id = user.institution_id]
    Filter --> Miss{found?}
    Miss -- no --> 404[404 Not Found]
    Miss -- yes --> Allow[proceed]
    Type -- session --> Owner[WHERE user_id = current_user.id]
    Owner --> Owned{owned?}
    Owned -- no --> 403[403 Forbidden]
    Owned -- yes --> Allow
    Type -- artifact --> Conv[load conversation, check owner]
    Conv --> Allow
    Allow --> Resp[200 response]
```
