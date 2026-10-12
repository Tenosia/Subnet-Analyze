# Subnet 76 — Phylax — analysis *(ARCHIVED — this subnet no longer exists)*

> ## ⚠️ Historical document
>
> **Netuid 76 is no longer Phylax.** The netuid was deregistered and
> **re-registered on 2026-09-05 at block 9,003,844** by **Heron Cove LLC** as
> **Ormas**, an outcomes API for coding work. The chain identity states it
> plainly: *"Registered September 5, 2026; **not a continuation of the former
> subnet 76**."*
>
> Nothing below applies to the current occupant of netuid 76. Alpha held from
> the Phylax era is a claim on an entirely different project.
>
> **→ Current analysis: [`SN076-ORMAS.md`](SN076-ORMAS.md)**
>
> *(Between Phylax and Ormas the netuid also briefly ran as `nun`. The watchdog
> in this folder logged the `nun → Ormas` rename — see
> [`notification.md`](notification.md).)*
>
> Kept for reference only. Banner added 2026-09-14.

**Analysed:** 2026-08-19 · **Chain state read live from finney** · TAO $190.42, SN76 α = τ0.002242074 = **$0.4264**

| | |
| --- | --- |
| Netuid | 76 (`finney`) |
| Name | Phylax (φύλαξ — "guardian") |
| Operator | praxi-labs |
| Owner hotkey | `5Cw4E2tJjsx1mxGaxpJHEAS9fEgjZQt7r7DeHhZ1Ce6yu5cs` |
| App | https://app.phyi.dev/ · API https://api.phyi.dev |
| Docs | https://docs.phyi.dev |
| Code | https://github.com/praxi-labs/phylax-subnet ([local checkout](phylax-subnet/)) |
| Corpus | https://github.com/praxi-labs/phylax-corpus-data |
| Registered at | block 7,574,784 |

---

## 1. Goal of the subnet

Phylax is a **decentralized trust layer for the AI software supply chain**. Agent ecosystems are assembled from third-party parts — agent skills, MCP servers, pip/npm packages, source repos — and that is where the risk lives: credential theft, data exfiltration, persistence, prompt injection.

The subnet's product is the **SSSA** (Signed Skill and Supply chain Safety Attestation): a portable, cryptographically signed verdict on an artifact, backed by proof the analysis actually ran.

Phylax's claim against ordinary LLM scanners is that a scanner built on a model alone is itself prompt-injectable, is defeated by obfuscation because nothing is ever executed, and emits prose rather than something a runtime can enforce. Phylax instead **detonates** artifacts in a sandbox and observes behaviour.

The subnet's own cited research: of 9,350 skill bundles analysed, 77% safe, 4.5% needing manual review, **18.5% confirmed threats**.

> The server schedules rounds and records results, but never decides the winner — that is on-chain Yuma consensus. "The server is a clock and a ledger, not a judge."

---

## 2. What you do as a miner

**You write one Python file and upload it. That is the entire job.**

You do **not** run a neuron. You do **not** build or ship a container. You do **not** serve anything and are never queried. There is no uptime requirement, no axon, no public IP.

```python
def agent_main(context: dict) -> dict:
    return {
        "verdict":  {"decision": "ALLOW | WARN | BLOCK", "risk_score": 0, "confidence": 0.0},
        "evidence": {},   # per-track schema
        "findings": [],   # repositories track
        "policy":   {},
    }
```

Your agent is a **security analyst program**. Validators pull it, run it in *their own* hardened sandbox against that round's artifacts, and score its verdicts against curated ground truth.

### The four tracks — pick exactly one

| Track | Artifact | Verification method | Emission share |
| --- | --- | --- | --- |
| `repositories` | source repos | static audit, scored F2 vs planted vulns | **0.30** |
| `packages` | pip / npm releases | detonation, install+import lifecycle, supply chain | **0.25** |
| `mcp_servers` | MCP server packages | detonation, dual-plane, probe, component analysis | **0.225** |
| `skills` | agent skill bundles | detonation, dual-plane, probe | **0.225** |

One hotkey → one track → one active agent. A new submission supersedes the old one. To change track you must `DELETE /v1/specialization/agent/{hotkey}` first, or the submission is refused with `409`.

### The loop

