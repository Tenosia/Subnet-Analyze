# Subnet Comparison Table

**35 Bittensor subnets, one snapshot.** Every economic figure below was read
live from finney at **block 8,998,579 (2026-09-05)**, TAO ≈ $256, so the rows are
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
| **SN14 Cacheon** | [`SN014-CACHEON.md`](SN014-CACHEON.md) | Inference-server speed race | Docker container serving a pinned 72B model | **yes** — serving rig | $0.13 | $2.49 | 6 / 256 | $2,230 | 48.6 % | Fastest *correct* server wins; two-pass correctness gate |
| **SN18 Zeus** | [`SN018-ZEUS.md`](SN018-ZEUS.md) | Weather / climate forecasting | ERA5 global-grid predictions | training yes; serving no | $256.00 | $1.11 | **35 / 257** | $795 | 50.3 % | Ships a random-number placeholder — you build the whole model |
| **SN26 Perturb** | [`SN026-PERTURB.md`](SN026-PERTURB.md) | Adversarial red-teaming of an image classifier | Adversarial examples via a hosted API | modest | $25.60 | $0.95 | **10 / 256** | $1,967 | 53.8 % | An undocumented, centrally-controlled burn rate sits on top |
| **SN28 SayGM** | [`SN028-GM.md`](SN028-GM.md) | Confidential LLM-API marketplace | A TEE-attested inference endpoint | **yes** — serving rig | $25.60 | $5.81 | **45 / 256** | $9,131 | 49.5 % | Paid on *revenue share*, not model quality |
| **SN29 hoτfloaτ** | [`SN029-COLDINT.md`](SN029-COLDINT.md) | *(file says coldint — dormant)* | — | — | $0.13 | $0.71 | 1 / 256 | $2,108 | 18.0 % | ⚠️ **Chain name is now `hoτfloaτ`.** File's "100 % burns" is stale — 1 UID takes the pool |
| **SN34 BitMind / GAS** | [`SN034-BITMIND.md`](SN034-BITMIND.md) | Detectors **vs** generators, both on-chain | A detector or a generator model | **yes** | $128.00 | $3.11 | **140 / 256** | $7,718 ← **owner** | **93.0 %** | Winner-take-all per modality per round; **owner takes 93 %** |
| **SN35 Cartha (0xMarkets)** | [`SN035-CARTHA.md`](SN035-CARTHA.md) | Liquidity mining — **not AI** | USDC locked into a vault | **none** | $25.60 | $0.62 | 2 / 256 | $1,602 | 18.0 % | Pure capital deployment; six figures for a principal vault |
| **SN36 automata** | [`SN036-LEOMA.md`](SN036-LEOMA.md) | *(file says Leoma video-gen)* | — | — | $256.00 | $1.35 | 1 / 3 | $3,991 ← **owner** | 59.0 % | ⚠️ **Netuid 36 was re-registered ~16 d ago as `automata`.** 3 UIDs, `alpha_out = 0`. The Leoma file describes a subnet that no longer exists |
| **SN38 ChronoLLM** | [`SN038-CHRONOLLM.md`](SN038-CHRONOLLM.md) | Chronologically-consistent LLMs, one per year | A trained model per target year | **yes** | $189.44 | $1.98 | 1 / 256 | $5,836 | 52.6 % | README's "winner takes all" is stale — it's exponential decay across ranks |
| **SN43 Graphite** | [`SN043-GRAPHITE.md`](SN043-GRAPHITE.md) | Graph/routing (TSP) **+ portfolio trading** | TSP solver, and/or a copy-trade leader | **none** | $25.60 | $1.20 | **13 / 256** | $2,911 | 58.9 % | README covers ~60 % of what actually pays |
| **SN47 Feval** | [`SN047-FEVAL.md`](SN047-FEVAL.md) | Verifiable LoRA evaluation | Adapter + published rollouts | 24–48 GB | $12.80 | $0.84 | 1 / 142 | $2,488 ← **owner** | **72.9 %** | Published repo ≠ live network; owner takes the whole miner pool |
| **SN53 Engy** | [`SN053-ENGY.md`](SN053-ENGY.md) | Verified LLM inference for real buyers | GPU serving capacity | **yes** — ref 4× RTX 4090 | $0.13 | $7.31 | **68 / 256** | $8,539 | 34.9 % | Earnings ∝ paid tokens served; 99 %+ acceptance SLA |
| **SN54 MIID (Yanez)** | [`SN054-MIID.md`](SN054-MIID.md) | Identity-preserving face variations for KYC | Synthetic image variations | **yes** — ~16 GB | $0.13 | $1.12 | **97 / 256** | $1,160 | 64.6 % | Both public sources describe a phase that has already passed |
| **SN58 Greevils** | [`SN058-GREEVILS.md`](SN058-GREEVILS.md) | TEE algo-trading on Hyperliquid | Agent in a TDX VM, or a plain HL account | none (VM ~$145/mo) | $25.60 | $2.42 | 1 / 256 | $7,152 | 41.2 % | Sole earner holds no on-chain commitment; zero `gva1` approvals |
| **SN60 Bitsec** | [`SN060-BITSEC.md`](SN060-BITSEC.md) | AI agents finding real smart-contract vulns | A security agent | modest | $0.13 | $1.24 | 2 / 256 | $1,824 | 38.5 % | Payout ranks by *agent*, not hotkey — one miner takes the pool |
| **SN61 RedTeam** | [`SN061-REDTEAM.md`](SN061-REDTEAM.md) | Bots that beat bot-detection, and vice versa | A Dockerised bot | modest | $12.89 | $3.27 | **45 / 256** | $316 | 18.0 % | Docs contradict themselves on which challenges are live |
| **SN71 Leadpoet** | [`SN071-LEADPOET.md`](SN071-LEADPOET.md) | B2B sales-lead generation | Qualified decision-maker leads | **none** — CPU + APIs | $0.25 | $1.19 | **52 / 256** | $2,827 ← **owner** | **73.3 %** | Live logic runs in a hosted AWS-Nitro TEE; the axon path is deprecated |
| **SN76 Phylax** | [`SN076-PHYLAX.md`](SN076-PHYLAX.md) | AI supply-chain security attestation | One Python file (`agent_main`) | **none** | $25.60 | $0.39 | **21 / 256** | $230 | 37.3 % | Your track's rounds have to actually be scheduled |
| **SN78 UMI (ex-Vocence)** | [`SN078-UMI.md`](SN078-UMI.md) | ASL→English translation *(pre-activation)* | HTTP translator service | yes, 24–80 GB | $0.13 | $1.41 | 1 / 256 | $4,167 | 47.2 % | Weights type-level disabled; the 0.10 quality floor is unproven |
| **SN79 MVTRX** | [`SN079-MVTRX.md`](SN079-MVTRX.md) | Agent-based market simulation | Always-on trading bot | **none** | $27.86 | $1.59 | **217 / 256** | $428 | 59.0 % | Below half the median score you earn exactly zero |
| **SN80 OpenRoboto** | [`SN080-OPENROBOTO.md`](SN080-OPENROBOTO.md) | Fine-tune π0.5 VLA robotics | A HuggingFace checkpoint | **yes** — A100-class | $0.13 | $3.91 | 5 / 256 | $8,240 ← **owner** | 52.2 % | ~$19/attempt; most of the pool sits on the operator's UID 0 |
| **SN82 Compelle** | [`SN082-COMPELLE.md`](SN082-COMPELLE.md) | Adversarial LLM debate | A prompt, committed on chain | **none** | $0.13 | $0.82 | 1 / 64 | $2,428 | 28.8 % | Incumbent-protected winner-take-all on only 64 slots |
| **SN90 KubeTEE** | [`SN090-KUBETEE.md`](SN090-KUBETEE.md) | DePIN confidential compute | A TDX GPU cluster | 8-node TDX datacenter | $0.13 | $7.42 | 2 / 97 | $15,843 ← **owner** | **65.1 %** | Onboarding is operator-gated — you cannot join |
| **SN92 MicroTensor** | [`SN092-MICROTENSOR.md`](SN092-MICROTENSOR.md) | Certified inference systems | ONNX/GGUF artifact + 128-byte pointer | training only (RTX 3090+) | $25.60 | $0.86 | **9 / 256** | $645 | 43.3 % | Docs name the wrong paying track |
| **SN101 Tag101** | [`SN101-TAG101.md`](SN101-TAG101.md) | Semantic tagging of X posts | 3 topic tags per post | **none** — CPU + LLM API | $0.17 | $1.13 | **245 / 256** | $2,994 ← **owner** | **78.5 %** | Consensus-scored: you're paid for predicting the crowd |
| **SN103 Capcomp** | [`SN103-CAPCOMP.md`](SN103-CAPCOMP.md) | LoRA composition | One JSON merge recipe | 32–48 GB | $256.00 | $3.34 | 4 / 120 | $8,881 | 55.4 % | Dethrone margin sits ~24× below measurement noise |
| **SN105 Beam** | [`SN105-BEAM.md`](SN105-BEAM.md) | Decentralised bandwidth / CDN | Nothing — you *run infra* | **none** | $0.13 | $1.81 | **202 / 256** | $91 | 53.7 % | Bandwidth + public IP + 24/7 uptime; only Qualified orchestrators earn |
| **SN107 Minos** | [`SN107-MINOS.md`](SN107-MINOS.md) | Genomic variant calling | Variant-caller hyperparameter config | **none** | $253.44 | $13.88 | **21 / 100** | $33,167 ← **owner** | **83.7 %** | Field has filled since the file was written — 1 → 21 earners |
| **SN114 SOMA** | [`SN114-SOMA.md`](SN114-SOMA.md) | Token-efficient SWE coding agents | Python compression module | **none** | $64.00 | $3.36 | **18 / 256** | $6,453 | 39.5 % | You pay inference; re-qualify every 2 weeks |
| **SN118 Ditto** | [`SN118-DITTO.md`](SN118-DITTO.md) | Agent-memory harness | Rust harness in Docker | **none** — CPU, 8 GB | $0.13 | $2.34 | 5 / 256 | $4,505 | 43.8 % | Crown locked near 0.97; ~$5/submission |
| **SN120 Affine** | [`SN120-AFFINE.md`](SN120-AFFINE.md) | Incentivised RL / reasoning competition | Fine-tuned LLM referenced on chain | **yes** | $264.50 | $13.65 | 5 / 256 | $8,059 | 58.5 % | Champion-vs-challenger, winner-take-all |
| **SN121 Sundae Bar** | [`SN121-SUNDAEBAR.md`](SN121-SUNDAEBAR.md) | AI "skill" evaluation for one commercial agent | A rubric-scored artifact | modest | $0.13 | $1.18 | 2 / 256 | $2,095 ← **owner** | **72.7 %** | Majority-burn: #1 gets only ~20 % of weight |
| **SN123 MANTIS** | [`SN123-MANTIS.md`](SN123-MANTIS.md) | Financial signal prediction | Encrypted prediction embeddings | **none** | $38.40 | $0.67 | **249 / 256** | $694 ← **owner** | 54.8 % | Copy-proof by construction; proportional payout |
| **SN124 Swarm** | [`SN124-SWARM.md`](SN124-SWARM.md) | Autonomous drone-pilot AI (RL) | A trained flight policy | **none** to run | $128.00 | $2.95 | **25 / 256** | $930 | 48.1 % | **One shot per hotkey** — benchmark all 1,100 seeds first |
| **SN127 Astrid** | [`SN127-ASTRID.md`](SN127-ASTRID.md) | AI trading competitions (live agents) | A live trading agent | **none** | $0.13 | $0.74 | 1 / 256 | $2,181 ← **owner** | **82.6 %** | Winner-take-few — top 3 by PnL per competition |

