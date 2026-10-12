# SN76 — Ormas (Outcomes API for Coding Work)

| | |
|---|---|
| **netuid** | 76 (`Ormas`, symbol `ن`) |
| **Operator** | **Heron Cove LLC** (Wyoming) · `operations@heroncove.us` |
| **Tagline** | *"Pay for verified receipts, not inference turns."* |
| **Owner hotkey** | `5CqaQ34dznCVTdrpcxoiTK…` — **holds UID 0** |
| **Owner coldkey** | `5CLWmDjLwkDtLQ86y9aiwfzrUCrtnnSWS9oEXianj2jMDCAo` |
| **Code** | https://github.com/heroncovelabs/ormas-subnet — **MIT**, 38 files, real implementation |
| **Local checkout** | `/root/Bittensor/76/ormas-subnet` (created today) |
| **Site / API** | https://ormas.ai · [/docs](https://ormas.ai/docs) · **`api.ormas.ai` (live, public routes)** |
| **Registered at block** | **9,003,844 — 2026-09-05, 8.1 days old** |
| **Predecessor** | ⚠️ **Not a continuation.** Netuid 76 was Phylax, then `nun`, then re-registered as Ormas |
| **Price** | 0.004978 TAO/ن (**≈ $1.27**) · tao_in **τ462** · alpha_in 92,906 · **alpha_out 0** |
| **Emission** | **`alpha_out_emission = 0` — the subnet emits nothing at all** |
| **UIDs** | 94 registered · 1 with incentive (owner) · 4 permits · 3 with dividends |
| **On-chain commitments** | 0 |
| **Registration cost** | **0.0005 TAO (~$0.13)** |

> **Two things to know before the detail.**
>
> **1. This is not the Phylax subnet.** The chain identity says so in its own
> words: *"Registered September 5, 2026; **not a continuation of the former
> subnet 76**."* [`SN076-PHYLAX-HISTORICAL.md`](SN076-PHYLAX-HISTORICAL.md)
> describes a different project that no longer exists here.
>
> **2. Nothing is being emitted.** `alpha_out_emission = 0` and `alpha_out = 0` —
> the subnet has not been started. The owner's UID holds 100 % of *incentive*,
> but 100 % of zero. **No one is being paid, including the operator.**
>
> The watchdog in this folder caught the takeover on its own: it logged
> `nun → Ormas` plus the GitHub repo and website appearing on chain from empty.

---

## 1 · Goal — in plain terms

Every coding-agent subnet so far pays for **effort**: tokens served, inference
turns, attempts made. Ormas refuses that framing entirely.

> *"A client describes a change **and the test that proves it**. Miners with
> public track records post a **firm ask** for the passing result. Accepted
> delivery → the miner is paid exactly its ask; a miss pays nothing."*

The mechanism is a **fixed-price bid for a verified outcome**:

```
Client posts:   a change to make  +  the test command that proves it  +  a reserve price
Miner posts:    a firm ask_usd for delivering the passing result
Gateway leases: the first ask at or under the reserve
Miner delivers: a git branch, having actually run the verify command
Validators:     independently clone, re-run verify on base and result, check
                scope from git diff, sign accept/reject
Settlement:     accepted → miner paid exactly its ask;  miss → client pays nothing
```

The line that captures it: **"The client's acceptance tests are the purchase
order; validators re-run them before anyone is paid."**

This is a genuinely different economic shape from every other coding subnet in
this folder. There is no leaderboard, no king, no quality score — an Outcome is
accepted or it is not, and the docs are explicit: *"there are no quality or
reliability multipliers."*

---

## 2 · What you do as a miner

**You implement one function: `solve()`.** Everything else — registration, repo
binding, leasing, cloning, running the verify command, publishing the branch,
building an honest receipt — is handled by the shipped skeleton.

```python
from ormas_subnet import MinerConfig, MinerSkeleton, OrmasMinerClient, TaskDraft
from ormas_subnet.skeleton import SolveResult
```

The loop, from the README:

> register → bind a repo → poll for a lease → clone/checkout the base commit →
> call your `solve(draft, workdir) -> SolveResult` → **actually run
> `draft.verify_command`** (bounded, credential-free env, no shell) → publish the
> result branch → complete.

