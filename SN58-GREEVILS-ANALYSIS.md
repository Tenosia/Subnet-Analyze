# SN58 — Greevils (Confidential Autonomous Trading on Hyperliquid)

| | |
|---|---|
| **netuid** | 58 (`greevils`, symbol `خ`) |
| **Chain identity** | name `greevils` · github `greevils-ai/greevils-cli` · url `www.greevils.ai` · contact `atlas@greevils.ai` |
| **Owner hotkey** | `5EPXZrLxMmV2ShUFXvffdGXZoyUrYwEKMHZbVfmPnmjJ3GHz` — **holds UID 0** |
| **Owner coldkey** | `5CLUzEqecEfGFxMwHSU5vbgzpFQCGZuC56DDX354JKe69gtJ` |
| **Registered at block** | 8,511,017 |
| **Repos (4 public)** | `greevils-cli` · `greevils-validator` · `greevils-public-harness` · `greevils-docs` |
| **Private repo** | `greevils-api` — submission + build backend, organizer only |
| **API** | `https://api.greevils.ai` (only `/docs` responds publicly) |
| **Local checkouts** | `/root/Bittensor/58/{greevils-cli,greevils-validator,greevils-public-harness,greevils-docs}` |
| **Live state (2026-08-29, block 8,951,884)** | tempo 360 |
| **Price** | 0.009837 TAO/خ (**≈ $2.518**) · tao_in τ1,077.31 · alpha_in 109,512 · alpha_out 426,012 |
| **UIDs** | 256 registered · **1 earning (UID 37, 100 %)** · 6 validator permits · 5 with dividends |
| **On-chain account claims** | **42** · **gva1 approval commitments: 0** |
| **Registration cost** | **0.10 TAO** (~$25.60) |
| **BURN_UID** | **0** — i.e. the owner's own hotkey |

> Live from finney, on-chain commitments, the weight matrix, and the four public
> repos on 2026-08-29. Where the docs and the code disagree I record both.

---

## 1. Goal of the subnet

Pay people to run **profitable autonomous trading agents**, and make the whole
thing verifiable — both *that the agent is the code it claims to be* and *that
the returns are real*.

The design is genuinely unusual and worth stating precisely:

1. You write a trading agent (a directory with an `entry.py`).
2. `greevils package` zips and **encrypts it on your machine**. The plaintext
   never leaves. You keep the `AGENT_KEY`.
3. `greevils submit` uploads only the **ciphertext**. The organizer's API bakes
   it together with the **public harness** into a GCP Confidential Space TDX
   image and publishes its content digest **D**.
4. `greevils deploy` launches that exact image as a TDX VM **on your own GCP
   project**. Inside the TEE the harness decrypts your agent, generates a
   Hyperliquid trading key that never leaves the trusted process, and runs your
   code as a **separate, lower-privileged OS user**.
5. Your agent trades by making plain HTTP calls to a **method-whitelisted
   loopback API**. It can trade; it can never withdraw.
6. `greevils commit` publishes a one-time on-chain proof that you control the
   Hyperliquid account, binding it to your hotkey.
7. The validator reads the claim, asks the API whether the account is a genuine
   attested agent, and scores the account on **actual trading performance**.

The trust anchor is the digest **D**. Because D is built from the *public*
harness plus your ciphertext, attestation of D simultaneously proves the custody
guarantees and the agent's identity.

**The threat model is honest about the real adversary.** From
`ARCHITECTURE.md`: Confidential Space protects the workload from the host and
the organizer — *but not from code running inside it*, so the agent is the
threat. In one Python process there is no way to hide a key from the agent
(`__name` is name-mangling; `gc.get_objects()` reaches everything). The only
real boundary is an OS process boundary. That reasoning is correct and it is
rare to see it written down.

**Ground truth is the Hyperliquid account balance.** No benchmark, no model
judge, no synthetic task. Real money, real fills, real drawdown.

---

## 2. What you do as a miner

Two lanes, and they are very different.

### Lane A — Agent (the product)

```bash
greevils package ./my-agent               # encrypt locally, prints AGENT_KEY
greevils submit  ./my-agent.enc           # ciphertext only
greevils status  a1b2c3d4                 # QUEUED → BUILDING → PUBLISHED, prints digest D
greevils deploy  a1b2c3d4 \
  --agent-key "$AGENT_KEY" --master-account 0xYourEOA \
  --env-file .env --project your-gcp-project --zone us-central1-a
greevils commit  --netuid 58 --coldkey ck --hotkey hk \
  --hl-address 0xACCT --signature 0xSIG
```