---

## 2 · What it takes to mine

The dimensions the [README](README.md) uses to compare, extended to all 35.

| Subnet | Core skill | Reward shape | Copy-resistant? | You pay inference? | Hardware barrier |
|---|---|---|---|---|---|
| **SN14 Cacheon** | Inference-serving optimisation / DevOps | Winner-take-most | Image is public once pushed | No — you serve | **High** — serving rig for a 72B model |
| **SN18 Zeus** | ML forecasting (weather) | Pure ML competition | Model stays yours | No | Training GPU; serving is CPU |
| **SN26 Perturb** | Adversarial ML / CV | Per-challenge, plus an opaque burn | Attacks are one-shot | No | Low–moderate |
| **SN28 SayGM** | Cloud / TEE operations | **Revenue-proportional** | N/A — it's capacity | No — buyers pay you | **High** — TEE-attested serving |
| **SN29 hoτfloaτ** | *unverified — file is stale* | 1 UID currently takes the pool | ? | ? | ? |
| **SN34 BitMind / GAS** | Deepfake detection **or** generation | Winner-take-all per modality per round | Model stays yours | No | **High** — GPU both sides |
| **SN35 Cartha** | **None — capital only** | Proportional to locked USDC | N/A | No | **Zero compute**; six-figure USDC for a principal vault |
| **SN36 automata** | *unknown — brand-new subnet* | Owner holds 100 % | ? | ? | ? |
| **SN38 ChronoLLM** | LLM pre/post-training | Exponential decay across ranks | Model stays yours | No | **High** — training GPU |
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
| **SN101 Tag101** | Data pipelines | Winner-take-most, consensus-scored | Tags are commodity | **Yes** — LLM API | **Low** — CPU |
| **SN103 Capcomp** | LoRA composition search | 10 ranks, rank 1 takes 90 % | Recipes published after payout | No | One 32–48 GB GPU |
| **SN105 Beam** | DevOps / bandwidth | **Tiered** — top 10 % take ~80 % | N/A — it's capacity | No — you pay **egress** | **Bandwidth + public IP + 24/7** |
| **SN107 Minos** | Bioinformatics / tuning | Winner-take-most | Configs are simple | No | **Low** — CPU, ≥60 GB disk |
| **SN114 SOMA** | Agent + token-efficiency engineering | Per-element tournament | Duplicate-adjacent | **Yes** — OpenRouter/DeepSeek | **Low** — dev machine |
| **SN118 Ditto** | Rust + information retrieval | **King-of-the-hill** (65–90 % to champion) | **Yes** — duplicate detection | No | **Low** — CPU, 8 GB |
| **SN120 Affine** | RL / reasoning fine-tuning | Winner-take-all champion | Model referenced on chain | No | **High** — training GPU |
| **SN121 Sundae Bar** | Rubric writing / agent design | **Majority-burn** — #1 gets ~20 % | Artifacts are scored, not held | Likely | Low–moderate |
| **SN123 MANTIS** | Quant / ML finance | **Proportional** (salience) | **Yes** — L2 split + uniqueness | No | **Lowest** — small VPS |
| **SN124 Swarm** | RL / robotics / control | King-of-the-hill, **last 5 champions paid** | Policy stays yours | No | **None** to run |
| **SN127 Astrid** | Quant trading | **Winner-take-few** — top 3 by PnL | Live agent, private | Maybe — LLM calls | **None** — Arena API |

