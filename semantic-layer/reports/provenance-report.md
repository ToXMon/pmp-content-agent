# Provenance report

Sources are Zoom automatic transcripts and existing derived RAG and callout files. Callout references indicate overlap with a cited passage; Sessions 3 and 4 include keyword-selected excerpts, which do not all make an exam claim. Treat instructor guidance as such. No timestamp or slide locator is inferred.

Session 1 has no inline source-entry headings. The builder matches every chunk's text against the transcript in order, excluding the explicit gap markers. Cite the transcript line window for precision; use the chunk IDs and entry bounds for RAG retrieval. In other sessions, the builder verifies RAG row IDs and row text against transcript headings.

Chunk IDs are stored verbatim and scoped by file and session. Overlapping chunks can legitimately point to the same entries. Source byte hashes are pinned in [source-manifest.json](../source-manifest.json). Topic source maps and the JSON index carry exact provenance.

| Session | Capture status | Missing source entries | Topics | Source files |
|---|---|---|---:|---|
| 1 | partial | 971 | 7 | [transcript](../../November%202026%20Session%201%20transcript.md), [rag](../../November%202026%20Session%201%20-%20RAG%20chunks.md), [callouts](../../November%202026%20Session%201%20-%20Exam%20callouts.md) |
| 2 | complete | None | 8 | [transcript](../../November%202026%20Session%202%20transcript.md), [rag](../../November%202026%20Session%202%20-%20RAG%20chunks.md), [callouts](../../November%202026%20Session%202%20-%20Exam%20callouts.md), [checkpoint](../../November%202026%20Session%202%20-%20partial%20transcript.md) |
| 3 | complete | None | 10 | [transcript](../../November%202026%20Session%203%20transcript.md), [rag](../../November%202026%20Session%203%20-%20RAG%20chunks.md), [callouts](../../November%202026%20Session%203%20-%20Exam%20callouts.md), [checkpoint](../../November%202026%20Session%203%20-%20partial%20transcript.md) |
| 4 | partial | 1444, 1650 | 14 | [transcript](../../November%202026%20Session%204%20transcript.md), [rag](../../November%202026%20Session%204%20-%20RAG%20chunks.md), [callouts](../../November%202026%20Session%204%20-%20Exam%20callouts.md) |
| 5 | partial | 87, 925, 1301 | 19 | [transcript](../../November%202026%20Session%205%20transcript.md), [rag](../../November%202026%20Session%205%20-%20RAG%20chunks.md), [callouts](../../November%202026%20Session%205%20-%20Exam%20callouts.md) |
