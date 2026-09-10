# Subnet Comparison Table

**39 Bittensor subnets, one snapshot.** Every economic figure below was read
live from finney at **block 9,031,872 (2026-09-09)**, TAO ≈ $256, so the rows are
directly comparable to each other. The individual analysis files use the α price
at each file's own analysis date and will differ.

> **Read this before using the numbers.** *Earning / UIDs* counts UIDs with
> non-zero incentive right now — it is the single best signal of whether a
> competitive field exists. *Owner capture* is the 18 % protocol cut **plus** any
> incentive and dividends flowing to the owner's own hotkey. *Top earner $/day*
> is marked **← owner** where the highest-paid UID is the subnet owner's.

---

## 1 · Live economics

| Subnet | File | Task | Miner deliverable | Miner GPU | Entry cost | α (USD) | Earning / UIDs | Top earner $/day | Owner capture | The catch |
|---|---|---|---|---|---|---|---|---|---|---|
| **SN14 Cacheon** | [`SN014-CACHEON.md`](SN014-CACHEON.md) | Inference-server speed race | Docker container serving a pinned 72B model | **yes** — serving rig | $0.13 | $2.40 | **12 / 256** | $1,258 | 49.7 % | Fastest *correct* server wins; two-pass correctness gate |
| **SN18 Zeus** | [`SN018-ZEUS.md`](SN018-ZEUS.md) | Weather / climate forecasting | ERA5 global-grid predictions | training yes; serving no | $256.00 | $1.00 | **13 / 257** | $1,456 | 45.5 % | Ships a random-number placeholder — you build the whole model |
| **SN25 UR** | [`SN025-UR.md`](SN025-UR.md) | Decentralized VPN / privacy network | Routable IP breadth — carry ingress+egress traffic | **none** | $0.13 | $2.54 | 1 / 256 | $7,497 ← **owner** | 64.2 % | Mechanism is testnet-first and **not live on mainnet**; owner's UID takes the whole pool |
| **SN26 Perturb** | [`SN026-PERTURB.md`](SN026-PERTURB.md) | Adversarial red-teaming of an image classifier | Adversarial examples via a hosted API | modest | $25.60 | $0.88 | **10 / 256** | $1,819 | 53.9 % | An undocumented, centrally-controlled burn rate sits on top |
| **SN28 SayGM** | [`SN028-GM.md`](SN028-GM.md) | Confidential LLM-API marketplace | A TEE-attested inference endpoint | **yes** — serving rig | $25.60 | $5.27 | **65 / 256** | $4,357 | 42.6 % | Paid on *revenue share*, not model quality |
| **SN29 hoτfloaτ** | [`SN029-COLDINT.md`](SN029-COLDINT.md) | *(file says coldint — dormant)* | — | — | $0.13 | $0.84 | 1 / 256 | $2,472 | 18.0 % | ⚠️ **Chain name is now `hoτfloaτ`.** File's "100 % burns" is stale — 1 UID takes the pool |
| **SN34 BitMind / GAS** | [`SN034-BITMIND.md`](SN034-BITMIND.md) | Detectors **vs** generators, both on-chain | A detector or a generator model | **yes** | $128.00 | $3.02 | **109 / 256** | $3,038 | 57.2 % | Winner-take-all per modality per round; **owner takes 93 %** |
| **SN35 Cartha (0xMarkets)** | [`SN035-CARTHA.md`](SN035-CARTHA.md) | Liquidity mining — **not AI** | USDC locked into a vault | **none** | $25.60 | $0.59 | 2 / 256 | $1,538 | 18.0 % | Pure capital deployment; six figures for a principal vault |
| **SN36 Epago** | [`SN036-LEOMA.md`](SN036-LEOMA.md) | *(file is 2 occupants stale — now `Epago`)* | — | — | $256.00 | $18.17 | 1 / 3 | $53,639 ← **owner** | 59.0 % | ⚠️ **Renamed twice: `Leoma`→`automata`→`Epago`.** 3 UIDs, 1 earner; now emitting |
| **SN38 ChronoLLM** | [`SN038-CHRONOLLM.md`](SN038-CHRONOLLM.md) | Chronologically-consistent LLMs, one per year | A trained model per target year | **yes** | $189.44 | $2.05 | **10 / 256** | $3,146 | 51.6 % | README's "winner takes all" is stale — it's exponential decay across ranks |
| **SN40 Ralph** | [`SN040-RALPH.md`](SN040-RALPH.md) | Open model compression — Qwen3-8B into bit tiers | A compressed GGUF + a commit-reveal hash | offline compression only | $253.44 | $0.98 | 1 / 256 | $2,881 | 43.5 % | **Every published crown-holder earns zero**; one uncrowned UID takes the whole pool |
| **SN43 Graphite** | [`SN043-GRAPHITE.md`](SN043-GRAPHITE.md) | Graph/routing (TSP) **+ portfolio trading** | TSP solver, and/or a copy-trade leader | **none** | $25.60 | $1.18 | 5 / 256 | $2,778 | 58.9 % | README covers ~60 % of what actually pays |
| **SN47 Feval** | [`SN047-FEVAL.md`](SN047-FEVAL.md) | Verifiable LoRA evaluation | Adapter + published rollouts | 24–48 GB | $12.80 | $0.70 | 2 / 149 | $1,878 ← **owner** | **78.8 %** | Published repo ≠ live network; owner takes the whole miner pool |
| **SN53 Engy** | [`SN053-ENGY.md`](SN053-ENGY.md) | Verified LLM inference for real buyers | GPU serving capacity | **yes** — ref 4× RTX 4090 | $0.13 | $6.42 | **68 / 256** | $6,520 | 33.9 % | Earnings ∝ paid tokens served; 99 %+ acceptance SLA |
| **SN54 MIID (Yanez)** | [`SN054-MIID.md`](SN054-MIID.md) | Identity-preserving face variations for KYC | Synthetic image variations | **yes** — ~16 GB | $0.13 | $1.12 | **100 / 256** | $1,154 | 65.0 % | Both public sources describe a phase that has already passed |
| **SN58 Greevils** | [`SN058-GREEVILS.md`](SN058-GREEVILS.md) | TEE algo-trading on Hyperliquid | Agent in a TDX VM, or a plain HL account | none (VM ~$145/mo) | $25.60 | $2.04 | 1 / 256 | $6,030 | 41.2 % | Sole earner holds no on-chain commitment; zero `gva1` approvals |
| **SN60 Bitsec** | [`SN060-BITSEC.md`](SN060-BITSEC.md) | AI agents finding real smart-contract vulns | A security agent | modest | $0.13 | $1.08 | 2 / 256 | $1,594 | 38.5 % | Payout ranks by *agent*, not hotkey — one miner takes the pool |
| **SN61 RedTeam** | [`SN061-REDTEAM.md`](SN061-REDTEAM.md) | Bots that beat bot-detection, and vice versa | A Dockerised bot | modest | $14.89 | $3.49 | **42 / 256** | $446 | 18.0 % | Docs contradict themselves on which challenges are live |
| **SN71 Leadpoet** | [`SN071-LEADPOET.md`](SN071-LEADPOET.md) | B2B sales-lead generation | Qualified decision-maker leads | **none** — CPU + APIs | $0.16 | $1.22 | **78 / 256** | $2,555 ← **owner** | **70.3 %** | Live logic runs in a hosted AWS-Nitro TEE; the axon path is deprecated |
| **SN76 Phylax** | [`SN076-PHYLAX.md`](SN076-PHYLAX.md) | AI supply-chain security attestation | One Python file (`agent_main`) | **none** | $0.13 | $1.27 | 1 / 72 | $3,762 ← **owner** | 59.0 % | Your track's rounds have to actually be scheduled |
| **SN78 UMI (ex-Vocence)** | [`SN078-UMI.md`](SN078-UMI.md) | ASL→English translation *(pre-activation)* | HTTP translator service | yes, 24–80 GB | $0.13 | $1.24 | 1 / 256 | $3,675 ← **owner** | 59.4 % | Weights type-level disabled; the 0.10 quality floor is unproven |
| **SN79 MVTRX** | [`SN079-MVTRX.md`](SN079-MVTRX.md) | Agent-based market simulation | Always-on trading bot | **none** | $8.04 | $0.92 | **216 / 256** | $247 | 59.0 % | Below half the median score you earn exactly zero |
| **SN80 OpenRoboto** | [`SN080-OPENROBOTO.md`](SN080-OPENROBOTO.md) | Fine-tune π0.5 VLA robotics | A HuggingFace checkpoint | **yes** — A100-class | $0.13 | $4.19 | 5 / 256 | $5,305 | 23.2 % | ~$19/attempt; most of the pool sits on the operator's UID 0 |
| **SN82 Compelle** | [`SN082-COMPELLE.md`](SN082-COMPELLE.md) | Adversarial LLM debate | A prompt, committed on chain | **none** | $0.13 | $0.82 | 1 / 64 | $2,423 | 29.0 % | Incumbent-protected winner-take-all on only 64 slots |
| **SN90 KubeTEE** | [`SN090-KUBETEE.md`](SN090-KUBETEE.md) | DePIN confidential compute | A TDX GPU cluster | 8-node TDX datacenter | $0.13 | $7.25 | 2 / 98 | $16,191 ← **owner** | **67.4 %** | Onboarding is operator-gated — you cannot join |
| **SN92 MicroTensor** | [`SN092-MICROTENSOR.md`](SN092-MICROTENSOR.md) | Certified inference systems | ONNX/GGUF artifact + 128-byte pointer | training only (RTX 3090+) | $25.60 | $0.86 | **9 / 256** | $1,272 ← **owner** | 58.4 % | Docs name the wrong paying track |
| **SN93 Bitcast** | [`SN093-BITCAST.md`](SN093-BITCAST.md) | Creator marketing — YouTube + X, paid on verified attention | An axon serving creators' YouTube OAuth tokens | **none** | $1.28 | $5.29 | 3 / 256 | $12,721 ← **owner** | **78.4 %** | Owner's hotkey **is** the burn UID and takes ~64 % of weight; emission field contradicts the weight vector |
| **SN101 Tag101** | [`SN101-TAG101.md`](SN101-TAG101.md) | Semantic tagging of X posts | 3 topic tags per post | **none** — CPU + LLM API | $0.13 | $1.10 | **246 / 256** | $2,914 ← **owner** | **78.5 %** | Consensus-scored: you're paid for predicting the crowd |
| **SN103 Capcomp** | [`SN103-CAPCOMP.md`](SN103-CAPCOMP.md) | LoRA composition | One JSON merge recipe | 32–48 GB | $256.00 | $0.66 | 1 / 128 | $1,958 | 56.8 % | Dethrone margin sits ~24× below measurement noise |
| **SN105 Beam** | [`SN105-BEAM.md`](SN105-BEAM.md) | Decentralised bandwidth / CDN | Nothing — you *run infra* | **none** | $0.16 | $1.57 | **211 / 256** | $81 | 56.2 % | Bandwidth + public IP + 24/7 uptime; only Qualified orchestrators earn |
| **SN107 Minos** | [`SN107-MINOS.md`](SN107-MINOS.md) | Genomic variant calling | Variant-caller hyperparameter config | **none** | $253.44 | $14.67 | **20 / 100** | $34,409 | 51.4 % | Field has filled since the file was written — 1 → 21 earners |
| **SN114 SOMA** | [`SN114-SOMA.md`](SN114-SOMA.md) | Token-efficient SWE coding agents | Python compression module | **none** | $64.00 | $3.33 | 4 / 256 | $7,855 | 39.6 % | You pay inference; re-qualify every 2 weeks |
| **SN118 Ditto** | [`SN118-DITTO.md`](SN118-DITTO.md) | Agent-memory harness | Rust harness in Docker | **none** — CPU, 8 GB | $0.13 | $2.18 | 5 / 256 | $4,188 | 42.8 % | Crown locked near 0.97; ~$5/submission |
| **SN119 CapabilityForge Next** | [`SN119-CAPABILITYFORGE.md`](SN119-CAPABILITYFORGE.md) | Training-data improvement for learning AI *(no implementation)* | **Undefined** — no format, no submission path | unknown | $0.13 | $0.71 | 1 / 256 | $2,096 ← **owner** | 61.6 % | **The repo is a 32-line README.** No code, 0 commitments; owner takes the whole pool |
| **SN120 Affine** | [`SN120-AFFINE.md`](SN120-AFFINE.md) | Incentivised RL / reasoning competition | Fine-tuned LLM referenced on chain | **yes** | $147.79 | $13.53 | 5 / 256 | $7,985 | 58.5 % | Champion-vs-challenger, winner-take-all |
| **SN121 Sundae Bar** | [`SN121-SUNDAEBAR.md`](SN121-SUNDAEBAR.md) | AI "skill" evaluation for one commercial agent | A rubric-scored artifact | modest | $0.13 | $1.06 | 2 / 256 | $1,874 ← **owner** | **72.5 %** | Majority-burn: #1 gets only ~20 % of weight |
| **SN123 MANTIS** | [`SN123-MANTIS.md`](SN123-MANTIS.md) | Financial signal prediction | Encrypted prediction embeddings | **none** | $38.40 | $0.65 | **249 / 256** | $675 ← **owner** | 58.6 % | Copy-proof by construction; proportional payout |
| **SN124 Swarm** | [`SN124-SWARM.md`](SN124-SWARM.md) | Autonomous drone-pilot AI (RL) | A trained flight policy | **none** to run | $128.00 | $2.85 | **25 / 256** | $927 | 48.1 % | **One shot per hotkey** — benchmark all 1,100 seeds first |
| **SN127 Astrid** | [`SN127-ASTRID.md`](SN127-ASTRID.md) | AI trading competitions (live agents) | A live trading agent | **none** | $0.13 | $0.65 | 1 / 256 | $1,931 ← **owner** | **83.1 %** | Winner-take-few — top 3 by PnL per competition |

