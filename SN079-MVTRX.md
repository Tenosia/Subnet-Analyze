# Subnet 79 — MVTRX (τaos) — analysis

**Analysed:** 2026-08-19 · **Chain state read live from finney at block 8,875,761** · TAO $190.42, SN79 α = τ0.006737046 = **$1.2829**

| | |
| --- | --- |
| Netuid | 79 (`finney`) · **testnet: netuid 366** |
| Name | MVTRX — "Building a SOTA Exchange for dTAO and Beyond" |
| Operator | taos-im · contact `to@mvtrx.fi` |
| Owner hotkey | `5EWwdZB7qCCMaAso5Mzcks4UUcPxKYvpAj32t5Mg1v6HSxoF` (UID 0) |
| Sites | https://taos.im · https://mvtrx.fi · https://mvtrx.exchange |
| Dashboards | https://taos.simulate.trading · https://mvtrx.simulate.trading · https://testnet.simulate.trading |
| Code | https://github.com/taos-im/sn-79 ([local checkout](sn-79/)) · v0.5.5 |
| Whitepaper | https://simulate.trading/taos-im-paper |
| Registered at | block 5,173,967 — **subnet is 514 days old (the most mature of the four analysed)** |

---

## 1. Goal of the subnet

MVTRX is **decentralised market research and AI model training**, built from three components:

- **τaos** — agent-based simulation of automated trading in intelligent markets. Miners are trading agents competing inside a simulated limit order book. *Live today.*
- **GenTRX** — distributed training of a shared order-book generative model, built on τaos simulation data. *Live today, opt-in.*
- **MVTRX Exchange** — a live off-chain limit order book exchange for Bittensor alpha tokens, running the same C++ matching engine. *Coming; mechanism to be published at testnet.*

The research purpose is to produce **Level 3 / market-by-order data** — every individual event in the book — from markets populated by genuinely intelligent, risk-managed participants. That data is the product, useful for strategy development, market surveillance, and regulatory analysis. The subnet incentivises miners toward *risk-averse, budget-constrained, active* trading precisely because that is what makes the output data realistic.

