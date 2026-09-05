# Perturb — Subnet 26 (SN26)

**Decentralized adversarial red-teaming of an image classifier.** Repo: `/home/vps-project/Bittensor/Perturb` (`0xsigurd/Perturb`, Python, active development — 46+ merged PRs) · netuid **26** (finney).

> **Archetype: ML competition with a central coordinator API.** Miners don't call each other or the validator peer-to-peer — a hosted API (`api.perturbai.io`) hands out challenge images and collects miner responses; the validator reads from that same API, scores independently, and is the only thing that actually touches the chain (`set_weights`). `perturbnet/protocol.py` defines a `bt.Synapse` (`AttackChallenge`) that looks like classic axon/dendrite Bittensor plumbing, but the shipped `neurons/miner.py` never serves an axon for it — it's pure REST polling (`GET /task`, `POST /submits`). Treat the synapse class as vestigial/unused, not the live path.
>
> ✅ **Accuracy note (unusual for this series): the three public sources mostly agree** — unlike SN121, this whitepaper/README/repo triangulate cleanly on the mechanism. The one place they *don't* agree is two specific numbers (a miner's minimum score-history requirement, and whether the reward tail is capped) — resolved below directly from `perturbnet/constants.py` and `perturbnet/emissions.py`, both freshly touched by commits named exactly for these features (`feat: limit ranked emission tail to 10`, `feat: lower weight eligibility threshold`). The whitepaper describes an earlier version of the incentive design; the shipped code is newer and stricter.

## Goal
Build "the world's first financially incentivized, continuously improving adversarial testing infrastructure": miners are paid to find adversarial examples — inputs imperceptibly modified so a production image classifier misclassifies them — at a rate no manual red-team or static benchmark could match. Commercial output: a growing adversarial-training dataset (subscription product) and on-chain "model robustness certificates" pitched at EU AI Act compliance / enterprise procurement. The verification asymmetry is the whole design rationale (per `README.md`): finding an adversarial example is hard, but *verifying* one — run the model, compare the prediction, measure the perturbation norm — is cheap and objective, which is what makes this scoreable at all.

## What a miner does
`neurons/miner.py` (`PerturbMiner`), confirmed end-to-end:
1. On a fixed cadence (`TASK_CADENCE_SECONDS = 120s` by default), poll the coordinator API for the current task — an ImageNet-100 image + its true label.
2. Run a local **PGD (Projected Gradient Descent)** attack against a locally-loaded copy of the target model (`EfficientNetV2-L`, downloaded via `torchvision`): 10 steps of sign-gradient ascent on cross-entropy loss w.r.t. the model's own predicted label, clipped to an L∞ ball (`epsilon`), until the prediction flips or the step budget runs out. This baseline is intentionally weak — the repo explicitly frames it as a floor, not a target ("competitive miners should optimize attack algorithms"; attack method/parameters are proprietary per-miner).
3. Upload the perturbed image to object storage (Hippius by default, or Cloudflare R2) and submit the URL back to the coordinator API (`POST /submits`) — **the whole round-trip (fetch → attack → upload → submit) is expected to complete within ~20 seconds** (comment in `miner.py::_process_task`).
4. The miner does **not** score its own attempt or talk to the validator directly — validators independently fetch the submitted image URL and do all verification/scoring themselves.

## Scoring / evaluation
Fully deterministic, code-grounded from `perturbnet/constants.py`, `neurons/validator.py`, and `README.md`'s "Scoring and Weighting" section:

**Hard gates (fail any one → score `0.0`):**
- Perturbation norm: `0.003 ≤ L∞ ≤ min(epsilon, 0.03)` (`MIN_LINF_DELTA` / `MAX_LINF_DELTA`) — too small doesn't count as an attack, too large isn't "imperceptible."
- `SSIM(clean, adversarial) ≥ 0.98` and `PSNR ≥ 38 dB` — perceptual-similarity floor, on top of the raw norm bound.
- Predicted class must actually change (comparing resolved ImageNet class indices, not just label strings — the validator normalizes labels and handles comma-separated ImageNet aliases).
- Miner responses are quantized to 8-bit PNG **before** any norm is measured, so every validator computes bit-identical Linf/SSIM/PSNR from the same transport format — no floating-point reproducibility gap between validators.

**Score (if gates pass):**
- `linf_score = (1 − clamp((norm−0.003)/(effective_max−0.003), 0, 1))²`, `rmse_score` computed the same way against RMSE — both quadratic, so scores drop off fast as the perturbation grows toward the ceiling, rewarding genuinely minimal attacks over merely-passing ones.
- `perturbation_score = 0.7 × linf_score + 0.3 × rmse_score` (`PERTURB_LINF_COMPONENT_WEIGHT` / `PERTURB_RMSE_COMPONENT_WEIGHT`).
- `+ 0.03 × margin_score` (rewards a decisive flip: `(best_wrong_logit − true_logit)/10`, clamped) `+ 0.01 × novelty_score` (rewards spatial spread of the changed pixels) — both minor tie-breaker weights on top of the dominant perturbation score.