---

## 2 · What it takes to mine

The dimensions the [README](README.md) uses to compare, extended to all 39.

| Subnet | Core skill | Reward shape | Copy-resistant? | You pay inference? | Hardware barrier |
|---|---|---|---|---|---|
| **SN14 Cacheon** | Inference-serving optimisation / DevOps | Winner-take-most | Image is public once pushed | No — you serve | **High** — serving rig for a 72B model |
| **SN18 Zeus** | ML forecasting (weather) | Pure ML competition | Model stays yours | No | Training GPU; serving is CPU |
| **SN25 UR** | Network operations / IP-address procurement | Two tiers: pooled tail (Merkle claim) + top-~200 head paid natively | **Yes** — shared prefixes split `1/claim(h)` | No | **None** — the scarce asset is *diverse routable prefixes*, not hardware |
| **SN26 Perturb** | Adversarial ML / CV | Per-challenge, plus an opaque burn | Attacks are one-shot | No | Low–moderate |
| **SN28 SayGM** | Cloud / TEE operations | **Revenue-proportional** | N/A — it's capacity | No — buyers pay you | **High** — TEE-attested serving |
| **SN29 hoτfloaτ** | *unverified — file is stale* | 1 UID currently takes the pool | ? | ? | ? |
| **SN34 BitMind / GAS** | Deepfake detection **or** generation | Winner-take-all per modality per round | Model stays yours | No | **High** — GPU both sides |
| **SN35 Cartha** | **None — capital only** | Proportional to locked USDC | N/A | No | **Zero compute**; six-figure USDC for a principal vault |
| **SN36 Epago** | *unknown — brand-new subnet* | Owner holds 100 % | ? | ? | ? |
| **SN38 ChronoLLM** | LLM pre/post-training | Exponential decay across ranks | Model stays yours | No | **High** — training GPU |
| **SN40 Ralph** | Quantization / PTQ research | Per tier: king 80 %, best challenger 20 %, rest nothing | **Yes** — a copy ties at zero margin | No | **Offline GPU** to quantize an 8B model; no serving |
| **SN43 Graphite** | Combinatorial optimisation **+** quant | Three-way split | Solutions are per-task | No | Low |
| **SN47 Feval** | LoRA fine-tuning | 3 seats (62.5 / 25 / 12.5 %) | Rollouts are published | No | One 24–48 GB GPU |
| **SN53 Engy** | GPU operations | **∝ paid tokens served** | N/A — it's capacity | No — buyers pay | **High** — multi-GPU rig |
| **SN54 MIID** | Generative CV | Per-cycle scoring | Model stays yours | No | ~16 GB GPU |
| **SN58 Greevils** | Quant trading | Pairwise tournament, dollar-capped human lane | Strategy must be open-sourced to earn | No | None — but **~$25k trading capital** |
| **SN60 Bitsec** | Security engineering (smart contracts) | One agent currently takes the pool | Findings are per-codebase | Likely | Low–moderate |
| **SN61 RedTeam** | Web automation / anti-detection | Decaying per-challenge points | Docker images are submitted | No | Low–moderate |
| **SN71 Leadpoet** | Data pipelines + sales intelligence | Per-request service | Leads are verifiable | **Yes** — API costs | **Low** — CPU + APIs |
| **SN76 Phylax** | Security engineering | Tiered | Detector code is yours | **Yes** — ~$21/attempt | **None** |
| **SN78 UMI** | ML / sign-language translation | *(not yet active)* | Model stays yours | No | 24–80 GB GPU |
| **SN79 MVTRX** | Quant trading | **Proportional**, with a half-median floor | Strategy stays yours | No | **Low** — small VPS |
| **SN80 OpenRoboto** | ML / robotics | Winner-take-most | Checkpoints are **public** | No | **High** — A100-class |
| **SN82 Compelle** | Rhetoric + prompt engineering | Incumbent-protected winner-take-all | Strategies are **public** | No | **None** |
| **SN90 KubeTEE** | Datacenter operations | Proportional to GPU capacity | N/A — it's capacity | No | **Extreme** — 8-node TDX cluster |
| **SN92 MicroTensor** | Model compression | Hypervolume frontier, 8 paid ranks | ε-collapse punishes copies | No | Training GPU only |
| **SN93 Bitcast** | Creator-network operations / BD | **USD-bounded** — pays only for verified attention; burn UID absorbs the rest | Attention is per-video and verified | No | **None** — a $5 VPS; the cost is recruiting creators |
| **SN101 Tag101** | Data pipelines | Winner-take-most, consensus-scored | Tags are commodity | **Yes** — LLM API | **Low** — CPU |
| **SN103 Capcomp** | LoRA composition search | 10 ranks, rank 1 takes 90 % | Recipes published after payout | No | One 32–48 GB GPU |
| **SN105 Beam** | DevOps / bandwidth | **Tiered** — top 10 % take ~80 % | N/A — it's capacity | No — you pay **egress** | **Bandwidth + public IP + 24/7** |
| **SN107 Minos** | Bioinformatics / tuning | Winner-take-most | Configs are simple | No | **Low** — CPU, ≥60 GB disk |
| **SN114 SOMA** | Agent + token-efficiency engineering | Per-element tournament | Duplicate-adjacent | **Yes** — OpenRouter/DeepSeek | **Low** — dev machine |
| **SN118 Ditto** | Rust + information retrieval | **King-of-the-hill** (65–90 % to champion) | **Yes** — duplicate detection | No | **Low** — CPU, 8 GB |
| **SN119 CapabilityForge Next** | *unknown — nothing published* | *undefined* | n/a | unknown | *unknown — no spec, no software* |
| **SN120 Affine** | RL / reasoning fine-tuning | Winner-take-all champion | Model referenced on chain | No | **High** — training GPU |
| **SN121 Sundae Bar** | Rubric writing / agent design | **Majority-burn** — #1 gets ~20 % | Artifacts are scored, not held | Likely | Low–moderate |
| **SN123 MANTIS** | Quant / ML finance | **Proportional** (salience) | **Yes** — L2 split + uniqueness | No | **Lowest** — small VPS |
| **SN124 Swarm** | RL / robotics / control | King-of-the-hill, **last 5 champions paid** | Policy stays yours | No | **None** to run |
| **SN127 Astrid** | Quant trading | **Winner-take-few** — top 3 by PnL | Live agent, private | Maybe — LLM calls | **None** — Arena API |

