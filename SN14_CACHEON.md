# Cacheon — Subnet 14 (SN14)

**Inference-server speed competition. Fastest correct server wins.** Repo: `/home/vps-project/Bittensor/hotfloat` (upstream `github.com/latent-to/cacheon`; this local clone lives under the `coldint` org as `hotfloat`, apparently a working/codename repo for the same project) · netuid **14** mainnet (470 testnet).

> **Not the subnet the user originally asked about.** This repo was pointed to as if it were subnet 29 ("coldint") material — its own README says plainly **"Cacheon (SN14)"**, a different netuid, different website (`cacheon.ai`, not `coldint.io`), different upstream org (`latent-to`, not `coldint`). See [`SN29_COLDINT.md`](SN29_COLDINT.md) for what SN29 actually is (short version: currently dormant, 100% burn). Cacheon appears to be built by the same or an affiliated team — very active development (100+ merged PRs, commits through mid-2026, sophisticated Postgres-backed validator state) — and is presumably what you actually want if you're looking at live code in this directory.

## Goal
Run an open competition for **production-grade LLM inference serving optimization**: given a fixed model and fixed hardware, whoever serves it fastest — while staying correct — wins. This is a genuinely different archetype from every other subnet analyzed in this series: not "train a better model," not "find an adversarial example," not "resell API access" — it's **systems/inference-engineering optimization** (batching, kernel choice, KV-cache management, scheduling, speculative decoding, etc., all fair game as long as output correctness holds).

