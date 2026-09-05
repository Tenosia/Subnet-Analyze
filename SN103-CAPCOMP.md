# SN103 — Capcomp / "LoRA Merger" (Capability Composition Subnet)

| | |
|---|---|
| **netuid** | 103 (`Capcomp`, symbol `Ա`) |
| **Operator brand** | LoRA Merger — the Capability Composition Subnet |
| **Owner hotkey** | `5E529AKMrdch2BnzYNuNxYSY6m1GNrxAcEqD6Pm3vy8SbwGV` (holds **UID 0**) |
| **Owner coldkey** | `5H3SQ4du9ThumJcUQb1VL2dixRBDKtt8hDRWLyPuANhHon7Y` |
| **Registered at block** | 8,762,380 |
| **Code (public protocol)** | https://github.com/Capcomp-AI/capability-composition-subnet |
| **Code (engine, operator-only)** | https://github.com/Capcomp-AI/lora-merger-engine — *not public* |
| **Submission API** | `https://api.capcomp.ai` (the **only** way into a run) |
| **Site** | https://www.capcomp.ai |
| **Local checkout** | `/tmp/claude-0/-root/c0422a1e.../scratchpad/capcomp` @ `9bdde88` |
| **Package version** | `capability-subnet` 2.0.0, spec `RECIPE_SCHEMA_VERSION = 1` |
| **Live state (2026-08-27, block 8,938,546)** | run **416**, 1079 blocks in, ~20.4 h left |
| **Price** | 0.009000 TAO/α · tao_in τ739.15 · alpha_in 82,123 α · alpha_out 198,269 α |
| **UIDs** | 87 registered, **8 earning**, 5 validator permits |
| **Registration cost** | **1.000 TAO** recycle (~$256 at TAO ≈ $256) |

> Data pulled live from finney + `api.capcomp.ai` on 2026-08-27. Where the docs
> and the code/chain disagree, the code and chain are recorded as authoritative
> and the disagreement is flagged.

---

## 1. Goal of the subnet

There are thousands of public LoRA adapters trained on the same base models.
Which **combination** of them, merged how, actually finishes a given task better
than any single one — that decision is currently made by intuition.

SN103 turns that decision into a measured competition. It pins one base model
(**Qwen3-8B**, revision `b968826d9c46dd6066d109eabc6255188de91218`), one frozen
pool of **30 certified rank-64 LoRA adapters**, and one evaluation arena. Miners
submit a **declarative JSON merge recipe**. The network reconstructs the merge
deterministically, serves it, scores it on hidden instances, and pays whoever
produced the best package.

The product is *not* a benchmark score — it is a deployable artifact: one merged
adapter file under 500 MB that runs on a single card, with a published,
replayable evaluation record.

**What the subnet is honestly built to discover**, in its own words, is whether
composition helps *at all*. The untouched base model sits on the board
permanently so the network can conclude "no" rather than pay miners to avoid
concluding it.

---

## 2. What you do as a miner

You submit **one JSON document**. Nothing else. You never serve inference, never
run a process the network talks to, never write to chain, and pay no
transaction fee.

```jsonc
{
  "schema_version": 1,
  "workflow_id": "lora_merger_logic_v1",
  "base_revision": "b968826d9c46dd6066d109eabc6255188de91218",
  "source_snapshot_sha256": "sha256:e88c04...",       // from `capcomp pool`
  "selected_adapters": ["action-planner-v1", "code-generation-v1", ...],  // 2–10
  "merge":       { "combination_type": "svd", "random_seed": 0 },
  "global_weights": { "action-planner-v1": 1.683, ... },                  // −2.0 … 2.0
  "layer_group_overrides": { "group_2": { "code-generation-v1": 0.089 } },
  "compression": { "output_rank": 8, "svd_clamp_quantile": 1.0 },
  "output":      { "dtype": "bfloat16", "adapter_name": "candidate" }
}
```

Every field is a bounded number, an enum, or a name from a frozen registry — which
is why the engine can rebuild it without ever executing miner code.

### The loop

```bash
pip install -e ".[miner]"                       # miner extra pulls torch/transformers
capcomp pool                                    # frozen pool + snapshot digest + layer ranges
capcomp init --out recipe.json                  # skeleton (or --random)
#   ... your private search goes here — this is the entire competition ...
capcomp validate --recipe recipe.json           # exact admission checks + advisories
capcomp size     --recipe recipe.json           # predicted artifact bytes
capcomp check    --recipe recipe.json           # ask the ENGINE if it would admit — free
capcomp timing   --block <current>              # which run measures this
capcomp submit   --recipe recipe.json --wallet.name <ck> --wallet.hotkey <hk> --confirm
capcomp status   --wallet.name <ck> --wallet.hotkey <hk>
```

Submission is a signed HTTP POST — you sign the exact string
`capcomp-submit:v1:<run_id>:sha256:<hex>`:

```
POST https://api.capcomp.ai/submit
{"hotkey": "5…", "recipe": "<recipe JSON bytes>", "signature": "0x…"}
```

**On-chain commitments are dead.** The engine does not read them. If
`capcomp submit` did not return success, you are not in the run — and you get no
error anywhere else.

### The three-run pipeline

| | |
|---|---|
| run **N** | you submit |
| run **N+1** | it is evaluated, score recorded |
| run **N+2** | that score sets weights on-chain; your recipe becomes **public** |

A run is **7200 blocks = 24 h**, anchored: run 412 opened at block 8,908,667
(≈12:00 Eastern, 23 Aug 2026), every run since opens 24 h later. So boundaries
land at ~noon Eastern daily.

