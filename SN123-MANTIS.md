# Subnet 123 — MANTIS 📈

> **"The Ultimate Signal Machine" — a decentralized quant hedge fund.** Miners submit timelock-encrypted price-prediction embeddings across ~11 challenges; validators pay TAO proportional to the *unique predictive information* each miner adds.

- Repo: https://github.com/Barbariandev/MANTIS · Backtester: https://github.com/BarbarianDev/mantis_model_iteration_tool
- Market: https://subnetalpha.ai/subnet/mantis/ · Lead: **Barbarian** (@Barbarian7676)
- *Snapshot as of 2026-07-31 — figures change.*

---

## 1. Purpose & goal
Decentralized financial forecasting — "the first decentralized, cooperative, incentivized prediction of BTCUSD." Miners contribute signals; the network aggregates them into institutional-grade trading signals (future: algo fund, subscription service, prediction markets). Alpha token holders vote on which time-series to incentivize.

## 2. What miners do
Every **~60 s** (`SAMPLE_EVERY=5` blocks): run **your own model**, produce predictions across the challenges, **timelock-encrypt** them (Drand IBE + X25519 — nobody can peek until maturity), and upload the JSON payload to **your Cloudflare R2 bucket** (object key = your hotkey, ≤25 MB, overwrite each cycle).

**Challenges & weights:**
| Challenge | Predict | Weight |
|---|---|---|
| MULTI-BREAKOUT (33 assets) | continuation vs reversal on 4-day breakouts | **5.0** |
| FUNDING-XSEC (20 assets) | perp funding-rate-change rank | **4.0** |
| ETH-LBFGS | 5 vol-regime probs + 12 exceedance thresholds | **3.5** |
| XSEC-RANK (33 assets) | cross-sectional return rank vs median | **3.0** |
| BTC-LBFGS-6H | vol regimes/thresholds, 6h | 2.875 |
| ETH-HITFIRST | which barrier hits first (up/down/neither) | ~2.5 |
| TRADEMIX (BTC/ETH/TAO/SOL) | timing + relative-value positions | ~2.6→15 |
| Binary ×5 (ETH + 4 FX) | 1h up/down | 1.0 each |

Zeroed if stale (std < 10⁻⁴), all-zero, constant, out-of-range, or probs don't sum to 1.

## 3. Scoring & incentive mechanism — *salience*
You are **not** scored on "were you right" but on **how much unique information your signal adds**. Per challenge, validators fit a **regularized meta-model** using *all miners' predictions as features* to predict the realized outcome (walk-forward, OOS, embargoed). Your **importance = |β_j|** (your coefficient) → normalized per challenge → × challenge weight → averaged → **EMA-smoothed (α=0.15)** → on-chain weights.

**Sybil/copy resistance:** L2 splits coefficient mass among correlated miners (n clones each get ≈ w/n); **>85% prediction overlap is zeroed**; L1 drives zero-info miners to 0. **Reward is proportional**, not KOTH — many miners earn at once.

## 4. How to win
1. **Have genuine, uncorrelated alpha** — a moderately-accurate *unique* signal beats a strong *crowded* one.
2. **Focus high-weight challenges** (MULTI-BREAKOUT 5.0, FUNDING-XSEC 4.0, LBFGS 3.5, XSEC-RANK 3.0).
3. **Submit continuously** — breakouts/funding shifts are rare (~1–5/asset/day); only live miners catch them.
4. **Respect format** (probs sum to 1, ranges [-1,1], vary predictions so std > 10⁻⁴).
5. **Feature ideas:** funding mean-reversion, OI shifts, momentum vs peers, liquidations, BTC→alt lead-lag; median-relative labeling isolates idiosyncratic skill.
6. **Backtest walk-forward** with the official Model Iteration Tool before going live. (TRADEMIX has a 21-day ≥90%-coverage probation.)

## 5. Hardware / device
**Light. No GPU required.** A modest **always-on VPS** runs the ~60 s submission loop; your model research happens offline on whatever hardware you like. **Uptime > raw power.**

## 6. Third-party services
- **Cloudflare R2** (mandatory payload host: `*.r2.dev` / `*.r2.cloudflarestorage.com`); commit URL on-chain once via `subtensor.commit()`.
- **Your own market data** to build features: Polygon (spot), OKX / Hyperliquid / CoinGlass (funding).
- **Drand beacon** (timelock), **Subtensor** (netuid 123 registration + weights).

## 7. Tech stack & setup
Python: `bittensor, torch, scikit-learn, numpy, boto3, timelock, cryptography, python-dotenv`. Dual encryption (X25519 ECDH + ChaCha20-Poly1305; Drand IBE BLS12-381). Validator storage: SQLite WAL.
```python
from generate_and_encrypt import generate_v2
payload = generate_v2(hotkey=my_hotkey, lock_seconds=30,
                      owner_pk_hex=OWNER_HPKE_PUBLIC_KEY_HEX, embeddings=embeddings)
# upload JSON to R2, key == hotkey, every ~60s
```
Key config: `BURN_PCT≈0.30–0.35` (UID 0), `NUM_UIDS=256`, `WEIGHT_SET_INTERVAL=360`, `MAX_DAYS=60`.

## 8. Economics & status
Proportional reward (not winner-take-all) — friendlier than KOTH — but **~30–35% burned**. Low compute cost, no per-inference bleed. Alpha economics change; check current price/mcap.

## 9. Honest take
**Highest skill ceiling and most "real" of the four** — the deliverable is genuine trading alpha, and you compete against other quants *and the market*. Copying is futile by design (L2 credit-split + uniqueness penalty). Best fit for a quant/ML-finance background with data infra; poor fit for plug-and-play miners. **Fastest start:** pick FUNDING-XSEC + XSEC-RANK (cross-sectional, clear features), backtest to real OOS edge, then submit continuously.
