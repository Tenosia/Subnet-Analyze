# SN92 — MicroTensor (Certified Inference Systems)

| | |
|---|---|
| **netuid** | 92 (`MicroTensor`, symbol `ᚂ`) |
| **Chain description** | *"A model factory and deployment layer for verified specialist AI"* |
| **Owner hotkey** | `5FeHbWK12HHMLY4AtnWkKk8jtQajhQZMLCenGd96Hhs4UJGc` — **UID 0** (also the coordinator hotkey) |
| **Owner coldkey** | `5E9LPDS2E5RFzoqRsF2D7NgJTFH3N2DVqeAodTksPJP7CT4x` |
| **Code** | https://github.com/microtensor-io/microtensor-subnet — **public, MIT** |
| **Local checkout** | `/root/Bittensor/92/microtensor-subnet` |
| **Version** | release `0.3.2`, mechanism `0.3.0` |
| **Sites** | https://microtensor.vercel.app · dashboard https://microtensor.cloud · **API `https://api.microtensor.cloud` (live)** |
| **Registered at block** | 8,352,006 |
| **Live state (2026-09-03, block 8,983,665)** | round **1238** (`code`) / **1237** (`extract`) |
| **Price** | 0.004172 TAO/ᚂ (**≈ $1.068**) · tao_in τ1,037.63 · alpha_in 244,141 · alpha_out 566,068 |
| **UIDs** | 256 registered · **9 earning** · 9 permits · 6 with dividends |
| **On-chain commitments** | **59**, all in the live `mt1|…` format |
| **Registration cost** | **0.10 TAO** (~$25.60) |
| **Owner miner incentive** | **0.0000** — the owner takes **no** miner emission |

> This is the healthiest live subnet in my series so far: nine miners genuinely
> earning, a real distribution of shares, an owner taking zero miner emission,
> and a public API that reproduces the leaderboard. It also has the **largest
> gap between its documentation and its live configuration** — including which
> track pays. Details in §11.

---

## 1. Goal of the subnet — the plain version

Frontier-quality AI is often unusable where it's needed: too expensive at volume,
too slow for interactive use, or simply not allowed to leave the building.

The standard fix is a **cascade**: a small, cheap specialist model answers most
queries, and a "router" decides when a question is too hard and escalates it to a
bigger model. The cost of that whole arrangement is:

```
C  =  c_front  +  (1 − ρ) · c_specialist
```

where `ρ` is the fraction the small front model resolves by itself.

Here's the problem MicroTensor exists to solve: **you cannot know `ρ`, or the
real end-to-end quality, or the real memory footprint, from any component's
published spec sheet.** Those are properties of the assembled system running on
specific hardware. So somebody has to actually build the thing and measure it.

That's the subnet. Miners build compact specialist systems; the network runs them
on its own certified hardware and publishes a **signed certificate** saying:
*this exact artifact, on this hardware envelope, achieves this quality at this
cost.*

The framing the repo uses is worth quoting because it's the honest distinction:

> Established evaluation ranks single frozen models against a quality metric…
> Microtensor supplies the complementary instrument: it measures **assembled
> systems** on the hardware they will run on.

Three properties make the certificate mean something:

1. **The network holds the weights and runs them.** The miner is *absent* at
   scoring time and supplies no measurements of its own.
2. **Scoring is deterministic** — greedy decoding, temperature 0, pinned engine.
   Two validators must get identical numbers, so a disagreement is a bug to
   attribute, not variance to tolerate.
3. **The task set is unobservable in advance** — seeded from the hash of the
   block at which submissions close.

---

## 2. What you do as a miner

**You train a model offline, upload it, and post a 128-byte pointer on chain.
That is the entire job.** You never serve traffic. You have no uptime
requirement. You come online once per round, send one extrinsic, and go back to
training.

### The three components

A submission is a **system** `S = (front, router, specialist)`:

| Component | What it does | Cost weight |
|---|---|---|
| **front** | The compact model that runs on **every** query | full |
| **router** | Decides "can the front handle this?" — **data, never code** (a threshold table or small ONNX graph) | counts against the front's envelope |
| **specialist** | The bigger model that handles escalations | weighted by `(1 − ρ)` |

**A system with only a front is completely valid** — it reduces to the
single-model case, which is how most of the network runs today.

### What you actually upload

```
my-model/
├── model.onnx        # or GGUF — the entrypoint named in your manifest
└── tokenizer.json
```

Plus a **manifest** (a *declaration*, not a program) and a **declared envelope**
`(size, peak memory, p95 latency)`.

> **No miner-authored code ever runs on validator hardware.** The validator
> supplies the engine. This is the safest posture of any subnet in my series, and
> the repo states the cost plainly: your architecture is bounded to what the
> engine implements.