---

## 3 · What the snapshot says

**17 of the 39 have a genuinely contested field** (≥ 9 UIDs earning):
**SN123 MANTIS** (249), **SN101 Tag101** (246), **SN79 MVTRX** (216), **SN105 Beam** (211), **SN34 BitMind** (109), **SN54 MIID** (100), **SN71 Leadpoet** (78), **SN53 Engy** (68), **SN28 SayGM** (65), **SN61 RedTeam** (42), **SN124 Swarm** (25), **SN107 Minos** (20), **SN18 Zeus** (13), **SN14 Cacheon** (12), **SN38 ChronoLLM** (10), **SN26 Perturb** (10), **SN92 MicroTensor** (9).

**11 pay exactly one UID:** SN25, SN29, SN36, SN40, SN58, SN76, SN78, SN82, SN103, SN119, SN127.
On **14** the single top earner **is the owner's own hotkey**: SN25, SN36, SN47, SN71, SN76, SN78, SN90, SN92, SN93, SN101, SN119, SN121, SN123, SN127.

**⚠️ SN103 Capcomp has collapsed since the last snapshot** — from **10 earners to
1** (UID 2 now takes 100 %). It was previously recommended here as a contested
field; treat that recommendation as withdrawn pending re-analysis.

**SN80 OpenRoboto has improved sharply** — owner capture fell from ~52 % to
**23.2 %**, and the top earner is no longer the owner's UID.

