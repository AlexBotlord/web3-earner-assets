import json, os, statistics
D = r"C:\web3-earner\.context\poidh-1520-ratlab-audit\research\rnd\research\coordinator\arms\packproof"
d = json.load(open(os.path.join(D, "aggregates", "packproof.json"), encoding="utf-8"))
pp = d["per_pack"]
rows = []
for p, s in pp.items():
    rows.append((p, s["on"]["kept"], s["on"]["correct_any"], s["off"]["correct_any"],
                 s["on_correct_given_kept"][0], s["on_correct_given_kept"][1],
                 s["on_correct_given_not_kept"][0], s["on_correct_given_not_kept"][1],
                 s["d_correct_any"][0]))
print(f"{'pack':22}{'kept':>6}{'ON_CA':>7}{'OFF_CA':>8}{'kept->CA':>9}{'nk->CA':>8}{'gap':>7}{'delta':>7}")
for r in rows:
    print(f"{r[0]:22}{r[1]:>6.2f}{r[2]:>7.2f}{r[3]:>8.2f}{r[4]:>9.3f}{r[6]:>8.3f}{r[4]-r[6]:>7.3f}{r[8]:>7.2f}")

def spearman(x, y):
    def rank(v):
        s = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0]*len(v); i = 0
        while i < len(s):
            j = i
            while j+1 < len(s) and v[s[j+1]] == v[s[i]]: j += 1
            for k in range(i, j+1): r[s[k]] = (i+j)/2 + 1
            i = j+1
        return r
    rx, ry = rank(x), rank(y)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a-mx)*(b-my) for a, b in zip(rx, ry))
    den = (sum((a-mx)**2 for a in rx)*sum((b-my)**2 for b in ry))**.5
    return num/den

kept = [r[1] for r in rows]; on = [r[2] for r in rows]; off = [r[3] for r in rows]
print("\nSpearman(kept, ON correct_any) = %.3f  n=%d" % (spearman(kept, on), len(rows)))
print("Spearman(kept, kept->CA)       = %.3f" % spearman(kept, [r[4] for r in rows]))
print("Spearman(OFF_CA, kept->CA)     = %.3f" % spearman(off, [r[4] for r in rows]))
print("Spearman(OFF_CA, gap)          = %.3f" % spearman(off, [r[4]-r[6] for r in rows]))
print("Pearson(kept, ON_CA)           = %.3f" % statistics.correlation(kept, on))
print("mean kept %.3f  mean ON_CA %.3f" % (statistics.mean(kept), statistics.mean(on)))

# pooled numbers check
po = d["pooled"]
print("\npooled n", po["n"], "ON CA", po["on"]["correct_any"], "OFF CA", po["off"]["correct_any"],
      "kept", po["on"]["kept"], "kept->CA", po["on_correct_given_kept"], "notkept->CA", po["on_correct_given_not_kept"])
# reconstruct 0.48 vs 0.26 counts
print("counts: ON", round(po["on"]["correct_any"]*po["n"]), "OFF", round(po["off"]["correct_any"]*po["n"]))
# cluster check: per-pack deltas
dl = [r[8] for r in rows]
print("per-pack deltas", dl, "mean %.4f sd %.4f se %.4f" % (statistics.mean(dl), statistics.stdev(dl), statistics.stdev(dl)/len(dl)**.5))
t = 2.306
print("pack-cluster 95%% CI: %.3f .. %.3f" % (statistics.mean(dl)-t*statistics.stdev(dl)/len(dl)**.5, statistics.mean(dl)+t*statistics.stdev(dl)/len(dl)**.5))
