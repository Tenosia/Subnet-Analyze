# GAS (BitMind) — Subnet 34 (SN34)

**Generative Adversarial Subnet: AI-content detectors vs. AI-content generators, competing on the same subnet.** Repo: `/home/vps-project/Bittensor/bitmind-subnet` (`BitMind-AI/bitmind-subnet`, Python package `gas`, CLI `gascli`, very actively developed — 400+ merged PRs) · netuid **34** mainnet (379 testnet).

> **Archetype: two-sided adversarial market, both sides on-chain.** Unlike every other subnet in this series, SN34 isn't one competition — it's **two linked competitions that feed each other**. "Discriminative" miners submit deepfake/AI-content detector models; "Generative" miners run servers that produce synthetic images/video on demand. Validators score discriminators on how well they catch fakes (including fakes produced by the subnet's own generative miners) and score generators on how well they *fool* those discriminators. Each side's difficulty scales with the other's quality — the literal Generative Adversarial Network training dynamic, but implemented as two separate Bittensor miner populations instead of one model's two heads.
>
> **Rebrand note**: the subnet still trades as "BitMind" externally (`bitmind.ai`, the app/leaderboard) but the repo, package, and CLI have all been renamed to **GAS** — "Generative Adversarial Subnet." Both public sources given (docs.bitmind.ai, subnetalpha.ai) describe only the discriminator/detection side accurately; neither mentions the generative-miner track, C2PA provenance verification, or the per-model pricing-tiered reward system — all confirmed live in the current codebase below.

## Goal
"Fake content is evolving fast. Staying ahead demands relentless innovation" (README). Rather than training a detector once against a static dataset (which stops improving the moment generative models move on), GAS keeps detector training data current by running its own adversarial content-generation loop: generative miners are continuously pushed to produce more convincing fakes, discriminative miners are continuously pushed to catch them, and the resulting arms race both produces state-of-the-art detection models *and* a continually-refreshed public dataset of real vs. synthetic media (published to the `gasstation` Hugging Face org).

## What a miner does

### Discriminative miners (detection track)
1. Train a binary classifier (image, video, and/or audio — pick any combination) that outputs `[p_real, p_synthetic]` per sample. Semi-synthetic content (inpainting, face-swaps) is scored as `synthetic`.
2. Package it in **safetensors format only** (ONNX was deprecated and is no longer accepted) — a zip containing `model_config.yaml`, `model.py` (with a `load_model()` function, statically analyzed and sandbox-restricted: `torch`/`torchvision`/`torchaudio`/`transformers`/`timm`/`einops`/`flash_attn`/`PIL`/`cv2`/`scipy`/`numpy`/`safetensors` allowed; network access, system calls, serialization, and dynamic code execution all blocked), and the `.safetensors` weights.
3. Push it (`gascli d push --image-model ... --wallet-name ... --wallet-hotkey ...`) — this uploads to BitMind's cloud inference system and registers the model reference on-chain. **You do not host inference yourself** — evaluation runs entirely on BitMind's cloud infrastructure, a major capital-requirement reduction versus the subnet's earlier design (per the README).
4. Your model must first clear an **entrance exam**: `gasbench run --small` against ~100 samples/dataset, ≥80% accuracy required across submitted modalities, 1h25m wall-clock cap, run in a sandboxed environment with no network access. ONNX submissions are additionally scanned for embedded lookup-table/memorization cheat patterns pre-exam.
5. Passing models proceed to the **full benchmark** (`gasbench run --full`): the complete public + **private holdout** dataset suite, 5-hour cap per modality, refreshed weekly. This is what actually sets your `sn34_score` and TAO emissions.
6. Up to **three models per modality per hotkey** may be submitted (the README's summary table simplifies this to "one model per modality"; the detailed mining doc's "three" is the actual current limit).

### Generative miners (generation track)
1. Run a **FastAPI server** exposing `POST /gen_image`, `POST /gen_video`, `GET /health`, `GET /miner_info`, `GET /status/{task_id}` — validators send prompts, your server responds asynchronously via webhook.
2. **Local model hosting is deprecated and unsupported** (`MINER_DEVICE` config is explicitly marked "local models currently not supported" in the docs) — a generative miner today is purely an **API orchestrator**, not a GPU host. You configure `IMAGE_SERVICE`/`VIDEO_SERVICE` to route to OpenAI (DALL-E 3, Sora 2), OpenRouter (Gemini image models, Google Veo, ByteDance Seedance), Stability AI (SD 3.5, Stable Image Ultra/Core), or Runway (Gen-4.5, Veo via Runway) — bring your own API key for whichever you use. This makes the generative track's hardware profile identical in spirit to SN28 (gm): no local compute, real recurring API spend instead.
3. **Every generated sample must carry a valid C2PA (Content Credentials) signature chained to a trusted root** — Google C2PA Root CA G3, GlobalSign chains, Truepic's WebClaimSigningCA (for Sora), Byteplus/ByteDance. This is real industry cryptographic provenance metadata, not a self-reported flag — content from models that don't produce a verifiable C2PA chain is rejected outright, and the miner code itself blocks routing to non-compliant models to avoid wasting your own API spend on content that will be rejected anyway. Notably excluded as of this snapshot: Kling, Wan, Hailuo (no C2PA at all), Sora via OpenRouter specifically (self-signed cert), Seedance 1.5 Pro, and Runway Gen-4.5 (a signing-infrastructure bug on Runway's side).

## Scoring / evaluation

**Discriminators — `sn34_score`, winner-take-all per modality per round:**
- `MCC_norm = ((MCC + 1) / 2)^α` (α = 1.2) — normalized Matthews Correlation Coefficient, which measures raw discrimination accuracy.
- `Brier_norm = ((0.25 − Brier) / 0.25)^β` (β = 1.8) — normalized Brier score, which measures probability *calibration* (not just "is the prediction right" but "is the confidence trustworthy").
- `sn34_score = sqrt(MCC_norm × Brier_norm)` — a **geometric mean**, which by construction punishes a model that's strong on one axis but weak on the other; you can't win purely on raw accuracy while being badly overconfident, or vice versa.
- Image, video, and audio are scored **completely independently**, each with its own round, its own benchmark-version number, and its own single winner who takes the round's alpha reward — this is winner-take-all per modality, so a strong all-rounder isn't required; specializing in one modality is a fully viable strategy.

**Generators — three multiplicative reward factors:**
- **Base reward**: `R_base = pass_rate × min(verified_samples, 10)` — a ramp that rewards your first 10 verified samples per evaluation window disproportionately, discouraging low-volume, low-effort participation.
- **Fool-rate multiplier**: `M = clamp(0, 2.0, fool_rate × sample_size_multiplier)`, where `fool_rate = N_fooled / (N_fooled + N_not_fooled)` against live discriminator miners, and the sample-size multiplier penalizes small evaluation counts (below a reference count of 20) and gives a log-scaled bonus (up to 2×) above it — so both "actually fool detectors" and "do it across enough samples to be statistically meaningful" matter.
- **Model-price multiplier**: `multiplier = sqrt(model_price / baseline_price)`, where baseline is currently the cheapest C2PA-capable model (`google/veo-3.1-lite` at $0.03/s of 720p-equivalent video). This is an unusual, deliberate design choice: **more expensive, higher-quality generation models earn proportionally more per sample** (sqrt-scaled to avoid runaway gaps — 4× the price earns 2×, not 4×), explicitly to discourage a race-to-the-bottom on cheap, low-quality generators. Veo 3.1 (full) currently scores a 2.58× multiplier over baseline.
- These stack: your total reward is roughly base × fool-multiplier × price-multiplier, so throughput, adversarial quality, and model-tier choice all compound rather than substitute for each other.

## Hardware / device
Asymmetric by design, and confirmed from `min_compute.yml` plus both mining docs:
- **Discriminative miner**: **no GPU hosting required for serving** — inference/evaluation runs entirely on BitMind's cloud infrastructure. You'll want a GPU locally only for *training* your detector model in the first place (unspecified size — depends entirely on your chosen architecture).
- **Generative miner**: **no GPU at all** — local model hosting is deprecated; you're purely orchestrating third-party generation APIs. This is effectively a CPU-only, API-spend-based track, closer to SN28 (gm) than to any GPU-heavy subnet in this series.
- **Validator**: the heavy compute lives here. `min_compute.yml` specifies GPU **required**, **80GB VRAM minimum** (explicitly A100 80GB PCIe-class), compute capability 8.0+, 32GB RAM, 1TB SSD, 100/20 Mbps network — validators run both the evaluation cloud infrastructure workload and their own local generative models (per Incentive.md, "validators run [generative] models to produce a continual, fresh stream of synthetic and semisynthetic data") using a long list of open text-to-image/video models (SDXL, FLUX.1-dev, HunyuanVideo, CogVideoX, Wan2.2, etc.) in addition to scoring miners.

## Third-party / dependencies
- **BitMind's own cloud evaluation infrastructure** — where discriminator models actually run; a real centralization point (miners don't control or see this infrastructure directly, similar in spirit to SN28's coordinator-API pattern, but for compute rather than transaction routing).
- **Hugging Face** — the `gasstation` org hosts continuously-refreshed public benchmark data generated by validators; validator operators need to request `gasstation` org access from the BitMind team (`HUGGINGFACE_HUB_TOKEN` is a *required* validator env var).
- **Generation API providers** (generative miners, bring-your-own key): OpenAI, OpenRouter, Stability AI, Runway — see the trust-anchor list above for which specific models actually qualify under the C2PA requirement.
- **C2PA / Content Credentials infrastructure** — real-world cryptographic provenance standard (the same one Adobe, Google, Microsoft, OpenAI, and others use for AI-content labeling); trust anchors are pinned `.pem` certs in `gas/verification/trust_anchors/`.
- **Weights & Biases** (optional, validator-side logging).
- **PM2** — process management for both miner tracks and the three validator processes (`sn34-data`, `sn34-generator`, `sn34-validator`).

## How to win
**Discriminative track:**
1. Optimize for the geometric mean, not raw accuracy — a well-calibrated model that admits uncertainty scores better than an overconfident one with the same raw hit rate, given the Brier-score half of `sn34_score`.
2. Generalize past the public datasets — the full benchmark's private holdouts exist specifically to catch overfitting to the visible `gasbench` data; train for robustness to novel generation methods, not memorization of known ones.
3. Pick your modality battles — since each of image/video/audio is winner-take-all independently, a narrow, excellent audio-only detector is a fully valid strategy against a subnet full of generalists.
4. Clear the 80% entrance-exam bar comfortably before pushing — failing it wastes a submission cycle for nothing.

**Generative track:**
1. Get your C2PA chain right *before* investing in scale — an unsigned/misconfigured provider means every sample gets rejected regardless of quality; verify locally with `gascli generator verify-c2pa <file> --verbose` first.
2. Don't default to the cheapest model reflexively — the sqrt price-multiplier means a pricier, higher-quality model can out-earn a cheap one per sample if it meaningfully improves your fool rate, not just your raw output cost.
3. Volume past the sample-size reference count (20) to capture the logarithmic bonus, but not so much that quality (pass rate, fool rate) drops — both factors multiply into your final reward.
4. Track the provider/model exclusion list actively — it changes as providers fix or break their C2PA signing (Seedance 1.5 Pro and Runway Gen-4.5 are excluded *today* but flagged as likely to return).

## Key files
- `README.md` — accurate, current overview of both tracks and the rebrand to GAS.
- `docs/Incentive.md` — full scoring math for both tracks, plus the list of generative models validators run to produce training/eval data.
- `docs/Discriminative-Mining.md` — the two-stage entrance-exam/full-benchmark pipeline, sandbox import restrictions, model format spec.
- `docs/Generative-Mining.md` — provider/model list with exact C2PA trust-anchor status per model, and the full pricing-multiplier table.
- `gas/verification/c2pa_verification.py` + `gas/verification/trust_anchors/*.pem` — the actual provenance-verification implementation and pinned trust roots.
- `gas/evaluation/rewards.py` — generator reward computation (base/fool/price multipliers) and the live model price table.
- `min_compute.yml` — validator hardware spec (no miner-specific section — both miner tracks are lighter-weight by design).

## Run / submit commands
```bash
git clone https://github.com/BitMind-AI/bitmind-subnet.git && cd bitmind-subnet
./install.sh                          # add --no-system-deps for discriminative-only miners
source .venv/bin/activate

# Discriminative miner: push safetensors detector(s)
gascli d push \
  --image-model image_detector.zip --video-model video_detector.zip --audio-model audio_detector.zip \
  --wallet-name <wallet> --wallet-hotkey <hotkey> --netuid 34
gascli d perf --wallet-name <wallet> --wallet-hotkey <hotkey>   # check your scores

# Generative miner: configure .env.gen_miner (API keys, IMAGE_SERVICE/VIDEO_SERVICE), then:
gascli generator start
gascli generator verify-c2pa <file> --verbose   # sanity-check C2PA before relying on it

# Validator (needs an 80GB-VRAM-class GPU + gasstation HF org access)
cp .env.validator.template .env.validator   # fill WALLET_NAME, WALLET_HOTKEY, HUGGINGFACE_HUB_TOKEN
gascli validator start
```

## Verdict
**One of the more genuinely novel and well-engineered designs in this series.** The two-sided adversarial market is a real, structurally sound answer to the "detectors go stale the moment generators improve" problem that plagues any static deepfake-detection benchmark, and the C2PA provenance requirement on the generative side is a legitimately clever anti-cheat mechanism grounded in a real industry standard rather than a bespoke, gameable heuristic. Both tracks have a notably low local-hardware barrier for miners (discriminative miners don't host inference; generative miners don't host models at all anymore) — the real cost is training expertise (discriminative) or API spend plus getting provenance signing right (generative). The trade-off, as with SN28: BitMind's own cloud evaluation infrastructure is a real centralization point for the discriminative track that neither public source discloses, and worth understanding before assuming this is a fully peer-to-peer evaluation like SN26 (Perturb)'s validator-side re-verification model.
