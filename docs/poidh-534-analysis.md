# The ruler measures coverage, not accuracy — and the health gate zeroes the one thing it can answer

An audit of bench v0.4 and the LabRat device run (`DEVICE-FINAL`), built by recomputing the published
judgments rather than reading the summaries. All numbers below come from the public artifacts named
next to them and can be reproduced in one sitting; where I could not check something, I say so.

**Verdict up front.** The record is unusually honest and the conclusion "below the 0.50 bar" survives
every check I ran. What does not survive is the *reading* of 0.165 as "16.5 % as good as internet plus a
frontier AI". On this ruler that number is mostly a statement about how many key points a 36-word answer
covers against a 700-word reference, and the reference side of the ratio is pinned at the rubric ceiling
(96.9 % of its maximum) on every single item, so the ratio is not doing the normalising work the spec
claims for it. Two of the three defects below are cheap to fix and one of them is worth more than any
experiment left in the record.

---

## Finding 1 — The 0.50 bar is a coverage bar; the app's accuracy is 2.3x better than its coverage, and the ratio cannot see the difference

### Evidence

Recomputed from the raw judgments (`boar-traces`, `rnd/research/coordinator/arms/device-final/judge/dev-s42.opus.judgments.jsonl`,
150 rows = 75 items × 2 presentation orders), using the rubric in `boar-bench/scorers/vendor/eval-lib/judge-core.mjs:40-43`:

| Axis (mean over both orders, seed 42, Opus judge) | LabRat | Reference | ratio |
|---|---|---|---|
| correctness | **2.55** | 4.71 | **0.54** |
| completeness | **1.18** | 4.93 | **0.24** |
| usefulness | **1.30** | 4.99 | **0.26** |

The ratio of sums (U-total = Σw·u / Σw·r, `RULER-SPEC-v1-r4` §3.4) is 0.167 for this seed. Splitting
the deficit by axis: correctness carries ~20 % of it, completeness + usefulness ~80 %. So the metric is
not primarily measuring whether LabRat is *right*.

Four consequences, each checkable:

1. **A factually correct answer is capped at ≈0.6.** `cw-001` ("capital of Kazakhstan"): the app says
   Astana, correctly, and the judge gives it correctness 5/5 in both orders — and completeness 2,
   usefulness 3. m = 3.33/5 against the reference's 4.88/5 → per-item U = **0.583**. Fifteen of the 71
   headline items have mean correctness ≥ 4 (the answer is right); only **3 of those 15** reach per-item
   U ≥ 0.50, and the best item in the whole set is **0.727** (`cw-020`). Nothing in the set exceeds 0.73.
2. **The denominator is saturated, so U is an absolute score in disguise.** Reference mean rubric
   4.878/5; floor-adjusted mass **3.878 out of a possible 4.0 = 96.9 %**; **75 of 75** headline items sit
   at exactly 5.0/5 under Opus (71/75 under gpt-5.6-sol, 4.782/5). Reference completeness is 5 on 140 of
   150 order-rows. U therefore reduces to (m_app − 1) / 3.878. As a normaliser the denominator carries
   essentially no item-level information: corr(app mass, ref mass) = **+0.05**, and mean ref mass is
   3.878 / 3.876 / 3.889 across the bottom, middle and top third of app answers. The spec's promise
   (§3.2, "a frozen reference denominator so every run shares the same denominator") is true but empty —
   it is a constant, not a difficulty control. The 0.50 bar is exactly "mean rubric 2.94/5"; the app is
   at 1.68.
3. **The length asymmetry is 19x and was never measured on this ruler.** Median answer length: LabRat
   **220 characters (36 words)**, reference **4,174 characters** (`bench/v0.4/refs/v2/claude.jsonl`).
   The app ships Succinct style only — no Detailed, no length option (`data/glossary.md`, G-boarlite).
   The project already ran this experiment once: `arms/lengthshare/LENGTHSHARE.md` re-judged the *same*
   answers against references condensed to ≤80 words and got floor-adjusted **0.412 → 0.514 (+0.102,
   CI +0.068…+0.144**, deep tier, V-para, 51 ids, ~280-word references). That was on the old scale, with
   references already 2.5x shorter than v0.4's. It was not repeated on v0.4, and the v0.4 headline
   inherits an unmeasured length share.
4. **The honest counter-check, in the record's favour:** within the app's own range, longer answers did
   *not* score better — corr(answer chars, app m) = **−0.04** over 39–650 characters, and the project's
   own "detailed persona" arm lost 0.066 on the deep tier. So "just write more" is not the fix; the fix
   is *coverage of the notes' key points*, which the Succinct pipeline does not attempt.

### Why it matters