`deploy` runs entirely on your infrastructure via `gcloud`: it enables
`compute` + `confidentialcomputing`, creates a workload service account, and
launches a `--confidential-compute-type=TDX` VM from the
`confidential-space-images` family, default machine type **`c3-standard-4`**.
Your `.env` is packed into VM metadata — the organizer never sees it and it is
**not** part of the attested digest.

### Lane B — Human

Trade a normal Hyperliquid account through the Greevils builder app and
`greevils commit` it. No TEE, no GCP, no code. **Humans face no eligibility
gate at all** — they just have to survive elimination and have traded at least
once. Their upside is bounded by a dollar cap instead (§3.5).

### The on-chain commitment

128-byte Raw field: `base64( hl_address(20B) || signature(65B) )` = 116 chars.
The signed message is *rebuilt* by the validator from the **committing hotkey**:

```
Greevils Hyperliquid ownership claim
hotkey: <ss58>
hyperliquid: <0xaddr lowercased>
```

Copy someone else's blob and it rebuilds under *your* hotkey, so the signature
no longer recovers to `hl_address` and the claim is rejected. Neat and correct.

---

## 3. Scoring logic

`greevils-validator/incentive.md` is 300+ lines and is the single source of
truth. I verified the key paths against `tournament.py` and `scoring.py`.

### 3.1 A unified pairwise tournament

You are **not** scored in isolation. Every eligible miner plays every other —
agents and humans in **one** tournament, cross-type included.

```
overlap W = [ max(start_A, start_B), now ]      floored at 30 days
winner of each pair banks (score_win − score_lose);  loser banks 0
Score(you) = Σ over all opponents  max(0, score_you − score_o)
```

The 30-day floor stops a good young account being reduced to a one-day overlap.
Two accounts both under 30 days are judged on full history.

### 3.2 Eligibility (lifetime) and elimination (instant DQ)

| Eligibility (agents only) | Threshold |
|---|---|
| Runtime | ≥ **60 days** since first trade |
| Active days | ≥ **40 days** with ≥ 1 fill |
| Executed value | ≥ **25 × A** lifetime (`A` = time-weighted avg equity) |
| Return | Σ daily % ≥ **1.5 %** |

Executed value counts **both sides**, so 25×A ≈ 12–13 round-trips of your book.

| Elimination (everyone) | Trigger |
|---|---|
| **Builder app only** | *Any* fill not routed through the Greevils builder app (~5 bps) |
| **Whitelist only** | Any pair outside the **47** allowed |
| **No spot** | Any spot trade — perps only |
| **Equity floor** | Balance below **$1,000** on any day (a withdrawal counts) |
| **Dead agent** | **14** consecutive zero-trading days (after a 7-day grace) |

Drawdown is **not** an elimination — it just devastates your score. There is
**no leverage limit**.

### 3.3 The five factors and the utility

```
U =  ln(1 + R)                                    # return
   + 0.08 · ln(1 + X/1000)                        # absolute $ profit
   − 0.308 · (D/0.10)²                            # drawdown        ← harshest
   − 0.15  · softplus(V/0.02 − 1)                 # downside vol
   − 0.75 · min(1,(1+non_profit_days)/14) · max(0, K − 0.14)   # concentration
```

The anchors are stated explicitly and are the most useful thing in the document:

| Term | Anchor |
|---|---|
| Absolute profit | $100k profit ≡ a +45 % return |
| **Drawdown** | **a 15 % drawdown erases the credit for a 100 % return**; 10 % costs a 36 % return |
| Downside vol | 5 % daily downside-vol ≡ a 25 % return penalty; nothing below 2 % |
| Concentration | all profit in one lucky day ≡ a ~90 % return penalty; free if spread over 7+ days |

**Drawdown is quadratic and dominates everything.** Mediocre-but-smooth beats
brilliant-but-violent, by design.

The concentration ramp advances **only on non-profit days** — keep printing green
days and it freezes near 1/14 and shrinks as K falls.

### 3.4 Transform and haircuts

```
G = (e^(1.5·U₊) − 1)/(e^1.5 − 1)     U₊ = max(0,U);  U ≤ 0 → G = 0
M_P  = 0.5 if trailing-30d PnL < 0
M_EV = 0.5 if Q_EV < 4  (Q_EV = 14d executed value / 14d avg equity)
M    = min(M_P, M_EV)                # worst single haircut, never 0.25
score = G · M
```

α = 1.5 means each doubling of your book relative to a rival multiplies your
matchup score by **2^1.5 ≈ 2.83**.

**Longevity bonus:** pre-overlap days credited at `2^(−age/90)`, κ = 0.5,
**upside-only, into R and X only**. A whole lifetime record caps at roughly one
extra live window. A bad past costs nothing; a good past never buys back risk.

### 3.5 Daily ground truth — flows cannot fake performance

