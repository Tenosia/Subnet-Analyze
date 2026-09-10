# SN25 — UR (Decentralized Privacy Network / VPN)

| | |
|---|---|
| **netuid** | 25 (`UR`, symbol `א`) |
| **Chain description** | *"The peer to peer privacy network and encryption layer for the internet"* |
| **Owner hotkey** | `5F6aRdsBHajN2NhZHBTB6ibBFu7YuZZEWruWzB8x6B6GiZ4D` — **holds UID 1**, and is **identical to the owner coldkey** |
| **Prior identity** | **SN25 was `Mainframe`** — the repo's own `PROJECTION.md` prices α as *"SN25 (Mainframe) spot"* |
| **Subnet code** | https://github.com/urfoundation/sn — Go + Solidity, created 2026-06-07, **pushed 2026-09-06** |
| **Product code** | [`urnetwork/connect`](https://github.com/urnetwork/connect) (created **2022-12-13**, 49★) · [`server`](https://github.com/urnetwork/server) · [`sdk`](https://github.com/urnetwork/sdk) — all pushed 2026-09-06 |
| **Local checkouts** | `/root/Bittensor/25/sn` · `/root/Bittensor/25/connect` (fetched today; the directory did not exist) |
| **Sites** | **[ur.xyz](https://ur.xyz/)** — the protocol/subnet · **[ur.io](https://ur.io/)** — URnetwork's consumer VPN, run by **BringYour, Inc.**, *"a Network Operator for the UR protocol"* |
| **Contact** | `brien@ur.io` · Discord `xcolwell` |
| **Registered at block** | **2,998,801** — one of the oldest slots in this folder |
| **Live state (2026-09-07)** | ur.xyz Subnet Ledger reads **"BLOCK NUMBER #1"** with data/users **empty** |
| **Price** | 0.009030 TAO/א (**≈ $2.31**) · **tao_in τ15,363** · alpha_in 1,701,293 · alpha_out 4,200,988 |
| **Price move** | **+187 %** since the whitepaper's peg of $0.8047 (2026-07-03) |
| **UIDs** | 256 registered · **1 with incentive (the owner)** · 15 permits · 14 with dividends |
| **On-chain commitments** | 263 |
| **Registration cost** | **0.0005 TAO (~$0.13)** |

> **The short version.** UR is a **real, four-year-old consumer VPN** (URnetwork,
> ~49★ on GitHub, shipping apps) that has designed an unusually sophisticated
> Bittensor subnet to pay the people who carry its traffic. The subnet spec is
> ~18,000 lines of documentation plus an audited Solidity contract suite. **It is
> also explicitly testnet-first and not yet live on mainnet** — and the chain
> agrees: the owner's own UID takes 100 % of the miner pool.

---

## 1 · Goal — in plain terms

Most VPNs are one company's servers. UR's thesis is that a VPN should be a **mesh
of ordinary people's connections** — *"Whole-internet encryption, powered by
people"* — and that the hard part is not the software but **paying the people who
carry the traffic**, provably and without the operator holding their money.

That payment layer is the subnet.

```
Consumer (ur.io app)
     ↓ encrypted traffic
Network Operator (NO)  ── runs the servers + the /verify endpoint
     ↓ assigns routes
Providers / miners     ── carry ingress + egress traffic on their own IPs
     ↑ walked and measured
Validators             ── walk operator-assigned chains, prove real-time transit
     ↓
Yuma Consensus         ── turns that measurement into α emission
```

Everything is denominated in the subnet's α, branded **$UR**.

**The thing being sold is routable IP breadth.** From the miners page:

> *"Miners compete to make the most **IPv4 /29 and IPv6 /48 subnets** available on
> the network, each kept **routable at any moment** for ingress or egress traffic.
> In other words, miners convert the public internet into an anonymous private
> network for everyone to use."*

Not bandwidth. Not uptime. **Distinct routable address space.**

---

## 2 · What you do as a miner

There are **two miner tiers inside one mechanism**, split by a governance
parameter **θ** (starting **θ ≈ 0.3** head / 0.7 tail). Which one you are in
depends on how much distinct routable address space you bring.

### Tier 1 — Provider in a pool (the on-ramp, `1−θ`)

You attach to a Network Operator and carry traffic. You are a `client_id`
**inside** that NO's pool — **not a UID**.

| | |
|---|---|
| **Why not a UID?** | A single NO may serve **100k+ providers**, against a subnet cap of ~256 UIDs |
| **How you're paid** | **Merkle claim** — you pull your α **directly from the immutable settlement vault** with a cryptographic proof against your NO's payout root |
| **Barrier** | Very low — *"the provider needs no UID or burn because the immutable vault owns one shared, burn-registered pool UID per NO"* |
| **Trust** | You trust your NO's discretionary payout split (it is auditable, but discretionary) |

The whole pool's weight is set by validators as **`implied_usage × quality`**,
where `implied_usage = the NO's epoch deposit ÷ its tier rate`.

### Tier 2 — Top-level miner (the head, `θ`)

The **top ~200 fleets by split-adjusted distinct routable egress-IP count** each
claim **their own miner UID**, are steered **directly** by validators, and are
**paid natively to their own coldkey** — no contract custody, no Merkle claim, no
operator in the payout path.

**The scoring formula:**

```
IPs(u)   = { distinct keyed prefix hash h : some client of u routed a VERIFIED trail hop from h }
claim(h) = #{ head miners u' : h ∈ IPs(u') }          # split across everyone sharing that prefix
score(u) = Σ over h ∈ IPs(u) of  1 / claim(h)         # split-adjusted unique routable-IP count
head_weight[u] = score(u)                             # the weight IS the IP score
```

Three things make this an unusual metric:

- **Granularity is `/29` IPv4 and `/48` IPv6.** Many exact IPs in one co-located
  prefix **collapse to one unit** — *"distinct exact IPs in one co-located prefix
  deliberately collapse and cannot double-count supply."* Renting 256 addresses in
  one datacentre rack buys you very little.
- **Shared prefixes split.** Each hash contributes **1.0 total, divided equally**
  among every head fleet observed on it. If four fleets share a prefix, each gets 0.25.
- **Liveness is baked in, so there is no separate quality term.** A unit counts
  only if *"the validator completed a real trail hop through it."*

Identity is a **dual-signed binding** of your `client_id`s to your head hotkey —
you must prove you control both, so you cannot claim IPs you do not operate.

### Promotion, demotion, and no double-pay

> *"A provider **starts in a pool, graduates to a top slot** as its routable-IP
> breadth grows, and **falls back** if it slips — with Bittensor's native
> deregistration churn running that tournament."*

A `client_id` earns in **exactly one** tier at a time.

---

## 3 · Scoring logic

### 3.1 The measurement — validators walk real routes

Validators are **independent Bittensor validator UIDs** staking their own α. They
run the routing-verification protocol in [`VALIDATOR.md`](https://github.com/urfoundation/sn/blob/main/VALIDATOR.md)
(974 lines):

> *"Each stakes its own UR and runs the routing-verification protocol,
> continuously **walking operator-assigned chains of miners** to prove real-time
> transit and **measure which miners are the weakest links**. That measurement is
> the core signal the network pays for."*

Each completed hop yields a **signed trail** carrying a per-hop **egress-IP-hash**
— a keyed hash at the policy granularity, **never the raw IP** — so a validator
can count each fleet's routable score units and the sharing splits **without
trusting anyone**. The README calls this the *"verify-the-top-200"* requirement:
a validator weights a claimed top miner only as high as **its own** observed IP
score justifies.

### 3.2 The three money channels

**1 · Deposits — the demand signal, and a one-way buyback.**

Network Operators deposit α sized to their real usage at an **off-chain published
rate** (deliberately *no on-chain oracle*). Deposits are **never distributed**:

> *"every exact deposit is transferred into the immutable `STReserveSink` and
> staked on the fixed reserve hotkey (compounding dividends, with no outbound
> bytecode)."*

A NO's cumulative locked α is its **conviction**, which sets its **tier → rate**:
zero conviction pays the baseline rate, more conviction lowers it. The
**one-way invariant** is explicit: *"no contract function ever sources a transfer
out of it."*

**2 · Emission — standard Yuma.** The usual **18 % owner / 41 % miner / 41 %
validator** split. Each tempo (~72 min) validators score **both miner tiers** from
their own trails and submit weights under **commit-reveal**.

**3 · Settlement — a 7-day epoch** (~50,400 blocks). The immutable vault captures
pool emission; providers **claim directly from the vault**. *"A NO directs where
its pool's rewards go but never holds anyone else's funds."*

### 3.3 The custody model is the design's centre of gravity

| Guarantee | Detail |
|---|---|
| **No operator custody** | The owner and NOs never hold anyone else's α |
| **Finalized claims are sacrosanct** | *"no upgrade, pause, or admin action can block or claw back a finalized claim"* — from day one |
| **The reserve is one-way** | No code path sources a transfer out of it |
| **Split governance** | `STReserveSink` and `STSettlementVault` are **non-upgradeable from launch**; only `STCoordinator` is UUPS-upgradeable, and mainnet requires a **2-of-3 Safe + ≥1-epoch timelock** |

Contract suite is Foundry-tested at **75/75** per the implementation log.

### 3.4 Validator rewards — native dividends only

Validators earn **native dividends (∝ stake × vtrust) and nothing else** in v1.
The "effort bounty" that would have paid validators for submitting trail proofs is
**explicitly parked out of scope** (D29) — the hardened implementation sits
byte-for-byte in `docs/parked/` for a later phase.

---

## 4 · Live competition landscape

### 4.1 The mechanism is not running on mainnet

The repo's launch ladder was flipped to **testnet-first** on 2026-07-03 (decision
D28), reversing an earlier mainnet-direct plan:

> *"**v1 is testnet-first** — the ladder below (M0 → M3) runs on **testnet**
> (chain 945 / test.finney); **mainnet is the later Phase-E promotion (M3)**,
> gated behind a clean testnet run, after which the M4+ production phases run on
> finney."*

The milestones are M0 rehearsal/probes → M1 testnet convergence → M2 buyback
reserve verified live on testnet → **M3 promote to mainnet** → M4 production
rollout → M5/M6 governance hardening.

The public protocol ledger at [ur.xyz](https://ur.xyz/) corroborates this — it
reads **"BLOCK NUMBER #1"** with *TOTAL DATA / BLOCK* and *TOTAL USERS / BLOCK*
both blank.

### 4.2 The chain agrees — the owner takes everything

| | |
|---|---|
| UIDs with non-zero incentive | **1** |
| That UID | **UID 1 — the owner's own hotkey** |
| Its incentive | **1.000000** (the entire miner pool) |

Four validators set weights, and they are unanimous:

| Setter | Stake | Weight |
|---|---|---|
| UID 212 | 183,886 | **100 % → UID 1** |
| UID 73 | 46,508 | **100 % → UID 1** |
| UID 148 | 41,412 | **100 % → UID 1** |
| UID 178 | 33,100 | **100 % → UID 1** |

Note this is **not** a case of a hidden mechanism paying an unexplained UID (as on
SN40 or SN93) — it is the straightforward consequence of a subnet whose incentive
mechanism has not been switched on. The owner holds the slot while the protocol is
built.

### 4.3 Two structural notes worth flagging

**The owner's hotkey and coldkey are the same key.** I verified both fields return
`5F6aRdsBHajN2NhZHBTB6ibBFu7YuZZEWruWzB8x6B6GiZ4D`. That is unusual practice —
hotkeys are meant to be operationally hot and coldkeys cold — and it means the key
signing weight extrinsics is also the key holding the owner's stake.

**The whitepaper places the owner at UID 0; the chain has it at UID 1.** §3 of
`WHITEPAPER.md` says *"owner coldkey + owner hotkey at **UID 0** (immune)"*. On
chain, UID 0 holds zero stake and zero incentive while UID 1 is the owner. A minor
drift, but the UID-0 immunity assumption is load-bearing in the doc.

### 4.4 The product behind it is real and old

This is the part that separates UR from most pre-launch subnets:

| | |
|---|---|
| `urnetwork/connect` | created **2022-12-13**, 49★, Go, MPL-2.0 — *"A web-standards VPN marketplace"* |
| `urnetwork/server` | created 2023-01-26, 19★ |
| `urnetwork/sdk` | created 2024-11-14 |
| `urfoundation/sn` | created **2026-06-07** — the subnet layer is 3 months old |
| All four | **pushed 2026-09-06** (yesterday) |

`ur.io` ships consumer VPN apps today, operated by **BringYour, Inc.**, which
describes itself as *"a Network Operator for the UR protocol."* The subnet is a
payment rail being retrofitted onto a working product — the opposite of the usual
order.

---

## 5 · Economics

Subnet emits **7,200 α/day**; 18 % owner / 41 % miner / 41 % validator →
**miner pool = 2,952 α/day**.

At α = 0.009030 TAO and TAO ≈ $256 → **α ≈ $2.31**:

| | α/day | USD/day |
|---|---|---|
| Miner pool (face value) | 2,952 | **$6,824** |
| **UID 1 (owner) — 100 % of it** | **2,952** | **$6,824** (~$205k/mo) |
| Every other UID | **0** | **$0** |
| **Owner total** (18 % cut + 100 % incentive) | 4,248 | **$9,820/day — 59.0 % of emission** |

### The demand model on paper

`PROJECTION.md` models NO deposits against real usage:

| Input | Value |
|---|---|
| Baseline data | **50 TB per 7-day block** |
| Baseline users | **100,000 active** |
| Price target | **$2,500 / block** ($10,000 per 4 blocks) |
| Rate card | **$0.025/GB** and **$0.0125 per active user·block** |
| α peg | **$0.8047** (fixed 2026-07-03) |
| → α rates | 0.031067 α/GB · 0.015534 α/user·block |
| Baseline deposit | **3,107 α/block**, growing to 31,067 α/block at 10× usage over a year |

> ⚠️ **The peg is now badly stale.** α has gone from $0.8047 to **$2.31 (+187 %)**
> since that document was written. At the *fixed* α rate card, a NO's cost in USD
> terms has risen **2.87×**. The whitepaper does say the peg is *"occasionally
> re-pegged (§7)"*, but anyone modelling NO economics must re-peg first — the
> published numbers are no longer usable as-is.

### Costs to participate

| Role | Cost |
|---|---|
| **Provider (pool tier)** | **Registration: none** — no UID, no burn. Just attach to a NO |
| **Top-level miner (head)** | A UID (registration **0.0005 TAO ≈ $0.13**) + **broad, distinct routable address space** |
| **Validator** | A UID + your own α stake; runs the trail-walking protocol |
| **Network Operator** | Servers, the `/verify` endpoint, and an ongoing **α deposit** sized to usage |
| **GPU** | **None anywhere in this subnet** |

**The real cost for a head miner is IP address space**, not hardware — and
specifically *diverse* space, since a `/29` is one unit no matter how many
addresses sit in it and shared prefixes split.

---

## 6 · How to become a winner

### Priority 1 — Do not expect to earn yet

The mechanism is testnet-first and mainnet promotion is milestone **M3**, gated
behind a clean testnet run. Today the owner's UID takes the entire miner pool.
Anything you build now is positioning, not income.

The right move is to ask — Discord `xcolwell`, or `brien@ur.io` — **where on the
M0→M6 ladder the network actually is**, and when M3 (mainnet promotion) is
expected. That single answer determines whether this is a month or a year away.

### Priority 2 — Understand that the scarce asset is *diverse* address space

This is the whole competitive question, and it is unlike anything else in this
folder. Your score is:

```
score(u) = Σ over distinct /29 (v4) or /48 (v6) prefixes  of  1 / (fleets sharing it)
```

Three consequences that should drive every decision:

- **Volume is worthless.** Traffic carried does not enter the head score at all.
  *"real VPN supply breadth, not traffic volume."*
- **Concentration is worthless.** 256 addresses inside one `/29` count as **one
  unit**. A single big rack is one point.
- **Popular hosting is diluted.** If you and three others all run on the same
  cheap VPS provider's prefix, you each get **0.25** of that unit.

So the winning shape is **many small footholds in many distinct networks** —
residential, mobile, small regional ISPs, geographically spread — not one large
datacentre presence. That is an unusual procurement problem, and it is where an
edge exists.

### Priority 3 — Start in a pool, graduate to the head

The pool tier needs **no UID and no burn**, so the cost of starting is essentially
zero: attach to a Network Operator (BringYour/ur.io is one) and carry traffic.
Build routable breadth there, and the design explicitly promotes you into a head
slot as your score grows, with deregistration churn running the tournament.

That is a genuinely low-risk on-ramp — you learn the operational reality before
committing to a UID.

### Priority 4 — Keep every prefix *routable*, continuously

A score unit counts only when *"the validator completed a real trail hop through
it."* Liveness is not a separate uptime term — it is baked into whether the unit
exists at all. A prefix that is not reachable when a validator walks it simply
does not count that round.

### Priority 5 — If you would rather validate

Validators are permissionless Bittensor-native UIDs and earn **native dividends
only** (∝ stake × vtrust). There is no effort bounty in v1 — it is parked. So
validating here is a staking-yield decision with an operational cost, not a
performance competition. Note the top of the dividend table is already
concentrated: UID 204 holds **56.3 %** with 2.3M stake.

### The path

1. Ask where the network is on the M0→M6 ladder. **Wait for the answer.**
2. Meanwhile, read [`VALIDATOR.md`](https://github.com/urfoundation/sn/blob/main/VALIDATOR.md)
   (974 lines) — it defines exactly what a trail hop is and therefore what makes a
   prefix count.
3. Join a pool as a provider through an existing NO. No UID, no burn, no risk.
4. **Audit your address diversity before spending anything** — count distinct
   `/29`s and `/48`s you can keep routable, not total IPs.
5. Re-peg the `PROJECTION.md` rate card at the current α price before modelling
   any NO-side economics.
6. Watch for a second UID showing non-zero incentive. That is the signal the
   mechanism has been switched on.

---

## 7 · Rules you must keep

| Rule | Consequence |
|---|---|
| A `client_id` earns in **exactly one** tier | Promoted out of the pool payout list on taking a UID — no double-pay |
| Head identity needs a **dual-signed `client_id`s ⇄ hotkey binding** | Validators **fail closed** if the hotkey is not a live UID |
| Prefixes must be **routable when walked** | Un-walked prefixes contribute nothing |
| Score granularity is `/29` v4, `/48` v6 | Many IPs in one prefix collapse to one unit |
| Shared prefixes split `1/claim(h)` | Co-located fleets dilute each other |
| Head slots are **top ~200 by score** | Maintained by native deregistration churn — slip and you fall back to a pool |
| NO deposits are **conviction stake** | Sunk into `STReserveSink` permanently; never distributed, never withdrawn |
| Validators must run trails themselves | *"a validator only weights a claimed top miner as high as its own observed IP score justifies"* |
| Finalized claims | Sacrosanct — no upgrade, pause or admin action can reverse them |

---

## 8 · Device conditions

**There is no GPU anywhere in this subnet.** This is network infrastructure.

### Provider / miner

| | |
|---|---|
| GPU | **None** |
| **The actual requirement** | **Distinct routable IPv4 `/29` and IPv6 `/48` prefixes**, kept reachable |
| Traffic | Carries **both ingress and egress**, encrypted only, safe-by-default security model |
| Client | `urnetwork/connect` (Go, MPL-2.0) — runs on consumer devices from normal app stores |
| Registration | **None** for the pool tier; 0.0005 TAO (~$0.13) for a head UID |
| Uptime | Continuous — liveness is the metric |

### Validator

| | |
|---|---|
| GPU | **None** |
| Work | Walk operator-assigned provider chains; collect signed trails; compute both tiers' weights; submit under commit-reveal |
| Stake | Its own α; rewards are native dividends ∝ stake × vtrust |
| Independence | Explicitly required — *"Validators are not pooled"* |

### Network Operator

Runs the privacy servers plus the `/verify` endpoint, commits the Merkle payout
root each epoch, and deposits α sized to real usage.

> **Against your BEAM box (2 cores / 3.7 GB, Hetzner CX22, 46.225.140.58):** the
> hardware is fine — this needs bandwidth and addresses, not compute. But it is
> **one IP in one Hetzner `/29`**, which is worth a fraction of one score unit
> shared with every other Hetzner-hosted fleet. **Address diversity, not the box,
> is the binding constraint here** — and it is the one thing a single VPS cannot
> give you.

---

## 9 · Third-party conditions

| Dependency | Role | Note |
|---|---|---|
| **BringYour, Inc.** | The founding Network Operator (ur.io) and the subnet owner | The product and the protocol share a parent today; the stated goal is more NOs |
| **Subtensor EVM + precompiles** | The ST contract suite runs on the Subtensor EVM | Precompiles are **runtime-only** — *"forge sim can't execute them"*, hence the on-node `cast` probe battery |
| **`STCoordinator` / `STSettlementVault` / `STReserveSink`** | Three distinct mapped coldkeys | Vault + sink **non-upgradeable**; coordinator UUPS behind a 2-of-3 Safe + timelock on mainnet |
| **Commitments pallet** | Used as *"the free data layer"* | Whitepaper §2.4 |
| **Release runtime pin** | Whitepaper §2.6 | The contract suite is pinned to a reviewed Subtensor runtime |
| **Foundry / Forge** | Contract test suite, **75/75** | |
| **`urnetwork/connect`** | The transport protocol and client | MPL-2.0, protobuf realtime transport, OpenAPI marketplace API |
| **Off-chain published rate schedule** | Sets NO deposit sizing | **Deliberately not an on-chain oracle** — a stated trust assumption |

Notably **absent**: no LLM, no model, no Hugging Face, no GPU cloud, no external
scoring API. The measurement is validators walking real network paths.

---

## 10 · Risks

1. **The mechanism is not live on mainnet.** The launch ladder is testnet-first
   with mainnet as milestone M3. The owner's UID takes 100 % of the miner pool
   today. Everything in the spec is a description of what will run, not what runs.

2. **The subnet slot was repurposed.** SN25 was **Mainframe**; the repo's own
   projection prices α against *"SN25 (Mainframe) spot."* The subnet layer
   (`urfoundation/sn`) is **three months old** on a slot registered at block
   2,998,801.

3. **Owner captures 59 % of emission**, all of it because the incentive mechanism
   is off. That will fall when miners start earning — but it has not yet.

4. **Owner hotkey and coldkey are the same key.** Unusual and worth understanding
   before trusting the governance model, since the key signing weights also holds
   the owner's stake.

5. **The whitepaper's UID assumption has drifted.** It places the owner at UID 0
   with immunity; the chain has the owner at UID 1 and UID 0 empty.

6. **The α peg is 187 % stale.** `PROJECTION.md`'s entire rate card is fixed to
   $0.8047/α. At $2.31 the modelled NO cost has nearly tripled in USD terms. Any
   deposit-side economics must be re-derived.

7. **Deposits are permanently sunk.** A NO's α goes into `STReserveSink` and can
   never come out — by design (it is the buyback), but it is a one-way commitment
   that should be sized accordingly.

8. **Only `STCoordinator` is upgradeable**, and on mainnet behind a 2-of-3 Safe
   plus a ≥1-epoch timelock. That is good practice, but it is still an upgrade
   path over the policy layer.

9. **The rate schedule is off-chain.** *"No on-chain oracle — a published
   per-tier rate schedule."* This is a deliberate simplification and an explicit
   trust assumption: whoever publishes the rates sets `implied_usage`, which sets
   pool weight.

10. **Head competition is a procurement race, not an engineering one.** Winning
    means acquiring diverse routable address space across many networks. That
    favours incumbents with existing footprints and is expensive to bootstrap.

11. **Validators earn dividends only.** The effort bounty is parked, so there is
    no direct payment for the trail-walking work itself in v1 — it is funded by
    stake yield.

12. **Dividend concentration.** UID 204 holds 56.3 % of validator dividends with
    2.3M stake; the top two hold ~75 %.

---

## 11 · Documentation notes

The `sn` repo is one of the most thoroughly documented in this folder —
~18,000 lines across ten markdown files, including a 1,831-line whitepaper, a
974-line validator protocol, a 782-line comparison against the rest of the
Bittensor field, and a 7,829-line implementation log that records **which decision
changed on which date** (D23 → D29).

| Observation | Detail |
|---|---|
| Owner at UID 0 | `WHITEPAPER.md` §3 says UID 0; chain has the owner at **UID 1** |
| α peg $0.8047 | `PROJECTION.md` — now **$2.31**, +187 % |
| Mainnet-direct launch (D24) | **Reverted by D28** to testnet-first; the D24 note is retained inline in the status log, which is honest but easy to misread |
| Effort bounty | Removed from v1, *"parked byte-for-byte at `docs/parked/`"* |
| `COMPARISON.md` | Self-assesses as **12 decisions aligned** with Bittensor norms, **2 divergent** (both *toward* trustlessness), **2 novel bets** |

The self-assessment in `COMPARISON.md` is a good sign: rather than claiming
novelty everywhere, it counts where it follows convention and names its two
genuine bets — coupling miner reward to revenue-backed demand, and the
pooled-tail/direct-head split.

---

## 12 · Verdict

**UR is the only subnet in this folder built as a payment layer for a product that
already exists and already has users.**

That inversion matters. `urnetwork/connect` has been developed since **December
2022**, has 49 stars, ships consumer VPN apps through normal app stores, and is
operated commercially by BringYour, Inc. The subnet (`urfoundation/sn`, June 2026)
was written **afterward**, to pay the people carrying that traffic. Compare the
usual order — a subnet spec looking for users.

The mechanism design is correspondingly serious. The **custody model** is the
strongest I have read here: no operator ever holds anyone else's α, the settlement
vault and reserve sink are **non-upgradeable from launch**, finalized claims are
sacrosanct against any admin action, and the reserve is one-way by invariant with
a Foundry test proving it holds *under a hostile upgrade*. The **two-tier miner
design** is a real answer to a real constraint — 100k+ providers cannot each hold
one of 256 UIDs — and it solves it without putting the operator in the payout
path. And the **head metric is unusually well-chosen**: scoring *split-adjusted
distinct routable prefixes* rather than traffic means you cannot win by renting
one big rack or by pushing volume, which are exactly the two things a naive VPN
incentive would reward.

**But none of it is running.** The launch ladder was flipped to testnet-first in
July, mainnet promotion is milestone M3, the public ledger reads "BLOCK #1" with
no data, and the owner's own UID takes 100 % of the miner pool. There is no
anomaly here and nothing hidden — it is simply a subnet whose incentive mechanism
has not been switched on, holding its slot while the protocol is finished.

**So the honest assessment is: excellent design, real product, unknown timeline.**
The question that decides everything is where on M0→M6 the network actually is,
and that is a question for the team rather than the code.

### Recommended path

1. **Ask where the network is on the M0→M6 ladder**, via Discord (`xcolwell`) or
   `brien@ur.io`. Nothing else can be planned without that.
2. **Join a pool as a provider now — it costs nothing.** No UID, no burn, no
   registration. You learn the operational reality and start building routable
   breadth while the head tier is still empty.
3. **Audit your address diversity before anything else.** Count distinct `/29`s
   and `/48`s you can keep continuously routable — not total IP addresses. That
   number *is* your future score.
4. **Do not model NO economics off `PROJECTION.md` as written** — re-peg the rate
   card from $0.8047 to the current α price first.
5. **Watch one signal:** any UID other than the owner's showing non-zero
   incentive. That is the moment this subnet becomes minable.

---

## 13 · Sources

**Code**
- https://github.com/urfoundation/sn (created 2026-06-07, pushed 2026-09-06) —
  `README.md`, `WHITEPAPER.md` (1,831 ln), `VALIDATOR.md` (974 ln),
  `COMPARISON.md` (782 ln), `IMPLEMENTATION_STATUS.md`, `PROJECTION.md`,
  `PLAN.md`, `FINALIZE.md`, `FINALIZE-COMPLETE.md`, `WHITEPAPER_DISCUSS.md`,
  `evm/` (Solidity + Foundry, 75/75)
- https://github.com/urnetwork/connect (created 2022-12-13, 49★, MPL-2.0) ·
  [`server`](https://github.com/urnetwork/server) · [`sdk`](https://github.com/urnetwork/sdk)
- Local: `/root/Bittensor/25/sn`, `/root/Bittensor/25/connect`

**Live sites** (fetched 2026-09-07)
- [ur.xyz](https://ur.xyz/) — protocol; Subnet Ledger at **"BLOCK NUMBER #1"**, data/users empty
- [ur.xyz/miners](https://ur.xyz/miners) · [/validators](https://ur.xyz/validators) · [/operators](https://ur.xyz/operators)
- [ur.io](https://ur.io/) — URnetwork consumer VPN, operated by BringYour, Inc.

**Chain** (finney, block ~9,013,700)
- `Subtensor.subnet(25)`, `metagraph(25)`, `weights(25)`, `recycle(25)`,
  `get_all_commitments(25)` — 263 commitments, `SubnetIdentitiesV3(25)`

**Price reference**
- TAO ≈ $256 → α ≈ $2.31 at 0.009030 TAO/α (whitepaper peg was $0.8047)
