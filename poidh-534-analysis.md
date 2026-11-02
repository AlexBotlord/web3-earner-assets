# The 0.165 is two-thirds a verbosity measurement

**An audit of the DEVICE-FINAL ruler result on bench v0.4 (poidh #534)**
Recomputed from the published judgments, 2026-11-02; every number is reproducible from the cited files.

---

## Finding

I recomputed the headline U-total from the published DEVICE-FINAL judgments and it reproduces (0.173 on seed 42 vs the published 0.165, pooled over seeds 42+43 with the stage-1 zeroing). Split by rubric axis, the composite turns out to be mostly a measurement of one thing: **answer length**.

| axis | app mean (1–5) | reference mean | U on that axis alone |
|---|---|---|---|
| correctness | 2.51 | 4.71 | **0.402** |
| completeness | 1.19 | 4.93 | **0.052** |
| usefulness | 1.31 | 4.99 | **0.080** |
| **composite (U-total)** | 1.67 | 4.88 | **0.173** |

The app answers in a median of **32 words** (max 67; the 512-token cap is never hit, `stopReason: eos` throughout). The reference half is a median of **703 words** (p10 335, max 2863): a **22×** gap. On a 1–5 scale the app's completeness is **1/5 in 127 of 150 judgments and never above 3/5**, while the reference is **5/5 in 140 of 150**; usefulness is 1/5 in 111 of 150.

So two of the three axes are not measuring what the 1.7B knows; they measure how much of a 700-word answer key a 32-word answer covers — precisely what the judge is told **not** to do: *"Do NOT reward length… A short answer that is correct and covers the essentials can win or tie."*

That is not a claim the bar was met, only a claim about what the headline number is: holding today's correctness (U 0.402), reaching 0.50 requires completeness and usefulness at **≈3.16/5 each** (today 1.19 and 1.31). The whole remaining distance sits on the two axes a longer answer moves, and the shipped build deliberately minimises exactly those.

---

## Evidence

**1. The judgments, answers and references agree, and are public.**
`device-final/judge/dev-s42.opus.judgments.jsonl` (150 rows = 75 items × 2 presentation orders) and `device-final/out/df-m1-v04-s42.jsonl` (88 answers, all `outcome: success`, `timedOut: false`, `capHit: false`, `personalityId: "succinct"`), under <https://huggingface.co/datasets/r4topunk/boar-traces/tree/main/rnd/research/coordinator/arms/device-final>. Items (sha256 `f9ad2f2f…`, matching the freeze) in <https://github.com/r4topunk/boar-bench/tree/main/bench/v0.4>; rubric and anti-length instruction in `scorers/vendor/eval-lib/judge-core.mjs`.

**2. The reference half sits at the ceiling, so the denominator carries no signal.**
Over 150 judgments the reference scores 4.71 / 4.93 / 4.99 — completeness never below 4, usefulness never below 4. A denominator that is a constant ≈4.0 per item means U-total collapses to *(app mean − 1)/4*: dynamic range on one side only. The floor was fixed on the numerator side (the v0.4 stage-1 zero, because declining everything scored ≈0.31 raw); the ceiling was not, since the reference is written by the same model family that judges it.

**3. The decisive control exists in the record — on the previous ruler, never on this one.**
X-108 / F-467 (<https://r4topunk.github.io/boar-research/data/experiments.json>): re-judging the *same answers* against references condensed to ≤80 words lifted the deep tier **0.412 → 0.514** (+0.102, CI 0.456–0.578, Opus, n=51) — the only configuration in the record that ever crossed the 0.50 bar, and it crossed it by aligning reference length. The v0.4 ruler, which carries the headline claim, kept uncapped references and never ran that arm. The record's read-out is *≈17 % of the gap is length* — measured against ~280-word references, not the 703-word ones used in the headline.

**4. The choice that sets the most-depressed axis was made under a judge the record does not use for headlines.**
Succinct was adopted on X-330 (1.7B: Succinct 0.263 vs Detailed 0.224; Δ +0.038, CI −0.005…+0.084) and X-373 (1/3/5 paragraphs → U 0.228/0.233/0.218; unsupported-fact rate 0.33/0.50/0.52) — **both judged by Claude Haiku**, on 51 and 27 development items, while the measurement chapter documents that Haiku compresses paired gaps to 0.70–0.95× of Opus with κ 0.49 on "correct" verdicts (F-996, F-2083). The **only** length-sensitivity measurement under the headline judge is X-326: a non-preregistered within-item slope over 13,310 rows giving **+0.31 ratio per doubling of length for the 1.7B under Opus**, and "no length reward" at ≥4B. The record reads X-326 as reassurance ("Succinct not penalised at ≥4B") while its own number says the 1.7B *is* penalised; it does not reconcile the two.

---

## Why it matters

The conclusion "the bar was not reached" (lines closed 2026-10-23) is stated as a property of the engine; on the published data two-thirds of its weight is a property of the output budget.

- **`0 of 71 wins` is not evidence about the model.** A pairwise comparison cannot yield a tie when one answer is 1/5 and 4/5 on two axes: under Opus, **0 ties in 150 judgments**; under gpt-5.6-sol, 1 tie and 1 win. The win rate is a deterministic function of the length gap and adds nothing beyond U.
- **The composite contradicts the record's own metric discipline.** The record forbids comparing its three metric families, then applies one 0.50 bar across them. On the old ruler the deep tier's correctness-only floor-adjusted score was 0.660 (above the bar) against a composite of 0.436; on v0.4 the same split is 0.402 against 0.173.

## Concrete fix

Two arms, ~300 Opus calls, both pre-registerable today:

1. **Length-matched reference arm (no app change).** Re-judge the same 88 published answers against the ≤80-word reference halves (tooling and protocol exist: X-108). This turns "22× terser" into a measured term and is the only way to state a bar result at matched verbosity.
2. **The arm that decides it.** App-side, one config: Detailed/3-paragraph persona, `DEEP_CONTEXT_TOKENS 1200`, `DEEP_MAX_TOKENS 400` (already implemented — X-091, X-324), 71 items × 2 orders, seed 42, same judge and references, **with the citation-support step enabled** (F-2232 notes it is skipped, so the measured engine is the one showing unsupported text). Pre-register a gate, not a trade: the arm counts only if completeness and usefulness each reach **≥3.2/5** while correctness stays inside its CI — X-373 shows the unsupported-claim rate rising from 0.33 to 0.50 between one and three paragraphs, so the naive version will lose correctness faster than it gains coverage.

Either way, print the three axes next to the composite. A ratio averaging 0.40 with 0.05 and 0.08 should not be the only number a reader sees.

## What I could not verify

- **I ran neither arm.** No Opus/Codex access here, and re-judging is out of scope for a claim: arm 1 is a prediction about sign and rough size, grounded in X-108.
- **My 0.173 reproduces, it does not correct.** One seed (42), 71 headline items, health weight 0.5, no stage-1 zeroing; the published 0.165 pools seeds 42+43 with `DECLINE2STAGE`, and I did not reconcile the 0.008.
- **The staged judge input is not published.** The ruler was judged against `work/v04/bench/questions.jsonl` (`questionsSha256` `fc39b032…`), built by `mk_v04.py` in boar-research, which maps each item's `checklist` to the judge's `rubric` field — so the notes reached the judge, but I cannot confirm it from the artifacts. A third party re-running today from `boar-bench` gets the opposite: neither `judge.mjs` (line 128) nor `judge-codex.mjs` (line 194) reads `checklist`, and `bench/v0.4/` ships no `questions.jsonl`, so a naive copy silently feeds **"Author notes…: (none)"**. Fix: accept `q.checklist` as a fallback in both adapters and publish the staged file beside the items — a reproduction defect, not the cause of the published number.