### The workflow

```bash
pip install .                     # CLI only: 2 cores, 4 GB, no GPU
pip install ".[validator]"        # adds the runtime so you can selfcheck

btcli subnet register --netuid 92 --wallet.name <ck> --wallet.hotkey <hk>

# ... train offline — this is the real work ...

mt miner package        # writes manifest.json, computes the artifact digest
mt miner selfcheck      # measures your envelope with a 10 % margin
mt miner upload         # host it (Hugging Face in practice)
mt miner publish        # the 128-byte on-chain pointer
```

### The on-chain commitment

Real ones, read from finney today:

```
mt1|1238|code|mt-3g|f328df081dc641540e2c2a87c34f7a86|hf:Samonte/rabi-coder-mt3@c0de1238
mt1|1237|extract|mt-3g|478ba6a78121a6163f5f134e82c5cc9a|https:huggingface.co/RealMiner/mt-extract/...
    ^    ^      ^       ^          ^                        ^
   ver  round  track   class    digest                    artifact URI
```

### Timing

| | |
|---|---|
| `ROUND_BLOCKS` | 21,600 (**72 h at 12 s/block** — note the README says "settles daily", see §11) |
| Submission window | `[start, close)` |
| Evaluation window | 560 blocks (~2 h) after close |
| **Seed** | `H(hash(B_close) ‖ track ‖ class)` — drawn from the **close** block |
| Submissions per hotkey | 1 per **6 hours** |
| Slots per (track, class) | **40**; evicted after 6 rounds below threshold |

The seed being drawn from the *close* block is the key anti-gaming property: you
cannot see the task draw while submissions are open, but anyone can reproduce it
the moment they close.

---

## 3. Scoring logic

There are three stages, and they run in this order.

### Stage 1 — Admission is binary

```
admissible ⇔ measured ≤ declared ≤ class ceiling
             for size, memory, and latency, on every component
```

Two separate ways to fail:

- **Over the class ceiling** → doesn't fit the hardware.
- **Within the ceiling but over your own declaration** → *"a false certificate is
  worse than no certificate."*

**Why honest declaration is the optimal strategy** — and this is a genuinely
elegant bit of design: no term of the score depends on your declaration. Declare
too low and you fail the gate entirely (total loss). Declare too high and you
pass, but you've written a pessimistic number into a public certificate, and
deployers pick the tighter guarantee (bounded loss). So the optimum is
`m̂* = m + z·ς` — **the truth plus a defensible margin**, which is exactly the
number a buyer needs.

Tolerances apply to *your declaration only*, never to the ceiling: 2 % on size and
memory, max(10 %, 15 ms) on latency.

### Stage 2 — Quality

```
A(a) = (1/|T|) · Σ q(a,t)      averaged over EVERY task
Σ(a) = g(a) · A(a)             gate, then rank
```

**Omission is never free.** A task you fail, refuse, or time out on scores zero
and stays in the denominator. You cannot inflate your score by attempting only
the easy ones.

