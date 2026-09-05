# ChronoLLM — Subnet 38 (SN38)

**Competitive training of chronologically-consistent LLMs — one model per year, no knowledge of the future.** Repo: `/home/vps-project/Bittensor/sn38` (`chronollm/sn38`, Python, `uv`-managed) · netuid **38** mainnet (474 testnet).

> ⚠️ **`subnetalpha.ai`'s page for this subnet is simply wrong — not a rebrand, a data error.** Its `/subnet/chronollm/` URL describes a completely unrelated on-chain betting/gambling platform ("Red vs Blue" Rock-Paper-Scissors, staking TAO against other players), citing GitHub org `TAO-Colosseum/tao-colosseum-subnet` — a different project entirely, with no connection to ChronoLLM's actual repo, team, or mechanism. `chronollm.com` and the `chronollm/sn38` GitHub repo agree with each other completely and match the code below; treat those as authoritative and disregard subnetalpha's listing for this netuid.
>
> ⚠️ **The README's "winner takes all" framing is also stale relative to the shipped code** — confirmed directly against the live metagraph screenshot you shared. The actual reward is an **exponential decay across up to the top 10 qualifying miners**, not a single winner. This is the most important correction in this whole write-up — see Scoring below.

## Goal
Solve **lookahead bias** in LLM-based financial/historical research: a standard LLM trained on data from all time periods "knows" the future relative to whatever historical moment you're asking it to reason about — a model asked to predict 2015 market trends has already seen the 2020 crash and every year since. ChronoLLM produces a family of models, one pinned to each year's actual knowledge cutoff, so backtesting and historical analysis can query a model that genuinely doesn't know what happened after that date. Built by Crunch/CrunchDAO (a crowdsourced ML research platform), grounded in the published ChronoGPT paper (arXiv:2510.11677).

## What a miner does
1. **Train one model per year, 2013–2024 inclusive** (`ALL_YEARS = range(2013, 2025)` in `constants.py` — the README's "2013-2025" is off by one year relative to what's actually required; trust the code). Each year's model must be trained **only** on data available up to that cutoff — a 2018 model must contain zero knowledge of 2019 or later.
2. **Architecture**: the README says "must use the ChronoGPT architecture," but this is stale — the shipped code (commit `63de910`, "Open evaluation to any AutoModelForCausalLM architecture") accepts **any HuggingFace `AutoModelForCausalLM`-compatible architecture** (Llama, Qwen, Gemma, Mistral, etc.) in addition to native ChronoGPT, and there's even a registry process for adding custom architectures not built into `transformers` (open a PR adding `configuration_<name>.py`/`modeling_<name>.py` under `sn38/architectures/`). **Hard cap: 2 billion parameters** — deliberately small, to keep the "leak" surface minimal and the subnet approachable without frontier-scale compute.
3. **Upload each yearly model to HuggingFace**, safetensors only (no pickle), pinned to an exact **commit SHA** (not a branch — immutable once submitted). Model repos can stay **private** during the submission window to prevent copying, but must switch to public within 1 hour after submissions close.
4. **Build `models.json`** mapping each year to `owner/repo@<40-char-sha>`, upload it as a public HuggingFace **dataset** repo (this one must always stay public — the backend polls it), and commit the reference on-chain (`python -m sn38.neurons.miner --models models.json --hf-token ...`).
5. **Self-test before submitting** (optional but recommended): `phala deploy` a self-test container that runs the exact same leak-detection code as the validator, against a held-out (non-production) dataset, inside a TEE — CPU-only, no GPU needed, rate-limited to 12 calls/day. Returns PASS/FAIL only.

## Scoring / evaluation
Fully code-grounded from `sn38/neurons/validator.py` and `README.md`/`docs/miner.md`, on a **weekly round** (Monday 12:00 UTC), with a deliberate overlap: miners prepare round N while validators simultaneously evaluate round N-1's already-frozen submissions, so there's no dead evaluation window.