### Weight-eligibility and reward split — where the public docs disagree with the shipped code
- **Eligibility threshold is 50, not 300.** `MIN_WEIGHT_HISTORY_SIZE = 50` (env: `PERTURB_MIN_WEIGHT_HISTORY_SIZE`) is what actually gates a miner into weight-setting — this is a recent change (`feat: allow early weight setting with effective history window` / `feat: lower weight eligibility threshold`). The whitepaper's "≥300 verified historical scores" conflates this with a *different* constant, `HISTORY_SIZE = 300`, which is just the size of the rolling score buffer kept per miner — not the number of scores you need before earning anything.
- **The reward tail is hard-capped at rank 10, not open-ended.** `perturbnet/emissions.py::ranked_emission_shares`: rank 1 = 70%, rank 2 = 15%, ranks 3–10 split the remaining 15% by descending linear rank-weight, and **anyone ranked 11th or below on positive average score gets zero** — confirmed by the literal commit `feat: limit ranked emission tail to 10` (`MAX_RANKED_MINER = 10`). The whitepaper's "ranks 3–N... distributed via descending linear rank weights" implies no cutoff; the live code disagrees.
- **A live, centrally-controlled burn rate sits on top of all of this — not documented in either public source.** Every weight-setting cycle, the validator fetches `burnRate` from `https://api.perturbai.io/api/v1/burn-rate` (`neurons/validator.py::_fetch_burn_rate`) and routes that fraction of total weight to `BURN_UID` (0) before the 70/15/15 split is applied to what's left: `miner_distribution_share = miner_share × (1 − burn_rate)`. `miner_share` itself is currently hardcoded to `1.0` in `validator.py`, so today the only live lever is `burn_rate` — but it's fetched from an off-chain API the subnet operator controls, not from on-chain governance. If the endpoint is slow/unreachable, it **fails open**: falls back to `DEFAULT_BURN_RATE = 0.0` (no burn), so miners aren't penalized by an outage, but it does mean actual emission share to the top miner can be silently throttled by the operator at any time without a code change on your end. Worth polling `/competition`-equivalent info (or just watching `weights_summary` log lines) rather than assuming a fixed 70%.

