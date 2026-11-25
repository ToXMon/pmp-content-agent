"""Validate every generated artifact against current read-only source evidence."""
from build_semantic_layer import check_manifest, layer_path, outputs
from sources import LAYER, load_sources, require


def main():
    try:
        sessions, hashes = load_sources()
        check_manifest(hashes)
        expected, (primary, acceptable, source, total) = outputs(sessions)
        wanted_topics = {name for name in expected if name.startswith("topics/")}
        actual_topics = {str(p.relative_to(LAYER)) for p in (LAYER / "topics").rglob("*.md")}
        require(actual_topics == wanted_topics, f"Missing/orphan topic files: {sorted(actual_topics ^ wanted_topics)}")
        problems = []
        for name, data in expected.items():
            path = layer_path(name)
            if not path.is_file() or path.read_bytes() != data.encode("utf-8"):
                problems.append(name)
        require(not problems, "Stale, missing or edited generated files: " + ", ".join(problems))
        require(primary == total, f"Primary retrieval regression: {primary}/{total}")
        require(source == total, f"Expected-source retrieval regression: {source}/{total}")
        print(f"Validated {len(wanted_topics)} topics, {len(sessions)} sessions, {len(hashes)} unchanged source files.")
        print(f"Retrieval: primary @1 {primary}/{total}; acceptable @3 {acceptable}/{total}; source @3 {source}/{total}.")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        raise SystemExit(f"Validation failed: {exc}") from None


if __name__ == "__main__":
    main()