```
P>0, N>0   →  P / max(S+N, $10k)        # profit + deposit: diluted
P>0, N≤0   →  (P+N) / max(S, $10k)
P≤0, N>0   →  (P/S)·(1 + N/(S+N))       # loss + deposit: loss RATE amplified
P≤0, N≤0   →  P / (S+N)                 # full loss, no floor
```

The **$10,000 profit-day denominator floor** is the sharpest practical detail: a
$300 gain on a $1,000 account reads **+3 %, not +30 %** — while a $300 loss on
$1,000 is a full **−30 %**. No upside inflation, no downside leniency. **Below
$10k of capital you are structurally handicapped.**

### 3.6 From scores to emissions

```
human_share = min( 50%, 0.1 · Σ max(0, human_PnL_$) / emission_value_$ )
agent_share = 1 − human_share
your_weight = pool_share · Score(you) / Σ Score(your pool)
```

Both pools are shared out by the **same unified score** — your type only decides
which pool you draw from. Anything unassigned **burns to `BURN_UID`, which
defaults to 0**.

**At current prices one round's emission is ≈ $18,132.** For humans to reach the
50 % cap the winning humans would collectively need **≈ $90,661 of PnL in one
day**. Realistically the human lane is a few percent and agents absorb ~95 %.

### 3.7 The agent gate — no grace period

`incentive.md` and `tournament.py:166` agree exactly. An agent earns **only** when
all three hold, always:

1. **Open-sourced** — code public
2. **Approved** — the highest-staked validator manually reviews that public code
   and commits `gva1:<base64(sha256(canonical_list))>` on chain
3. **≥ 60 days runtime** — plus the full eligibility gate

```python
if not miner.open_sourced:
    return False, ["agent is not open-sourced and approved"]
if m.runtime_days < REQUIRED_RUNTIME_DAYS:
    return False, [...]
failures = check_eligibility(miner.account_type, m)
```

Being a *valid* agent (`RUNNING + HEALTHY + PASS`) only classifies you as an
agent; it grants **no** eligibility. The doc says plainly: *"Expect the agent
pool to burn until the first agent qualifies."*

**A lone eligible miner earns nothing** — the tournament needs a rival to form a
pair.

---

## 4. Live competition landscape

### 4.1 One UID earns everything, and it has no commitment

```
 uid  incentive     emission        stake     divid  vperm
  37  1.000000      147.601           0.0   0.00000  False   ← 100 % of the miner pool
   0  0.000000       84.615      748525.8   0.57327  True    ← owner, BURN_UID
   1  0.000000       53.966      477249.5   0.36562  True
```

`E[37] = 147.601 α/tempo = 0.41 × 360` — precisely the entire miner pool.

The on-chain weight matrix shows unanimity:

| Setter | Stake | Weight |
|---|---|---|
| UID 0 (owner) | 748,526 | **100 % → UID 37** |
| UID 1 | 477,250 | **100 % → UID 37** |
| UID 10 | 40,196 | **100 % → UID 37** |
| UID 33 | 31,071 | **100 % → UID 37** |
| UID 36 | 8,662 | **100 % → UID 37** |
| UID 12 | 2,798 | 100 % → UID 0 (burn) |
| UID 91 | 0 | 100 % → UID 0 (burn) |

**But UID 37 has no on-chain commitment.** Verified two independent ways:

- `get_all_commitments(58)` returns **42** entries, cleanly decoded, no errors —
  UID 37's hotkey (`5DLpF3EHyn5aMa…`) is **not among them**
- `get_commitment(58, 37)` returns `''`

And `evaluation.py` calls `collect_verified_claims(subtensor, metagraph, netuid)`
fresh every round — `commitments.py` reads the chain and caches nothing. **The
published validator code, run against the chain as it stands today, would score
UID 37 zero.**

Meanwhile **none of the 41 registered hotkeys that *do* hold valid claims earn
anything at all.**

I cannot determine the cause from public data. The candidate explanations are:
the deployed validator differs from the published repo; the binding was
established when a commitment existed and the deployed build persists it; or the
weights are stale. **I am flagging this as an unexplained, verified anomaly
rather than guessing.**

### 4.2 No agent can currently be approved

Approval requires the top-staked validator to publish an approved-digest list to
`greevils-api` and commit `gva1:<hash>` on chain. Scanning all 42 commitments:

> **`gva1` approval commitments: 0**

With no approval commitment, `get_approved_digests` returns an empty set, so
`open_sourced` is False for every agent, so **no agent passes
`is_in_tournament`**. Under the published rules the agent lane — ~95 % of
emission — should be **entirely burning**. It is not; UID 37 takes it.

### 4.3 The rest of the field

