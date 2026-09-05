# MIID (Yanez) — Subnet 54 (SN54)

**Synthetic identity-preserving face image variations for KYC/deepfake stress-testing.** Repo: `/home/vps-project/Bittensor/MIID-subnet` (`yanez-compliance/MIID-subnet`, Python) · netuid **54** mainnet (322 testnet).

> ⚠️ **Both public sources describe an earlier phase as if it were current — it isn't.** `subnetalpha.ai` frames this as a name/text-variation subnet ("Phase 1: Name-based threat scenarios" as the active description). The repo is unambiguous that this is stale: **"Image generation is the only scored task. There is no separate reward path for name, DOB, or address variations."** The subnet is currently in **Phase 4 ("Deepfake / Face-Based Adversarial Testing for KYC")**, and has been since Q1 2026 per the roadmap — an entirely different, GPU-heavy, face-image-diffusion task. If you came here expecting text/LLM-based name-variation work (which is what Phase 1-3 was), that path pays nothing today.
>
> ⚠️ **The repo contradicts itself on hardware, and the README is the one to trust.** `min_compute.yml` states `gpu: required: False` with LLM-sized VRAM specs ("Increased from 8GB to 16GB for **better LLM inference**") — clearly written for the earlier text-generation phase and never updated. The README and `docs/miner.md`, by contrast, are unambiguous and repeated multiple times: **"GPU with at least 8GB VRAM... required for production mining"** and **"without image generation enabled you will not earn rewards."** Do not plan hardware around `min_compute.yml` for this subnet.
>
> ⚠️ **The documented cycle window has already passed as of this analysis.** `docs/miner.md` states "Phase 4 Cycle 2 Execution (current stage)" running **Mar 16 – Apr 20, 2026** — that window is behind us now. A newer cycle is almost certainly live; check the [Yanez Dashboard](https://tao-ui-dashboard.yanez.ai/) for the actual current cycle dates and status before planning around anything dated in this document.

## Goal
Stress-test KYC, biometric verification, and fraud-detection systems by generating **identity-preserving adversarial face image variations** — the same underlying person, transformed in ways real fraudsters use to evade detection (pose changes, lighting manipulation, expression changes, background swaps, and simulated screen-replay/photo-of-a-photo attacks). Yanez Compliance sells the resulting dataset and testing capability commercially to financial institutions; the subnet is the decentralized generation engine behind that product. Backed by Yuma accelerator and reportedly has "multi-billion dollar institutions" as early clients, per subnetalpha.

## What a miner does
1. Receive a **base face image** (from the validator) plus a variation request specifying a **type** and **intensity** (Light/Medium/Far).
2. **Five variation types** (Cycle 2): `pose_edit` (±15° to >±45° head rotation), `expression_edit` (subtle to dramatic expression change), `lighting_edit` (subtle to dramatic lighting/shadow change), `background_edit` (color/environment change, sometimes with requested accessories like head coverings), and `screen_replay` (simulate the face as photographed off a screen — must show at least 2 of: moiré/pixel grid, screen glare hotspots, keystone distortion, capture-typical gamma shift, or bezel/edge cues).
3. Generate the variation using one of **three shipped diffusion models** — `flux_klein` (FLUX.2-klein-4B, ~8GB VRAM, the stable default), `pulid` (identity-focused, tries Nunchaku PuLID then falls back to FLUX.1-Kontext, ~12GB+), `pulid_flux2` (FLUX.2-klein backbone, ~8GB) — randomly selected per query by default, or pinned via `MIID_MODEL`. Two more (`flux_kontext`, `qwen`) are wired in and enablable manually for miners wanting an edge.
4. **Self-validate identity preservation locally** using **AdaFace** (a face-recognition similarity model) before submitting — the miner-side recommended threshold (≥0.7) is deliberately stricter than the validator's actual pass bar (≥0.6), giving you margin.
5. **Encrypt the result with drand timelock encryption** (a distributed randomness beacon service) and upload to S3; return a signed reference, not the raw image, to the validator.

## Scoring / evaluation
Fully code-grounded from `MIID/validator/reward.py` and `docs/miner.md`'s "Reward System" section — a genuinely multi-stage pipeline:

1. **Automated pre-checks**: corrupt images, exact duplicates of the seed image, or duplicates of another miner's submission are filtered immediately (score 0 or -1 for duplicates).
2. **Identity preservation gate**: AdaFace similarity must clear **≥0.6** — below 0.4 is explicitly flagged as "identity not preserved... looks like a different person."
3. **Automated variation-type detection**: systems check what transformation was actually produced against what was requested.
4. **Manual human review**: reviewers confirm the miner followed the query, preserved identity, and produced *exactly* the requested transformation — no more, no less. Extra unintended changes (e.g. expression drifting during a pose edit) draw a **partial-match penalty**.

**Discrete score scale** (unusual — skips 1 and 4): `0` = failed pre-checks, `-1` = duplicate, `2` = partial match (multiple variations detected, or intensity mismatch), `3` = acceptable, `5` = exact transformation match with identity preserved.

**Ranking and reward** (`get_image_variation_rewards` in `reward.py`):
- Composite per-miner score = average validation score (primary) + a tiny identity-preservation-weighted tiebreak.
- Miners are ranked by this composite, then filtered: only miners **within a top-N rank cap** *and* clearing the **≥0.6 average identity-preservation threshold** are reward-eligible ("blended rank cap with quality threshold").
- **If no miner clears both filters in a round, it's a declared "BURN EVENT"** — the log even names it that explicitly — deferring to a reputation-weighted fallback stage rather than necessarily zeroing everyone immediately.
- **Fixed burn UID is 59** (not the more common UID 0 seen elsewhere in this series) — worth knowing if you're checking the metagraph and see a concentration there.
- **Reputation-based, not purely per-round**: your face-variation scores feed into an ongoing **reputation** score with **tier multipliers**, which is what actually determines your share of the reward pool — consistent performance over time compounds, a single good or bad round doesn't fully determine your payout.
- Leftover code paths (`kav_weight`/`uav_weight`, 10%/90%) reference the older Known/Unknown Attack Vector text-variation scoring from Phases 1-3 — per the README's explicit statement that image generation is now the *only* scored task, treat this as likely-vestigial code from the earlier phase rather than a currently-active reward split, though I could not fully verify it's dead code versus still blended in some way.

## Hardware / device
Trust the README/`docs/miner.md` over `min_compute.yml` (see warning above):
- **Miner**: GPU with **≥8GB VRAM** (NVIDIA CUDA or Apple Silicon MPS) is a hard requirement for earning anything — CPU-only generation is explicitly called "too slow for production, you will not keep up with validator requests." Recommended: 8+ CPU cores (12+ for continuous throughput), 16GB+ RAM (32GB+ better), **80GB+ free disk minimum** (150GB+ recommended) for model weights/cache/outputs, open port 8091.
- **Validator**: does not need the miner's image-generation stack (`requirements-miner.txt` is miner-only), but does need to run identity-preservation checks and coordinate the manual-review pipeline.

## Third-party / dependencies
- **Hugging Face** — required account + API token; you must accept gated-model licenses for FLUX.2-klein-4B and FLUX.1-Kontext-dev before the miner can download weights.
- **AdaFace** (`mk-minchul/AdaFace`, a separate GitHub repo + checkpoint download) — the face-identity-similarity model both miners (self-check) and validators (actual gate) use; a real, non-optional setup step (clone + download a checkpoint from Google Drive via `gdown`).
- **drand** — a distributed randomness/timelock encryption beacon, used to encrypt submissions before upload (an `timelock` Python package is optional; falls back to a raw-bytes sandbox mode without it).
- **S3-compatible object storage** — where encrypted image submissions actually get uploaded; miners return signed references, not raw images, to the validator directly.
- **Weights & Biases** — testnet result visualization (`wandb.ai/MIID-dev-test/subnet322-test`).
- **Yanez's own dashboard** (`tao-ui-dashboard.yanez.ai`) — the authoritative live source for current cycle status, scores, and leaderboard; check this before trusting any dated info in the repo's docs.

## How to win
1. **Get the GPU/model stack actually running first** — the miner logs must show `Phase 4 image generation: ENABLED`; if it shows `DISABLED (missing packages)`, you earn literally nothing regardless of anything else. This is a hard, binary gate before any scoring nuance matters.
2. **Precision over creativity** — the scoring explicitly punishes producing *more* than what was asked (an unintended expression change during a pose edit is a partial-match penalty, not a bonus for "extra realism"). Match the requested type and intensity exactly.
3. **Guard identity preservation above the validator's own bar** — the miner-side recommended AdaFace threshold (≥0.7) is intentionally stricter than the validator's pass bar (≥0.6), giving you a safety margin against model variance between your local check and the validator's actual scoring run.
4. **Background edits must be genuine transformations, not composites** — copy-pasting a face onto a new background is explicitly called out as scoring negatively; the diffusion model needs to actually blend/relight the result naturally.
5. **Reputation compounds — consistency matters more than any single great submission.** Since reward weighting is tier/reputation-based, a miner who's reliably "acceptable" (score 3) over many rounds likely out-earns one with occasional perfect scores (5) mixed with failures.
6. **Watch which of the three (or five) models you're running** — `MIID_MODEL_RANDOM` defaults to picking randomly per query; pinning to a specific model (or experimenting with the two "recommended alternatives," `flux_kontext`/`qwen`, which need more VRAM but offer stronger instruction-following) is an explicit, code-supported lever for differentiating your output quality.

## Key files
- `docs/miner.md` — by far the most current, precise, and internally-consistent document in the repo; trust this over the top-level README for anything mechanism-specific.
- `docs/Face Variation Reward System.pdf` — worked examples of accepted/rejected submissions.
- `MIID/miner/generate_variations.py` — the actual diffusion pipeline wiring, model list, and tunable generation parameters (`NUM_INFERENCE_STEPS`, `GUIDANCE_SCALE`).
- `MIID/validator/reward.py` — the full scoring/ranking/burn-event logic (`get_image_variation_rewards`, `_apply_blended_rank_cap_with_quality`).
- `MIID/miner/ada_face_compare.py` — the local AdaFace self-check implementation.
- `MIID/miner/drand_encrypt.py` / `MIID/validator/drand_utils.py` — the timelock-encryption submission scheme.
- `min_compute.yml` — present but stale (see warning); do not use for hardware planning on this subnet.

## Run / submit commands
```bash
git clone https://github.com/yanez-compliance/MIID-subnet.git && cd MIID-subnet
bash scripts/miner/setup.sh
source miner_env/bin/activate

git clone https://github.com/mk-minchul/AdaFace.git MIID/miner/AdaFace
mkdir -p MIID/miner/AdaFace/pretrained
gdown 1eUaSHG4pGlIZK7hBkqjyp2fc2epKoBvI -O MIID/miner/AdaFace/pretrained/adaface_ir50_ms1mv2.ckpt

export HF_TOKEN="hf_YOUR_TOKEN_HERE"
export FLUX_DEVICE="cuda"   # or mps
python -m MIID.miner.downloading_model

btcli wallet create --wallet.name miner_wallet --wallet.hotkey miner_hotkey
btcli subnet register --netuid 54 --wallet.name miner_wallet --wallet.hotkey miner_hotkey --subtensor.network finney

python neurons/miner.py --netuid 54 --subtensor.network finney \
  --subtensor.chain_endpoint wss://entrypoint-finney.opentensor.ai:443 \
  --wallet.name miner_wallet --wallet.hotkey miner_hotkey --logging.debug
# confirm the log line: "Phase 4 image generation: ENABLED"
```
Testnet first is explicitly recommended (netuid **322**) — a full walkthrough with W&B result visibility is documented in `docs/miner.md`.

## Verdict
**A legitimate, commercially-grounded subnet (real financial-institution clients cited) that has moved decisively past what both third-party sources still describe.** The multi-stage scoring pipeline (automated pre-checks → identity gate → variation-type detection → human review) and reputation-weighted payout are more sophisticated anti-gaming design than a simple per-round score, and the drand timelock encryption on submissions is a thoughtful touch against result-copying between miners mid-round. The real barrier is a genuine, non-optional GPU requirement (8GB+ VRAM minimum) that the repo's own `min_compute.yml` incorrectly downplays — don't let that file talk you out of the hardware you'll actually need, and don't let subnetalpha's outdated "name-based" framing convince you this is a text-generation subnet. Verify the current cycle window on the live dashboard before committing hardware/time, since the documented cycle dates have already elapsed relative to today.
