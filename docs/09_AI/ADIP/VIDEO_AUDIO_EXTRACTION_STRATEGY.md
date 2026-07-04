# ADIP — Video and Audio Extraction Strategy

**Document ID:** ADIP-AV-001  
**Version:** 1.0.0  
**Status:** Architecture Design  
**Last Updated:** 2026-06-29

---

## 1. Context

Video and audio documents appear in AQAA's QA evidence context:
- Recorded lectures (evidence of teaching activity)
- Video-recorded assessments (oral examinations, practical demonstrations)
- Audio-recorded moderation meetings
- Recorded industry placement/WIL visits
- Video evidence of laboratory sessions (attendance and practical evidence)

These are not common in the initial TUT pilot but are planned for Phase 7+ as AQAA expands to support richer evidence types.

---

## 2. Audio Extraction Strategy

### 2.1 Transcription Engine

**Primary engine:** OpenAI Whisper  
**Model:** `whisper-base` (pilot) → `whisper-medium` (production)  
**Install:** `pip install openai-whisper`  
**Note:** Requires `ffmpeg` for audio format conversion

**Why Whisper:**
- Open source, runs locally — no external API dependency
- Supports South African English, Afrikaans, Zulu, Sotho
- Produces word-level timestamps
- Available in multiple sizes (base: fast, medium: balanced, large: accurate)

### 2.2 Audio Processing Pipeline

```
Audio file (MP3/WAV/AAC/FLAC/OGG)
    │
    ▼ ffmpeg → convert to WAV 16kHz mono (Whisper requirement)
    │
    ▼ Silence detection → split long recordings at natural pause points
    │   (prevents token limit issues; max segment: 30 seconds)
    │
    ▼ Whisper transcription per segment
    │   Output: {text: "...", start: 12.5, end: 18.3, confidence: 0.87}
    │
    ▼ Concatenate segments → full transcript with timestamps
    │
    ▼ Speaker diarisation (planned) → identify speaker turns
    │
    ▼ DocumentChunk per sentence with:
        chunk_type: "transcript_segment"
        timestamp_seconds: 12.5
        transcript_word_count: 45
        ocr_confidence: 0.87 (Whisper confidence)
```

### 2.3 Output Model

```json
{
  "chunk_type": "transcript_segment",
  "text": "The assessment brief must be submitted to the moderation committee at least two weeks before the assessment date.",
  "timestamp_seconds": 145.3,
  "speaker_label": "speaker_0",
  "ocr_confidence": 0.91,
  "page_number": null,
  "document_id": "UUID",
  "source_file": "moderation_meeting_2026_03_15.mp3"
}
```

---

## 3. Video Extraction Strategy

### 3.1 Audio Track Extraction

Video documents are processed by extracting the audio track first:

```
Video file (MP4/MOV/AVI/MKV)
    │
    ▼ ffmpeg → extract audio track as WAV 16kHz mono
    │
    ▼ Whisper transcription (same as audio pipeline above)
    │
    ▼ Optional: keyframe extraction for visual content analysis
```

### 3.2 Visual Content (Future — Phase 7)

For videos containing visual content relevant to QA (e.g., practical demonstration videos):

| Future Capability | Technology | Phase |
|------------------|-----------|-------|
| Keyframe extraction | ffmpeg `-vf select='gt(scene,0.4)'` | Phase 7 |
| Slide detection | Scene change detection | Phase 7 |
| Text on screen (OCR) | Frame → EasyOCR | Phase 7 |
| Visual content description | Vision-language model (LLaVA) | Phase 8 |

### 3.3 Lecture Recording Handling

For recorded lectures submitted as QA evidence:

**Relevant metadata to extract:**
- Duration (teaching contact time evidence)
- Date (from filename/metadata — supports attendance evidence)
- Speaker identification (lecturer identified)

**Not extracted in pilot:**
- Content accuracy (is what the lecturer said correct?)
- Student engagement metrics
- Screen-share content from LMS recordings

---

## 4. Confidence and Limitations

| Scenario | Whisper Performance | Confidence |
|---------|---------------------|-----------|
| Clear speech, quiet background, native English | Excellent | 0.88–0.95 |
| South African English (standard) | Good | 0.82–0.90 |
| Afrikaans speech | Good | 0.80–0.88 |
| Accented English (strong regional accent) | Moderate | 0.70–0.82 |
| Multiple overlapping speakers | Poor | 0.50–0.70 |
| Heavy background noise | Poor | 0.40–0.65 |
| Technical jargon (module codes, NQF terms) | Moderate | 0.70–0.82 |

**All audio/video transcripts undergo confidence-gated routing:**
- Average transcript confidence ≥ 0.80 → include in full-text and vector index
- Average transcript confidence 0.65–0.79 → include with `pending_review` flag
- Average transcript confidence < 0.65 → quarantine; do not index; flag for human review

---

## 5. Storage and Privacy

**Storage:** Transcripts stored in ADIP chunk index (PostgreSQL + Qdrant)  
**Source files:** Stored immutably at `adip/{institution_id}/{year}/{uuid}.mp4`  
**Privacy note:** Audio/video recordings may contain student voices or personal information  

**POPIA compliance for video/audio:**
- Student recordings (oral exams): institution confirms consent before ADIP ingestion
- Moderation meetings: stored as institutional records, not searchable without authorisation
- Access control: ADIP audio/video records restricted to QA Officer+ role

---

## 6. Priority Roadmap

| Priority | Capability | Phase |
|---------|-----------|-------|
| 🔴 DEPRIORITISED | Audio/video extraction | Phase 7 (after PDF fully working) |
| 🟡 Architecture only | Transcript model designed | Phase 5.4F (this document) |
| 🟢 Immediate focus | PDF, DOCX, HTML, XLSX | Phase 5.4G (next) |

**Note:** Video and audio extraction is architecturally designed here but **not implemented in Phase 5.4G**. The infrastructure (Whisper, ffmpeg) is noted for future installation. All Phase 5.4G implementation effort targets PDF, DOCX, HTML, and XLSX for the TUT pilot.