- **256 UIDs registered**, 42 with account claims, 41 of those registered.
- **Zero** of the claim-holders earn anything.
- Dividends are concentrated: UID 0 at 57.3 %, UID 1 at 36.6 %, then 3.1 / 2.4 /
  0.66 %. Two hotkeys hold ~94 %.
- Only 6 validator permits.

### 4.4 Repo maturity — the strongest of any subnet analysed this week

Unlike SN47's two-commit dump, this has real, dated engineering history:

```
2026-07-23  feat: drop agent grace period
2026-07-20  feat: operator ban list
2026-07-17  feat: score only after 4 full utc days
2026-07-15  fix:  keep transition-day flows
2026-07-10  feat: maturity ramp for young accounts
2026-07-10  feat: score miners only after 30 days
2026-07-09  feat: floor profit-day return denominator
2026-07-09  revert: restore $1000 equity floor
2026-07-08  fix:  raise equity floor to $10000
2026-07-07  fix:  overlap window floor
```

That is a mechanism being tuned against live behaviour — including a **revert**,
which is a healthy sign. Four public repos, a threat model, and a 300-line
incentive spec.

---

## 5. Miner economics

Subnet emits **1.000 α/block = 7,200 α/day**; 18 % owner cut, 41 % miners, 41 %
validator dividends → **miner pool = 2,952 α/day**.

At α = 0.009837 TAO and TAO ≈ $256 → **α ≈ $2.518**:

### Today

| Recipient | Share | α/day | TAO/day | USD/day | USD/mo |
|---|---|---|---|---|---|
| **UID 37 (sole earner)** | **100 %** | **2,952** | **29.04** | **~$7,434** | **~$223,000** |
| All 41 claim-holders | 0 % | 0 | 0 | $0 | $0 |
| Owner UID 0 (18 % cut + 57.3 % dividends) | — | 2,988 | 29.39 | **~$7,526** | ~$225,800 |

**The owner captures 41.5 % of total emission** — notably the *lowest* of the four
subnets analysed, and it comes from the owner cut plus legitimately staked
dividends rather than from a fallback that pays itself.

### Costs to compete

| Item | Cost |
|---|---|
| Hotkey registration | **0.10 TAO ≈ $25.60** |
| GCP Confidential Space TDX VM (`c3-standard-4`, default) | **~$0.20/hr ≈ $145/mo** |
| **Trading capital** | $1,000 hard floor — but the **$10k profit-day denominator floor** makes anything under $10k structurally uncompetitive |
| Builder fee | ~**5 bps** on every fill, mandatory |
| Turnover cost | 25×A lifetime + Q_EV ≥ 4 per fortnight ⇒ ~2 round-trips/week of fee drag |
| **Time** | **≥ 60 days** before an agent can earn one satoshi |
| GPU | **None.** No model, no inference, no training |

**This is the cheapest *infrastructure* of any subnet I have analysed — ~$170/mo
all-in — and the most expensive *precondition*: a genuine 60-day profitable
trading record, plus a manual code review, plus open-sourcing your alpha.**

Realistic budget to be a serious contender: **$25,000–100,000 of trading
capital** (well above the $10k denominator floor, with room to survive drawdown
above the $1,000 DQ), ~$170/mo of infrastructure, and two months before any
revenue.

### Liquidity

`alpha_in` 109,512 against τ1,077.31. The sole earner mints 2,952 α/day = **2.7 %
of pool depth per day** against `subnet_volume` of 21,219 α. That is thin —
daily selling at that rate would move the price materially.

---

## 6. How to become the king

The honest framing: **SN58 pays one UID everything, and the documented path to
displacing it takes a minimum of 60 days plus a manual approval that has never
once been granted on chain.**

### Priority 1 — Resolve the two anomalies before committing capital.

Email `atlas@greevils.ai` and ask two specific questions:

1. **Why does UID 37 earn 100 % with no on-chain commitment**, while 41 hotkeys
   holding valid claims earn zero? Is the deployed validator the published one?
2. **When will a `gva1` approval be issued?** There are zero on chain. Without
   one, no agent can ever pass `is_in_tournament`, and the documented agent lane
   is unreachable by construction.

Their answers determine whether this subnet is minable at all. Do not fund a
trading account before you have them.

### Priority 2 — Start the 60-day clock *now*, on the human lane.

This is the key strategic insight and it costs almost nothing:

- **Humans face no eligibility gate.** No runtime minimum, no return hurdle, no
  turnover hurdle. Survive elimination and trade once.
- **The tournament is unified.** Your score is computed against agents *and*
  humans, so a human score is directly comparable — and beating an agent raises
  your score exactly as much as beating a human.
- Runtime accrues from your **first trade**, so a human account started today is
  a 60-day-old account in two months, ready to convert.

