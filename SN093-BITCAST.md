# SN93 — Bitcast (Decentralized Creator Economy / "Proof of Attention")

| | |
|---|---|
| **netuid** | 93 (`Bitcast`, symbol `ᚃ`) |
| **Chain description** | A decentralized content marketing protocol — brands pay for verifiable attention |
| **Owner hotkey** | `5DAoDtMxVqtMu2Nd5E7QhPEGXDMgrySvE1b3rRT5ARDhfNNK` — **holds UID 0, which is also `BURN_UID`** |
| **Owner coldkey** | `5EbY1SebUuz189w1G96JN4mmHnShAECA6JefCRYhSLqyYg2c` (identical to UID 0's coldkey) |
| **Code** | https://github.com/bitcast-network/bitcast — public, actively developed (commits 2026-09-06) |
| **Local checkout** | `/root/Bittensor/93/bitcast` @ `1a32108` |
| **Sites** | https://bitcast.network · [/revenue](https://bitcast.network/revenue) · [/rewards](https://bitcast.network/rewards) |
| **Registered at block** | **5,370,681** — one of the older subnets in this folder |
| **Live state (2026-09-07, block 9,012,008)** | tempo 360, commit-reveal **on** |
| **Price** | 0.020204 TAO/ᚃ (**≈ $5.17**) · **tao_in τ24,234** · alpha_in 1,199,475 · alpha_out 3,817,035 |
| **Pool depth** | **By far the deepest in this folder** — τ24,234 vs τ1,000–3,000 typical |
| **UIDs** | 256 registered · **3 with incentive** · 14 permits · 9 with dividends |
| **Registration cost** | **0.005 TAO** (~$1.28) |
| **Immunity** | 50,400 blocks (**7 days**) — unusually generous |

> **The headline.** This is one of the very few subnets in this folder with
> **verifiable external revenue**: $422.3K earned, $261.8K of it (62 %) recycled
> into α buybacks. It is also a subnet where **the owner's own hotkey is the burn
> UID and currently absorbs ~64 % of the weight vector**, and where the chain's
> emission field does not match the weights validators are setting. Both facts
> are below, with the arithmetic.

---

## 1 · Goal — in plain terms

Brands want attention. Creators have audiences. The hard part is **proving** the
attention was real and pricing it honestly.

Bitcast is a marketplace for that:

1. **Brands post briefs** — "make a video about X", with a format, a start/end
   date, and a spend **cap**.
2. **Creators publish** YouTube videos (and X posts) that satisfy a brief.
3. **Validators verify** by pulling the creator's own **YouTube Analytics API**
   data through an OAuth token — actual watch-minutes and actual YouTube
   Premium revenue, not scraped view counts.
4. **Scores are computed in USD**, then converted into on-chain weights against
   the day's emission budget priced in USD.

The tagline on the site is *"proof of attention"*, and the mechanism earns it:
the **scored** quantity is **`estimatedRedPartnerRevenue`** — the actual YouTube
Premium partner revenue a video earned — read from Google's own analytics endpoint
for a channel that must be in the **YouTube Partner Program**. `estimatedMinutesWatched`
is used only for the channel-level gate, never for the score: the code states plainly
that *"watch time is never a substitute"*. There is no self-reporting.

**What makes the economics unusual:** miner emission is bounded by *measured USD
value delivered*. If creators produce less value than the daily emission budget
is worth, the remainder is not distributed — it goes to the burn UID. The
network only pays for attention it can prove.

### Live network scale (from the operator's dashboard, 2026-09-05)

| | |
|---|---|
| Creators | **1,100** — 78 YouTube · 1,033 X |
| Content rewarded | **7,234** pieces |
| Rewards paid | **$515.4K** lifetime (142.0K α) — $376.9K YouTube, $138.6K X |
| Audience | 10.96M subscribers + followers |
| Views | 4.80M |
| **Revenue** | **$422.3K** across all chains |
| **Buybacks** | **$261.8K** — 83.5K α bought back |
| **Buyback ratio** | **62.0 %** of revenue recycled into the subnet |
| Engagement | 1.87 % |

---

## 2 · What you do as a miner

### The critical distinction: a miner is an **operator**, not a creator

This trips people up, and it explains why 1,100 creators map onto so few UIDs.

From the README: *"Miners serve YouTube OAuth access tokens for the channels
they operate."* From the dashboard: *"Operators earn emissions for coordinating
creators."* And from the config:

```python
max_accounts_per_synapse: int = 1000
```

**One miner UID can front up to 1,000 YouTube accounts.** You recruit creators,
hold their OAuth refresh tokens, and expose them to validators. The emission
lands on your UID; how you split it with the creators is your business, off
protocol.

That is the actual job: **creator-network operations and business development**,
not ML and not infrastructure.

### The entire wire protocol is one message

```python
# bitcast/protocol.py — AccessTokenSynapse, the single wire message
```

Your axon answers one question: *"what access tokens do you have?"* You never
serve inference, never run a model, never handle a task.

```bash
python -m neurons.miner --netuid 93 --subtensor.network finney \
    --wallet.name miner --wallet.hotkey default
```

Credentials go in `~/.bitcast/secrets/`, one JSON per YouTube account with
`client_id`, `client_secret`, `refresh_token` — or set `TOKEN_SOURCE=api`.

---

## 3 · Scoring logic

### 3.1 Channel gates — every one must pass

```python
checks["acceptance"]      = channel_analytics["ypp"]          # YouTube Partner Program
checks["channel_age"]     = age_days >= 21
checks["min_subs"]        = subCount >= 100
checks["max_subs"]        = subCount <= 500_000
checks["retention"]       = averageViewPercentage >= 10
checks["minutes_watched"] = sum(minutes) >= 1000              # over a 90-day lookback
```

The code is explicit that YPP is now mandatory with no alternative:

> *"Acceptance requires affirmative YouTube Partner Program membership. There is
> no alternative route: alpha stake no longer substitutes for YPP."*

Note the **500,000 subscriber ceiling**. Large channels are excluded by design —
this targets the mid-tail.

### 3.2 Video gates

| Gate | Requirement |
|---|---|
| `public_video` | privacy status must be `public` |
| `publish_date` | published no earlier than brief start − **3 days** |
| `age_limit` | published within the last **17 days** (14 scoring + 3 reward delay) |
| `auto_captions_only` | **manual captions disqualify the video** |

That last one is an anti-gaming rule worth noticing: uploaded caption tracks are
rejected, so the transcript the LLM reads is the one YouTube generated.

### 3.3 The score is driven by real revenue, via a dampened curve

**What enters the curve is money, not views.** A video scores only if its
windowed YouTube Premium revenue is positive:

```python
if not is_ypp_account:   return 0.0, "non_ypp_ineligible"
if total_revenue <= 0.0: return 0.0, "ypp_zero_revenue"
```

A net-negative total (chargebacks, revenue adjustments) is floored rather than
allowed onto the reward curve.

```python
def calculate_curve_value(value):
    sqrt_value = math.sqrt(value)
    return sqrt_value / (1 + 0.1 * sqrt_value)      # YT_CURVE_DAMPENING_FACTOR = 0.1
```

Diminishing returns: doubling watch-time does **not** double your score. A video
is scored on **growth along that curve** between two 7-day rolling windows, with
a lifetime deduction applied as a floor in curve space:

```python
score = max(curve(day2) - threshold, 0) - max(curve(day1) - threshold, 0)
        where threshold = lifetime_deduction / scaling_factor
```

### 3.4 Format determines the multiplier

| Brief format | USD scaling factor | Lifetime deduction |
|---|---|---|
| `dedicated` (whole video about the brand) | **×1,800** | $100.00 |
| `ad-read` / `integration` | ×400 | $25.00 |
| `productPlacement` | ×200 | $6.25 |

**A dedicated video is worth 4.5× an ad-read and 9× a product placement**, but
carries a $100 lifetime deduction it must clear before earning anything. Product
placement clears its $6.25 floor almost immediately but tops out low.

### 3.4b Two further per-brief knobs

```python
usd_target = adjusted_curve_difference * scaling_factor * boost_factor
```

- **`boost`** — a per-brief multiplier, validated to `0.1 … 10.0`. A brand can
  make one brief up to 10x more valuable than another.
- **`max_count`** — a per-brief cap on how many videos earn, enforced **FIFO**:
  videos sort by publish date and everything past the cap is zeroed
  (`limitation_status = "limited_fifo"`). **Publishing early to a capped brief
  matters; latecomers earn nothing.**

### 3.5 Anti-exploitation: the median threshold

Period 2 is proportionally scaled down to the channel's **historical median**
measured over a `T−60 … T−30` window:

```python
yt_score_cap_start_days: int = 60
yt_score_cap_end_days: int = 30
```

You cannot buy a traffic spike and cash it. A video's scoreable performance is
capped at what the channel normally does, measured a month before the brief.

### 3.6 USD → weights, and where the remainder goes

```python
daily_alpha = 7200 * alpha_out_emission
miner_budget_alpha = daily_alpha * 0.41 * mechanism_split
daily_budget_usd = miner_budget_alpha * alpha_price_usd     # CoinGecko
```

Each miner's weight = its USD score ÷ the daily USD budget. Then:

```python
def sum_to_final_rewards(weights_matrix, uids):
    """Sum each miner's weights across briefs; the burn UID absorbs the remainder to 1.0."""
    rewards[burn_idx] = max(1.0 - other_sum, 0.0)
```

Per-brief caps apply first, then the total is capped at 1.0. **Anything not
earned by measured content value flows to `BURN_UID = 0`.**

> ⚠️ **`BURN_UID = 0` is the owner's own hotkey and coldkey.** I verified both:
> `metagraph.hotkeys[0] == subnet.owner_hotkey` and
> `metagraph.coldkeys[0] == subnet.owner_coldkey`. So the "burn" is not
> destruction — it is a transfer to the subnet owner, and it is currently the
> largest single line in the weight vector.

A `SUBNET_TREASURY_UID = 106` exists to receive a slice from the burn UID, but
`subnet_treasury_percentage = 0.0` — **it is switched off**.

### 3.7 Cadence

| | |
|---|---|
| Validator step | 60 s |
| Full reward cycle | every **240 steps ≈ 4 hours** |
| Scoring window | 14 days a video remains scoreable |
| Reward delay | 3 days (analytics lag realtime) |
| Rolling window | 7 days per average |
| Lookback | 90 days of channel history |
| Max videos/channel | 75 |

---

## 4 · Live competition landscape

### 4.1 Validators weight only three UIDs

Thirteen validators are setting weights, and they agree closely:

| Setter | Stake | Weight vector |
|---|---|---|
| UID 0 (owner) | 2,327,145 | uid0 **63.86 %** · uid152 21.50 % · uid153 14.64 % |
| UID 118 | 858,491 | uid0 **65.08 %** · uid152 20.83 % · uid153 14.09 % |
| UID 27 | 252,551 | uid0 **63.33 %** · uid152 21.40 % · uid153 15.30 % |
| UID 60 | 33,117 | uid0 73.40 % · uid152 21.60 % · uid153 5.00 % |
| UID 29 | 37,718 | uid0 **100 %** |

**Only two non-owner UIDs (152, 153) receive any weight at all.** Those are the
operator accounts fronting the 1,100 creators.

That ~64 % on UID 0 is the mechanism working as written: creators earned roughly
36 % of the day's USD emission budget, and the burn UID absorbed the rest.

### 4.2 ⚠️ The emission field does not match the weights

This is the most significant unexplained thing I found, and I checked it three ways.

| UID | Incentive | Dividends | **Actual emission (α/tempo)** | Implied by weights |
|---|---|---|---|---|
| **0** (owner / burn) | 0.6531 | 0.6579 | **88.087** | 175.1 expected |
| **152** | 0.2072 | 0 | **0.076** | 30.6 expected |
| **153** | 0.1398 | 0 | **0.052** | 20.6 expected |
| **157** | **0.0000** | **0.0000** | **126.933** ← | **0 expected** |
| 158 | 0.0000 | 0.0000 | 6.280 | 0 expected |

Decomposing the pool (block 9,012,008):

```
sum(E) all UIDs                  = 267.164 α/tempo
  E where dividends > 0 (vals)   = 133.823      ← the validator half, correct
  E where incentive > 0, div = 0 = 0.128        ← the miner half, essentially ZERO
  E where neither                = 133.213      ← lands on UID 157 + 158
```

Validator dividends reconcile perfectly (`E = D × 147.6 × 0.905`, ratio 0.9055–0.9071
across every validator — the 0.905 is the root-stake share). **The miner half does
not reconcile at all.** UID 152 and 153 receive 0.25 % of what their weights imply,
while **UID 157 — zero stake, zero incentive, zero dividends, `active=False`, and in
no validator's weight vector — receives 126.9 α/tempo ≈ 2,539 α/day ≈ $13,130/day.**

Confirmed at the neuron level, not just the metagraph:

```
UID 157: emission=126.933108076  incentive=0.0  dividends=0.0
         active=False  stake=τ0.000000000  axon 34.202.196.66:8095
```

**I could not explain this from public data.** UID 157's `last_update` is 195,361
blocks (~27 days) old, so one reading is that the emission field reflects a stale
weight regime the chain has not re-derived. Another is a mechanism outside standard
Yuma. I am recording it as an open anomaly rather than guessing — but the practical
consequence is real: **the UIDs validators are actually rewarding are receiving
almost nothing, and an unweighted UID is receiving the bulk of the miner pool.**

### 4.3 Dividend concentration

| UID | Dividends | Stake |
|---|---|---|
| **0** (owner) | **65.79 %** | 2,327,145 |
| 118 | 24.03 % | 858,491 |
| 27 | 7.11 % | 252,551 |
| 29, 60, … | < 1 % each | |

The owner holds ~66 % of validator dividends on top of ~64 % of the miner weight.

---

## 5 · Economics

Subnet emits **1.000 α/block = 7,200 α/day**; 18 % owner cut, 41 % miners, 41 %
validator dividends → **miner pool = 2,952 α/day**.

At α = 0.020204 TAO and TAO ≈ $256 → **α ≈ $5.17**:

| | α/day | USD/day |
|---|---|---|
| Full miner pool (face value) | 2,952 | **$15,268** |
| Weight to UID 0 (burn → owner), ~64 % | ~1,890 | ~$9,772 |
| Weight to UID 152, 21.5 % | ~635 | ~$3,283 |
| Weight to UID 153, 14.6 % | ~431 | ~$2,229 |
| **Owner total** (18 % cut + burn weight + 65.8 % dividends) | **~5,166** | **≈ $26,720/day — 71.8 % of all emission** |

> Those are the figures the **weight vector** implies. Per §4.2 the chain's
> emission field currently shows UID 152 and 153 receiving ~$8 and ~$5 a day
> instead. Treat the weight-derived numbers as what the mechanism intends and
> the emission field as what is presently observable — they disagree.

### The revenue side is real, and that is rare

$422.3K of external revenue with **62 % recycled into α buybacks (83.5K α)** and a
public 1,204-row transaction audit is the strongest external-demand evidence of
any subnet in this folder. The α price ($5.17) and pool depth (τ24,234) are
consistent with that: this is not a subsidy-only token.

### Costs to mine

| Item | Cost |
|---|---|
| Registration | **0.005 TAO ≈ $1.28** — the cheapest in the folder |
| GPU | **None** |
| Server | A small VPS to run the axon — that is genuinely all |
| **The real cost** | **Creator acquisition.** You need YPP channels with 100–500k subs willing to hand you OAuth access and make branded content |
| Immunity | 50,400 blocks (7 days) to establish yourself |

---

## 6 · How to become a winner

**This is a business-development subnet wearing a Bittensor interface.** The
software is trivial; the moat is creator relationships.

### Priority 1 — Resolve the emission anomaly before investing

Ask the operator directly: **why do UIDs 152 and 153 hold 21.5 % and 14.6 % of
every validator's weight vector but receive 0.25 % of the implied emission, while
unweighted UID 157 receives 126.9 α/tempo?** Until that is answered you cannot
model what a weight share is actually worth. This is the single highest-value
question and it is answerable in a sentence.

### Priority 2 — Understand you are recruiting, not building

With `max_accounts_per_synapse = 1000`, your score is the **sum over every channel
you onboard**. Two operators currently front 1,100 creators between them. Your
competitive variable is how many qualifying channels you can sign, not code.

Qualifying means, per channel: **YPP member**, ≥21 days old, **100–500,000 subs**,
≥10 % average view percentage, ≥1,000 watch-minutes over 90 days. The sub ceiling
matters — mega-channels are ineligible, so the target is the mid-tail creator who
is monetised but not huge.

### Priority 3 — Push creators toward `dedicated` briefs

The format multiplier is the largest single lever in the scoring code:

| Format | Multiplier | Deduction | Break-even |
|---|---|---|---|
| `dedicated` | **×1,800** | $100 | needs real volume, then pays 4.5× an ad-read |
| `ad-read` / `integration` | ×400 | $25 | middle ground |
| `productPlacement` | ×200 | $6.25 | earns soonest, caps lowest |

For a creator with genuine watch-time, dedicated is worth roughly **9× a product
placement** on the same audience. For a small channel that cannot clear $100 of
curve value, product placement is the only format that pays at all.

### Priority 4 — Optimise for retention and consistency, not spikes

Two rules in the code make burst tactics worthless:

- **The dampened curve** `sqrt(v)/(1+0.1·sqrt(v))` saturates. At high volume,
  extra watch-time adds very little score.
- **The median threshold** caps period 2 at the channel's own `T−60 … T−30`
  median. A bought spike is scaled straight back down.

What *does* compound is raising the channel's baseline median over time — which
is the same thing YouTube itself rewards.

### Priority 5 — Watch the brief caps and pick uncrowded briefs

```python
brief_cap = brief.get("cap", 1.0)
if brief_sum > brief_cap:
    result[:, brief_idx] *= brief_cap / brief_sum
```

Each brief has its own spend cap, and everyone chasing it is diluted pro-rata. A
less popular brief with an unfilled cap pays more per unit of delivered
attention than a crowded one. Fetch the brief list and look at where the field
is *not*.

### Priority 6 — Respect the mechanical disqualifiers

- Manual caption tracks **disqualify a video**. Leave auto-captions alone.
- The video must be **public** and published no more than 3 days before the
  brief starts.
- A video stops scoring **17 days** after publication. This is a treadmill, not
  an annuity — the income is entirely from fresh content.

### Priority 7 — Take the custody question seriously

You will hold **OAuth refresh tokens for other people's YouTube channels**.
That is a real custodial responsibility with real legal and reputational
exposure, and it is the reason creators will hesitate to sign with an unknown
operator. Being credible here *is* the business.

### The path

1. Ask the operator the §4.2 question. Wait for the answer.
2. Register (0.005 TAO ≈ $1.28) and stand up the axon on any small VPS.
3. Recruit YPP channels in the 100k–500k sub band with ≥10 % retention.
4. Fetch active briefs; steer creators to `dedicated` where volume supports it
   and to uncrowded briefs where the cap is unfilled.
5. Publish continuously — the 17-day window means output must be sustained.
6. Track your USD score against the daily budget; the gap between the two is
   what flows to the owner's UID.

---

## 7 · Rules you must keep

| Rule | Consequence if broken |
|---|---|
| Channel is a **YPP member** | Channel rejected — no alternative route, stake does not substitute |
| Channel ≥ 21 days old | Rejected |
| Channel between **100 and 500,000 subs** | Rejected at either end |
| Average view percentage ≥ 10 % | Rejected |
| ≥ 1,000 watch-minutes over the 90-day lookback | Rejected |
| Video is **public** | Not scored |
| Published ≥ (brief start − 3 days) | Not scored |
| Published within the last **17 days** | Not scored |
| **No manual caption track** | **Disqualified** — auto-captions only |
| ≤ 75 videos per channel evaluated | Excess ignored |
| Content must match the brief (LLM-judged) | No score for that brief |
| Per-brief `cap` | Diluted pro-rata with everyone else on that brief |

---

## 8 · Device conditions

### Miner — the lightest in this folder

| | |
|---|---|
| GPU | **None** |
| CPU / RAM | Whatever runs a Python axon — a $5 VPS is ample |
| Public IP + port | **Required** (axon must be reachable) |
| Uptime | Continuous — validators query on a ~4 h cycle |
| Secrets | One JSON per YouTube account in `~/.bitcast/secrets/` (`client_id`, `client_secret`, `refresh_token`), or `TOKEN_SOURCE=api` |
| Python | 3.12 |

### Validator — API keys are the real requirement

| | |
|---|---|
| GPU | **None** |
| Keys needed | **LLM provider** (`CHUTES_API_KEY` or `OPENROUTER_API_KEY`), `RAPID_API_KEY` (transcripts), `BITCAST_API_KEY` |
| YouTube quota | Analytics rate-limited to **480 queries/min** project-wide; 4 concurrent per OAuth user, 6 videos in parallel per channel |
| Cadence | 60 s steps, full reward cycle every ~4 h |
| Telemetry | Grafana Loki, on by default, explicitly best-effort — *"a telemetry failure cannot affect validation, EMA state"* |

> **Against your BEAM box (2 cores / 3.7 GB, Hetzner CX22, 46.225.140.58):**
> this is one of the very few subnets in the folder where that machine is
> **genuinely sufficient for the miner role** — the axon just serves OAuth
> tokens. It could also run a validator, since no GPU is needed; the constraint
> there is API keys and quota, not hardware. **What the box cannot supply is the
> creator network, which is the entire competitive asset.**

---

## 9 · Third-party conditions

| Dependency | Role | Failure mode |
|---|---|---|
| **YouTube Data + Analytics API** | The entire ground truth | Total dependency. Quota exhaustion or an OAuth revocation zeroes a channel |
| **Google OAuth** | Miners hold creators' refresh tokens | A revoked token silently removes that channel from scoring |
| **YouTube Partner Program** | Hard acceptance gate | Non-YPP channels cannot participate at all — Google decides your eligibility |
| **Bitcast briefs server** (`/api/v2/validator/briefs`) | Operator-run; supplies every brief | **Centralised.** No briefs → nothing to score. Mitigated by in-process + on-disk caching so a validator survives an outage |
| **Chutes or OpenRouter** | LLM decides whether content matches a brief | **A model is a judge here** — unusual for this folder, and it is on the scoring path |
| **RapidAPI** | Video transcripts (≤250k chars, 10 retries) | No transcript → the LLM cannot match the brief |
| **CoinGecko** | α price for USD→weight conversion | A bad price mis-sizes the whole budget |
| **Grafana Loki** | Score-audit telemetry, on by default | Explicitly cannot affect weights |
| **finney** | Registration, weights (commit-reveal on) | — |
| **X / Twitter** | 1,033 of the 1,100 creators | **Not in this repo** — the X pipeline is elsewhere or operator-run |

---

## 10 · Risks

1. **`BURN_UID = 0` is the owner's own hotkey and coldkey**, and it currently
   absorbs **~64 %** of every validator's weight vector. The README calls this
   "burn"; on chain it is a transfer to the subnet owner. Owner capture totals
   **~71.8 %** of emission.

2. **The emission field contradicts the weight vector** (§4.2). The two UIDs
   validators actually reward receive ~0.25 % of what their weights imply, while
   an unweighted, zero-stake, inactive UID 157 receives ~2,539 α/day. Unexplained
   from public data, and it makes the value of a weight share unknowable today.

3. **A miner custodies other people's YouTube credentials.** You hold OAuth
   refresh tokens for up to 1,000 channels you do not own. That is a genuine
   legal, security and reputational exposure with no protocol-level protection.

4. **Only two non-owner UIDs earn.** 1,100 creators aggregate behind two
   operators. The operator layer is the bottleneck, and it is near-monopolised.

5. **An LLM sits on the scoring path.** Brief-matching is judged by a model via
   Chutes or OpenRouter. Every other quality gate in this subnet is deterministic;
   this one is not, and provider drift changes outcomes.

6. **The briefs server is centralised and operator-run.** No public brief feed
   means an outsider cannot independently verify what was commissioned, at what
   cap, or whether the field was told about it simultaneously.

7. **Google is a single point of failure and a gatekeeper.** YPP membership,
   Analytics access and API quota are all Google's to grant or withdraw.

8. **Income is a treadmill.** A video scores for 17 days and then stops. There is
   no annuity — sustained publishing is mandatory.

9. **The 500,000-subscriber ceiling** excludes exactly the creators with the most
   attention to sell, capping how large a legitimate operator can grow.

10. **38 % of revenue is not recycled.** The 62 % buyback ratio is genuinely good
    and publicly audited, but the remainder's destination is not documented here.

11. **The X side is invisible in this repo.** 1,033 of 1,100 creators are on X,
    and this codebase is explicitly *"the canonical **YouTube** subnet repo"*.
    The mechanism paying the majority of creators is not in the public code I read.

---

## 11 · Documentation notes

Unusually clean — the code is the spec and the README does not overclaim.

| Observation | Detail |
|---|---|
| `BURN_UID = 0` described as burn | It is the owner's hotkey/coldkey. Disclosed in code (`burn_uid: int = 0`) but the word "burn" reads as destruction |
| `SUBNET_TREASURY_UID = 106` | Wired but **disabled** — `subnet_treasury_percentage = 0.0` |
| README scope | Says *"canonical YouTube subnet repo"*; the dashboard shows X carrying 94 % of creators. The X pipeline is out of scope for this repo, not hidden |
| `FALLBACK_MECH_EMISSION_RATIO = 0.85` | Used when the mechanism split cannot be read — a silent 15 % budget swing |
| Consensus constants | Cleanly isolated in a frozen `ConsensusParams` model with an explicit warning that changing any value diverges weights. Good practice |

---

## 12 · Verdict

**Bitcast is the only subnet in this folder whose product is bought by people
outside Bittensor, at a scale you can audit.** $422.3K of revenue, $261.8K of α
buybacks, a 1,204-row public transaction ledger, 1,100 creators and 7,234 pieces
of rewarded content. The α price ($5.17), the pool depth (τ24,234) and the
buyback ratio (62 %) all corroborate each other. Set against SN47 (owner takes
100 %), SN90 (one related-party miner) or SN78 (weights not yet active), that is
a different category of thing.

The mechanism is also well-built. Scoring reads Google's own analytics rather
than anything self-reported; YPP membership is a hard gate the operator does not
control; the dampened square-root curve kills volume farming; the `T−60…T−30`
median threshold kills bought spikes; manual captions are disqualifying so the
LLM reads a transcript nobody authored. And the payout is **bounded by measured
USD value delivered** — the network structurally cannot pay for attention it
failed to verify. That last property is rare and genuinely good design.

**Two things weigh heavily against it.** First, the honest consequence of that
bounded payout is that the shortfall goes somewhere, and here it goes to the
owner's own UID — ~64 % of the weight vector today, ~71.8 % of emission all in.
Second, and more concerning, **the chain's emission field does not match the
weights validators are setting**: the two UIDs actually being rewarded receive a
quarter of a percent of what their weight implies, while an unweighted UID
collects the bulk of the miner pool. I could not explain that, and no one should
commit capital here until the operator does.

**And the opportunity, if it resolves, is unusual.** Entry is **$1.28**, no GPU,
a $5 VPS, and a seven-day immunity window. The competitive asset is not compute
or model quality — it is a roster of monetised mid-tail creators willing to work
to brand briefs. If you have or can build that, almost nothing else in this
folder converts a non-technical asset into emission this directly.

### Recommended path

1. **Ask the operator the §4.2 question first.** Everything else is downstream of it.
2. Register anyway — $1.28 and a 7-day immunity window cost nothing to hold.
3. Stand up the axon on the Hetzner box; the software side is genuinely done in
   an afternoon.
4. **Spend your effort on creator acquisition**, in the 100k–500k sub band, YPP
   members with ≥10 % retention. That is the whole game.
5. Steer creators to `dedicated` briefs where their volume clears the $100 floor,
   and to briefs whose caps are unfilled.
6. **Watch three signals:** whether UID 152/153 emission starts matching their
   weights; whether a third operator UID appears (the layer is near-monopolised);
   and whether the buyback ratio holds above 60 % as emission grows.

---

## 13 · Sources

**Code**
- https://github.com/bitcast-network/bitcast @ `1a32108` (2026-09-06)
- Local: `/root/Bittensor/93/bitcast`
- `bitcast/config.py` (frozen `ConsensusParams`), `bitcast/validator/youtube/scoring.py`,
  `bitcast/validator/reward/scaler.py`, `bitcast/validator/reward/pricing.py`,
  `bitcast/validator/reward/orchestrator.py`, `bitcast/utils/briefs.py`,
  `bitcast/miner/`, `bitcast/protocol.py`, `README.md`

**Live operator dashboard** (fetched 2026-09-07, data stamped 2026-09-05)
- https://bitcast.network · [/revenue](https://bitcast.network/revenue) · [/rewards](https://bitcast.network/rewards)

**Chain** (finney, block 9,012,008)
- `Subtensor.subnet(93)`, `metagraph(93)`, `weights(93)`, `recycle(93)`,
  `get_subnet_hyperparameters(93)`, `neuron_for_uid(157|152|0, 93)`

**Reference**
- https://taostats.io/subnets/93/metagraph

**Price reference**
- TAO ≈ $256 → α ≈ $5.17 at 0.020204 TAO/α
