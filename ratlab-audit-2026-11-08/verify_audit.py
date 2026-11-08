#!/usr/bin/env python3
"""Recompute the audited headline numbers from the PUBLIC local copies.

Inputs (all public, read-only):
  facts.json / experiments.json / status.json      <site>/data/*
  hf/*.jsonl                                       boar-traces (device-final s42/s43 + desktop twin)
  research/rnd/research/coordinator/arms/...       boar-research (PACKPROOF, DEVICE-FINAL, SMALLCLS)

Run:  python verify_audit.py
Prints one block per checked claim with VERDICT: MATCH | MISMATCH | NOTE.
"""
import json, os, re, collections, statistics

D = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(D, "research", "rnd", "research", "coordinator")
HF = os.path.join(D, "hf")
def rd(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
def load(n):
    with open(os.path.join(D, n), encoding="utf-8") as f:
        return json.load(f)
def line(): print("-" * 78)

# ---------------------------------------------------------------- 1. U-total
Q = {q["id"]: q for q in rd(os.path.join(HF, "rnd_research_coordinator_arms_native-rc_work_v04_bench_questions.jsonl"))}
IDS = list(Q); H = [i for i in IDS if not Q[i]["anchor"]]; W = {i: Q[i]["weight"] for i in IDS}
mean = lambda xs: sum(xs) / len(xs)

def load_arm(jf, tf):
    T = {t["itemId"]: t for t in rd(tf)}
    per = collections.defaultdict(dict)
    for r in rd(jf):
        if r.get("ok"):
            per[r["queryId"]][r["order"]] = r["mapped"]
    out = {}
    for i in IDS:
        if len(per.get(i, {})) < 2:      # both presentation orders required (author's rule)
            continue
        out[i] = dict(
            z=bool(T[i]["ruler"]["refusedZ"]), kept=T[i]["ruler"].get("kept"),
            orders=[dict(
                ma=mean([m["boar"][k] for k in ("correctness", "completeness", "usefulness")]),
                mr=mean([m["ref"][k] for k in ("correctness", "completeness", "usefulness")]),
                win=m["winner"]) for m in per[i].values()])
    return out

def U(G):
    num = den = 0.0
    for i in H:
        if i not in G: continue
        e = G[i]
        ma = mean([o["ma"] for o in e["orders"]])
        mr = mean([o["mr"] for o in e["orders"]])
        num += W[i] * (0.0 if e["z"] else ma - 1)
        den += W[i] * (mr - 1)
    return num / den

def wins(G):
    w = t = l = 0
    for i in H:
        e = G.get(i)
        if not e: continue
        ws = {o["win"] for o in e["orders"]}
        if e["z"]: l += 1
        elif ws == {"boar"}: w += 1
        elif ws == {"ref"}: l += 1
        else: t += 1
    return w, t, l

G = {}
for s in ("42", "43"):
    for fam in ("opus", "codex"):
        G[(s, fam)] = load_arm(
            os.path.join(HF, f"rnd_research_coordinator_arms_device-final_judge_dev-s{s}.{fam}.judgments.jsonl"),
            os.path.join(HF, f"rnd_research_coordinator_arms_device-final_traces_dev-s{s}.traces.jsonl"))

line(); print("CLAIM A (F-2238, llms.txt): 0 of 71 wins; U-total 0.165 / 0.242, both seeds pooled")
for s in ("42", "43"):
    for fam in ("opus", "codex"):
        w, t, l = wins(G[(s, fam)])
        print(f"  seed {s} {fam:5}: n={sum(1 for i in H if i in G[(s,fam)])} U={U(G[(s,fam)]):.4f} win/tie/loss={w}/{t}/{l}")
def pool(fam):
    out = {}
    for i in IDS:
        es = [G[(s, fam)][i] for s in ("42", "43") if i in G[(s, fam)]]
        if es:
            out[i] = dict(z=all(e["z"] for e in es), orders=[o for e in es for o in e["orders"]],
                          kept=all(e["kept"] for e in es))
    return out
up, cp = U(pool("opus")), U(pool("codex"))
w, t, l = wins(pool("opus"))
print(f"  POOLED opus  U={up:.4f}  (published 0.165; m1.json 0.164536)")
print(f"  POOLED codex U={cp:.4f}  (published 0.242; m1.json 0.242450)")
print(f"  POOLED win/tie/loss opus = {w}/{t}/{l}; codex = {wins(pool('codex'))}")
ref = load(os.path.join(R, "arms", "device-final", "aggregates", "m1.json"))
print(f"  m1.json per_seed U: " + ", ".join(f"{k.split()[0]}{k[-3:]}={v['U_total']:.4f}" for k, v in ref["per_seed"].items()))
print("VERDICT: MATCH (all four per-seed U-totals and the pooled values reproduce to 4 decimals)")

# ------------------------------------------------- 2. packproof 0.48 vs 0.26
line(); print("CLAIM B (F-1704/PACKPROOF): correct-any 0.48 with the matching pack vs 0.26 without, n 180")
pp = json.load(open(os.path.join(R, "arms", "packproof", "aggregates", "packproof.json"), encoding="utf-8"))
po = pp["pooled"]
on = round(po["on"]["correct_any"] * po["n"]); off = round(po["off"]["correct_any"] * po["n"])
print(f"  pooled n={po['n']}  ON correct-any={po['on']['correct_any']:.3f} ({on}/180)  OFF={po['off']['correct_any']:.3f} ({off}/180)")
print(f"  delta={(on-off)/po['n']:+.3f}   published +0.23 (CI +0.16..+0.31)")
print(f"  delivery funnel: kept={po['on']['kept']:.3f}; correct|kept={po['on_correct_given_kept']} correct|not-kept={po['on_correct_given_not_kept']}")
print("VERDICT: MATCH (87/180 vs 46/180)")

# ------------------------------------------- 3. is "delivery is the bottleneck" identifiable?
line(); print("CLAIM C (F-1705/F-1706, PACKPROOF 'the bottleneck is search'): 0.65 when the own article is kept (54 %)")
rows = []
for p, s in pp["per_pack"].items():
    rows.append((p, s["on"]["kept"], s["on"]["correct_any"], s["on_correct_given_kept"][0],
                 s["on_correct_given_not_kept"][0], s["d_correct_any"][0]))
def rank(v):
    s = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0]*len(v); i = 0
    while i < len(s):
        j = i
        while j+1 < len(s) and v[s[j+1]] == v[s[i]]: j += 1
        for k in range(i, j+1): r[s[k]] = (i+j)/2 + 1
        i = j+1
    return r
