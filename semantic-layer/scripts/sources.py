"""Read the existing Markdown formats without renumbering any source locator."""
from bisect import bisect_right
from hashlib import sha256
from pathlib import Path
import re

LAYER = Path(__file__).resolve().parents[1]
ROOT = LAYER.parent
CHUNK = re.compile(r"^## (.+?)\s*(?:— |\()source entries (\d+)[–-](\d+)\)?$")
ENTRY = re.compile(r"^### Source entry (\d+)$")
RAG_ENTRY = re.compile(r"^(?:### Source entry (\d+)|\*\*Source entry (\d+)\*\*)$")
TRANSCRIPT = re.compile(r"^(.+ Session (\d+)) transcript\.md$")
S1_CALLOUT = re.compile(r"Transcript lines? (\d+)(?:[–-](\d+))?\.")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def numbered(lines, pattern):
    return [(i, pattern.fullmatch(line)) for i, line in enumerate(lines)
            if pattern.fullmatch(line)]


def compact(lines):
    return [line.strip() for line in lines if line.strip()]


def runs(ids):
    result = []
    for n in sorted(set(ids)):
        if result and n == result[-1][1] + 1:
            result[-1][1] = n
        else:
            result.append([n, n])
    return result


def load_sources():
    sessions, hashes = {}, {}
    for path in sorted(ROOT.iterdir()):
        m = TRANSCRIPT.fullmatch(path.name)
        if not m:
            continue
        label, n = m[1], int(m[2])
        require(n not in sessions, f"Ambiguous session number: {n}")
        files = {key: ROOT / (label + suffix) for key, suffix in {
            "transcript": " transcript.md", "rag": " - RAG chunks.md",
            "callouts": " - Exam callouts.md", "checkpoint": " - partial transcript.md",
        }.items()}
        texts = {}
        for key, file in files.items():
            if key in {"callouts", "checkpoint"} and not file.exists():
                continue
            require(file.resolve().parent == ROOT, f"Source outside repository: {file}")
            raw = file.read_bytes()
            hashes[file.name] = sha256(raw).hexdigest()
            texts[key] = raw.decode("utf-8").splitlines()
        tr = texts["transcript"]
        rag = texts["rag"]
        body = tr.index("## Transcript") + 1
        chunks, anchors = {}, {}
        headings = numbered(rag, CHUNK)
        require(headings, f"No RAG headings: {label}")
        tr_entries = numbered(tr, ENTRY)
        inline = bool(tr_entries)
        positions = [i for i, _ in tr_entries]
        ids = [int(e[1]) for _, e in tr_entries]
        require(ids == sorted(set(ids)), f"Duplicate or unordered transcript IDs: {label}")
        rag_ids = set()
        flat_tr = [i for i in range(body, len(tr)) if tr[i].strip()
                   and not (n == 1 and tr[i] == "[Source transcript entry 971 was not rendered by Zoom.]")]
        cursor = 0
        for idx, (line, h) in enumerate(headings):
            name, start, end = h[1], int(h[2]), int(h[3])
            require(name not in chunks and start <= end, f"Invalid chunk: {label}/{name}")
            chunks[name] = (start, end)
            section = rag[line+1:headings[idx+1][0] if idx+1 < len(headings) else len(rag)]
            if inline:
                rows = numbered(section, RAG_ENTRY)
                row_ids = [int(e[1] or e[2]) for _, e in rows]
                require(row_ids == list(range(start, end+1)), f"Chunk entry mismatch: {label}/{name}")
                for j, (pos, _) in enumerate(rows):
                    entry = row_ids[j]
                    k = bisect_right(ids, entry) - 1
                    require(k >= 0 and ids[k] == entry, f"Unknown source entry: {label}/{entry}")
                    actual = section[pos+1:rows[j+1][0] if j+1 < len(rows) else len(section)]
                    original = tr[positions[k]+1:positions[k+1] if k+1 < len(positions) else len(tr)]
                    require(compact(actual) == compact(original), f"RAG text mismatch: {label}/{name}/{entry}")
                rag_ids.update(row_ids)
            else:
                require(n == 1, f"Unrecognized unnumbered transcript: {label}")
                marker = "[Source entry 971 was not rendered by Zoom.]"
                text = [line for line in compact(section) if line != marker]
                lines = flat_tr[cursor:cursor+len(text)]
                require(text and text == [tr[i].strip() for i in lines], f"Unaligned transcript text: {label}/{name}")
                anchors[name] = (lines[0]+1, lines[-1]+1)
                cursor += len(text)
        header = "\n".join(tr[:body])
        if inline:
            require(ids and rag_ids == set(ids), f"Transcript and RAG inventory differ: {label}")
            missing = sorted(set(range(ids[-1]+1)) - set(ids))
        else:
            require(cursor == len(flat_tr), f"Unaligned transcript tail: {label}")
            require("One source index (971) was not rendered" in header, "Review Session 1 capture convention")
            missing = [971]
            coverage = set()
            for lo, hi in chunks.values():
                coverage.update(range(lo, hi+1))
            require(coverage == set(range(max(coverage)+1)) - set(missing), "Unrecognized Session 1 chunk ranges")
            ids = sorted(coverage - set(missing))
        if missing and inline:
            m = re.search(r"did not render source (?:entries|entry|indices|index) ([0-9, ]+)", header)
            require(m and list(map(int, re.findall(r"\d+", m[1]))) == missing,
                    f"Undocumented transcript gaps: {label}")
        if not missing:
            require(re.search(r"complete|no gaps", header, re.I), f"Completeness not declared: {label}")
        callouts = []
        for i, line in enumerate(texts.get("callouts", []), 1):
            m = re.fullmatch(r"#{2,3} Source entry (\d+)", line)
            c = S1_CALLOUT.search(line) if n == 1 else None
            if m:
                entry = int(m[1])
                require(entry in ids, f"Invalid callout ID: {label}/{entry}")
                callouts.append({"file": files["callouts"].name, "file_line": i, "source_entry": entry})
            elif c:
                lo, hi = int(c[1]), int(c[2] or c[1])
                require(body < lo <= hi <= len(tr), f"Invalid callout line: {label}/{i}")
                callouts.append({"file": files["callouts"].name, "file_line": i, "transcript_lines": [lo, hi]})
        sessions[n] = dict(files={k: files[k].name for k in texts}, entries=set(ids),
                           missing=missing, chunks=chunks, anchors=anchors, callouts=callouts,
                           count=len(tr), body=body, positions=[i+1 for i in positions],
                           ordered_ids=[int(e[1]) for _, e in tr_entries],
                           status="partial" if missing else "complete")
    require(set(range(1, 6)) <= sessions.keys(), "Missing one or more original sessions")
    return sessions, hashes


