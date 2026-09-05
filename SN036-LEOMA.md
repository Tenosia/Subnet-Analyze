# Leoma — Subnet 36 (SN36)

> ## ⚠️ THIS SUBNET NO LONGER EXISTS AT THIS NETUID (checked 2026-09-05, block 8,998,579)
>
> Netuid 36 was **re-registered at block 8,884,359 (~16 days ago)** and its chain name is now
> **`automata`**. It has **3 UIDs**, `alpha_out = 0`, and the owner's hotkey at UID 0 holds
> **100 % of incentive**. Leoma — the AI video-generation subnet described below, with the
> `Wan2.2-I2V-A14B` base and king-of-the-hill duels — **is gone from netuid 36**.
>
> Everything below is retained as a record of the previous occupant. Do not act on it.

**AI video generation, king-of-the-hill, deterministic reference-based duels.** Repo: `/home/vps-project/Bittensor/leoma` (`RendixNetwork/leoma`, Python, CLI `leoma`) · netuid **36** (finney).

> **Status check first, since you shared live metagraph data**: your screenshot shows netuid 36 marked **"At Risk"** by taostats, market cap ~$298K, only **1 active miner**, and UID 243 holding effectively 100% of incentive/dividends (1.0/1.0) with all other listed UIDs at zero. That's consistent with what the code predicts for an extremely young king-of-the-hill subnet: whoever currently holds the crown (or is the sole registered challenger) captures nearly all miner-side emission, because there's no one else to split it with yet. This is a legitimately new, resource-heavy, and currently very thin subnet — read the hardware section before assuming this is approachable.

## Goal
Produce state-of-the-art **image/text-to-video generation** ("Cinematic AI Video for Creative Teams" per the public site) through a continuously-defended champion model, using a scoring design built around one core idea: *finding* a better video model is hard, but *verifying* one is objectively easier when you have the real ground-truth continuation of a video clip to compare against — so the subnet scores candidates against **real held-out video**, not just relative preference between two generations.

## What a miner does
Miners never run inference themselves:
1. **Fine-tune the pinned base architecture** — currently `Wan2.2-I2V-A14B` (a 14B-parameter image-to-video diffusion model, digest-pinned in `chain.toml`), at 480p (832×480), 81 frames @ 16fps. All challengers must be architecturally compatible with this exact pinned config — a mismatched model shape is rejected pre-dispatch in seconds, no GPU spent.
2. **Upload weights to Hippius Hub** (a decentralized/content-addressed storage registry) under a repo named `leoma-<model-name>-<your-hotkey>`, public so validators can pull it without your credentials: `leoma miner push --model-dir ./out --repo <repo> --revision submission-001`.
3. **Commit the immutable reveal on-chain**: `leoma miner commit --repo <repo> --digest sha256:<...>` — only `repo + digest + hotkey` go on-chain (`set_reveal_commitment`); the mutable upload "revision" label is never submitted, only the immutable content digest.
4. **Wait to be duelled.** Every validator independently discovers your reveal, queues you as a challenger, and dispatches a duel to its own GPU eval server.

## Scoring / evaluation — "the duel"
Fully code-grounded from `chain.toml` (explicitly "THIS FILE IS THE EXAM PAPER") and `README.md`:

