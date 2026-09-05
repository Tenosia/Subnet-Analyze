# SN90 — KubeTEE ("AI Factory" / Confidential Compute)

| | |
|---|---|
| **netuid** | 90 (`KubeTEE`, symbol `テ`) |
| **Operator brand** | KubeTEE AI Factory — Decentralized Clusters for SOTA AI in TEE |
| **Corporate** | KubeTEE AI LTD (subnet owner) · 1-HORIZON LTD (miner operator, stated related party) |
| **Owner hotkey** | `5EKtGWqskt8qBqdAZ78pSWRCYRuYmDc5XbwJPDqH1EpiSTEE` (holds **UID 0**) |
| **Owner coldkey** | `5C9y6fnLPSzBeh1Np7f4DnGen42xV29nL9qZTDuwpVC4iTEE` |
| **Registered at block** | 8,618,670 |
| **Code** | https://github.com/KubeTEE-AI/kubetee-subnet @ `f17788b` (validator only — no miner code exists) |
| **Site / gateway** | https://kubetee.ai · `llm.kubetee.ai` (LiteLLM, OpenAI-compatible) |
| **Validator image** | `ghcr.io/kubetee-ai/kubetee-validator:v1` (public) |
| **Live dashboard** | https://s3.hippius.com/kubetee-validator/index.html · machine-readable `dashboard.json` |
| **Rancher proxy** | `https://validator.kubetee.ai` (owner-operated, hotkey-signed) |
| **Local checkout** | `/tmp/claude-0/-root/c0422a1e.../scratchpad/kubetee` |
| **Live state (2026-08-28, block 8,940,312)** | epoch 24834, tempo 360 |
| **Price** | 0.036386 TAO/テ · tao_in τ2,326.74 · alpha_in 64,712 · alpha_out 220,381 |
| **UIDs** | 95 registered · **2 earning** · 6 validator permits · 6 with dividends |
| **Registration cost** | **0.0005 TAO** (~$0.13) — effectively free |
| **Miner deposit** | 100 TAO stated — **measured, not enforced** (the sole miner has posted τ0) |

> Live from finney + the operator's published `dashboard.json` on 2026-08-28.
> Where README/site and the shipped validator code disagree, **the code is
> recorded as authoritative** and the disagreement is flagged in §11.

---

## 1. Goal of the subnet

Sell **enterprise confidential compute**: run AI workloads inside hardware
Trusted Execution Environments so data and models are protected *in use*, not
just at rest and in transit, on decentralized Kubernetes clusters supplied by
Bittensor miners.

The stack is entirely off-the-shelf open source, assembled rather than invented:

```
RKE2 (FIPS-140-2 validated Kubernetes)
  └─ Rancher + Fleet GitOps          multi-cluster management
      └─ Kata Containers 4.1.0       each pod is a hardware-isolated VM
          └─ Confidential Containers (CoCo) + Trustee   attestation & secrets
              └─ Intel TDX + NVIDIA Confidential Computing
                  └─ runtimeClass: kata-qemu-nvidia-gpu-tdx-runtime-rs (GPU)
                                    kata-qemu-tdx-runtime-rs           (CPU)
```

Armada is the planned multi-cluster batch scheduler; LiteLLM at `llm.kubetee.ai`
is the live inference front door. Target buyers are regulated workloads —
HIPAA, SOC2/PCI-DSS, FedRAMP — that need attestable isolation.

**This is a DePIN infrastructure subnet, not an ML competition.** There is no
model to train, no task to solve, no leaderboard. You supply GPU capacity in a
qualifying configuration; the validator checks it is present and healthy and
pays you a USD-denominated rate per GPU-hour.

The economic thesis: external demand buys SN90 Alpha on the open market to pay
for compute; spent Alpha is **recycled** (returned to unissued supply, not
burned) and re-emitted, so consumption funds the miner budget and the emission
subsidy decays toward a "crossover" where net Alpha issuance ≈ 0.

---

## 2. What you do as a miner

### The honest headline: you cannot currently become a miner by registering.

From the README, verbatim:

> **KubeTEE onboards each miner today.** The miner supplies the cluster and the
> hardware it runs on; KubeTEE binds it by applying the `kubetee.ai/hotkey`
> label that links the cluster to the miner's registered hotkey.
>
> Self-service permissionless onboarding ships in **Phase 1**. Until then the
> platform endpoints, credentials, and binding procedures behind onboarding are
> intentionally **not published in this public repository**.

And the rate is explicitly capped:

> **Onboarding rate is demand-driven.** New miner capacity is added to match
> proven demand, not ahead of it, so emissions are not diluted by unused
> clusters.

The validator's gate is `hotkey_of(cluster) == your_hotkey`. That label is
applied by the operator, off-chain, by hand. Registering a hotkey costs 0.0005
TAO and, without that label, earns **exactly zero forever**. This is the single
most important fact about SN90 as a mining opportunity.

### If you were onboarded, the deliverable is a cluster

| Requirement | Detail |
|---|---|
| **Cluster size** | **≥ 8 nodes**, all co-located in **one data center** |
| **Topology** | 5 combined control-plane + etcd + worker nodes, **plus ≥ 3 dedicated 8-GPU workers per GPU type** |
| **CPU platform** | **Intel TDX only** — 5th Gen Xeon (Emerald Rapids) or 6th Gen (Granite Rapids). BIOS + kernel TDX enabled |
| **Not supported** | Intel 4th Gen (Sapphire Rapids) or older; AMD SEV-SNP is **Phase 1, not scored today**; SEV / SEV-ES never |
| **GPUs** | **Exactly 8 per node, all identical model**, from H100 / H200 / B200 / B300 / RTX PRO 6000 Blackwell **Server** Edition |
| **Not supported** | A100, V100, RTX PRO 6000 **Workstation** Edition, anything else |
| **Per node** | ≥ 8 CPU cores, ≥ 16 GiB RAM, node Ready + schedulable |
| **Labels** | `nvidia.com/gpu.workload.config = vm-passthrough`, a confidential Kata runtime handler, `nvidia.com/gpu.count ≥ 8` |
| **Management** | Cluster registered with the operator's **Rancher**; Fleet GitOps deploys the stack |
| **Collateral** | **100 TAO** on your own mining hotkey (non-custodial, non-slashable, currently **not enforced**) |
| **One cluster per hotkey** | Enforced by the label contract |