def resolve(session, window, sources):
    """Return exact lines, file-qualified chunk refs, and supported entry ranges."""
    src = sources[session]
    lo, hi = window
    require(type(lo) is int and type(hi) is int and src["body"] < lo <= hi <= src["count"],
            f"Invalid transcript lines: S{session} {window}")
    positions = src["positions"]
    if positions:
        first, last = bisect_right(positions, lo)-1, bisect_right(positions, hi)-1
        require(first >= 0, f"Window precedes first entry: S{session} {window}")
        ids = set(src["ordered_ids"][first:last+1])
        chunks = [k for k, (a, b) in src["chunks"].items() if any(a <= i <= b for i in ids)]
        basis = "transcript-entry-headings"
    else:
        chunks = [k for k, (a, b) in src["anchors"].items() if a <= hi and b >= lo]
        ids = {i for k in chunks for i in range(src["chunks"][k][0], src["chunks"][k][1]+1)} & src["entries"]
        basis = "session-1-chunk-bounds; exact locator is transcript lines"
    require(chunks and ids, f"Unresolved source: S{session} {window}")
    refs = [c for c in src["callouts"]
            if (c["source_entry"] in ids if "source_entry" in c else
                c["transcript_lines"][0] <= hi and c["transcript_lines"][1] >= lo)]
    return {"session": session, "transcript_file": src["files"]["transcript"],
            "transcript_lines": window, "rag_file": src["files"]["rag"],
            "rag_chunk_ids": chunks, "source_entry_ranges": runs(ids), "entry_range_basis": basis,
            "callouts": refs, "source_completeness": src["status"], "missing_source_entries": src["missing"]}