**Stage 1 — consistency ("leak") check, all miners:**
- Each yearly model is tested against a **private evaluation dataset** the model must not be able to answer from future knowledge. Validators run this entirely inside a **Trusted Execution Environment** (Phala Cloud, Intel TDX) — the evaluation questions are only accessible inside the enclave, invisible to both the validator operator and every miner, and the validator's own code is auditable via remote attestation. This exists specifically to prevent miners from overfitting to a known test set.
- Missing years, oversized (>2B param) models, or errors receive the worst possible score.
- **Anti-copy**: the validator hashes submitted model weights and checks for exact duplicates across miners (first submitter wins ties); an SVD-spectral-distance check (`svd_gate.py`, replacing an earlier cosine-similarity check per commit `aee3d8c`) provides a more sophisticated near-duplicate detector beyond exact-hash matching.
- **Only the top 10 miners by leak score qualify for Stage 2.**

**Stage 2 — quality evaluation, top 10 only:**
- Qualified models answer open-ended questions in a round-robin tournament; an **LLM judge** scores every pairwise duel. Win rate becomes the quality score.

**Final score**: `0.7 × normalized_leak_score + 0.3 × quality_win_rate` — consistency dominates, but quality is a real, non-trivial third of the score.

**Weight distribution — the part the docs get wrong.** `run_stage2_and_score()` in `validator.py`:
```python
rewards = np.exp(-0.8 * (np.arange(n) ** 0.9))
rewards /= rewards.sum()
rewards *= emission_pct
```
This is an **exponential decay across ranks**, not a single winner. I verified this formula's *exact* ratio predictions against the live metagraph screenshot you shared: rank-1→rank-2 ratio ≈2.226, rank-2→rank-3 ≈2.0, rank-3→rank-4 ≈1.93, rank-4→rank-5 ≈1.89 — every one of those matched your real on-chain incentive figures (0.520/0.234/0.117/0.061/0.032) to three decimal places. **This is confirmed live production behavior, not a guess.** Concretely: rank 1 gets roughly half the qualifying pool's total weight, but ranks 2 through 10 all earn real, meaningfully-declining shares — reaching rank 5 of 10 still earned about 3.2% of the pool in the round your screenshot captured. Qualifying and posting a competitive (not necessarily best) score is enough to earn something; you do not need to be #1.
- If **only one** miner qualifies Stage 1, that miner gets the entire weight (skips Stage 2 entirely — no duels needed against nobody).
- If **no** miner qualifies, the validator **keeps the previous round's on-chain weights** rather than zeroing everyone out or burning — a softer fallback than most subnets in this series.
- Config values above (`min_eval_score=-3.0`, `leak_epsilon=-6.0`, `top_n_for_quality=10`, the `0.7`/`0.3` split, `emission_pct`) are read from a backend-served config with these as code-level fallback defaults — the live values could differ without a code change; `api.chronollm.com/docs` is where the current authoritative numbers live.

## Hardware / device
- **Miner**: a GPU for training — the 2B-parameter cap keeps this in reach of a single modern high-end consumer/prosumer GPU for most training approaches, though the exact minimum isn't specified in the repo (scales with your training method and per-year dataset size, and you're training ~12 separate models, not one).
- **Miner self-test**: explicitly CPU-only, no GPU — runs on a rented Phala Cloud CPU instance (`tdx.xlarge`, 8 vCPU/16GB recommended minimum).
- **Validator**: runs inside Phala Cloud (Intel TDX) — a TEE requirement for validators specifically, to keep the private eval dataset secret from everyone including the validator operator. No explicit min_compute.yml was found in this repo; budget for TEE-compatible hosting plus GPU access to actually run inference on submitted models during evaluation.

## Third-party / dependencies
- **HuggingFace** — model + dataset hosting; required for every miner (write token needed).
- **Phala Cloud** (Intel TDX TEE) — both the validator's evaluation environment and the optional miner self-test environment; a real, non-optional infrastructure dependency for validators, optional-but-recommended for miners.
- **`api.chronollm.com`** — the backend that serves round/config state, quality-duel questions, and receives submitted eval results; a centralized service the validator trusts as ground truth for config values and coordinates rounds through.
- **An LLM judge** (unspecified which model/provider in what I read) — used for Stage 2 pairwise quality duels.
- **Bittensor / Subtensor** — standard registration, on-chain submission commitment, `set_weights`.

