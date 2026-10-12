# Subnet Comparison Table

**41 Bittensor subnets, one snapshot.** Every economic figure below was read
live from finney at **block 9,181,379 (2026-09-30)**, TAO ≈ $304.89, so the rows are
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
| **SN14 Cacheon** | [`SN014-CACHEON.md`](SN014-CACHEON.md) | Inference-server speed race | Docker container serving a pinned 72B model | **yes** — serving rig | $0.15 | $2.70 | **16 / 256** | $2,333 | 45.7 % | Fastest *correct* server wins; two-pass correctness gate |
| **SN18 Zeus** | [`SN018-ZEUS.md`](SN018-ZEUS.md) | Weather / climate forecasting | ERA5 global-grid predictions | training yes; serving no | $304.89 | $1.24 | **23 / 257** | $12,554 ← **owner** | 46.1 % | Ships a random-number placeholder — you build the whole model |
| **SN20 Witness** | [`SN020-WITNESS.md`](SN020-WITNESS.md) | Agentic video understanding — metered observation | Structured reconstruction from budgeted frame/audio/transcript calls | not specified (inference may be remote) | $60.98 | $0.70 | 1 / 256 | $2,057 | 52.1 % | **Research preview, not publicly launched**; owner's UID takes the whole pool |
| **SN25 UR** | [`SN025-UR.md`](SN025-UR.md) | Decentralized VPN / privacy network | Routable IP breadth — carry ingress+egress traffic | **none** | $0.15 | $2.07 | 1 / 256 | $7,305 ← **owner** | 67.0 % | Mechanism is testnet-first and **not live on mainnet**; owner's UID takes the whole pool |
| **SN26 Perturb** | [`SN026-PERTURB.md`](SN026-PERTURB.md) | Adversarial red-teaming of an image classifier | Adversarial examples via a hosted API | modest | $30.49 | $0.73 | 5 / 256 | $3,622 ← **owner** | 87.0 % | An undocumented, centrally-controlled burn rate sits on top |
| **SN28 SayGM** | [`SN028-GM.md`](SN028-GM.md) | Confidential LLM-API marketplace | A TEE-attested inference endpoint | **yes** — serving rig | $30.49 | $6.23 | **71 / 256** | $14,257 ← **owner** | 49.8 % | Paid on *revenue share*, not model quality |
| **SN29 hoτfloaτ** | [`SN029-COLDINT.md`](SN029-COLDINT.md) | *(file says coldint — dormant)* | — | — | $0.15 | $0.85 | 1 / 256 | $2,521 | 18.0 % | ⚠️ **Chain name is now `hoτfloaτ`.** File's "100 % burns" is stale — 1 UID takes the pool |
| **SN34 BitMind / GAS** | [`SN034-BITMIND.md`](SN034-BITMIND.md) | Detectors **vs** generators, both on-chain | A detector or a generator model | **yes** | $152.44 | $3.62 | **106 / 256** | $3,866 | 57.4 % | Winner-take-all per modality per round; **owner takes 93 %** |
| **SN35 `logic`** | [`SN035-CARTHA.md`](SN035-CARTHA.md) | *(file says Cartha/0xMarkets — re-registered)* | — | — | $304.89 | $0.98 | 1 / 5 | $2,904 | 47.6 % | ⚠️ **Re-registered 18.7 d ago as `logic`.** 4 UIDs, 1 earner — the Cartha vault is gone |
| **SN36 Epago** | [`SN036-LEOMA.md`](SN036-LEOMA.md) | *(file is 2 occupants stale — now `Epago`)* | — | — | $30.49 | $1.19 | 1 / 29 | $3,507 | 42.8 % | ⚠️ **Renamed twice: `Leoma`→`automata`→`Epago`.** 3 UIDs, 1 earner; now emitting |
| **SN38 ChronoLLM** | [`SN038-CHRONOLLM.md`](SN038-CHRONOLLM.md) | Chronologically-consistent LLMs, one per year | A trained model per target year | **yes** | $225.62 | $5.84 | **10 / 256** | $35,900 | 52.7 % | README's "winner takes all" is stale — it's exponential decay across ranks |
| **SN40 Ralph** | [`SN040-RALPH.md`](SN040-RALPH.md) | Open model compression — Qwen3-8B into bit tiers | A compressed GGUF + a commit-reveal hash | offline compression only | $301.84 | $0.80 | 1 / 256 | $2,362 | 44.2 % | **Every published crown-holder earns zero**; one uncrowned UID takes the whole pool |
| **SN43 Graphite** | [`SN043-GRAPHITE.md`](SN043-GRAPHITE.md) | Graph/routing (TSP) **+ portfolio trading** | TSP solver, and/or a copy-trade leader | **none** | $30.49 | $1.21 | 6 / 256 | $2,815 ← **owner** | 90.6 % | README covers ~60 % of what actually pays |
| **SN47 GPUForge** | [`SN047-FEVAL.md`](SN047-FEVAL.md) | *(file says Feval — netuid repurposed)* | — | — | $15.24 | $0.62 | 1 / 158 | $1,824 | 42.9 % | ⚠️ **Netuid renamed to `GPUForge`** — verifiable GPU training, a different project entirely |
| **SN53 Engy** | [`SN053-ENGY.md`](SN053-ENGY.md) | Verified LLM inference for real buyers | GPU serving capacity | **yes** — ref 4× RTX 4090 | $0.17 | $10.61 | **14 / 256** | $6,845 | 34.0 % | Earnings ∝ paid tokens served; 99 %+ acceptance SLA |
| **SN54 MIID (Yanez)** | [`SN054-MIID.md`](SN054-MIID.md) | Identity-preserving face variations for KYC | Synthetic image variations | **yes** — ~16 GB | $0.15 | $1.78 | **131 / 256** | $5,971 ← **owner** | 64.7 % | Both public sources describe a phase that has already passed |
| **SN58 `dippy-speach`** | [`SN058-GREEVILS.md`](SN058-GREEVILS.md) | *(file says Greevils — netuid repurposed)* | — | — | $30.49 | $1.92 | 1 / 256 | $8,889 ← **owner** | 82.3 % | ⚠️ **Netuid renamed to `dippy-speach`**, identity blanked. The Greevils subnet is gone |
| **SN60 Bitsec** | [`SN060-BITSEC.md`](SN060-BITSEC.md) | AI agents finding real smart-contract vulns | A security agent | modest | $0.15 | $1.25 | 3 / 256 | $1,851 | 32.3 % | Payout ranks by *agent*, not hotkey — one miner takes the pool |
| **SN61 RedTeam** | [`SN061-REDTEAM.md`](SN061-REDTEAM.md) | Bots that beat bot-detection, and vice versa | A Dockerised bot | modest | $12.36 | $3.21 | **95 / 256** | $204 | 18.0 % | Docs contradict themselves on which challenges are live |
| **SN71 Leadpoet** | [`SN071-LEADPOET.md`](SN071-LEADPOET.md) | B2B sales-lead generation | Qualified decision-maker leads | **none** — CPU + APIs | $0.15 | $1.16 | 2 / 256 | $4,594 ← **owner** | 72.8 % | Live logic runs in a hosted AWS-Nitro TEE; the axon path is deprecated |
| **SN76 Ormas** | [`SN076-ORMAS.md`](SN076-ORMAS.md) | Fixed-price bids for verified coding outcomes | A git branch that makes the client's own test pass | **none** | $0.15 | $1.86 | 1 / 135 | $8,211 ← **owner** | 79.3 % | `alpha_out_emission = 0` — the subnet emits nothing to anyone |
| **SN78 UMI (ex-Vocence)** | [`SN078-UMI.md`](SN078-UMI.md) | ASL→English translation *(pre-activation)* | HTTP translator service | yes, 24–80 GB | $228.67 | $1.05 | **107 / 256** | $1,487 ← **owner** | 37.6 % | Weights type-level disabled; the 0.10 quality floor is unproven |
| **SN79 MVTRX** | [`SN079-MVTRX.md`](SN079-MVTRX.md) | Agent-based market simulation | Always-on trading bot | **none** | $13.87 | $0.95 | **242 / 256** | $102 | 59.0 % | Below half the median score you earn exactly zero |
| **SN80 OpenRoboto** | [`SN080-OPENROBOTO.md`](SN080-OPENROBOTO.md) | Fine-tune π0.5 VLA robotics | A HuggingFace checkpoint | **yes** — A100-class | $0.20 | $8.12 | 8 / 256 | $7,920 | 23.1 % | ~$19/attempt; most of the pool sits on the operator's UID 0 |
| **SN82 `uruz`** | [`SN082-COMPELLE.md`](SN082-COMPELLE.md) | *(file says Compelle — re-registered 3.6 d ago)* | — | — | $549.17 | $1.36 | 1 / 2 | $0 ← **owner** | 59.0 % | ⚠️ **Re-registered 3.6 d ago as `uruz`**, no identity, `alpha_out_emission = 0` |
| **SN90 KubeTEE** | [`SN090-KUBETEE.md`](SN090-KUBETEE.md) | DePIN confidential compute | A TDX GPU cluster | 8-node TDX datacenter | $0.15 | $7.22 | 3 / 99 | $11,274 | 37.0 % | Onboarding is operator-gated — you cannot join |
| **SN92 `Available`** | [`SN092-MICROTENSOR.md`](SN092-MICROTENSOR.md) | *(file says MicroTensor — identity wiped)* | — | — | $30.49 | $0.45 | 1 / 256 | $1,315 | 43.7 % | ⚠️ **Identity wiped to `Available`** — every field blank, 1 earner. Effectively abandoned |
| **SN93 Bitcast** | [`SN093-BITCAST.md`](SN093-BITCAST.md) | Creator marketing — YouTube + X, paid on verified attention | An axon serving creators' YouTube OAuth tokens | **none** | $1.52 | $5.82 | 2 / 256 | $10,226 ← **owner** | 84.3 % | Owner's hotkey **is** the burn UID and takes ~64 % of weight; emission field contradicts the weight vector |
| **SN101 Tag101** | [`SN101-TAG101.md`](SN101-TAG101.md) | Semantic tagging of X posts | 3 topic tags per post | **none** — CPU + LLM API | $0.94 | $1.15 | **229 / 256** | $5,119 ← **owner** | 79.9 % | Consensus-scored: you're paid for predicting the crowd |
| **SN103 Capcomp** | [`SN103-CAPCOMP.md`](SN103-CAPCOMP.md) | LoRA composition | One JSON merge recipe | 32–48 GB | $304.89 | $0.34 | 1 / 128 | $1,013 | 56.9 % | Dethrone margin sits ~24× below measurement noise |
| **SN105 Beam** | [`SN105-BEAM.md`](SN105-BEAM.md) | Decentralised bandwidth / CDN | Nothing — you *run infra* | **none** | $0.15 | $1.98 | **222 / 256** | $100 | 55.0 % | Bandwidth + public IP + 24/7 uptime; only Qualified orchestrators earn |
| **SN107 Minos** | [`SN107-MINOS.md`](SN107-MINOS.md) | Genomic variant calling | Variant-caller hyperparameter config | **none** | $301.84 | $12.47 | **20 / 100** | $29,303 | 47.4 % | Field has filled since the file was written — 1 → 21 earners |
| **SN108 ChipForge** | [`SN108-CHIPFORGE.md`](SN108-CHIPFORGE.md) | **Silicon design** — RISC-V cores in Verilog | A Verilog/SystemVerilog RV32 CPU core, zipped | **none** (8 cores / 24 GB) | $152.44 | $1.35 | 1 / 62 | $0 ← **owner** | 59.0 % | Docs say winner-takes-all; the shipped validator default pays the winner **10 %** |
| **SN114 SOMA** | [`SN114-SOMA.md`](SN114-SOMA.md) | Token-efficient SWE coding agents | Python compression module | **none** | $76.22 | $5.85 | **132 / 256** | $8,608 | 40.4 % | You pay inference; re-qualify every 2 weeks |
| **SN118 Ditto** | [`SN118-DITTO.md`](SN118-DITTO.md) | Agent-memory harness | Rust harness in Docker | **none** — CPU, 8 GB | $0.15 | $2.16 | 1 / 256 | $10,130 ← **owner** | 83.3 % | Crown locked near 0.97; ~$5/submission |
| **SN119 CapabilityForge Next** | [`SN119-CAPABILITYFORGE.md`](SN119-CAPABILITYFORGE.md) | Training-data improvement for learning AI *(no implementation)* | **Undefined** — no format, no submission path | unknown | $0.15 | $0.68 | 1 / 256 | $2,135 ← **owner** | 61.5 % | **The repo is a 32-line README.** No code, 0 commitments; owner takes the whole pool |
| **SN120 Affine** | [`SN120-AFFINE.md`](SN120-AFFINE.md) | Incentivised RL / reasoning competition | Fine-tuned LLM referenced on chain | **yes** | $222.51 | $14.12 | 1 / 256 | $82,627 ← **owner** | 99.3 % | Champion-vs-challenger, winner-take-all |
| **SN121 Sundae Bar** | [`SN121-SUNDAEBAR.md`](SN121-SUNDAEBAR.md) | AI "skill" evaluation for one commercial agent | A rubric-scored artifact | modest | $0.17 | $1.19 | 1 / 256 | $6,100 ← **owner** | 89.2 % | Majority-burn: #1 gets only ~20 % of weight |
| **SN123 MANTIS** | [`SN123-MANTIS.md`](SN123-MANTIS.md) | Financial signal prediction | Encrypted prediction embeddings | **none** | $45.73 | $0.69 | **247 / 256** | $2,279 ← **owner** | 63.5 % | Copy-proof by construction; proportional payout |
| **SN124 Swarm** | [`SN124-SWARM.md`](SN124-SWARM.md) | Autonomous drone-pilot AI (RL) | A trained flight policy | **none** to run | $152.44 | $2.92 | **25 / 256** | $919 | 48.9 % | **One shot per hotkey** — benchmark all 1,100 seeds first |
| **SN127 Astrid** | [`SN127-ASTRID.md`](SN127-ASTRID.md) | AI trading competitions (live agents) | A live trading agent | **none** | $0.15 | $0.72 | 4 / 256 | $2,734 ← **owner** | 70.9 % | Winner-take-few — top 3 by PnL per competition |

