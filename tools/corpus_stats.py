import sys, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.bcaldata.corpus import select_files, records_for_file
REPO = Path.home()/"bc-al-data/vendor/BCApps"
K = int(sys.argv[1]) if len(sys.argv)>1 else 30
files = select_files(REPO, K)
n=body=doc=test=0; loc=collections.Counter(); kinds=collections.Counter()
for f in files:
    try: recs=list(records_for_file(f,"microsoft/BCApps",REPO))
    except Exception: continue
    for r in recs:
        n+=1; kinds[r["object_kind"]]+=1
        if r["is_test"]: test+=1
        if r["has_body"]: body+=1
        if len(r["doc_comment"])>20: doc+=1
        b=r["body_loc"]
        loc["0" if b==0 else "1-2" if b<3 else "3-10" if b<11 else "11-30" if b<31 else "31-60" if b<61 else "60+"]+=1
print(f"files={len(files)}  members={n}")
print(f"  with body           {body:6}  ({body/n:.0%})")
print(f"  in test codeunits   {test:6}  ({test/n:.0%})")
print(f"  with doc-comment>20  {doc:6}  ({doc/n:.0%})")
print("  body size (LOC):", dict(loc.most_common()))
print("  object kinds:", dict(kinds.most_common()))
