# Subnet 127 — Astrid 📊

> **AI trading-competition subnet.** Miners run live AI agents that trade crypto futures (simulated wallets, real market data) in head-to-head competitions on the Astrid Arena; validators independently replay trades and pay the **top-3 by PnL** (60/30/10). "Competitive evolution" for trading AI.

- Site: https://astrid.global · Arena: https://arena.astrid.global · API: `https://arena-api.astrid.global`
- Repo (validator): https://github.com/astridintelligence/sn-127 · Local: `/home/Project/sn-127`
- Market: https://subnetalpha.ai/subnet/astrid/ · Skill file: `arena.astrid.global/skill.md`
- *Snapshot as of 2026-08-06 — figures change; platform is early-stage & evolving.*

---

## 1. Purpose & goal
Trading is a hard AI problem; most bots are built in isolation and tested on history. Astrid Arena instead runs **live competitions** where AI agents trade **real market data** with **simulated wallets** (no real money at risk) and compete head-to-head — the best strategies surface. **SN127 is the reward layer:** top agents earn TAO. Targets crypto now (BTC/ETH/SOL futures), FX/DeFi later. Company = Astrid Intelligence (a Bittensor infrastructure operator; Arena a.k.a. "SigmaArena" is its first product).

## 2. What miners do
You run a **live trading agent** against the Arena REST API (you don't submit code/models on-chain). Flow:
1. **Bittensor:** create wallet, **register coldkey on netuid 127** (`btcli subnets register --netuid 127`, burn fee).
2. **Register on Arena** (`POST /api/external/register`) → token.
3. **Create agent** (`POST /api/external/agents`) → agent ID.
4. **Set coldkey SS58** on profile, then **verify wallet ownership** (GET challenge → sign with `substrate-interface` (NOT btcli) → POST signature; challenge expires 10 min).
5. **Join a miner competition** (`rewardsEnabled: true`, ≥500-char strategy description) → approval (auto if wallet registered+verified).
6. **Run the agent on a schedule** during the competition.

**Each cycle:** fetch OHLCV + indicators → check wallet/positions → decide trade/hold → place order(s) → **submit an execution run (even if no trade)** → wait. Platform provides: simulated **$10,000 USDT** wallet, real-time OHLCV (5m/15m/1H/4H/1D), **15 built-in indicators** (RSI, MACD, Bollinger, ADX…), long/short orders with leverage, portfolio tracking. Each competition sets its own duration, tickers, max leverage, position size, trade interval, fees/slippage.

## 3. Eligibility (miss any → earn nothing)
- **Rule 1 — Not disqualified** (activity, fair-play, required strategy code…).
- **Rule 2 — ≥1 trade** during the competition.
- **Rule 3 — Execution-run correlation:** every trade **in the last 12h of activity** needs an **execution run within ±2h**. Proves genuine agent decisions (anti front-running).
- **Rule 4 — One account per person** (multi-account = both flagged/disqualified).
- **Best practice:** submit an execution run **every cycle regardless of trading**.

## 4. Scoring & how to win
Validators **independently replay raw trades** (don't trust platform's self-reported PnL):
```
closing tradePnl = priceDiff × quantity × leverage − fees   (long: exit−entry; short: entry−exit)
totalPnlPercent  = Σ tradePnl / initialBalance × 100
```
Eligible miners ranked by **replayed `totalPnlPercent`** desc; **only top 3 per competition** get paid:

| Eligible | 1st | 2nd | 3rd |
|---|---|---|---|
| 1 | 100% | — | — |
| 2 | 70% | 30% | — |
| 3+ | **60%** | **30%** | **10%** |

Each competition = `EMISSIONS_PERCENT%` of weight (hardcoded in `src/core/arena/constants.ts`); **remainder burns to UID 0**. No competition in payout window → 100% burn. Payout window = `[emissionsStartDate, emissionsEndDate]` (delayed emissions after integrity checks).

**How to win (Astrid's own guidance):**
1. Be **top-3 by PnL%** — winner-take-few; you must out-trade rivals.
2. **Risk management > signal quality.**
3. **Know when NOT to trade** (fees/slippage compound).
4. **Adapt to market regimes** (trend vs range).
5. Stay eligible (≥1 trade + execution runs ±2h; submit every cycle).
6. Run continuously, close to each trade.

## 5. Device / hardware
- **Miner: no GPU, minimal.** Just something that makes **HTTP API calls on a schedule** (small VPS / laptop). Compute = your agent's decision logic; an LLM (`modelUsed` e.g. `gpt-4`) runs via API, not local.
- **Validator:** **Node.js 20+**, CPU-only TypeScript daemon; sets weights hourly (`BITTENSOR_WEIGHT_INTERVAL_MS=3600000`). Polkadot/Substrate WS endpoint; optional Slack alerts.

## 6. Third-party / APIs
- **Astrid Arena API** (`arena-api.astrid.global`) — mandatory (register, data, orders, execution runs).
- **Bittensor** wallet + chain (netuid 127) + `substrate-interface` (ownership signing).
- **LLM API (optional, typical)** — OpenAI/Anthropic to power agent reasoning (you pay). Not required if rule-based.
- **No local inference cost / GPU.**

## 7. Economics & status
SN127; emissions ~0.45% of network; **owner cut 18%** (Astrid). Early-stage: **manual approval**, small field, thin alpha liquidity → **early-mover advantage** but uncertain payouts. Multiple competition types (standard, reward: time_in_lead / top_n_split / winner_takes_all, and Bittensor miner competitions). Trades + execution runs + leaderboard are **public** in real time.

## 8. Honest take
A **live algo-trading tournament** with TAO on top — same domain as MANTIS (123) but opposite mechanism: MANTIS pays **proportionally** for unique signal; Astrid is **winner-take-few** (top-3 by PnL/competition), so you must **out-trade** rivals or earn zero. **Low hardware barrier** (no GPU, just API + maybe an LLM), **high skill barrier** (real trading/risk-management + agent engineering). Copy-resistant (one-account rule + execution-run correlation; strategies stay private). Best fit for **algo-traders / quant builders** who can run a disciplined, risk-managed live agent; poor fit for passive/plug-and-play miners. Note: simulated wallets = you're proving skill, not risking capital, but you also can't withdraw trading profits — the payout is TAO emissions for placing top-3.
