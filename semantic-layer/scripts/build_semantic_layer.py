"""Generate the semantic layer from reviewed catalog records and read-only sources."""
import argparse
import csv
import io
import json
import re
from urllib.parse import quote

from query_semantic_index import rank
from sources import LAYER, load_sources, require, resolve, runs

FIELDS = ("topic_id domain title concepts aliases project_stages development_approaches "
          "when guidance exam_reasoning approach_relevance artifacts distinction related_topics windows").split()
LIST_FIELDS = ("concepts aliases project_stages development_approaches artifacts related_topics").split()
STAGES = {"initiation", "planning", "delivery", "monitoring-and-control", "closure"}
APPROACHES = {"predictive", "adaptive", "hybrid"}
CATALOG = LAYER / "catalog"
LOCK = LAYER / "source-manifest.json"
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|FIXME|TK|lorem ipsum|placeholder)\b", re.I)
TERMS = {
    "WBS": ("work breakdown structure", "SCOPE-WBS", ["decomposition", "work package", "WBS dictionary"]),
    "RTM": ("requirements traceability matrix", "SCOPE-REQUIREMENTS", ["requirements elicitation"]),
    "CPM": ("critical path method", "SCHEDULE-CPM", ["float", "dependencies"]),
    "EVM": ("earned value management", "COST-EVM", ["EV", "PV", "AC", "CPI", "SPI", "EAC", "BAC", "CV", "SV"]),
    "EV": ("earned value", "COST-EVM", ["EVM", "PV", "AC"]),
    "PV": ("planned value", "COST-EVM", ["EVM", "EV"]),
    "AC": ("actual cost", "COST-EVM", ["EVM", "EV"]),
    "CPI": ("cost performance index", "COST-EVM", ["EVM", "CV"]),
    "SPI": ("schedule performance index", "COST-EVM", ["EVM", "SV"]),
    "EAC": ("estimate at completion", "COST-EVM", ["EVM", "BAC"]),
    "BAC": ("budget at completion", "COST-EVM", ["EAC", "cost baseline"]),
    "CV": ("cost variance", "COST-EVM", ["CPI"]),
    "SV": ("schedule variance", "COST-EVM", ["SPI"]),
    "CCB": ("change control board", "CHANGE-CONTROL", ["change request", "baseline change"]),
    "PMIS": ("project management information system", "ARTIFACT-PMIS", ["configuration management"]),
    "WIP": ("work in progress", "DELIVERY-CADENCE", ["Kanban", "throughput"]),
    "CFD": ("cumulative flow diagram", "MONITOR-FLOW", ["WIP", "throughput"]),
    "DoD": ("definition of done", "QUALITY-ACCEPTANCE", ["acceptance criteria"]),
    "ECO": ("exam content outline", "EXAM-REASONING", ["practice exams"]),
    "CBA": ("cost-benefit analysis", "FOUND-VALUE", ["NPV"]),
    "NPV": ("net present value", "FOUND-VALUE", ["CBA"]),
    "SEAM": ("stakeholder engagement assessment matrix", "STAKE-ENGAGEMENT", ["stakeholder register"]),
    "COQ": ("cost of quality", "QUALITY-MANAGE", ["prevention", "appraisal", "failure costs"]),
    "T&M": ("time and materials", "PROC-CONTRACTS", ["fixed-price contract", "cost-reimbursable contract"]),
    "PESTEL": ("PESTLE", "GOV-ENVIRONMENT", ["external business environment"]),
}


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def link(label, file, line=None, prefix="../../"):
    return f"[{label}]({prefix}{quote(file)}" + (f"#L{line})" if line else ")")


def window_label(window):
    lo, hi = window
    return str(lo) if lo == hi else f"{lo}–{hi}"