A minimum qualifying cluster is therefore **3 × 8 = 24 GPUs of one class**, plus
5 more nodes. At Blackwell prices that is roughly **$1.5M–4M of hardware** plus
a TDX-capable colocation contract.

There is **no miner software in this repository.** The only code shipped is the
validator. Your "miner" is the cluster itself; the operator's Fleet GitOps
deploys everything onto it.

---

## 3. Scoring logic

Two stages: a **binary fail-closed readiness gate**, then a **USD-denominated
capacity payout**. There is no quality measurement, no benchmark, no ranking.

### 3.1 The readiness gate (`infrastructure_validation.py`)

> *"A miner's verdict is binary: every required signal must pass, else score 0.
> Any explicit missing/malformed/ambiguous/unhealthy evidence is a failure."*

Checks, all read from the operator's Rancher inventory:

1. Cluster carries `kubetee.ai/hotkey` == your registered hotkey
2. Not banned (`kubetee.ai/ban != "true"`)
3. Cluster Ready, HA topology present (etcd / control-plane / worker roles)
4. At least one schedulable worker
5. Every active node ≥ 8 CPU cores and ≥ 16 GiB
6. ≥ 1 schedulable 8-GPU worker of a supported class with `vm-passthrough`
   **and** a confidential Kata runtime handler

A Rancher outage is a **cycle skip**, not a per-miner failure.

> ⚠️ **What "attestation" actually means in the shipped code.** Requirement 6 is
> a **string match on a Kubernetes label**:
> ```python
> if "kata" in low and ("tdx" in low or "nvidia-gpu" in low): ...
> ```
> There is **no TDX quote verification, no CoCo Trustee call, and no Intel Trust
> Authority check anywhere in the validator**. `grep -ri "attest" validator/*.py`
> returns only comments. Fresh TEE attestation is listed as "Designed / to be
> built". See §11.

### 3.2 The payout formula (`miner_scoring.py`)

```
usd_earned  = Σ over GPU classes ( gpu_count × effective_card_price ) × tenure × window_hours
weight      = usd_earned / emission_pool_usd
owner_weight = 1 − Σ(miner weights)          # "recycled to the owner UID"
```

- `tenure` is **hardcoded to 1.0** — *"while the reliability gate is not wired."*
- `window_hours` = tempo × 12 s / 3600 = **1.2 h** per epoch.
- Whatever miners do not earn goes to the owner's UID as weight.

### 3.3 The price card

| GPU | Published card ($/GPU/hr) | Targon-clamped effective (live) |
|---|---|---|
| B300 | $10.00 | $9.75 |
| B200 | $8.00 | $8.00 |
| H200 | $5.50 | **$4.125** |
| H100 | $4.00 | $4.00 |
| RTX6000 | $2.50 | $2.00 |

The published card is a **target maximum**. Each cycle the owner's validator
polls `stats.targon.com/api/miners`, takes the highest $/card per class on
Targon (SN4), and **clamps the card downward** — floor `0.75×`, envelope
`[0.8×, 1.25×]` of the compiled-in default. One publisher writes the snapshot to
Hippius S3; every other validator reads it.

### 3.4 Worked example — the only live miner, verified

UID 56, cluster `na-us-oakland-56`, 32 × B200 + 48 × H200:

```
usd/hr  = 32 × $8.000  +  48 × $4.125   =  $256.00 + $198.00  =  $454.00
usd/epoch = $454.00 × 1.2 h                                    =  $544.80
weight  = 544.80 / 2658.46                                     =  0.2049
```
Dashboard reports `usd: 544.8`, `share: 20.5`. ✔ Formula confirmed exactly.

### 3.5 ⚠️ The emission pool is sized against the wrong denominator

`chain_state.py`:

```python
def emission_pool_usd(self, tao_usd: float, miner_share: float = 0.41) -> float:
    ...
    total_alpha = sum(emissions.values())        # ← the WHOLE metagraph
    return total_alpha * tao_usd * spot          # ← miner_share never used
```

`miner_share` is declared and **never referenced in the body**; the single
caller (`validator.py:171`) does not pass it either. So the USD pool is sized
against the full **82 %** of emission that flows through the metagraph
(miners + validators), while weights only distribute the **41 %** miner half.

Verified on chain:

| | |
|---|---|
| sum of metagraph emission | 295.20 α/tempo = 0.82 × 360 ✔ |
| pool | 295.20 × $9.01 = **$2,658** ✔ (dashboard: 2658.46) |
| UID 56 USD target | $544.80/epoch → **$10,896/day** |
| UID 56 actually receives | 28.50 α/tempo → 570 α/day → **$5,310/day** |
| **realisation ratio** | **48.7 %** — i.e. exactly the 0.41/0.82 factor |

**Every miner is paid roughly half the USD compensation rate the mechanism
advertises.** The published price card is not the rate you receive; halve it.

---

## 4. Live competition landscape

### 4.1 There is one miner

From the operator's own `dashboard.json` (block 8,940,297):

```json
{"fleet_gpus": {"B200": 32, "H200": 48},
 "miners": [{"uid": 56, "cluster_name": "na-us-oakland-56",
             "gpus": [["B200",32],["H200",48]], "ready": true,
             "usd": 544.8, "share": 20.5, "alpha": 60.4958}],
 "miner_usd": 544.8, "owner_usd": 2113.66, "total_pool_usd": 2658.46,
 "usd_per_alpha": 9.01, "pricing_source": "live"}
```

