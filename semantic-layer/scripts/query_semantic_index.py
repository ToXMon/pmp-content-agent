"""Rank local topic records using words and phrases; never call an API."""
import argparse
import json
import re
from collections import Counter

from sources import LAYER

STOP = set("a an the and or to by of on in for with do does is are was were be it this that my our i we you how what when should can could would about have has from if which as at after before".split())


def words(text):
    return re.findall(r"[a-z0-9]+", text.casefold())


def rank(query, records):
    tokens = words(query)
    significant = set(tokens) - STOP
    # Preserve uppercase short acronyms: English “ac” or “ev” need not mean EVM.
    acronyms = set(re.findall(r"\b[A-Z][A-Z0-9]{1,4}\b", query))
    phrases = {tuple(tokens[i:j]) for i in range(len(tokens))
               for j in range(i+1, min(i+10, len(tokens))+1)}
    lookup = []
    df = Counter()
    for r in records:
        fields = [(r["title"], 5)] + [(t, 4) for t in r["concepts"] + r["aliases"]]
        fields += [(t, 2) for t in r["artifacts"]] + [(r["guidance"], 1), (r["when"], 1), (r["distinction"], 1)]
        lexicon = {}
        phrasescores = {}
        for term, weight in fields:
            for w in set(words(term)) - STOP:
                if len(w) <= 2 and w.upper() not in acronyms:
                    continue
                lexicon[w] = max(lexicon.get(w, 0), weight)
            wt = tuple(words(term))
            if weight >= 4 and wt in phrases and (len(wt) > 1 or
                    len(wt[0]) > 2 or wt[0].upper() in acronyms):
                phrasescores[wt] = max(phrasescores.get(wt, 0), weight)
        lookup.append((r, lexicon, phrasescores))
        df.update(lexicon)
    results = []
    for r, lexicon, matches in lookup:
        score = sum(lexicon[w] * (20 // df[w] + 1) for w in significant & lexicon.keys())
        score += sum(weight * (8 if len(phrase) > 1 else 3) for phrase, weight in matches.items())
        if score:
            results.append((score, r))
    return sorted(results, key=lambda pair: (-pair[0], pair[1]["topic_id"]))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--json", action="store_true", help="Return complete ranked records with source maps")
    args = p.parse_args()
    if args.limit < 1:
        p.error("--limit must be positive")
    records = json.loads((LAYER / "semantic-index.json").read_text(encoding="utf-8"))
    hits = rank(args.query, records)[:args.limit]
    if args.json:
        print(json.dumps([{"score": score, **r} for score, r in hits], ensure_ascii=False, indent=2))
        return
    if not hits:
        print("No matching topics.")
    for score, r in hits:
        print(f'{score:4}  {r["topic_id"]}  {r["title"]}  {r["topic_file"]}')
        for source in r["sources"]:
            print(f'      S{source["session"]} {", ".join(source["rag_chunk_ids"])}; '
                  f'transcript lines {source["transcript_lines"]}; {source["source_completeness"]}')


if __name__ == "__main__":
    main()