def topic_records(sessions):
    records = []
    for catalog in sorted(CATALOG.glob("*.json")):
        if catalog.name == "retrieval-tests.json":
            continue
        for row in read_json(catalog):
            require(isinstance(row, list) and len(row) == len(FIELDS), f"Invalid row in {catalog.name}")
            r = dict(zip(FIELDS, row))
            ident = r["topic_id"]
            require(isinstance(ident, str) and re.fullmatch(r"[A-Z]+(?:-[A-Z]+)+", ident), f"Invalid topic ID: {ident}")
            for key in set(FIELDS) - {"windows"}:
                require(isinstance(r[key], str) and r[key].strip() and not PLACEHOLDER.search(r[key]), f"{ident}: invalid {key}")
            require(re.fullmatch(r"[a-z]+(?:-[a-z]+)+", r["domain"]), f"{ident}: invalid domain")
            for key in LIST_FIELDS:
                vals = [v.strip() for v in r[key].split("|")]
                require(all(vals) and len(set(vals)) == len(vals), f"{ident}: invalid or duplicate {key}")
                r[key] = vals
            require(set(r["project_stages"]) <= STAGES, f"{ident}: invalid stage")
            require(set(r["development_approaches"]) <= APPROACHES, f"{ident}: invalid approach")
            windows = r.pop("windows")
            require(windows and len({tuple(w) for w in windows}) == len(windows), f"{ident}: empty or duplicate windows")
            r["sources"] = [resolve(n, [a, b], sessions) for n, a, b in windows]
            r["topic_file"] = f"topics/{ident.lower()}.md"
            r["topic"] = ident.lower()
            r["modes"] = ["practitioner", "exam-coach"]
            r["source_files"] = sorted({file for s in r["sources"] for file in
                                       [s["transcript_file"], s["rag_file"], *(c["file"] for c in s["callouts"])]})
            r["rag_chunks"] = [{"session": n, "file": file, "id": chunk} for n, file, chunk in
                              sorted({(s["session"], s["rag_file"], ch) for s in r["sources"] for ch in s["rag_chunk_ids"]})]
            r["source_entry_ranges"] = [{"session": s["session"], "ranges": s["source_entry_ranges"],
                                         "basis": s["entry_range_basis"]} for s in r["sources"]]
            focus = r["concepts"][0]
            qs = [f"What is {focus} and when would I use it?",
                  f"How can I apply {focus} on my project, and what should I do next?",
                  f"What should I record about {focus} in {r['artifacts'][0]}?",
                  f"How might PMP test my understanding of {focus}?"]
            if len(r["concepts"]) > 1:
                qs.append(f"How does {focus} relate to {r['concepts'][1]}?")
            if "adaptive" in r["development_approaches"]:
                qs.append(f"What does {focus} look like in agile work?")
            if "hybrid" in r["development_approaches"]:
                qs.append(f"How would I apply {focus} in a hybrid project?")
            r["retrieval_questions"] = qs
            records.append(r)
    ids = {r["topic_id"] for r in records}
    require(records and len(ids) == len(records), "Missing catalog or duplicate topic IDs")
    for r in records:
        require(set(r["related_topics"]) <= ids - {r["topic_id"]}, f"{r['topic_id']}: invalid related topic")
    return sorted(records, key=lambda r: r["topic_id"])


def topic_page(r):
    result = [f"# {r['title']}", "", f"Topic ID: `{r['topic_id']}`", ""]
    for heading, content in [
        ("Related concepts and aliases", ", ".join(r["concepts"]) + ".\n\nSearch aliases: " + ", ".join(r["aliases"]) + "."),
        ("When it matters", r["when"]), ("Practitioner guidance", r["guidance"]),
        ("PMP exam reasoning", r["exam_reasoning"]),
        ("Predictive, adaptive and hybrid relevance", r["approach_relevance"]),
        ("Related project artifacts", ", ".join(r["artifacts"]) + "."),
        ("Common mistakes and distinctions", r["distinction"]),
        ("Related semantic topics", ", ".join(f"[{t}]({t.lower()}.md)" for t in r["related_topics"])),
        ("Example retrieval questions", "\n".join(f"- {q}" for q in r["retrieval_questions"])),
    ]:
        result += [f"## {heading}", "", content, ""]
    result += ["## Source map", ""]
    for s in r["sources"]:
        lo, hi = s["transcript_lines"]
        tr = link(f"transcript lines {window_label((lo, hi))}", s["transcript_file"], lo)
        rag = link("RAG file", s["rag_file"])
        chunks = ", ".join(f"`{c}`" for c in s["rag_chunk_ids"])
        entries = ", ".join(window_label(w) for w in s["source_entry_ranges"])
        gaps = f"; missing IDs {', '.join(map(str, s['missing_source_entries']))}" if s["missing_source_entries"] else ""
        bounds = " (chunk bounds, not exact entry IDs for those lines)" if s["session"] == 1 else ""
        result.append(f"- Session {s['session']} ({s['source_completeness']}{gaps}): {tr}; {rag}: {chunks}; entries {entries}{bounds}.")
        for c in s["callouts"]:
            locator = f"entry {c['source_entry']}" if "source_entry" in c else f"transcript lines {window_label(c['transcript_lines'])}"
            result.append("  - " + link(f"Instructor callout, {locator}", c["file"], c["file_line"]))
    return "\n".join(result) + "\n"