**Owner capture spans 18.0 % to 92.6 %**, and **SN119 CapabilityForge Next is the
starkest case in the set**: its entire published implementation is a 32-line
README committed the day this snapshot was taken, with **zero on-chain
commitments**, while the owner's UID takes 100 % of the miner pool.

---

## 4 · ⚠️ Staleness found while re-checking

Re-reading every file against live chain state surfaced four items where the
document no longer describes the subnet:

| File | What it says | What the chain says now |
|---|---|---|
| [`SN029-COLDINT.md`](SN029-COLDINT.md) | *"coldint. Status: DORMANT. 100 % of weight burns. Do not mine here."* | Chain name is **`hoτfloaτ`**. One UID (19, **not** the owner) takes 100 % of the miner pool, and owner capture is only the bare 18 % cut. **The burn claim is stale — re-analysis needed.** |
| [`SN036-LEOMA.md`](SN036-LEOMA.md) | Leoma — AI video generation, king-of-the-hill, `Wan2.2-I2V-A14B` | Netuid 36 is now **`automata`**, **re-registered at block 8,884,359 (~16 days ago)**, with **3 UIDs** and `alpha_out = 0`. **The Leoma subnet no longer exists at this netuid.** |
| [`SN107-MINOS.md`](SN107-MINOS.md) | *"~1 active miner (open field)"* | **21 UIDs earning.** The open field has closed; α is also the highest in the set at **$13.88**, with owner capture at 83.7 %. |
| [`README.md`](README.md) | *"Deep-dive summaries of **eight** Bittensor subnets"* · snapshot 2026-07-31 | **35 subnets** are now documented here. |

