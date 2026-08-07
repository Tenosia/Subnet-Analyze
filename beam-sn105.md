# Bittensor Subnet 105 — Beam (Decentralized Bandwidth Network)

> Analysis + deployment record. Sources: `github.com/Beam-Network/beam`, `github.com/Beam-Network/beam-core-public`, https://b1m.ai, https://subnetalpha.ai/subnet/beam, and live testing on this VPS.
> Last updated: 2026-07-31.

---

## Table of Contents
1. [What Beam Is](#1-what-beam-is)
2. [Architecture & Roles](#2-architecture--roles)
3. [Scoring — PRISM](#3-scoring--prism)
4. [Rewards & Tiers](#4-rewards--tiers)
5. [Graduation (Qualifying → Qualified)](#5-graduation-qualifying--qualified)
6. [Hardware / VPS Requirements](#6-hardware--vps-requirements)
7. [Our Deployment (Vast.ai)](#7-our-deployment-vastai)
8. [The Big Gotcha: `orchestrator_not_routable`](#8-the-big-gotcha-orchestrator_not_routable)
9. [Current Status — UID 223](#9-current-status--uid-223)
10. [Operations (persistence, monitoring)](#10-operations-persistence-monitoring)
11. [Scaling & Tier A Strategy](#11-scaling--tier-a-strategy)
12. [Reference Card](#12-reference-card)

---

## 1. What Beam Is

Beam is an **open coordination layer for bandwidth** — effectively a competitive, decentralized CDN. It moves real client data between storage endpoints (S3, GCS, Cloudflare R2, HTTP) and turns bandwidth into a measurable, verifiable, incentivized commodity.

- **Problem it targets:** cloud egress is expensive ($0.08–0.12/GB), routing isn't programmable, idle bandwidth can't be monetized.
- **It is NOT an AI/ML subnet.** No GPU, no models. You compete on **network throughput, reliability, and uptime.**
- **You earn** by moving bytes fast and reliably, with cryptographic proof (Merkle / Proof-of-Bandwidth).
- Economics (subnetalpha, approx): ~2,952 alpha/day emission, ~0.167 TAO registration/node, ~1,200+ active miners, alpha ≈ $2.20.

---

## 2. Architecture & Roles

| Role | Who runs it | What it does |
|------|-------------|--------------|
| **Clients** | data owners | request transfers (move A → B) |
| **BeamCore** | Beam team (central, `beamcore.b1m.ai`) | assigns work, tracks, scores (PRISM), materializes weights |
| **Orchestrator** | **YOU (the miner)** | holds the SN105 UID, manages a worker pool, receives task batches over NATS, routes to workers → **earns emissions** |
| **Worker** | you (your pool) | moves the actual bytes between storage endpoints; paid off-chain by the orchestrator |
| **Validators** | Bittensor validators | read BeamCore epoch summaries and `set_weights` on-chain |

**Key point:** the miner that earns is the **Orchestrator**. You run one orchestrator + one or more workers under it. You're scored at the **pool level** (aggregate of all your workers).

**Data path:** workers transfer bytes **directly** between source/destination storage via short-lived signed URLs (`signed_url_v1` = direct multipart PUT). The orchestrator's worker gateway is a **control channel** (task offers + results over WebSocket) — bulk data does **not** flow through it. This is why a NAT'd host can work: only the control connection needs to be reachable; heavy transfer is worker↔storage (outbound).

---

## 3. Scoring — PRISM

From `beam-core-public/packages/ops-scheduler/src/prism/scoring.ts`:

```
performance = 0.40 · throughput + 0.60 · reliability     ← reliability weighted MORE
reliability = success_rate  (verified / (verified + max(failures, reassignments)), 24h half-life)
throughput  = provider-verified bandwidth, 1-hour half-life (recent sustained speed)
readiness   = % of window ready + NATS-connected   (0 if disconnected/not-ready)
penalty     = 1 − Σ(integrity_mismatch·1.0 + sybil·0.5 + fraud·0.1, 48h half-life)

PRISM_final = performance × readiness × penalty     (all clamped to [0,1])
```

**Lever priority (highest impact first):**
1. **Reliability (60% of performance)** — keep task success ~100%. Every failure/reassignment hurts (24h half-life).
2. **Zero penalties** — `integrity_chunk_mismatch` has coeff **1.0**; one corrupted delivery can wipe your score.
3. **Readiness = uptime** — it's a *multiplier*; any downtime scales the whole score down and stops task flow.
4. **Throughput (40%)** — high sustained bandwidth; 1h half-life rewards recent, continuous speed.

> Note: `throughput` is fleet-normalized to ~[0.2, 1.0]. Because it has a 1-hour half-life, **sparse tasks make VERIFIED BW decay between transfers** — this is normal in the Qualifying phase and is NOT a fault.

---

## 4. Rewards & Tiers

From `beam-core-public/.../epoch-summary-math.ts`:

```
base_raw = task_done_count × penalty_multiplier      (rolling 7-day window)

Tier A = top 10%   → 80% of emissions
Tier B = next 30%  → 15%
Tier C = remaining → 5%
```

- Within each tier, split proportionally by `base_raw`. **Winner-take-most.**
- Routing share ∝ PRISM score → higher PRISM → more tasks routed → higher `task_done_count` → higher tier. It compounds.
- **Owner-group fairness:** orchestrators under the same owner are grouped; share is based on the group's *average* PRISM. → **Running many orchestrators does NOT multiply rewards. Scale workers, never orchestrators.**
- **Weekly seasonal reset:** every Sunday 00:00 UTC, routing score resets to neutral 0.5 (qualified status persists). Automatic — no config change; just stay online to rebuild quickly.
- If there are **no client transfers** in a window, 90% of emission **burns to UID 0**.

---

## 5. Graduation (Qualifying → Qualified)

**Only Qualified orchestrators earn.** New orchestrators start in the **Qualifying** pool doing calibration transfers (assigned round-robin / fairly — extra capacity does NOT get you more calibration tasks).

```
confidence = min(1, tasks/120) × success_rate × maturity     → graduate at ≥ 0.9
maturity   = 0.8 + 0.2 × min(1, age_days / 7)
```

| Requirement | Target |
|-------------|--------|
| Verified calibration tasks | ~120 |
| Success rate | ~100% |
| Node age (maturity) | ~7 days (min ~3.5 days to reach maturity 0.9) |

**Time to first rewards: ~4–7 days** of reliable, continuous operation. PRISM/rank do **not** gate graduation — only `CONF.SCORE` does.

---

## 6. Hardware / VPS Requirements

**No GPU. The resource is network bandwidth + uptime + reliability.**

| | Orchestrator (miner) | Worker (moves bytes) |
|---|---|---|
| GPU | ❌ none | ❌ none |
| Python | 3.10–3.12 | 3.10–3.12 |
| Network | stable outbound to BeamCore/Bittensor/storage; **publicly reachable gateway port** | high, stable **upload AND download** bandwidth (the core competitive resource) |
| Disk | modest | scratch space for transfer chunks |
| Uptime | 24/7 (direct score multiplier) | high |

**Recommended starting VPS:** 4 vCPU / 8 GB / NVMe / **≥1 Gbps unmetered**, real public IP where **public port == listen port** (e.g. Hetzner, Contabo, OVH). Tier A realistically wants more aggregate bandwidth.

> ⚠️ **Avoid NAT'd GPU rental containers (Vast/RunPod) for production** — they meter bandwidth (Beam's product), have interruptible uptime, and only expose remapped ephemeral ports. See §7–8 for how we made Vast work anyway.

---

## 7. Our Deployment (Vast.ai)

Deployed on a Vast.ai container: **32 cores, 377 GB RAM, RTX 4090 (unused by Beam), 10 Gbps NIC**, public IP `69.176.92.125`.

**Measured bandwidth:** ~3.2 Gbps download (well-peered), ~199 Mbit/s single-stream upload, **~1.8 Gbps aggregate parallel upload**. Per-transfer speed in practice ≈ 75–160 Mbps (upload-leg limited).

**The Vast NAT problem:** container is behind Docker NAT (`172.17.0.2`); inbound ports are only the ones Vast mapped at creation, and **external port ≠ internal port**. Beam advertises `url = http://EXTERNAL_IP:API_PORT` and needs that to be the *public* port.

**Solution — socat bridge** (make the advertised port equal the public mapped port):
```bash
# Vast maps container:10100 -> public 69.176.92.125:56569
socat TCP-LISTEN:10100,fork,reuseaddr TCP:127.0.0.1:56569
```
```dotenv
# neurons/orchestrator/.env
EXTERNAL_IP=69.176.92.125
API_PORT=56569                                   # advertises the PUBLIC port
ORCHESTRATOR_WORKER_GATEWAY_URL=http://69.176.92.125:56569
BEAMCORE_ORCHESTRATOR_API_KEY=<from registration>   # see §8
```
Flow: `external → 69.176.92.125:56569 (Vast host) → container:10100 → socat → 127.0.0.1:56569 (orchestrator)`. Verified externally reachable.

> Optional local patch: `orchestrator.py` runs `start_polling()` in the background so uvicorn serves HTTP in ~1s instead of ~50s. Harmless; overwritten by `git pull`.

---

## 8. The Big Gotcha: `orchestrator_not_routable`

**This cost hours of debugging. The error name is misleading.**

`orchestrator_not_routable` does **NOT** mean your network is unreachable. Confirmed by packet capture: **BeamCore never probes your port** — it decides server-side. It means **BeamCore has no orchestrator RECORD for your hotkey.**

There are **TWO separate registrations**, both required:
1. **On-chain** (subnet): `btcli subnet register --netuid 105` → gives you a UID. *Necessary but not sufficient.*
2. **BeamCore record** (the missing step): a **signed HTTP POST** that creates your orchestrator record and issues an API key:

```python
# signature over "{hotkey}:{fee_percentage}", signed with the hotkey; hex with 0x prefix
POST https://beamcore.b1m.ai/orchestrators/register
{ "hotkey": "5F...", "signature": "0x...", "fee_percentage": 0,
  "name": "...", "region": "us-east", "url": "http://<ip>:<port>", "max_workers": 1000 }
# → returns { orchestrator_id, api_key, "orchestrator registered" }
```
The `api_key` is shown **only once**. Set it as `BEAMCORE_ORCHESTRATOR_API_KEY` in the orchestrator `.env`, then the NATS `register` succeeds (`status=registered`).

**Ruled out during debugging (all were red herrings):** port reachability (Jina confirmed reachable), startup race, on-chain registration alone, on-chain axon (all 256 neurons have `0.0.0.0`), source-IP mismatch, port value. **The only fix was the BeamCore record.**

Prerequisite note: `403 hotkey is not registered on this subnet` means step 1 (on-chain) is missing.

---

## 9. Current Status — UID 223

| Field | Value |
|-------|-------|
| Orchestrator UID | **223** (hotkey `5H49dCMAxvPifM...`) |
| Worker UID | **59** (hotkey `5FuzaM5aaCAM...`) |
| orchestrator_id | `8fff9bcf-5153-4977-8d91-6756a7312cf9` |
| Registered (BeamCore) | 2026-07-28 |
| Status / Ready | active / true |
| Tier | Qualifying (graduating) |
| PRISM | ~0.75–0.80 (climbing) |
| Success % | 100% |
| Readiness % | ~99.8% |
| Verified BW | ~75–160 (throughput-limited; decays between sparse tasks) |
| Tasks / CONF | ~52 tasks, CONF ~0.36 and climbing toward 0.9 |
| Est. graduation | ~Aug 1–2 (needs ~120 tasks + ~3.5–7 days age) |

**Observed lessons:** during Qualifying, **rank is noisy and cosmetic** (field is tightly clustered); VERIFIED BW/PRISM dip between sparse tasks (1h half-life) — neither affects graduation. Only `CONF.SCORE` matters until Qualified.

---

## 10. Operations (persistence, monitoring)

Vast containers have **no systemd** (PID 1 = bash), so we use detached scripts:

| Script | Purpose |
|--------|---------|
| `/home/Project/beam/beam-run.sh` | supervisor: socat + orchestrator + worker, each in a 5s auto-restart loop |
| `/home/Project/beam/beam-monitor.sh` | watchdog: relaunches if the supervisor dies or the orchestrator hangs (3× failed `/health`) |
| `/home/Project/beam/onstart.sh` | Vast On-start script: relaunches supervisor + watchdog after an instance reboot |
| `/home/Project/beam/beam-stop.sh` | stops everything |

```bash
# start (detached, survives session logout)
setsid nohup bash /home/Project/beam/beam-run.sh    >/dev/null 2>&1 &
setsid nohup bash /home/Project/beam/beam-monitor.sh >/dev/null 2>&1 &

# health checks
curl http://localhost:56569/health
curl -s https://beamcore.b1m.ai/orchestrators/5H49dCMAxvPifMFtCeJfyCQqwAyomVJb9zbBcJRbREeGpk6B
tail -f /home/Project/beam/logs/{orchestrator,worker,monitor}.log
```

**⚠️ Must-do:** set the **Vast "On-start Script"** field to `bash /home/Project/beam/onstart.sh` so a Vast reboot self-recovers (the one failure mode the scripts can't catch on their own).

**Health signals that actually matter:** `ready=True`, fresh `last_seen`, `SUCCESS %` ~100%, no disconnects. BW/PRISM/rank dips are noise.

**Co-hosting:** other workloads (cargo/Rust, Ollama, PyTorch, Fire-Vision GPU miner) run fine alongside — they use CPU/GPU, Beam uses network. With 32 cores at ~16% load, no contention observed, transfers unaffected. `nice -n 10 ionice -c3 <cmd>` any heavy compile to protect orchestrator responsiveness.

---

## 11. Scaling & Tier A Strategy

**When:** only *after* graduation. During Qualifying, calibration is round-robin — more workers do NOT help.

**How to earn more (post-graduation):** rewards ∝ completed tasks. You increase completed tasks by (a) raising PRISM so BeamCore routes you more, and (b) adding capacity to complete them.

**Worker count:** bandwidth-driven, not a fixed number.
```
this box: ~1.8 Gbps aggregate upload ÷ ~0.1 Gbps/worker ≈ up to ~15 workers to saturate
```
Start with 3–4, add 2 at a time, watch VERIFIED BW rise + SUCCESS stay 100%. Stop when you saturate ~1.8 Gbps, or success drops, or you clear all routed tasks. Practical target on one box: **~4–8 workers**.

**Tier A feasibility:**
- Your ops are already Tier-A grade (100% reliability, ~99.8% readiness, zero penalties).
- Bottleneck is **throughput** (Vast upload ceiling ~1.8 Gbps; leaders show ~180–193 verified BW vs your ~100).
- **One Vast box realistically → Tier B (15%).** Tier A → add **workers on additional high-bandwidth boxes**, all pointing at your ONE orchestrator's public gateway (`http://69.176.92.125:56569`) — multiplies aggregate throughput without breaking owner-group fairness.
- **Decide with numbers:** Vast bills bandwidth; extra boxes cost money. Measure emissions per tier before chasing the top 10% — Tier B on cheap infra may beat fighting for A.

**Golden rule:** scale **workers**, never orchestrators (owner-group fairness cancels extra orchestrators).

---

## 12. Reference Card

**Wallets (this deployment)**
```
coldkey:  beam
hotkeys:  orchestrator (UID 223), worker1 (UID 59)
path:     ~/.bittensor/wallets/beam
```

**Credentials (back these up — API key shown only once)**
```
BEAMCORE_ORCHESTRATOR_API_KEY = b1m_cufwDEU23CjsB2x3e0SC6A_ChysLsYji   (in orchestrator/.env)
orchestrator_id               = 8fff9bcf-5153-4977-8d91-6756a7312cf9
```

**Endpoints**
```
CORE_SERVER_URL   = https://beamcore.b1m.ai
ORCH_GATEWAY_URL  = tls://orch-gateway.b1m.ai:4222      (NATS control)
Dashboard         = https://data.b1m.ai/weights
Advertised gateway= http://69.176.92.125:56569          (Vast public map of container:10100)
```

**Vast port mappings (container → public @ 69.176.92.125)** — 8 total, fixed at instance creation
```
22 → 40373 (SSH)      1111 → 22579 (Portal)   6006 → 10469 (TB)    8080 → 35476 (Jupyter)
8384 → 45303 (Sync)   10100 → 56569 (BEAM)    10200 → 57754 (free) 72299 → 18681 (INVALID >65535)
```

**One-time setup recap**
```bash
# 1. wallets + on-chain registration
btcli wallet new-coldkey --wallet.name beam
btcli wallet new-hotkey  --wallet.name beam --wallet.hotkey orchestrator
btcli wallet new-hotkey  --wallet.name beam --wallet.hotkey worker1
btcli subnet register --netuid 105 --network finney --wallet.name beam --wallet.hotkey orchestrator
btcli subnet register --netuid 105 --network finney --wallet.name beam --wallet.hotkey worker1
# 2. BeamCore record (THE step that clears not_routable) — signed POST /orchestrators/register
# 3. set BEAMCORE_ORCHESTRATOR_API_KEY in orchestrator/.env
# 4. socat bridge + run supervisor
```

**Golden rules**
- On-chain registration ≠ BeamCore registration — you need **both**.
- `not_routable` = missing BeamCore record, NOT a network problem.
- Scale **workers**, never orchestrators.
- During Qualifying: only `CONF.SCORE` matters; ignore BW/PRISM/rank noise.
- Reliability + readiness + zero penalties > raw bandwidth.
- Keep it online 24/7; the Sunday reset is automatic.