def aliases(records):
    ids = {r["topic_id"] for r in records}
    for abbreviation, (_, topic, _) in TERMS.items():
        require(topic in ids, f"Unknown alias target for {abbreviation}")
    return {
        "aliases": [{"alias": a, "canonical": c, "topic_id": t, "related_not_synonyms": rel}
                    for a, (c, t, rel) in sorted(TERMS.items())],
        "topic_search_aliases": {r["topic_id"]: r["aliases"] for r in records},
        "related_not_synonyms": {"change control": ["change request", "CCB", "baseline change"],
                                 "risk": ["uncertainty", "threat", "opportunity", "risk response", "issue"],
                                 "work breakdown structure": ["decomposition", "work package"],
                                 "definition of done": ["acceptance criteria", "formal acceptance"]},
    }


def coverage(sessions, records):
    summary = ["# Coverage report", "",
               "Mapped means cited by a topic, not that the whole chunk was summarized. Entry coverage uses exact transcript entries in Sessions 2 onward. Session 1 uses whole chunk bounds; exact lines remain in each topic. Unmapped includes logistics, repeated material and in-scope discussion not yet curated.", "",
               "| Session | Transcript entries mapped | Chunks mapped | Callout locators mapped | Missing IDs |",
               "|---|---:|---:|---:|---|"]
    detail = []
    for n, src in sorted(sessions.items()):
        cited = [(r["topic_id"], s) for r in records for s in r["sources"] if s["session"] == n]
        entries = {i for _, s in cited for a, b in s["source_entry_ranges"] for i in range(a,b+1)}
        chunks = {c for _, s in cited for c in s["rag_chunk_ids"]}
        callouts = {c["file_line"] for _, s in cited for c in s["callouts"]}
        gaps = ", ".join(map(str, src["missing"])) or "None"
        summary.append(f"| {n} | {len(entries)}/{len(src['entries'])} | {len(chunks)}/{len(src['chunks'])} | {len(callouts)}/{len(src['callouts'])} | {gaps} |")
        detail += ["", f"## Session {n}", "",
                   "- Topics: " + (", ".join(sorted({t for t, _ in cited})) or "None"),
                   "- Unmapped chunks: " + (", ".join(sorted(src["chunks"].keys() - chunks)) or "None"),
                   "- Unmapped captured entry ranges: " + (", ".join(window_label(w) for w in runs(src["entries"] - entries)) or "None"),
                   "- Unmapped callout file-line ranges: " + (", ".join(window_label(w) for w in runs({c["file_line"] for c in src["callouts"]} - callouts)) or "None")]
        if "checkpoint" in src["files"]:
            detail.append("- Superseded, not used as evidence: " + link(src["files"]["checkpoint"], src["files"]["checkpoint"]))
    return "\n".join(summary + detail) + "\n"


def provenance(sessions, records):
    out = ["# Provenance report", "",
           "Sources are Zoom automatic transcripts and existing derived RAG and callout files. Callout references indicate overlap with a cited passage; Sessions 3 and 4 include keyword-selected excerpts, which do not all make an exam claim. Treat instructor guidance as such. No timestamp or slide locator is inferred.", "",
           "Session 1 has no inline source-entry headings. The builder matches every chunk's text against the transcript in order, excluding the explicit gap markers. Cite the transcript line window for precision; use the chunk IDs and entry bounds for RAG retrieval. In other sessions, the builder verifies RAG row IDs and row text against transcript headings.", "",
           "Chunk IDs are stored verbatim and scoped by file and session. Overlapping chunks can legitimately point to the same entries. Source byte hashes are pinned in [source-manifest.json](../source-manifest.json). Topic source maps and the JSON index carry exact provenance.", "",
           "| Session | Capture status | Missing source entries | Topics | Source files |", "|---|---|---|---:|---|"]
    for n, s in sorted(sessions.items()):
        names = ", ".join(link(k, v) for k, v in s["files"].items())
        topics = sum(any(src["session"] == n for src in r["sources"]) for r in records)
        out.append(f"| {n} | {s['status']} | {', '.join(map(str,s['missing'])) or 'None'} | {topics} | {names} |")
    return "\n".join(out) + "\n"


