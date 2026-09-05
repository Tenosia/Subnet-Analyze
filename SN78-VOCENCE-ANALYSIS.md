# Subnet 78 — Vocence — analysis

**Analysed:** 2026-08-19 · **Chain state read live from finney at block 8,875,714** · TAO $190.42, SN78 α = τ0.002089592 = **$0.3979**

| | |
| --- | --- |
| Netuid | 78 (`finney`) |
| Name | Vocence — "The voice layer for decentralized intelligence" |
| Operator | vocence-78 |
| Owner hotkey | `5Fk765B4CRBekwErwE5VxvveWhHztHSfsnsLt8cbDayDWsuk` (**= UID 0, the burn UID**) |
| Owner coldkey | `5FnQCJW2Rm1BijNBUJzPetcpZx43RWutYiyaxA8j88fy9i9L` |
| Site / docs | https://www.vocence.ai · /docs/getting-started · /dashboard |
| Code | https://github.com/vocence-78/vocence ([local checkout](vocence/)) |
| Discord | https://discord.gg/TWmfwJAtXG |
| Registered at | block 7,966,145 — **subnet is 126 days old** |

---

## 1. Goal of the subnet

Vocence is an **open, incentivized voice-intelligence subnet**. The long-term scope is PromptTTS, STT, STS, voice cloning and other multimodal voice tasks. **Q1 focus is PromptTTS only.**

Miners fine-tune a text-to-speech model that follows a natural-language prompt describing both *what* to say and *how* to say it:

> *"A calm middle-aged male voice with a warm tone, speaking slowly and clearly, reading the following sentence…"*

Validators measure three things: **content correctness** (does the speech match the text), **audio quality** (naturalness, absence of artifacts), and **prompt adherence** (does the voice match the described traits).

Everything runs through a standardized interface — canonical wrapper + Hugging Face repo + Chutes deployment — so outputs are directly comparable across miners.

---

## 2. What you do as a miner

**You fine-tune one specific model and deploy it as an HTTP endpoint. This is real ML training work — the only one of the three subnets analysed so far that requires a GPU.**

### The model is locked

From `vocence/domain/config.py:213-217`:

> *"SHA-256 of the locked `miner.py` that all miners must ship byte-for-byte. Miners fine-tune the **Qwen3 1.7B 12Hz voice-design model**; this fixed inference script prevents pre/post-processing, alternative models, and speaker-embedding injection through the inference path."*

```
CANONICAL_MINER_PY_SHA256 = "4e57d5ee0151681931d6601503fc8e1d21b9d2f22b2e359778727b14ee6ea212"
```

You cannot change the architecture. You cannot change the inference path. **The only thing you compete on is the quality of your fine-tuned weights.** That is unusually clean as a competition — and unusually unforgiving, because there is nowhere to hide engineering cleverness.

### The deliverable

A Hugging Face repo containing **exactly** these files — no more, no less:

| File | Replaceable |
| --- | --- |
| `miner.py` | **NO — byte-identical to canonical, SHA-256 enforced** |
| `model.safetensors` | **yes — your fine-tuned weights** |
| `speech_tokenizer/model.safetensors` | yes |
| `config.json`, `generation_config.json` | yes |
| `merges.txt`, `vocab.json`, `tokenizer_config.json`, `preprocessor_config.json` | yes |
| `speech_tokenizer/{config,configuration,preprocessor_config}.json` | yes |
| `vocence_config.yaml` | yes — must declare `model_name` matching the on-chain commit |
| `chute_config.yml` | yes — GPU/deploy config |
| `.gitattributes`, `.gitignore`, `README.md` | optional |

Combined `.safetensors` must be **≥ 50 MiB**. Any extra file → `extra_files:...` rejection.

### The engine contract

```python
Miner(path_hf_repo: Path)
warmup() -> None
generate_wav(instruction: str, text: str) -> tuple[np.ndarray, int]   # mono float32 PCM, sample rate
```

Served as **`POST /speak`** → `{"text": ..., "instruction": ...}` → raw WAV bytes. Plus `GET /health`.

### The loop