### "Completion is honest" — the part worth reading twice

The skeleton deliberately refuses to let a miner self-certify:

| Field | How it is produced |
|---|---|
| usage/cost | **only from what `solve` reports** — *"an unknown value is never fabricated as zero"* |
| `scope_ok` | computed from a **real `git diff`** against `allowed_paths` — *"never asserted"* |
| `verification_state` | from the verify command's **actual exit code** |

The miner terms restate it as an obligation: *"usage you do not know is reported
as unknown, never as zero; `verified` is never self-declared."*

### The firm ask is the competitive variable

```python
OrmasMinerClient.claim_task(..., ask_usd=...)   # or MinerConfig.ask_usd
```

> *"the first ask at or under the client's reserve is leased; an ask above it is
> recorded and skipped, the job stays queued."*

So this is a **first-acceptable-bid auction against a hidden reserve**, not a
best-quality contest. Default `None` lets the gateway derive an ask for you.

### What is NOT in the repo

Stated plainly, and it matters:

> *"**Not our mining logic.** Our own miner — the agentic worker, model routing,
> cost capture, orchestration loop — stays private. It competes on this same
> protocol, on the same terms as every other miner. Nothing about *how* to solve
> a task well lives here."*

You bring the coding agent. They bring the marketplace.

### You can run the whole loop offline

`docs/QUICKSTART_LOCAL.md` + `ormas_subnet/localnet.py` give a local stand-in
gateway — **no token, no network host, no chain**. And `reference_solver.py`
runs a shell command and commits the result, so the skeleton works end to end
with zero model calls.

---

## 3 · Economics — how a USD bid becomes alpha

`docs/economics.md` is headed **"Status: planned — not yet live."** Read
everything below as design, not behaviour.

The problem it solves is stated cleanly:

> *"**Emission is fixed in alpha.** … **Demand is variable in USD.** … The model
> below exists to reconcile a fixed alpha supply with a variable dollar demand
> without anyone converting a customer's dollars for a miner."*

### The rule

| Step | Mechanism |
|---|---|
| **Bid → target** | Your accepted `ask_usd` becomes your **emission target** in USD. *"Only Outcomes accepted through the validator-gated path count; a miner's own report of success never does."* |
| **Target → weight** | Each epoch validators sum what every miner is owed and set weights **proportional to owed USD**, converting at the SN76 pool price and a published TAO/USD reference — both recorded in the epoch artifact with source ids |
| **Excess → owner UID** | Owed < capacity → the remainder of miner weight goes to the **owner UID**, where it burns or recycles. *"Unearned emission is not distributed to miners."* |
| **Shortfall → carry-forward** | Owed > capacity → pro-rata payment, remainder carried |
| **Persistent balance → treasury top-up** | Aged balances netted daily and paid **in alpha from Heron Cove's treasury** — counsel-gated, **default-off** |
| **Buybacks** | Heron Cove may buy alpha with **earned** revenue; manual, *"never wired to customer payments"* |

The carry-forward ledger:

```
owed_open(miner, epoch) = owed_open(miner, epoch−1)
                        + accepted_usd(miner, epoch)
                        − usd_value(emission_received(miner, epoch))
```

> *"The ledger is a pure function of chain weights, chain emissions, the published
> prices, and the accepted set; two validators running the same code on the same
> inputs produce the same ledger byte for byte."*

If the price cannot be established within a staleness cap, *"the epoch is marked
degraded and weights are held, not guessed."*

### Deliberate exclusions

The doc lists what the model **does not** do, which is as informative as what it does:

- No paying miners in USD by default, no converting a specific customer's dollars
- No holding alpha or USD on anyone's behalf
- **No quality or reliability multipliers** — accepted or not
- **No topping up the operator's own miner** — *"Its balance is published like any other and never paid from treasury"*
- **No accepting delegation to the company validator**

### Many parameters are openly unchosen

`economics.md` ends with a list of **OPEN** decisions: UTC cutoff, T+N payout
delay, dispute window, carry-forward aging, TAO/USD sources and staleness cap,
buyback share, foreign-miner policy, KYC tier contents, and whether the 40 %
per-hotkey weight cap survives. Publishing the gaps *"recorded here only so
nobody invents them"* is unusual and good practice.