---

## 2 · What it takes to mine

The dimensions the [README](README.md) uses to compare, extended to all 40.

| Subnet | Core skill | Reward shape | Copy-resistant? | You pay inference? | Hardware barrier |
|---|---|---|---|---|---|
| **SN14 Cacheon** | Inference-serving optimisation / DevOps | Winner-take-most | Image is public once pushed | No — you serve | **High** — serving rig for a 72B model |
| **SN18 Zeus** | ML forecasting (weather) | Pure ML competition | Model stays yours | No | Training GPU; serving is CPU |
| **SN20 Witness** | Video understanding + tool-use policy | Quality × efficiency, gated at `0.8 × best` | **Yes** — identical reconstructions split the score | Your own inference | **None locally** — full harness runs GPU-free; competitive inference needs one |
| **SN25 UR** | Network operations / IP-address procurement | Two tiers: pooled tail (Merkle claim) + top-~200 head paid natively | **Yes** — shared prefixes split `1/claim(h)` | No | **None** — the scarce asset is *diverse routable prefixes*, not hardware |
| **SN26 Perturb** | Adversarial ML / CV | Per-challenge, plus an opaque burn | Attacks are one-shot | No | Low–moderate |
| **SN28 SayGM** | Cloud / TEE operations | **Revenue-proportional** | N/A — it's capacity | No — buyers pay you | **High** — TEE-attested serving |
| **SN29 hoτfloaτ** | *unverified — file is stale* | 1 UID currently takes the pool | ? | ? | ? |
| **SN34 BitMind / GAS** | Deepfake detection **or** generation | Winner-take-all per modality per round | Model stays yours | No | **High** — GPU both sides |
| **SN35 `logic`** | *unverified — netuid re-registered* | Proportional to locked USDC | N/A | No | **Zero compute**; six-figure USDC for a principal vault |
| **SN36 Epago** | *unknown — brand-new subnet* | Owner holds 100 % | ? | ? | ? |
| **SN38 ChronoLLM** | LLM pre/post-training | Exponential decay across ranks | Model stays yours | No | **High** — training GPU |
| **SN40 Ralph** | Quantization / PTQ research | Per tier: king 80 %, best challenger 20 %, rest nothing | **Yes** — a copy ties at zero margin | No | **Offline GPU** to quantize an 8B model; no serving |
| **SN43 Graphite** | Combinatorial optimisation **+** quant | Three-way split | Solutions are per-task | No | Low |
| **SN47 `GPUForge`** | *unverified — netuid repurposed* | 3 seats (62.5 / 25 / 12.5 %) | Rollouts are published | No | One 24–48 GB GPU |
| **SN53 Engy** | GPU operations | **∝ paid tokens served** | N/A — it's capacity | No — buyers pay | **High** — multi-GPU rig |
| **SN54 MIID** | Generative CV | Per-cycle scoring | Model stays yours | No | ~16 GB GPU |
| **SN58 `dippy-speach`** | *unverified — netuid repurposed* | Pairwise tournament, dollar-capped human lane | Strategy must be open-sourced to earn | No | None — but **~$25k trading capital** |
| **SN60 Bitsec** | Security engineering (smart contracts) | One agent currently takes the pool | Findings are per-codebase | Likely | Low–moderate |
| **SN61 RedTeam** | Web automation / anti-detection | Decaying per-challenge points | Docker images are submitted | No | Low–moderate |
| **SN71 Leadpoet** | Data pipelines + sales intelligence | Per-request service | Leads are verifiable | **Yes** — API costs | **Low** — CPU + APIs |
| **SN76 Ormas** | Autonomous coding agents | **Firm-price auction** — paid your exact ask on acceptance, nothing on a miss | **Yes** — the client's own test is the spec, and validators re-run it | **Yes** — every attempt, and misses are unpaid | **None** |
| **SN78 UMI** | ML / sign-language translation | *(not yet active)* | Model stays yours | No | 24–80 GB GPU |
| **SN79 MVTRX** | Quant trading | **Proportional**, with a half-median floor | Strategy stays yours | No | **Low** — small VPS |
| **SN80 OpenRoboto** | ML / robotics | Winner-take-most | Checkpoints are **public** | No | **High** — A100-class |
| **SN82 `uruz`** | *unverified — re-registered* | Incumbent-protected winner-take-all | Strategies are **public** | No | **None** |
| **SN90 KubeTEE** | Datacenter operations | Proportional to GPU capacity | N/A — it's capacity | No | **Extreme** — 8-node TDX cluster |
| **SN92 `Available`** | *unverified — identity wiped* | Hypervolume frontier, 8 paid ranks | ε-collapse punishes copies | No | Training GPU only |
| **SN93 Bitcast** | Creator-network operations / BD | **USD-bounded** — pays only for verified attention; burn UID absorbs the rest | Attention is per-video and verified | No | **None** — a $5 VPS; the cost is recruiting creators |
| **SN101 Tag101** | Data pipelines | Winner-take-most, consensus-scored | Tags are commodity | **Yes** — LLM API | **Low** — CPU |
| **SN103 Capcomp** | LoRA composition search | 10 ranks, rank 1 takes 90 % | Recipes published after payout | No | One 32–48 GB GPU |
| **SN105 Beam** | DevOps / bandwidth | **Tiered** — top 10 % take ~80 % | N/A — it's capacity | No — you pay **egress** | **Bandwidth + public IP + 24/7** |
| **SN107 Minos** | Bioinformatics / tuning | Winner-take-most | Configs are simple | No | **Low** — CPU, ≥60 GB disk |
| **SN108 ChipForge** | **RTL / digital hardware design** | Winner-take-all, 48 h then beat your own best | **Yes** — SPIKE-verified functional score | No | **High** — 8–16 cores, 24–32 GB, full EDA toolchain |
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