```
1. register hotkey on netuid 76        (one time)
2. stake 50 α to your own hotkey       (one time, ~$21, stays yours)
3. write my_agent.py
4. python3 scripts/evaluate_local.py --agent my_agent.py --track packages   ← free, seconds
5. ./scripts/register.sh               ← signs + uploads code + inference key
6. wait for the round (every 2 days)
7. read your score, improve, resubmit
```

Rate limit: **one version every two hours** per hotkey. Unlimited versions over time.

### Detection principle

The docs state it as **intent versus behaviour**: derive what the artifact *declares*, observe what it *does*, flag the deviation.

Two evidence planes must both be covered:
- **Action plane** — what the artifact actually did, as canonical capability names (non-canonical names are silently dropped).
- **Context plane** — what it tried to make the *agent* do: prompt injection, hidden instruction overrides.

An artifact can be malicious on either plane.

---

## 3. Scoring logic

### 3.1 Round structure

Rounds open every **2 days**, operator-scheduled. At round open:

1. The participant set **freezes** — every active agent per track, pinned by hash.
2. Per track the backend freezes a pool of **3× the task count**. Each validator draws *its own* task set from that pool, seeded by `round seed + its own hotkey`. Deterministic and auditable afterwards; unknowable in advance.
3. Validators race the same block deadline independently.
4. Weights are set **once per round**, after all four tracks complete.

Your score is the **average across validators**, so no single validator can sink you.

### 3.2 Budgets (frozen)

| Track | Tasks | Reps | CPU budget/rep | Worst case/agent |
| --- | --- | --- | --- | --- |
| skills | 50 | 3 | 8 s | 1,200 CPU s |
| mcp_servers | 40 | 3 | 15 s | 1,800 CPU s |
| packages | 30 | 3 | 30 s | 2,700 CPU s |
| repositories | 50 | 2 | 90 s | 9,000 CPU s |

Budget is **CPU time via cgroup accounting**, not wall clock — faster hardware cannot change outcomes. A wall-clock backstop of 3× catches sleeping/stalling runs. Sandbox per run: **2 GB memory (swap off), 1 CPU, 256 pids**.

### 3.3 Reducing repetitions

- **Behavioural tracks** — each task's completed reps vote. Majority wins; with no strict majority, the median ordinal under `ALLOW < WARN < BLOCK`, taking the *lower* ordinal on an even split. A failed rep is excluded, not zeroed. A task with zero completed reps counts **incorrect**.
- **Repositories** — each rep's findings scored independently, task score = mean over completed reps; 0.0 with zero completed reps.

**Determinism is mandatory.** Seed your randomness, avoid time-dependent branches. A flaky agent loses its own vote.

### 3.4 Behavioural tracks — clamped MCC

`BLOCK` or `WARN` on a malicious label = TP. `ALLOW` on a safe label = TN.

```
score = max(0, MCC)
MCC   = (TP·TN − FP·FN) / sqrt((TP+FP)(TP+FN)(TN+FP)(TN+FN))
```

Zero denominator is defined as MCC 0. Under that convention **every constant predictor sits at exactly 0** — the clamp sends constant, random, and inversely-correlated agents to zero while preserving ranking among real detectors.

> Worked example (30 tasks, 8 malicious / 22 safe): catch 6 of 8, wrongly flag 2 safe → TP 6, FN 2, FP 2, TN 20 → MCC = 116/176 = **0.659**.
> An agent answering `ALLOW` to everything → MCC **0**, score **0**.

### 3.5 Repositories — F-beta, β = 2

```
F2 = 5PR / (4P + R)        R = matched/planted    P = matched/reported
```

β=2 tilts toward **recall** — a missed real vulnerability costs more than a false flag.

A reported finding **matches** when it:
- names the same file (full path *or* a suffix of one), **and**
- agrees on the weakness — CWE numbers compared **numerically** (`CWE-79` == `CWE-079`), against the primary CWE *or* any entry in `all_cwes`; failing that, **≥34% title+description overlap**, **and**
- lands **within ten lines** of the planted finding.

> Worked example: 4 planted, 5 reported, 3 match → R = 0.75, P = 0.6, F2 = **0.714**.

### 3.6 Quality thresholds (frozen)

| Tracks | Metric | Threshold |
| --- | --- | --- |
| skills, mcp_servers, packages | clamped MCC | **0.20** |
| repositories | F2 | **0.50** |

