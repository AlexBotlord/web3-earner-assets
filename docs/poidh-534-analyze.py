# Audit of benching v0.4 / DEVICE-FINAL (POIDH #534). Stdlib only.
# Prints every number quoted in analysis.md. Place next to:
#   ./boar-bench/bench/v0.4/{items.jsonl,refs/v2/claude.jsonl}
#   ./boar-research/rnd/research/coordinator/{ruler/factavail/out/factavail-items.json,arms/device-final/...}
#   ./traces/{judge_dev-s42.opus.judgments.jsonl,judge_dev-s42.codex.judgments.jsonl,traces_dev-s42.traces.jsonl}
import json, os, statistics as st, collections

D = os.path.dirname(os.path.abspath(__file__))
P = lambda *a: os.path.join(D, *a)
AX = ("correctness", "completeness", "usefulness")
w = lambda: print()

items = {r["id"]: r for r in (json.loads(l) for l in open(P("boar-bench", "bench", "v0.4", "items.jsonl"), encoding="utf-8") if l.strip())}
tr = {t["itemId"]: t for t in (json.loads(l) for l in open(P("traces", "traces_dev-s42.traces.jsonl"), encoding="utf-8") if l.strip())}
fa = json.load(open(P("boar-research", "rnd", "research", "coordinator", "ruler", "factavail", "out", "factavail-items.json"), encoding="utf-8"))["items"]
H = [i for i in items if not items[i]["tags"]["anchor_vexact"]]
print(f"items {len(items)}, headline H {len(H)}, health items {sum(1 for i in H if items[i]['tags']['health_safety'])}")

def load(fam):
    rows = [json.loads(l) for l in open(P("traces", f"judge_dev-s42.{fam}.judgments.jsonl"), encoding="utf-8") if l.strip()]
    by = collections.defaultdict(dict)
    for r in rows:
        by[r["queryId"]][r["order"]] = r["mapped"]
    return rows, by

def per_item(by):
    out = {}
    for i, o in by.items():
        if "boarA" not in o or "boarB" not in o:
            continue
        g = lambda side, k: (o["boarA"][side][k] + o["boarB"][side][k]) / 2
        mb = sum(g("boar", k) for k in AX) / 3
        mr = sum(g("ref", k) for k in AX) / 3
        out[i] = dict(mb=mb, mr=mr, corr=g("boar", "correctness"), comp=g("boar", "completeness"), usef=g("boar", "usefulness"))
    return out

for fam in ("opus", "codex"):
    rows, by = load(fam)
    it = per_item(by)
    n = len(it)
    print(f"\n=== {fam} ({n} items, {len(rows)} order-rows) ===")
    for k in AX:
        a = st.mean((o["boarA"]["boar"][k] + o["boarB"]["boar"][k]) / 2 for o in by.values())
        r = st.mean((o["boarA"]["ref"][k] + o["boarB"]["ref"][k]) / 2 for o in by.values())
        print(f"  {k:12s} app {a:.2f}  ref {r:.2f}  ratio {a/r:.2f}")
    sU = sum(v["mb"] - 1 for v in it.values()) / sum(v["mr"] - 1 for v in it.values())
    print(f"  U (unweighted, 75 items) {sU:.4f}; mean app m {st.mean(v['mb'] for v in it.values()):.3f}; "
          f"mean ref m {st.mean(v['mr'] for v in it.values()):.3f}")
    print(f"  ref floor-adj mass {st.mean(v['mr']-1 for v in it.values()):.3f}/4.0 = "
          f"{(st.mean(v['mr']-1 for v in it.values())/4)*100:.1f}%; at ceiling {sum(1 for v in it.values() if v['mr']>=3.999)}/{n}")
    print("  ref completeness==5 on order-rows:",
          sum(1 for o in by.values() for k in o if o[k]["ref"]["completeness"] == 5), "/", 2 * n)
    good = [(i, v) for i, v in it.items() if v["corr"] >= 4]
    over = [(i, round((v["mb"]-1)/(v["mr"]-1), 3)) for i, v in good if (v["mb"]-1)/(v["mr"]-1) >= 0.5]
    print(f"  items with mean correctness >= 4: {len(good)}; of those per-item U >= 0.5: {len(over)} {over}")
    print("  top per-item U:", sorted(((round((v['mb']-1)/(v['mr']-1), 3), i) for i, v in it.items()), reverse=True)[:4])
    if fam == "opus":
        print(f"  cw-001: correctness {it['cw-001']['corr']:.1f}, completeness {it['cw-001']['comp']:.1f}, "
              f"usefulness {it['cw-001']['usef']:.1f}, per-item U {(it['cw-001']['mb']-1)/(it['cw-001']['mr']-1):.3f}")
        lo = [v for v in it.values() if v["mb"] <= 1.0]
        print(f"  corr(app,ref) = {st.correlation([v['mb'] for v in it.values()], [v['mr'] for v in it.values()]):+.3f}; "
              f"ref mass by app tercile {st.mean(v['mr']-1 for v in lo):.3f} (bottom) ... {st.mean(v['mr']-1 for v in it.values() if v['mb']>=2.5):.3f} (top)")