**16 of the 41 have a genuinely contested field** (≥ 9 UIDs earning):
**SN123 MANTIS** (247), **SN79 MVTRX** (242), **SN101 Tag101** (229), **SN105 Beam** (222),
**SN114 SOMA** (132), **SN54 MIID** (131), **SN78 UMI** (107), **SN34 BitMind** (106),
**SN61 RedTeam** (95), **SN28 SayGM** (71), **SN124 Swarm** (25), **SN18 Zeus** (23),
**SN107 Minos** (20), **SN14 Cacheon** (16), **SN53 Engy** (14), **SN38 ChronoLLM** (10).

**17 pay exactly one UID:** SN20, SN25, SN29, SN35, SN36, SN40, SN47, SN58, SN76, SN82,
SN92, SN103, SN108, SN118, SN119, SN120, SN121.
On **20** the single top earner **is the owner's own hotkey**: SN18, SN25, SN26, SN28, SN43,
SN54, SN58, SN71, SN76, SN78, SN82, SN93, SN101, SN108, SN118, SN119, SN120, SN121, SN123, SN127.

**⚠️ Five netuids have been renamed or re-registered in the 16 days since the last
snapshot** — SN35, SN47, SN58, SN82 and SN92. Their files now describe subnets that no
longer exist at those netuids. See §4. Combined with SN29, SN36 and SN76, **eight of the
41 documents here are describing a different project than the one on chain.** Netuid
churn is the single most common failure mode in this folder.

