# Cartha (0xMarkets) — Subnet 35 (SN35)

**Not an AI subnet — a liquidity-mining subnet.** Repos: `/home/vps-project/Bittensor/cartha-validator` (`General-Tao-Ventures/cartha-validator`, Python, the weight-setter) + `/home/vps-project/Bittensor/cartha-cli` (`General-Tao-Ventures/cartha-cli`, the miner-facing registration/deposit tool) · netuid **35** mainnet (78 testnet).

> **Archetype: pure capital deployment, zero compute.** Every other subnet in this series has a miner running *some* software — a model, an inference server, an attack generator, an API proxy. SN35 has none of that. "Mining" here means depositing USDC into an on-chain vault (on Base, an Ethereum L2) and locking it for a chosen duration. Your reward is a direct function of `amount × lock_duration`, computed by a validator that does no ML evaluation at all — it just reads verified deposit data and applies a formula. This is the most literal "put up capital, earn yield" design of anything analyzed here, closer to a DeFi liquidity-mining program than to a Bittensor ML competition.
>
> **Rebrand/pivot history, confirmed**: subnetalpha.ai notes SN35 was previously **LogicNet**, an AI-reasoning subnet by AIT Protocol, discontinued in 2025 and pivoted wholesale to this DeFi design under new operators (General Tao Ventures / GTV). The public brand is **0xMarkets** (the perpetual-futures exchange this subnet supplies liquidity to); **Cartha** is the protocol/validator codebase's internal name. Both names refer to the same subnet.

## Goal
Power **0xMarkets**, a permissionless perpetual-futures exchange (forex pairs, crypto, and — per the roadmap — commodities, eventually tokenized stocks/bonds) offering traders up to 500x leverage. SN35's job is to be the exchange's **liquidity engine**: Bittensor emissions (ALPHA tokens) incentivize people to lock USDC into the exchange's trading-pair vaults, and the subnet's weight-setting mechanism rewards whoever provides the most, longest-committed capital.

## What a miner does
There is no neuron process to run. "Mining" is entirely a financial action performed through the `cartha-cli` tool and a web UI:
1. **Register** a Bittensor hotkey on netuid 35 (`cartha miner register --wallet-name ... --wallet-hotkey ...`).
2. **Choose a pool** (`cartha vault pools` lists the 6 currently available: BTC/USD, ETH/USD, EUR/USD, GBP/USD, JPY/USD, GOLD/USD, each with its own vault contract address on Base).
3. **Lock USDC** into a chosen pool's vault for a chosen duration (`cartha vault lock --pool-id ... --amount ... --lock-days ...`) — this opens a browser flow at `liquidity.0xmarkets.io` for a two-phase on-chain transaction (approve USDC allowance, then lock). The verifier service auto-detects the completed lock and includes it in the next weekly epoch.
4. That's the entire miner-side workflow. No software runs continuously on your end — you deposit, you wait, you get scored weekly.

### Two roles: principal vs. federated
- **Principal miner**: the hotkey that registered and operates a vault. Their Bittensor score is based on the **total** USDC locked across their *entire* vault — their own deposit plus everyone else's.
- **Federated miner**: anyone who locks USDC into an *existing* principal's vault. They don't need to register a hotkey or clear any threshold themselves — they earn a proportional share of whatever ALPHA their principal's vault earns, distributed **off-chain** by a separate tool (`cartha-principal-rewards`) using the same scoring formula at finer granularity, minus a commission the principal takes for operating the vault (principal's own "home" positions pay no commission; "guest"/federated positions do).
- **This is the practical low-capital entry point**: if you don't have $100k+ USDC, becoming a federated miner in an already-qualifying vault costs nothing beyond your deposit and gets you a fair, formula-driven share — no threshold to personally clear.

## Scoring / evaluation
Fully code-grounded from `cartha_validator/scoring.py` and `docs/ARCHITECTURE.md`, operating on a **weekly epoch** (Friday 00:00 UTC → Thursday 23:59 UTC, frozen at epoch start to prevent mid-week gaming):

- **Per-position score**: `position_score = pool_weight × amount_usdc × lock_boost`
  - `pool_weight = 1.0` for all pools currently (pre-DEX-launch equal-weight mode; post-launch this will shift to on-chain-queried allocations per pool, already coded but inactive)
  - `amount_usdc` = the amount frozen at epoch start — **mid-epoch top-ups don't count until the following epoch**, closing an obvious gaming vector
  - `lock_boost = min(lock_days, 365) / 365` — a 365-day lock gets the maximum 1.0 boost; a 182-day lock gets 0.5. **Locking longer is a direct, linear multiplier on your score at the same deposit amount.**
- **Miner score = sum of ALL active position scores**, not an average — every distinct position (different pool, different lock duration) adds its own contribution. A vault with many federated positions of varying lock lengths sums all of them.
- **Hard minimum threshold**: a principal miner's **entire vault** must total ≥100,000 USDC or the *whole vault* scores zero for that epoch — this zeroes out the principal **and every federated miner in it**, regardless of their own individual lock quality. This is the single most important number to know before starting.
- **Weight normalization**: `remaining_weight = 1 − trader_pool_weight (0.243902) = 0.756098`; each qualifying miner gets `(their_score / total_score) × 0.756098` of total subnet weight.
- **Fixed allocations regardless of miner performance**: 24.3902% always goes to a fixed "Incentive Pool" hotkey (ecosystem airdrops/trader rewards — not something you can earn into). If **no** miner clears the 100k threshold in a given epoch, the entire 75.6098% miner share routes to the subnet-owner hotkey as an **emission burn**, not left unpaid.
- **Reference emission rate** (display-only, not a guarantee): total subnet ALPHA emission is stated as `2952.0 ALPHA/day`; your estimated share is `your_weight × 2952.0`. I don't have live ALPHA(35) USD pricing to convert this to a dollar yield — check that yourself before modeling returns.