---

## 3 · What the snapshot says

**Only nine of the 35 have a genuinely contested field** (≥ 9 UIDs earning):
**SN123 MANTIS** (249), **SN101 Tag101** (245), **SN79 MVTRX** (217),
**SN105 Beam** (202), **SN34 BitMind** (140), **SN54 MIID** (97), **SN53 Engy**
(68), **SN28 SayGM** (45) and **SN61 RedTeam** (45). Then a long tail of
**SN18 Zeus** (35), **SN124 Swarm** (25), **SN76 Phylax** (21), **SN107 Minos**
(21), **SN114 SOMA** (18), **SN43 Graphite** (13), **SN26 Perturb** (10) and
**SN92 MicroTensor** (9).

**Eight subnets pay exactly one UID:** SN29, SN36, SN38, SN47, SN58, SN78, SN82,
SN127. On **SN34, SN36, SN47, SN71, SN80, SN90, SN101, SN107, SN121 and SN127**
the single top earner **is the owner's own hotkey**.

**Owner capture spans 18.0 % to 93.0 %.** The floor (18 %) is just the protocol
cut with nothing added — SN29, SN35 and SN61 sit there. The ceiling is
**SN34 BitMind at 93.0 %**, followed by SN107 Minos (83.7 %), SN127 Astrid
(82.6 %) and SN101 Tag101 (78.5 %).

**Alpha price spans 55×** — from SN76 Phylax at $0.39 to SN107 Minos at $13.88
and SN120 Affine at $13.65.

**Entry cost spans 2,000×** — from $0.13 (many) to $264.50 (SN120 Affine),
$256 (SN18, SN36, SN103) and $253 (SN107).

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
**SN101 Tag101**, **SN118 Ditto**, **SN123 MANTIS**, **SN107 Minos** — all CPU-only.
Note SN101 and SN114 make you pay for inference.

**If you are a strong ML engineer with a training rig:** **SN92 MicroTensor**
(9 seats, geometric curve where rank 8 still earns ~⅓ of rank 1, and the
frontier is fully public), **SN103 Capcomp**, **SN120 Affine**, **SN18 Zeus**.

**Avoid or verify first:** **SN36 automata** (brand-new, owner holds everything),
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