**Two subnets are emitting nothing at all:** **SN108 ChipForge** (registered 9.7 d ago) and
**SN82 `uruz`** (re-registered 3.6 d ago). Both show `alpha_out_emission = 0` and
`moving_price = 0` — a dTAO subnet earns emission in proportion to its *moving* price, which
starts at zero for a fresh registration. **SN76 Ormas was in exactly this state on 2026-09-14
and is now emitting normally at $8,211/day to its owner UID**, so the zero is usually
temporary rather than terminal.

**Owner capture spans 18.0 % to 99.3 %.** **SN120 Affine** is now the starkest in the set at
**99.3 %** — the owner holds effectively all incentive and all dividends. Then
**SN43 Graphite** (90.6 %), **SN121 Sundae Bar** (89.2 %), **SN26 Perturb** (87.0 %) and
**SN93 Bitcast** (84.3 %). Only **SN29 hoτfloaτ** and **SN61 RedTeam** sit at the bare 18 %
protocol floor.

**SN108 ChipForge has the most expensive entry in the set by two orders of magnitude** —
**τ0.5 ≈ $152**, against a τ0.0005 ≈ $0.15 floor on most subnets.

---

## 4 · ⚠️ Staleness found while re-checking

Re-reading every file against live chain state. **Eight netuids no longer host the project
their document describes:**

