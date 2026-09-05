# SN47 — Feval (Verifiable LoRA Evaluation)

| | |
|---|---|
| **netuid** | 47 (`Feval`, symbol `צ`) |
| **Chain identity** | name `Feval` · github `center196/feval` · url `x.com/Feval47` |
| **Description (on chain)** | *"Scaling reliable and verifiable LLM evaluation across decentralized environments…"* |
| **Owner hotkey** | `5GjN9n3ndtbRTir5HCRsaaFjxfoQpffnYsAc5VG9iWMfdEWj` — **holds UID 0** |
| **Owner coldkey** | `5GBmFsPkMDGcEcKwL69rCcbSko2xX2WTUzs6riW7d8XVqTpv` |
| **Registered at block** | 7,340,355 (long-lived slot — **repurposed**, see §4.1) |
| **Code** | https://github.com/center196/feval — **created 2026-08-28 00:36 (+07), 2 commits** |
| **Local checkout** | `/root/Bittensor/47/feval` @ `45f5760` |
| **Package** | `feval` 1.0.0 · protocol `feval-network-v9` |
| **Live state (2026-08-28, block 8,940,871)** | dataset window 2483, tempo 360 |
| **Price** | 0.003073 TAO/צ (≈ $0.787) · tao_in τ1,318.88 · alpha_in 429,176 · alpha_out 1,425,813 |
| **UIDs** | 116 registered · **1 earning (UID 0 = the owner)** · 14 validator permits · 10 with dividends |
| **Registration cost** | **0.05 TAO** (~$12.80) — `min_burn` 0.05, `max_burn` 100 |
| **Immunity** | 5,000 blocks (~16.7 h) · commit-reveal **enabled**, period 1 |

> Live from finney, on-chain commitments, and the miner's public Hugging Face
> artifacts on 2026-08-28. **The published repository and the live network
> disagree on several consensus-critical constants** — see §11. Where they
> differ I record both and say so.

---

## 1. Goal of the subnet

Make LLM evaluation **cheap to verify**. The expensive half of evaluation is
generation; the cheap half is checking. Feval splits them:

- **Miners** train a LoRA adapter on a pinned small base model, then run the
  evaluation themselves and publish the complete **rollouts** (prompts,
  generated tokens, answers) to Hugging Face.
- **Validators** never regenerate the full set. They spot-check a handful of
  random rows per round by re-running just those rows and confirming the tokens
  match what the miner claimed.

The whole design rests on one idea, and it is genuinely the subnet's
contribution:

### The canonical-token rule

Greedy decoding is not reproducible across GPUs — tiny floating-point ordering
differences flip near-ties and the sequences diverge. Feval makes generation
**deterministic by protocol rather than by hardware**:

> Among the top **3** tokens whose probability is within **85 %** of the maximum,
> a protocol hash — seeded on `(evaluation_seed, model_digest, row_id)` — picks
> one canonical token.

```python
# canonical.py
multiplier, offset = canonical_row_coefficients(...)   # sha256-derived
return min(candidates, key=lambda t: ((t * multiplier + offset) % HASH_PRIME, t))
```

Both sides run the identical rule. This tolerates cross-GPU non-determinism
*without* letting a miner pick whichever plausible token is convenient — the
choice among near-ties is pseudorandom and unpredictable before the seed is
known. That is the mechanism that makes a 1-in-N audit meaningful.

Contrast with SN103, which sidesteps the same problem by having every validator
re-measure every candidate on its own hardware and comparing *outcomes* rather
than bytes. Feval's approach is far cheaper per validator, and strictly more
fragile if the rule has an escape hatch.

---

## 2. What you do as a miner

Three artifacts: a trained adapter, a rollout repository you keep fresh, and one
chain commitment pointing at both.

```bash
uv venv --python 3.12 && source .venv/bin/activate && uv pip install -e .
cp .env.example .env          # set HF_TOKEN

# 1. train your LoRA (not provided — this is the whole competition)

# 2. publish the adapter + register it on chain
feval miner publish-model \
  --adapter-dir output/my-lora \
  --model-repo my-org/my-lora \
  --rollout-repo my-org/my-rollouts \
  -w my-wallet -H my-hotkey -n finney

# 3. keep rollouts current, forever
feval miner watch-rollouts \
  --adapter-dir output/my-lora --work-dir miner-work \
  -w my-wallet -H my-hotkey -n finney
```

### The chain commitment

512-byte `BigRaw`, compact keys:

```json
{"p":"f3","m":"<model_repo>","r":"<40-hex model revision>",
 "h":"<64-hex model_digest>","d":"<rollout_repo>"}
```

The block at which it lands **proves priority** — that is the copy-protection
primitive (`runtime.py::_copy_filtered`; a later duplicate digest is marked a
copy of the earlier owner and dropped from weights).

### What the network will download from you — and nothing else

```python
MODEL_FILES   = ("adapter_config.json", "adapter_model.safetensors")
ROLLOUT_FILES = ("manifest.json", "rollouts.jsonl")
```

> *"Python, pickle, model configuration, tokenizer, templates, and dataset
> scripts are never loaded from miner repositories."*

