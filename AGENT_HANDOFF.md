# PMP Content Handoff

## Current state

- Sessions 1–3 have been captured from Zoom's rendered automatic transcript and converted to Markdown.
- Each completed session has a full transcript, RAG chunks, and exam-callout/Susanism artifact.
- Transcript source-entry IDs are retained for provenance and retrieval.
- Session 3 was verified with source entries `0–2151` present contiguously with no gaps.

## Completed artifacts

- `November 2026 Session 1 transcript.md`
- `November 2026 Session 1 - RAG chunks.md`
- `November 2026 Session 1 - Exam callouts.md`
- `November 2026 Session 2 transcript.md`
- `November 2026 Session 2 - RAG chunks.md`
- `November 2026 Session 2 - Exam callouts.md`
- `November 2026 Session 3 transcript.md`
- `November 2026 Session 3 - RAG chunks.md`
- `November 2026 Session 3 - Exam callouts.md`

## Reproduction scripts

- `build_session2_artifacts.mjs`
- `build_session3_artifacts.mjs`

Both scripts read a capture JSON file from `/private/tmp` and write the corresponding Markdown artifacts. The Session 3 capture checkpoint is currently `/private/tmp/pmp-session3-capture.json` and is not committed because it is outside the repository.

## Next task

Continue with Session 4 using the Zoom replay URL supplied by the user:

`https://skillsoftbootcamp.zoom.us/rec/share/2dxi39e34LApXKKmOnx8X2FRe3g4-85s1RhtTgsXEwlpH_dQyRkK1TOuhfl5F1Fm.-LlIx6RtpemPzL_0`

The replay date is Nov 19, 2026 and duration is approximately 5h47m. Registration has been completed in the browser; a passcode may still be requested. Capture the virtualized `.transcript-list-item[data-active="true"]` entries into `/private/tmp/pmp-session4-capture.json`, verify source-index continuity, then create:

- `November 2026 Session 4 transcript.md`
- `November 2026 Session 4 - RAG chunks.md`
- `November 2026 Session 4 - Exam callouts.md`

Use short checkpointed scroll batches and save after every batch to avoid losing progress when the Zoom renderer becomes unstable.