So: register, commit a normal Hyperliquid account, trade through the builder app,
and accumulate the track record *while* you develop the agent. You earn from the
(small) human pool immediately and bank the longevity bonus at the same time.

### Priority 3 — Optimise for drawdown above all else.

Everything about this scorecard says the same thing. λ = 0.308 with D₀ = 0.10 and
a **quadratic**:

| Your max drawdown | Return needed just to break even on the scorecard |
|---|---|
| 5 % | ~8 % |
| 10 % | **~36 %** |
| 15 % | **~100 %** (a full double) |
| 20 % | ~220 % |

A strategy that makes 30 % with a 5 % max drawdown crushes one that makes 100 %
with a 15 % drawdown. Size small, stop early, and never let a position run.
Given there is **no leverage limit**, the temptation runs exactly the wrong way.

### Priority 4 — Spread your wins across days, and keep trading.

Concentration K is the Herfindahl of your profit days; free above ~7 effective
profit days (K₀ = 0.14). Its ramp advances **only on non-profit days**, so a
steady drip of small green days both lowers K *and* freezes the ramp. One lucky
day followed by two idle weeks is a ~90 % return penalty.

This argues strongly for **high-frequency, small-edge, many-small-wins**
strategies over swing trades. Which conveniently also satisfies Q_EV ≥ 4.

### Priority 5 — Keep capital above $10,000 and never near $1,000.

The profit-day floor means a $5,000 account has its gains halved in the scoring
while its losses are counted in full. And a single bad day that dips below
$1,000 at the 00:00 UTC snapshot is a **permanent DQ**. Humans: keep the account
in **Standard mode**, not Unified or Portfolio Margin, across midnight UTC — the
snapshot misreads equity in those modes and can trip the floor.

### Priority 6 — Route every single fill through the builder app.

One off-app fill is an indelible DQ (`db.mark_disqualified`, never re-checked).
Not a haircut — permanent. Also: perps only, 47 whitelisted pairs only, never go
14 days dark.

### Priority 7 — Decide whether you will actually open-source your alpha.

To earn from the **agent** pool you must publish your trading code publicly and
have a competitor's validator manually review it. That is a real, permanent cost
that most profitable traders will refuse to pay. Be clear with yourself about it
before spending two months building.

### The path

1. Ask the two questions in Priority 1. Wait for answers.
2. Register (0.10 TAO). Commit a **human** Hyperliquid account funded at
   $25k+ and start trading through the builder app today — the clock is the
   scarce resource.
3. Build the agent in parallel; `package`/`submit`/`deploy` on a
   `c3-standard-4` TDX VM (~$145/mo) and let it accrue runtime.
4. Audit `greevils-public-harness` yourself before handing it a key — that is
   precisely why it is published.
5. At day 60, if and only if a `gva1` approval mechanism is demonstrably live:
   open-source, request approval, and convert to the agent lane.
6. Track drawdown as your primary KPI, not return.

---

## 7. Rules you must keep

| Rule | Consequence if broken |
|---|---|
| Every fill through the Greevils builder app (~5 bps) | **Permanent, indelible DQ** |
| Only the 47 whitelisted pairs | Instant DQ |
| Perps only — no spot (`@index` or `BASE/QUOTE`) | Instant DQ |
| Balance ≥ $1,000 every day (withdrawals count) | Instant DQ |
| No 14 consecutive zero-trade days (7-day grace) | Instant DQ (abandonment) |
| Humans: Standard mode across 00:00 UTC | Snapshot misreads equity → can trip the $1,000 DQ |
| Agent: open-sourced **and** gva1-approved **and** ≥ 60 days | Earns **0** — no grace period |
| Agent: ≥ 40 active days, Σ daily % ≥ 1.5 %, ≥ 25×A executed value | Score 0 this round |
| Need at least one other eligible miner | Lone eligible miner scores 0; it burns |
| Don't try to fix a losing % with a deposit | Loss *rate* is amplified (anti-rescue) |
| Duplicate HL address across hotkeys | Single weight split evenly across positions |
| Operator ban list (`BANNED_ADDRESSES`) | Dropped before scoring |

---

## 8. Device / hardware conditions

**No GPU anywhere in this subnet.** That is the headline.

### Miner — agent lane

| | |
|---|---|
| Compute | **GCP Confidential Space TDX VM**, default `c3-standard-4` (4 vCPU) |
| Requirement | A GCP project with `compute` + `confidentialcomputing` APIs, `gcloud` auth |
| Image | `confidential-space-images` family, `--confidential-compute-type=TDX` |
| Ports | 8443 (attestation token server), 8080 (participant UI, MASTER_ACCOUNT-signed) |
| Cost | **~$0.20/hr ≈ $145/mo** |
| Local | Any laptop for `package` / `submit` / `commit` |
| **Trading capital** | $1,000 hard floor; **$10,000 is the real floor**; $25k+ to be competitive |