- **3 submissions per run**, only the **last** is measured. Identical resend is free.
- Submissions are **refused (409)** in the last **300 blocks (~1 h)** of a run.
- **Do not replace your recipe once the run you submitted in has closed** — sending
  a new one during run N+1 re-files it under N+1, so N+1 measures nothing from
  you and you lose a full day.
- Max recipe size 256 KB. `401` bad signature, `403` not registered, `429` out of attempts.

---

## 3. Scoring logic

### 3.1 Hard gates — a failure means grade `null`, no rank, no pay

| Gate | Requirement | Live behaviour |
|---|---|---|
| `artifact_size` | ≤ 500 MB (`524288000`) | never bound — rank 8 = 43.7 MB |
| `sample_sufficiency` | ≥ 20 valid instances | never bound (1350/1350) |
| `agent_limits` | ≤ 12 turns, ≤ 8192 output tokens | never bound (1 turn, 1024 tok) |
| `safety` | 0 critical unsafe actions | never bound on this workflow |
| `stage_floors` | every critical stage above floor | never bound |
| **`base_retention`** | **≥ 0.95** vs base model on a 40-item probe | **binds constantly** |
| **`baseline`** | **e2e ≥ reference + 0.02** | **binds constantly** |

In run 414 (25 candidates) these two gates eliminated **18 of 25**:

- **13 failed retention.** Values are quantised — the base model answered 31 of
  the 40 probe items, so retention = *your correct*/31. Observed values are
  exactly `30/31 = 0.968` (pass), `29/31 = 0.935` (fail), `28/31 = 0.903` (fail).
  **You may lose at most ONE probe item.** That is the single biggest killer in
  this subnet.
- **5 more failed the baseline gate** (reference e2e was 0.1119, so you needed
  e2e ≥ 0.1319).

I reproduced the qualification set exactly with `retention ≥ 0.95 AND e2e ≥ 0.1319`
— it accounts for all 25 rows with no exceptions.

### 3.2 The qualified score (quality)

```
qualified = 0.55·end_to_end + 0.15·stage_balance + 0.10·ood
          + 0.10·token_efficiency + 0.05·retention + 0.05·artifact_efficiency
```

`stage_balance` is the **geometric mean over the 12 capability axes**, floored at
`STAGE_BALANCE_EPSILON = 1e-3` per axis. Geometric, so it punishes gaps instead
of averaging them away.

### 3.3 The grade (what ranking and the throne use)

```
grade = 0.50·qualified + 0.40·improvement + 0.10·token_efficiency
improvement = clamp01( (e2e − reference_e2e) / (1 − reference_e2e) )
```

**Worked example — the run-414 champion, UID 84:**

```
qualified    = 0.3081
improvement  = (0.15481 − 0.1119) / (1 − 0.1119) = 0.04296 / 0.8881 = 0.04837
cost         = token_efficiency = 1.0000
grade        = 0.50(0.3081) + 0.40(0.04837) + 0.10(1.0)
             = 0.15405 + 0.019348 + 0.10 = 0.27340
```
Engine reported **0.2733875**. ✔ Formula confirmed.

I also reproduced `stage_balance` exactly for six candidates from the published
per-axis vectors (e.g. UID 84: computed 0.047310 vs reported 0.047310). The
published scoring is genuinely re-derivable — this subnet's auditability claim
holds up.

### 3.4 Taking the throne, and whether the run pays at all

The run's best candidate takes the throne by exceeding the reigning champion's
grade by **`CHAMPION_DETHRONE_MARGIN = 0.0005`**.

**That single test also decides whether anyone is paid.** If the leader cannot
clear it, the entire miner share burns — second place does not inherit a run its
leader did not win.

### 3.5 Marginal value of every lever

Derived from the weights above at the live reference (0.1119):

| Lever | Δgrade per +0.01 absolute | × dethrone margin |
|---|---|---|
| **`end_to_end`** | **0.007254** | **14.5×** |
| `token_efficiency` | 0.001500 | 3.0× |
| `stage_balance` | 0.000750 | 1.5× |
| `ood` | 0.000500 | 1.0× |
| `retention` | 0.000250 | 0.5× |
| `artifact_efficiency` | 0.000250 | 0.5× |

`d(grade)/d(e2e) = 0.7254`. One extra correct instance out of 1350 =
**0.000537 grade = 1.07× the dethrone margin.** The throne moves on roughly
**one question**.

---

## 4. Live competition landscape

### 4.1 Run 414 leaderboard (submitted 414 → measured 415 → paid 416)

Reference (base model) e2e = **0.1119**. Reigning grade 0.272824, champion 0.273388.

| rk | uid | verdict | grade | e2e | stg-bal | ood | ret | tokEff | artEff | MB | method | rank | #ad |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 84 | **dethrone** | 0.27339 | 0.1548 | 0.0473 | 0.200 | 1.000 | 1.0000 | 0.9166 | 43.7 | `svd` | 8 | 6 |
| 2 | 78 | held | 0.27273 | 0.1593 | 0.0464 | 0.140 | 0.968 | 1.0000 | 0.9166 | 43.7 | `svd` | 8 | 5 |
| 3 | 72 | held | 0.27167 | 0.1563 | 0.0368 | 0.160 | 1.000 | 1.0000 | 0.9166 | 43.7 | `svd` | 8 | 6 |
| 4 | 77 | held | 0.27094 | 0.1548 | 0.0387 | 0.180 | 0.968 | 1.0000 | 0.9166 | 43.7 | `svd` | 8 | 6 |
| 5 | 83 | held | 0.27054 | 0.1541 | 0.0473 | 0.170 | 0.968 | 1.0000 | 0.9166 | 43.7 | `svd` | 8 | 6 |
| 6 | 14 | held | 0.23053 | 0.1341 | 0.0191 | 0.130 | 0.968 | 0.8574 | 0.9166 | 43.7 | `svd` | 8 | 3 |
| 7 | 60 | held | 0.22956 | 0.1319 | 0.0301 | 0.180 | 0.968 | 0.8529 | 0.8334 | 87.4 | `svd` | 16 | 2 |
| — | 18 others | **gate fail** | — | 0.117–0.138 | | | 0.903–1.000 | | | | | | |