The simulator is a C++ agent-based engine built on [MAXE](https://github.com/maxe-team/maxe), with background agents parameterised from established literature (Chiarella et al. 2007; Vuorenmaa & Wang 2014). Currently **40 order books, ~1,000 background agents each**; the stated aim is 1,000+ books.

> *"taos (/ˈtɑos/): To make things out of metal by heating it until it is soft and then bending and hitting it with a hammer to create the right shape."*

---

## 2. What you do as a miner

**You write and host an algorithmic trading bot. This is the most familiar shape of the four subnets analysed — a real always-on miner that answers validator requests under a latency penalty.**

### The mechanic

Validators pause the simulation, push a state update to every miner, wait for responses, submit the resulting instructions back into the simulation, and resume. Your job is to return orders and cancellations that maximise **risk-adjusted return across all 40 book realizations simultaneously**.

You implement an agent class, referenced in your miner config:

```
~/.taos/agents/           # examples installed by install_miner.sh
agents/                   # in-repo examples
agents/proxy/             # local offline simulator for testing
```

The state update carries **all L3 messages since the last update**, so the most detailed microstructure strategies are possible — you are limited only by the interval at which you can act.

### Latency is scored — directly

> *"the response time of miners is used to determine the 'delay' or 'latency' with which their instructions will be processed by the simulator. Longer response times thus imply more events that may take place before execution of their instructions, requiring realistic effects like price slippage to be accounted for."*

| Parameter | Default |
| --- | --- |
| `scoring.min_delay` | 10,000,000 ns = **10 ms** |
| `scoring.max_delay` | 1,000,000,000 ns = **1,000 ms** |
| `scoring.min_instruction_delay` | 5,000,000 ns = 5 ms (additive per subsequent instruction in one response) |
| `scoring.max_instruction_delay` | 25,000,000 ns = 25 ms |

Your wall-clock response time maps into simulated execution delay between 10 ms and 1 s. **Slow responses get worse fills.** This is a genuine infrastructure lever — the only one across all four subnets analysed.

### The loop

```
1. Develop your agent locally against agents/proxy/  (free, offline, own machine)
2. Test on TESTNET netuid 366, monitor at testnet.simulate.trading
3. btcli register on netuid 79   (burn ~τ0.18 = $34.60)
4. ./install_miner.sh  → run_miner.sh
5. Stay online. Respond fast. Round-trip profitably across all 40 books.
6. Iterate on the strategy; scores are a rolling EMA that survives simulation restarts
```

A new simulation configuration is deployed roughly **weekly**; each run starts every miner with the same initial capital. **Scores are not cleared between runs** — a rolling window carries performance across simulations. Deregistration resets that UID's balance and positions to the configured starting values.

---

## 3. Scoring logic

### 3.1 Two reward pools

| Pool | Share | Scored on |
| --- | --- | --- |
| **Trading** | ~95% | Kappa-3 + PnL from simulation trading. **All registered miners participate.** |
| **GenTRX training** | ~5% (`--scoring.gentrx.simulation_share`) | Gradient quality vs held-out order-book data. **Opt-in.** |

The training allocation **scales with participation** (`N_active / N_registered`) and unused portion **returns to the trading pool**. If nobody trains, 100% goes to trading. Training runs in a background thread concurrently with live trading — the README is explicit that there is **no trade-off**.

### 3.2 Trading pool — the core metric

```
K₃(τ) = (μ − τ) / [LPM₃(τ)]^(1/3)
```

where μ is mean return, τ the target threshold, and LPM₃ the **third lower partial moment** measuring downside risk. Kappa-3 heavily penalises downside volatility while rewarding consistent profitability.

**Critically: returns come from actual realized P&L on closed round-trip trades.** Standing limit orders that never fill contribute nothing. Per FAQ #12, this was a deliberate migration away from inventory-based Sharpe specifically to kill passive "standing still" strategies.

| Config | Default | Meaning |
| --- | --- | --- |
| `scoring.kappa.weight` | **0.79** | Kappa-3 share of the trading score |
| `scoring.pnl.weight` | **0.21** | Realized PnL share |
| `scoring.kappa.lookback` | 10,800 s sim = **3 h** | rolling assessment window |
| `scoring.kappa.min_lookback` | 5,400 s sim = 1.5 h | minimum before Kappa is computed |
| `scoring.kappa.min_realized_observations` | **3** | round-trips required before you get *any* Kappa score |
| `scoring.kappa.tau` | 0.0 | minimum acceptable return |
| `scoring.kappa.normalization_min/max` | −2.5 / +2.5 | Kappa is normalised into this range |
| `scoring.pnl.normalization.method` | `daily_return` | floor −1.0, cap +1.0 |
| neglected books ratio | **0.375** | the worst 37.5% of your books are excluded from scoring |

That last one matters: **you may neglect up to 37.5% of the 40 books** — the lowest-performing ones are dropped before scoring. You do not have to be good everywhere, but you must be good on ~25 of 40.

### 3.3 The volume cap — the thing that will bite you

```
cap = Simulation.Agents.MultiBookExchangeAgent.Balances.wealth × capital_turnover_cap
capital_turnover_cap = 10.0     over trade_volume_assessment_period = 86,400 s sim (24 h)
sampling interval = 600 s sim
```

Trade more than **10× your initial capital in QUOTE volume within a rolling 24 simulated hours** and **no further instructions are accepted on that book except cancellations** until the trailing volume drops back under the limit.

> *"If the cap is hit early in the first 24 hours, there is a high risk of deregistration as no further actions will be possible until at least 24 simulation hours have elapsed."*

And: **traded volumes are NOT reset when a new simulation begins.** The 24-hour window spans simulation boundaries. Your current usage is in the state update at `self.accounts[book_id]['traded_volume']`.

### 3.4 Currently-disabled knobs — read the config, not the prose

Several mechanisms the README and FAQ describe as active are **set to 0.0 by default in the shipped config**:

| Config | Default | Effect |
| --- | --- | --- |
| `scoring.activity.impact` | **0.0** | volume-weighting of scores is **off** |
| `scoring.activity.decay_rate` | **0.0** | inactivity decay is **off** |
| `scoring.kappa.pnl.impact` | **0.0** | |

The prose says scores "are scaled in proportion to their round-trip trading volume with a decay factor applied during inactive periods." With `impact = 0.0` those multipliers are currently inert. The **volume cap in §3.3 is still enforced** — that is a hard gate on instruction acceptance, not a scoring multiplier. Treat the activity weighting as a lever the owner can re-enable at any time, and do not build a strategy that only works while it is off.

Inventory balance multipliers *are* live: `scoring.inventory.min_balance_ratio_multiplier = 0.5`, `max = 1.2` — holding a larger ratio of BASE currency multiplies your Kappa score up to 1.2×, holding too little cuts it to 0.5×.

### 3.5 Scores → weights: Pareto amplification + soft floor

Two transformations run on the raw trading scores before weights are set.

**Soft floor** (`apply_reward_floor`, [reward.py:961](sn-79/taos/im/validator/reward.py#L961)) — enabled by default:

```
thr = percentile(positive_scores, 50)          # rewarding.floor.percentile = 50
lo  = thr × (1 − softness)                     # rewarding.floor.softness = 0.5
factor = clip((score − lo) / (thr − lo), 0, 1)
```

**Below half the median score you earn exactly zero.** Between half-median and median you ramp linearly. The stated purpose: *"so a fleet of merely-adequate UIDs stops earning and the payout concentrates on genuine performers."*

**Pareto allocation** ([reward.py:936](sn-79/taos/im/validator/reward.py#L936)) — scores are sorted and multiplied element-wise by a sorted Pareto draw, so the highest raw score receives the largest multiplier:

```
rewarding.pareto.shape = 1.42        rewarding.pareto.scale = 1.0
rewarding.seed = 898746039182        # fixed — deterministic across validators
```

The config comment documents the tuning history precisely:

> *"1.0 concentrated ~51% of reward on the top-5 UIDs, over-amplifying whichever strategy tops Kappa (currently directional-luck/farm winners in the up-market); 1.42 (the pre-0.5.4 curve) halves that to ~33% and restores honest mid-tier reward."*

**Measured live today: top-5 hold 35.0% of miner incentive.** The curve is doing exactly what the comment says.

Final score is an **EMA** across observations (`--neuron.moving_average_alpha`), so ranking moves slowly and past performance persists across simulation restarts.

### 3.6 No emission burn

FAQ #11 is explicit: *"we do not burn miner emissions and do not currently have any plans to implement this."* Confirmed on chain — 41.0% of tempo emission reaches miners, matching the standard dTAO allocation exactly.

---

## 4. Live competition landscape (2026-08-19)

### Chain state

| | |
| --- | --- |
| UIDs | 256 / 256 |
| **Validator permits** | **1** — UID 0, the owner, holding 3,793,182 α |
| UIDs with stake > 0 | 209 |
| Registration | allowed; recycle **τ0.1817 ≈ $34.60** |
| Immunity period | **7,200 blocks ≈ 24 hours** |
| Tempo | 360 blocks (1.2 h) → 20 tempos/day |
| Commit-reveal | enabled, period 1 |
| α price | τ0.006737046 = **$1.2829** — 3.2× SN76's and SN78's |
| α emission | 1.0 α/block ≈ 7,200 α/day |
| Miner pool | 147.5 α/tempo = **2,951 α/day ≈ $3,785/day** |

### The incentive distribution — the healthiest of the four

```
UIDs with nonzero miner incentive: 216 / 256   (84%)
```

| Concentration | Share of miner incentive |
| --- | --- |
| top 1 | 9.1% |
| top 3 | 23.7% |
| top 5 | **35.0%** |
| top 10 | 48.0% |
| top 20 | 61.3% |
| top 50 | 78.8% |

This is a **real gradient**, not a cliff. Compare: SN78 has exactly one earner; SN76 has at most twelve. Here 216 UIDs earn something, and the curve matches the documented Pareto target almost exactly.

### Earnings by rank

| Rank | α/tempo | α/day | USD/day | USD/month |
| --- | --- | --- | --- | --- |
| 1 | 13.373 | 267.5 | **$343** | $10,293 |
| 2 | 11.648 | 233.0 | $299 | $8,966 |
| 3 | 9.913 | 198.3 | $254 | $7,630 |
| 5 | 7.868 | 157.4 | $202 | $6,056 |
| 10 | 3.015 | 60.3 | $77 | $2,321 |
| 20 | 1.591 | 31.8 | $41 | $1,225 |
| 30 | 0.933 | 18.7 | $24 | $718 |
| 50 | 0.582 | 11.6 | $15 | $448 |
| 75 | 0.370 | 7.4 | $9.49 | $285 |
| 100 | 0.258 | 5.2 | $6.62 | $199 |
| 150 | 0.103 | 2.1 | $2.65 | $79 |
| 200 | 0.036 | 0.7 | $0.91 | $27 |

**Median earner: $5.40/day ($162/month).** Registration ($34.60) pays for itself within a month down to roughly **rank 193**.

> ⚠️ **Validator centralisation:** only **one** validator permit exists right now (UID 0, the owner). FAQ #10 discusses vTrust discrepancies *between* validators, implying more have run historically. Today the owner is effectively the sole scorer. That is a material governance risk and worth confirming in Discord before committing.

---

## 5. Miner economics

### Costs

| Item | Cost |
| --- | --- |
| Registration burn | **τ0.1817 ≈ $34.60** (real, and it moves with demand) |
| Server | 4 cores / 4 GB RAM minimum; 8 cores / 3.5 GHz recommended |
| Storage | 100 GB min, 250 GB recommended SSD, 1,000–5,000 IOPS |
| Bandwidth | continuous — you answer every state update from every validator |
| GPU | **none for trading**; optional 6–8 GB VRAM for GenTRX |
| Ongoing | a VPS, always on |

**~1 GB RAM per miner instance** for the base Bittensor + subnet tooling; beyond that it depends entirely on your strategy's complexity.

### The return profile

Unlike the other three subnets, **there is a broad earning middle**. You do not need to be #1 to make money — rank 30 is $718/month, rank 50 is $448/month, against a $34.60 entry and a cheap VPS. That changes the risk calculus fundamentally: this is the only one of the four where a competent-but-not-dominant miner has positive expected value.

The soft floor is the real hurdle: **you must clear half the median score** to earn anything at all.

---

## 6. How to become a winner

### What you are optimising

Maximise **Kappa-3 on realized round-trip P&L**, across ~25 of 40 books (you may drop the worst 37.5%), within a 3-hour rolling window, without breaching a 10× capital turnover cap per 24 simulated hours, while responding fast enough that your execution delay stays near 10 ms rather than 1 s.

### The levers, in order of value

1. **Downside asymmetry is the whole metric.** LPM₃ raises losses to the third power before the cube root. One large loss dominates many small gains. A strategy with modest but consistent round-trips will beat a higher-mean strategy with fat left-tail losses — decisively. **Cut losers hard and early; that single behaviour matters more than entry logic.**

2. **You must actually close positions.** Only completed round-trips produce observations, and `min_realized_observations = 3` means fewer than 3 round-trips in the window earns you **no Kappa score at all**. Unrealized paper gains are worth zero. This is the trap that catches market-making strategies that quote beautifully and never take profit.

3. **Latency is a genuine infrastructure edge.** 10 ms → 1,000 ms of simulated delay is a 100× range in slippage exposure. Fast, tight response loops directly improve fills. **This is the one lever where the CX23 experience transfers directly** — it is the same shape as the BEAM 15-second wave deadline: response time converts into outcome, and the fix is efficient code and a well-placed box, not cleverness.

4. **Respect the volume cap or die in the first 24 hours.** 10× initial capital per rolling 24 sim-hours, spanning simulation boundaries, and hitting it locks you out of everything but cancellations. Read `self.accounts[book_id]['traded_volume']` every tick and throttle. The FAQ explicitly warns this causes deregistration.

5. **Exploit the 37.5% neglect allowance.** You are scored on your best ~25 of 40 books. A strategy that performs well in some regimes and poorly in others is *not* automatically penalised — the worst books are dropped. Do not over-engineer for universal robustness at the cost of peak performance.

6. **Hold BASE inventory.** `min_balance_ratio_multiplier = 0.5`, `max = 1.2` — a 2.4× swing on your Kappa score purely from inventory composition. Running flat-to-zero BASE halves your score.

7. **Opt into GenTRX.** ~5% of rewards, scaled by participation, and the README states there is no trade-off with trading — it runs in a background thread. With few participants your share of that pool is large. A GPU (6–8 GB) helps; CPU-only works but "may miss round deadlines."

### The path in

**Use the testnet.** This is the decisive advantage over the other three subnets:

- `agents/proxy/` runs the simulation engine **locally, offline, free** — develop and measure before spending anything
- **netuid 366** is a full testnet with a continuously-running owner validator on the latest code, monitored at testnet.simulate.trading
- Testnet TAO is free from the Bittensor Discord faucet

You can measure your actual Kappa-3 before risking $34.60 or a UID. Do that.

> **The FAQ says it plainly:** *"Note that the example miners given in the /agents directory are not expected to perform well in the subnet — you need to develop a smart custom algorithm to compete."*

### Honest assessment

This is a **quantitative trading competition**. The skill required is algorithmic trading strategy design — market microstructure, inventory management, risk control. That is a genuine and specific expertise, and neither the ops skill from BEAM nor general software engineering substitutes for it.

But the structure is by far the friendliest of the four: a broad earning curve, a free local simulator, a real testnet, a mature 514-day-old subnet, no emission burn, and a documented mechanism whose owner visibly tunes it *toward* mid-tier fairness rather than away from it.

---

## 7. Rules you must keep

| Rule | Consequence |
| --- | --- |
| Respond to validator state updates promptly | Response time → simulated execution delay, 10 ms to 1 s |
| ≥3 realized round-trips in the 3 h window | Below that, **no Kappa score at all** |
| Stay under 10× capital turnover per 24 sim-hours | Instructions rejected on that book (cancellations still allowed) until volume decays; **high deregistration risk** if hit early |
| Clear half the median trading score | Soft floor tapers you to **zero** |
| Survive 24 h immunity (7,200 blocks) | Deregistration resets balance and positions |
| Keep the miner online | Missed responses = no instructions submitted |
| Volume counters span simulations | Not reset at a new simulation start |

**Notably absent:** there is no blacklist, no manual review, no hash-pinned code, no permitted-strategy list. The README states *"There are no strict limitations on what strategies are able to be applied."* Enforcement is entirely mechanical — the volume cap, the soft floor, and the metric itself. Of the four subnets analysed, this has by far the lightest rulebook and no discretionary operator judgment over individual miners.

The owner's stated levers are mechanism tuning, not policing: simulation parameters are republished roughly weekly, and scoring parameters are *"continuously monitored and reviewed."*

---

## 8. Device / hardware conditions

| | **Miner** | Validator |
| --- | --- | --- |
| CPU | **4 cores min / 8 recommended**, 2.5–3.5 GHz, x86_64 | **16 cores** |
| RAM | **4 GB min** (~1 GB per miner instance) | **32 GB** |
| Swap | 1 GB min / 2 GB recommended | — |
| Storage | **100 GB min / 250 GB SSD recommended**, 1,000–5,000 IOPS | same |
| GPU | **not required** (optional 6–8 GB VRAM for GenTRX) | optional 8–16 GB for GenTRX |
| OS | **Ubuntu ≥ 22.04** | Ubuntu ≥ 22.04, g++ 14 |
| Python | 3.10.9 (tested) | 3.10.9 |
| Uptime | **continuous** | continuous |
| Docker | **not provided** — native install only, on the roadmap | not provided |

Validator install compiles cmake and g++ from source and *"takes quite a long time, often 2+ hours on Ubuntu 22.04."* Miner install is much lighter.

> **Note for this operator:** this is the first subnet of the four whose miner side actually fits the kind of box you already run. **4 cores / 4 GB is close to the BEAM VPS spec** (2 cores / 3.7 GB) — under the minimum, but the same order of magnitude, unlike SN66's 8 GB Lean build or SN78's GPU requirement.
>
> **Do not co-locate it with BEAM anyway.** The 100 GB storage minimum alone exceeds the 26 GB free on 46.225.140.58, and more importantly both subnets are latency-scored: SN79 converts response time into execution slippage exactly as BEAM's 15-second wave deadline converts it into superseded tasks. Two latency-sensitive miners on two shared cores would degrade both. Rent a second small VPS — at rank-50 money ($448/month) that is trivially affordable.

---

## 9. Third-party conditions

**The lightest third-party footprint of the four subnets analysed.**

| Dependency | Detail | Risk |
| --- | --- | --- |
| **None mandatory for trading** | No API keys, no LLM judge, no hosting platform, no external model registry | — |
| S3 bucket | **GenTRX only** — miners upload gradients to a personal bucket, discovered via chain commitments | Opt-in; skip GenTRX and you need nothing |
| Grafana dashboards | taos.simulate.trading, testnet.simulate.trading | Read-only monitoring |
| Bittensor | `btcli` wallet, register | — |

Contrast: SN78 needs Chutes + Hugging Face + `gpt-audio-1.5` + an owner API + Hippius, and validating there requires the team to grant you three separate credentials. SN76 requires an OpenRouter/Chutes key and uploading it to the operator. **SN79's trading path requires you to trust nobody but the chain and the owner's validator.**

The real dependency here is **governance, not infrastructure**: with one validator permit live, the owner is effectively the sole scorer, and simulation configurations are republished weekly at the owner's discretion.

---

## 10. Risks

1. **Single validator.** Only one permit is live (UID 0, the owner, 3.79M α staked). Whatever the historical picture, today one party computes every score. Confirm in Discord before committing.
2. **Weekly config republishing.** Simulation parameters change roughly weekly at the owner's discretion. A strategy tuned to one background-model parameterisation can degrade when the next lands.
3. **Currently-inert scoring knobs.** `activity.impact` and `activity.decay_rate` are 0.0 today but are documented as active mechanisms. If re-enabled, volume weighting and inactivity decay start biting strategies built while they were off.
4. **The volume cap is a deregistration trap.** Hit it early in your first 24 hours and you cannot act at all — during exactly the immunity window you needed to establish a score.
5. **Soft floor at half-median.** Merely adequate earns literally zero. The middle of the distribution is real, but the bottom half of it is not.
6. **Real registration cost.** $34.60 and rising with demand — 350× SN78's burn. Not free experimentation.
7. **Scoring divergence is by design.** FAQ #10: each validator's simulation differs stochastically, and the owner defends this as *"a key element guaranteeing the robustness of the top scoring miners."* Your score has irreducible variance you cannot engineer away.
8. **Exchange component unannounced.** MVTRX Exchange *"will extend both with additional reward dimensions; mechanism details will be published when Exchange enters testnet."* A significant future re-weighting is explicitly signalled.
9. **Skill gate is real.** Algorithmic trading strategy design. The example agents are stated not to be competitive.
10. **No Docker.** Native install only, on a specific Ubuntu/Python/g++ stack.

---

## 11. Verdict

| | SN66 Conjectures | SN76 Phylax | SN78 Vocence | **SN79 MVTRX** |
| --- | --- | --- | --- | --- |
| Work | write Lean proofs | write a detector | fine-tune a TTS model | **write a trading bot** |
| Skill | research maths | security eng. | ML / speech | **quant trading** |
| Miner emissions | **none** | yes | yes | yes |
| **Earning UIDs** | 1 per bounty | ≤12 | **1** | **216 of 256** |
| Entry cost | $95/attempt | ~$21 | $0.10 | **$34.60** |
| Running cost | none | inference spend | GPU + Chutes | **a small VPS** |
| GPU | no | no | **yes** | no |
| Always-on server | no | no | chute must stay hot | **yes** |
| **Latency scored** | no | no | no | **yes** |
| Top earner | $5,157 once | $224/day | $1,175/day | **$343/day** |
| Median earner | $0 | $0 | $0 | **$5.40/day** |
| Testnet | no | local corpus | no | **yes (netuid 366)** |
| Third-party deps | none | 2 | **5** | **0** |
| Rulebook | manual review | blacklist | permanent blacklist | **mechanical only** |

**SN79 has the lowest top-end payout and by far the best structure.** It is the only one of the four with a genuine earning middle, a free local simulator, a real testnet, no discretionary blacklist, no third-party dependencies on the trading path, and a documented mechanism whose owner tunes *toward* mid-tier fairness.

It is also the only one where any part of the BEAM/CX23 experience transfers: **latency is scored**, and the shape is identical — response time converts directly into worse outcomes, and the remedy is efficient code and a well-placed machine. That is a real, if partial, edge.

The gate is genuine, though: this is quantitative trading, and no amount of infrastructure skill compensates for a strategy that loses money.

**Recommended path:**

1. **Start entirely free.** Clone the repo, run `agents/proxy/` locally, and read `agents/README.md`. Nothing is spent and nothing is registered.
2. **Build against the metric, not against intuition.** Optimise Kappa-3 on *closed round-trips*, not paper P&L. Verify you produce ≥3 round-trips per 3-hour window before anything else.
3. **Instrument the volume cap from day one.** Track `self.accounts[book_id]['traded_volume']` and throttle well under 10× capital. This is the single most common way to die here.
4. **Go to testnet 366.** Free TAO from Discord, real validator, real dashboard. Measure your actual score against live competitors.
5. **Only register on mainnet once testnet shows you clearing the median comfortably** — the soft floor means half-median earns nothing, and you have a 24-hour immunity window to establish yourself.
6. **Rent a separate small VPS.** 4+ cores, 8 GB, 100 GB SSD, low latency to validators. Do not put it on the BEAM box.
7. **Opt into GenTRX once trading is stable.** ~5% of rewards, no trading trade-off, and thin participation means a large share.

**Ranking across all four analysed:** for this operator, SN79 is now the best fit — cheap entry, forgiving distribution, free practice environment, no GPU, no third-party lock-in, and a latency dimension where existing experience genuinely helps. SN76 remains second (no uptime burden, twelve seats). SN78 is highest-paying but single-seat and GPU-gated. SN66 pays miners nothing at all.

---

*Sources: local checkout of `taos-im/sn-79` v0.5.5 (`README.md`, `FAQ.md`, `min_compute.yml`, `taos/im/config/__init__.py`, `taos/im/validator/reward.py`, `taos/im/utils/kappa.py`); live finney chain state for netuid 79 at block 8,875,761 (subnet info, hyperparameters, metagraph incentive/emission/stake/permits); taos.im.*
