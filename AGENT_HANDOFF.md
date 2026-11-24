# PMP Content Handoff

## Current state

- Sessions 1–4 have been captured from Zoom's rendered automatic transcript and converted to Markdown.
- Session 1 has one known source gap: Zoom did not render source index `971`.
- Sessions 2 and 3 have gap-free source IDs `0–2188` and `0–2151`, respectively.
- Session 4 has 1,987 captured entries with source IDs `0–1988`; Zoom did not render indices `1444` and `1650` despite targeted rescans. The missing text is not inferred.
- Every captured session has a transcript, RAG chunks, and exam-callout/Susanism artifact; check each transcript's extraction status before treating it as gap-free.
- Transcript source-entry IDs are retained for provenance and retrieval.

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
- `November 2026 Session 4 transcript.md` (source indices `1444` and `1650` unavailable from Zoom)
- `November 2026 Session 4 - RAG chunks.md`
- `November 2026 Session 4 - Exam callouts.md`

## Reproduction scripts

- `build_session2_artifacts.mjs`
- `build_session3_artifacts.mjs`
- `build_session4_artifacts.mjs`

The scripts read capture JSON files from `/private/tmp` and write the corresponding Markdown artifacts. The Session 3 capture checkpoint is `/private/tmp/pmp-session3-capture.json`; the Session 4 checkpoint is `/private/tmp/pmp-session4-capture.json`. These capture files are outside the repository.

## Next task

Continue with Session 5 after obtaining its replay URL. The `Nov 2026 PMP5Day` sheet identifies the recording date as Nov 20, 2026 and has a passcode in `C7`, but the URL cell `D7` is blank. Once the URL is available, use short checkpointed batches and verify source-index continuity before generating the three Markdown artifacts.