```
1. Fine-tune Qwen3 1.7B 12Hz voice-design           ← GPU, the actual work
2. Push weights to a Hugging Face repo (exact manifest)
3. Render chute_template/vocence_chute.py.jinja2 with your 4 variables
4. chutes build <module>:chute --local
5. chutes deploy <module>:chute --accept-fee        ← chute NAME must contain "vocence"
6. btcli register on netuid 78
7. vocence miner commit --chute-id <uuid>            ← commits model_name + revision + chute_id
8. wait for owner validation (1-hour cycle) → is_valid
9. accumulate 41+ evals in ≥2 validator buckets
10. beat every earlier eligible miner by 2pp
```

**Only four template variables may change:** `VOCENCE_REPO`, `VOCENCE_REVISION` (must be a 40-char hex SHA, not a branch), `VOCENCE_CHUTES_USER`, `VOCENCE_CHUTE_ID`. Anything else → `wrapper_hash_mismatch`.

---

## 3. Scoring logic

### 3.1 Task generation — derived from real audio, not written

Validators do **not** invent prompts. Each validator keeps a local corpus of English LibriVox clips (20–25 s, `CORPUS_LOCAL_DIR`, cap 10,000, oldest pruned). It picks a random clip and makes **one `gpt-audio-1.5` pointwise call** that returns two parallel views of the same voice:

**Structured spec (closed enums)** — drives scoring, never sent to you:

| Field | Values |
| --- | --- |
| `transcription` | exact words |
| `gender` | male / female / neutral |
| `pitch` | low / mid / high |
| `speed` | slow / normal / fast |
| `age_group` | child / young_adult / adult / senior |
| `emotion` | neutral / happy / sad / angry / calm / excited / serious / fearful |
| `tone` | warm / cold / friendly / formal / casual / authoritative |
| `accent` | us / uk / au / in / neutral / other |

**Natural-language `instruction`** — what you actually receive:

```json
{ "text": "<transcription>",
  "instruction": "An adult female with an American accent, speaking at a normal pace in a mid-range pitch, sounding neutral and formal throughout" }
```

> The natural-language form is **never** consumed by scoring. It exists to test that your model handles realistic user-style prompts *"rather than overfitting to a deterministic `key: value` template."*

**You must pass `text` and `instruction` to your model verbatim.** Any rewriting, paraphrasing, expansion, normalization, prosody-tagging, or SSML injection is a **blacklist** offence.

### 3.2 Evaluation — two judge calls per miner

1. **Pointwise extraction** on your audio → the same 8-field structured schema.
2. **Pairwise naturalness** — the judge hears the source clip and yours, presentation order randomized, and answers which sounds more natural as human speech.

Judge temperature is **0.0**. Trait-extractor drift (`"american"` → `"us"`) is coerced through an alias map.

### 3.3 Element scoring

| Element | Rule | Weight |
| --- | --- | --- |
| `script` | `1 − WER(spec, yours)`, clamped `[0,1]`; Levenshtein on lowercase word tokens | **0.30** |
| `naturalness` | 1.0 if the judge picks your clip, else 0.0 | **0.15** |
| `gender` | exact enum match | 0.10 |
| `speed` | ordinal: exact 1.0, **off-by-one 0.5**, else 0.0 | 0.10 |
| `emotion` | exact enum match | 0.10 |
| `age_group` | ordinal: exact 1.0, off-by-one 0.5, else 0.0 | 0.10 |
| `pitch` | ordinal: exact 1.0, off-by-one 0.5, else 0.0 | 0.05 |
| `accent` | exact enum match | 0.05 |
| `tone` | exact enum match | 0.05 |
| | | **1.00** |

### 3.4 The pass threshold is the whole game

```
generated_wins = (score >= PASS_THRESHOLD)      PASS_THRESHOLD = 0.9
```

> *"`generated_wins` is the ranking primitive.* Per-validator and global aggregates both use the binary win/lose signal. **The continuous `score` and `breakdown` are stored for diagnostics and dashboards but do not drive winner selection.**"

**This is the single most important fact about mining Vocence.** Your ranking signal is `wins / total` where a win means clearing **0.90** on a weighted sum. A score of 0.89 is worth exactly as much as 0.10 — zero. There is no partial credit anywhere in the ranking path.