The repo explicitly rejects the obvious composite alternative
(`A/P × 1/ℓ × 1/m̂`) on four grounds — unboundedness, substitutability, gradient
misdirection ("the formula instructs the network to produce very small models
that do not work"), and dimensional incoherence. Gate-then-rank instead maps onto
the question a buyer actually asks: **does it fit, and how good is it.**

### Stage 3 — Emission follows the *frontier*, not a rank

This is the part that decides your income, and it is unlike every other subnet in
my series.

Systems are plotted on the **cost–quality plane**. The non-dominated set is the
**frontier**. Your emission is proportional to your **exclusive hypervolume** —
how much area the frontier *loses* if you weren't there:

```
E(S)  ∝  HV(frontier)  −  HV(frontier without S)
```

Both coordinates are quantised to an integer grid (`HV_QUANT_Q = HV_QUANT_C =
10,000`) so frontier membership is **bitwise identical** across validators.

Two systems inside one epsilon-neighbourhood (`EPS_QUALITY = 0.005`,
`EPS_COST = 0.01`) **collapse to the earlier commitment** — the later one added
nothing.

Within a system, each component is priced by **role-baseline ablation**:

```
φ(component) = V(system) − V(system with component → published role baseline)
```

A component the system doesn't need measures **zero** and earns nothing.

### Stage 4 — Score to weight

| Mechanism | Value | Purpose |
|---|---|---|
| Track threshold `τ` | **0.20** | below this you don't score |
| `MIN_ROUNDS_OBSERVED` | **2** | *"unknown is not the same as good"* |
| Paid ranks `K` | **8** | geometric schedule `α_j = (1−γ)γ^(j−1)/(1−γ^K)` |
| Rank decay `γ` | **0.85** | rank 8 still earns ~⅓ of rank 1 |
| **Hysteresis `ε`** | **0.005** at *every* rank boundary | anti-copying |
| Incumbent decay `δ` | **0.05** per round without material improvement | anti-stagnation |
| **Concentration cap** | **0.25** per **coldkey** | one operator can't take a whole track |
| Asymmetric smoothing | `DECAY_RATE 0.40` vs `RECOVERY_RATE 0.10` | regressions punished fast, recovery earned |

The hysteresis reasoning is explicitly a response to SN9's documented
winner-take-all hoarding: applying `ε` at *every* boundary, not just rank 1,
removes the return on "copy the leader and land second" — *"a stronger defence
than detection because it operates before the copy is made."*

---

## 4. Live competition landscape

### 4.1 Two arenas — and the docs name the wrong one

From the live API (`GET /v1/arenas`):

| Arena | Emission share | Ceilings (size / RSS / p95) | Metric | Submitted → admitted | Frontier | Best quality | Cheapest |
|---|---|---|---|---|---|---|---|
| `code` / `mt-3g` | **0.0** | 1.5 GiB / 3 GiB / **45,000 ms** | pass@1 (greedy) | 49 → **32** | 3 | 0.5371 | 2,742 ms |
| **`extract` / `mt-3g`** | **1.0** | 1.5 GiB / 3 GiB / **15,000 ms** | entity micro-F1 (exact) | 23 → **23** | **8** | **0.9672** | 1,351 ms |

**The `extract` track carries 100 % of emission share and is not in the
documented track table at all** (the docs list `code` as the only enabled track,
at share 1.00). See §11.

Per-arena config also differs sharply: `code` draws **15 tasks/round** at 480 CPU-s
per artifact; `extract` draws **200 tasks/round** at 6,000 CPU-s.

**Allowed base models (live):**
- `code`: Qwen2.5-Coder-0.5B/1.5B-Instruct, Qwen3-0.6B, Qwen3-1.7B
- `extract`: Qwen3-0.6B, Qwen3-1.7B

### 4.2 The leaderboard — and the single most important lesson

Round 1237, `extract` (the arena that pays):

| rank | quality | ms/query | **share** | UID | chain incentive |
|---|---|---|---|---|---|
| **1** | 0.9526 | **3,550** | **70.73 %** | 10 | 0.0400 |
| 2 | 0.4677 | **1,351** ← cheapest | **12.75 %** | 4 | 0.0000 |
| 3 | 0.8475 | 2,203 | 7.34 % | 21 | 0.0000 |
| 4 | 0.7294 | 1,797 | 7.28 % | 234 | 0.0000 |
| 5 | 0.5501 | 1,589 | 0.59 % | 235 | 0.0000 |
| **6** | **0.9672** ← **best quality** | 9,690 | **0.52 %** | 23 | 0.0888 |
| 7 | 0.8520 | 2,746 | 0.41 % | 236 | 0.0000 |
| 8 | 0.5729 | 1,652 | 0.38 % | 203 | 0.0179 |

> ### 🔑 **Being the most accurate does not win.**
>
> Rank 6 has the **highest quality on the board (0.9672)** and earns **0.52 %**.
> Rank 1 has *slightly lower* quality (0.9526) at **less than half the latency**,
> and earns **70.73 %** — 136× more.
>
> Meanwhile rank 2, with mediocre quality (0.4677), earns **12.75 %** purely for
> owning the **cheapest corner** of the frontier that nobody else covers.
>
> This is the hypervolume mechanism working exactly as designed. Rank 6 is
> *dominated* — rank 1 is better on quality *and* cost — so it covers almost no
> exclusive area. Rank 2 is dominated by nobody on cost, so it owns real ground.

The same lesson in `code` round 1236: the miner with **quality 1.0000** (a perfect
score, 7,485 ms) earned **19.70 %**, while a miner at 0.8280 quality and 5,356 ms
earned **80.30 %**.

### 4.3 On-chain emission

Nine UIDs earning, with a real distribution:

| UID | incentive | α/day | $/day | $/mo |
|---|---|---|---|---|
| 38 | 0.2681 | 791 | **$845** | ~$25,400 |
| 42 | 0.1787 | 528 | $564 | ~$16,900 |
| 30 | 0.1577 | 466 | $497 | ~$14,900 |
| 26 | 0.1243 | 367 | $392 | ~$11,800 |
| 23 | 0.0888 | 262 | $280 | ~$8,400 |
| 7 | 0.0711 | 210 | $224 | ~$6,700 |
| 37 | 0.0533 | 157 | $168 | ~$5,000 |
| 10 | 0.0400 | 118 | $126 | ~$3,800 |
| 203 | 0.0179 | 53 | $56 | ~$1,700 |

**UID 0 (the owner) has incentive `0.0000`** — it takes no miner emission at all.
That is the first time I've seen this in the series.

⚠️ **A discrepancy worth noting:** the API says `code` has emission share **0.0**,
yet the three highest on-chain incentives (UIDs 38, 42, 26) are all `code` round-1238
certificate holders, while most ranked `extract` miners hold **zero** incentive.
Weights are EMA-smoothed (`EMA_ALPHA 0.30`) and gated by `MIN_ROUNDS_OBSERVED = 2`,
which explains part of it — new `extract` entrants haven't accrued enough rounds.
But it does not explain `code` paying at all if its share is truly zero. The most
likely reading is that the API's `emission_share` is a **forward-looking governance
value** the on-chain weights have not yet caught up to. **I could not confirm that
from public data and am flagging it rather than guessing.**

---

## 5. Miner economics

Subnet emits **1.000 α/block = 7,200 α/day**; 18 % owner cut, 41 % miners, 41 %
validator dividends → **miner pool = 2,952 α/day**.

At α = 0.004172 TAO and TAO ≈ $256 → **α ≈ $1.068** → miner pool ≈ **$3,153/day**.

| | |
|---|---|
| Top miner today | **$845/day** (~$25,400/mo) |
| Rank 8 of the paid cohort | ~$56–168/day |
| Rank 8 vs rank 1 (by schedule) | **~⅓** — the tail is genuinely worth competing for |
| **Owner capture** | 18 % cut + 52.7 % of dividends = 2,851 α/day ≈ **$3,045/day = 39.6 % of emission** — and **0 % of the miner pool** |

### Costs

| Item | Cost |
|---|---|
| Registration | **0.10 TAO ≈ $25.60** |
| **Training GPU** | RTX 3090 24 GB floor / 4090 24 GB / 5090 32 GB. **NVIDIA only** |
| Training host | 8 cores, 32 GB RAM, 500 GB SSD |
| Running the CLI | 2 cores, 4 GB, **no GPU** |
| `mt miner selfcheck` | ~5 GB RAM for `mt-3g`, **no GPU** (engine is CPU-only) |
| Uptime | **Not required** — online once per round |
| Hosting | Hugging Face in practice, free |

**This is a favourable cost structure.** The only real expense is a single
consumer GPU you already own or rent by the hour, and you burn it on training
rather than on serving. Compare with SN90 ($1.5M–4M of datacenter) or SN58
($25k of trading capital at risk).

---

## 6. How to become a winner

The mechanism is public, deterministic, and the entire leaderboard is queryable.
That makes this one of the few subnets where strategy can be reasoned about
precisely rather than guessed.

### Priority 1 — Compete in `extract`, not `code`.

`extract` carries **emission share 1.0**; `code` carries **0.0**. The docs say
the opposite. Trust the live API (`GET /v1/arenas`) over `docs/mechanism.md`, and
confirm with the operator before committing training time — this is the single
highest-stakes fact in the subnet and it is mis-documented.

`extract` is also the friendlier arena on the numbers: **23 of 23 submissions were
admitted** (versus 32 of 49 in `code`), so the envelope is not what's eliminating
people there.

### Priority 2 — Find an empty corner of the frontier. Do not chase peak accuracy.

This is the whole game, and §4.2 is the proof. Your income is **exclusive
hypervolume**, not rank on a quality list.

Plot the current frontier before you train anything:

```bash
curl -s https://api.microtensor.cloud/v1/certificates | python3 -m json.tool
```

From round 1237, the occupied points on `extract` are roughly:

```
quality
 0.97 ┤                                        ● rank 6  (0.52 % — dominated)
 0.95 ┤        ● rank 1  (70.7 %)
 0.85 ┤     ● rank 3 / rank 7
 0.73 ┤   ● rank 4
 0.57 ┤  ● rank 8
 0.47 ┤ ● rank 2  (12.7 % — owns the cheap corner)
      └──┴────┴──────┴───────────────────────────── ms/query
       1351  1797   2203   2746        3550      9690
```

Two structurally profitable targets:

- **Below 1,351 ms at any usable quality.** Nobody occupies that region. Rank 2
  earns 12.75 % with quality 0.4677 simply for being cheapest — a system at, say,
  900 ms and 0.50 quality would take that corner outright.
- **Above 0.9526 quality at under 3,550 ms.** That directly attacks the 70.7 %
  position. Note you must clear it by `ε = 0.005` in quality or `0.01` in cost —
  epsilon-neighbours collapse to whoever committed *first*.

What is *not* worth doing: another point at ~0.85 quality / ~2,200 ms. Ranks 3 and
7 are already stacked there and both earn under 8 %.

### Priority 3 — Optimise latency as hard as you optimise accuracy.

Cost is one of two frontier axes and it is the one most miners under-serve. The
`extract` p95 ceiling is **15,000 ms**, which is enormous — so the ceiling is not
binding and latency is purely a *competitive* axis, not an admission one. Rank 1's
advantage over rank 6 is almost entirely speed.

Practical levers: aggressive quantisation (GGUF Q4), a smaller base (Qwen3-0.6B
rather than 1.7B), shorter generation, and cutting tokenizer/preprocessor overhead
— remember **size is total**, every file in the directory counts.

### Priority 4 — Declare your envelope honestly, with a small margin.

`mt miner selfcheck` computes exactly the right number (measured + 10 %). Under-declaring
is fatal (inadmissible, score zero); over-declaring costs you commercial selection
and nothing else. Run it before every submission — in `code`, **17 of 49 submissions
(35 %) failed admission**.

### Priority 5 — Use the free training data and reference completions.

```bash
curl https://api.microtensor.cloud/v1/corpora/<corpus-version>/public
```

This returns the train split **plus one vetted reference completion per task**,
with `reference_model` naming what produced them. **You can distil from a larger
model without ever running one.** That is a substantial free head start and most
newcomers won't read far enough into `miner_setup.md` to find it.

### Priority 6 — Publish a training run, or you are rejected at discovery.

W&B, `entity="microtensor"`, `project="training-runs"`, `name="<your-hotkey-ss58>"`,
carrying the artifact digest. Order matters: **package → log the digest → ship.**
The repo is honest that this is *"a timestamped record, not a proof of
computation"* — it raises the cost of appropriation, nothing more.

> Note `PROVENANCE_REQUIRED` is currently `False` in `constants.py` while the docs
> call it mandatory. Do it anyway — it costs nothing and the flag can flip.

### Priority 7 — Understand the anti-copy and anti-stagnation machinery.

- **Hysteresis `ε = 0.005` at every rank boundary** — copying the leader and
  landing beside them earns you nothing.
- **Epsilon-collapse** — a system inside one ε-neighbourhood of an existing one
  collapses to the *earlier* commitment. Being second to the same idea is worth zero.
- **Incumbent decay 5 %/round** without material improvement — if you take a
  position, keep improving it.
- **Concentration cap 25 % per coldkey** — a slate of hotkeys under one coldkey
  gets zeroed lowest-first. Don't bother.
- **`MIN_ROUNDS_OBSERVED = 2`** — you earn nothing for your first rounds. Budget
  for it; most zero-incentive `extract` miners in §4.3 are simply new.

### The path

1. `GET /v1/arenas` and `/v1/certificates`; confirm with the operator that
   `extract` is the paying track.
2. Register (0.10 TAO ≈ $25.60). Slots are capped at 40 per arena — `extract` has
   23 systems, so there is room now.
3. Pull the public corpus with reference completions; distil into Qwen3-0.6B.
4. Export to ONNX/GGUF, `mt miner package`, `mt miner selfcheck`.
5. **Aim at an unoccupied frontier corner** — cheapest, or above 0.9526 quality
   under 3,550 ms. Not the middle.
6. Log the W&B run with the digest, upload, `mt miner publish`.
7. Iterate: cost axis first, then quality.

---

## 7. Rules you must keep

| Rule | Consequence if broken |
|---|---|
| `measured ≤ declared ≤ class ceiling` on size, RSS, p95 | **Inadmissible — scores zero, does not exist for the round** |
| Base model from the live allowlist, declared `<repo>@<sha>` | Rejected |
| ONNX opset 13–21 (standard domains) or GGUF v2–v3 | Rejected — `safetensors` has **no engine** |
| No custom operators | Rejected — *"a validator will not run code it cannot audit"* |
| Size is **total** (weights + tokenizer + config + everything) | Over-ceiling → inadmissible |
| Router must be **data**, not code; ≤ 4 MiB; allowlisted ops/features | Rejected |
| Publish a resolvable W&B training run bound to the digest | Rejected at discovery |
| Manifest ≤ 64 KiB | Rejected by the submission API |
| 1 submission per hotkey per **6 hours** | Refused |
| Clear the incumbent by `ε = 0.005` | You don't take the rank |
| Don't land inside an ε-neighbourhood of an existing system | **Collapses to the earlier commitment — you earn zero** |
| Score above track threshold `τ = 0.20` | Below → no score; 6 consecutive rounds → **slot evicted** |
| One coldkey ≤ 25 % of the paid cohort | Excess zeroed lowest-first |
| Greedy decoding, temperature 0 | Fixed by the track — not a knob |

---

## 8. Device conditions

### Miner

| | Requirement |
|---|---|
| **Training GPU** | RTX 3090 24 GB **floor**; RTX 4090 24 GB / 5090 32 GB recommended |
| **Vendor** | **NVIDIA only** — `bitsandbytes` and `unsloth` require CUDA. AMD, Apple Silicon and Intel **will not run the stack** |
| Training host | 8 cores, 32 GB RAM, 500 GB SSD |
| Toolchain | **Unsloth** (60–70 % less VRAM, 2–5× faster) + bitsandbytes |
| Running the CLI | **2 cores, 4 GB RAM, no GPU, 50 GB disk** |
| `mt miner selfcheck` | RAM above the class ceiling — **5 GB for `mt-3g`**; still no GPU |
| **Uptime** | **Not required.** Online once per round for one extrinsic |
| `min_compute` enforced? | **No** — `enforced: false` for miners |

### Validator

| | Requirement |
|---|---|
| OS | **Linux** — the jail needs `resource.setrlimit`; refuses to start elsewhere |
| CPU | 8 cores |
| RAM | 32 GB |
| Disk | **1 TB NVMe** (cap 2 TB) |
| **GPU** | **None** — *"the engine runs on CPUExecutionProvider. Validation is deliberately cheap so that validating is not a capital barrier."* |
| Network | 1 Gbps, **500–1,000 GB/month** (a full round pulls every submission) |
| Uptime | **Required** — continuous neuron |
| Stake | `MIN_VALIDATOR_STAKE = 1,000` α |
| Reference bench | One certified device per class served (`mt-3g` at launch) |
| `min_compute` enforced? | **Yes** |

> **Against your BEAM box (2 cores / 3.7 GB):** it can run the **miner CLI**
> end-to-end — `init`, `package`, `upload`, `publish` all fit in 2 cores / 4 GB.
> It cannot run `selfcheck` (needs ~5 GB) and cannot train. It cannot validate
> (8 cores / 32 GB / 1 TB NVMe). **So the box is a usable submission host; the
> training GPU has to live elsewhere.** That's a better fit than SN90 or SN58.

---

## 9. Third-party conditions

| Dependency | Role | Failure mode |
|---|---|---|
| **`api.microtensor.cloud`** | Coordinator / control plane: corpus, arenas, certificates, submission API | Operator-run. **Hidden test partitions live here and are served only to validators.** Public read endpoints work today (`/health` → `{"status":"ok","plane":"edge"}`) |
| **Coordinator hotkey** | `5FeHbWK12HHMLY4Atn…` = **the owner's hotkey** | The control plane is the owner. Replication 3, quorum 0.67 |
| **Hugging Face** | Artifact hosting (`hf:` and `https:huggingface.co/…` URIs), base models, role baselines | Miner-chosen; an unfetchable artifact simply doesn't score |
| **Pinned base models** | Qwen2.5-Coder-0.5B/1.5B-Instruct, Qwen3-0.6B/1.7B — by exact SHA | Off-allowlist → rejected |
| **Weights & Biases** | `microtensor/training-runs` provenance | Required by docs for admission (`PROVENANCE_REQUIRED` is `False` in code today) |
| **ONNX Runtime / GGUF engine** | The execution engine, CPU-only | Consensus-critical: `environment_digest` (`env:a9b6b17587d8aaea`) pins it |
| **Unsloth / bitsandbytes** | Recommended training stack | CUDA-only — hard vendor lock for miners |
| **finney** | Registration, 128-byte commitments, weights | `MAX_COMMITMENT_BYTES = 128` shapes the pointer format |
| **GitHub releases** | Signed auto-update channel (`stable` / `prerelease`) | Ed25519-signed; `mt update` polls every 300 s |

Notably **absent**: no TEE, no trusted hardware, no model-as-judge, no closed
scoring service. Every enabled metric is *computed, not judged* — the repo makes
that the admission criterion for a track.

---

## 10. Risks

1. **The documentation names the wrong paying track.** Docs say `code` is the only
   enabled track at share 1.00; the live API says `code = 0.0` and `extract = 1.0`,
   and `extract` isn't in the documented track table at all. A miner who follows
   the docs trains for the wrong arena.

2. **On-chain incentive doesn't match the published emission shares.** The three
   highest incentives are `code` miners despite `code` showing 0.0 share.
   EMA smoothing and `MIN_ROUNDS_OBSERVED` explain part of it; not all of it.

3. **The control plane is the owner, and it holds the hidden tests.** The corpus's
   `fixed` and `rotating` partitions and every hidden test are served only to
   validators by `api.microtensor.cloud`, whose hotkey is the owner's. The
   determinism guarantees are strong, but the *task supply* is centralised.

4. **Live parameters are far from the committed constants.** `TASKS_PER_ROUND` 200
   in code vs 15 live for `code`; `CPU_SECONDS_PER_ARTIFACT` 12,000 vs 480; p95
   ceiling 180 ms documented vs 45,000/15,000 ms live. The mechanism is tunable by
   design, but nothing in the repo tells you the current values — only the API does.

5. **`code` admission is brutal: 17 of 49 submissions (35 %) failed the gate.**
   `extract` admitted 23 of 23, so this is arena-specific, but the envelope gate is
   real and unforgiving.

6. **The engine bounds your architecture.** ONNX opset 13–21 standard domains, or
   GGUF v2–v3. No custom operators. `safetensors` has no engine. Anything clever
   that doesn't export cleanly is simply unavailable to you.

7. **NVIDIA-only training.** Stated as a hard requirement, not a preference.

8. **A 3-day round is slow feedback**, and `MIN_ROUNDS_OBSERVED = 2` means roughly
   **six days before a new artifact can hold any weight.**

9. **Epsilon-collapse punishes independent rediscovery.** If you land inside an
   ε-neighbourhood of an existing system you collapse into it and earn zero — even
   if you got there honestly and independently.

10. **Owner takes 39.6 % of emission** via the 18 % cut plus 52.7 % of validator
    dividends. Lower than every other subnet in the series, and notably **0 % of
    the miner pool** — but the dividend concentration is still substantial.

11. **`code` may be a stranded asset.** 49 submissions and 32 admitted systems sit
    in an arena the API says pays nothing. If that share is real and permanent,
    that work is unpaid.

12. **Thin alpha liquidity.** 244,141 α in the pool against τ1,038; the top miner
    mints 791 α/day ≈ 0.32 % of depth per day. Manageable, but `subnet_volume` is
    only 74,215 α.

---

## 11. Documentation defects found

The code and prose are internally consistent; the gap is between **both of them
and the live network**.

| Claim | Where | Live reality |
|---|---|---|
| `code` is the only enabled track, emission share **1.00** | `docs/mechanism.md` §2, `miner_setup.md` §1, `CLASS_WEIGHTS` | **`code` = 0.0, `extract` = 1.0** |
| The track table lists code / document / analytics / support / detect / vqa / speech / video / image-synth | `docs/mechanism.md` §2 | The paying track is called **`extract`** and appears nowhere in that list (likely `document` renamed) |
| `mt-3g` p95 ceiling **180 ms** | mechanism §2, `min_compute.yml`, `miner_setup.md` | **45,000 ms** (`code`) / **15,000 ms** (`extract`) — 83–250× larger |
| `TASKS_PER_ROUND = 200` | `constants.py:88` | 15 for `code`, 200 for `extract` |
| `CPU_SECONDS_PER_ARTIFACT = 12_000` | `constants.py:91` | 480 for `code`, 6,000 for `extract` |
| Base models "Qwen3 (0.6B, 1.7B, 4B) and Llama 3.2 (1B, 3B)" | `miner_setup.md` §5 | Qwen2.5-Coder-0.5B/1.5B + Qwen3-0.6B/1.7B. **No Llama, no Qwen3-4B** |
| *"A round settles daily"* | `README.md` | `ROUND_BLOCKS = 21_600` = **72 hours** |
| Training run *"required for admission"* | `miner_setup.md` §6, mechanism §7 | `PROVENANCE_REQUIRED: Final[bool] = False` |
| `CLASS_WEIGHTS = {"mt-3g": 1.0}` | `constants.py:94` | Correct — but it's a *class* weight; the *track* split it implies is inverted |

To the project's credit, `docs/mechanism.md` explicitly separates **frozen** from
**tunable** (§14), and every value above that moved is in the tunable set. The
defect is that the repo publishes stale tunables as if current, and only the API
tells the truth. **`mt inspect tracks` reads from a local checkout, so it will
report the stale values too.**

---

## 12. Verdict

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

**MicroTensor is the healthiest live subnet I have analysed in this series, and
it has the best-argued incentive mechanism of the nine.**

The evidence is on chain rather than in the prose. **Nine miners earning**, with a
genuine distribution from $845/day down to $56/day — not one UID taking
everything. **The owner's miner incentive is `0.0000`**; it earns from the 18 %
cut and staked dividends like anyone else, and takes nothing from the miner pool.
Fifty-nine real commitments in a live format. A public API that reproduces the
leaderboard, the frontier, and the certificates. After SN47 (owner takes 100 %),
SN90 (one related-party miner), SN58 (one UID with no commitment) and SN78 (a
non-serving UID at 100 %), this is what a working subnet looks like.

The mechanism reasoning is unusually careful. **Gate-then-rank** is defended
against the obvious composite alternative on four specific grounds, including that
a product formula *"instructs the network to produce very small models that do not
work."* **Hypervolume emission** means discovering a new trade-off point pays
wherever it occurs, which a rank ordering structurally cannot express.
**Hysteresis at every boundary** is an explicit response to SN9's documented
hoarding, and the argument — that it defeats copying *before the copy is made* —
is correct. **The truthful-declaration equilibrium** is genuinely elegant: no score
term depends on your declaration, under-declaring is fatal, over-declaring costs
commercial selection, so the optimum is the truth plus a defensible margin.
And **no miner-authored code ever runs on validator hardware** — the tightest
sandbox posture of the nine.

**The serious problem is that the documentation describes a different network than
the one running.** The docs say `code` is the only enabled track at 100 % emission.
The live API says `code` pays **nothing** and `extract` — a track absent from the
documented list entirely — pays **everything**. The p95 ceiling is documented at
180 ms and is actually 15,000–45,000 ms. The base-model allowlist is wrong. A
miner who reads the repository carefully and follows it will train the wrong model
for the wrong arena against the wrong constraints. That is not a cosmetic defect.

**And the strategy the mechanism actually rewards is counter-intuitive enough to
trap most entrants.** The miner with the best quality score on the board earns
**0.52 %**. The miner with mediocre quality but the lowest cost earns **12.75 %**.
Income is exclusive hypervolume, not accuracy — and nothing in the miner guide
puts that in front of you with a worked example.

### Recommended path

1. **Confirm the paying track with the operator before anything else.** `extract`
   vs `code` is a fork in the road worth days of GPU time. The API and the docs
   disagree, and the on-chain incentives agree with neither cleanly.
2. **Register now — $25.60.** Slots are 40 per arena and `extract` holds 23, so
   there is room, and `MIN_ROUNDS_OBSERVED = 2` on a 3-day round means ~6 days
   before you can earn. Start the clock.
3. **Pull `/v1/certificates` and plot the frontier before you train.** Pick an
   unoccupied corner — below 1,351 ms, or above 0.9526 quality under 3,550 ms.
   Do not aim at the crowded middle.
4. **Use the free reference completions** from `/v1/corpora/<version>/public` to
   distil into Qwen3-0.6B. Most newcomers won't find them.
5. **Treat latency as a first-class objective**, not an afterthought. It is half
   the frontier and the axis where the field is weakest.
6. **Run `mt miner selfcheck` every time.** A third of `code` submissions failed
   admission.
7. **Watch two signals:** whether `code`'s emission share stays at 0.0, and whether
   the repo's tunables get refreshed to match the API. The second one tells you
   how much of the documentation you can trust going forward.

---

## 13. Sources

**Code** (public, MIT)
- https://github.com/microtensor-io/microtensor-subnet — release 0.3.2, mechanism 0.3.0
- Local: `/root/Bittensor/92/microtensor-subnet` (162 files)
- `docs/mechanism.md` (944 lines), `docs/miner_setup.md` (681),
  `docs/validator_setup.md` (350), `docs/coordinator_setup.md` (322),
  `README.md` (224), `min_compute.yml`
- `microtensor/core/constants.py`, `microtensor/harness/`, `microtensor/envelope/`,
  `scripts/pin_base_models.py`

**Live API** (fetched 2026-09-03)
- `GET https://api.microtensor.cloud/v1/arenas` — both arenas, ceilings, shares,
  base models, role baselines
- `GET https://api.microtensor.cloud/v1/certificates` — 13 certificates across
  rounds 1236–1238
- `GET https://api.microtensor.cloud/health` → `{"status":"ok","plane":"edge"}`
- `GET /v1/corpora/<version>/public` — documented train split + reference completions

**Chain** (finney, block 8,983,665)
- `Subtensor.subnet(92)`, `metagraph(92)`, `recycle(92)`
- `get_all_commitments(92)` — **59** commitments in `mt1|round|track|class|digest|uri` format
- `SubnetIdentitiesV3(92)`

**Sites**
- https://microtensor.vercel.app · https://www.microtensor.cloud/network/arenas

**Price reference**
- TAO ≈ $256 → α ≈ $1.068 at 0.004172 TAO/α
