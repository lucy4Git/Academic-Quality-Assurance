# Citation-Verified AI — User Guide

## What Is Grounded AI?

AQAA's AI Workspace now shows where each factual claim comes from. Every answer is verified against the institutional knowledge base and marked with a **grounding status**.

## Grounding Status Badges

| Badge | Meaning |
|-------|---------|
| **Grounded** (green) | All factual claims are supported by cited sources |
| **Partially Grounded** (amber) | Some claims are cited, but others could not be verified |
| **No Source Found** (grey) | No institutional knowledge was found for this query |

## Reading Citations

Below the grounding badge, you will see a **Citations** section listing each source that was referenced in the answer:

- **SOURCE:N** — the numbered source used in the answer text
- **Title** — the name of the knowledge item (programme, module, or document)
- **Copy** button — copies the full citation reference to your clipboard
- **Search** link — opens Knowledge Search pre-filled with the source title

## Inline Source References

When a real AI provider is active (not LOCAL_DEV), the answer text itself contains inline references like:

> "The ICT programme requires 360 credits **[SOURCE:1]** and runs over three years **[SOURCE:2]**."

These numbers match the citations listed below the answer.

## What To Do With Partially Grounded Answers

1. Check the Sources panel on the right — the retrieved documents are listed there.
2. Use the **Search** link on any citation to find more related content.
3. If the answer covers a topic not in the knowledge base, contact your System Admin to extend the IKP indexing.

## Limitations

- Citation grounding is only available when the IKP knowledge base has been indexed for your institution.
- In LOCAL_DEV mode, answers use template assembly and citations may not be present.
- The citation verifier checks for `[SOURCE:N]` references in the answer text — claims supported only by context (without an explicit inline reference) are flagged as unsupported.