## Hardware / device
Consistent across `README.md` and `min_compute.yml`-equivalent docs (this repo states requirements directly in `README.md` rather than a separate YAML):
- **Miner** — minimum: 4 vCPU, 16 GB RAM, 50 GB SSD, 20+ Mbps network. Recommended: 8 vCPU, 32 GB RAM, **NVIDIA GPU with 8+ GB VRAM**, 100+ GB SSD. GPU is not strictly required (PGD on a single image can run on CPU, just slowly) but is recommended — you're racing a 20-second-ish response window and the target model runs locally for every attack step.
- **Validator** — minimum: 8 vCPU, 32 GB RAM, **NVIDIA GPU with 12+ GB VRAM**, 100 GB SSD. Recommended: 16 vCPU, 64 GB RAM, 24+ GB VRAM, 200 GB SSD. The validator also runs the target model locally (to establish ground truth and re-verify every miner's claimed class-flip), so it needs real GPU headroom too, unlike SN121's CPU-only validator.
- First validator/miner start auto-downloads the full ImageNet-100 train split from Hugging Face (~8 GB) — budget for that on first boot (`docs/READINESS_CHECKLIST.md`).
- This is a genuine GPU-required subnet on both sides — closer to Zeus/Affine's archetype than to Tag101/Leadpoet/Sundae Bar's CPU-only ones, though at a much smaller VRAM footprint than fine-tuning a 32B LLM.

## Third-party / dependencies
- **Hugging Face** — `clane9/imagenet-100` dataset (the fixed challenge source, ~126k images, train split).
- **torchvision** — `EfficientNetV2-L_Weights.IMAGENET1K_V1`, the fixed target classifier both sides run locally.
- **sundae_bar-style coordinator API** (`api.perturbai.io`) — task assignment, miner response submission, leaderboard reporting, and the burn-rate policy endpoint. Closed-source, operator-run.
- **Object storage** — Hippius (default) or Cloudflare R2, for miner response images and validator dataset export.
- **PM2** (Node.js process manager) — used to run/restart both miner and validator processes; Node.js 18+ is a setup prerequisite purely for this, not for any subnet logic.
- **Bittensor / Subtensor** — standard Python `bittensor` SDK (unlike SN121's Node/Polkadot-API validator), used only for wallet/metagraph/`set_weights` — not for miner↔validator messaging, which goes through the coordinator API instead.

## How to win
1. **Beat the baseline PGD attack — that's the whole game.** The shipped miner is explicitly a weak floor (10-step single-model PGD, untargeted, no ensembling). Stronger, still-imperceptible attacks (better step-size schedules, momentum/Adam-based PGD, ensemble/transfer attacks, structured perturbations that minimize SSIM/PSNR cost more efficiently) directly raise your `perturbation_score`.
2. **Optimize against the quadratic scoring curve, not just "does it pass."** Since `linf_score`/`rmse_score` are squared, the gap between a perturbation just barely under the ceiling and one close to the 0.003 floor is large — a genuinely minimal attack scores far better than a merely-valid one.
3. **Respect the perceptual gates as hard constraints, not soft targets** — SSIM ≥ 0.98 and PSNR ≥ 38 dB will zero out an otherwise well-scored attack; tune against these directly, not just the L∞ budget.
4. **Reliability matters as much as attack quality**: you need `MIN_WEIGHT_HISTORY_SIZE = 50` valid scored responses before you earn anything at all, and the cadence is a new task every 2 minutes with a ~20-second response budget — a miner that's slow or crashes loses eligibility progress, not just one round.
5. **Rank matters non-linearly and has a hard floor** — only the top 10 miners by positive average score earn anything (rank 1 gets 70%, rank 2 gets 15%, 3–10 split the last 15%); sitting at rank 11 is functionally the same as not mining. Aim decisively for top-10, not "positive score."
6. **Don't assume 100% of nominal weight reaches miners** — the live-fetched `burn_rate` can silently reduce everyone's share at the operator's discretion; watch the validator's `weights_summary` logs (`burn=`, `top=`) rather than assuming the documented 70/15/15 split is the full picture.

## Key files
- `README.md` — the most accurate single document (whitepaper is one revision behind on incentive-mechanism specifics).
- `perturbnet/constants.py` — every tunable threshold (`MIN_LINF_DELTA`, `MAX_LINF_DELTA`, `MIN_SSIM`, `MIN_PSNR_DB`, `HISTORY_SIZE`, `MIN_WEIGHT_HISTORY_SIZE`, `K_MINERS`, `TASK_CADENCE_SECONDS`, burn-rate config) — read this before tuning anything.
- `perturbnet/emissions.py` — the exact 70/15/15-with-rank-10-cutoff formula (`ranked_emission_shares`).
- `neurons/validator.py::_set_weights` / `_fetch_burn_rate` — full weight-setting + burn logic, including the eligibility/history-window and burn-rate fail-open behavior.
- `neurons/miner.py::_attack_image` — the baseline PGD implementation to beat.
- `perturbnet/protocol.py` — the (currently unused in the live flow) `AttackChallenge` synapse schema.
- `docs/READINESS_CHECKLIST.md` — pre-mainnet operational checklist (dataset download, GPU/CUDA match, smoke test).

## Run / submit commands
```bash
git clone https://github.com/0xsigurd/Perturb && cd Perturb

# one-time setup (installs PM2 + Python/Bittensor deps; validator setup also
# pre-downloads the ~8GB ImageNet-100 split)
bash ./scripts/setup_common.sh miner        # or: validator

# miner
cp scripts/miner.env.example scripts/miner.env
# edit: WALLET_NAME, WALLET_HOTKEY, NETUID=26, NETWORK=finney
bash ./scripts/run_miner.sh

# validator
cp scripts/validator.env.example scripts/validator.env
# edit: WALLET_NAME, WALLET_HOTKEY, PERTURB_API_KEY
bash ./scripts/run_validator.sh

# sanity check before trusting a long run
python scripts/integration_smoke_test.py
```
Both roles require a wallet hotkey already registered on netuid 26 (`btcli subnet register --netuid 26`) before starting.

## Verdict
**One of the more honestly-engineered subnets in this series** — the verification-asymmetry design (cheap to check, hard to produce) genuinely fits Bittensor's incentive model well, scoring is deterministic and bit-reproducible by construction (uint8 quantization before every norm measurement), and the repo is active and well-tested (unit-testable emission formula, a real smoke test, a readiness checklist). The catch is entirely economic, not technical: a hard-10 reward cliff means most participants earn nothing regardless of score, and an operator-controlled, off-chain-fetched burn rate means even a secure #1 position isn't a fixed, auditable-on-chain percentage — read the live logs, not the whitepaper's numbers, before sizing expected returns. GPU required on both sides (unlike SN121/SN101/SN71), but at a modest 8–12+ GB VRAM tier, not the 32B-model-training tier of Affine/Zeus.