### 3.7 Scores → weights

Per round, every validator:

1. Applies the track threshold, ranks eligible agents per track.
2. **Pays only the top three per track: 0.50 / 0.30 / 0.20** of that track's share. Ties broken by `sha256(round seeds : track : hotkey)` — unpredictable before the round, rotates between rounds, identical on every validator.
3. Splits **95% performance / 5% contribution** (the 5% divides equally among active agents from hotkeys with accepted corpus contributions).
4. Normalises over all miner UIDs. Each miner holds weight only in its own track.
5. Smooths: `w = 0.3·w_new + 0.7·w_prev` (EMA α 0.3).
6. Sets the vector on chain, once per round. **Commit-reveal is enabled** (period 1 tempo).

**Idle-track rule:** when a track has no qualifying agent, its share is **split equally among the tracks that do**. This is the single most exploitable line in the spec — see §6.

---

## 4. Live competition landscape (2026-08-19)

### Chain state

| | |
| --- | --- |
| Neurons | **256 / 256 — the subnet is FULL** |
| Registration | allowed; recycle currently ≈ τ0 (min_burn 0) |
| Immunity period | **100 blocks ≈ 20 minutes** |
| Tempo | 360 · commit-reveal on, period 1 |
| α price | τ0.002242074 = $0.4264 |
| α emission | 1.0 α/block ≈ 7,200 α/day ≈ $3,070/day total |

### Agent population (`/v1/agents`, 336 records all-time)

| Status | Count |
| --- | --- |
| active | 198 |
| **deregistered** | **136 (40%)** |
| withdrawn | 2 |

**40% of every agent ever submitted lost its UID.** With 256/256 full and a 20-minute immunity period, weak UIDs get pruned fast.

### Slots and qualification (current)

| Track | Slots used / 80 | Scored | Above threshold | **Earning** |
| --- | --- | --- | --- | --- |
| repositories | 37 | 30 | **9** | 3 |
| packages | 22 | pending | — | 3 |
| mcp_servers | **18** | **never scored** | — | 3 |
| skills | 19 | pending | — | 3 |

**96 eligible agents compete for at most 12 paying places.** ~87% of miners earn nothing.

### Round history (`/v1/rounds`, 24 records, 9 rounds)

| Round | repositories | packages | skills | mcp_servers |
| --- | --- | --- | --- | --- |
| 9 | 33 miners · 0.540/0.540/0.520 | 18 · **1.000/1.000/0.968** | 9 · 0.739/0.733/0.733 | — |
| 8 | 35 · 0.780/0.760/0.750 | 21 · 0.825/0.800/0.800 | 14 · 0.729/0.729/0.681 | — |
| 7 | 28 · 0.810/0.770/0.625 | 20 · 0.905/0.780/0.780 | 16 · 0.740/0.738/0.736 | — |
| 6 | 19 · 0.606/0.587/0.562 | 16 · **1.000**/0.951/0.800 | 17 · 0.558/0.542/0.535 | — |
| 5 | 29 · 0.375/0.375/0.375 | 37 · **1.000**/0.882/0.798 | 48 · 0.388/0.375/0.375 | — |
| 4 | 30 · 0.335/0.276/0.250 | — | 58 · 0.602/0.602/0.561 | — |
| 3 | 25 · 0.811/0.794/0.754 | 50 · 0.899/0.899/0.899 | — | — |
| 2 | 0 | — | 61 · 0.597/0.555/0.517 | — |
| 1 | — | 0 | 16 · 0.530/0.517/0.395 | 0 |

Validators grew 2 → **5**.

**Reading the table:**

- **`packages` is saturated.** Three agents at MCC 1.000 / 1.000 / 0.968. Perfect scores. You would have to tie a perfect agent and win a hash tiebreak. Avoid.
- **`repositories` is a knife fight at the threshold.** Round 9 top scores 0.540 / 0.540 / 0.520 against a **0.50** threshold. Currently 9 of 30 scored agents clear it, ranks 1–5 within 0.019 of each other. Tiny F2 movements decide everything, and the tiebreak hash rotates each round — so rank is partly luck at this compression.
- **`skills` bled out.** 61 miners in round 2 → **9** in round 9. Scores ~0.73. The exodus is the mechanism working as designed: only 3 of 61 earned, so 58 left.
- **`mcp_servers` has never produced a scored round.** 18 agents hold slots; exactly one has ever appeared in a round record (round 9), and none have ever been scored. Its 0.225 share has been idle for all 9 rounds.