### 3.5 Global aggregation

Each validator generates samples locally, then weight-setting is global:

```
validator_weight = stake ** VALIDATOR_WEIGHT_EXPONENT      (default 0.25 — fourth root)

global_win_rate(miner) = Σ(stake_v**0.25 · win_rate_v) / Σ(stake_v**0.25)
```

The fourth-root exponent deliberately compresses the gap between large and small validators while preserving stake ordering.

### 3.6 Eligibility and the winner rule

**⚠️ The docs and the code disagree. The code is authoritative** — `vocence/domain/config.py:131-132` hardcodes these values *specifically so validators cannot diverge*, and the git history confirms the change: *"fix: lower validator-count gates to 2 (hardcoded) for the 2-validator subnet."*

| Constant | `docs/scoring.md` says | **`config.py` actually says** |
| --- | --- | --- |
| `MIN_ACTIVE_VALIDATORS_FOR_GLOBAL_SCORING` | 3 | **2** |
| `MIN_VALIDATOR_APPEARANCES_FOR_ELIGIBILITY` | 3 | **2** |
| `MIN_EVALS_TO_COMPETE` | 40 | 40 (need **>40**, so 41+) |
| `THRESHOLD_MARGIN` | 0.02 | 0.02 (hardcoded, not env-tunable) |
| `PASS_THRESHOLD` | 0.9 | 0.9 |
| `MAX_EVALS_FOR_SCORING` | 50 | 50 |

**To be eligible:** >40 evaluations in at least **2** validator buckets.

**To win:**

```
candidate_global_win_rate >= P_global_win_rate + 0.02      for EVERY earlier eligible miner P
```

Miners are ordered by **chain commit block, ascending** — earlier commit = earlier participant. And the **owner's base model is injected as a synthetic participant committed at block 1000**, so it is *always* first in that ordering.

> *"Prevent miners from using the base model to win. The base model is a normal participant… but with priority: it is treated as committed at block 1000, so any miner must beat its win rate by the threshold margin to become the winner."*

Base model: `concil859856/qwen3-voicedesign-base`, weights hash pinned so anyone who commits the base model under their own chute gets grouped with the owner.

**Tie-breaks** (deterministic, so honest validators converge): higher `global_win_rate` → higher `eligible_validator_count` → higher `weighted_evals` → **earlier commit block** → lexicographically smaller hotkey.

### 3.7 Winner-take-all, or burn

The winner gets **weight 1.0**. Everyone else gets **zero**. There is no second place.

If any of these hold, validators set weight `1.0` on **UID 0 (burn)** and nobody earns:

1. Fewer than 2 active validators
2. Fewer than 2 matched in `VALIDATOR_BUCKETS_JSON`
3. No usable global scoring data
4. No miner satisfies eligibility
5. **No eligible miner beats every earlier eligible miner by 2pp**

> *"Burning is preferred over setting inconsistent non-burn weights from weak or partial evidence."*

Weights are set every **`CYCLE_LENGTH = 150` blocks (~30 min)**, at `block % 150 == 15`, ± 2 blocks tolerance.

---

## 4. Live competition landscape (2026-08-19)

### Chain state

| | |
| --- | --- |
| UIDs | **256 / 256 — full** |
| Validator permits | **8** |
| UIDs with stake > 0 | 11 |
| Registration | allowed; recycle **τ0.0005 ≈ $0.10** |
| Immunity period | **5,000 blocks ≈ 16.7 hours** |
| Tempo | 360 blocks (1.2 h) → 20 tempos/day |
| Commit-reveal | enabled, period 1 |
| α price | τ0.002089592 = **$0.3979** |
| α emission | 1.0 α/block ≈ 7,200 α/day ≈ $2,865/day |

### The incentive distribution — this is the headline

```
UIDs with nonzero miner INCENTIVE: 1
  uid  98   incentive 1.000000   emission 147.60 α/tempo   stake 1,771
  all other 255 UIDs: incentive 0.000000
```

**One miner holds the entire subnet.** UID 98 (`5G6M6aWF1wRQez3YjmHWqQhq1kk7oE3dtsXsCRDcpVcfon6e`) has incentive exactly 1.0. Every other miner earns exactly nothing.