---

## 4 · Live state

### 4.1 The gateway is real and running; the subnet is not

**The commercial side works today.** `api.ormas.ai/v1/public/providers` returns
live data:

| provider | affiliation | acceptance | median quote | quote → branch |
|---|---|---|---|---|
| `operator-1` | **operator-run** | 0.63 | **$0.42** | 145 s |
| `provider-0af465` | **independent** | 1.00 | **$0.10** | **6 s** |

Nine production tasks settled at their firm asks on 2026-09-12 with **zero
platform fee**, per the README. So there is already **one independent provider**
delivering accepted work — that is more real activity than most 8-day-old
subnets have.

**The chain side is switched off.** `alpha_out_emission = 0`, `alpha_out = 0`,
`sum(E) = 0`. Three validators (UIDs 1, 19, 25) set 100 % weight on UID 0, the
owner — but that weight moves nothing, because there is no emission to move.
Pool depth is **τ462**, among the thinnest in this folder.

### 4.2 The operator discloses its own conflict, unprompted

Three separate statements, all volunteered:

> *"Heron Cove LLC runs a miner and a validator on SN76 and operates the gateway
> that settles work. **Until validators gate settlement on the production
> gateway, acceptance is not independent of us**; we say so wherever a number
> appears (`/v1/public/providers` labels our miner `operator-run`)."*

> *"**No validators configured in production yet.** … `api.ormas.ai` has no
> validator count configured and no third-party miner connected, so every
> production receipt to date reflects **our trusted miner's own verify run**,
> not an independent decision."*

And the public API repeats it in its own `basis` field: *"Validator acceptance is
not live yet; nothing here ranks or rates providers."*

The `operator-run` label on their own provider row is a small thing that most
operators would omit.

### 4.3 The reference validator ships

Not just described — `ormas_subnet/validator.py` and `neurons/validator.py` are
in the repo. It *"clones the job's repo, independently re-runs the verify command
on base and result, checks scope from `git diff`, signs, and posts
accept/reject."* The gateway is built to settle a third-party miner **only on
unanimous validator acceptance** and *"refuses its claim until a validator count
is configured."*

So the architecture for independence exists; it is the deployment that has not
happened.

### 4.4 Netuid 76's history

| | |
|---|---|
| Was | **Phylax** — AI supply-chain security attestation ([archived file](SN076-PHYLAX-HISTORICAL.md)) |
| Then | **`nun`** — the watchdog logged registered-UID growth under this name |
| **Now** | **Ormas**, re-registered **2026-09-05**, explicitly *"not a continuation"* |

---

## 5 · What a miner would earn

**Today: nothing.** The subnet emits zero.

Under the planned model, earnings are **not** a share of a fixed pool — they are
your accepted USD bids, converted to weight:

```
your weight ∝ your owed USD  (accepted asks + carried balance)
```

At the observed median quotes ($0.10–$0.42 per task) this is a **high-volume,
low-ticket** business. Nine tasks at ~$0.42 is under $4 of settled value. For the
emission side to matter, either task volume or ticket size has to grow by orders
of magnitude — and if owed USD stays below the epoch's emission capacity, **the
excess goes to the owner UID**, not to miners.

### Costs

| Item | Cost |
|---|---|
| Registration | **0.0005 TAO ≈ $0.13** |
| GPU | **None required by the protocol** |
| **The real cost** | **Your coding agent** — model calls, orchestration, and the compute to actually make tests pass. Heron Cove *"supplies none of them and does not pay for them."* |
| Local development | **Free** — localnet gateway, no token, no chain |
| Risk per task | You spend model tokens on every attempt; **a miss pays nothing** |
| KYC | W-9/W-8 + screening required before any treasury top-up (not before emissions) |

**That last risk is the defining one.** You bear the full inference cost of every
attempt and are paid only on acceptance. Your bid must cover your expected cost
divided by your acceptance rate — at 0.63 acceptance, a $0.42 ask must cover
~$0.26 of expected spend just to break even.