w()
print("=== health items (seed 42) ===")
for i in sorted(i for i in H if items[i]["tags"]["health_safety"]):
    r = tr[i]["ruler"]
    print(f"  {i:8s} path={','.join(r['paths']):22s} refusedZ={str(r['refusedZ']):5s} "
          f"kept={str(r['kept']):5s} factavail={fa[i]['label']:9s} text={tr[i]['answer']['text'][:60]!r}")

w()
print("=== answer length ===")
ref = {r["id"]: r for r in (json.loads(l) for l in open(P("boar-bench", "bench", "v0.4", "refs", "v2", "claude.jsonl"), encoding="utf-8") if l.strip())}
la = [len(tr[i]["answer"]["text"]) for i in tr]
lr = [len(ref[i]["answer"]) for i in tr if i in ref]
print(f"  app median {st.median(la):.0f} chars ({st.median([len(tr[i]['answer']['text'].split()) for i in tr]):.0f} words); "
      f"ref median {st.median(lr):.0f} chars -> {st.median(lr)/st.median(la):.1f}x")

w()
print("=== published aggregate vs report (m1.json) ===")
m1 = json.load(open(P("boar-research", "rnd", "research", "coordinator", "arms", "device-final", "aggregates", "m1.json"), encoding="utf-8"))
for fam, name in (("G1", "G1 Claude (Opus vs Claude refs)"), ("G2", "G2 Codex (gpt-5.6-sol vs Codex refs)")):
    print(f"  {fam} per-seed CR {m1['per_seed'][name+' s42']['CR']:.3f} / {m1['per_seed'][name+' s43']['CR']:.3f}  "
          f"pooled CR {m1['pooled'][name]['CR']:.4f}  correct_per_100 {m1['pooled'][name]['correct_per_100']:.2f}  "
          f"(DEVICE-FINAL.md: pooled CR is not reported)")
print(f"  U-total pooled G1 {m1['pooled']['G1 Claude (Opus vs Claude refs)']['U_total']:.4f}, "
      f"abs_app {m1['pooled']['G1 Claude (Opus vs Claude refs)']['abs_app']:.3f}, "
      f"abs_ref {m1['pooled']['G1 Claude (Opus vs Claude refs)']['abs_ref']:.3f}")
print("  factavail U (pooled G1):", {k: round(v['U'], 3) for k, v in m1['pooled']['G1 Claude (Opus vs Claude refs)']['factavail'].items()})
print("  factavail U (pooled G2):", {k: round(v['U'], 3) for k, v in m1['pooled']['G2 Codex (gpt-5.6-sol vs Codex refs)']['factavail'].items()})