| File | What it says | What the chain says now |
|---|---|---|
| [`SN082-COMPELLE.md`](SN082-COMPELLE.md) | Compelle — adversarial LLM debate, 64 slots | **Re-registered 3.6 days ago (block 9,155,260) as `uruz`.** No identity set at all, `alpha_out_emission = 0`. **The Compelle subnet is gone.** |
| [`SN047-FEVAL.md`](SN047-FEVAL.md) | Feval — verifiable LoRA evaluation | Netuid renamed in place to **`GPUForge`** — *"a Bittensor subnet for verifiable GPU training"*, repo `forgenet47/gpuforge`. **Different project, same netuid.** |
| [`SN058-GREEVILS.md`](SN058-GREEVILS.md) | Greevils — TEE algo-trading on Hyperliquid | Chain name is now **`dippy-speach`** and every identity field is blank. **Re-analysis needed.** |
| [`SN092-MICROTENSOR.md`](SN092-MICROTENSOR.md) | MicroTensor — certified inference, 8–9 paid seats | Chain name is **`Available`** with **every identity field wiped** — no repo, no URL, no description — and **1 earner**. Effectively abandoned. |
| [`SN035-CARTHA.md`](SN035-CARTHA.md) | Cartha / 0xMarkets — liquidity mining | **Re-registered 18.7 days ago as `logic`.** 4 UIDs, 1 earner. **The vault is gone.** |
| [`SN076-PHYLAX-HISTORICAL.md`](SN076-PHYLAX-HISTORICAL.md) | Phylax — AI supply-chain attestation | Netuid 76 is **`Ormas`** (already archived; see [`SN076-ORMAS.md`](SN076-ORMAS.md)). **Ormas has since switched emission on** — owner UID now takes **$8,211/day**, owner capture **79.3 %**. |
| [`SN029-COLDINT.md`](SN029-COLDINT.md) | *"coldint. DORMANT. 100 % of weight burns."* | Chain name is **`hoτfloaτ`**; one UID (not the owner) takes the pool at the bare 18 % owner floor. **The burn claim is stale.** |
| [`SN036-LEOMA.md`](SN036-LEOMA.md) | Leoma — AI video generation, king-of-the-hill | Netuid 36 is **`Epago`**. **The Leoma subnet no longer exists at this netuid.** |

