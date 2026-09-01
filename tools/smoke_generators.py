"""Smoke: run the deterministic generators over a hash-selected slice of BCApps.
Prints per-generator counts + a couple of real samples. No model, no compile."""
import json, sys, collections, textwrap, io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.bcaldata.corpus import select_files, records_for_file
from src.bcaldata.alparse import objects
from src.bcaldata.generators import MEMBER_GENERATORS, object_level_g6

REPO = Path.home() / "bc-al-data/vendor/BCApps"
KEEP_ONE_IN = int(sys.argv[1]) if len(sys.argv) > 1 else 40

files = select_files(REPO, KEEP_ONE_IN)
print(f"selected {len(files)} / {len(sorted((REPO/'src').rglob('*.al')))} .al files "
      f"(deterministic sha1 % {KEEP_ONE_IN} == 0)\n")

counts = collections.Counter()
by_objkind = collections.Counter()
samples = collections.defaultdict(list)
n_members = n_parse_err = 0
recs_total = 0

for f in files:
    try:
        recs = list(records_for_file(f, "microsoft/BCApps", REPO))
    except Exception as e:
        n_parse_err += 1
        continue
    recs_total += len(recs)
    for rec in recs:
        n_members += 1
        by_objkind[rec["object_kind"]] += 1
        for gen in MEMBER_GENERATORS:
            for cand in gen(rec):
                counts[cand["gen"]] += 1
                if len(samples[cand["gen"]]) < 2 and rec["body_loc"] >= 5:
                    samples[cand["gen"]].append(cand)
    # object-level G6
    src = f.read_bytes()
    for obj in objects(src):
        for cand in object_level_g6(obj.text, obj.kind, obj.obj_id, obj.name,
                                    "microsoft/BCApps", str(f.relative_to(REPO))):
            counts[cand["gen"]] += 1
            if len(samples[cand["gen"]]) < 2:
                samples[cand["gen"]].append(cand)

print(f"parsed {n_members} members from {len(files)-n_parse_err} files "
      f"({n_parse_err} parse errors)\n")
print("object kinds seen:", dict(by_objkind.most_common(8)), "\n")
print("=== candidates per generator ===")
for g, c in counts.most_common():
    per_file = c / max(1, len(files))
    print(f"  {g:16} {c:6}   (~{per_file:.1f}/file  ->  ~{int(per_file*len(sorted((REPO/'src').rglob('*.al'))))} on full BCApps)")

for g, sl in samples.items():
    print(f"\n{'='*70}\n### SAMPLE — {g}\n{'='*70}")
    s = sl[0]
    print(f"[provenance] {s['meta']}")
    for msg in s["messages"]:
        body = msg["content"]
        if len(body) > 1400:
            body = body[:1400] + "\n... [truncated]"
        print(f"\n--- {msg['role'].upper()} ---\n{body}")
    if s.get("rejected_al"):
        print(f"\n--- REJECTED (mutated: {s['meta'].get('mutation_desc')}) ---\n{s['rejected_al'][:600]}")