### Miner — human lane

Nothing but a funded Hyperliquid account and the builder app. **Zero infrastructure.**

### Validator

| | |
|---|---|
| Compute | A small VPS — pure Python, SQLite (`greevils_validator.sqlite`) |
| GPU | **None** |
| Work | Poll Hyperliquid, snapshot daily balances, run the pairwise tournament, set weights |
| Deps | `requests`, `eth_account`, `bittensor` |
| External | `api.greevils.ai` (agent validity), CoinGecko (TAO/USD) |
| Cadence | Scoring once per UTC day at the 00:00 boundary; `BLOCKS_PER_ROUND = 7200` |

> **Against your BEAM box (2 cores / 3.7 GB):** it can comfortably run the
> **validator**, and it can run the CLI for `package`/`submit`/`commit`. It
> cannot host the agent — that must be a GCP Confidential Space TDX VM by
> construction. **This is the only subnet of the four where your existing box is
> genuinely sufficient for a real role.**

---

## 9. Third-party conditions

| Dependency | Role | Failure mode |
|---|---|---|
| **Hyperliquid** | The entire ground truth — balances, fills, PnL | Total dependency. An API change, an outage, or a delisting breaks scoring. All performance risk is Hyperliquid counterparty risk. |
| **Greevils builder app** | Every fill must carry its ~5 bps | Mandatory routing. `BUILDER_EXCLUSIVITY_START` gates when the rule begins. |
| **GCP Confidential Space** | The TEE that hosts every agent | **Single cloud, single vendor.** No AWS Nitro, no Azure, no bare metal. If your GCP project is suspended you are off the air. |
| **Intel TDX** | Hardware isolation | Single TEE vendor. |
| **Intel Trust Authority** | Attestation verification (`--ita-region`, `ita-api-key`) | Optional token backend; adds an Intel dependency. |
| **`greevils-api`** | **Private.** Builds your image, holds `RUNNING/HEALTHY/PASS`, serves approved lists | **The organizer decides who is an agent.** You cannot self-attest into the agent pool. Only `/docs` is public. |
| **`greevils-public-harness`** | The in-TEE trusted process holding your trading key | Public and auditable — the right call, and the mitigation for the above |
| **CoinGecko** | TAO/USD for the human dollar cap | Missing price → `human_share = 0`, humans earn nothing that round (degrades safely) |
| **`eth_account`** | EIP-191 signature recovery for claims | — |
| **finney** | Registration, claims, gva1 approvals, weights | 128-byte Raw commitment limit shapes the whole claim design |

Notably **absent**: no Hugging Face, no model weights, no GPU cloud, no dataset
dependency. The surface is small — but two links in it (Hyperliquid and GCP) are
absolute.

---

## 10. Risks

1. **UID 37 earns 100 % with no on-chain commitment.** Verified two ways
   (`get_all_commitments` = 42 entries, no errors, UID 37 absent;
   `get_commitment(58,37)` = `''`). Five of seven weight-setters, including the
   owner and the largest external validator, agree on it. Meanwhile all 41
   hotkeys with valid claims earn zero. **The published validator code would not
   produce this weight vector.** Unexplained.

2. **Zero `gva1` approvals exist.** No agent can pass `is_in_tournament`, so the
   agent lane — ~95 % of emission — is unreachable under the published rules.
   The docs acknowledge the design intent (*"expect the agent pool to burn"*) but
   nothing is burning.

3. **`BURN_UID` defaults to 0, which is the owner's hotkey.** Same anti-pattern
   as SN47: the "burn" is a transfer to the owner. Currently UID 0's incentive is
   0.0 so it is not firing — but two validators (UID 12, UID 91) are already
   routing 100 % there.

4. **The agent gate is, in practice, a permission.** Approval requires manual
   review by *the highest-staked validator* — which is currently the owner
   (UID 0, 57.3 % of dividends). That is a discretionary, off-chain,
   single-party decision over who may earn from 95 % of emission.

5. **You must open-source your trading alpha to earn.** For most profitable
   traders this is disqualifying. A working strategy published publicly is a
   strategy with a decaying edge — and you publish it *before* being paid.

6. **60 days of unpaid runtime.** Two months of capital at risk, infrastructure
   cost, and fee drag before an agent can earn anything.

7. **You are trading real money with real loss risk.** Unique among the subnets
   analysed: your downside is not opportunity cost, it is your capital. There is
   **no leverage limit**, and a drawdown is a permanent scar in that window's
   score.