147.60 α/tempo = **41% of the 360 α emitted per tempo** — precisely the standard dTAO miner allocation, confirming a single miner is absorbing 100% of the miner pool.

### Emission by UID (α per tempo)

| UID | Emission | Stake | Role |
| --- | --- | --- | --- |
| **98** | **147.60** | 1,771 | **the winning miner** |
| 0 | 100.62 | 917,587 | owner / burn UID — validator stake |
| 200 | 37.55 | 339,080 | validator |
| 198 | 3.31 | 30,106 | validator |
| 210 | 2.86 | 29,613 | validator |
| 211 | 1.82 | 12,832 | validator |
| 11 | 1.45 | 13,791 | validator |

The owner holds **917,587 α staked on UID 0** — by far the dominant validator stake. Note that under `VALIDATOR_WEIGHT_EXPONENT = 0.25`, the owner's 917k stake gives it weight `917587^0.25 ≈ 30.9` versus a 12.8k-stake validator's `≈ 10.6` — only ~3× the influence despite ~70× the stake. The fourth root is doing real work here.

---

## 5. Miner economics

| | |
| --- | --- |
| Miner pool | 147.60 α/tempo × 20 tempos = **2,952 α/day** |
| **Winner take** | **2,952 α/day ≈ $1,175/day** |
| **Everyone else** | **$0** |

### Costs

| Item | Cost |
| --- | --- |
| Registration burn | τ0.0005 ≈ **$0.10** (trivially cheap) |
| **Fine-tuning GPU** | your biggest cost — Qwen3 1.7B fine-tune, realistically A100/H100 hours |
| **Chutes hosting** | continuous — 1 GPU, **≥16 GB VRAM**, `shutdown_after_seconds: 10000`, must stay **hot** |
| Hugging Face | free tier fine |
| Ongoing | the chute must stay hot 24/7 or you fail validation (`chute_not_running`) |

**The risk profile is the inverse of SN76.** Entry is nearly free but the running cost is real and continuous, and the payoff is strictly binary: $1,175/day or $0/day.

---

## 6. How to become a winner

### What you are actually up against

To take the crown from UID 98 you must clear **all** of these simultaneously:

1. Accumulate **41+ evaluations in ≥2 validator buckets**
2. Beat the **owner's base model** (committed at block 1000, so always first in order) by **2pp** of win rate
3. Beat **every other earlier-committed eligible miner** — including UID 98 — by **2pp**
4. Where "win rate" means fraction of evaluations scoring **≥ 0.90** on the weighted sum

Note the asymmetry: the incumbent needs only to hold its rate; **you** must clear it by 2 percentage points. Commit order is a permanent advantage, and it is also the 4th tie-break. This mechanism structurally favours whoever got there first.

### Where the points actually are

At `PASS_THRESHOLD = 0.9`, you need near-perfect element scores. Working backwards from the weights:

- **`script` at 0.30 is the largest single term and the most controllable.** It is `1 − WER`. WER is a solved-ish engineering problem — clean phoneme coverage, no truncation, no hallucinated words, no dropped sentence endings on 20–25 s clips. **Any model that mangles long-form text cannot reach 0.9 regardless of how good its voice control is.** Fix this first.
- **`naturalness` at 0.15 is binary and adversarial** — you are pairwise-compared against *real LibriVox human audio*. Winning that coin flip is genuinely hard; assume you lose it often. If you lose naturalness (0.15) you need `0.9 / 0.85 = 94.1%` of every remaining element to still pass. That is brutal, and it means **naturalness is effectively a second gate, not a soft bonus.**
- **The ordinal trio (`pitch`, `speed`, `age_group`, total 0.25) gives half credit for off-by-one.** Being approximately right is worth something here and nowhere else. Train so that errors land adjacent rather than far.
- **The exact-match four (`gender` 0.10, `emotion` 0.10, `tone` 0.05, `accent` 0.05) are all-or-nothing.** `gender` and `emotion` at 0.10 each are the highest-value binary traits — a gender miss alone costs you the entire margin.