## How to win
1. **Nail Stage 1 first — it's 70% of your score and the hard gate to even compete for Stage 2.** A model that leaks future knowledge scores at the worst possible level regardless of how good its answers are; get this right before optimizing quality at all.
2. **Submit all 12 years.** Missing years score at the worst possible level — a partial submission caps your leak score badly even if your submitted years are excellent.
3. **You don't need to be #1 — top 10 with a competitive score pays real money.** Given the confirmed exponential-decay formula, the realistic target for a new miner is "qualify into the top 10 and post a decent final score," not "beat everyone." This is meaningfully more achievable than the README's "winner takes all" language suggests.
4. **Self-test before every submission** — it's free (CPU-only, rate-limited but generous at 12/day) and runs the *exact* validator leak-detection code against a held-out dataset, so a pass there is a strong signal you'll pass in production; an overfit model will specifically fail because the self-test dataset differs from the production one.
5. **Respect the 2B parameter cap and the immutable-commit-SHA submission format precisely** — an oversized model or a branch reference instead of a pinned SHA both score at the worst level, independent of actual model quality.
6. **Consider the broader architecture allowance** — since any `AutoModelForCausalLM`-compatible architecture is accepted (not just ChronoGPT, despite what the README implies), you can bring existing Llama/Qwen/Gemma/Mistral fine-tuning expertise rather than learning a bespoke architecture from scratch.

## Key files
- `README.md` — accurate on the mechanism's shape, stale on two specifics (year range, architecture requirement, and the winner-take-all framing) — cross-check against the code.
- `docs/miner.md` — more accurate and more detailed than the README on architecture flexibility and submission mechanics.
- `sn38/neurons/validator.py::run_stage2_and_score` — the actual, confirmed-live exponential reward formula.
- `sn38/template/constants.py` — `ALL_YEARS` (the real 2013–2024 range) and network/owner-UID config.
- `sn38/template/leak.py` — the chronological-consistency scoring implementation.
- `sn38/template/svd_gate.py` — the near-duplicate/anti-copy spectral-distance check.
- `sn38/template/quality.py` / `quality_prompts.py` — Stage 2 LLM-judge duel implementation.
- `debug/test_automodel.py` — run this locally before submitting; it's the same code path the validator uses.

## Run / submit commands
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone git@github.com:chronollm/sn38.git && cd sn38 && uv sync

btcli subnet register --netuid 38 --wallet.name miner --wallet.hotkey default

# after training all 12 yearly models and building models.json:
python -m sn38.neurons.miner \
  --wallet.name miner --wallet.hotkey default \
  --models models.json --hf-token hf_xxx

# verify pickup
curl https://api.chronollm.com/rounds/current
curl https://api.chronollm.com/submissions/{round}/{uid}

# optional free self-test (CPU-only, via Phala Cloud)
npm install -g phala && phala login
phala deploy -c docker-compose.self-test.yml --pre-launch-script scripts/prelaunch.sh \
  -e HOTKEY_FILE_CONTENT="$(cat ~/.bittensor/wallets/miner/hotkeys/default)" \
  -e HF_TOKEN=hf_xxx -e HF_REPO=your-username/your-model@commit-sha \
  --instance-type tdx.xlarge --no-dev-os
```

## Verdict
**A genuinely well-designed, currently-live subnet with a real research grounding (a published paper backing the core idea) and a reward mechanism friendlier to new entrants than its own docs claim.** The TEE-protected private eval dataset is a sound anti-overfitting design, the free CPU-only self-test is a rare and genuinely useful courtesy to miners, and the 2B parameter cap keeps this achievable without frontier-scale compute — training twelve small yearly models is real work but not a moonshot. The main things to get right before investing training time: verify the *current* live config values at `api.chronollm.com/docs` rather than trusting this doc's cited defaults, and don't be discouraged by the README's "winner takes all" language — the confirmed exponential-decay formula means a solid (not necessarily best) top-10 submission earns real, meaningful emissions.