Non-rename staleness:

| File | What it says | What the chain says now |
|---|---|---|
| [`SN078-UMI.md`](SN078-UMI.md) | *"weights not yet active"* | **107 UIDs earning.** The incentive is live — re-analysis needed. |
| [`SN107-MINOS.md`](SN107-MINOS.md) | *"~1 active miner (open field)"* | **20 UIDs earning**, top earner **$29,846/day** — the largest single payout in the set. |
| [`SN120-AFFINE.md`](SN120-AFFINE.md) | Incentivised RL competition | **Owner capture 99.3 %**, 1 earner. Verify before committing anything. |

---

## 5 · How to choose

**If you want a field you can actually place in** — ≥ 20 earners and a
proportional or tiered payout rather than winner-take-all:
**SN123 MANTIS** (247 earners, proportional, copy-proof, lowest hardware bar),
**SN79 MVTRX** (242, proportional above a median floor, no GPU, free testnet),
**SN105 Beam** (222, tiered, but you need bandwidth and 24/7 uptime),
**SN61 RedTeam** (95 earners at the bare 18 % owner floor — the best owner-capture
number in the set alongside SN29),
**SN124 Swarm** (25, and it pays the **last five** champions, so a breakthrough keeps earning).

**If you have GPUs and want to sell capacity rather than compete on models:**
**SN28 SayGM** (71 earners, revenue share) or **SN53 Engy** (14 earners, paid ∝ tokens
actually served). Both are operations problems, not ML problems.

