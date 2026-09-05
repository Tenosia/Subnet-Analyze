# Subnet 80 — OpenRoboto — analysis

**Analysed:** 2026-08-19 · **Chain state read live from finney at block 8,879,501** · TAO $190.42, SN80 α = τ0.014757472 = **$2.8100**

| | |
| --- | --- |
| Netuid | 80 (`finney`) |
| Name | OpenRoboto — "An open competition on Bittensor for continuously improving robotics models" |
| Operator | openroboto-ai · contact `riccardo@openroboto.ai` |
| Owner hotkey | `5HTwtytUfeUhK4p8NRCGppjUZrhJ5ckoRHeVWEQafg2N1Zo6` (**= UID 0**) |
| Site | https://www.openroboto.ai · [docs](https://www.openroboto.ai/#/docs) · [leaderboard](https://www.openroboto.ai/#/benchmark) · [queue](https://www.openroboto.ai/#/queue) |
| API | https://api.openroboto.ai (public, no key) |
| Code | https://github.com/openroboto-ai/openroboto-subnet ([local checkout](openroboto-subnet/)) |
| Eval toolkit | https://github.com/openroboto-ai/openroboto-evaluation |
| Registered at | block 7,151,800 — **subnet is 240 days old** |

---

## 1. Goal of the subnet

OpenRoboto is a competition to **improve open vision-language-action (VLA) robotics models**.