One miner. 80 GPUs. 20.5 % of the pool to it; **79.5 % recycled to the owner.**

### 4.2 On-chain emission

| UID | Role | Incentive | Dividends | α/day | $/day |
|---|---|---|---|---|---|
| **0** | owner hotkey | **0.8069** | 0.4057 | **3,580** | **~$33,343** |
| **56** | the only miner | **0.1931** | — | **570** | ~$5,310 |
| 1 | `5E2LP6EnZ54m3w` (large root validator) | 0 | 0.4259 | 1,257 | ~$11,715 |
| 93 | validator | 0 | 0.1313 | 388 | ~$3,612 |
| 90, 9, 57 | validators | 0 | 0.0184 / 0.0076 / 0.0111 | small | |
| **all other 88 UIDs** | registered, unbound | **0** | 0 | **0** | **$0** |

**93 of 95 registered UIDs earn nothing.** They hold hotkeys with no
`kubetee.ai/hotkey` binding, which is the only way in.

### 4.3 The one miner is exempted from the confidential-computing requirement

`config.py`:

```python
# SN90 owner staging miner — hybrid TDX/non-CC GPUs count for payout.
# Hardcoded so every validator (owner + readers) scores UID 56 the same way.
OWNER_MINER_UID = 56
```

`validator.py`:

```python
include_tdx_non_cc = miner.uid == cfg.owner_miner_uid
...
cc_ok = p.vm_passthrough and p.kata_confidential_runtime
if cc_ok: ...                      # every other miner must clear this
if include_tdx_non_cc and (        # UID 56 only needs a TDX-capable label
        labels.get("intel.feature.node.kubernetes.io/tdx") == "true"
     or labels.get("feature.node.kubernetes.io/cpu-security.tdx.enabled") == "true"
     or "tdx" in labels.get("nvidia.com/cc.mode", "").lower()
     or labels.get("katacontainers.io/kata-runtime") == "true"):
    breakdown[p.gpu_class] += count
```

So the sole earning miner is paid for GPUs that need only be *TDX-capable*, not
running confidential. Every future external miner must clear the stricter bar.
This is disclosed in code comments and the validator README, but it sits
directly against the README's headline claim that **"TEE attestation is
mandatory — no attestation means no emissions."**

### 4.4 What is genuinely live

Not vapour — these are real and verifiable:

- Kata 4.1.0 + CoCo TEE runtime classes on TDX H200/B200 nodes
- `llm.kubetee.ai` serving **GLM-5.2**, **DeepSeek-V4-Flash-0731**,
  **Ornith-1.5-397B** (claimed first worldwide availability, 2026-08-20)
- SN28 sayGM connected as an inference provider + idle-capacity channel since
  2026-08-19; free window closed at 14,812,329,857 tokens
