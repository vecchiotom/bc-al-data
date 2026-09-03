"""Stage 5/6 behavior: preference-aware dedup, whole-app held-out, per-gen cap."""
from __future__ import annotations
import json

from bcaldata.assemble import assemble
from bcaldata.filter import filter_file


def _pair(prompt: str, chosen: str, rejected: str, path: str, gen: str = "g5_error_fix") -> dict:
    return {"gen": gen, "target_al": chosen, "rejected_al": rejected,
            "messages": [{"role": "user", "content": prompt},
                         {"role": "assistant", "content": f"```al\n{chosen}\n```"}],
            "meta": {"repo": "microsoft/BCApps", "path": path, "member": "Foo"}}


def test_filter_keeps_distinct_broken_variants_of_one_member(tmp_path):
    # same fix, five different breakages -> all five must survive (dedup on prompt+rejected)
    rows = [_pair(f"Fix this:\n{bad}", "procedure Foo() begin Bar() end;", bad, "src/App/A.al")
            for bad in ("procedure Foo() begin BaX() end;",
                        "procedure Foo() begin Bar( end;",
                        "procedure Foo() begin Bar() en;",
                        "procedure Foo() begi Bar() end;",
                        "procedure Foo() begin Bqr() end;")]
    src = tmp_path / "g5.jsonl"
    src.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    out = tmp_path / "g5.out.jsonl"
    stats = filter_file(src, out)
    assert stats["kept"] == 5, stats


def test_assemble_heldout_is_whole_app_and_disjoint(tmp_path):
    vdir = tmp_path / "verified"
    vdir.mkdir()
    sft = [{"gen": "g1_fim", "target_al": f"p{i}",
            "messages": [{"role": "user", "content": f"q{i}"},
                         {"role": "assistant", "content": f"```al\np{i}\n```"}],
            "meta": {"repo": "microsoft/BCApps", "path": f"src/App{i % 7}/x/f.al"}}
           for i in range(200)]
    (vdir / "g1.jsonl").write_text("\n".join(json.dumps(r) for r in sft) + "\n")

    card = assemble(vdir, kind_cap=1.0, out_dir=tmp_path / "ds")
    assert card["heldout"] + card["train"] + card["val"] == 200
    assert card["heldout"] > 0 and card["train"] > 0
    heldout = [json.loads(l) for l in (tmp_path / "ds" / "heldout.jsonl").read_text().splitlines() if l.strip()]
    held_apps = {tuple(r["meta"]["path"].rsplit("/", 1)[0].split("/")) for r in heldout}
    train = [json.loads(l) for l in (tmp_path / "ds" / "train.jsonl").read_text().splitlines() if l.strip()]
    train_apps = {tuple(r["meta"]["path"].rsplit("/", 1)[0].split("/")) for r in train}
    assert held_apps.isdisjoint(train_apps)


def test_assemble_kind_cap_bounds_a_dominant_generator(tmp_path):
    vdir = tmp_path / "verified"
    vdir.mkdir()
    rows = []
    for i in range(180):
        rows.append({"gen": "g1_fim", "target_al": f"a{i}",
                     "messages": [{"role": "user", "content": f"qa{i}"},
                                  {"role": "assistant", "content": f"```al\na{i}\n```"}],
                     "meta": {"repo": "microsoft/BCApps", "path": f"src/App{i}/f.al"}})
    for i in range(20):
        rows.append({"gen": "g2_sig2body", "target_al": f"b{i}",
                     "messages": [{"role": "user", "content": f"qb{i}"},
                                  {"role": "assistant", "content": f"```al\nb{i}\n```"}],
                     "meta": {"repo": "microsoft/BCApps", "path": f"src/Other{i}/f.al"}})
    (vdir / "all.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    card = assemble(vdir, kind_cap=0.5, out_dir=tmp_path / "ds")
    assert card["dropped_to_kind_cap"] > 0