> ⚠️ **Data caveat:** `/v1/leaderboard` returns only `repositories` rows and ignores the `?track=` parameter. `/v1/rounds` and `/v1/agents` disagree with it on population. Treat `/v1/agents` + `/v1/rounds` as authoritative. Also note **subnetalpha.ai publishes stale emission shares** (67.5/22.5/7.5/2.5) from an older mechanism version — the repo's `docs/mechanism.md` is the truth.

---

## 5. Miner economics

Assuming the standard dTAO split (41% of α emission to miners):

**Miner pool ≈ 2,952 α/day ≈ $1,259/day** across every earning miner on the subnet.

| Position | Weight share | α/day | USD/day |
| --- | --- | --- | --- |
| repositories rank 1 | 17.81% | 526 | **$224** |
| repositories rank 2 | 10.69% | 316 | $135 |
| repositories rank 3 | 7.13% | 211 | $90 |
| **solo qualifier in mcp_servers** | **21.37%** | **631** | **$269** |
| rank 4+ anywhere | 0% | 0 | **$0** |

### Costs

| Item | Cost |
| --- | --- |
| Registration burn | ~τ0 right now (moves with demand; 256/256 full) |
| Stake | **50 α ≈ $21** — staked to your own hotkey, never in subnet custody, withdrawable |
| Inference | **your own OpenRouter / Chutes spend**, metered per run |
| Hardware | a Linux box for local testing only |
| Ongoing | nothing — no server to keep online |

Entry cost is very low. **The risk is not money, it is that you place 4th and earn exactly zero forever.**

---

## 6. How to become a winner

### The structural opportunity: the idle-track rule

From `phylax/analysis/scoring.py:compute_emission_weights` — when a track has fewer than three qualifying agents, `split = TOP_K_SPLIT[:len(top)]` and `denom = sum(split)`. **A sole qualifying agent in a track takes that track's entire share.** And an idle track's share is redistributed to tracks that do qualify.

Computed against the current live state:

```
Today  (repos + packages + skills qualify, mcp_servers idle):
  repositories rank1 = 17.81%   packages rank1 = 15.44%   skills rank1 = 14.25%

You qualify ALONE in mcp_servers:
  mcp_servers rank1  = 21.37%   ← more than winning the biggest track outright
  (and everyone else's share drops, because your track stops being idle)

If mcp_servers fills to 3:
  rank1 = 10.69%   rank2 = 6.41%   rank3 = 4.28%
```

**Clearing MCC 0.20 alone in `mcp_servers` pays more than beating 33 competitors for rank 1 in `repositories`.**

⚠️ **The catch, stated honestly:** mcp_servers has never had a scored round in 9 rounds. Either the operator is not scheduling it, or its 18 parked agents all fail the threshold. Which one it is decides whether this is free money or a dead end — and the API data does not answer it. **This is cheap to test:** one registration, one agent, one round (2 days). Ask in Discord first.

### Track selection, ranked

1. **`mcp_servers`** — highest expected value if the track is live. Verify schedulability before committing.
2. **`skills`** — only 9 miners, scores ~0.73, and the emission share is identical to mcp_servers (0.225). The field thinned because most miners could not clear the bar, not because the track is closed. Best *confirmed-live* opportunity.
3. **`repositories`** — biggest share (0.30) but 37 agents and a 0.019 spread across ranks 1–5. You would be fighting for hundredths of an F2 point with a random tiebreak.
4. **`packages`** — **do not enter.** Three agents at MCC ≈ 1.0. There is no room above them.

### Winning the metric

**Repositories (F2, threshold 0.50):**
- β=2 weights recall 4× over precision. **Over-report rather than under-report** — a missed planted vuln costs far more than a false positive.
- Matching is generous and gameable in your favour: file may be a **path suffix**, CWE compared **numerically**, ±10-line tolerance, and a **34% title/description overlap** substitutes for a CWE match entirely. Emit a rich CWE list in `all_cwes` and descriptive titles to catch the overlap path.
- Nobody has broken 0.81 in 9 rounds. The metric has real headroom — this is a genuine engineering problem, not a saturated one.

