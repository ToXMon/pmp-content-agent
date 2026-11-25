# PMP semantic layer

This layer lets a PMP Partner find a topic before opening the course evidence. The retrieval path is **source transcript → existing RAG chunks → semantic topic and index → Copilot retrieval**. The topic notes are original summaries of Sessions 1–5. They neither replace the existing files nor constitute official PMI guidance.

## Use it locally

Run from the repository root with Python 3.10+; no dependencies, API keys or service calls are needed.

```sh
python3 semantic-layer/scripts/query_semantic_index.py 'Should I overlap activities or add resources to shorten the finish date?'
python3 semantic-layer/scripts/query_semantic_index.py 'What does a CPI below one mean?' --limit 3 --json
python3 semantic-layer/scripts/build_semantic_layer.py
python3 semantic-layer/scripts/validate_semantic_layer.py
```

Start with the [taxonomy](topic-taxonomy.yaml) or the [JSON index](semantic-index.json). The [CSV](semantic-index.csv) has one row per topic and stores list/object cells as JSON. The YAML files use JSON syntax, a YAML 1.2 subset, to keep the build dependency-free. `topic_search_aliases` contains retrieval terms; `aliases` contains canonical expansions; `related_not_synonyms` keeps distinct concepts such as EV and PV separate.

## Use it as a Copilot knowledge layer

In an approved knowledge location, keep the topic Markdown, index and original sources accessible under the same permissions. Use the topic ID, title, aliases and project context to retrieve candidates. Follow the `sources` objects in the JSON to open the original transcript or RAG excerpt before citing an answer. The same chunk label can occur in multiple sessions; use the provided session and filename to disambiguate it. The local query tool is a lexical baseline for testing the metadata, not a live Copilot integration. Workbook, slide visuals and recording timestamps are not inferred. Follow the repository's existing public/private boundary; do not publish recordings or transcripts to a public location.

For practitioner answers, use the scenario and delivery approach. For exam coaching, distinguish instructor study cues from PMI rules and use the current official PMI outline or Code for official requirements. Keep the capture gaps in the answer when the evidence depends on a partial session. Session 1 uses exact transcript lines plus chunk-level source bounds; only Sessions 2 onward have inline entry headings.

## Add or extend coverage

1. Add the next session's original `… Session N transcript.md` and `… Session N - RAG chunks.md` at the repository root. Include the exam callout file if there is one. Preserve the original ID and gap conventions. The parser accepts the existing numbered transcript and RAG heading styles; adapt `scripts/sources.py` if the source format changes.
2. Read the new material. In `catalog/`, append verified transcript line windows to existing topics when the new session supports them, or add a new topic with a unique ID. Catalog rows follow `FIELDS` in the builder; pipe-delimited columns represent lists and each final window is `[session, first line, last line]`, inclusive. Keep topic IDs unchanged once published. If intentionally retiring a topic, remove its generated page and update links and tests.
3. Add realistic tests to `catalog/retrieval-tests.json` as `[query, primary ID, [acceptable secondary IDs], session, expected transcript line]`. The ranker does not index the fixtures or the example retrieval questions.
4. Run the builder with `--register-new` once to append new source hashes and rebuild. This flag will refuse changes to any already pinned source. Review actual source corrections and affected line windows before updating the manifest deliberately; it is not a bypass flag. Normal catalog edits only need a regular build. Rebuilds write only changed files under `semantic-layer/`; the wider source inventory is rechecked each time.
5. Run validation and read the [coverage](reports/coverage-report.md), [provenance](reports/provenance-report.md) and [retrieval](reports/retrieval-test-report.md) reports. Unmapped entries include both non-topical material and passages still available for future curation. Mapping a chunk does not mean every passage in it is summarized.

The [source manifest](source-manifest.json) pins bytes for the canonical transcripts, RAG chunks, callout files and superseded checkpoints. The validator checks that generated Markdown, taxonomy, aliases, index exports and reports match the curated catalog and source inventory. It can detect fabricated or stale locators and missing gap notices; reviewers still need to judge whether the source supports the summary.
