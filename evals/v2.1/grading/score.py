import json, pathlib, statistics as st, sys
key = json.load(open("docxbuild/blind21-key.json"))
rows = []
for s in ["S1","S2","S3","S4","S5","S6"]:
    p = pathlib.Path(f"blind21/{s}-scores.json")
    if not p.exists(): continue
    sc = json.load(open(p))
    for rid, v in sc.items():
        cond, model, n = key[f"{s}/{rid}"].split("-")
        assert len(v["scores"]) == 12, (s, rid)
        rows.append(dict(s=s, rid=rid, cond=cond, model=model, total=sum(v["scores"]), items=v["scores"], note=v["note"]))
def agg(f):
    xs=[r["total"] for r in rows if f(r)]; return (st.mean(xs), min(xs), max(xs), len(xs)) if xs else None
out=[]
for s in sorted({r["s"] for r in rows}):
    for m in ["sonnet","haiku","all"]:
        b=agg(lambda r: r["s"]==s and r["cond"]=="baseline" and (m=="all" or r["model"]==m))
        k=agg(lambda r: r["s"]==s and r["cond"]=="skill" and (m=="all" or r["model"]==m))
        out.append(f"{s} {m:6s} baseline {b[0]:5.2f} [{b[1]}-{b[2]}] n={b[3]} | skill {k[0]:5.2f} [{k[1]}-{k[2]}] n={k[3]} | delta {k[0]-b[0]:+.2f}")
for m in ["sonnet","haiku","all"]:
    b=agg(lambda r: r["cond"]=="baseline" and (m=="all" or r["model"]==m)); k=agg(lambda r: r["cond"]=="skill" and (m=="all" or r["model"]==m))
    out.append(f"ALL {m:6s} baseline {b[0]:5.2f}/12 ({b[0]/12:.0%}) n={b[3]} | skill {k[0]:5.2f}/12 ({k[0]/12:.0%}) n={k[3]}")
# per-item deltas per scenario
for s in sorted({r["s"] for r in rows}):
    d=[]
    for i in range(12):
        bi=st.mean(r["items"][i] for r in rows if r["s"]==s and r["cond"]=="baseline"); ki=st.mean(r["items"][i] for r in rows if r["s"]==s and r["cond"]=="skill")
        d.append(f"{i+1}:{ki-bi:+.1f}")
    out.append(f"{s} item deltas " + " ".join(d))
# wins
import itertools
print("\n".join(out))
json.dump(rows, open("docxbuild/scored21-rows.json","w"), indent=1)
