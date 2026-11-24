---
name: pmp-replay-transcript-extraction
description: Repeatable workflow for extracting authenticated Zoom PMP replay transcripts into complete, LLM-ready Markdown, RAG chunks, and Susan Daniels exam-callout notes. Use when processing PMP replay links from the workbook or a supplied replay URL.
---

# PMP replay transcript extraction

## Goal

Turn each requested PMP Zoom replay into auditable learning artifacts: a complete transcript in spoken order, retrieval-friendly chunks, and a separate list of Susan Daniels' explicit exam/key-slide callouts. Preserve source IDs and URLs so omissions can be detected; never invent words, timestamps, credentials, or exam claims.

## Done means

- [ ] Identify the exact workbook/tab/link (or use the supplied URL) and record session/date metadata.
- [ ] Reach the actual replay page. If Zoom asks for registration, passcode, or login, pause for the user and resume without guessing credentials.
- [ ] Capture every rendered transcript row, including source row ID, speaker, text, and timestamp when present. Save checkpoints frequently.
- [ ] Confirm the end of the transcript and verify IDs are contiguous from 0 through the final ID; investigate every gap or duplicate before proceeding.
- [ ] Write `November YYYY Session N transcript.md` with source URL, capture metadata, complete rows, and an explicit completeness verdict.
- [ ] Write `November YYYY Session N - RAG chunks.md` with stable chunk IDs, contiguous source-ID ranges, roughly 350–650 words per chunk, and enough overlap for retrieval.
- [ ] Write `November YYYY Session N - Exam callouts.md`, preserving Susan's explicit “exam”, “know”, “key slide/topic”, or equivalent callouts verbatim or as faithful excerpts with source IDs; label interpretation separately.
- [ ] Update the handoff/index with files, verification results, and any unresolved limitation.

## Before you start

Work in the PMP content workspace. Inspect the workbook's latest tab first; do not assume sheet order. For a browser replay, keep the authenticated replay tab open and use the browser's transcript panel rather than attempting to download media. The transcript list is virtualized: scroll in short batches, wait for rows to render, and append only newly seen IDs. Keep a JSON checkpoint outside the final Markdown so a browser interruption can resume safely.

If authentication or a one-time passcode is required, tell the user exactly what page/action is needed and wait. Never store passwords or passcodes in the repository.

## Steps

1. **Resolve the source.** Locate the exact `.xlsx` file and inspect the latest tab. Record session number, class date, replay URL, and workbook cell/sheet. If the user supplies a replay URL, still record it as the canonical source.
2. **Open and authenticate.** Navigate to the replay URL, complete only actions already authorized by the user, and wait until the Zoom recording itself (not a generic Zoom landing page) is visible. Do not close the tab while waiting for user input.
3. **Initialize capture.** Create `/private/tmp/pmp-sessionN-capture.json` (or the workspace's established capture path) with `entries`, `seenIds`, `lastId`, `terminalEndObserved`, source metadata, and a capture timestamp. Use the page's rendered transcript rows and retain the row's numeric ID when available.
4. **Capture incrementally.** Read visible rows, normalize whitespace without changing wording, and append only unseen IDs. Scroll a small amount, wait for rendering, then repeat. After each batch persist the checkpoint. If the page reconnects or jumps, re-read the last few IDs and deduplicate rather than clearing prior data.
5. **Capture callouts.** While reviewing rows, flag explicit Susan Daniels exam/key-slide language (for example “this is on the exam”, “know this”, “key slide”, or a clearly marked exam topic). Store the exact row IDs and text; distinguish her explicit callout from your own teaching summary.
6. **Verify completeness.** Do not accept “video reached the end” alone. Require both a terminal end observation and `sorted(ids) == range(0, max_id + 1)` (or an equivalent source-provided contiguous range). Report and repair missing IDs, duplicates, or an early-stop/reconnect condition.
7. **Generate artifacts.** Use the workspace's session builder or a small deterministic script to generate the transcript, RAG chunks, and callouts. Keep source-ID references in every artifact; never add guessed timestamps. Include a front-matter completeness verdict and the canonical replay URL.
8. **Quality check.** Re-open the generated files, compare entry and callout counts with the capture JSON, search for placeholder text, and run the contiguous-ID check again. If any check fails, fix the source or regenerate before reporting success.
9. **Handoff.** Update `AGENT_HANDOFF.md` (or the project index) with the session status, exact filenames, capture path, verification command, and the next unfinished session. Leave authenticated browser state open if another session is queued.

## Decisions (and why)

- Prefer rendered transcript rows over audio transcription — it preserves Zoom's speaker segmentation and avoids inventing words.
- Checkpoint outside the final Markdown — browser tabs can reload or virtualized rows can disappear.
- Treat explicit Susan callouts as a separate artifact — exam emphasis must remain distinguishable from generated study advice.
- Keep a gap report even when extraction is partial — a partial transcript must never be presented as complete.

## Don't

- Don't use a generic Zoom page as evidence that the replay opened.
- Don't guess a passcode, bypass registration, or automate around a login wall.
- Don't claim completeness from word count, video duration, or the last visible row.
- Don't silently fill missing IDs, paraphrase explicit exam callouts as quotations, or manufacture timestamps.
- Don't commit raw authenticated session logs, cookies, passcodes, or private distillation runs.

## Verify before you say you're done

Run the project-specific verifier (or an equivalent check) in this order:

```bash
python -m json.tool /private/tmp/pmp-sessionN-capture.json >/dev/null
PMP_SESSION=N python - <<'PY'
import json, os
n = os.environ['PMP_SESSION']
p = f'/private/tmp/pmp-session{n}-capture.json'
d = json.load(open(p))
ids = sorted(int(x['id']) for x in d['entries'])
assert ids == list(range(ids[-1] + 1)), 'missing or duplicate transcript IDs'
assert d.get('terminalEndObserved') is True, 'terminal end not observed'
print(f'verified {len(ids)} transcript rows')
PY
```

Then report the replay URL, files created, row/callout counts, contiguous-ID result, and any limitation. Explain that this skill is reusable by invoking it whenever the user asks to process another PMP replay link.