8. **Total Hyperliquid dependency.** Every input is one venue's API. Counterparty,
   liquidity, delisting, and outage risk all pass straight through.

9. **Single-cloud, single-TEE.** GCP Confidential Space with Intel TDX is the
   only supported deployment. No second source.

10. **The organizer classifies agents.** `greevils-api` is private and its
    `RUNNING/HEALTHY/PASS` verdict decides your pool. The harness is public
    (good), but the classifier is not.

11. **Extreme concentration today.** 256 UIDs, 1 earning, 2 hotkeys holding 94 %
    of dividends, 6 permits.

12. **The $10,000 profit-day floor is a soft capital gate.** Undercapitalised
    miners are systematically handicapped: gains scaled down, losses counted in
    full.

13. **Thin alpha liquidity.** 2,952 α/day minted against 109,512 α of depth and
    21,219 α of volume — 2.7 % of depth per day.

14. **A permanent DQ from one mistake.** A single off-app fill, one spot trade,
    one unlisted pair, or one midnight dip below $1,000 ends that account
    forever. `db.mark_disqualified` is never re-checked.

15. **Constants are declared tunable.** *"Constants are defaults and may be
    tuned; this document reflects the current configuration."* Most are
    `os.getenv`-overridable per validator, so two validators could in principle
    score differently.

---

## 11. Documentation defects found

Far fewer than the other three subnets — the docs are unusually good.

| Claim | Where | Reality |
|---|---|---|
| *"Agent lane is alive from day one: before any agent open-sources, closed-source agents earn with NO eligibility gate… once any agent open-sources (the latch)"* | `rewards.py` module docstring | **Stale.** `tournament.py:166` now requires `open_sourced` unconditionally — *"accepted for signature compatibility but no longer gates anything"*. Removed in commit `2e08a01`, "drop agent grace period". `incentive.md` is correct. |
| *"GRACE (no agent approved yet): any valid agent earns"* | `approvals.py` module docstring | Same stale grace-period description |
| `latched` computed in `tournament_weights` | `tournament.py:305` | Computed, passed to `is_in_tournament`, and **ignored**. Dead code. |
| `greevils commit --netuid 1` | `greevils-cli/README.md` | Example uses netuid **1**; the live subnet is **58** |
| `BURN_UID = 0` described as "the burn UID" | `config.py:52`, `incentive.md` §7 | UID 0 is the **owner's hotkey**, not an incinerator |
| Chain identity `github_repo` | on-chain `SubnetIdentitiesV3` | Points at `greevils-cli`, not `greevils-docs` (the map) — minor |

To the project's credit: `incentive.md` and `tournament.py` agree on every
substantive rule I checked, including the exact constants (λ=0.308, D₀=0.10,
μ=0.15, V₀=0.02, η=0.75, K₀=0.14, α=1.5, κ=0.5, H=90, cap=50 %, k=0.1). The two
stale docstrings are leftovers from a removed feature, not live contradictions.

---

## 12. Verdict

### Against the subnets analysed this week

| | **SN58 Greevils** | **SN47 Feval** | **SN103 Capcomp** | **SN90 KubeTEE** |
|---|---|---|---|---|
| Type | TEE algo-trading | Verifiable LoRA eval | LoRA composition | DePIN conf. compute |
| Ground truth | **Real Hyperliquid PnL** | Benchmark rows | Benchmark rows | GPU inventory |
| **Entry cost** | 0.10 TAO + **$25k trading capital** | 0.05 TAO ≈ $12.80 | 1 TAO ≈ $256 | 0.0005 TAO + **$1.5M–4M** |
| **Infrastructure** | **~$145/mo, no GPU** | One 24–48 GB GPU | One 32–48 GB GPU | 8-node TDX datacenter |
| Time to first earn | **≥ 60 days** (agent); immediate (human) | Immediate | 2 days | n/a |
| Can you start today? | Human lane yes; agent lane **blocked** (no gva1) | Yes (resolve repo/live gap) | **Yes** | **No** |
| Seats that pay | Proportional by score | 3 (62.5/25/12.5 %) | 10, rank 1 takes 45 % | Proportional |
| Miners earning | **1 of 256** | **0** (owner takes all) | **7 of 25** | **1 of 95** |
| Owner capture | **41.5 %** | **100 % of miner pool** | 76.6 % | 67.7 % |
| Repo maturity | **4 repos, real history, threat model** | 2 commits, 1 day old | Mature + adversarial tests | Mature + CI |
| Doc quality | **300-line spec w/ anchors** | 56-line README | Excellent | Good, self-disclosing |
| Auditability | Chain + Hyperliquid public; **but organizer classifies** | Chain + HF | **Excellent** | Weak |
| Unique risk | **You can lose your own money** | Repo ≠ live network | Noise > dethrone margin | Can't participate |

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