---

## 6 · How to become a winner

### Priority 1 — Understand that you are bidding, not competing on quality

There is no score to maximise. *"An Outcome is accepted or it is not."* The only
levers are:

1. **Your acceptance rate** — do the tests actually pass when independently re-run?
2. **Your ask** — the first bid at or under the hidden reserve wins the lease.
3. **Your cost per attempt** — because misses are unpaid.

The winning quantity is `ask × acceptance − cost_per_attempt`, and the binding
constraint is that you cannot see the reserve.

### Priority 2 — Study the one independent provider already beating the operator

`provider-0af465` is worth studying closely:

| | operator-1 | provider-0af465 |
|---|---|---|
| acceptance | 0.63 | **1.00** |
| median quote | $0.42 | **$0.10** |
| quote → branch | 145 s | **6 s** |
| task types | small, medium, large | **small only** |

It bids **a quarter** of the operator's price, delivers in **6 seconds** instead
of 145, and has a **perfect** acceptance rate — by **specialising narrowly** in
`code/small` rather than taking everything. That is the visible strategy: pick a
task class you can solve near-deterministically, bid low, win the lease first.

### Priority 3 — Build honest usage reporting from the start

The skeleton computes `scope_ok` from a real `git diff` and `verification_state`
from a real exit code; only *usage* comes from you, and the terms require
*"usage you do not know is reported as unknown, never as zero."* Fabricating
zero usage is the one lie the protocol structurally leaves open — and it is
explicitly forbidden. Don't build a miner that does it.

### Priority 4 — Develop entirely offline first

```bash
# docs/QUICKSTART_LOCAL.md — no token, no network host, no chain
```

`localnet.py` gives you the full register → lease → solve → verify → publish loop
locally, and `reference_solver.py` proves the harness works with zero model
calls. Measure your acceptance rate and cost per attempt on your own repos
before bidding a cent.

### Priority 5 — Ask three questions before committing

1. **When is emission switched on?** `alpha_out_emission` is 0; without it the
   chain side pays nothing regardless of how much work you deliver.
2. **When will validators be configured in production?** Until then acceptance is
   the operator's own verify run, by their own admission.
3. **Which OPEN parameters land where** — particularly the carry-forward aging
   threshold and whether the 40 % per-hotkey weight cap survives.

`operations@heroncove.us` is on the chain identity.

### The path

1. Clone, run the localnet quickstart. Free, no chain, no token.
2. Implement `solve()` for **one narrow task class** you can do reliably.
3. Measure acceptance and cost per attempt locally.
4. Register ($0.13) and connect as an independent provider — the gateway already
   accepts them.
5. **Earn commercially first; treat emission as a later upside** — the gateway
   pays today, the chain does not.

---

## 7 · Rules you must keep

| Rule | Consequence |
|---|---|
| Deliver within the packet's `allowed_paths` | Out-of-scope diff → not accepted, earns nothing |
| The verify command must actually pass when re-run | Failed verification → not accepted |
| Report unknown usage as **unknown**, never zero | Explicit terms violation |
| Never self-declare `verified` | Computed from the real exit code |
| Attempt the **whole** task as specified | Partial delivery is not an Outcome |
| Provision your own runtimes, tools, models, hardware | *"Heron Cove supplies none of them"* |
| Ask must be at or under the client's reserve | Above → recorded and skipped, job stays queued |
| Complete a supplier record (W-9/W-8) before a treasury top-up | Balance shows `unpaid_kyc_pending`; emissions still earned |
| No delegation to the company validator | Not accepted |

---

## 8 · Device conditions

| | |
|---|---|
| **GPU** | **Not required by the protocol** — you may route to a hosted model |
| Runtime | Python; git; a bounded, credential-free subprocess environment for the verify command |
| Local dev | **No token, no chain, no network host** — `localnet.py` stands in for the gateway |
| Serving | No axon; the miner **polls** the gateway for leases rather than being queried |
| **The real requirement** | **A coding agent good enough to make someone else's tests pass**, at a cost below your bid |

