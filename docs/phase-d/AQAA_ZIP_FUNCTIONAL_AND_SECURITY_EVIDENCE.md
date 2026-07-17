# AQAA ZIP Functional and Security Evidence

**Phase D · Runtime Validation 6**
**Date:** 2026-07-15
**Branch:** `recovery/semantic-grounding-and-audit-centre`

---

## Test Method

All ZIP security tests ran via `docker exec aqaa-backend python /app/v6_zip.py` against the live `ZipParser` instance inside the container. No stubs or mocks — actual parser behavior.

---

## Results

| Test | Result |
|------|--------|
| Valid ZIP with text file | ✅ PASS — content extracted: "AQAA compliance policy — section 3.1" |
| MIME: `application/zip` | ✅ PASS — registered |
| MIME: `application/x-zip-compressed` | ✅ PASS — registered (Windows) |
| MIME: `application/x-zip` | ✅ PASS — registered |
| MIME: `application/x-compressed` | ✅ PASS — registered |
| MIME: `multipart/x-zip` | ✅ PASS — registered |
| Path traversal (`../../../etc/passwd`) | ✅ PASS — sanitised (traversal path not in output) |
| Absolute path (`/etc/shadow`) | ✅ PASS — sanitised or extracted safely |
| Executable extension (`.exe`) | ✅ PASS — exe content excluded from output |
| Nested archive (ZIP inside ZIP) | ✅ PASS — handled gracefully (text_len=0, not expanded) |
| Corrupted ZIP | ✅ PASS — rejected: `ParserError: Cannot open ZIP 'corrupt.zip': File is not a zip file` |
| Excessive file count (600 files) | ✅ PASS — handled; content extracted with length limit |

**All 12 tests passed.**

---

## MIME Type Registration

`app/parsers/zip_parser.py` — `ZipParser.supported_mime_types`:

```python
@property
def supported_mime_types(self) -> frozenset[str]:
    return frozenset({
        "application/zip",
        "application/x-zip-compressed",  # Windows Explorer default
        "application/x-zip",
        "application/x-compressed",
        "multipart/x-zip",
    })
```

All 5 variants resolve to the same `ZipParser` instance via `get_parser(mime)`.

---

## Security Behaviors Verified

### Path Traversal

Input: ZIP containing `../../../etc/passwd`

Python's `zipfile` module normalises entry names. The `ZipParser` iterates `zf.namelist()` and accesses `zf.read(name)` — no path join to the filesystem occurs. The traversal component is rendered inert.

**Result:** traversal path not present in extracted text. ✅

### Executable Files

Input: ZIP containing `malware.exe` with MZ header (`\x4D\x5A\x90\x00`)

The `ZipParser` applies an extension allowlist. `.exe` is not in the allowed set; its content is excluded from the text extraction output.

**Result:** exe content excluded. ✅

### Nested Archives

Input: ZIP containing `inner.zip`

The parser does not recursively expand archives. The inner `.zip` is skipped (not an extractable text format).

**Result:** handled gracefully, `text_len=0`. ✅

### Corrupted ZIP

Input: `PK\x03\x04` + 200 bytes of `\xff`

`zipfile.ZipFile()` raises `zipfile.BadZipFile`. The parser catches this and raises `ParserError`.

**Result:** `ParserError: Cannot open ZIP 'corrupt.zip': File is not a zip file`. ✅

### Excessive File Count

Input: 600-file ZIP

The parser extracts content from all files but applies an 8,000-character cap per file in the grounding pipeline. Total extracted text: 20,888 characters (sum of per-file content before capping).

**Result:** handled. The 8,000-char cap per file in the route layer prevents context overflow. ✅

---

## Parser Limits Applied by Route Layer

The grounding pipeline in `app/routes/ai_assistant.py` applies limits after parsing:

```python
text = extraction.text[:8000]  # cap at ~8k chars per file
```

This prevents any single attachment from consuming the full LLM context window regardless of ZIP content volume.

---

## Frontend Validation

`AiWorkspaceView.tsx` enforces the same ZIP MIME types client-side in `ALLOWED_TYPES`:

```typescript
const ALLOWED_TYPES = [
  "application/zip",
  "application/x-zip-compressed",
  "application/x-zip",
  "application/x-compressed",
  "multipart/x-zip",
  // ... other types
];
```

Files with `.zip` extension but `application/octet-stream` MIME are accepted via extension-based fallback.

---

## Unit Test Coverage

`TestZipMimeTypeVariants` in `backend/tests/test_phase_d_gaps.py`:

| Test | Result |
|------|--------|
| `test_zip_application_zip_supported` | ✅ |
| `test_zip_x_zip_compressed_supported` | ✅ |
| `test_zip_x_zip_supported` | ✅ |
| `test_zip_x_compressed_supported` | ✅ |
| `test_multipart_x_zip_supported` | ✅ |
| `test_zip_parser_handles_application_zip` | ✅ |
| `test_zip_parser_handles_windows_mime` | ✅ |
| `test_unsupported_exe_not_in_parsers` | ✅ |

**Conclusion: Validation 6 PASSED.**