**Note UID 78:** highest e2e in the field (0.1593) and still lost the throne — its
`ood` was 0.140 vs the champion's 0.200 and retention 0.968 vs 1.000. e2e alone
does not win.

### 4.2 Throne history

| run | champion | grade | submissions | qualified |
|---|---|---|---|---|
| 411 | UID 60 (`5CiNSUWysg…`) | 0.26097 | 40 | 9 |
| 412 | UID 78 (`5C5NmF8MRf…`) | 0.26319 | 10 | 5 |
| 413 | UID 78 (`5C5NmF8MRf…`) | 0.27282 | 21 | 10 |
| 414 | UID 84 (`5FkGUm2LKz…`) | 0.27339 | 25 | 7 |

The throne has changed hands in **4 of the last 4 runs** and the run has paid
every time. Grade is creeping: 0.261 → 0.263 → 0.273 → 0.273. Only **25–40 %** of
submissions qualify.

### 4.3 Current queue

- Run **415**: 36 submissions (reveals in run 417)
- Run **416** (open now): 8 submissions so far

Submission counts are rising — 10 → 21 → 25 → 36. The field is getting busier.

### 4.4 The 12 axes — where the score actually is

Champion UID 84's per-axis vector:

| axis | UID84 | UID78 | UID60 |
|---|---|---|---|
| `format_compliance` | 0.6993 | 0.6881 | 0.7168 |
| `boolean_expressions` | 0.4103 | 0.3846 | 0.3056 |
| `code_execution` | 0.3186 | 0.3375 | 0.3054 |
| `word_sorting_mistake` | 0.2553 | 0.2872 | 0.1900 |
| `word_sorting` | 0.1748 | 0.1748 | 0.1226 |
| `zebra_puzzle` | 0.0579 | 0.0496 | 0.0000 |
| `goods_exchange` | 0.0388 | 0.0485 | 0.0244 |
| `cipher` | 0.0326 | 0.0435 | 0.0392 |
| `object_counting` | 0.0211 | 0.0105 | 0.0400 |
| `time_sequence` | 0.0200 | 0.0200 | 0.0094 |
| **`arrow_maze`** | **0.0000** | **0.0000** | **0.0000** |
| **`web_of_lies`** | **0.0000** | **0.0000** | **0.0000** |

**Two axes are dead for the entire field.** They are floored at 1e-3 inside the
geometric mean, which is why every stage_balance is stuck around 0.03–0.05.

### 4.5 The current meta (from the 25 published run-414 recipes)

Total convergence at the top:

- **All 7 qualifiers used `combination_type: "svd"`.** No TIES, no DARE, no linear
  in the money. (`dare_ties_svd` appears 3× — all failed. `linear` 1× — failed.)
- **All top 6 used `output_rank: 8`.** Rank 8 → 43.7 MB → `artifact_efficiency`
  0.9166. Rank 16 → 87.4 MB → 0.8334, a 4.2× dethrone-margin handicap before
  anything else.
- **All used `svd_clamp_quantile: 1.0`** (clamping disabled).
- Top 5 selected **5–6 adapters**; the 2–3 adapter recipes all landed rank 6+ or
  failed.
- **All 25 used `layer_group_overrides`** — per-depth coefficients are table stakes.
- Top 5 all hit **`token_efficiency = 1.0000`** (saturated), so it is no longer a
  differentiator at the top.

Champion-class recipes use **small, asymmetric coefficients** — e.g. UID 72:
`action-planner-v1: 1.683`, `qwen3-8b-test-v1: 0.3005`,
`code-generation-v1: 0.009`, two adapters at `0.0`, plus group-3 override
`qwen3-8b-test-v1: 1.2`. Note adapters carried at weight **0.0** globally and
revived only at specific depths — that is the discovered trick.

### 4.6 The adapter pool (30, frozen)

**9 with declared capability:** `structured-explanation-v1` (structured_output),
`action-planner-v1` (tool_calling), `code-generation-v1` (python_code_generation),
`embedded-engineering-v1` (technical_domain_language), `industrial-ifc-v1`
(industrial_asset_schema), `chained-reasoning-v1` (fault_reasoning),
`parallel-reasoning-v1` (general_reasoning), `constrained-selection-v1`
(resource_decision), `document-extraction-v1` (structured_log_extraction).

**3 declared distractors** (selectable on purpose, `validate` warns):
`general-instruction-v1`, `creative-writing-v1`, `legal-citation-v1`.

**18 marked `unmeasured`** — and this is where the alpha is. `qwen3-8b-test-v1`
and `qwen3-8b-stateless-knapsack-lora-seed7-v1` are both "unmeasured" and both
appear in the top recipes. Nobody has published what the other 16 do.

---

## 5. Miner economics

Subnet emits **1.000 α/block = 7200 α/day**. Split: 18 % owner cut, 41 % miners,
41 % validator dividends → **miner pool = 2952 α/day**.

At α = 0.009000 TAO and TAO ≈ $256:

| Rank | Weight | α/day | TAO/day | USD/day | USD/month |
|---|---|---|---|---|---|
| **1st (throne)** | 0.450 | **1328.4** | **11.96** | **~$3,061** | **~$91,800** |
| 2nd | 0.025 | 73.8 | 0.664 | ~$170 | ~$5,100 |
| 3rd | 0.015 | 44.3 | 0.399 | ~$102 | ~$3,060 |
| 4th | 0.005 | 14.8 | 0.133 | ~$34 | ~$1,020 |
| 5th | 0.0025 | 7.4 | 0.066 | ~$17 | ~$510 |
| 6th–10th | 0.0025 total | 7.4 total | 0.066 | ~$17 total | ~$510 total |
| **"Burn" → owner UID 0** | 0.500 | 1476.0 | 13.29 | ~$3,401 | — |

Verified against chain: UID 84 `E = 66.42 α/tempo × 20 tempos/day = 1328.4 α/day`. ✔
Every rank reconciles exactly.

> ⚠️ **Update, 2026-09-03.** The live incentive vector is now
> `0.90 / 0.05 / 0.03 / 0.01 / 0.005 / tail` — the `RANK_SHARES` ladder applied to a
> **full** miner pool — and UID 0's incentive is **0.0000**. `BURN_SHARE` is therefore
> effectively **0 on the live network**, while `constants.py:641` still reads `0.50`.
> Rank 1 now takes **90 % of the miner pool, not 45 %**: 2,656.8 α/day, ≈ $9,129/day at
> that date's α price. The owner's 50 % burn stream is gone; its capture is now the
> 18 % cut plus validator dividends (55.2 % of emission in total). The champion also
> changed hands again — UID 77 now holds the throne, not UID 84.

**This is a winner-take-all subnet.** Rank 1 pays **18× rank 2** and **180× rank 4**.
Ranks 2–10 combined are 5 % of the miner pool. Placing is information, not income.

### Costs

| Item | Cost |
|---|---|
| Registration (recycle) | **1.000 TAO ≈ $256**, one-off per hotkey |
| Recipe building / validation | ~$0 — any laptop |
| Reconstruction only (CPU) | ~32 GB RAM box, ~$30–60/mo |
| **Serious local evaluation** | 1× 32–48 GB GPU (A6000 / L40S / 5090) — **~$0.5–1.2/h rented ≈ $360–870/mo** |
| Search at scale | multi-GPU; this is where the contest actually is |

### Liquidity caveat

`alpha_in` is only **82,123 α** against `tao_in` **τ739**. Winning the throne
mints **1328 α/day = 1.6 % of pool depth per day**. Realised proceeds will be
materially below the $3,061/day mark-to-market figure if you sell daily, and
you would be a significant fraction of `subnet_volume` (13,174 α).

### Owner capture

| Stream | α/day |
|---|---|
| Owner cut (18 %) | 1296.0 |
| 50 % miner-share "burn" → owner UID 0 | 1476.0 |
| Validator dividends (UID 0 holds 92.83 % of dividend weight) | 2740.3 |
| **Total to owner hotkey** | **5512.3 α/day = 76.6 % of all subnet emission** |

The "burn" **is not a burn.** `chain.py::owner_uid` and `docs/validator.md` are
explicit: burned emission is routed to *the subnet owner's UID*, resolved from
the metagraph. On chain, UID 0 = the owner hotkey and carries `I = 0.499992`.
The subnet is transparent about this in code, but the README's word "burns"
reads as destruction and is not.

---

## 6. How to become the king

The top 5 grades in run 414 spanned **0.00285** total, and the dethrone margin is
**0.0005**. You do not need a breakthrough — you need to reliably clear a bar you
are already near. Ranked by expected value:

### Priority 1 — Attack the two dead axes. This is the biggest unclaimed edge.

`arrow_maze` and `web_of_lies` are **0.0000 for the entire field**, floored at
1e-3 inside a 12-way geometric mean. Because the mean is geometric, lifting a
floored axis is worth far more than the same gain on a healthy axis.

Computed from the champion's actual per-axis vector:

| lift `arrow_maze` to | new stage_balance | Δgrade | × dethrone margin |
|---|---|---|---|
| 0.01 | 0.05732 | 0.00075 | **1.5×** |
| 0.02 | 0.06073 | 0.00101 | **2.0×** |
| 0.05 | 0.06555 | 0.00137 | **2.7×** |
| 0.10 | 0.06944 | 0.00166 | **3.3×** |
| **both** dead axes to 0.05 | 0.09081 | 0.00326 | **7×** |
| **both** dead axes to 0.10 | 0.10193 | 0.00410 | **8×** |

Each family gets ~101 of the 1350 instances. **One single correct `arrow_maze`
answer** (1/101 = 0.0099) is worth ≈1.5× the dethrone margin — more than the
entire gap between rank 1 and rank 2. Find an adapter combination or a
depth-weighting that makes the model produce *anything* valid on these two
families and you take the throne.

Start by measuring, for each of the 30 adapters alone and each pair, its
`arrow_maze` / `web_of_lies` pass rate on the public corpus. Nobody in the
published record has done this.

### Priority 2 — Copy the meta baseline exactly, then search around it.

Non-negotiable starting configuration, from what actually qualified:

- `combination_type: "svd"` — every qualifier used it
- `output_rank: 8` — 43.7 MB, best artifact_efficiency, and it correlates with
  passing retention (small update = less base damage). Rank 16 costs you 4.2×
  the dethrone margin before you start.
- `svd_clamp_quantile: 1.0`
- 5–6 adapters, not 2–3
- heavy use of `layer_group_overrides`, including adapters at global weight 0.0
  revived at one depth

### Priority 3 — Never fail the retention gate.

You may lose **one** of 31 probe items. 13 of 25 candidates died here. Practical rules:

- Keep `output_rank` low and total update magnitude small.
- Avoid negative coefficients (the docs flag their interaction with this gate,
  and no qualifier used one).