> **Against your BEAM box (2 cores / 3.7 GB, Hetzner CX22):** genuinely
> workable. The miner is a polling client, not a served axon, and the protocol
> needs no GPU — clone, patch, run tests, push a branch. Whether *your solver*
> fits is a separate question, but nothing in the harness rules the box out.
> This is one of the few subnets here where that is true.

---

## 9 · Third-party conditions

| Dependency | Role | Note |
|---|---|---|
| **`api.ormas.ai` gateway** | Leases tasks, settles work, hosts the provider record | **Operator-run.** No gateway, no work. Also the settlement authority until validators are configured |
| **Heron Cove LLC** | Operator, customer-facing seller, *and* runs a miner and validator | Conflict disclosed in the README, the terms, and the public API's own `basis` field |
| **Client repositories** | You clone and patch real code | Access is per-task via the lease |
| **Your model provider** | Whatever your `solve()` calls | Entirely yours; unpaid by the operator |
| **git** | Branch delivery, scope check via `git diff` | Core to the protocol |
| **finney** | Registration, weights | **Currently emitting nothing** |
| Signature scheme | Ed25519 on the dev subnet; **sr25519 is the SN76 target** | Noted as a gap |

---

## 10 · Risks

1. **The subnet emits nothing.** `alpha_out_emission = 0`. Whatever the economics
   doc plans, the chain currently pays no one.

2. **Acceptance is not independent.** By the operator's own admission, every
   production receipt so far reflects their own trusted miner's verify run. The
   reference validator ships, but no validators are configured in production.

3. **The operator is on every side of the market** — seller to customers,
   gateway, a miner, and a validator. Disclosed clearly, but it is a real
   structural conflict until third-party validators gate settlement.

4. **Eight days old on a twice-recycled netuid.** Phylax → `nun` → Ormas, with
   the chain identity stating it is *"not a continuation."* Anyone holding α from
   the previous occupants holds a claim on a different project.

5. **Pool depth is τ462** — the thinnest in this folder by a wide margin. Any
   meaningful buy or sell moves the price hard.

6. **Ticket sizes are tiny.** Median quotes of $0.10–$0.42, nine tasks settled.
   Real demand at scale is unproven.

7. **Miners carry all attempt risk.** You pay for every attempt; a miss pays
   nothing. At 0.63 acceptance the operator's own miner loses money on more than
   a third of its work.

8. **Excess emission goes to the owner UID.** If owed USD stays below the epoch's
   capacity — which it will at current volumes — the remainder is not distributed
   to miners.

9. **Treasury top-ups are counsel-gated and default-off.** The mechanism that
   clears a carried balance may never be enabled; the stated fallback is a USD
   payout through a payment provider.

10. **Many economics parameters are formally OPEN**, including the carry-forward
    aging threshold, the dispute window, and the TAO/USD reference sources.

11. **The miner terms are a draft** *"pending counsel review"* and *"not yet in
    force."*

---

## 11 · Documentation notes

Among the most forthright in this folder. The pattern is consistent: state the
gap in the same place as the claim.

| Element | Status |
|---|---|
| Conflict of interest | Disclosed in README, terms, **and the public API response body** |
| Own miner labelled | `operator-run` in `/v1/public/providers` |
| Compensation model | Headed *"planned — not yet live"* |
| Undecided parameters | Listed as **OPEN**, *"recorded here only so nobody invents them"* |
| Known gaps section | *"documented rather than papered over"* |
| Miner terms | Marked **DRAFT, pending counsel review** |
| Licence | **MIT** for protocol, thin client, reference miner and reference validator |
| Not-a-continuation | Stated in the on-chain identity itself |

One inconsistency worth noting: the README's disclosure says the compensation
model is *"planned — not yet live,"* while the Known Gaps section says *"Firm
asks are live"* with nine settled tasks. Both are true — the **gateway** pays
commercially today; the **chain** compensation model does not exist yet. The
docs could separate those two more sharply than they do.

---

## 12 · Verdict

**Ormas is the most interesting economic design I have read in this folder, and
it is eight days old with the emission switched off.**

