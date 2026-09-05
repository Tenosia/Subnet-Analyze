# Subnet 124 — Swarm 🚁

> **"The open arena where AI learns to fly."** A competitive benchmark where miners train autonomous **drone-pilot AI** and compete across thousands of fresh procedurally-generated worlds. Deterministic physics sim, public leaderboard, King-of-the-Hill rewards. Built around **search & rescue**; pilots transfer to real hardware (the open-source **Langostino** drone).

- Site: https://swarm124.com · Leaderboard: https://swarm124.com/benchmark
- Repo: https://github.com/swarm-subnet/swarm (v5.0.0, MIT) · Local: `/home/Project/swarm`
- Market: https://subnetalpha.ai/subnet/swarm/ · Discord: https://discord.gg/8dPqPDw7GC
- *Snapshot as of 2026-08-03 — figures change.*

---

## 1. Purpose & goal
Drones are ready as hardware; the bottleneck is the **AI that flies them**, built today in closed silos where no one can prove whose is best. Swarm is the open arena that settles it: train a pilot, submit it, and it competes on a public leaderboard across worlds it has never seen — **"no private test sets, no memorizing, no shortcuts."** Rewards are paid automatically by Bittensor (SN124).

## 2. Five missions (challenge families)
Each family is its own competition — own champion lineage, own emission slice. **One hotkey = one model in one family.**

| Family | ID | Task | Drones | Maps | Slice |
|---|---|---|---|---|---|
| **Interceptor** | `cf_interceptor` | Chase & catch a fleeing (validator-flown) drone | 1 vs target | Open | **30%** |
| **Swarm Autopilot** | `cf_swarm_autopilot` | Land a team fast, no collisions | 2–8 | City/Open/Mountain/Village/Forest | 20% |
| **Swarm SAR** | `cf_swarm_sar` | Team sweep to find the victim together | 2–8 | same | 20% |
| **Autopilot** | `cf_autopilot` | Cross world, find pad, land clean | 1 | + Warehouse | 15% |
| **Search & Rescue** | `cf_search_and_rescue` | Find a lost person, hold steady hover above | 1 | + Warehouse | 15% |

Worlds: City, Ski Village, Mountains, Warehouse, Forest (4 seasons), Open terrain — **1,100 brand-new worlds per family every week**.

## 3. What miners do
Mining is **lightweight** (commit a GitHub URL, go offline — validators do the work). The effort is *training the model*.

**Interface** (Search & Rescue example — each family has its own contract):
- **Observation:** `depth` (256×256×1, 0.5–30 m), `rgb` (256×256×3, on-demand, **max 40/episode**), `state` (position, velocity, orientation, action history, search-area direction).
- **Action:** `[dir_x, dir_y, dir_z, speed, yaw, rgb_request]`. Max **3.0 m/s**, yaw ≤ 180°/s, **50 Hz**, **60 s** episodes. No map/GPS/obstacle list.
- **Agent:** implement `DroneFlightController.act(observation) → action` in `drone_agent.py` (SB3/PyTorch/ONNX/custom).
- **Limits:** ≤ **50 MiB uncompressed**; no binaries (`.exe/.so/.dll/.sh/.bat/.pyc`), no symlinks/path-traversal; pip packages must be on the **Docker whitelist**.

**Submission flow:**
```
swarm doctor → train → swarm model test → swarm model package --family-id cf_x
→ swarm model verify → swarm benchmark → swarm repo package → swarm repo verify
→ push public GitHub repo → python neurons/miner.py --netuid 124 --github_url ...
```
Repo must contain the **byte-exact template README** (SHA-256), `submission_manifest.json`, and `artifacts/<family_id>/submission.zip`. Front-run protection: **private repo → commit on-chain → wait finalize → make public**.

## 4. Scoring logic
Per-seed reward (most families):
```
score = 0.45 × success + 0.45 × time + 0.10 × safety
```
| Term | Weight | Meaning |
|---|---|---|
| Success | 0.45 | 1 if objective met, else 0 |
| Time | 0.45 | 1 within target time, → 0 at 60 s horizon |
| Safety | 0.10 | 1 if clearance ≥ 1.0 m (0.6 m Forest); 0 at ≤ 0.2 m; linear |

- **Interceptor** overrides to **0.5 success / 0.5 time** (no safety).
- Non-success failures = **0.01** participation; errors/illegit = 0.
- **Model score = mean over all 1,100 seeds** (steady skill > lucky runs).
- SAR "CONFIRMED": speed < 1 m/s, ≤ 2 m horizontal, 2–4 m above victim, outside a 0.8 m no-touch sphere — held continuously **2.0 s**.

## 5. How to win — King of the Hill (5-king window)
Rewards are **not** winner-take-all. Each family's slice is split across its **last 5 champions**.