Two further items worth a look, flagged but not confirmed stale:
**SN60 Bitsec** (2 earners — the file's "one miner captures the pool" still
holds) and **SN35 Cartha** (2 earners, owner capture at the 18 % floor).

---

## 5 · How to choose

**If you want a field you can actually place in** — ≥ 20 earners and a
proportional or tiered payout rather than winner-take-all:
**SN123 MANTIS** (249 earners, proportional, copy-proof, lowest hardware bar),
**SN79 MVTRX** (217, proportional above a median floor, no GPU, free testnet),
**SN105 Beam** (202, tiered, but you need bandwidth and 24/7 uptime),
**SN124 Swarm** (25, and it pays the **last five** champions, so a breakthrough
keeps earning).

**If you have GPUs and want to sell capacity rather than compete on models:**
**SN53 Engy** (68 earners, paid ∝ tokens actually served) or **SN28 SayGM**
(45 earners, revenue share). Both are operations problems, not ML problems.

**If you have no GPU and no capital:** **SN76 Phylax**, **SN82 Compelle**,
**SN101 Tag101**, **SN118 Ditto**, **SN123 MANTIS**, **SN107 Minos**, **SN93 Bitcast** — all CPU-only.
Note SN101 and SN114 make you pay for inference.

**If you are a strong ML engineer with a training rig:** **SN92 MicroTensor**
(9 seats, geometric curve where rank 8 still earns ~⅓ of rank 1, and the
frontier is fully public), **SN103 Capcomp**, **SN120 Affine**, **SN18 Zeus**.