- Validator v1 on Finney: 12 modules, 35 tests, one `set_weights` per epoch
- Real upstream contribution — [kata-containers#13535](https://github.com/kata-containers/kata-containers/issues/13535),
  a root-caused OVMF eager-memory-acceptance bug on large TDX guests, filed with
  serial logs and three fix proposals
- Albedo SN97 distillation eval PoC: 100-sample run succeeded 2026-08-09, then
  **parked 2026-08-13**

### 4.5 What is not

Armada (the scheduler the whole batch story rests on) is **"In development"** —
not deployed. Paid jobs, permissionless onboarding, fresh TEE attestation,
Armada job metrics, serving probes, price-competitiveness scoring, Lium/Chutes
scraping, the Jobs MCP server, validator-in-TEE, and on-chain collateral bonding
are all unbuilt. The two US production clusters are unchecked boxes.

---

## 5. Miner economics

Subnet emits **1.000 α/block = 7,200 α/day**; 18 % owner cut, 41 % miners,
41 % validator dividends → **miner pool = 2,952 α/day**.

At α = 0.036386 TAO and TAO ≈ $256 (α ≈ $9.31; the validator's own feed says
$9.01):

### The live miner

| | |
|---|---|
| Fleet | 32 × B200 + 48 × H200 = 80 GPUs (10 nodes) |
| Advertised USD target | $454.00/hr → **$10,896/day** |
| Weight | 0.205 (chain incentive 0.193, EMA-lagged) |
| **Actually received** | **570 α/day = 20.74 TAO/day ≈ $5,310/day ≈ $159k/mo** |
| Effective realised rate | **~$2.76/GPU/hr** against a $5.68/GPU/hr card |

### What a new miner would earn (if onboarded)

Because weight = your_usd / pool and the pool is fixed, a new miner **dilutes
the owner's recycle share, not the existing miner** — until total miner USD
exceeds the pool, at which point everyone is pro-rata normalised.

| Fleet (minimum qualifying) | Card $/hr | Advertised $/day | **Realised ≈49 % $/day** | **$/mo** |
|---|---|---|---|---|
| 3 × 8 H100 = 24 | $96.00 | $2,304 | **~$1,123** | ~$33.7k |
| 3 × 8 H200 = 24 | $99.00 | $2,376 | **~$1,158** | ~$34.7k |
| 3 × 8 B200 = 24 | $192.00 | $4,608 | **~$2,245** | ~$67.4k |
| 3 × 8 B300 = 24 | $234.00 | $5,616 | **~$2,736** | ~$82.1k |
| 6 × 8 B200 = 48 | $384.00 | $9,216 | **~$4,490** | ~$134.7k |

*Headroom check:* the whole miner pool is 2,952 α/day ≈ $27,500/day. Once
aggregate miner USD targets exceed $2,658/epoch (~$53,000/day advertised),
weights are pro-rata normalised and everyone's realised rate falls further.
At current prices the subnet can absorb roughly **4–5 more minimum B200
clusters** before dilution starts biting.

### Costs

| Item | Cost |
|---|---|
| Hotkey registration | **0.0005 TAO** (~$0.13) — but worthless without the binding label |
| **Collateral** | 100 TAO ≈ **$25,600** (stated; not currently enforced) |
| **Hardware — 3 × 8-GPU B200 nodes** | ~$1.2M–1.8M capex, or ~$3–6/GPU/hr rented |
| 5 × TDX control-plane/worker nodes | ~$50–100k |
| Colocation, power, cooling (80 GPUs ≈ 80–100 kW) | ~$25–60k/mo |
| Networking, storage (Longhorn), ops staff | material |

**Break-even reality:** the realised ~$2.76/GPU/hr for B200/H200 mixed is at or
below what you would get renting the same cards on the open market
(B200 spot ≈ $4–6/GPU/hr, H200 ≈ $2–3.50/GPU/hr). The B200 half is clearly
underwater versus spot; the H200 half is roughly at market. **The economic case
rests on Alpha appreciation and on the recycle flywheel actually spinning up,
not on the compute rate.**

### Owner capture

| Stream | α/day |
|---|---|
| Owner cut (18 %) | 1,296.0 |
| UID 0 incentive (0.8069 of miner pool) | 2,382.0 |
| UID 0 validator dividends (0.4057) | 1,197.6 |
| **Total to the owner hotkey** | **4,875.6 α/day = 67.7 % of all emission** |

≈ **$45,400/day** at current prices. The README states the owner's 18 % stream
and 100 % of its dTAO conviction are *"programmatically re-locked on-chain so it
never decays and is never withdrawn"* — that claim covers the owner's dTAO
position; I did not attempt to verify the lock on chain, and the UID-0
**incentive** share (2,382 α/day, the recycled miner remainder) is a separate,
liquid stream.

---

## 6. How to become a winner

**Blunt answer: you cannot, today, by your own action.** There is no search to
run, no model to build, no score to beat. The gate is an operator applying a
label to your cluster, and the operator has said publicly that it adds capacity
only to match proven demand.

If you want in, the sequence is:

1. **Contact KubeTEE and get in the onboarding queue.** This is a business
   development conversation, not a technical one. Ask directly: what demand
   justifies onboarding my cluster, and when.
2. **Pre-qualify hardware before spending anything.** The bar is narrow and
   unforgiving:
   - Intel Emerald Rapids or Granite Rapids Xeon only (`lscpu | grep "Model name"`,
     `dmesg | grep -i tdx`). Sapphire Rapids and all AMD are out today.
   - Exactly 8 identical GPUs per node from H100/H200/B200/B300/RTX PRO 6000
     **Server**. Verify by PCI ID (`lspci -nn | grep -i nvidia`) — the
     Workstation RTX PRO 6000 has no CC support and is rejected.
   - ≥ 3 such nodes **per GPU type**, plus 5 more nodes, one data center.
3. **Choose the GPU class on realised economics, not the card.** B200 at a
   realised ~$3.94/GPU/hr against $4–6 spot is a loss versus renting them out
   yourself. H100 at ~$1.97 and H200 at ~$2.03 realised are also at or below
   market. **On pure compute revenue no class currently clears spot** — model
   this in Alpha, and be explicit that you are taking an Alpha-appreciation bet.
4. **Maximise GPU count per qualifying node, not node count.** Payout is
   `Σ gpu_count × card_price`, read from the `nvidia.com/gpu.count` label, with
   a hard floor of 8 per node and no ceiling in the scoring code. There is no
   quality term, no uptime term (tenure is pinned at 1.0), and no job-success
   term. Capacity is the entire score.
5. **Prefer B300 if you are buying new.** $9.75 clamped vs B200 $8.00 —
   the best card rate, and the Targon clamp has moved it least (−2.5 %) while
   H200 was cut 25 %.
6. **Post the 100 TAO collateral even though it is unenforced.** It is
   non-custodial and stays on your own hotkey; being short is the stated reason
   validators may decline to score you once Phase 1 lands.
7. **Watch for Phase 1.** Permissionless onboarding, on-chain collateral
   bonding, and attestation-based scoring all land together. That is the moment
   this subnet becomes minable by an outsider — and also the moment the scoring
   bar gets materially harder.

### The realistic alternative: run a reader validator

This is the one role that **is** permissionless today, and it is genuinely
cheap:

- Requirements: a hotkey registered on SN90 with `validator_permit=True`, a
  Taostats API key, and Docker. **No GPU, no Rancher account, no onboarding.**
- `docker compose up -d` with ~6 env vars; dry-run with `DRY_RUN=1 ONCE=1`.
- Evidence comes through the owner's hotkey-signed Rancher proxy at
  `validator.kubetee.ai`.

Validator dividends are currently 41 % of emission = 2,952 α/day ≈ $27,500/day,
but they are distributed by **stake weight**, and UID 0 + UID 1 hold ~83 % of
it. A permit requires enough stake to make the top-N cut. Model this as a
staking-yield play with an ops cost, not as a mining play.

---

## 7. Rules you must keep

| Rule | Consequence if broken |
|---|---|
| Cluster must carry `kubetee.ai/hotkey` == your hotkey (operator-applied) | Score 0 — you are invisible to the validator |
| `kubetee.ai/ban != "true"` | Score 0 |
| One cluster per hotkey | Only the first bound cluster is read |
| Cluster Ready + HA topology (etcd / control-plane / worker) | Score 0 |
| Every active node ≥ 8 CPU cores, ≥ 16 GiB | Score 0 |
| ≥ 1 schedulable 8-GPU worker, supported class | Score 0 |
| That worker labelled `nvidia.com/gpu.workload.config=vm-passthrough` | Score 0 |
| That worker exposes a confidential Kata runtime handler | Score 0 (UID 56 exempted) |
| `nvidia.com/gpu.count ≥ 8` per node | Node excluded from the GPU breakdown |
| All 8 GPUs identical model | Node fails uniformity |
| Intel TDX enabled in BIOS **and** kernel | Node not TEE-capable → score 0 |
| Keep CC **on** (guest debug off) | *"Capacity with CC off is not confidential capacity and is not what the subnet scores"* |
| Any missing / malformed / ambiguous evidence | **Fail-closed** — treated as failure, not as unknown |
| 100 TAO collateral on your hotkey | Currently measured only; enforcement is Phase 1 |

---

## 8. Device / hardware conditions

### Miner — the real bar

| | Requirement |
|---|---|
| **Nodes** | ≥ 8 per cluster: 5 combined CP+etcd+worker, **+3 dedicated 8-GPU workers per GPU type** |
| **Locality** | All nodes in a **single data center** |
| **CPU** | Intel Xeon **Emerald Rapids (5th Gen)** or **Granite Rapids (6th Gen)**, TDX in BIOS + kernel |
| **CPU excluded** | Sapphire Rapids and older; all AMD (SEV-SNP is Phase 1, unscored) |
| **GPU** | **Exactly 8, identical**, from H100 (80GB) / H200 (141GB) / B200 (192GB) / B300 (288GB) / RTX PRO 6000 Blackwell **Server** (96GB, CC mode on) |
| **GPU excluded** | A100, V100, RTX PRO 6000 Workstation, mixed models, 1–7 or 9+ per node |
| **Per node** | ≥ 8 cores, ≥ 16 GiB (validator floor; real stack needs far more) |
| **Software** | RKE2, Rancher-registered, NVIDIA GPU Operator, Kata 4.1.0 + CoCo, Longhorn, monitoring, Armada Executor |
| **Power** | ~10–14 kW per 8-GPU Blackwell node; ~100 kW for a 10-node cluster |

> **Against your BEAM box (46.225.140.58, 2 cores / 3.7 GB):** completely
> irrelevant here. SN90 is not a software-mining subnet — the unit of
> participation is a TDX-enabled, multi-million-dollar GPU cluster in a data
> center. There is no low-end path, no CPU-only tier, and no way to submit
> anything. The **only** thing that box could plausibly run is a reader
> validator (Docker + 6 env vars, no GPU), and even that needs a
> `validator_permit`, which needs stake.

### Validator — trivially cheap

| | Reader mode |
|---|---|
| GPU | **None** |
| Hardware | Anything that runs Docker; a small VPS is enough |
| Install | `ghcr.io/kubetee-ai/kubetee-validator:v1`, `docker compose up -d` |
| Credentials | Hotkey mnemonic + Taostats API key |
| Rancher | None — signs requests with its hotkey against the owner's proxy |
| Ports | 9100 metrics (9101 proxy is owner-only) |
| Cadence | One cycle per 360 s ≈ one epoch; one `set_weights` per epoch |

Owner mode additionally holds the Rancher bearer token and Hippius S3 write
keys — **not published**.

> The roadmap item *"Validator runs in a TEE (Kata + CoCo) on the control plane"*
> is **unchecked**. Today the referee is an ordinary container on the operator's
> machine.

---

## 9. Third-party conditions

| Dependency | Role | Failure mode |
|---|---|---|
| **Rancher** (`validator.kubetee.ai`) | **The only source of miner evidence.** Owner-operated | Outage = cycle skip, no weights. The operator controls every input to scoring. |
| **RKE2** | FIPS-140-2 validated Kubernetes base | FIPS-140-3 is a *target*, not achieved |
| **Kata Containers 4.1.0** | Pod-as-VM confidential runtime | Stock 4.1.0 OVMF still needs the operator's `ovmf-tdx-bump-202605` overlay; several upstream issues open |
| **Confidential Containers / Trustee** | Attestation + secret release (KBS) | **Not called by the validator** — attestation is unscored |
| **Intel TDX** | Hardware memory encryption | Sole supported TEE; single-vendor dependency |
| **Intel Trust Authority** | Quote verification for RA-TLS | Referenced in design; not in validator code |
| **NVIDIA** GPU Operator / NIM / NeMo | GPU passthrough, inference, microservices | NIM Operator's Kata sandbox support is **experimental** upstream |
| **Armada** | Multi-cluster batch scheduler | **Not deployed.** The batch product does not exist yet |
| **LiteLLM** (`llm.kubetee.ai`) | OpenAI-compatible gateway, virtual keys, budgets | Live |
| **Taostats API** | TAO/USD compensation feed | **Fails closed** — no price, no weights that cycle |
| **CoinGecko** | TAO/USD fallback when Taostats 429s | Public, unkeyed |
| **Targon SN4** (`stats.targon.com/api/miners`) | Supply-side payout clamp on the price card | **Fails soft** → cache → S3 → compiled default |
| **Hippius SN75 S3** | Publishes price card, payout snapshot, dashboard | Payload is **unsigned**; integrity rests on the write credential, TLS, and the `[0.8×,1.25×]` envelope |
| **Cloudflare** | DNS + bot-fight on `kubetee.ai` | Blocks default Python UA (error 1010); client must set its own User-Agent |
| **ghcr.io + Watchtower** | Validator image distribution + **hourly auto-update** | The operator can push `v1.x.y` and every reader validator pulls it within the hour |
| **SN28 sayGM** | Inference provider + idle-capacity demand channel | Live since 2026-08-19 |
| **Base / Chainlink CCIP / Aerodrome** | TAO-on-Base acquisition rail | Live 2026-08-21; billing on it is Phase 2 |
| **Lium SN51 / Chutes SN64** | Demand-side price feeds | **Nothing scrapes them** — design only |

---

## 10. Risks

1. **You cannot mine without the operator's permission.** Onboarding is manual,
   the procedures are deliberately unpublished, and the rate is explicitly
   throttled to demand. Registration is free and worthless without the label.
   Everything else on this list is downstream of that.

2. **One miner, 95 UIDs.** 93 registered hotkeys earn zero. There is no
   competitive landscape to analyse because there is no competition.

3. **The sole earning miner is a stated related party** — 1-HORIZON LTD, described
   in the README as vertically split from KubeTEE AI LTD. Its coldkey
   (`5FKdc9f7…`) differs from the owner coldkey (`5C9y6fnL…`), so they are not
   the same on-chain entity, but there is no on-chain evidence of independence
   either. It is also the UID with the hardcoded CC exemption.

4. **The owner captures 67.7 % of all emission** (~$45,400/day) — 18 % cut plus
   80.7 % of the miner pool as "recycle" plus 40.6 % of validator dividends.

5. **Confirmed payout bug: miners receive ~48.7 % of the advertised rate.**
   `emission_pool_usd()` sizes the USD pool against 82 % of emission while
   weights distribute only the 41 % miner share; the `miner_share=0.41`
   parameter is declared and never used. Verified end-to-end against chain and
   dashboard.

6. **"TEE attestation is mandatory — no attestation means no emissions" is not
   what the code does.** The validator does a substring match on a Kubernetes
   label. No quote, no Trustee, no Intel Trust Authority. A miner with the right
   labels and no working TEE would score identically to one with a real attested
   fleet.

7. **A hardcoded exemption for the only paid miner.** `OWNER_MINER_UID = 56`
   makes non-CC GPUs count for payout for that UID alone. Disclosed, but it
   contradicts the headline claim and it benefits the sole earner.

8. **The validator "trusts nobody" claim does not hold.** Unlike SN103, where I
   could recompute every score from published evidence, here **all** miner
   evidence originates from the operator's Rancher, reached through the
   operator's proxy, priced by a card the operator publishes to S3 as an
   unsigned object. A reader validator independently verifies nothing about the
   physical fleet.

9. **Hourly auto-update from the operator's registry.** Watchtower is shipped
   enabled in `docker-compose.yaml`, pinned to the mutable `v1` tag. A pushed
   image reaches every reader validator within an hour. Convenient; also a
   single supply-chain control point over the whole validator set.

10. **`tenure` is hardcoded to 1.0.** There is no uptime, reliability, job-success
    or SLA term in scoring today. Capacity present at poll time is the entire score.

11. **The product the tokenomics depend on does not exist yet.** The recycle
    flywheel needs paid jobs; paid jobs need Armada; Armada is "in development".
    Phase 2 is where billing lands. Until then emissions are a pure subsidy with
    no measured demand-side revenue.

12. **Enormous, illiquid, single-purpose capex.** ~$1.5M–4M for a minimum
    qualifying cluster, on hardware locked to Intel TDX + specific NVIDIA SKUs,
    to earn a realised rate at or below open-market GPU rental.

13. **FIPS claims need careful reading.** FIPS-140-2 applies to the **RKE2
    crypto module** (BoringCrypto cert #3678), not to the TEE. The repo's own
    FIPS doc states plainly: *"no current TEE implementation has standalone
    FIPS 140-3 validation"*, SEV-SNP firmware crypto is unvalidated, and Intel
    TDX/MKTME has no standalone validation. FIPS-140-3 is a **Phase 3 target**.
    It also flags 15–35 % performance overhead for combined FIPS + CC.

14. **Single-vendor TEE.** Intel TDX only. AMD SEV-SNP is Phase 1 and unscored,
    so there is no hardware diversity and no second source.

15. **Taostats fails closed.** A price-feed outage means no weights that cycle.
    A prolonged outage means no emission distribution changes at all.

16. **Alpha liquidity.** 64,712 α in the pool against τ2,327. Daily emission to
    the owner alone (4,876 α) is 7.5 % of pool depth. Marks are not realisable
    at size.

17. **Concentrated dividend capture.** UID 0 and UID 1 hold ~83 % of validator
    dividends; six UIDs hold all of it.

---

## 11. Documentation defects found (trust the code)

| Claim | Where | Reality in shipped code |
|---|---|---|
| "TEE attestation is mandatory — **no attestation means no emissions**" | README §Subnet Economics | Substring match on a node label. No quote verification anywhere in `validator/` |
| "Compliance is enforced rather than requested" | README §Subnet Economics | Enforced against a label the operator applies |
| "emissions distributed per resources provided, **weighted by attested TEE health, job-execution quality, and uptime**" | README §Incentive Mechanism | Only capacity is scored. `tenure` hardcoded 1.0; no job metrics; no health term |
| `miner_share: float = 0.41` | `chain_state.py:128` | Declared, never used → miners paid ~48.7 % of target |
| "A **100 TAO deposit** held as on-chain registration collateral" | README §For Miners | Measured, not enforced. The sole miner holds **τ0** stake |
| "Miners keep CC on: capacity with CC off … is not what the subnet scores" | README §Miner onboarding | True for everyone **except** hardcoded UID 56 |
| Validator runs in a TEE, "the referee itself attested" | README §Validator Runtime | Unchecked roadmap box; runs as a plain container today |
| "Each run, your validator reads the commitments on chain, fetches each miner's recipe…" | — | *(that was SN103; no equivalent defect here)* |
| Competitive pricing scores miners on price competitiveness | README §Competitive Pricing | *"Nothing scrapes Lium or Chutes. No per-job-class target price is computed, no miner is scored on price competitiveness."* — the doc itself says so |
| FIPS-140-3 badge at top of README | README header | Badge reads "Target"; the linked RKE2 page is FIPS-**140-2**. Repo's own FIPS doc says no TEE has 140-3 validation |
| `CAPSUB…`-style env drift | `validator/.env.example` | Reader-mode template is accurate; owner credentials intentionally absent |

To the project's credit, most of these gaps are **self-disclosed** — the "What
Ships Today" table, the Competitive Pricing status block, and the code comments
are unusually candid. The defect is that the headline prose and badges assert
the finished state while the tables assert the current one.

---

## 12. Verdict

### Against SN103 (analysed 2026-08-27)

| | **SN90 KubeTEE** | **SN103 Capcomp** |
|---|---|---|
| Type | DePIN infrastructure | ML competition |
| Miner deliverable | A TDX GPU cluster in a data center | One JSON merge recipe |
| Can you start today? | **No — operator-gated onboarding** | **Yes — register and submit** |
| Entry cost | 0.0005 TAO + **$1.5M–4M hardware** + 100 TAO collateral | 1 TAO (~$256) + rented GPU |
| Miner code in repo | **None** (validator only) | Full miner CLI + local eval |
| Scoring | Binary readiness gate × GPU capacity × price card | 12-axis measured evaluation, re-derivable |
| Competitive miners | **1** of 95 UIDs | 7 qualified of 25, 36 submissions in the live run |
| Payout shape | Proportional to capacity | Winner-take-all (45 % to rank 1) |
| Rank-1 income | ~$5,310/day (the only miner) | ~$3,061/day |
| Owner capture | **67.7 %** | 76.6 % |
| Auditability | **Weak** — all evidence from the operator's Rancher | **Excellent** — I re-derived every score to 5 decimals |
| Self-disclosure | **Very good** — "What Ships Today" table is candid | **Very good** — "What is not yet true" page |
| Verified defect found | Payout bug: miners get 48.7 % of advertised rate | Reference moved mid-run; gate array contradicts verdicts |
| Feedback latency | One epoch (72 min) | 1 day to score, 2 to pay |

### All ten subnets, one snapshot

Every figure in this table was **re-read live from finney on 2026-09-03** (block
8,984,103, TAO ≈ $256) so the rows are directly comparable to each other. The
per-document economics sections above use the α price at each document's own
analysis date and will differ.

| Subnet | Task | Miner deliverable | Miner GPU | Entry cost | α (USD) | Earning / UIDs | Top earner $/day | Owner capture | The catch |
|---|---|---|---|---|---|---|---|---|---|
| **SN47 Feval** | Verifiable LoRA eval | Adapter + published rollouts | 24–48 GB | $12.80 | $0.72 | **1 / 129** | $2,139 ← **owner** | **68.8 %** | Published repo ≠ live network; owner takes the whole miner pool via a `{0: 1.0}` fallback |
| **SN58 Greevils** | TEE algo-trading on Hyperliquid | Agent in a TDX VM, or a plain HL account | none (VM ~$145/mo) | $25.60 + ~$25k capital | $2.29 | 1 / 256 | $6,747 | 41.3 % | Sole earner holds no on-chain commitment; zero `gva1` approvals exist |
| **SN76 Phylax** | AI supply-chain security attestation | One Python file (`agent_main`) | **none** | $25.60 + ~$21/attempt | $0.60 | **21 / 256** | $364 | 40.5 % | Your track's rounds have to actually be scheduled |
| **SN78 Vocence → UMI** | ASL→English translation *(pre-activation)* | HTTP translator service | yes, 24–80 GB | $0.13 | $1.11 | 1 / 256 | $3,290 | 46.9 % | UMI weights type-level disabled; chain still says Vocence; the 0.10 floor is unproven |
| **SN79 MVTRX** | Agent-based market simulation | Always-on trading bot | **none** | $25.41 | $1.68 | **210 / 256** | $444 | 59.0 % | A genuine quant-trading skill gate; latency is scored |
| **SN80 OpenRoboto** | Fine-tune π0.5 VLA robotics | HF checkpoint | yes, A100-class | $0.13 + ~$19/attempt | $3.72 | 2 / 256 | $8,891 ← **owner** | 56.1 % | 81 % of the miner pool sits on the operator's UID 0 |
| **SN82 Compelle** | Adversarial LLM debate | A prompt, committed on chain | **none** | $0.13 | $0.88 | 1 / **64** | $2,599 | **28.8 %** | Incumbent-protected winner-take-all on 64 slots |
| **SN90 KubeTEE** | DePIN confidential compute | A TDX GPU cluster | 8-node TDX datacenter | $0.13 + **$1.5M–4M** | $8.10 | 2 / 97 | $18,715 ← **owner** | 66.6 % | Onboarding is operator-gated — you cannot join |
| **SN92 MicroTensor** | Certified inference systems | ONNX/GGUF artifact + 128-byte pointer | training only (RTX 3090+) | $25.60 | $0.86 | **9 / 256** | $646 | **39.2 %** *(0 % of the miner pool)* | Docs name the wrong paying track — `code` pays 0, `extract` pays all |
| **SN103 Capcomp** | LoRA composition | One JSON merge recipe | 32–48 GB | **$256.00** | $3.02 | **10 / 105** | $8,012 | 55.1 % | Dethrone margin sits ~24× below measurement noise |

**What the snapshot says.** Four of the ten have a functioning competitive field:
**SN79** (210 earners), **SN76** (21), **SN103** (10) and **SN92** (9). Five pay
exactly one UID, and on **SN47, SN80 and SN90** the single top earner *is* the
owner's own UID. Owner capture runs 28.8 – 68.8 %, and **SN92 is the only one
whose owner draws nothing at all from the miner pool** — its 39.2 % is the 18 %
protocol cut plus staked dividends, nothing else. Alpha prices moved materially
between the individual analyses and this snapshot (**SN78 +122 %** since August,
**SN90 −14 %** since its own writeup), so read every USD column as a same-day
comparison, not a forecast.

**Where a newcomer can actually compete today**, ranked: **SN79 MVTRX** (210
paying seats, $25 entry, no GPU, free testnet) → **SN92 MicroTensor** (9 paying
seats on a geometric curve where rank 8 still earns ~⅓ of rank 1, one consumer
GPU for training only, public API that hands you the whole frontier) → **SN76
Phylax** (21 seats, no GPU, local corpus to iterate against) → **SN103 Capcomp**
(10 seats, contested, but $256 entry and a noise-dominated throne) → **SN82
Compelle** ($0.13, one seat, incumbent protected). The remaining five are either
operator-gated, pre-activation, or paying a single UID that is often the owner's.

### Assessment

**SN90 is a real engineering effort and, right now, not a mining opportunity.**

The technical work is genuine — Kata 4.1.0 + CoCo on TDX with 8-GPU passthrough
is legitimately hard, the upstream OVMF root-cause filing is the work of people
who actually run this stack, and `llm.kubetee.ai` serves real models. The
validator is small, tested, fail-closed, and honestly documented in its status
tables. I would take these operators seriously as infrastructure engineers.

**But as a subnet it is one company paying itself.** One miner — a stated
related party, holding a hardcoded exemption from the confidential-computing
requirement the subnet's whole pitch rests on — earns 19 % of the pool while the
owner recycles the other 81 % to itself, on top of the 18 % cut and 41 % of
dividends. Onboarding is manual, unpublished, and rate-limited by the operator's
own demand judgement. That is not a decentralized compute network yet; it is a
company with a subsidised balance sheet and a roadmap.

**Two findings should weigh heavily in any decision.** First, the payout bug: a
declared-but-unused `miner_share` parameter means the advertised GPU price card
overstates realised compensation by roughly 2×, and at ~$2.76/GPU/hr realised
the compute economics are underwater against open-market rental. Second, the
attestation gap: the subnet's differentiator — "no attestation means no
emissions" — is, in code, a substring match on a Kubernetes label. Both are
verifiable from the repository; neither is hidden; neither is fixed.

Compared with SN103, the contrast is sharp. On SN103 I could recompute the
champion's grade to five decimals from published data and disagree with the
operator if I wanted to. On SN90 there is nothing an outsider can independently
verify about the physical fleet — all evidence flows from the operator's Rancher
through the operator's proxy, priced by the operator's unsigned S3 object.

### Recommended path

1. **Do not buy hardware for this.** The realised rate is below spot GPU rental
   on every class. If you already own TDX-capable Blackwell nodes and they are
   idle, the conversation is different — otherwise the capex has better uses.
2. **Do not register a hotkey expecting to mine.** It costs $0.13 and earns
   $0.00 without an operator-applied label. 93 UIDs are already in that position.
3. **If you want exposure, treat it as an Alpha position, not a mining position.**
   The thesis is the recycle flywheel and the DePIN crossover. Those depend on
   Armada shipping and paid jobs landing in Phase 2. Track those two milestones.
4. **The one actionable role today is a reader validator** — no GPU, Docker plus
   six env vars, evidence via the owner's proxy. But dividends go by stake and
   UID 0 + UID 1 hold ~83 %, so price it as staking yield with an ops cost.
5. **If you are seriously interested in supplying capacity, open the BD
   conversation now and ask three specific questions:** what demand justifies
   onboarding my cluster and when; when does the `miner_share` denominator get
   fixed; and when does scoring move from label-matching to real TDX quote
   verification. The answers will tell you more than any further code reading.
6. **Re-evaluate at Phase 1.** Permissionless onboarding, on-chain collateral
   bonding, and attestation-based scoring land together. That is the first
   moment SN90 is minable by an outsider — and the first moment its headline
   claims and its code line up.
7. **Watch the miner count.** One external, unrelated miner appearing with a real
   attested fleet would be the strongest single signal that this is becoming a
   network rather than a company.

---

## 13. Sources

**Code (authoritative)**
- https://github.com/KubeTEE-AI/kubetee-subnet @ `f17788b`
- `validator/miner_scoring.py`, `validator/infrastructure_validation.py`,
  `validator/chain_state.py`, `validator/validator.py`, `validator/config.py`,
  `validator/price_feed.py`, `validator/targon_payout_feed.py`,
  `validator/README.md`, `validator/.env.example`
- `docs/GPU-NODE-REQUIREMENTS.md`, `docs/NODE-REGISTRATION.md`,
  `docs/COMPETITIVE-PRICING.md`, `docs/MINER-DEPOSIT.md`, `docs/TOKENOMICS.md`,
  `docs/FIPS-140-3.md`, `docs/SN28-SAYGM.md`, `docs/SN97-ALBEDO-POC.md`

**Live operator data** (fetched 2026-08-28)
- `https://s3.hippius.com/kubetee-validator/dashboard.json` (block 8,940,297, epoch 24834)
- `https://s3.hippius.com/kubetee-validator/index.html`

**Chain** (finney, block 8,940,312)
- `Subtensor.subnet(90)`, `Subtensor.metagraph(90)`, `Subtensor.recycle(90)`

**External references supplied**
- https://kubetee.ai/
- https://katacontainers.io/
- https://docs.rke2.io/security/fips_support (FIPS-140-2 validated; 140-3 not yet)

**Upstream / ecosystem**
- kata-containers issues [#13535](https://github.com/kata-containers/kata-containers/issues/13535),
  [#13631](https://github.com/kata-containers/kata-containers/issues/13631), #13471, #13482
- `https://stats.targon.com/api/miners` (SN4 supply-side payout clamp)
- Confidential Containers, Armada, Rancher, LiteLLM, Longhorn, Hippius SN75

**Price reference**
- TAO ≈ $256; the validator's own feed reported `usd_per_alpha = 9.01`