- **Reference-based, not relative.** Because the source corpus is real video, the ground-truth continuation of each held-out clip is known. King and challenger each generate a continuation from the same clip's first frame + prompt, using the **same block-hash-seeded per-clip seed** (so neither model can be tipped off in advance — the seed is unpredictable until the block is mined). Each generation is scored against the **real continuation** by reference distance — **LPIPS** (perceptual distance) by default, with MSE/SSIM available; lower is better.
- **Statistically confident crowning, not a raw comparison.** Over `n_clips = 32` held-out clips, the per-clip advantage (`king_distance − challenger_distance`) is bootstrapped (`n_bootstrap = 10000`, `alpha = 0.001`), and the crown only passes if the **lower confidence bound** exceeds `delta_threshold` (currently `0.0025`). A challenger that's marginally or luckily better does not dethrone the king.
- **A built-in cheat detector**: a trivial "freeze the conditioning frame and don't move" baseline is run as a **third duelist** through the same bootstrap. A challenger must beat this cheat baseline confidently too, not just the king — because on a mostly-static clip, doing nothing scores deceptively well against a naive reference-distance metric alone.
- **Everything that can move a verdict is pinned in `chain.toml` and hashed into a `consensus_digest`** sent with every eval request and echoed back in every verdict: the corpus, generation parameters (frame count/fps/resolution/steps/guidance), the metric, the threshold, even the Python/CUDA/compute-capability/dependency-lock versions of the eval box itself. A validator running a different config is refused at the door rather than silently producing a divergent verdict — this is a genuinely unusual level of consensus rigor for a Bittensor subnet.
- **The corpus is a pinned, digest-addressed manifest**, not a live bucket listing — which video, which window inside it, and the hash of the decoded ground-truth frames are all fixed offline ahead of time, so "two honest validators disagree" bugs from listing/scene-detection differences are structurally impossible.
- **Emission**: the crowned king plus up to **4 prior kings still registered** ("the king chain") split weight **equally**. If there is no valid king — including at genesis, before a corpus/seed digest is pinned — **100% burns to UID 0**, deliberately: the previous design that auto-crowned the first-ever reveal with no duel was judged strictly worse than burning, since it just handed the subnet to whoever committed first.

## Hardware / device
Sharply asymmetric, and the validator side is genuinely one of the most expensive in this entire series:
- **Miner**: no inference hosting at all — but fine-tuning a 14B-parameter video diffusion model to a competitive standard is itself a serious training compute requirement (unspecified minimum; scales with your approach — full fine-tune vs. LoRA/adapter, dataset size, etc.).
- **Validator's eval server** (the GPU box that actually runs the duels): the production layout requires **exactly 8× H100 80GB** visible with no other process consuming their VRAM (`docker-compose.eval.8xh100.production.yml`, one isolated process per GPU pair), CUDA 12.4, compute capability 9.0 (Hopper-specific — this pin will reject Ampere-class A100s or anything older). Model-level CPU offload is used to keep only the active transformer expert on each card, and this offload mode is itself a **consensus pin**, not an operator tuning choice — every eval box must run identically. This is roughly **$150-250k+ of GPU hardware** at current market rates, or the equivalent in rental cost, just to stand up one compliant evaluator — far beyond Perturb's 8-GPU-but-any-generation ask or BitMind's single 80GB card.
- **The validator process itself** (chain scanning, dispatching duels, setting weights) is lightweight — the GPU cost lives entirely in the separate eval server it talks to over `EVAL_SERVER_URL`, typically an SSH tunnel.
- This hardware asymmetry — and the fact that even the *validator* side requires an eight-figure-adjacent GPU investment — is almost certainly why the subnet currently shows so few active validators/miners in your screenshot; the entry cost on both sides is real.