Miners fine-tune **π0.5** (~3B params, [openpi](https://github.com/Physical-Intelligence/openpi) by Physical Intelligence) and publish full checkpoints on Hugging Face. The subnet evaluates every submission in **MuJoCo simulation on the LIBERO task suites**, ranks results against the base-model baseline, and pays through Bittensor emissions.

The output is genuinely open: every submitted model is a downloadable artifact, and every score is reproducible from a publicly verifiable seed.

The architecture is unusually well-documented and auditable. Every mechanism leaves a public trace — a chain transaction, an API response, a Hugging Face commit, a drand beacon round. The docs are explicit: *"Nothing here needs to be taken on trust."*

---

## 2. What you do as a miner

**You fine-tune a robotics model on a GPU, upload it, pay a fee, and announce it on chain. This is model training — the same category as SN78 Vocence, but robotics instead of speech.**

### The pipeline

```
1. Read control.json                      → current round, fee, hyperparameters
2. Download training data + π0.5 base     → gs://openpi-assets/checkpoints/pi05_base
3. Train in the openpi-runner container   → GPU work, any recipe you like
4. Merge LoRA into the base               → MUST export a complete checkpoint
5. Upload to Hugging Face                 → repo name must end in your hotkey's last 12 chars
6. python rt.py submit                    → upload + burn 0.1 TAO + announce, one command
7. Wait for evaluation                     → 6 LIBERO suites in MuJoCo
```

### What must be in the uploaded repo

| Requirement | Detail |
| --- | --- |
| Checkpoint format (one of) | openpi JAX `params/` directory (orbax OCDBT) **or** PyTorch `model.safetensors` |
| Normalization stats | `assets/physical-intelligence/libero/norm_stats.json` (state dim 8, action dim 7) |
| Architecture | must match π0.5 (`pi05_libero`), **2.5B–4.5B parameters** |
| **NOT accepted** | **a bare LoRA adapter** — the worker performs no merging |

**Any training recipe is allowed, LoRA included.** But you must merge and export the full model. The reference hyperparameters in `control.json` today are: 3 epochs, batch size 4, lr 1e-4, warmup 0.05, grad accumulation 8, LoRA r=32 / alpha=64 / dropout=0.1, targeting `q_proj`/`k_proj`/`v_proj`/`o_proj`. Those are *reference values*, not requirements.

### Free pre-check before you pay

```bash
uv run libero_eval/check_model.py --model /path/to/checkpoint --config pi05_libero
# exit 0 = will be accepted, exit 1 = would be rejected (reasons printed)
```

Pure CPU, public, and it costs nothing. **Run it every time.** 14 of 100 tracked tasks are `eval_failed` and 8 more `rejected` — that is 22 miners who paid the fee and got nothing.

---

## 3. Scoring logic

### 3.1 The evaluation

Submissions run in **MuJoCo on six LIBERO task suites**:

| Suite | Type |
| --- | --- |
| `libero_spatial` | base |
| `libero_object` | base |
| `libero_goal` | base |
| `libero_10` | base |
| `libero_object_swap` | **perturbation** |
| `libero_spatial_swap` | **perturbation** |

The two swap suites exist for a specific reason, stated plainly in the docs:

> *"An internal red-team study showed the four base suites alone could be saturated for roughly $50 of GPU time by memorizing public demonstrations. The swap perturbations showed zero transfer from that attack — an attacker has to pay separately for each perturbation dimension."*

Your score is the **mean across the six suites**.

### 3.2 Deterministic, unpredictable seeds

```
seed = uint32( last 4 bytes of SHA256( "{block_hash}:{round_num}:{drand_randomness}" ) )
```

Two independent public beacons, neither controllable by miner or operator:
1. **Bittensor block hash** of the block containing your commitment — you cannot choose which block includes your transaction
2. **drand** — the public distributed randomness beacon, fetched at task creation

Unpredictable before submission, frozen after, and verifiable byte-for-byte at `https://api.drand.sh/public/{round}`. If drand is temporarily unavailable the task enters `seed_failed`, a **non-terminal retryable** state — you are never rejected for the operator's infrastructure problem.

### 3.3 Ranking — king-of-the-hill, and this is the whole story

The subnet does **not** rank by raw score. It uses a challenge system:

1. Scored miners are ordered by earliest scoring time; the first becomes **champion** (Rank 1).
2. Each subsequent miner **challenges the champion**: the challenger's average must exceed the champion's by at least **`champion_margin` = 0.01**.
3. Challenge succeeds → challenger becomes champion, old champion drops to Rank 2, rest shift down.
4. **Challenge fails → the challenger does not appear on the board at all.**
5. Board is capped at **Top 3**, weights **70 / 20 / 10**.

Two consequences the docs call out:

- Copying the champion's weights **cannot** dethrone it — a copy ties, and a tie loses by margin.
- A settled round's champion is **held** until someone clears the bar in a later round.

**This is the harshest ranking rule of the five subnets analysed.** You do not get partial credit for being 4th, or 10th, or for beating the baseline by a wide margin. You beat the incumbent by 0.01, or you are invisible.

### 3.4 The evaluation fee (burn)

Every submission is preceded by **burning 0.1 TAO** (`control.json` → `payment.burn_rate_tao`), currently **$19.04**.

Destroyed, not transferred — *"There is no recipient. The operator earns nothing from fees, which removes any incentive to farm submissions or sell evaluation slots."*

The backend verifies fail-closed against the chain:

1. The burn tx exists in the claimed block (single-block lookup, no trust in your claim)
2. The signer is the submitting hotkey or its owning coldkey
3. The amount matches the published rate
4. The tx has not been used by any prior submission (anti-replay, strict exact hash match — no prefix matching)
5. **The burn block is within 10 blocks (~2 minutes) of the commitment block**

> ⚠️ **The 2-minute window is a real trap.** The docs warn explicitly: *"Do not run `burn` and `announce` as separate manual steps — any delay (wallet prompt, network retry, debugging) will exceed the window, the submission is rejected, and the fee is lost."* **Always use `rt.py submit`**, which chains upload → burn → announce in one command.

Failed verification = `burn_rejected`, terminal, **and the burned TAO is not refunded**.

### 3.5 Weights on chain

The backend resolves the ranking, a lightweight validator reads it from a read-only API, normalizes to u16, and calls `set_weights` on netuid 80. Validators run no benchmarks — they are pure weight relays.

---

## 4. Live competition landscape (2026-08-19)

### Round 1 status

| | |
| --- | --- |
| Round | 1, **live** (still the first round after 240 days) |
| Baseline π0.5 | **0.502917** (3 trials, std 0.001) |
| **Submissions this round** | **132** |
| Champion | uid 242, score **0.8566**, `held: true`, settled 2026-08-17 |

### The leaderboard — all of it

| Rank | UID | Score | Δ vs baseline | Suites | Weight | HF repo |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 242 | **0.8566** | +0.3537 | 6/6 | 70% | `poppy0619/pi05-RuKL3HneRr8K` |
| 2 | 231 | 0.8461 | +0.3432 | 6/6 | 20% | `0xjulius/pi05-afBJhgBJD6KZ` |
| 3 | 218 | 0.8298 | +0.3269 | 12/12 | 10% | `Roboterr/pi05-4xJrD6TomxRp` |

**That's the entire board. Three rows, out of 132 submissions.**

### Queue outcomes (100 tracked tasks)

| Status | Count |
| --- | --- |
| evaluated | 74 |
| **eval_failed** | **14** |
| **rejected** | **8** |
| pending | 2 |
| evaluating | 2 |

Rejection reasons (public via `/api/v1/scan-rejections`): **plagiarism_detected ×3**, burn_rejected ×1, hf_commit_missing ×1, HF file structure error ×1, plus 2 unlabelled. The weight-fingerprinting anti-plagiarism system is live and catching people.

**So: ~74 miners paid $19 and received a real score. Three of them are on the board. The other ~71 earn nothing.**

### Chain state

| | |
| --- | --- |
| UIDs | 256 / 256 |
| Validator permits | 12 |
| UIDs with stake > 0 | 22 |
| Registration | allowed; recycle **τ0.00055 ≈ $0.10** |
| Immunity period | 5,000 blocks ≈ 16.7 hours |
| Tempo | 360 blocks (1.2 h) → 20 tempos/day |
| α price | τ0.014757472 = **$2.8100 — the highest of the five subnets analysed** |
| α emission | 1.0 α/block ≈ 7,200 α/day |

### ⚠️ The single most important economic fact

```
UIDs with nonzero miner incentive: 4

  uid   0   incentive 0.906203   ← 90.6%
  uid 242   incentive 0.065644   ← 6.6%  (champion)
  uid 231   incentive 0.018753   ← 1.9%  (rank 2)
  uid 218   incentive 0.009369   ← 0.9%  (rank 3)
```

**90.6% of the miner incentive vector is assigned to UID 0** — and I verified that **UID 0's hotkey is exactly the subnet owner's hotkey** (`5HTwtytUfeUhK4p8NRCGppjUZrhJ5ckoRHeVWEQafg2N1Zo6`).

The remaining 9.4% splits 6.56 : 1.88 : 0.94 across the top three — precisely the documented **70/20/10**. So the published mechanism is being applied faithfully; it is simply being applied to **less than a tenth of the pool**.

**Nothing in the repository documentation explains this allocation.** `SUBNET_OVERVIEW.md` describes only the 70/20/10 split across Top 3. On Bittensor, UID 0 is conventionally used as a burn destination, and many subnets deliberately withhold emissions while a subnet matures — but here UID 0 is a *registered neuron owned by the operator*, not an unreachable address, so emission directed there is received rather than destroyed. I cannot tell from public data whether this is intended as a burn, a maturity hold-back, or operator revenue. **Ask in Discord before committing — this single number changes the subnet's economics by more than 10×.**

---

## 5. Miner economics

| Position | Incentive share | α/tempo | α/day | **USD/day** |
| --- | --- | --- | --- | --- |
| **Champion (rank 1)** | 6.56% | 9.69 | 193.8 | **$545** |
| Rank 2 | 1.88% | 2.77 | 55.4 | $156 |
| Rank 3 | 0.94% | 1.38 | 27.7 | $78 |
| **Rank 4+ / unranked** | 0% | 0 | 0 | **$0** |
| *UID 0 (owner)* | *90.6%* | *133.8* | *2,676* | *$7,520* |

If the 90.6% were released to the competition, rank 1 would be worth roughly **$5,800/day**. As things stand it is $545/day.

### Costs

| Item | Cost |
| --- | --- |
| Registration burn | τ0.00055 ≈ **$0.10** (negligible) |
| **Evaluation fee** | **0.1 TAO = $19.04 per submission**, non-refundable, burned |
| **GPU for training** | 24 GB VRAM minimum, A100 80GB recommended |
| RAM / Disk | 32 GB / 200 GB SSD min; 64 GB / 500 GB NVMe recommended |
| Hugging Face | free tier |
| Ongoing | **none** — no server, no uptime, nothing to keep online |

**Cost structure is the inverse of SN79.** Nothing runs continuously; you pay in GPU hours and $19 per attempt.

---

## 6. How to become a winner

### The bar, precisely

| | |
| --- | --- |
| Baseline π0.5 | 0.502917 |
| Current champion | **0.8566** |
| **You must score** | **≥ 0.8666** (champion + 0.01 margin) |
| Anything below | invisible — no rank, no emission, $19 gone |

Beating the baseline by +0.35 is not enough. Rank 2 at 0.8461 beat the baseline by +0.34 and earns $156/day; a miner at 0.8460 earns nothing at all.

### What actually decides it

1. **The swap suites are where the competition is really settled.** Four base suites can be saturated by memorizing public demos for ~$50 of GPU — the operator red-teamed exactly that. `libero_object_swap` and `libero_spatial_swap` showed **zero transfer** from that attack. So the top of the board is decided by *generalization*, not memorization. Any effort that improves base-suite scores while leaving swap performance flat is wasted effort.

2. **You cannot copy your way in.** Weight fingerprinting via HF LFS metadata (sha256 of every shard) is live and has already caught 3 plagiarism attempts in round 1. And even a perfect copy of the champion *ties*, and a tie fails the margin.

3. **Merge your LoRA.** The single most common self-inflicted rejection. The worker does no merging. 14 `eval_failed` in 100 tasks — run `check_model.py` before every submission; it is free and CPU-only.

4. **Use `rt.py submit`.** The 10-block burn↔announce window will eat your $19 if you run the steps by hand.

5. **Budget for multiple attempts.** At $19 each with a hard 0.8666 bar, assume several submissions. A serious campaign is a few hundred dollars in fees plus A100 hours.

### Honest assessment

The engineering here is the best of the five subnets analysed — verifiable seeds from two independent beacons, public pre-check tooling, published rejection reasons, live plagiarism detection, an auditable API with no key required, and an anti-gaming table that names each attack and its countermeasure. The operator has clearly thought hard about honesty.

But the *economics* are the problem, and they are two problems stacked:

- **Only 3 of 132 submissions earn anything**, and the margin rule means near-misses earn exactly zero rather than a proportional share.
- **90.6% of the pool is not in the competition at all.**

Together these mean the realistic outcome for a new entrant is: spend A100 hours, pay $19 several times, score somewhere between 0.50 and 0.85, and receive nothing.

---

## 7. Rules you must keep

| Rule | Consequence |
| --- | --- |
| Upload a **complete merged checkpoint**, never a bare LoRA adapter | CPU pre-check fails → `eval_failed`, fee lost |
| Architecture matches π0.5, **2.5B–4.5B params** | rejected |
| Include `assets/physical-intelligence/libero/norm_stats.json` | rejected |
| **HF repo name must end with your hotkey's last 12 SS58 chars** | scan-time rejection (anti-squatting) |
| Burn exactly the published rate (0.1 TAO) | `burn_rejected`, terminal |
| **Burn and commitment within 10 blocks (~2 min)** | `burn_rejected`, fee lost |
| Burn tx signer = submitting hotkey (or owning coldkey) | `burn_rejected` |
| Never reuse a burn tx | anti-replay, strict exact hash match |
| One commitment per hotkey per round | resubmitting overwrites and resets to pipeline start |
| Original weights only | **plagiarism_detected** — terminal, already caught 3× |
| Beat the champion by ≥ 0.01 | otherwise **you do not appear on the board at all** |

Chain commitment payload (≤512 bytes, `Data::BigRaw`):

```json
{ "s": "<hotkey SS58>", "h": "<block hash>", "c": "<HF commit, 40 hex>",
  "r": <round>, "i": "<HF repo id>", "b": "<burn tx hash>", "bb": <burn block> }
```

One payload binds identity, artifact, payment, and round together.

**Notably: no manual review, no discretionary blacklist, no appeal process needed** — every rule is mechanical and every rejection reason is published at `/api/v1/scan-rejections` for miners to look up themselves. That is meaningfully better governance than SN78's permanent no-appeal blacklist.

---

## 8. Device / hardware conditions

| | Miner | Validator |
| --- | --- | --- |
| **GPU** | **1× NVIDIA, 24 GB VRAM min · A100 80GB recommended** | none — pure weight relay |
| RAM | 32 GB min / 64 GB recommended | minimal |
| Disk | 200 GB SSD min / 500 GB NVMe recommended | minimal |
| OS | Ubuntu 22.04 / 24.04 | any Linux |
| Python | 3.11 | 3.11 |
| Docker | required, + NVIDIA Container Toolkit | no |
| **Uptime** | **none** — train, submit, done | polls control.json |

Benchmark workers (GPU machines running the LIBERO suites) are operated by the subnet, not by miners.

> **Note for this operator:** like SN78, this needs **real GPU compute** — 24 GB VRAM minimum, A100 80GB recommended, plus 200–500 GB of disk. The BEAM box at 46.225.140.58 (2 cores, 3.7 GB RAM, 26 GB free, no GPU) cannot participate in any capacity.
>
> The good news is the same as SN78's: there is **nothing to keep online**. You rent GPU hours, train, submit, and shut down. It does not compete with BEAM for machine resources at all — the cost moves entirely to rented compute plus $19 per attempt.

---

## 9. Third-party conditions

| Dependency | Detail | Risk |
| --- | --- | --- |
| **Hugging Face** | **Mandatory.** Checkpoint hosting, pinned by commit hash. Write token required. Repo must stay public and reachable. | Hard dependency |
| **NVIDIA GPU + Docker** | Mandatory for training | rented or owned |
| **drand** | Public randomness beacon for seed derivation | Handled gracefully — unavailability causes retryable `seed_failed`, never rejection |
| **Google Cloud Storage** | `gs://openpi-assets/checkpoints/pi05_base` — the base model | read-only, public |
| **OpenRoboto backend** | Chain scanning, seed derivation, queue, ranking, API | **Closed-source.** Held-out task data, the scoring service, and owner tools are explicitly outside the repo |
| Bittensor | wallet, register, commit | — |

**No API key is required for anything a miner does.** The public API is genuinely public — I queried `/health`, `/rounds/current`, `/leaderboard`, `/queue/status`, `/scan-rejections`, and `/control.json` without credentials. That is the lightest credential burden of the four emission-paying subnets.

The real dependency is **the closed backend and held-out data**. The operator is candid about this: the trust boundary is documented, and the reason held-out data stays private is obvious (it is the evaluation set). Seed derivation is public *because* the block hash and drand value do not exist when you submit — a genuinely clever design.

---

## 10. Risks

1. **90.6% of miner emissions go to UID 0, the owner's own hotkey.** Undocumented in the repo. This is the dominant risk and the first thing to ask about.
2. **3 of 132 submissions earn.** The margin rule gives zero to near-misses rather than a proportional share.
3. **$19 per attempt, non-refundable**, whether you score 0.87 or your upload is malformed. 22 of 100 tracked tasks failed before producing any score.
4. **The 10-block burn window** will silently eat your fee if you script the steps yourself.
5. **Round 1 has run for 240 days.** `auto_advance_round` is true in `control.json`, but no round 2 has landed. A champion `held: true` blocks the top slot indefinitely until someone clears the bar.
6. **Incumbent advantage.** The champion holds until beaten by +0.01; the champion needs to do nothing.
7. **Closed backend.** Scoring service, held-out data, and owner tools are not public. The mechanism is verifiable; the execution is not fully.
8. **Real capital requirement.** A100-class GPU hours to fine-tune a 3B VLA competitively.
9. **Only 12 validator permits and 22 UIDs with stake** on a 240-day-old subnet — thin participation.

---

## 11. Verdict

| | SN66 | SN76 | SN78 | SN79 | **SN80** |
| --- | --- | --- | --- | --- | --- |
| Work | Lean proofs | detector code | fine-tune TTS | trading bot | **fine-tune VLA** |
| Skill | research maths | security eng. | ML / speech | quant trading | **ML / robotics** |
| **Earning UIDs** | 1/bounty | ≤12 | 1 | **216** | **3** |
| Entry cost | $95/attempt | ~$21 | $0.10 | $34.60 | $0.10 + **$19/attempt** |
| Running cost | none | inference | GPU + Chutes | small VPS | **GPU hours only** |
| GPU | no | no | yes | no | **yes** |
| Always-on | no | no | chute hot | **yes** | **no** |
| Top earner | $5,157 once | $224/day | $1,175/day | $343/day | **$545/day** |
| Median earner | $0 | $0 | $0 | **$5.40/day** | **$0** |
| α price | $0.48 | $0.43 | $0.40 | $1.28 | **$2.81** |
| Free practice | local verify | local corpus | no | **testnet + local sim** | **free CPU pre-check** |
| Emission actually in play | 0% | 100% | 100% | 100% | **9.4%** |

**OpenRoboto has the best engineering and among the worst economics of the five.**

The mechanism design is genuinely excellent — dual-beacon seeds, public pre-check tooling, published rejection reasons, live weight fingerprinting, a fully public API, and an anti-gaming table that is honest about what each countermeasure does and does not cover. The swap-suite reasoning in particular shows real adversarial thinking. If you care about a subnet being *honest*, this one is.

But a prospective miner faces: a 0.8666 bar against a held champion, $19 per attempt, A100-class costs, three paying seats out of 132 submissions, and **nine-tenths of the reward pool sitting on the operator's own UID**.

**Recommended path:**

1. **Ask about UID 0 first.** 90.6% of the miner pool is not in the competition. Whether that is a maturity hold-back or permanent changes everything. Do not spend a GPU hour before you have an answer.
2. If the answer is unsatisfactory, **skip this subnet.** The same GPU budget on SN78 buys a shot at $1,175/day against one incumbent, with no per-attempt fee.
3. If you do proceed: **download the champion's checkpoint** (`poppy0619/pi05-RuKL3HneRr8K`, revision pinned in the leaderboard) — it is public, that is the point of the subnet. Evaluate it locally with the open eval toolkit to see exactly what 0.8566 looks like.
4. **Optimize for the swap suites**, not the base four. That is where the remaining headroom is, and it is where memorization provably fails.
5. **Run `check_model.py` before every single submission.** Free, CPU-only, and it prevents the 22% failure rate that has already cost other miners real money.
6. **Always `rt.py submit`** — never the three steps by hand.

**Ranking across all five for this operator:** SN79 remains the best fit (cheap, broad earning curve, free testnet, no GPU, latency skill transfers). SN76 second. SN80 and SN78 are both GPU-gated single-winner races — SN78 pays more and has no per-attempt fee, but SN80 has far better governance and a much higher α price. SN66 still pays miners nothing.

---

*Sources: local checkout of `openroboto-ai/openroboto-subnet` (`README.md`, `docs/SUBNET_OVERVIEW.md`, `docs/MINER_DEPLOY.md`, `docs/SEED_GENERATION.md`, `docs/control_json_example.json`, `validator.py`, `rt.py`, `miner.example.yaml`); live `api.openroboto.ai` (`/health`, `/control.json`, `/api/v1/rounds/current`, `/api/v1/leaderboard`, `/api/v1/queue/status`, `/api/v1/scan-rejections`); live finney chain state for netuid 80 at block 8,879,501 (subnet info, hyperparameters, metagraph incentive/emission/stake/permits, UID 0 hotkey identity).*