**Behavioural tracks (clamped MCC, threshold 0.20):**
- **False positives are what kill you.** The docs' own worked example: the stock reference agent flags almost everything, scores TP 4 / FP 5, and lands at exactly **MCC 0.0000**. Being trigger-happy is mathematically identical to answering `ALLOW` to everything.
- Every constant predictor is exactly 0. You must actually discriminate.
- Thread the probe — write the file, resolve the host, echo the token. The validator copies the probe file out of the container and byte-compares it **from outside**. Skip it and the run is zero regardless of a correct verdict.
- Make at least one inference call. No call while the proxy is healthy = score 0.

**Universal:**
- **Determinism.** 2–3 reps must agree. Seed everything. No `time`, no unseeded randomness, no network-order dependence.
- **Stay under CPU budget.** cgroup-accounted, so a slow algorithm is a failed rep no matter what machine you tested on.
- Iterate locally against `phylax-corpus-data` — free, seconds, versus 2 days per on-chain round.
- Resubmit often (one version / 2 hours). Round-9 winners were at versions 15, 16, 27, 30 — **winners iterate hard**.

---

## 7. Rules you must keep

| Rule | Consequence of breaking it |
| --- | --- |
| One hotkey, one track, one active agent | Second-track submission refused `409` |
| Agent ≤ 256 KiB source; body ≤ 266,240 bytes | `422` (code) / `413` (body) |
| `agent_main(context)` must exist | Agent scores 0 for the round |
| Code hash must match at fetch | Agent scores 0 for the round |
| Code must differ from an active agent on the track | Rejected at upload (copied code = 0) |
| 50 α staked before registering a slot *and* before submitting | Rejected at upload |
| One version per 2 hours | Rejected at upload |
| Reachable inference path | Rejected at upload |
| Submit before the round's submission window closes | Competes next round instead |
| Thread the liveness probe (behavioural tracks) | That rep fails |
| Make an inference call | Score 0 (`inference_key_failed` on 401/402/403/429) |
| Stay in CPU + wall + memory budget | That rep fails |
| Return well-formed output | That rep fails |
| Use canonical capability taxonomy names | Non-canonical capabilities silently **dropped** |
| Score ≥ threshold at least once per 6 rounds | **Slot evicted** |

**Failure principle:** *a fault of the agent scores zero deterministically; a fault of the infrastructure abstains.* Infrastructure faults (sandbox image unavailable, artifact fetch failure, proxy unreachable, any track incomplete at window close) make the **validator abstain entirely** — it sets no weights and its EMA state is untouched. A partial vector is never submitted.

**Screening reads executable code only**, not comments or docs. Hostile behaviour is rejected at upload.

---

## 8. Device / hardware conditions

**For mining: essentially nothing.** Validators own the runtime.

| | Miner | Validator |
| --- | --- | --- |
| Machine | a Linux host for local testing | **16 vCPU, 32 GB RAM, 100 GB disk** (floor spec) |
| Neuron process | **none** | continuous |
| Container image | **none — you ship no image** | Docker, fails closed |
| Public IP / axon | **none** | — |
| Uptime | **none** | full round window (30 h) |
| GPU | none | none |
| Python | 3.10+ | 3.10+ |

Your agent runs inside the validator's jail: **2 GB memory (swap disabled), 1 CPU, 256 pids, tmpfs `/tmp`**, non-root, `cap-drop=ALL`, `no-new-privileges`, internal network with no internet. Agent code enters by **copy, not bind mount**.

⚠️ **Local corpus warning:** `phylax-corpus-data` contains **real malware** — a compromised node-ipc build, a Discord token stealer. Your antivirus will flag the checkout. **Unpack and run it inside a container or VM**, never on your host.

> **Note for this operator:** unlike SN66, the *mining* side of Phylax has no hardware demand at all — nothing runs continuously and nothing needs to be online. The only local requirement is a throwaway Linux box (ideally a VM) to run `evaluate_local.py` against the malware corpus. That must **not** be the BEAM orchestrator at 46.225.140.58 — not for CPU reasons but because you would be unpacking live malware onto the box running the miner.

---

## 9. Third-party conditions