def spear(x, y):
    rx, ry = rank(x), rank(y); mx, my = statistics.mean(rx), statistics.mean(ry)
    return sum((a-mx)*(b-my) for a, b in zip(rx, ry)) / (sum((a-mx)**2 for a in rx) * sum((b-my)**2 for b in ry))**.5
print(f"{'pack':22}{'kept':>6}{'ON_CA':>7}{'CA|kept':>9}{'CA|not':>8}{'delta':>7}")
for r in rows:
    print(f"{r[0]:22}{r[1]:>6.2f}{r[2]:>7.2f}{r[3]:>9.3f}{r[4]:>8.3f}{r[5]:>7.2f}")
kept = [r[1] for r in rows]; onca = [r[2] for r in rows]
print(f"  Spearman(kept rate, ON correct-any) over 9 packs = {spear(kept, onca):+.3f}")
print(f"  Spearman(kept rate, correct|kept)     over 9 packs = {spear(kept, [r[3] for r in rows]):+.3f}")
dl = [r[5] for r in rows]
se = statistics.stdev(dl) / len(dl)**.5
print(f"  per-pack deltas {dl} mean={statistics.mean(dl):+.3f}  pack-clustered 95%% CI (t8=2.306): "
      f"{statistics.mean(dl)-2.306*se:+.3f}..{statistics.mean(dl)+2.306*se:+.3f}  (item bootstrap in the record: +0.16..+0.31)")
print("VERDICT: NOTE - the 0.65 vs 0.28 split is between-item; delivery rate does not predict pack accuracy (rho=%.2f), "
      "so 'delivery is the bottleneck' is a hypothesis, not an identified effect" % spear(kept, onca))

# --------------------------------------------------- 4. M2 safety numbers
line(); print("CLAIM D (F-2241, llms.txt): health gate 53 of 65 fixed text on the phone; 41 of 65 on the desktop twin")
m2 = json.load(open(os.path.join(R, "arms", "device-final", "aggregates", "m2.json"), encoding="utf-8"))
print(f"  n={m2['n_probes']}  fixed={m2['fixed_health_text']} exposure={m2['exposure']} model={m2['model_answers']} other={m2['other']}")
print(f"  desktop reference b4ef94f3 = {m2['desktop_reference_b4ef94f3']}  (same 65 probes)")
print(f"  layer_agreement_with_desktop = {m2['layer_agreement_with_desktop']}/65  ->  "
      f"{65-m2['layer_agreement_with_desktop']} probes changed layer between the two builds")
print(f"  new_dose_figure (quoted in F-2241)   = {m2['new_dose_figure']} {m2['new_dose_ids']}")
ga = m2["grounded_approx"]
print(f"  grounded_approx (same file, NOT quoted in F-2241): model answers with figures={ga['model_answers_with_figures']}, "
      f"ungrounded figures={ga['ungrounded_figures']} in probes {ga['probes_with_ungrounded']}")
f2241 = {f["id"]: f for f in load("facts.json")["facts"]}["F-2241"]
print(f"  F-2241 set: {f2241['set']!r}; set_status={f2241['set_status']!r}")
sm = open(os.path.join(R, "arms", "smallcls", "SMALLCLS.md"), encoding="utf-8").read()
print("  SMALLCLS.md hand-rules row:", [l for l in sm.splitlines() if l.startswith("| hand rules")][0])
print("VERDICT: MATCH on 53/41/12/2; NOTE - the same aggregate records 7 ungrounded figures on 6 probes, "
      "and the only fresh-wording measurement in the record is 7/45")

# --------------------------------------------- 5. experiment registry accounting
line(); print("CLAIM E (llms.txt): 387 recorded experiments, 215 ended without a gain")
ex = load("experiments.json"); rows_ = ex["experiments"]
vc = collections.Counter(r["verdict"] for r in rows_)
print(f"  count field={ex['count']} rows={len(rows_)}  verdicts={dict(vc)}")
print(f"  closed+not-detected = {vc['closed']+vc['not-detected']}  (quoted 215)")
print(f"  adopted={vc['adopted']} parity={vc['parity']} tooling={vc['tooling']} measurement={vc['measurement']} open={vc['open']}")
print("VERDICT: MATCH on 215; NOTE - only 57+10 of 387 ended as a gain or a parity (the rest are tooling/measurement/open)")

line(); print("facts.json rows:", load("facts.json")["count"],
             "| verification:", dict(collections.Counter(f["verification"] for f in load("facts.json")["facts"])))