- The probe is general instruction-following — arithmetic, ordering, exact
  formats, answering in the language addressed — **not** the workflow. Test it
  separately. Carry a "retention anchor" adapter.
- Retention is only worth 0.5× margin as a *score*, but it is infinite as a *gate*.

### Priority 4 — Then push `end_to_end`, then `ood`.

e2e is 14.5× the margin per point and is the dominant term. But at the top
everyone is at 0.154–0.159, so the realistic increments are ~1–3 instances.
`ood` (100 instances/run) is the live tiebreaker — it is what won UID 84 the
throne over UID 78's higher e2e. A 0.06 ood swing was worth 6× the margin.

### Priority 5 — Submit every single day, without fail.

Run-to-run variation on identical artifacts is ~0.017 e2e ≈ **0.012 in grade** —
**24× the dethrone margin.** The constants file admits this outright: *"nothing
here establishes that the spread is below 0.0005."* The top five are within
0.0028 of each other, well inside the noise.

**Consequence:** once you are in the top cluster, the throne is substantially a
daily lottery, and each ticket is worth ~$3,061. A miner in the top cluster who
submits 30 days a month has ~30 draws; one who submits 10 days has ~10. Automate
the daily resubmit and never miss a boundary.

### The path

1. Register a hotkey (1 TAO). Immunity applies; you are not deregistered for losing.
2. Rent one 48 GB GPU. Pull the pinned Qwen3-8B + the 30-adapter pool (~9 GB).
3. Build the local eval harness (`miner/local_eval.py`) and the public pack
   (`generate-public-pack`, 120 instances). **Use far more than 120 instances** —
   the docs warn 20 cannot distinguish similar recipes; you need hundreds.
4. Reproduce the meta baseline (svd / rank 8 / 6 adapters / layer overrides).
   Confirm you clear retention and e2e ≥ ref + 0.02 locally.
5. Run the per-adapter and per-pair sweep specifically on `arrow_maze` and
   `web_of_lies`. This is the differentiated work.
6. `capcomp check` (free, engine-side), then submit — daily, early in the run,
   never inside the last 300 blocks.

---

## 7. Rules you must keep

| Rule | Consequence if broken |
|---|---|
| Submit via `capcomp submit` / `POST /submit` only | On-chain commitment is silently ignored — no error, no row, no pay |
| ≤ 3 submissions per run; only the last measured | `429`, attempt refused |
| Do not submit in the last 300 blocks of a run | `409`, nothing stored, no attempt spent — you skip a day |
| Do not resubmit during the run that is measuring you | You withdraw the submission about to be judged and lose a full day |
| 2–10 adapters, from the frozen snapshot only | Rejected at admission |
| `source_snapshot_sha256` must match the current pool | Rejected — built against a pool that no longer exists |
| Coefficients within −2.0 … 2.0 | Schema rejection |
| `output_rank` ∈ {8,16,32,48,64,96,128}; **128 ≈ 666 MB** | Legal schema value, automatic evaluation rejection (>500 MB) |
| No unknown fields, no executable content | Rejected outright |
| Do not supply `density` to a method that ignores it | Error, not a silent ignore |
| Retention ≥ 0.95 (lose ≤ 1 of 31 probe items) | Grade `null`, no rank, no pay |
| e2e ≥ reference + 0.02 | Grade `null`, no rank, no pay |
| Leader must clear champion grade + 0.0005 | **Entire miner pool burns for that run** |
| Anti-copy vs every prior submission | Rejected |

---

## 8. Device / hardware conditions

### Miner (`min_compute.yml`)

| | Minimum | Recommended |
|---|---|---|
| CPU | 8 cores @ 2.5 GHz | 16 cores |
| **GPU** | **not required** — `required: false` | 32 GB VRAM min if used, 48 GB rec, CC ≥ 8.0 |
| RAM | 32 GB | 64 GB |
| Disk | 250 GB SSD, 1000 IOPS | 500 GB |
| Net | 200 ↓ / 50 ↑ Mbps | |
| OS | Ubuntu 22.04 | |

Practical tiering:

| What you're doing | What you need |
|---|---|
| Build + validate + submit recipes | **Any machine** — a $5 VPS is enough |
| Reconstruct an artifact | ~32 GB RAM; GPU optional but **~30× faster** on trimming methods |
| Evaluate locally | GPU that fits the **24 GiB serving reservation** → 32 GB card minimum |
| Search seriously | As many GPUs as you want to spend — this is the competition |

> **Against your BEAM box (46.225.140.58, 2 cores / 3.7 GB):** it can build,
> validate, sign and submit recipes and run `capcomp check`/`timing`/`status`
> indefinitely. It **cannot** reconstruct an artifact (needs ~32 GB RAM) and
> **cannot** evaluate locally. You would be submitting blind. That is survivable
> for rank 6–10 tail money (~$3–8/day) but hopeless for the throne. A separate
> rented 48 GB GPU box is required to compete.

### Validator

| | |
|---|---|
| GPU | **4 × 32 GB minimum** (RTX 5090 class), 8 recommended — enforced by `MIN_VALIDATOR_CARDS=4`, `MIN_VALIDATOR_CARD_GIB=32` |
| CPU | 16 cores min, 32 rec (merges are pinned single-thread; cores = throughput) |
| RAM | 64 GB min, 128 rec |
| Disk | 120 GB min (base ~16 GB + pool ~9 GB) |
| Install | `capability-subnet[merge]` |

A validator **refuses to start** below the floor rather than scoring every miner
zero for its own missing hardware. There is **no lightweight mode** —
`--neuron.evaluation` defaults to `own`, where the validator rebuilds, serves and
scores every candidate itself. Serving is pinned at `gpu_memory_utilization`
0.78 on a 32 GB card / 0.50 on 48 GB, `max_model_len` 8192, batch concurrency 32,
temperature 0, **thinking channel off**.