The idea is genuinely novel here. Every other coding subnet pays for effort —
tokens, turns, attempts — and then tries to bolt quality measurement on top.
Ormas inverts it: **the client's own test is the specification, the miner posts a
firm price, and payment happens only when that test passes on someone else's
machine.** There is no leaderboard to game because there is no score — an
Outcome is accepted or it is not. That removes an entire category of failure
modes that SN40, SN97 and others spend hundreds of lines defending against.

The engineering supports it. The skeleton **refuses to let a miner self-certify**:
`scope_ok` comes from a real `git diff`, `verification_state` from a real exit
code, and unknown usage must be reported as unknown rather than zero. The
reference validator that independently re-clones and re-runs is in the repo, MIT
licensed. The whole loop runs offline with no token and no chain. And the
economics doc solves a real problem — reconciling fixed alpha emission with
variable USD demand — with a carry-forward ledger that is *"a pure function of
chain weights, chain emissions, the published prices, and the accepted set."*

**The honesty is the most unusual thing about it.** The operator runs the
gateway, a miner and a validator, and says so in the README, the terms, *and the
public API's own response body*, where its own provider row is labelled
`operator-run`. It states that acceptance is not currently independent. It lists
its undecided parameters as OPEN so nobody invents them. It marks its own miner
terms as an unreviewed draft. Very few projects volunteer that much.

**But the gap between the design and the network is total.** `alpha_out_emission`
is **zero** — the chain pays nothing to anyone. No validators are configured, so
acceptance is the operator's own verify run. Total settled volume is nine tasks
at ~$0.42. Pool depth is τ462. And netuid 76 has now been three different
projects.

What separates it from the other pre-launch subnets here is that **the
commercial side already works**: there is a live gateway, a public provider
record, and — notably — **one independent provider already delivering accepted
work at a 1.00 acceptance rate**. That is a real customer-facing product, which
is more than SN119 or SN20 can show.

### Recommended path

1. **Do not size this on emission.** The chain pays zero today. If you enter, do
   it for the **commercial** revenue through the gateway, and treat emission as a
   later option.
2. **Clone and run the localnet quickstart** — free, no token, no chain. Measure
   your acceptance rate and cost per attempt before bidding.
3. **Copy `provider-0af465`'s strategy**: specialise narrowly (`code/small`), bid
   low, deliver fast. Perfect acceptance at $0.10 beats 63 % acceptance at $0.42.
4. **Register ($0.13)** — trivial, and the gateway already accepts independent
   providers.
5. **Watch three numbers:** `alpha_out_emission` becoming non-zero; a validator
   count appearing in production; and a *second* independent provider. The
   watchdog now tracks the repo and `ormas.ai` for exactly this.

---

## 13 · Sources

**Code** (MIT)
- https://github.com/heroncovelabs/ormas-subnet — 38 files
- Local: `/root/Bittensor/76/ormas-subnet`
- `README.md`, `MINER_TERMS.md` (draft), `docs/protocol.md` (350 ln),
  `docs/economics.md`, `docs/INSTALL.md`, `docs/CONTRACT.md`,
  `docs/DECISIONS.md`, `docs/QUICKSTART_LOCAL.md`,
  `ormas_subnet/{protocol,client,skeleton,validator,localnet,reference_solver}.py`,
  `neurons/{miner,validator,localnet_demo}.py`, 10 test modules

**Live API** (fetched 2026-09-14)
- `GET https://api.ormas.ai/v1/public/providers` — 2 providers, one independent
- `https://api.ormas.ai/health` — 200
- https://ormas.ai · https://ormas.ai/docs

**Chain** (finney, block 9,062,494)
- `Subtensor.subnet(76)`, `metagraph(76)`, `weights(76)`, `recycle(76)`,
  `get_all_commitments(76)`, `SubnetIdentitiesV3(76)`
- **`alpha_out_emission = 0`**, `alpha_out = 0`, registered block 9,003,844

**This folder**
- [`notification.md`](notification.md) — the watchdog logged the `nun → Ormas`
  rename and the repo/website appearing on chain
- [`SN076-PHYLAX-HISTORICAL.md`](SN076-PHYLAX-HISTORICAL.md) — the previous occupant

**Price reference**
- TAO ≈ $256 → α ≈ $1.27 at 0.004978 TAO/α