This is the tightest miner-input surface of the three subnets I have looked at.
Combined with strict JSON parsing (duplicate keys rejected, non-finite numbers
rejected) and hard size caps, the attack surface is small and deliberate.

### Adapter bounds

| Bound | Value |
|---|---|
| `MAX_LORA_RANK` | 16 |
| `MAX_LORA_ALPHA` | 256 |
| `MAX_ABS_LORA_VALUE` | 100.0 |
| `MAX_ADAPTER_BYTES` | 256 MB |
| `MAX_ADAPTER_ELEMENTS` | 100,000,000 |
| `MAX_ROLLOUT_BYTES` | 768 MB |
| `MAX_ROLLOUT_LINE_BYTES` | 512 KB |
| Allowed target modules | `q_proj k_proj v_proj o_proj gate_proj up_proj down_proj in_proj out_proj z_proj a_proj b_proj` |

The base model and revision are **pinned and enforced** — `artifacts.py:171`
rejects any manifest whose `base_model`/`base_revision` differ from config.

---

## 3. Scoring logic

### 3.1 The evaluation window

| Constant | Value |
|---|---|
| `DATASET_WINDOW_BLOCKS` | 3,600 (**12 h**) — window = `block // 3600` |
| `EVALUATION_ROWS` | **32** per window |
| `MATH_ROWS` / `INSTRUCTION_ROWS` | 16 / 16 |
| `CANDIDATE_POOL_ROWS_PER_TASK` | 50,000 |
| `WEIGHT_INTERVAL_BLOCKS` | 150 (**30 min**) |

Rows are drawn deterministically from a sealed pool via
`evaluation_seed(netuid, window)` — every validator derives the same 32 rows
with no coordination.

**Sources (pinned to immutable revisions):**

| Task | Dataset | Revision | Scoring |
|---|---|---|---|
| Math | `nvidia/Nemotron-SFT-Math-v4` | `84d42ad0cb96…` | strict numeric / exact match |
| Instruction | `nvidia/Nemotron-RL-instruction_following` | `3b253899665c…` | deterministic constraint checks |

### 3.2 Rewards are binary per row

**Math** (`rewards.py::strict_numeric_fraction`) parses only a *complete, inert*
numeric answer — plain numbers, `a/b`, `\frac{a}{b}`, `\boxed{…}` — and only when
the boxed value is the final content. It explicitly *"never calls `eval`, SymPy,
a shell, or a model."* Free-form expressions, variables and explanatory text
score 0.

**Instruction** is an IFEval-style engine with ~28 hand-written constraint types
— `keywords:frequency`, `length_constraints:number_paragraphs`,
`punctuation:no_comma`, `change_case:english_capital`, `startend:quotation`,
`detectable_format:number_bullet_lists`, `count:count_unique`, and so on.
**All constraints must pass** for the row to score 1:

```python
return int(all(_check_constraint(text, c) for c in constraints))
```

Any unrecognised constraint id returns `False` — fail-closed.

No model judges anything anywhere in this subnet.

### 3.3 Champion promotion — paired 99 % lower confidence bound

The 32 binary rewards are packed into a bit vector. A challenger is compared to
the reigning king **row-by-row on the identical 32 rows**:

```python
differences = [c - k for c, k in zip(candidate, king)]
mean = sum(differences)/n
lcb  = mean - z * sqrt(variance/n)          # z = 2.326347874  → 99 % one-sided
promote if lcb >= PROMOTION_DELTA_MIN       # 0.01
```

Pairing is the right call — it cancels row difficulty entirely, so the variance
is only in *disagreements*. With n = 32 and z = 2.326, a challenger realistically
needs to win roughly **5–7 more rows than it loses** for the bound to clear 0.01.
That is a demanding bar on 32 rows, and it is deliberately so.

**At most one model is promoted per weight cycle.** If the king vanishes, a more
conservative *unpaired* two-proportion bound is used against its last valid
score, purely to preserve liveness.

### 3.4 Emission split — three champions

```python
CHAMPION_COUNT  = 3
CHAMPION_SHARES = (0.50, 0.20, 0.10)
CHALLENGER_SHARE = 0.0
```

Shares are **normalised to sum to 1** (`champion_weight_mapping`), so with all
three seats filled the real split is:

| Seat | Raw share | **Normalised** |
|---|---|---|
| King | 0.50 | **62.5 %** |
| 2nd | 0.20 | **25.0 %** |
| 3rd | 0.10 | **12.5 %** |
| Challengers | 0.00 | **0 %** |

A champion is dropped from the mapping if its commitment changed, its digest
no longer matches, it scored ≤ 0, or it is flagged as a copy.

### 3.5 ⚠️ The fallback pays the owner

```python
# runtime.py:1036
if not normalized:
    # UID 0 is the protocol burn target. Never reward a zero-score
    # model merely because no positive champion exists yet.
    normalized = {0: 1.0}
```

**UID 0 is not a burn address.** On SN47, UID 0 is the subnet owner's own hotkey
(`5GjN9n3ndt…`, coldkey identical to `owner_coldkey`). So whenever no champion
qualifies, **100 % of the miner pool is paid to the owner.**