> ⚠️ **Doc conflict:** the capcomp.ai website states validators need "a small VPS,
> no GPU required." The repo, `min_compute.yml` and enforced protocol constants
> all say 4 × 32 GB GPUs. **The code is authoritative — the website is wrong.**
> The GPU-free path is only `capability-audit` (replaying a closed run from
> published traces), which is auditing, not validating.

### Auditor (anyone)

No GPU, no registration: `capability-audit run --run <n>` and
`capability-audit replay --run <n>`.

---

## 9. Third-party conditions

| Dependency | What it is | Failure mode |
|---|---|---|
| **`api.capcomp.ai`** | Operator-run submission service. **The only way into a run.** | **Single point of failure.** Down = nobody can submit; there is no on-chain fallback (commitments are explicitly not read). `503` = chain unreachable, retry. |
| **`lora-merger-engine`** | The evaluation engine. **Private, operator-only repo.** | You cannot inspect or run the scheduler, serving, store or hidden-seed handling. You audit its *output*, never its *operation*. |
| **Hugging Face** | Base model `Qwen/Qwen3-8B` @ `b968826d9c46…` (Apache-2.0); all 30 adapters; both corpora | HF outage or repo/revision takedown blocks pool import, local eval, and validator instance regeneration. All pinned to immutable revisions, which mitigates mutation but not deletion. |
| **`AffineFoundation/affine-lgc`** @ `19765edac477` | Logic corpus, 81,566 puzzles → ~3,193 used | **Public.** The hidden seed protects *which items* a run draws, not the items. Selection band `avg@16_qwen3_4b_instruct_2507` ∈ [0.20, 0.80]. |
| **`AffineFoundation/rl-python`** @ `0cc711b1f059` | Code corpus, ~2,944 problems → 25 % of every run | **Public**, same caveat. Scored by execution in an isolated interpreter (`-I -S`, no env, ≤32 cases/problem, 20 s ceiling). |
| **vLLM / SGLang** | Serving the merged package | Serving failure is an *infrastructure* outcome — you are not scored down, you are simply not measured. |
| **PyTorch ≥ 2.2, safetensors, PEFT-compatible format** | Reconstruction | SVD is **not bitwise reproducible across devices** (LAPACK vs cuSOLVER); the network compares outcomes, not hashes. |
| **Docker ≥ 24.0** | Sandbox tool services (`docker-compose.sandbox.yml`) | Engine/backend only. |
| **PostgreSQL** (`psycopg`) | Hidden snapshot for `industrial_maintenance_de_v1` SQL stage | Only for the non-default maintenance workflow. |
| **`bittensor >= 11.0, < 12`** | Chain SDK | ⚠️ Your `/root/beam/.venv` has **bittensor 10.5.0** — incompatible. Capcomp needs its **own venv**. |
| **finney chain** | Identity, registration, weights, run anchoring | Run boundaries are derived from block height at 12.0029 s/block; drift ~21 s/day. |
| **Hidden seed root** (`CAPSUB_HIDDEN_SEED_ROOT`) | Operator secret controlling instance draw | **Explicitly "NOT DEFENDED"** in the project's own honest-limits page: an operator choosing one seed root dishonestly at genesis is not caught. An eventual reveal is "planned". |

---

## 10. Risks

1. **The submission API is a single centralised chokepoint.** No on-chain
   fallback exists by design. If `api.capcomp.ai` is down when a run opens, or the
   operator declines your submission, you have no recourse and no evidence.

2. **The evaluation engine is closed source.** The scoring *rules* are public and
   genuinely re-derivable (I verified grade and stage_balance to 5 decimals) —
   but the *engine that executes them*, including hidden seed generation and
   candidate scheduling, is private.

3. **Genesis seed-root choice is undefended.** The project states this itself. A
   dishonestly chosen root at genesis is not detectable today.

4. **The dethrone margin is far below measurement noise.** Margin 0.0005;
   run-to-run variation on *identical artifacts* ≈ 0.017 e2e ≈ 0.012 grade — **24×
   the margin**. `constants.py` concedes: *"nothing here establishes that the
   spread is below 0.0005. If a throne starts changing hands on reruns rather than
   on new submissions, that is the thing to measure."* Top-5 grades span 0.00285.
   **A large part of who wins $3,061/day is currently noise.**

5. **The reference moved mid-run, and the published gate details contradict the
   verdicts.** In run 414, candidates submitted before block ~8,926,000 were
   gated against reference 0.112; later ones against 0.117 — a 0.005 shift, 25 %
   of the required 0.02 margin, purely as a function of *when you submitted*.
   Worse, the published `gates` array marks `baseline: passed=false` for UIDs 14
   and 60 while `verdict_reason` says "cleared every gate" and both were ranked
   and paid. UID 75 failed only that same gate and was excluded. The authoritative
   value is the top-level `reference_e2e = 0.1119`; the gate-detail strings are
   rendered against a different, later measurement. **The published record is
   internally inconsistent.**

6. **Owner captures 76.6 % of all emission** (18 % cut + 50 % "burn" to owner UID
   + 92.8 % of validator dividends). The "burn" is a transfer to the owner, not
   destruction. Miners split 23.4 %, and one miner gets 18.4 % of that.

7. **Extreme winner-take-all.** Rank 1 = 18× rank 2. Ranks 2–10 combined = 5 % of
   the miner pool. If you are not taking the throne you are earning $17–170/day
   against $360–870/mo of GPU cost — **structurally loss-making**.

8. **The whole run can pay zero.** If no candidate clears champion + 0.0005, the
   entire miner share burns. Hasn't happened in runs 411–414, but as grades
   plateau (0.273 → 0.273) it becomes likelier.