**Greevils has the best-designed incentive mechanism of the four, and a live
state that does not match it.**

The scoring document is the most rigorous I have read on Bittensor. Every
constant carries a stated anchor — *"a 15 % drawdown erases the credit for a
100 % return"* — which means the designers know what their own parameters do.
The pairwise-on-overlap tournament is the correct answer to "how do you compare
traders who started on different days". The flow-adjustment algebra genuinely
closes the deposit/withdrawal gaming vector in all four quadrants. The
longevity bonus is upside-only so a long record never buys back risk. The
two-process TEE argument — that in-process key hiding is cosmetic because
`gc.get_objects()` reaches everything — is correct and rarely stated. And the
git history shows real tuning against live behaviour, including a revert.

**But the chain tells a different story than the docs.** One UID takes 100 % of
the miner pool with no on-chain commitment, while 41 hotkeys holding valid
claims earn nothing. Zero `gva1` approvals exist, which under the published
rules makes the agent lane — ~95 % of emission — mathematically unreachable.
The published validator, run against today's chain, would not produce today's
weight vector. Something is running that is not this code, and I cannot tell
what from outside.

**The structural objection is harder than the operational one.** To earn from
the agent pool you must publish your profitable trading strategy publicly and
have it manually approved by the largest validator — currently the owner. Most
traders with a real edge will not do that, which selects for either weak
strategies or participants who value emission above alpha. That is a genuine
design tension, not an implementation bug, and it is the thing I would want the
team to answer.

**What makes it interesting anyway:** the human lane has **no eligibility gate
at all**, competes in the same unified tournament, costs ~$25 to enter plus
capital you already control, needs no GPU and no cloud, and starts the 60-day
clock immediately. That is a genuinely cheap option on a well-designed
mechanism.

### Recommended path

1. **Write to `atlas@greevils.ai` before funding anything.** Two questions: why
   does UID 37 earn 100 % with no commitment while 41 valid claims earn zero;
   and when will the first `gva1` approval exist. Both are answerable in a
   sentence, and both are disqualifying if the answers are bad.
2. **If the answers hold up, enter the human lane immediately.** 0.10 TAO,
   $25k+ in a Standard-mode Hyperliquid account, every fill through the builder
   app. No gate, no GPU, no cloud — and the 60-day clock starts on your first
   trade.
3. **Run drawdown as your primary KPI.** λ = 0.308 quadratic means a 15 %
   drawdown costs a full double. Many small green days beat few large ones on
   both the concentration and volatility terms.
4. **Keep capital above $10,000 and far above $1,000.** The profit-day floor
   halves the score of a $5k account; the $1,000 midnight snapshot is a
   permanent DQ.
5. **Build the agent in parallel and audit the harness yourself** — it is
   published precisely so you can confirm it cannot exfiltrate your key before
   you trust it with one.
6. **Decide the open-source question honestly, early.** If you will not publish
   your strategy, the agent pool is permanently closed to you and the human
   lane's dollar cap is your ceiling. That may still be worth it — but know it
   going in.
7. **Watch three signals:** the first `gva1` approval commitment appearing on
   chain; UID 37's incentive dropping below 1.0; and any claim-holding UID
   earning a non-zero weight. The third is the cleanest proof that the published
   mechanism is the one actually running.

---

## 13. Sources

**Code (all four public repos, pulled 2026-08-29)**
- `greevils-ai/greevils-docs` @ `392d9ae` — the map
- `greevils-ai/greevils-validator` @ `2e08a01` — `incentive.md`, `tournament.py`,
  `scoring.py`, `rewards.py`, `evaluation.py`, `approvals.py`, `commitments.py`,
  `config.py`, `db.py`, `pricing.py`
- `greevils-ai/greevils-cli` @ `dd4decc` — `deploy.py`, `commit.py`, `approve.py`
- `greevils-ai/greevils-public-harness` @ `db964eb` — `ARCHITECTURE.md`,
  `supervisor.py`, `signer/`, `agent/`
- Local: `/root/Bittensor/58/`

**Chain** (finney, block 8,951,884)
- `Subtensor.subnet(58)`, `metagraph(58)`, `recycle(58)`, `weights(58)`
- `get_all_commitments(58)` — 42 claims, **0 `gva1`**
- `get_commitment(58, 37)` → `''`
- `SubnetIdentitiesV3(58)`

**Endpoints probed**
- `https://api.greevils.ai` — `/docs` 200; `/`, `/health`, `/agents`,
  `/leaderboard`, `/stats` all 404 (private backend)
- https://www.greevils.ai

**Price reference**
- TAO ≈ $256 → α ≈ $2.518 at 0.009837 TAO/α