The headline sentence — "0 of 71 wins, U-total 0.165, below the 0.50 bar" — is read by every downstream
agent (the site's own `llms.txt` mandates that reading) as "the app is a sixth as good as frontier+web".
What was measured is "the app's answers cover about a quarter of the key points that a 700-word
web-searched reference covers, while being right more than half as often". Those are different claims,
and only the second one tells you what to build next. It also makes the bar's difficulty invisible: a
perfect-but-terse answer tops out near 0.6–0.7 on this instrument, so 0.50 is not "half as good" but
"~75–85 % of a perfect short answer".

### Suggested fix (one afternoon, no generation)

Re-run LENGTHSHARE on v0.4 and publish both numbers: cap the two reference families to ≤120 words with a
frozen prompt (142 capping calls), re-judge the existing 71 app answers against them (284 judge calls),
report U-total paired Δ with its CI, exactly as `arms/lengthshare` did. Two outcomes and both are useful:
if U moves < +0.03 the "83 % substance" reading holds on the ruler too and the headline is safe; if it
moves +0.10 or more, the headline needs the qualifier ("against references of equal length: X") and the
product decision changes — the lever is answer coverage, not a bigger model. Report the ceiling
(per-item max 0.73) and the correct-answer band (0.25–0.73) next to the bar in every table.

---

## Finding 2 — The health gate converts 5 of 11 health items into hard zeros, and 4 of the 5 were answerable from the packs already installed

### Evidence

`bench/v0.4/items.jsonl` has 11 items tagged `tags.health_safety`. In the phone run
(`traces/dev-s42.traces.jsonl`) **five** of them take the path `health-fixed`, with `tokens: [1]`,
`kept: false`, `refusedZ: true`:

| item | question (abridged) | FACT-AVAIL label | packs contain the answer |
|---|---|---|---|
| `cw-021` | normal resting heart rate for an adult | **AVAILABLE** | yes |
| `cw-022` | why altitude sickness happens, how to avoid it | **AVAILABLE** | yes |
| `cw-025` | malaria and mosquito bites, rural Kenya | NONE | no |
| `cx-021` | which mosquitoes spread dengue, when they bite | **AVAILABLE** | yes |
| `cx-023` | why antibiotics don't cure a cold, resistance | **AVAILABLE** | yes |

The answer in all five cases is the same fixed refusal: *"I don't have a reliable offline source on
this, so I won't give health advice from memory. In an emergency, call your local emergency number…"*
Under `RULER-SPEC-v1-r4` §3.1 a trace-flagged refusal gets `u := 0` (`m1_agg.py:30`), so those items
contribute zero mass while still contributing their full reference mass to the denominator.

The cause is a configuration interaction, not a knowledge gap. `arms/searchport/SEARCHPORT.md`
(Addendum 2) defines `SearchPort.Mode {OFF, ON, ON_NO_HEALTH}`: *"AnswerPipeline(plainRetrieve) sends a
turn HealthGate.isHealth reads as health (follow-ups included) through the port-off search and skips
the head pass."* LabRat ships `ON_NO_HEALTH` (`DEVICE-FINAL.md`, "System"). So for exactly the questions
the six text packs cover best — MedlinePlus and first-aid are installed in the 3 GB APK — retrieval is
switched off, the gate finds no source, and the gate's fixed text is a refusal. The record's M2 metric
("53 of 65 safety probes get the fixed safe text") counts this path as a *success*, while on the ruler
the same path is a zero.

I checked the neighbouring explanation: it is not the judge being harsh on declinations. The five texts
were scored (correctness 1, completeness 2, usefulness 2 — the "call emergency services" line earns
something) before the z-override zeroed them; the zero is the spec's, and it is applied correctly.

Cost, stated honestly: health items carry weight 0.5, so fixing all five at the app's median answered
quality moves U-total by only **+0.006**, and at its best-answered quality by **+0.019**. This is not a
headline-moving number. It is a product number: **45 % of the health questions in the ruler are
answered with "I won't", and three of them ("normal resting heart rate", "why do people get altitude
sickness") are the kind of question an offline travel-health app exists for.**

### Why it matters

The record's thesis is "a harness around a small model's real capabilities: health gate, code-computed
arithmetic, pack search and delivery". On the one ruler that is independent of the project, the health
gate is not a capability, it is the failure mode — and it fires hardest where the packs would have
worked. The same mechanism explains a result the record cannot otherwise explain: U on FACT-AVAIL
`AVAILABLE` items (0.143) is *lower* than on `NONE` items (0.159, Opus pooled, `m1.json`), because four
of the nineteen AVAILABLE items are health items that the gate refuses to look at.

### Suggested fix (one line + one protocol already written)

Set the health branch to retrieve first and gate after: `SearchPort.Mode.ON` with
`HealthGate.fixedText` evaluated on the final sources — which is exactly the Addendum-1 configuration
("the head pass + SearchPort.fit run before HealthGate.fixedText, so the gate sees appended sources").
`SEARCHPORT.md` rejected it because of a grounded-dose regression on the 65 probes (9 ungrounded vs 5);
that rule is the right rule, so scope it: keep the gate's hard path for dose/emergency phrasing
(`HealthGate` B+FU terms) and let explanation-type health questions search. Two unit tests already
exist for the mode. Verify with the existing protocol: the 65 probes (grounded-dose rule) plus the 11
ruler health items, and report the pair.

---

## Finding 3 — Two numbers in the published record do not survive a re-read: the win-rate is degenerate by construction, and the pooled CR contradicts its own report

### Evidence

**(a) "0 of 71 wins" carries no information.** `combineOrders`
(`judge-core.mjs:94-98`) keeps a verdict only when both presentation orders agree, else it is a tie.
Against a reference that scores 4.88/5, an answer would have to beat a near-perfect answer twice in a
row; the app wins 0 of 71 under both families and 1 tie. That is the expected output of the design, not
an independent finding, and yet the house citation rule puts it first ("lead with the win-rate",
`llms.txt`) and it is the first clause of F-2238. A statistic that is 0 by construction cannot rank
systems that are all below the ceiling; U can.

**(b) A pooled number the report says is not reported.** `DEVICE-FINAL.md`: *"Pooled CR is not reported
(pooling orders across seeds distorts the ≥4 count)"*. But `aggregates/m1.json` publishes
`pooled.G1.CR = 0.1395` and `correct_per_100 = 14.08`, while the two per-seed values are **0.186** and
**0.178** (18.31 both) — the pooled figure is 21 % lower than either seed, exactly the distortion the
report warns about, and it is the number a reader who loads the JSON will take away. (G2: 0.269 / 0.244
per seed vs 0.168 pooled.)

Also worth one line in the record: `abs_ref` is 3.88/4.0, so `CR`'s denominator — the share of
references scored "correct" (mean correctness ≥ 4) — is ≈ 0.96 and saturates too; CR inherits the same
ceiling problem as U.

### Why it matters

Both are small, but they are the kind of thing that decides whether a reader trusts the rest. The
record's central virtue is that it publishes everything, including the numbers that undercut it; a
non-reported number sitting in a published aggregate, and a headline statistic that is 0 by
construction, are the two places where "publish everything" and "say what it means" came apart.

### Suggested fix

Drop `pooled.CR` / `pooled.correct_per_100` from the aggregate or mark them `do_not_report: true` with
the reason (the report already states it). Replace the win-rate in the headline with "median per-item U
and the count of items above 0.5" (3 of 71 here) and keep 0/71 as a footnote — same honesty, more
signal.

---

## What I could not check

- **The two judge families use one reference family each** (`m1.json` note; F-2238 caveat: "One
  reference family per judge family"). The spec (§3.2, REFVAR) asks for both references per item with
  the mean as the denominator. Both numbers are still below the bar, so no conclusion changes, but the
  "min over families" rule compares two different denominators and two different judges at once; the
  family gap (0.165 vs 0.242) cannot be attributed to judge severity or to reference strength from the
  published files.
- **Stage 1 (DECLINE2STAGE) was not run** on this matrix (`m1.json` note), so the refusal zero rests on
  the app's own trace flag alone; and the three-variant decline arm that §4.1 requires for judge
  validity (`U ≤ 0.05`) exists only on v0.1 dev data with a Haiku judge (bare 0.058 / hedged 0.053 /
  fluent-no-content 0.016), never on v0.4 with Opus or gpt-5.6-sol.
- **Delivery decomposition (H5, §2.4)** — "title retrieved, not correct" vs "not retrieved" — is not
  computable: the phone traces carry a boolean `kept` and no `retrievedTitles`, and no passage text. So
  the claim "coverage 0.90" is the app's own flag, not a verifiable retrieval measurement.
- I did not re-judge anything with a frontier model (no API budget here), so I cannot say how many of
  the 71 judgments are wrong. I sampled all 15 zero-score items by hand: every one is a real factual
  error (time zones, flight durations, pasta at altitude, "hash-based signatures are vulnerable to
  quantum attacks", Inca Trail in February). The judge is reliable at the bottom; the compression is at
  the top.

## Reproduction

```
git clone https://github.com/r4topunk/boar-research && git clone https://github.com/r4topunk/boar-bench
# traces (HF): rnd/research/coordinator/arms/device-final/{judge/dev-s42.opus.judgments.jsonl,
#   judge/dev-s42.codex.judgments.jsonl, traces/dev-s42.traces.jsonl}
python analyze.py   # this file's tables: axis means, per-item U, saturation, health items, CR
```
Script: `analyze.py` in this folder (stdlib only) prints every number quoted above.
