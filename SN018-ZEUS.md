# Zeus — Subnet 18 (SN18)

**Decentralized weather / climate forecasting.** Repo: [`Orpheus-AI/Zeus`](https://github.com/Orpheus-AI/Zeus) · Site: zeussubnet.com · netuid **18** (finney) / **301** (testnet).

> **Archetype: pure ML model competition** (like SN44/SN62). The default code ships a **random-number placeholder** — you compete entirely on the forecasting model you build. This is the closest analog to Ridges/Vision in this workspace.

## Goal
Replace slow, expensive **physics-based numerical weather prediction (NWP)** with fast **data-driven ML forecasting**. Validators score miners against real **ERA5 reanalysis** ground truth (Copernicus/ECMWF — hourly global data since 1940). The subnet's pitch is beating centralized SOTA: their BRP model reports **RMSE 1.05 K vs a 1.74 K baseline (~40% better)** on temperature, and ~0.89 RMSE on 2-day windspeed (~45% better).

## What a miner must produce
Predict a single ERA5 variable over the **full global grid** for a requested horizon.

- **Output shape:** `(requested_hours, 721, 1440)` at **0.25° resolution** (721 lat × 1440 lon), returned **blosc2-compressed → base64**.
- **Horizons:** short-range **49 steps** (0→+48h) or long-range **361 steps** (0→+360h / 15 days), always hourly.
- **Variables + challenge weights:**

| Variable | Weight |
|---|---|
| `100m_u_component_of_wind` | 0.30 |
| `100m_v_component_of_wind` | 0.30 |
| `2m_temperature` | 0.20 |
| `surface_solar_radiation_downwards` | 0.20 |

Wind (u + v = **60%**) carries most of the weight — prioritize it.

## What the miner does operationally
1. **Install:** clone repo, create **conda env (Python 3.11)**, run the setup script.
2. **Register** hotkey on **netuid 18** (mainnet) or **301** (testnet).
3. **Configure** `miner.env` (`NETUID`, `SUBTENSOR_NETWORK`, `WALLET_NAME`, `WALLET_HOTKEY`, `AXON_PORT`, `BLACKLIST_FORCE_VALIDATOR_PERMIT=True`). Open your axon port.
4. **Run continuously:** `./start_miner.sh` (long-running neuron).
5. **Commit–reveal each cycle:** at the hash window, compute forecast → compress with blosc2 → hash with your hotkey → **commit the hash on-chain** (Subtensor `Commitments` pallet). Then **reveal the identical compressed prediction** when a validator queries your axon. Mismatched/failed reveals are penalized (anti-copying).
6. **The real job:** replace the placeholder model with your trained forecaster.

## ⚠️ Default code is a placeholder
The stock miner is a naive random baseline:
```python
precomputed_forecast_15days = np.random.rand(24*15+1, 721, 1440).astype(np.float16)
precomputed_forecast_49hours = np.random.rand(49, 721, 1440).astype(np.float16)
```
`pre_compute_predictions()` has a `TODO` and isn't implemented. **You plug your model into `pre_compute_predictions()` in `neurons/miner.py`** (called at init and on each challenge block; results served by `_forward_unhashed_predictions()`). The protocol / commit-reveal plumbing is done for you — **the forecasting model is 100% on you.**

## Scoring / evaluation
- Validators fetch your grid, compare against **ERA5 ground truth** for the same time/variable.
- Metric is **error-based (RMSE-style)** per variable, aggregated with the challenge weights above. Lower error → higher incentive.
- Commit-reveal ensures you can't copy another miner's answer after seeing it; a failed/mismatched reveal is penalized.
- Training data is **free and effectively unlimited** (public ERA5), so there's **no proprietary-data barrier** — the barrier is **modeling skill**.

## Hardware / device
Two very different requirements — don't confuse them:

| | Run the miner (inference) | Train a competitive model |
|---|---|---|
| **GPU** | **Not required** — serves precomputed grids | **Required** — a serious GPU (multi-GB VRAM; more = faster iteration on global-grid tensors) |
| **RAM/disk** | Modest; grids are large but compressed | Large — ERA5 datasets are big; plan for substantial disk |
| **Network** | Stable axon (open port) | For downloading ERA5 training data |

Effectively: **cheap CPU box to run + serve**, but you need **real GPU compute to build the model** that wins.

## Third-party / dependencies
- **ERA5 / Copernicus CDS** for training data (public, free — register for a CDS API key).
- Bittensor wallet + `bittensor` / `btcli`.
- Python **3.11** (conda), `blosc2`, numpy, your ML stack (PyTorch etc.).
- No paid LLM/API keys required to *run* — only compute + data to *train*.

## How to win
1. **Build a real spatiotemporal forecaster** (e.g. graph/vision-transformer over the lat-lon grid, GraphCast/Pangu-style, or a fine-tune of an open weather model) — anything beats the random placeholder immediately.
2. **Prioritize wind** (`100m_u` + `100m_v` = 60% of the score).
3. **Nail both horizons** (49h and 361h) — long-range 15-day is harder and differentiates the field.
4. **Beat the ERA5 baseline RMSE consistently**; the reference BRP model (~1.05 K temp RMSE) sets the bar to aim at.
5. **Keep the neuron up 24/7** and ensure reveals always match commits (a broken reveal zeroes the round).

## Key files / commands
- `neurons/miner.py` → `pre_compute_predictions()` — **where your model goes**.
- `neurons/miner.py` → `_forward_unhashed_predictions()` — serves the compressed grid.
- `miner.env` — wallet/network/axon config.
- `start_miner.sh` — launches the neuron.

```bash
# after conda env + setup + wallet:
btcli subnet register --netuid 18 --subtensor.network finney \
  --wallet.name miner --wallet.hotkey default
./start_miner.sh
```

## Verdict
**Hard, but pure meritocracy** — no data moat, unlimited free training data, and the default is beatable trivially. Your ceiling is entirely your modeling skill + GPU budget. Best fit if you have weather/ML forecasting expertise or want a clean model-training competition.