| Dependency | Detail | Risk |
| --- | --- | --- |
| **Inference API key** | **Mandatory.** `cpk_` (Chutes) or `sk-or-` (OpenRouter) — hard-coded prefix check in `phylax/harness/inference_proxy.py:53-56`. No other provider is accepted. | You fund your agent's inference. Key rejected upstream (401/402/403/429) → **score 0** for the round. Keep it funded. |
| **Phylax backend** | `https://api.phyi.dev` — holds your code, schedules rounds. Identity pinned via `PHYLAX_SERVER_HOTKEY` so the client refuses an impersonator. | Centralised. If it is down you cannot submit. It is "a clock and a ledger, not a judge" — but it *does* gate submissions. |
| **Corpus repo** | `praxi-labs/phylax-corpus-data` (git-lfs) | Local only. **Not** the scoring corpus — round ground truth is never served to anyone. |
| **Docker** | Validators only | — |
| **Bittensor** | `btcli` for wallet + registration | — |

Provider split across all 336 agents: **openrouter 309, chutes 27**.

Your key is uploaded to the backend with your code and metered through **the validator's** proxy — every LLM call carries a per-agent, per-task nonce, so one agent's activity can never vouch for another's.

---

## 10. Risks

1. **Top-3-only.** 96 eligible agents, ≤12 paying seats. Rank 4 earns exactly the same as rank 80: zero. This is the defining risk.
2. **The subnet is full (256/256) with a 20-minute immunity period.** 136 of 336 agents — 40% — have already been deregistered. You can lose your UID before your first round is even scored.
3. **Score compression in repositories.** Ranks 1–5 within 0.019 F2. At that spread the `sha256` tiebreak — which rotates every round — is effectively deciding who gets paid.
4. **Packages is closed.** MCC 1.000 at rank 1 and 2. Nothing to win.
5. **mcp_servers may be dormant.** Never scored in 9 rounds. The arbitrage in §6 is contingent on the operator actually scheduling it.
6. **Centralised control plane.** The operator opens rounds, sets slot caps, and publishes the contributor set. "Tunable with notice" covers round length, slot caps, EMA α, and commit-reveal.
7. **Ongoing inference cost with no floor on return.** You pay per round whether or not you place.
8. **You upload an API key** to a third-party backend.

---

## 11. Verdict

Phylax is a **genuine competitive-ML subnet** and the structural opposite of SN66:

| | SN66 Conjectures | SN76 Phylax |
| --- | --- | --- |
| Work | human writes Lean proofs | you write a detector program |
| Emissions to miners | **none** — 100% to treasury UID 121 | **yes** — normal Yuma consensus |
| Cost to try | $95 per attempt | ~$21 stake + inference |
| Income | one-off bounty | continuous, every 2 days |
| Scales with skill | no | **yes** |
| Automatable | no | **yes** |
| Hardware | 8 GB build box | none for mining |

The entry cost is genuinely low and there is **no infrastructure to run** — which means it does not compete with BEAM for machine resources at all. That makes it a far better fit than SN66 for running alongside an existing operation.

The bar is real, though: this is a security-engineering problem, not an ops problem. Nothing from the CX23 playbook (fleet sizing, queue depth, deadline budgets) transfers. What transfers is the discipline of **measuring against a metric and iterating** — and here the metric is published, frozen, and testable locally in seconds.

**Recommended path:**
1. Ask in Discord whether `mcp_servers` rounds are being scheduled. That single answer is worth more than any other research.
2. If yes → build for `mcp_servers`, the solo-qualifier position pays 21.37%.
3. If no → build for `skills`. Same 0.225 share, only 9 competitors, scores ~0.73 and clearly beatable.
4. Either way, iterate locally against `phylax-corpus-data` **in a VM** until you clear the threshold with margin. Do not register until then — a UID on a full subnet with 20-minute immunity is not something to hold idle.
5. Never enter `packages`.

---

*Sources: local checkout of `praxi-labs/phylax-subnet` (`docs/mechanism.md`, `docs/miner_setup.md`, `docs/agent_contract.md`, `docs/local_testing.md`, `phylax/analysis/scoring.py`, `phylax/harness/inference_proxy.py`, `.env.example`); live `api.phyi.dev` `/v1/agents`, `/v1/rounds`, `/v1/leaderboard`; live finney chain state for netuid 76; docs.phyi.dev.*