9. **The subnet's core premise is unproven by its own admission.** From
   `references.py`: the best-single-adapter reference was **removed** for card
   time. On a 250-item benchmark the best single adapter scored 0.132 vs base
   0.100, and *"no merge has beaten it."* On the run-411 draw the strongest
   challenger scored 0.1496 against a scaled specialist near 0.150 — *"that
   challenger clears the base by a wide margin and would not clear the specialist
   at all. It is eligible because this reference was removed."* **The network is
   currently paying for merges that may not beat one adapter used alone.** The
   repo says restoring that reference is "the first thing to do" if this happens.

10. **Public corpora.** Both are readable. Only the draw is hidden. A miner who
    fine-tunes intuition on the public corpus has an advantage the design
    acknowledges and only partially mitigates.

11. **Blind submission if you have no GPU.** Local scores "predict, they do not
    decide," and 120 public instances cannot separate close recipes.

12. **Thin alpha liquidity.** 82,123 α depth; a throne-holder mints 1.6 % of it
    daily. Mark-to-market ≠ realisable.

13. **Docs contradict the code in several places** (see §11). Trust
    `constants.py` and the API, not the README or the website.

---

## 11. Documentation defects found (trust the code)

| Claim | Where | Reality |
|---|---|---|
| "Base retention ≥ **98 %**" | `docs/miner.md` hard-gates table | `BASE_RETENTION_FLOOR = 0.95` |
| "Peak VRAM ≤ 24 GB" gate | `docs/miner.md` | `constants.py`: *"Peak GPU memory is deliberately not gated or scored."* |
| "Latency p95 ≤ 30 s" gate | `docs/miner.md` | Latency is no longer scored; its 5 pts moved to token efficiency |
| "Beat the strongest permanent reference by **3 points**" | `README.md` | `DEFAULT_END_TO_END_MARGIN = 0.02` — 2 points |
| "Validators: small VPS, **no GPU**" | capcomp.ai website | 4 × 32 GB GPUs, protocol-enforced |
| "validator — thin weight-setter. No GPU" | `min_compute.yml` header comment | Same file's `validator:` block: `required: true, min_vram: 32, min_count: 4` |
| "reads the commitments on chain, fetches each miner's recipe from the URI it committed" | `docs/validator.md` §What you are doing | Commitments are dead; submission is via the API only |
| `CAPSUB_NETUID=1`, `SERVING_MAX_MODEL_LEN=4096` | `.env.example` | Live netuid is 103; constant is 8192 |
| "require_beat_reference is **off by default**" | `README.md` | The `baseline` gate is visibly binding and excluding candidates in live run data |

---

## 12. Verdict

### All ten subnets, one snapshot

Every figure in this table was **re-read live from finney on 2026-09-03** (block
8,984,103, TAO ≈ $256) so the rows are directly comparable to each other. The
per-document economics sections above use the α price at each document's own
analysis date and will differ.

| Subnet | Task | Miner deliverable | Miner GPU | Entry cost | α (USD) | Earning / UIDs | Top earner $/day | Owner capture | The catch |
|---|---|---|---|---|---|---|---|---|---|
| **SN47 Feval** | Verifiable LoRA eval | Adapter + published rollouts | 24–48 GB | $12.80 | $0.72 | **1 / 129** | $2,139 ← **owner** | **68.8 %** | Published repo ≠ live network; owner takes the whole miner pool via a `{0: 1.0}` fallback |
| **SN58 Greevils** | TEE algo-trading on Hyperliquid | Agent in a TDX VM, or a plain HL account | none (VM ~$145/mo) | $25.60 + ~$25k capital | $2.29 | 1 / 256 | $6,747 | 41.3 % | Sole earner holds no on-chain commitment; zero `gva1` approvals exist |
| **SN76 Phylax** | AI supply-chain security attestation | One Python file (`agent_main`) | **none** | $25.60 + ~$21/attempt | $0.60 | **21 / 256** | $364 | 40.5 % | Your track's rounds have to actually be scheduled |
| **SN78 Vocence → UMI** | ASL→English translation *(pre-activation)* | HTTP translator service | yes, 24–80 GB | $0.13 | $1.11 | 1 / 256 | $3,290 | 46.9 % | UMI weights type-level disabled; chain still says Vocence; the 0.10 floor is unproven |
| **SN79 MVTRX** | Agent-based market simulation | Always-on trading bot | **none** | $25.41 | $1.68 | **210 / 256** | $444 | 59.0 % | A genuine quant-trading skill gate; latency is scored |
| **SN80 OpenRoboto** | Fine-tune π0.5 VLA robotics | HF checkpoint | yes, A100-class | $0.13 + ~$19/attempt | $3.72 | 2 / 256 | $8,891 ← **owner** | 56.1 % | 81 % of the miner pool sits on the operator's UID 0 |
| **SN82 Compelle** | Adversarial LLM debate | A prompt, committed on chain | **none** | $0.13 | $0.88 | 1 / **64** | $2,599 | **28.8 %** | Incumbent-protected winner-take-all on 64 slots |
| **SN90 KubeTEE** | DePIN confidential compute | A TDX GPU cluster | 8-node TDX datacenter | $0.13 + **$1.5M–4M** | $8.10 | 2 / 97 | $18,715 ← **owner** | 66.6 % | Onboarding is operator-gated — you cannot join |
| **SN92 MicroTensor** | Certified inference systems | ONNX/GGUF artifact + 128-byte pointer | training only (RTX 3090+) | $25.60 | $0.86 | **9 / 256** | $646 | **39.2 %** *(0 % of the miner pool)* | Docs name the wrong paying track — `code` pays 0, `extract` pays all |
| **SN103 Capcomp** | LoRA composition | One JSON merge recipe | 32–48 GB | **$256.00** | $3.02 | **10 / 105** | $8,012 | 55.1 % | Dethrone margin sits ~24× below measurement noise |