**Avoid or verify first:** **SN36 Epago** (brand-new, owner holds everything),
**SN29 hoτfloaτ** (file stale, one earner), **SN90 KubeTEE** (you cannot join —
onboarding is operator-gated), **SN78 UMI** (weights not yet active),
**SN34 BitMind** (93 % owner capture), **SN107 Minos** (83.7 %).

---

## 6 · Universal cautions

1. **Verify economics live before committing capital.** Alpha price, earner
   counts, burn share and champion scores all move — several moved materially in
   the days between the individual files and this snapshot.
2. **Winner-take-most vs proportional is the single biggest structural choice.**
   Eight of these subnets pay exactly one UID.
3. **Check whether the top earner is the owner.** On ten of the 35 it is.
4. **Read the incentive code, not the marketing.** Every file in this folder that
   was written from source found the public description stale or wrong somewhere —
   SN36, SN38, SN43, SN47, SN54, SN60, SN61, SN90, SN92 and SN121 all carry an
   explicit accuracy caveat.
5. **A netuid is not a permanent identity.** SN36 was re-registered as a different
   subnet entirely; SN29 and SN78 were renamed under new operators.

---

*Generated from live finney state at block 8,998,579 on 2026-09-05. Regenerate
whenever a new subnet analysis is added to this folder.*