This is exactly the trap SN103's code documents and avoids:

> *"Note that UID 0 is **not** an incinerator — it belongs to whichever neuron
> registered into the first slot… Live components resolve the owner's UID from
> the metagraph instead and decline to submit at all when there is none."*

Live chain confirms the fallback is what is running: **UID 0 incentive =
1.000000**, `E = 147.601 α/tempo` = exactly `0.41 × 360` = the entire miner pool.

### 3.6 The audit

| Constant | Value |
|---|---|
| `AUDIT_ROWS_PER_ROUND` | 8, uniformly random without replacement |
| `AUDIT_DELAY_BLOCKS` | 5 (rows chosen from a *future* block hash) |
| `audit_interval_seconds` | 420 (~7 min) |
| `AUDIT_MIN_FAKE_ROW_FRACTION` | 0.01 |
| `AUDIT_DETECTION_CONFIDENCE` | 0.999 |

`audit_seed` mixes `block_hash`, hotkey, model digest, rollout revision and round
number, and the challenge block is 5 blocks ahead — so a miner cannot know which
rows will be checked when it publishes.

`required_audit_rounds` computes `ceil(log(1−0.999)/log(1−0.01)) = 688` samples
→ 86 rounds, but caps at full coverage: with 32 rows that is
**⌈32/8⌉ = 4 rounds**, i.e. the entire window is verified within ~28 minutes.

