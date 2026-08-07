# Bittensor Subnet Analysis

Deep-dive summaries of eight Bittensor subnets, one file each. *Snapshot as of 2026-07-31 — all figures (prices, champions, active miners, weights) change over time; re-verify before committing capital.*

| # | Subnet | File | Domain |
|---|---|---|---|
| 53 | **Engy** ⚡ | [subnet-53-engy.md](subnet-53-engy.md) | Verified LLM inference (GPU serving) |
| 105 | **Beam** 📡 | [beam-sn105.md](beam-sn105.md) | Decentralized bandwidth / CDN (+ deployment record) |
| 107 | **Minos** 🧬 | [subnet-107-minos.md](subnet-107-minos.md) | Genomic variant calling |
| 114 | **SOMA** 🧩 | [subnet-114-soma.md](subnet-114-soma.md) | Token-efficient SWE coding agents |
| 118 | **Ditto** 🧠 | [subnet-118-ditto.md](subnet-118-ditto.md) | Agent-memory harness |
| 123 | **MANTIS** 📈 | [subnet-123-mantis.md](subnet-123-mantis.md) | Financial signal prediction |
| 124 | **Swarm** 🚁 | [subnet-124-swarm.md](subnet-124-swarm.md) | Autonomous drone-pilot AI (RL) |
| 127 | **Astrid** 📊 | [subnet-127-astrid.md](subnet-127-astrid.md) | AI trading competitions (live agents) |

---

## At-a-glance comparison

| Dimension | Beam (105) | Minos (107) | SOMA (114) | Ditto (118) | MANTIS (123) |
|---|---|---|---|---|---|
| **What you submit** | Nothing — you *run infra* (orchestrator + workers) | Variant-caller hyperparameter config | Python compression module for a coding agent | Rust memory harness (Docker) | Encrypted prediction embeddings |
| **Core skill** | DevOps / bandwidth / uptime | Bioinformatics / tuning | Agent + token-efficiency engineering | Rust + information retrieval | Quant / ML finance |
| **Reward shape** | **Tiered** (top 10% → 80%) | Winner-take-most (87% burn, top 10%) | Winner-take-per-element tournament | **King-of-the-hill** (champion 65–90%) | **Proportional** (salience) |
| **Copy-resistant?** | N/A — it's capacity, not a model | Configs are simple; skill = tuning | Duplicate-adjacent | Yes — duplicate detection | **Yes — L2 split + uniqueness** |
| **GPU needed?** | No | No | No | No | No |
| **You pay inference?** | No — you pay **bandwidth/egress** | No | **Yes (OpenRouter/DeepSeek)** | No | No |
| **Hardware barrier** | **Bandwidth + public IP + 24/7 uptime** | Low (CPU, ≥60 GB disk) | Low (dev machine) | Low (CPU, 8 GB) | **Lowest** (small VPS, uptime) |
| **Money barrier** | Reg + **bandwidth/server cost** | Registration + compute | Reg + **per-inference cost** | Reg + **~$5/submission** | Registration only |
| **Live & crowded?** | **Live, ~1,200 miners** | ~1 active miner (open) | Active dev, small field | **Live & saturated (crown locked)** | Active quant field |
| **Best fit for** | Infra/ops operators w/ cheap bandwidth | Genomics/tuning specialists | Agent engineers w/ budget | Rust/IR engineers (early movers) | Quants with data infra |

---

## How to choose

- **If you're an infra/ops operator (not ML):** **Beam** — a different game entirely (decentralized CDN). No model, no submission; you run an orchestrator + workers and compete on **throughput + reliability + 24/7 uptime**. Needs a publicly-reachable port and a bandwidth budget. Already deployed here (UID 223) — see [beam-sn105.md](beam-sn105.md).
- **Lowest barrier to *try*:** MANTIS or Minos (no per-inference cost, no submission fee).
- **If you're a quant / ML-finance person:** **MANTIS** — highest skill ceiling, proportional reward (don't need #1), copy-proof. Or **Astrid (127)** if you'd rather run a *live* trading agent than submit signals — but it's **winner-take-few** (top-3 by PnL per competition), so you must out-trade rivals. No GPU; needs the Arena API + maybe an LLM. See [subnet-127-astrid.md](subnet-127-astrid.md).
- **If you're a Rust / retrieval engineer:** **Ditto** — pure skill race, but the crown is locked at ~0.97; realistically aim for tail ranks (~0.93+) and prioritize originality + a clean Docker build.
- **If you're strong at agent/context engineering and can fund inference:** **SOMA** — but it's a moving target (re-qualify every 2 weeks).
- **If you have bioinformatics depth:** **Minos** — open field today; position for Phase 2 (custom algorithms).
- **If you're a GPU / infra operator with real hardware:** **Engy** — run verifiable LLM inference for real paying buyers; earnings ∝ paid tokens you serve, gated by a 99%+ acceptance SLA + a TOPLOC honesty proof. Needs a multi-GPU rig (ref: 4× RTX 4090); validating is CPU-only. See [subnet-53-engy.md](subnet-53-engy.md).
- **If you're an RL / robotics / control engineer:** **Swarm** — train a drone-pilot policy on depth+state → flight commands. King-of-the-Hill pays the **last 5 champions per mission** (breakthroughs keep paying), no GPU or inference cost to *run*, but **one shot per hotkey** — benchmark the full 1,100 seeds locally first. See [subnet-124-swarm.md](subnet-124-swarm.md).

## Universal cautions
1. **Verify economics live** — burn %, alpha price, champion scores, and active-miner counts all move.
2. **Winner-take-most vs proportional matters** — Ditto/Minos reward ~only the top; MANTIS/SOMA spread wider.
3. **Copy-resistance is real** on Ditto and MANTIS — forking the top miner earns nothing.
4. **Read the incentive code, not the marketing** — SOMA's live task ≠ its website; Ditto's README "not yet live" was stale vs. a live leaderboard.