## What a miner does
1. Build a Docker container that serves the pinned target model — **V1 arena is `Qwen2.5-72B-Instruct`** — via an OpenAI-compatible `/v1/chat/completions` endpoint with streaming and logprobs support. Model weights are **mounted at runtime** (`/models`), not baked into the image, and the image itself is capped at **20GB**.
2. Push the image to a public container registry.
3. Pay a submission fee and commit the image reference + digest on-chain in one step (`miner/commit.py`) — the fee amount is configurable (`CACHEON_SUBMISSION_FEE_RAO`, default `0`/disabled in this snapshot, so check the live value before assuming it's free).
4. The validator picks up new commitments within ~6 minutes, pulls the image, and evaluates it against a pinned vLLM baseline on identical hardware.
5. GPU hardware is **only needed for local testing** before submission — miners don't need to run inference themselves in production; the validator provisions and pays for the GPU pod that actually times your server.

Techniques are wide open: the whole premise is that a smarter inference stack (better batching, custom kernels, speculative decoding, alternate serving frameworks like SGLang) can beat stock vLLM on the same hardware, and the subnet pays for finding those gains.

## Scoring / evaluation
Fully code-grounded from `validator/scoring.py`, `validator/challengers.py`, and `validator/config.py`:

**Two-pass correctness gate — fail either, score is zero:**
- **Pass 1 (text-similarity DQ)**: the miner's decoded output text is compared character-by-character (via `difflib.SequenceMatcher`, tokenizer-agnostic on purpose — a correct output from vLLM and from SGLang should read near-identically as text even if their tokenizations differ) against the baseline's output. Must clear `PASS1_TEXT_SIM_DQ_THRESHOLD` — a value that was recently *lowered* from 0.90 to 0.40 (commit `456002a`), i.e. the correctness bar for this pass was loosened, likely to tolerate legitimate cross-framework decoding variance rather than punish it as cheating.
- **Pass 2 (teacher-forcing logprob gate)**: the baseline model independently scores the miner's actual output tokens in a single forward pass. A genuine same-model server produces tokens the baseline assigns high probability to (typically −0.5 to −2.0 mean logprob per the code comments); a server dumping garbage or a different model entirely scores far lower (−15 to −30). Must clear both a mean-logprob threshold (default −4.0) and a min-logprob threshold (default −12.0, catching isolated garbage tokens in an otherwise-plausible output) — this is a materially harder anti-cheat gate than a plain text-diff, since it can't be gamed by just copying the baseline's text without actually running comparable inference.

**Speed score (only computed if correctness passes):**
- `speed_improvement = median(max(0, (baseline_e2e − miner_e2e) / baseline_e2e))` across prompts — end-to-end wall time from request start to an *aligned* token position (both baseline and miner must emit at least `ceil(0.9 × baseline_token_count)` tokens — `SPEED_TOLERANCE_RATIO = 0.9` — before speed credit applies, preventing a server from gaming the metric by truncating output early).
- Score is the **median** improvement across the prompt set, not mean — resistant to being pulled up by a few lucky-fast prompts or down by one slow outlier.

**Weight distribution — winner-take-most, not winner-take-all:**
- **Winner: 80%** of the competition pool (`CACHEON_WINNER_WEIGHT_SHARE`), **runner-up: 20%** (`CACHEON_RUNNER_UP_WEIGHT_SHARE`) — everyone else gets nothing. This is a real, code-confirmed 80/20 split, distinct from Affine's pure 100/0 or Perturb's 70/15/15-to-rank-10.
- **Dethrone margin**: a challenger must beat the current winner's *fresh* re-measured score by a fixed **1% margin** (`CACHEON_WINNER_EPSILON_INITIAL = 0.01`) to take the top spot — a small but real anti-noise-churn buffer, similar in spirit to Affine's dominance margin.
- **Duplicate-submission defense** (`challengers.py`): commitments are grouped by base image name (ignoring tag); if you resubmit trivial version bumps of the same image, only the highest-tagged version is evaluated and the rest are auto-rejected as superseded — you can't flood the challenger queue with near-identical resubmissions to burn validator GPU time.

## Hardware / device
This is a genuinely GPU-heavy subnet, but asymmetrically — validators bear almost all of the hardware burden, not miners:
- **Miner**: no GPU required to *mine* — only for local testing before submission. The real requirements are a public container registry account and enough TAO for the submission fee (when non-zero).
- **Validator**: split into two components. An **always-on CPU host** (chain scanning, weight setting — cheap, no GPU) plus an **ephemeral GPU pod rented on-demand** only when challengers are actually queued (not running 24/7, which materially reduces validator cost versus a subnet needing constant GPU uptime). That GPU pod needs a serious **8-GPU NVLink/SXM pod** — 8× H200, 8× B200, or 8× B300 rated "Tier A," with 8× H100 as a "Tier B fallback" — plus 400GB storage for the 72B-parameter model weights. This tier of hardware is typically only accessible via specialized GPU rental providers, not a home rig; the repo's own `providers/` directory (Lium, Targon, Shadeform) confirms the validator is built to rent these pods on-demand from commercial GPU clouds rather than assume dedicated ownership.

## Third-party / dependencies
- **GPU rental providers** — Lium, Targon, and Shadeform are all wired in (`validator/providers/`) as interchangeable backends for renting the ephemeral 8-GPU eval pod; this is validator-side infrastructure, not something miners need directly.
- **Public container registry** (Docker Hub or similar) — miners push their image here; the validator pulls from it.
- **Postgres** (`cacheon_db`) — the validator's state store (evaluation progress, per-round incumbent re-evaluations, eval history) migrated fairly recently from a mix of S3 + local state to a shared Postgres backend (per the commit log: "drop S3 from eval progress path," "make structured validator state Postgres-only").
- **vLLM** — the pinned baseline serving framework (`vllm/vllm-openai:v0.22.0` in this snapshot) every miner is scored against; miners are free to use vLLM, SGLang, or a custom stack as long as they beat this baseline.
- **Bittensor / Subtensor** — standard on-chain commitment (image ref + digest + payment proof) and `set_weights`.

## How to win
1. **Correctness is a hard gate, not a tiebreaker** — the teacher-forcing logprob check specifically defends against "just serve garbage fast," so optimization work has to preserve genuine model-equivalent output, not just superficially similar text.
2. **Optimize end-to-end latency to the aligned token, not raw throughput** — the scoring window is time-to-Nth-token with a 90%-of-baseline-length floor, so techniques that trade a slower start for higher steady-state throughput (or vice versa) need to be evaluated against *this specific* metric, not a generic tokens/sec benchmark.
3. **Beat the incumbent by more than 1%, decisively** — a marginal improvement inside the epsilon won't dethrone the current winner even if it's technically faster; aim for a clear, reproducible win.
4. **Runner-up is real money, not consolation** — with an 80/20 split (vs. Affine's 100/0), being the clear #2 is still worth pursuing even against a strong incumbent, unlike subnets where anything short of #1 earns nothing.
5. **Don't try to game the queue with resubmission spam** — the base-image dedup means only your best-tagged version per image name gets evaluated; focus effort on one strong submission rather than many minor variants.
6. **This is a systems-engineering competition, not an ML-training one** — the leverage is in serving-stack engineering (custom CUDA kernels, smarter batching/scheduling, speculative decoding, quantization that preserves the correctness gate) rather than anything resembling model fine-tuning.

## Key files
- `README.md` — the single clearest document of any subnet in this series; read it directly, it's already excellent.
- `validator/scoring.py` — both correctness passes and the speed-improvement formula, in full.
- `validator/challengers.py` — challenger selection, precheck, and duplicate-image dedup logic.
- `validator/config.py` — every tunable constant (`CACHEON_WINNER_WEIGHT_SHARE`, `CACHEON_WINNER_EPSILON_INITIAL`, `CACHEON_SUBMISSION_FEE_RAO`, baseline image pin) — check current live values here before assuming any number in this doc is still current.
- `validator/gpu_orchestrator.py`, `validator/providers/*` — how the ephemeral GPU eval pod gets rented and torn down.
- `miner/commit.py` — the on-chain commit flow (fee payment + image reference).
- `example-miner/` — a minimal stock-vLLM submission that scores zero by design; exists purely to verify the submission contract works end-to-end before you invest in actual optimization.

## Run / submit commands
```bash
# Miner
docker tag my-server:latest docker.io/myuser/cacheon-miner:v1
docker push docker.io/myuser/cacheon-miner:v1
python miner/commit.py \
  --wallet-name <wallet> --wallet-hotkey <hotkey> \
  --image "docker.io/myuser/cacheon-miner:v1" --digest "sha256:..." \
  --fee 0.1 --network finney --netuid 14

# Validator — CPU host (always-on)
git clone https://github.com/latent-to/cacheon && cd cacheon
cp .env.example .env   # wallet + S3/Postgres config
docker compose up --build

# Validator — GPU pod (on-demand, only when challengers are queued)
bash scripts/gpu_setup/setup.sh
docker compose -f validator/gpu-compose.yml up --build -d
```
Full docs at `cacheon.ai/docs` — linked extensively from the README for every step (API contract, scoring detail, GPU pod setup).

## Verdict
**A well-engineered, actively-maintained subnet with a genuinely distinct value proposition** — most Bittensor ML-competition subnets ask "train a better model," this one asks "serve an existing model faster without breaking it," which is a real, commercially relevant problem (inference cost dominates production LLM spend) that rewards systems/performance-engineering skill rather than ML-research skill. The two-pass correctness gate (text-similarity + teacher-forcing logprobs) is a notably more rigorous anti-cheat design than a naive output-diff. Barrier to entry is real but different from a training subnet: you need serious inference-engineering chops and access to 8-GPU-class hardware for *local testing* (production evaluation cost is borne by the validator, not you), plus a working submission fee/gate to check current live values for before committing.