def retrieval_report(records):
    tests = read_json(CATALOG / "retrieval-tests.json")
    require(len(tests) >= 25 and len({t[0] for t in tests}) == len(tests), "Need at least 25 unique retrieval tests")
    ids = {r["topic_id"]: r for r in records}
    out = ["# Offline retrieval tests", "",
           "Top 1 requires the primary topic. Top 3 separately records whether the primary or an acceptable secondary is found. Source hit requires a top-3 primary record with the expected transcript anchor. Fixtures are not ranked as text; this is a regression suite, not a measure of Copilot accuracy.", "",
           "| # | Query | Expected primary | Acceptable secondary | Expected source | Actual top 3 | Top 1 | Acceptable @3 | Source @3 |",
           "|---:|---|---|---|---|---|---|---|---|"]
    primary_hits = acceptable_hits = source_hits = 0
    for i, (q, primary, secondary, session, line) in enumerate(tests, 1):
        require(primary in ids and set(secondary) <= ids.keys() - {primary}, f"Invalid test topics: {q}")
        anchor = next((s for s in ids[primary]["sources"] if s["session"] == session
                       and s["transcript_lines"][0] <= line <= s["transcript_lines"][1]), None)
        require(anchor, f"Expected source absent: {primary} S{session}:{line}")
        top = [r["topic_id"] for _, r in rank(q, records)[:3]]
        exact = bool(top and top[0] == primary)
        acceptable = bool(set(top) & {primary, *secondary})
        found_source = primary in top
        primary_hits += exact
        acceptable_hits += acceptable
        source_hits += found_source
        source_link = link(f"S{session} line {line}", anchor["transcript_file"], line)
        out.append(f"| {i} | {q.replace('|', '&#124;')} | {primary} | {', '.join(secondary) or 'None'} | {source_link} | {', '.join(top) or 'None'} | {'pass' if exact else 'miss'} | {'pass' if acceptable else 'miss'} | {'pass' if found_source else 'miss'} |")
    summary = (f"Primary @1: **{primary_hits}/{len(tests)}**. "
               f"Acceptable @3: **{acceptable_hits}/{len(tests)}**. "
               f"Expected source @3: **{source_hits}/{len(tests)}**.")
    out[2:2] = [summary, ""]
    return "\n".join(out) + "\n", (primary_hits, acceptable_hits, source_hits, len(tests))


def outputs(sessions):
    records = topic_records(sessions)
    result = {r["topic_file"]: topic_page(r) for r in records}
    domains = {}
    for r in records:
        domains.setdefault(r["domain"], []).append({"topic_id": r["topic_id"], "title": r["title"], "path": r["topic_file"]})
    result["topic-taxonomy.yaml"] = dump({"version": 1, "domains": dict(sorted(domains.items()))})
    result["concept-aliases.yaml"] = dump(aliases(records))
    result["semantic-index.json"] = dump(records)
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=list(records[0]), lineterminator="\n")
    writer.writeheader()
    for r in records:
        writer.writerow({k: v if isinstance(v, str) else json.dumps(v, ensure_ascii=False) for k, v in r.items()})
    result["semantic-index.csv"] = buf.getvalue()
    result["reports/coverage-report.md"] = coverage(sessions, records)
    result["reports/provenance-report.md"] = provenance(sessions, records)
    result["reports/retrieval-test-report.md"], stats = retrieval_report(records)
    return result, stats


def check_manifest(hashes, extend=False):
    pinned = read_json(LOCK)
    require(all(hashes.get(name) == digest for name, digest in pinned.items()),
            "An original source is missing or changed. Review outside this builder; the manifest was not updated.")
    if not extend:
        require(hashes == pinned, "New source files found; use --register-new after review.")
    return {**pinned, **hashes}


def layer_path(name):
    path = LAYER / name
    require(path.resolve().is_relative_to(LAYER), f"Unsafe output path: {path}")
    # Even an in-tree symlink or hard link could redirect a write to an existing file.
    require(not path.is_symlink() and not any(p.is_symlink() for p in path.parents if p != LAYER.parent),
            f"Symlink at output path: {path}")
    if path.exists():
        require(path.is_file() and path.stat().st_nlink == 1, f"Unexpected output file: {path}")
    return path


def write_changed(name, data):
    path = layer_path(name)
    blob = data.encode("utf-8")
    if not path.exists() or path.read_bytes() != blob:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
        return 1
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--register-new", action="store_true", help="Append new sources without changing existing hashes")
    mode.add_argument("--initialize-manifest", action="store_true", help="First capture only; refuses an existing manifest")
    args = p.parse_args()
    try:
        sessions, hashes = load_sources()
        if args.initialize_manifest:
            require(not LOCK.exists(), "Manifest already exists")
        else:
            check_manifest(hashes, args.register_new)
        files, (primary, acceptable, source, total) = outputs(sessions)
        for name in (*files, LOCK.name):
            layer_path(name)
        if args.initialize_manifest or args.register_new:
            write_changed(LOCK.name, dump(dict(sorted(hashes.items()))))
        changed = sum(write_changed(name, data) for name, data in files.items())
        require(load_sources()[1] == hashes, "Source files changed during build")
        print(f"{len(files)} generated files, {changed} updated; retrieval primary @1 {primary}/{total}, acceptable @3 {acceptable}/{total}, expected source @3 {source}/{total}")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        p.exit(1, f"Build failed: {exc}\n")


if __name__ == "__main__":
    main()