**Concrete arithmetic:** win naturalness + perfect traits + WER 0.03 → score ≈ 0.99, pass. Lose naturalness + perfect traits + perfect WER → 0.85, **fail**. Lose naturalness and you cannot pass at all. **Naturalness is not 15% of your score — it is a prerequisite.**

### Strategy

1. **Read the corpus.** Source audio is English LibriVox, 20–25 s. Your fine-tuning distribution should match that: long-form read speech, not short commands.
2. **Train against the judge's enum vocabulary.** Scoring is against `gpt-audio-1.5`'s extraction of *your* audio into eight closed enums. You are not optimizing "good speech" — you are optimizing "speech that this specific judge labels with the same eight values it assigned the source." Build a local eval loop that replicates it.
3. **Prompts vary in phrasing by design.** The natural-language instruction is regenerated per source clip specifically to punish template overfitting. Train on paraphrase diversity.
4. **Commit early.** Commit order is both the threshold-chain ordering and the 4th tie-break. A hotkey that commits sooner needs strictly less to win, forever.
5. **Budget only 2 commits.** You get **2 valid on-chain commits** post-block-8,270,310, total. That is not two per round — that is two, ever, for that hotkey. Do not burn one on an untested model.

### Honest assessment

This subnet has **one prize and a well-defended incumbent**. Unlike SN76, where four tracks and a top-3 split give several ways in, here there is exactly one seat, and taking it requires beating a fine-tuned model *and* the owner's baseline by a hard margin, on a metric with a 0.9 cliff and an adversarial human-audio comparison built in.

The upside is that the competition surface is unusually pure — locked architecture, locked inference script, published weights and metric. If you can genuinely out-train the field on Qwen3 TTS, nothing else stands in the way. If you cannot, no amount of engineering, infrastructure, or ops skill will substitute.

---

## 7. Rules you must keep

### Auto-reject (recoverable — fix and re-commit)

| Rule | Failure code |
| --- | --- |
| `miner.py` byte-identical to canonical | `miner_py_hash_mismatch` |
| Only manifest files in the repo | `extra_files:...` |
| All required files present | `missing_required_files:...` |
| Weights as `.safetensors` only (no `.bin`/`.pt`/`.pth`/`.ckpt`) | `safetensors_missing` |
| Combined `.safetensors` ≥ 50 MiB | `safetensors_below_min_size` |
| `vocence_config.yaml` `model_name` == on-chain commit | `model_name_mismatch:yaml=...` |
| Wrapper modified beyond the 4 approved variables | `wrapper_hash_mismatch` |
| Chute **name** contains `vocence` (case-insensitive) | `chute_name_missing_vocence` |
| Chute is hot | `chute_not_running` |
| `model_revision` is a 40-char hex SHA, not a branch/tag | `wrapper_revision_not_sha` → **blacklist if repeated** |
| **≤ 2 valid on-chain commits** at/after block 8,270,310 | `too_many_commits` → **blacklist if repeated** |
| Weights not byte-identical to an earlier miner | `duplicate_model:earliest_uid=<n>` |
| Per-tensor fingerprint < 95% match vs **every** row ever stored | `tensor_clone_of_existing:...` |

Validation runs on a **1-hour cycle**. Expensive checks (weight download, tensor fingerprint) are cached per `(model, revision)`.

> Commits **before block 8,270,310** are ignored entirely — *"treated as if it never happened."* A hotkey that only ever committed pre-cutover is **invisible to the subnet**.

### Blacklist (permanent, no appeal)

- Copying another miner's weights **in any form** — byte clone, repackage, rename/re-shard, format conversion, ε-noise, precision roundtrip, dtype conversion, partial-layer replacement
- Sybil: multiple hotkeys serving the same effective model, or coordinating across hotkeys you control
- Repeatedly landing near-misses just under the 95% dedup threshold
- Proxying `/speak` to another chute, returning pre-recorded audio, replaying cached outputs
- **Modifying `text` or `instruction` before passing them to your model** — any "prompt enrichment"
- Returning audio that doesn't match the requested text or traits
- Serving different quality to different validator UIDs
- Loading weights at runtime from any repo other than your declared `model_name`
- Probing the validation surface
- *"Any form of cheating not listed above — if it looks like gaming, it gets you blacklisted"*