## Third-party / dependencies
- **Hippius Hub** — decentralized/content-addressed model storage; miners upload here, validators pull public repos anonymously (no credentials needed to read).
- **A private Hippius state bucket** — validators need this for durable king-chain persistence (`HIPPIUS_OWN_BUCKET`; legacy R2-compatible aliases supported).
- **A public-read dashboard bucket** — validators publish a `dashboard.json` snapshot separately from their private canonical state.
- **Bittensor / Subtensor** — standard reveal-commitment scanning and `set_weights`.
- **PyTorch / diffusers / lpips** (the eval server's `[eval]` extra) — the actual generation + scoring stack, version-pinned via `eval_lock_digest` in `chain.toml`.
- No LLM-API or third-party inference dependency of the kind seen in SN28/SN34's generator tracks — generation happens entirely locally on the eval server's own GPUs, from locally-downloaded weights.

## How to win
1. **Beat the pinned base model, not an arbitrary bar.** The genesis king is the stock, un-fine-tuned `Wan2.2-I2V-A14B` itself — your job as a first challenger is to fine-tune it into something that reconstructs real held-out video continuations more faithfully (lower LPIPS distance) than the unmodified base, by a statistically confident margin.
2. **Optimize for the real metric, not a proxy.** Since scoring is LPIPS distance to the *actual* ground-truth continuation (not human preference, not a CLIP-alignment score alone — those files exist in `eval/_clip.py`/`eval/_flow.py` but LPIPS is the pinned default duel metric), the objective is genuinely "predict what happens next in this exact clip," not just "look plausible."
3. **Don't rely on staying static.** The freeze-baseline anti-cheat means a model that hedges by barely animating won't automatically win on low-motion clips — it's explicitly tested against the "do nothing" cheat and must beat that too.
4. **Watch the calibration risk the code itself flags as the biggest open risk**: `delta_threshold = 0.0025` needs to exceed the cross-GPU noise floor of generation itself (LPIPS scoring is deterministic on CPU, but the GPU generation step is not bit-exact across hardware) — the subnet operators explicitly call this "the subnet's largest open consensus risk," so a challenger's win/loss margin near that threshold could, in principle, be sensitive to which physical validator GPU ran it. Not something you control, but worth knowing the ground is still being calibrated.
5. **Given the current single-miner state**, dethroning the existing king (if one is crowned) may currently be more achievable than on a mature, heavily-contested subnet — but verify current chain state yourself before assuming that's still true, and confirm you can actually clear the fine-tuning + confident-margin bar before committing training resources.

## Key files
- `README.md` — clear, accurate, and unusually well-written; matches the code closely.
- `leoma/chain.toml` — the entire consensus surface: architecture pin, corpus manifest digest, generation parameters, duel metric/threshold/bootstrap config, runtime environment pins. Read this before anything else.
- `leoma/app/validator/king.py` + `king_state_store.py` — the king-chain crowning and persistence logic.
- `leoma/app/validator/copy_check.py` / `reveal_scan.py` — anti-plagiarism and on-chain reveal discovery.
- `leoma/eval/_lpips.py`, `eval/metrics.py`, `eval/calibrate.py` — the actual duel metric implementation and calibration tooling.
- `docs/PRODUCTION_8XH100_RUNBOOK.md` — exact eval-server hardware/deployment requirements.
- `docs/TESTNET_RUNBOOK.md` — includes the cross-GPU noise-floor calibration procedure referenced above.
- `docs/CORPUS_V2_PILOT_RUNBOOK.md` — a next-generation captioned corpus in active development, explicitly **not yet activated** on mainnet consensus (`chain.toml` still points at corpus v1) — worth checking whether this has shipped by the time you read this, since it would be a consensus-changing event.

## Run / submit commands
```bash
# Miner: fine-tune Wan2.2-I2V-A14B per chain.toml's pinned config, then:
leoma miner push --model-dir ./out \
  --repo <user-or-project>/leoma-<model-name>-<your-hotkey-ss58> --revision submission-001
leoma miner commit --repo <repo> --digest sha256:<...> --coldkey <wallet-name> --hotkey <hotkey-name>

# Validator (requires a separately-hosted 8xH100 eval server, reached over SSH tunnel)
pip install -e .
cp env.validator.example .env   # wallet, EVAL_SERVER_URL, HIPPIUS_OWN_*
leoma serve

# Eval server (the GPU box)
uv sync --frozen --extra eval --no-dev
cp env.eval.example .env        # HIPPIUS_VIDEOS_READ_*
uv run leoma servers eval-server
leoma corpus verify --sample 4  # prove the box decodes the pinned corpus byte-identically before it duels
```

## Verdict
**The most rigorously engineered consensus design in this entire series, and also the most capital/hardware-intensive to participate in on the validator side.** The reference-based, digest-pinned, bootstrap-confident duel mechanism is a genuinely thoughtful solution to a hard problem (grading video generation objectively and reproducibly across independent validators), and the code's own comments are unusually honest about open risks (the cross-GPU noise floor calibration gap is flagged as the single biggest risk, in the code itself, rather than glossed over). But this honesty cuts both ways: it's a young, thin subnet right now — one active miner, an "At Risk" flag, and an 8×H100 hardware floor just to run a compliant validator — so treat it as an early, high-effort, high-hardware-barrier opportunity rather than something to casually try. Confirm current chain state (miner count, current king, recent duel activity) directly before committing real fine-tuning or GPU-rental resources.
