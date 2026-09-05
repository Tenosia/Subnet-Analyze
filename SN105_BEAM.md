# Beam — Subnet 105 (SN105)

**Decentralized bandwidth / data-transfer network (a competitive, verifiable CDN).** Repo: `Beam-Network/beam` · netuid **105** (finney).

> **Archetype: infrastructure / raw resource — NOT AI.** No GPU, no models. You compete on **network throughput, reliability, and uptime.** The miner is the **Orchestrator** (managing a worker pool); emissions are **steeply tiered** (top ~10% take ~80%).

## Goal
An open coordination layer for **bandwidth** — moving real client data between storage endpoints (S3, GCS, Cloudflare R2, HTTP) and turning bandwidth into a *measurable, verifiable, incentivized commodity*. Targets the fact that cloud egress is expensive (**$0.08–0.12/GB**), routing isn't programmable, and idle bandwidth can't be monetized. Miners earn by moving bytes fast and reliably, with cryptographic proof (Merkle / Proof-of-Bandwidth).

## The 5 roles
| Role | Who | Does |
|---|---|---|
| **BeamCore** | the Beam team (central, `beamcore.b1m.ai`) | assigns work, tracks, scores (PRISM), materializes weights |
| **Orchestrator** | **YOU (the miner)** | holds the SN105 UID, manages a worker pool, receives task batches over NATS, routes to workers — **earns the $TAO emissions** |
| **Worker** | you (your pool) | moves the actual bytes between storage endpoints; paid by the orchestrator off-chain |
| **Validators** | Bittensor validators | read BeamCore epoch summaries and `set_weights` on-chain |
| **Clients** | data owners | submit transfer jobs |

**Key point: the miner that earns emissions is the Orchestrator.** You run an orchestrator **plus your own workers** under it, and you're scored at the **pool level** (aggregate of all your workers).

## What a miner does (orchestrator)
From `docs/orchestrator.md`:
1. Register an orchestrator hotkey on **netuid 105** (`btcli subnet register --netuid 105`).
2. Run the orchestrator (`neurons/orchestrator/main.py`) — connects to BeamCore NATS, advertises a **publicly reachable worker gateway** (port 8000), sets `READY=true`.
3. Run **workers** (`neurons/worker/worker.py`) connected to your gateway — they execute chunk transfers using short-lived signed URLs and report `task_result` receipts.
4. Pass a readiness/qualification phase, then complete production transfers reliably to rank into a high emission tier.

## Scoring — PRISM
From `guide/prism.md`:
```
performance   = 0.40·throughput + 0.60·reliability      ← reliability weighted MORE
readiness     = (ready & connected) × active_time_ratio  ← your uptime %
PRISM_final   = performance × readiness × penalty         (all clamped 0–1)
```
- **Throughput** = provider-verified bandwidth, **1-hour half-life** (recent sustained throughput matters most).
- **Reliability** = task success vs failures, **24-hour half-life** — **60% of performance**, so reliability beats raw speed.
- **Readiness** = % of the window you were connected + ready. Intermittent downtime multiplies everything down.
- PRISM shapes **routing** — a higher score gets you **more task assignments** → more chances to complete production work → more reward. It's a positive feedback loop.

## Rewards / weights (tiered)
- Emissions are **steeply tiered**: the **top ~10% of orchestrators capture ~80%** of emissions. Being merely "okay" earns little; you need to be near the top of the pool ranking.
- Validators translate BeamCore's PRISM-based epoch summaries into on-chain weights.

## Hardware / device
**No GPU.** The resource is **network bandwidth + uptime + reliability**:

| | Orchestrator (miner) | Worker (does the moving) |
|---|---|---|
| **Compute** | Light (coordination) | Light (I/O bound) |
| **Network** | Stable outbound to BeamCore/Bittensor/storage; **public IP/domain + open port 8000** for the worker gateway | **High upload AND download bandwidth** — the core competitive resource |
| **Uptime** | Must stay connected + ready | Must stay available |

Winning setup = **cheap, high-bandwidth, high-uptime servers** (ideally unmetered / high egress cap), not GPUs. Aggregate **Gb/s across your worker fleet** drives throughput.

## Third-party / dependencies
- **BeamCore** connection over **NATS** (message bus for task batches / receipts).
- Storage endpoints your transfers touch: **S3, GCS, Cloudflare R2, HTTP** (via short-lived signed URLs — you don't hold long-term creds).
- Bittensor wallet + `btcli`.
- A **public IP or domain + open port 8000** for the worker gateway.

## How to win
1. **Maximize aggregate bandwidth** — run many high-upload/high-download workers; more Gb/s = more throughput = better routing.
2. **Prioritize reliability over raw speed** — it's 60% of performance with a 24h half-life; a failed transfer hurts more than a slightly slower successful one.
3. **Near-perfect uptime** — readiness multiplies the whole score; downtime is punished twice (readiness + lost throughput recency).
4. **Use unmetered / high-egress-cap hosting** — egress cost is your main expense; cheap bandwidth is the moat.
5. **Scale the worker fleet** to push into the **top 10%** tier (where ~80% of emissions live) — mid-pack earns little.

## Key files / commands
- `neurons/orchestrator/main.py` — the orchestrator (the miner) — **what earns emissions**.
- `neurons/worker/worker.py` — a worker (moves bytes).
- `docs/orchestrator.md`, `docs/worker.md` — operator guides.
- `guide/prism.md` — the PRISM scoring spec.

```bash
btcli subnet register --netuid 105 --subtensor.network finney \
  --wallet.name miner --wallet.hotkey default
# run orchestrator (advertise public gateway :8000, READY=true), then attach workers
python neurons/orchestrator/main.py    # + one or more neurons/worker/worker.py
```

## Verdict
**Hard for a different reason — it's a capital/infrastructure game, not a skill game.** No AI to build, but you need **real, cheap, reliable bandwidth at scale** and near-perfect uptime to reach the top-10% tier where the rewards concentrate. Best fit if you have access to unmetered high-bandwidth servers; poor fit if you only have a single small VPS.