> *"Once blacklisted, every future commit from that hotkey is excluded… The blacklist is hotkey-scoped and permanent."* Applied within ≤1 hour, pending evaluations discarded, **no appeal process**.

Note the dedup rule is **first-stored-wins permanently** — a rejected fingerprint is *not* stored, so the original keeps its claim forever.

---

## 8. Device / hardware conditions

| | Miner | Validator |
| --- | --- | --- |
| **Fine-tuning** | **GPU required** — Qwen3 1.7B 12Hz. Not specified by the subnet; realistically 24–80 GB VRAM depending on method | — |
| **Serving** | on **Chutes**, not your hardware: `gpu_count: 1`, `min_vram_gb_per_gpu: 16` | — |
| **Uptime** | your chute must stay **hot** 24/7 or you fail validation | full-time |
| Local machine | modest — build/deploy only | Docker + Watchtower, Postgres |
| Storage | HF repo (model + speech tokenizer) | local LibriVox corpus, up to 10,000 clips |
| Python | 3.12 (`.python-version`), `uv` tooling | same |

Chute deploy config you control: `shutdown_after_seconds: 10000`, `concurrency: 1`, `max_instances: 1`, `scaling_threshold: 0.5`.

> **Note for this operator:** this is the first of the three subnets that needs **real GPU compute**, and the serving side is continuous. The BEAM box at 46.225.140.58 (2 cores, 3.7 GB RAM, no GPU) is irrelevant to this subnet in both directions — it cannot fine-tune, and it does not need to, because serving happens on Chutes. Your costs move from "a machine you own" to "GPU hours you rent" plus continuous Chutes hosting. That is a cleaner separation than SN66, but it is a real recurring bill against a payoff that is $0 until you hold the single crown.

---

## 9. Third-party conditions

**This subnet has the heaviest third-party dependency of the three analysed.**

| Dependency | Detail | Risk |
| --- | --- | --- |
| **Chutes** | **Mandatory.** Your model is deployed and served on Chutes. Chute **name** must contain `vocence`. | Hard dependency — no Chutes account, no mining. Continuous hosting cost. |
| **Hugging Face** | **Mandatory.** Weights live in an HF repo, pinned by 40-char commit SHA. | Repo must stay public and reachable or you auto-reject. |
| **`gpt-audio-1.5`** | The judge. Every score comes from OpenAI-family audio model calls (1 pointwise on source + 2 per miner). | **You are optimizing against a closed third-party model.** If its behaviour drifts, every miner's score moves and you have no visibility. |
| **Owner API** | Centralized service: blocklist, dashboard telemetry, evaluation submission. Endpoint **provided by the Vocence team**. | Owner controls the blocklist — permanent, no appeal. |
| **Hippius** | S3-compatible storage for validator sample buckets. Validators need readonly creds for *every peer* via `VALIDATOR_BUCKETS_JSON`. | Validator-side; a missing/unreadable bucket reduces coverage and can force a **burn**. |
| **Chutes permission** | **Validators must be granted access by the Vocence team** to call miners' chutes. | Validating is permissioned, not open. |
| Bittensor | `btcli` wallet, register, commit | — |

**Centralization assessment:** running a validator requires the team to grant you a Chutes key, hand you the owner API endpoint, and issue Hippius sub-bucket keys. That is three separate gates controlled by the operator. Combined with the owner holding 917k stake on UID 0 and injecting its own base model as the miner everyone must beat, the operator's control over this subnet is substantially higher than SN76's.

---

## 10. Risks