**If you have no GPU and no capital:** **SN101 Tag101**, **SN123 MANTIS**,
**SN107 Minos**, **SN93 Bitcast**, **SN76 Ormas** — all CPU-only.
Note SN101 and SN114 make you pay for inference, and SN76 makes you pay for every
attempt whether or not it is accepted.

**If you are a hardware / RTL engineer:** **SN108 ChipForge** is the only subnet here that
wants Verilog rather than Python, and with 62 UIDs and **zero qualifying submissions** the
crown is currently uncontested. But it emits nothing today, entry is **$152**, and the
shipped validator default pays the winner **10 %** while routing 90 % to the owner's UID.
Read [`SN108-CHIPFORGE.md`](SN108-CHIPFORGE.md) §3.3 before spending anything.

**If you are a strong ML engineer with a training rig:** **SN103 Capcomp**, **SN18 Zeus**
(23 earners), **SN38 ChronoLLM**. *(SN92 MicroTensor is no longer a candidate — its
identity has been wiped.)*

**Avoid or verify first:** **SN82 `uruz`**, **SN47 `GPUForge`**, **SN58 `dippy-speach`**,
**SN92 `Available`**, **SN35 `logic`** (all five renamed or re-registered — the documents
here describe projects that have left), **SN120 Affine** (99.3 % owner capture),
**SN43 Graphite** (90.6 %), **SN121 Sundae Bar** (89.2 %), **SN90 KubeTEE** (you cannot
join — onboarding is operator-gated), **SN108 ChipForge** (emits nothing yet, $152 entry).

---

## 6 · Universal cautions

1. **Verify economics live before committing capital.** Alpha price, earner
   counts, burn share and champion scores all move — several moved materially in
   the days between the individual files and this snapshot.
2. **Winner-take-most vs proportional is the single biggest structural choice.**
   Seventeen of these subnets pay exactly one UID.
3. **Check whether the top earner is the owner.** On twenty of the 41 it is.
4. **Read the incentive code, not the marketing.** Every file in this folder that
   was written from source found the public description stale or wrong somewhere —
   SN36, SN38, SN43, SN47, SN54, SN60, SN61, SN90, SN92 and SN121 all carry an
   explicit accuracy caveat.
5. **A netuid is not a permanent identity.** SN36 was re-registered as a different
   subnet entirely; SN29 and SN78 were renamed under new operators.

---

*Generated from live finney state at block 8,998,579 on 2026-09-05. Regenerate
whenever a new subnet analysis is added to this folder.*