## Hardware / device
Almost a non-question for miners (there's no software to run), and trivially light for validators — confirmed from `cartha-validator/README.md`:
- **Miner**: no compute requirement at all. You need a Bittensor wallet, USDC, and a browser.
- **Validator**: 2 CPU cores, 4GB RAM, 20GB SSD, stable internet — this validator does no ML inference or heavy computation; it polls a REST API (the Cartha verifier), applies arithmetic, and calls `set_weights`. Genuinely one of the lightest validator footprints in this entire series (comparable to SN121's Node.js weight-setter, lighter than SN26/SN28/SN34's GPU-requiring validators).
- **Note**: validators must be **whitelisted by the subnet owner** to query the verified-miner list at all — this isn't a permissionless validator role the way most Bittensor subnets are; contact the team to be added.

## Third-party / dependencies
- **Base** (an Ethereum L2, chain ID 8453 mainnet / 84532 Sepolia testnet) — where the actual USDC vaults live; this is real on-chain DeFi infrastructure, not simulated.
- **USDC** — the deposit currency; you need real USDC on Base to participate at all.
- **Cartha Verifier API** (`api.cartha.finance`) — a centralized, operator-run service that is the validator's **single source of truth** for the frozen weekly miner list, deposit amounts, expiry, and deregistration status. The validator explicitly does not independently re-verify on-chain state in the default (and mainnet-required) mode — a materially centralized trust point, similar in shape to SN28 (gm)'s finalizer-trust model.
- **Cartha Leaderboard API** — receives ranking data post-publication for the frontend; not part of the reward calculation itself.
- **Bittensor / Subtensor** — standard hotkey registration, metagraph, and `set_weights`.
- **`liquidity.0xmarkets.io`** — the web UI that actually executes the on-chain lock transaction; the CLI opens this in your browser rather than submitting the transaction itself.

## How to win
1. **Understand the 100,000 USDC cliff first — it's binary, not gradual.** A vault at $99,999 earns exactly as much as a vault at $0: nothing. This is the single biggest strategic fact on this subnet.
2. **If you don't have six figures of USDC, go federated, not principal.** Find (or coordinate on) an existing vault that's already comfortably past the threshold, and lock into it — you get formula-proportional rewards minus the principal's commission, with none of the threshold risk.
3. **Lock long, not just large.** Since `lock_boost` is linear in days up to 365, a smaller amount locked for a full year can out-score a larger amount locked briefly — model the amount×duration product, not just deposit size.
4. **Watch for the DEX-launch pool-weight change.** Right now all 6 pools are equal-weighted; `pool_weights.py` already has the code to switch to on-chain, potentially unequal allocations once the actual 0xMarkets DEX goes live — that could make some pools meaningfully more or less rewarding overnight.
5. **If considering becoming a principal**, understand you're not just depositing — you're operating a vault other people may lock into, taking on the coordination/trust relationship and commission economics with any federated miners, and you personally bear the 100k threshold risk for the whole vault's collective epoch.
6. **This is fundamentally a capital-and-timing game, not a technical one** — there's no model to train, no server to run better than a competitor. Edge here comes from capital efficiency (hitting the threshold, optimizing lock duration) and DeFi-native judgment (which pools, when, alongside genuine platform trading-volume growth), not engineering.

## Key files
- `cartha-validator/README.md` + `docs/ARCHITECTURE.md` — the clearest, most precise documents in this analysis; formulas are stated exactly and match the code.
- `cartha_validator/scoring.py` — the position/miner scoring implementation.
- `cartha_validator/weights.py` — normalization, fixed trader-pool allocation, emission-burn fallback.
- `cartha_validator/pool_weights.py` — current equal-weight mode vs. the inactive-until-DEX-launch on-chain allocation path.
- `cartha-cli/README.md` — the full miner registration/lock flow, pool listing, status checking.
- `abis/vault.json` (in `cartha-validator`) — the on-chain vault contract interface.

## Run / submit commands
```bash
# Miner (no daemon — a one-time CLI flow, then you're done until you want to adjust)
pip install cartha-cli
cartha miner register --wallet-name <coldkey> --wallet-hotkey <hotkey>
cartha vault pools                                    # see available pools + vault addresses
cartha vault lock \
  --coldkey <coldkey> --hotkey <hotkey> \
  --pool-id BTCUSD --amount 1000.0 --lock-days 365 \
  --owner-evm 0xYourEVMAddress --chain 8453 --vault-address 0xVaultAddress
cartha miner status --wallet-name <coldkey> --wallet-hotkey <hotkey>   # check position, expiry, epoch inclusion

# Validator (must be whitelisted by the subnet owner first — contact them before setting this up)
cd cartha-validator && uv sync
uv run python -m cartha_validator.main --wallet-name <cold> --wallet-hotkey <hot> --netuid 35 --dry-run
```

## Verdict
**A completely different animal from every other subnet in this series — evaluate it as a DeFi liquidity-mining program, not as an AI opportunity.** The mechanism itself is honestly and precisely documented (formulas in the docs match the code exactly, a rarity across this whole series), and the weekly-epoch freeze + expiry filtering + deregistration handling show real engineering care against gaming. But the barrier to meaningful reward is capital, not skill: the 100,000 USDC all-or-nothing threshold means small independent depositors need to federate into an existing qualifying vault rather than go it alone, and the entire reward depends on trusting a centralized, operator-run verifier API as ground truth for who deposited what. If you came here expecting a mining opportunity that rewards technical work, this isn't it — if you have real USDC to deploy and want Bittensor-native yield on it, it's one of the more transparently-engineered options in this set.