1. **Winner-take-all with one seat.** Live chain state confirms it: 1 UID with incentive, 255 with zero. Second place earns the same as last place.
2. **Entrenched incumbent + owner baseline.** You must clear *every* earlier eligible miner by 2pp, and the owner's base model is permanently first in line at block 1000. Commit order is a structural, permanent advantage you cannot buy back.
3. **The 0.9 cliff.** Scoring is binary per evaluation. 0.899 pays nothing. And losing the naturalness coin-flip (0.15) mathematically caps you at 0.85 — below threshold no matter how perfect everything else is.
4. **Two commits, ever.** Post-block-8,270,310 you get 2 valid commits per hotkey. A third is auto-rejected and repeats get you blacklisted.
5. **Blacklist is permanent with no appeal**, and the rule list is explicitly non-exhaustive: *"if it looks like gaming, it gets you blacklisted."*
6. **Docs contradict code** on the validator-count gates (3 vs 2). If you had planned against the published docs you would have modelled eligibility wrong. Always read `config.py`.
7. **Burn is the default outcome.** Five separate conditions trigger it, and the subnet explicitly prefers burning to setting weak weights. Only 8 validator permits exist and the gate needs 2 active — a thin margin.
8. **Judge dependency.** Your entire score comes from a closed third-party audio model at temperature 0. Its drift is your risk.
9. **Continuous cost, binary payoff.** GPU fine-tuning plus 24/7 Chutes hosting, against $0 until you hold the crown.
10. **Q1 scope only.** PromptTTS is stated as the *initial* implementation. Everything you tune could be re-weighted when STT/STS arrive.

---

## 11. Verdict

| | SN66 Conjectures | SN76 Phylax | **SN78 Vocence** |
| --- | --- | --- | --- |
| Work | human writes Lean proofs | write a detector program | **fine-tune a TTS model** |
| Skill needed | research maths + Lean | security engineering | **ML / speech training** |
| Miner emissions | **none** (100% to treasury) | yes | yes |
| Paying places | 1 per bounty | 3 per track × 4 tracks | **exactly 1, network-wide** |
| Entry cost | $95/attempt | ~$21 stake | ~$0.10 burn |
| Running cost | none | inference spend | **GPU + 24/7 Chutes hosting** |
| GPU | no | no | **yes** |
| Winner take | ~$5,157 one-off | ~$224/day | **~$1,175/day** |
| Owner centralization | high | moderate | **highest** |

Vocence pays the most of the three — **$1,175/day, more than five times SN76's top slot** — because it concentrates everything into one seat. That is the whole trade: highest payoff, narrowest door.

The competition itself is admirably clean. The architecture is locked, the inference script is hash-pinned, the metric is published, and there is no infrastructure edge to exploit. Whoever trains the best Qwen3 TTS fine-tune wins, full stop. For an operator whose strength is ops and systems tuning — which is where the CX23/BEAM experience lives — that is precisely the wrong shape of competition. **Nothing you are good at transfers here.**

**Recommended path:**

1. **Do not register yet.** Registration is cheap ($0.10) but you only get **2 commits ever**, and a UID on a full subnet with 16.7-hour immunity is not worth holding idle.
2. **First, replicate the judge locally.** Build the scoring loop — LibriVox clips → `gpt-audio-1.5` spec extraction → your model → element scoring → the 0.9 gate. Until you can measure win rate offline, you are guessing.
3. **Measure the base model's win rate first.** `concil859856/qwen3-voicedesign-base` is public. Score it through your local loop. That number plus 2pp is the actual bar — and if the stock base model is already scoring well, the gap you must close is small; if it scores poorly, the incumbent at UID 98 has found something you would need to match.
4. **Fix WER before voice control.** 0.30 weight, fully controllable, and no amount of trait accuracy rescues a model that mangles 20–25 s passages.
5. **Treat naturalness as a gate, not a weight.** If you lose it you cannot reach 0.9. Optimize for winning that pairwise comparison against human LibriVox audio, or accept that you will never pass.
6. Only commit once your local win rate clears the base model by a comfortable margin — you cannot afford to spend a commit learning.

**Honest bottom line:** of the three subnets analysed, this is the highest-paying and the one where your existing skillset helps least. Enter it only if you want to build genuine speech-model training capability, not as an extension of the BEAM operation.

---

*Sources: local checkout of `vocence-78/vocence` (`README.md`, `docs/scoring.md`, `docs/base-model-protocol.md`, `miner_sample/MINER_GUIDE.md`, `vocence/domain/config.py`, `vocence/ranking/global_scoring.py`, `vocence/pipeline/evaluation.py`, `miner_sample/example_repo/{miner.py,chute_config.yml}`, `CHANGELOG.md`); live finney chain state for netuid 78 at block 8,875,714 (subnet info, hyperparameters, metagraph incentive/emission/stake); vocence.ai.*