At the live scale (`row_count: 10000` in the miner's manifest) the statistical
bound binds instead: 86 rounds ≈ 10 hours to reach 99.9 % confidence that no
more than 1 % of rows are forged.

---

## 4. Live competition landscape

### 4.1 This is a repurposed subnet, relaunched days ago

Netuid 47 registered at block **7,340,355** — far older than the Feval code. The
on-chain commitments make the history plain. Of **85** commitments:

| Cohort | Count | Example |
|---|---|---|
| **"evolai" era** (previous protocol) | **80** | `{"m2":{"m":"mrthor102/evolai-mb2-super-002","r":"main"}}` · `{"t":{"m":"Roystar/evolai-qwen2.5-1.5b",…}}` |
| Other / undecodable | 5 | |
| **Feval protocol (`"p":"f3"`)** | **1** | see below |

Those 80 are stale artefacts of a completely different mechanism — Mamba2 and
Qwen2.5 full models, not LoRA adapters. They are inert under the Feval
validator, which only reads `p == "f3"`.

The GitHub repo was created **today** (2026-08-28 00:36 +07) with two commits,
`first commit` and `logo`. `README.md` links to a `SECURITY.md` that **does not
exist in the repository**.

### 4.2 There is exactly one Feval miner, and it earns nothing

```
hotkey  5HQkZmWwY9BuwSnC1gQkEprT1t8gD6okac2G3pyP6fdTg2WR   (UID 110)
coldkey 5DAvbHfkGRJBMQCaPrG6DXMCtfyDaLUBcc2y4BQptKgzR8eP
commit  block 8,938,576
        {"p":"f3",
         "m":"feval-center/miner-47-lora",
         "r":"6055d3b29b76f88fa409a21faa450f0c45be4fbe",
         "h":"bd21e9efcdef1d90f9773332ce9a457f3c73b1c6cd6b8ffecaffd68bf2dbf985",
         "d":"feval-center/miner-47-rollouts"}
incentive 0.000000   emission 0.000
```

The Hugging Face org is **`feval-center`** — operator-branded, and it contains
exactly **one** model repo. Its coldkey differs from the owner coldkey, so they
are distinct on-chain entities; the naming makes an affiliation likely but I
cannot prove it from chain.

Both artifacts are live and being maintained:

| Repo | Last modified | Files |
|---|---|---|
| `feval-center/miner-47-lora` (model) | 2026-08-27 19:41 | `adapter_config.json`, `adapter_model.safetensors`, `feval_model.json` |
| `feval-center/miner-47-rollouts` (dataset) | 2026-08-27 23:33 | `manifest.json`, `rollouts.jsonl` (58.1 MB, LFS) |

The published adapter is tiny — **rank 4, alpha 4, `q_proj` + `v_proj` only**:

```json
{"base_model_name_or_path": "Qwen/Qwen3-4B-Base",
 "r": 4, "lora_alpha": 4.0, "target_modules": ["q_proj","v_proj"],
 "revision": "b1ecb62b18378adb8af264260fbbbd618222be87"}
```

### 4.3 Emission is 100 % to the owner

| UID | Role | Incentive | Dividends | α/day |
|---|---|---|---|---|
| **0** | **owner hotkey** | **1.000000** | 0 | **2,952** |
| 110 | the only Feval miner | 0 | 0 | 0 |
| 1 | `5E2LP6EnZ54m3w` | 0 | 0.33794 | 998 |
| 12 | `5Do5iLBHhSEjwC` | 0 | 0.26027 | 768 |
| 5, 6, 14, 28, … | validators | 0 | 0.106 / 0.103 / 0.093 / 0.049 | |
| **all other ~100 UIDs** | | **0** | 0 | **0** |

One UID earns incentive, and it is the owner's, via the `{0: 1.0}` fallback.

### 4.4 What that means

The subnet is **live but pre-competitive**. The mechanism runs, weights are set
every 150 blocks, the audit loop turns — and no external miner has yet published
a Feval-protocol model. The one that has cannot clear the bootstrap bar (or is
being rejected; see §11), so the fallback fires every cycle.

---

## 5. Miner economics

Subnet emits **1.000 α/block = 7,200 α/day**; 18 % owner cut, 41 % miners, 41 %
validator dividends → **miner pool = 2,952 α/day**.

At α = 0.003073 TAO and TAO ≈ $256 → **α ≈ $0.787**:

### Today

| Recipient | Share | α/day | TAO/day | USD/day | USD/mo |
|---|---|---|---|---|---|
| **UID 0 (owner), via fallback** | **100 %** | **2,952** | **9.07** | **~$2,322** | **~$69,700** |
| Every miner | 0 % | 0 | 0 | $0 | $0 |

### If the hill were contested

| Seat | Normalised | α/day | TAO/day | USD/day | USD/mo |
|---|---|---|---|---|---|
| **King** | 62.5 % | 1,845 | 5.67 | **~$1,451** | ~$43,500 |
| 2nd | 25.0 % | 738 | 2.27 | ~$581 | ~$17,400 |
| 3rd | 12.5 % | 369 | 1.13 | ~$290 | ~$8,700 |
| 4th+ | 0 % | 0 | 0 | $0 | $0 |

Also 2,952 α/day (~$2,322) flows to validator dividends by stake — concentrated,
with UID 1 at 33.8 % and UID 12 at 26.0 %.

### Costs

| Item | Cost |
|---|---|
| Registration (recycle) | **0.05 TAO ≈ $12.80** — the cheapest entry of any subnet I have analysed |
| Training a rank-≤16 LoRA on a 4B base | Hours on one 24–48 GB card; ~$5–40 per run rented |
| **Rollout generation (the real cost)** | 10,000 rows per window at the live scale, regenerated every 12 h |
| Hugging Face hosting | Free for public repos |
| Continuous `watch-rollouts` | One GPU host, always on: ~$300–900/mo |

**This is by far the cheapest of the three subnets to enter.** $12.80 to
register, one commodity GPU to compete, and the top-3 payout structure means
three seats pay rather than one. Against SN103's 1 TAO + rented A6000 and SN90's
$1.5M–4M cluster, SN47 is the only one where a solo miner with a single card is
economically plausible.

### Liquidity

`alpha_in` 429,176 against τ1,318.88 — deeper in token terms than SN103, but the
alpha is cheap ($0.787) and `subnet_volume` is 42,115 α. The king's 1,845 α/day
is 0.43 % of pool depth per day — the least slippage-constrained of the three.

---

## 6. How to become the king

The unusual thing about SN47 right now: **the throne is empty and the entry cost
is $12.80.** Whether that is an opportunity or a warning is the whole question.

### Priority 1 — Resolve the repo/live mismatch before writing any code.

This is blocking and nothing else matters until it is settled. The public
repository pins `Qwen/Qwen3.5-4B-Base @ daa9c16f…`; the only live miner published
against `Qwen/Qwen3-4B-Base @ b1ecb62b…`, and its manifest declares
`feval-rollouts-v14` where the repo declares `v8`. Since `artifacts.py:171`
rejects on base-model mismatch, **at most one of those two can be valid, and the
public code cannot validate the live artifact.** Ask the operator directly:
which base model and which rollout protocol is the running network on. Do not
spend a GPU-hour before you have that answer.

### Priority 2 — Optimise for the paired LCB, not for average accuracy.

The promotion test is `mean(candidate − king) − 2.326·se ≥ 0.01` over 32 paired
binary rows. Two consequences most people will miss:

- **Rows you both get right or both get wrong contribute nothing.** Only
  disagreements move the bound. You are not maximising score; you are maximising
  *net wins on rows the king fails*.
- **Variance is the enemy.** A model that wins 8 and loses 3 clears far more
  easily than one that wins 12 and loses 7, despite the same margin of 5.
  Consistency beats brilliance at n = 32.

So: profile the incumbent's published rollouts (they are public), find the rows
it fails, and train specifically to fix those **without regressing anything it
gets right.**

### Priority 3 — Split your effort 50/50 between math and instruction-following.

16 rows each, equally weighted. The instruction half is **not a language
problem — it is a rule-compliance problem**, checked by ~28 deterministic
regex-and-count constraints that are fully readable in `rewards.py`. Things like
`punctuation:no_comma`, `change_case:english_capital`, `count:count_unique`,
`detectable_format:number_highlighted_sections`. A small LoRA can be trained
directly against that exact checker — you have the grader source.

That is the single highest-yield insight in this subnet: **you can run the
scorer offline on your own generations, for free, with no GPU.** Most miners
will train on the dataset; you should train against the verifier.

For the math half, note the parser is deliberately brittle — it accepts only a
complete inert number as the final content. Train the format (`\boxed{…}` last,
nothing after it) as hard as you train the arithmetic; a correct answer in the
wrong wrapper scores 0.

### Priority 4 — Take the seat while it is free.

`bootstrap_min_score = 0.0`, and with no champions the promotion path is simply
`score > 0`. The first valid Feval model with any positive score becomes king
and takes 62.5 % of the miner pool (~$1,451/day at current prices). Every
subsequent challenger must then clear your grade by a 99 %-confidence paired
margin — which, at n = 32, is a genuinely strong defensive position.

**This is the cheapest king-of-the-hill seat currently available on Bittensor,
and it is unoccupied.** That is the entire investment case.

### Priority 5 — Keep `watch-rollouts` running without gaps.

The window rolls every 3,600 blocks (12 h) and you must have fresh rollouts for
the current window to be scored at all. A champion that misses a window falls to
the unpaired-LCB path and can be displaced by a weaker challenger. Treat uptime
as a first-class requirement, and keep `validator-state.json` if you also run a
validator.

### Priority 6 — Never forge a row.

The audit samples 8 uniformly random rows per ~7 min against a block hash 5
blocks in the future. You cannot predict the draw. At 32 rows the whole window is
covered in 4 rounds (~28 min); at 10,000 rows a 1 % forgery rate is caught with
99.9 % confidence in ~86 rounds. The expected value of cheating is negative and
the mechanism is well built here.

### The path

1. Contact the operator; settle the base-model / protocol question (§11).
2. Register a hotkey — 0.05 TAO. Immunity is 5,000 blocks (~16.7 h).
3. Pull the pinned base and both Nemotron datasets; reproduce the 32-row window
   locally from `evaluation_seed(47, window)`.
4. Build an offline harness around `rewards.py` — the exact grader, no GPU needed.
5. Train a rank-≤16 LoRA against that harness, weighted toward instruction
   constraints where the marginal row is cheapest to win.
6. `publish-model`, then `watch-rollouts` under a process supervisor.
7. Verify your commitment decodes (`"p":"f3"`) and that your rollout manifest
   base model matches whatever the operator confirms in step 1.

---

## 7. Rules you must keep

| Rule | Consequence if broken |
|---|---|
| Commitment protocol must be `"p":"f3"` | Ignored entirely — 80 stale `evolai` commitments prove this is silent |
| Commitment ≤ 512 bytes (chain BigRaw limit) | `publish-model` raises |
| Model repo exposes exactly `adapter_config.json` + `adapter_model.safetensors` | Nothing else is downloaded; missing files = invalid |
| Rollout repo exposes exactly `manifest.json` + `rollouts.jsonl` | Same |
| `base_model` / `base_revision` must match config | **Rejected** (`artifacts.py:171`) |
| LoRA rank ≤ 16, alpha ≤ 256, abs value ≤ 100 | Rejected |
| Adapter ≤ 256 MB, ≤ 100M elements, tensor dim ≤ 65,536 | Rejected |
| Rollouts ≤ 768 MB, ≤ 512 KB per line | Rejected |
| Target modules from the 12-name allowlist | Rejected |
| Strict JSON — no duplicate keys, no NaN/Inf | Rejected |
| Rollouts must obey the canonical-token rule exactly | Audit failure |
| Keep rollouts fresh each 3,600-block window | Not scored that window |
| Do not duplicate an earlier miner's `model_digest` | Flagged as a copy, dropped from weights (earliest commit block wins) |
| Score must be **> 0** | Excluded from `champion_weight_mapping` even if seated |
| Only 3 seats pay | 4th place earns **nothing** — `CHALLENGER_SHARE = 0.0` |

---

## 8. Device / hardware conditions

The README is the entire stated requirement: *"Linux or WSL, Python 3.12, an
NVIDIA GPU, and a Bittensor wallet."* Everything else is inferred from the code.

### Miner

| | |
|---|---|
| OS | Linux or WSL |
| Python | **3.12** |
| GPU | NVIDIA, CUDA. Base is **4B in BF16** ≈ 8 GB weights |
| Practical VRAM | **24 GB comfortable, 16 GB tight, 48 GB for fast rollout generation** |
| Real cost driver | **Rollout generation**, not training — 10,000 rows regenerated every 12 h at the live scale |
| Stack | vLLM 0.27.1, transformers 5.15.0, datasets 5.0.1, safetensors 0.8.0, bittensor 11.1.0 |
| Pinned for consensus | BF16, **eager execution**, GDN-compatible vLLM settings — *"pinned in code because these settings affect consensus"* |
| Storage | Base model + two Nemotron datasets + rollout history; budget 200 GB+ |
| Uptime | Continuous — `watch-rollouts` must not miss a window |
| Secrets | `HF_TOKEN` in `.env` (or `HF_TOKEN_PATH`) |

### Validator

| | |
|---|---|
| GPU | **32 GB** — stated explicitly: *"A 4B BF16 base plus one 32K sequence fits on a 32 GB GPU"* |
| Tuning | `AUDIT_GPU_MEMORY_UTILIZATION = 0.60`, `AUDIT_MAX_NUM_BATCHED_TOKENS = 4096`, `AUDIT_MAX_NUM_SEQS = 8` |
| Why 0.60 | vLLM must not reserve nearly all remaining VRAM for KV cache, and prompt-logprob softmax is chunked below its 8 K default |
| Work | Audit 8 rows per ~7 min — **far lighter than generation** |
| State | Keep `validator-state.json` across restarts |
| Optional | W&B mirror (`FEVAL_REPORT_WANDB=1`) — *"missing credentials/package/network never affect audits or weights"* |

> **Against your BEAM box (2 cores / 3.7 GB):** cannot mine and cannot validate —
> both need a CUDA GPU and vLLM. But unlike SN90, the gap here is one rented
> commodity card, not a data centre. A single 24–48 GB GPU at ~$0.3–0.8/h makes
> you a full participant. **Of the three subnets analysed, SN47 has by far the
> lowest hardware barrier.**

---

## 9. Third-party conditions

| Dependency | Role | Failure mode |
|---|---|---|
| **Hugging Face Hub** | Base model, both datasets, **and every miner artifact** | **Central single point of failure.** No model, no rollouts, no evaluation. There is no fallback host. |
| `Qwen/Qwen3.5-4B-Base` @ `daa9c16f…` | Pinned base (repo) | Verified to exist (HTTP 200). Changing it is *"a subnet protocol upgrade"* |
| `Qwen/Qwen3-4B-Base` @ `b1ecb62b…` | Base the **live** miner actually used | Verified to exist. Conflicts with the above — see §11 |
| `nvidia/Nemotron-SFT-Math-v4` @ `84d42ad0…` | 16 math rows/window | Verified. Immutable snapshot |
| `nvidia/Nemotron-RL-instruction_following` @ `3b253899…` | 16 instruction rows/window | Verified. Immutable snapshot |
| **vLLM 0.27.1** | Generation + audit. BF16 + eager pinned | **Consensus-critical.** A version or setting drift changes tokens and breaks audits |
| **bittensor 11.1.0** | Chain, commitments, weights | ⚠️ Your `/root/beam/.venv` has **10.5.0** — Feval needs its own venv |
| transformers 5.15.0 / datasets 5.0.1 / safetensors 0.8.0 | Tokenizer, data, weights | Exact pins in `pyproject.toml` |
| **Weights & Biases** | Optional public summary mirror, `feval-subnet-47` | Explicitly non-consensus; opt out with `FEVAL_REPORT_WANDB=0` |
| **finney** | Identity, commitments, weights, window anchoring | Commit-reveal **enabled** (period 1) |
| `feval-center` HF org | The only live miner's artifacts | Operator-branded; one repo |

Notably **absent**: no operator-run API, no closed-source engine, no proxy, no
S3 price feed. Everything a validator needs is on-chain or on Hugging Face.
That is a meaningfully better decentralisation posture than SN90 and comparable
to SN103.

---

## 10. Risks

1. **The published code does not match the live network.** Rollout manifest v8
   vs v14, and two different pinned base models. `artifacts.py:171` rejects on
   base-model mismatch, so a validator running the public repo would reject the
   only live miner outright. Either the operator runs unpublished code or the
   repo is a sanitised snapshot. **This is the top risk and it is unresolved.**

2. **The repository is one day old with two commits.** `first commit` and
   `logo`, created 2026-08-28 00:36. No development history, no tests directory,
   no CI, and `README.md` links to a `SECURITY.md` that does not exist.

3. **UID 0 is treated as a burn address but is the owner's hotkey.** The
   `{0: 1.0}` fallback pays the owner 100 % of the miner pool whenever no
   champion qualifies — which is the state right now, worth ~$2,322/day. The
   code comment calls UID 0 *"the protocol burn target"*; on chain it is
   `owner_hotkey` with `owner_coldkey` matching the subnet owner.

4. **Zero external miners.** 116 UIDs, 85 commitments, and exactly one uses the
   Feval protocol — from an operator-branded Hugging Face org. There is no
   evidence yet that anyone outside the team can or has participated.

5. **A repurposed subnet slot.** 80 of 85 commitments belong to a prior "evolai"
   mechanism. Whatever community existed has not migrated. Historical emission
   and price history describe a different product.

6. **The canonical-token rule is load-bearing and unaudited.** The entire
   cheap-verification claim rests on it. If a miner can steer generation so that
   near-ties resolve favourably — or if 3 candidates within 85 % is wide enough
   to admit meaningful choice — the audit becomes decorative. I found no
   published analysis of this, and it is exactly where I would look for an
   exploit.

7. **n = 32 is a small sample for a 99 % bound.** It makes promotion hard (good
   for stability) but also means a genuinely better model can sit unpromoted for
   many windows, and a lucky king can hold a seat it does not deserve.

8. **Only three seats pay, and 4th earns literally zero.**
   `CHALLENGER_SHARE = 0.0`. There is no participation reward, no tail, no
   consolation. You are top-3 or you are unpaid.

9. **Total Hugging Face dependency.** Base model, datasets, and every miner
   artifact. An HF outage halts the subnet; a repo deletion erases a champion.

10. **Consensus depends on exact vLLM behaviour.** BF16, eager execution and GDN
    settings are pinned *in code* because they change tokens. A vLLM upgrade, a
    different CUDA version, or an unusual GPU could desynchronise a validator
    from the network.

11. **Validator dividends are concentrated.** Two UIDs hold ~60 % of dividend
    weight; ten hold all of it.

12. **`min_burn` 0.05 / `max_burn` 100 TAO.** Registration is trivially cheap
    today, but the burn adjusts. If the subnet becomes contested, entry cost can
    rise by 2,000× before hitting the cap.

13. **No documentation beyond a 56-line README.** No spec, no incentive-mechanism
    document, no architecture notes, no worked examples. Everything in this
    analysis was reverse-engineered from source. That is a real ongoing cost for
    any miner, and it means the protocol can change without a changelog.

---

## 11. Repo vs live network — the mismatch in detail

| Field | GitHub repo (HEAD, today) | Live network (miner manifest / adapter) |
|---|---|---|
| Rollout manifest protocol | `feval-rollouts-v8` | **`feval-rollouts-v14`** |
| Network protocol | `feval-network-v9` | not exposed in the manifest |
| `base_model` | `Qwen/Qwen3.5-4B-Base` | **`Qwen/Qwen3-4B-Base`** |
| `base_revision` | `daa9c16f371249f9ad1c75a9ed6f956c08ea08f5` | **`b1ecb62b18378adb8af264260fbbbd618222be87`** |
| `max_output_tokens` | 32,768 | **4,096** |
| `EVALUATION_ROWS` | 32 | manifest `row_count`: **10,000** |
| `dataset_window` | `block // 3600` | 2483 — ✔ **matches** |
| `evaluation_seed` | derived from `(netuid, window)` | present and well-formed — ✔ consistent |

The window arithmetic and seed structure line up, so the two are clearly the same
family of code. But the protocol version moved **forward** (v8 → v14) while the
pinned base model moved **backward** (Qwen3.5 → Qwen3), which cannot both be a
simple "repo is older" story. The most consistent reading is that the published
repository is a **renumbered or partially-sanitised snapshot**, not the code
producing the live artifacts.

Practical consequence for you: **do not assume `constants.py` is authoritative.**
Confirm the running values with the operator before training anything.

### Other documentation defects

| Claim | Where | Reality |
|---|---|---|
| *"See SECURITY.md for security guidance"* | `README.md` | File does not exist in the repository |
| `CHAMPION_SHARES = (0.50, 0.20, 0.10)` reads as 80 % paid, 20 % burned | `constants.py` | Shares are **normalised**; the real split is 62.5 / 25 / 12.5 and nothing is burned |
| *"UID 0 is the protocol burn target"* | `runtime.py:1037` | UID 0 is the **owner's hotkey**; the fallback pays the owner, it does not burn |
| Two parallel weight paths | `validator.py::write_weights` (uses `adapter_hash`) vs `runtime.py::_maybe_set_weights` (uses `model_digest`) | Only the `runtime.py` path is live; `validator.py`'s appears to be a stale CLI path |

---

## 12. Verdict

### Against the subnets analysed this week

| | **SN47 Feval** | **SN103 Capcomp** | **SN90 KubeTEE** |
|---|---|---|---|
| Type | LoRA training + verifiable eval | LoRA composition contest | DePIN confidential compute |
| Miner deliverable | Adapter + published rollouts | One JSON merge recipe | A TDX GPU cluster |
| **Entry cost** | **0.05 TAO ≈ $12.80** | 1 TAO ≈ $256 | 0.0005 TAO + **$1.5M–4M** |
| Hardware to compete | **One 24–48 GB GPU** | One 32–48 GB GPU | 8+ node TDX datacenter cluster |
| Can you start today? | **Yes — but resolve §11 first** | **Yes** | **No** — operator-gated |
| Base model | Qwen3(.5)-4B-Base | Qwen3-8B | n/a |
| Seats that pay | **3** (62.5 / 25 / 12.5 %) | 10, but rank 1 takes 45 % | proportional to capacity |
| **Throne status** | **EMPTY** | contested, changed hands 4/4 runs | n/a (1 miner) |
| Rank-1 income | ~$1,451/day | ~$3,061/day | ~$5,310/day |
| Active external miners | **0** | ~25/run, 36 in queue | **0** |
| Owner capture today | **100 % of miner pool** (fallback) | 76.6 % of all emission | 67.7 % of all emission |
| Feedback latency | **30 min** (weights), 12 h window | 1 day to score, 2 to pay | 72 min |
| Auditability | **Good** — all on-chain + HF, no operator API | **Excellent** — re-derived to 5 dp | **Weak** — operator's Rancher only |
| Documentation | **56-line README** | Extensive, candid | Extensive, candid |
| Repo maturity | **2 commits, 1 day old** | Mature, tests, adversarial suite | Mature, 35 tests, CI |

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

**Feval has the best core idea of the three and the least evidence behind it.**

The canonical-token rule is a real contribution. Cross-GPU non-determinism is the
reason most decentralised evaluation designs force every validator to redo every
computation; resolving near-ties by a seeded hash that neither side can steer is
an elegant way out, and it is what makes an 8-rows-per-7-minutes audit
meaningful. The paired LCB promotion test is statistically correct and correctly
motivated. The miner-input surface — four files, no pickle, no tokenizer, strict
JSON — is the tightest I have reviewed. `rewards.py` never calls `eval`, SymPy, a
shell, or a model, and says so.

**But almost nothing else is in place.** The repository is one day old with two
commits, no tests, no spec, and a dangling `SECURITY.md` link. It does not match
the network it claims to describe — different base model, different protocol
version — which means the public code cannot currently validate the only live
miner. There are zero external participants. And the "burn" fallback pays the
owner 100 % of the miner pool, ~$2,322/day, which is the actual live state of the
subnet rather than a hypothetical.

The honest framing: this is a **week-one subnet with a good mechanism and no
track record**, sitting on a repurposed slot whose previous community did not
migrate. It is not comparable to SN103, which has a contested leaderboard, a
mature adversarial test suite and fully re-derivable scores. It is a
fundamentally healthier design than SN90, which is one company paying itself
behind a permissioned gate — but SN90 at least has running infrastructure and
disclosed status tables, and Feval has neither.

**What makes it interesting anyway: the throne is empty and it costs $12.80 to
try.** That asymmetry does not exist on the other two.

### Recommended path

1. **Ask the operator one question before anything else:** which base model and
   which rollout protocol version is the live network on? The public repo says
   Qwen3.5-4B-Base / v8; the live miner says Qwen3-4B-Base / v14. Their answer
   determines whether the repo is usable at all. **Do not train before this.**
2. **Register a hotkey now regardless — 0.05 TAO is noise.** Immunity is
   ~16.7 h, `min_burn` can rise to 100 TAO, and holding a UID costs nothing.
3. **Build the offline grader harness first.** `rewards.py` is the complete,
   exact scorer and needs no GPU. You can measure candidate generations for free
   and iterate before renting anything. This is the single biggest efficiency
   available in this subnet.
4. **Target the instruction half hardest.** 16 of 32 rows are decided by ~28
   readable regex/count constraints. Training against a verifier you can read is
   strictly easier than training against a benchmark you cannot.
5. **Take the empty seat.** With no champions, `bootstrap_min_score = 0.0` means
   the first valid positive-scoring model becomes king at 62.5 % of the miner
   pool. Then the 99 % paired LCB works *for* you against every challenger.
6. **Size the position as a speculative bet, not a business.** Zero external
   miners, a one-day-old repo, an undocumented protocol that already disagrees
   with itself, and an owner currently taking 100 % of emission. Risk only what
   the $12.80 + a month of GPU rental represents to you.
7. **Watch three signals:** a second external Feval commitment appearing; the
   repo gaining real commit history and a matching protocol version; and UID 0's
   incentive dropping below 1.0. The last one is the cleanest proof that the
   mechanism has started paying miners rather than the owner.

---

## 13. Sources

**Code (as published)**
- https://github.com/center196/feval @ `45f5760` (created 2026-08-28 00:36 +07)
- Local: `/root/Bittensor/47/feval`
- `feval/constants.py`, `network.json`, `feval/champions.py`, `feval/rewards.py`,
  `feval/canonical.py`, `feval/schedule.py`, `feval/artifacts.py`,
  `feval/runtime.py`, `feval/validator.py`, `feval/inference.py`,
  `feval/chain.py`, `feval/config.py`, `pyproject.toml`, `.env.example`

**Chain** (finney, block 8,940,871)
- `Subtensor.subnet(47)`, `Subtensor.metagraph(47)`, `Subtensor.recycle(47)`
- `Subtensor.get_all_commitments(47)` — 85 commitments, 80 `evolai`-era, 1 `p:f3`
- `SubnetIdentitiesV3` — name/github/url, `get_subnet_hyperparameters(47)`

**Live miner artifacts** (fetched 2026-08-28)
- `https://huggingface.co/feval-center/miner-47-lora` — `adapter_config.json`
- `https://huggingface.co/datasets/feval-center/miner-47-rollouts` — `manifest.json`

**Upstream pins (all verified to resolve)**
- `Qwen/Qwen3.5-4B-Base` @ `daa9c16f371249f9ad1c75a9ed6f956c08ea08f5` (repo pin)
- `Qwen/Qwen3-4B-Base` @ `b1ecb62b18378adb8af264260fbbbd618222be87` (live pin)
- `nvidia/Nemotron-SFT-Math-v4` @ `84d42ad0cb960f07f951b9baa9ed2b46a5a18c66`
- `nvidia/Nemotron-RL-instruction_following` @ `3b253899665cb71334bb54c14eb5d91751beaad7`

**Social**
- https://x.com/Feval47 (subnet URL on chain; not fetched)

**Price reference**
- TAO ≈ $256 → α ≈ $0.787 at 0.003073 TAO/α