**What the snapshot says.** Four of the ten have a functioning competitive field:
**SN79** (210 earners), **SN76** (21), **SN103** (10) and **SN92** (9). Five pay
exactly one UID, and on **SN47, SN80 and SN90** the single top earner *is* the
owner's own UID. Owner capture runs 28.8 – 68.8 %, and **SN92 is the only one
whose owner draws nothing at all from the miner pool** — its 39.2 % is the 18 %
protocol cut plus staked dividends, nothing else. Alpha prices moved materially
between the individual analyses and this snapshot (**SN78 +122 %** since August,
**SN90 −14 %** since its own writeup), so read every USD column as a same-day
comparison, not a forecast.

**Where a newcomer can actually compete today**, ranked: **SN79 MVTRX** (210
paying seats, $25 entry, no GPU, free testnet) → **SN92 MicroTensor** (9 paying
seats on a geometric curve where rank 8 still earns ~⅓ of rank 1, one consumer
GPU for training only, public API that hands you the whole frontier) → **SN76
Phylax** (21 seats, no GPU, local corpus to iterate against) → **SN103 Capcomp**
(10 seats, contested, but $256 entry and a noise-dominated throne) → **SN82
Compelle** ($0.13, one seat, incumbent protected). The remaining five are either
operator-gated, pre-activation, or paying a single UID that is often the owner's.

### Assessment

**This is the most technically honest subnet I have read.** The scoring is
genuinely reproducible — I recomputed the champion's grade to 0.27340 against a
reported 0.2733875, and reproduced `stage_balance` to five decimals for six
candidates straight from published per-axis data. The "What is not yet true"
page concedes things most subnets bury. The constants file argues with itself in
public and records measurements rather than assertions.

**But three things should give you pause.** The dethrone margin (0.0005) sits
24× below the engine's own measured noise, so the throne is substantially a
lottery among the top cluster. The owner takes 76.6 % of emission while calling
half of it a "burn". And the subnet removed the one reference — the best single
adapter — that would prove composition works at all, and its own code says the
current champion would likely fail it.

**The opportunity is real and unusually well-defined.** Two of twelve axes are
dead for the entire field, sitting on a geometric-mean floor. Lifting them is
worth 1.5–8× the dethrone margin, which is more than the entire spread between
rank 1 and rank 5. The meta is fully public and fully converged (`svd`, rank 8,
5–6 adapters, layer overrides), so you can reproduce the baseline in a day and
spend all your effort on the one axis nobody has attacked.

### Recommended path

1. **Do not mine this from the BEAM box.** You would submit blind. Register a
   hotkey (1 TAO) and rent one 48 GB GPU — budget ~$400–900/mo.
2. **Build the local harness first.** Pinned Qwen3-8B + 30-adapter pool + public
   pack, scaled to 400+ instances, not 120.
3. **Reproduce the meta baseline exactly** (`svd`, `output_rank: 8`,
   `svd_clamp_quantile: 1.0`, 5–6 adapters, layer_group_overrides). Confirm
   retention ≥ 0.95 and e2e ≥ ref + 0.02 locally. That alone should put you rank 5–7.
4. **Then do the differentiated work:** sweep all 30 adapters and their pairs
   against `arrow_maze` and `web_of_lies` specifically. Characterise the 18
   "unmeasured" adapters — that is unclaimed ground.
5. **Automate a daily submit** early in each run (never inside the last 300
   blocks). Once in the top cluster, every day is a $3,061 lottery ticket and
   missing a day forfeits a draw.
6. **Model your break-even honestly.** Rank 2–5 does not cover GPU cost. This is
   a throne-or-nothing subnet: either commit to winning it or do not enter.
7. **Watch for the best-single-adapter reference being restored.** `references.py`
   names it as the first remedy. If it returns, the bar jumps from ~0.112 to
   ~0.150 and most of the current field — including the champion — stops
   qualifying overnight. That is the single largest regime risk to your investment.

---

## 13. Sources

**Code / spec (authoritative)**
- https://github.com/Capcomp-AI/capability-composition-subnet @ `9bdde88`
- `capability_subnet/common/constants.py`, `scoring/contribution.py`,
  `scoring/references.py`, `scoring/weight_vector.py`, `common/chain.py`,
  `registry/data/adapter_registry.json`, `registry/data/base_manifest.json`,
  `workflows/lora_merger_logic_v1/sources.py`
- `docs/miner.md`, `docs/validator.md`, `docs/architecture.md`, `docs/arena.md`,
  `min_compute.yml`, `pyproject.toml`, `.env.example`

**Live API** (fetched 2026-08-27)
- `GET https://api.capcomp.ai/contract`, `/health`, `/run/416`, `/run/415`,
  `/run/414`, `/run/414/results`, `/run/414/weights`, `/run/411..413/results`

**Chain** (finney, block 8,938,546)
- `Subtensor.subnet(103)`, `Subtensor.metagraph(103)`, `Subtensor.recycle(103)`

**Site**
- https://www.capcomp.ai — including the "What is not yet true" honest-limits page

**External price reference**
- TAO ≈ $256 (CoinGecko / Coinbase, 2026-08-27)

**Upstream**
- `Qwen/Qwen3-8B` @ `b968826d9c46dd6066d109eabc6255188de91218` (Apache-2.0)
- `AffineFoundation/affine-lgc` @ `19765edac477`
- `AffineFoundation/rl-python` @ `0cc711b1f059`