**Get crowned** — beat the champion by a **dynamic floor** (shrinks as scores climb):
| Families | floor (champ ≤ 0.5) | floor min (champ → 1.0) |
|---|---|---|
| Autopilot, Swarm Autopilot, Interceptor | +0.015 | +0.005 |
| Search & Rescue, Swarm SAR | +0.02 | +0.007 |

**Slice split among the 5 kings:**
```
ladder = 0.7 ^ rank          # rank 0 (newest crown) = full weight
gain   = log((1−prev)/(1−score))   # headroom closed; 0 if no improvement
bonus  = 1 + 0.3 × min(gain, 1.0)  # bigger jump → up to +30%
share  = ladder × bonus / Σ(window)
```
- Champion earns most; each older seat keeps **70%** of the one above (0.49 @ rank2, ~0.24 @ rank4); 6th crowning ages you out.
- A **big jump keeps paying through 4 more dethronings**; a copycat barely clearing the floor earns ~nothing.
- **Re-crown with a NEW hotkey** to reclaim rank-0 (old hotkey's slot is locked).

**Strategy:** pick a family (Interceptor = biggest 30% but hardest; Autopilot/SAR = simpler first crown) → train strong RL policy → **benchmark full 1,100 seeds locally, hard** (one shot per hotkey) → crown with a *big* jump → keep repo public/reachable → iterate via fresh hotkeys.

## 6. Evaluation timing & flow
- **Epoch = 7 days, rollover Monday 16:00 UTC.** 1,100 fresh worlds/family/epoch (each validator generates its own via `SystemRandom()`; seeds published after).
- Chain scanner polls every **3 min**; validators lease seeds in **batches of 50**, run agent in **sandboxed Docker**; stitched mean over [0,1100) = score → champion check.
- **1.5 h pre-rollover freeze** (commit after rollover). **~20 min** commit cooldown.
- **Stale-family burn:** 7 days with no new crowning → family slice **burns** (re-evals don't reset the clock; champion must re-beat itself from a fresh hotkey).
- Full 1,100-seed benchmark every submission (a 300-seed screening exists but is `SCREENING_ENABLED = False`).

## 7. Emissions
Family slices are **absolute** (Interceptor 0.30, Swarm Autopilot 0.20, Swarm SAR 0.20, Autopilot 0.15, SAR 0.15 = 1.00). A non-payable family (no king / stale / archived) **burns** its slice — nothing redistributes across families, but within a family an ineligible seat renormalizes onto surviving kings. Validators recompute weights locally from raw kings + shares (no shared secret); final vector L1-normalized on chain.

## 8. Device & third-party
| Role | CPU | RAM | GPU | Disk | Net |
|---|---|---|---|---|---|
| Miner | 3+ cores (8 rec) | 8 GB min | **Not required** | 20 GB (100 rec) | 100/20 Mbps |
| Validator | 3+ cores | 16 GB | Not required | 50 GB | — |

**No GPU required to mine** (commit URL, go offline). GPU only helps *train* your policy. **Third-party:** GitHub (mandatory public repo), Bittensor/subtensor (finney, netuid 124), Docker (local benchmark + validator sandbox). **No external API / inference cost / per-submission fee** — deterministic PyBullet sim.

**Tech stack:** Python 3.11+, PyBullet (`swarm-bullet3`), `swarm-drone-gym`, Stable-Baselines3 / sb3-contrib / gymnasium / PyTorch / ONNX, `swarm` CLI. Whitelist: torch, torchvision, onnx(runtime), stable-baselines3, gymnasium, numpy, scipy, scikit-learn, opencv, pillow, matplotlib, einops, tensorboard, etc.

## 9. Gotchas (submission killers)
1. **README hash mismatch** — #1 silent killer; must be byte-exact template. Let `swarm repo package` write it; `swarm repo verify` first.
2. **One shot per hotkey** — once evaluated, the slot locks; a new artifact is ignored. New model = new hotkey.
3. Repo must be **public + reachable + intact** or the seat forfeits payout.
4. Non-whitelisted package / >50 MiB / wrong URL shape / freeze window / private repo → no score.

## 10. Honest take
Best fit for **RL / robotics / control engineers** — the skill is real drone-control ML (depth-perception + policy learning), not prompt tricks. **Copy-resistant** (KotH pays *jumps* + each crown needs a fresh hotkey and a real improvement). Friendlier than pure KotH: 5 kings earn per family and breakthroughs keep paying for ~4 dethronings. **Low money/hardware barrier to run** (no GPU, no inference cost, no fee) — the cost is your training compute and skill. Mind the one-shot rule, the README trap, and the 7-day stale-family burn.
