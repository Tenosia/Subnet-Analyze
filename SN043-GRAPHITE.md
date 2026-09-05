# Graphite — Subnet 43 (SN43)

**Graph/routing optimization (TSP family) — now folded into a three-way reward split that also includes real portfolio trading.** Repo: `/home/vps-project/Bittensor/Graphite-Subnet` (`GraphiteAI/Graphite-Subnet`, Python) · netuid **43** (finney).

> ⚠️ **The top-level `README.md` describes only about 60% of what the subnet actually pays for.** It's entirely about solving the Traveling Salesman Problem — no mention anywhere of the **"TaoTrader" Leader/copy-trading system** or the **"organic portfolio rebalancing"** stream, both of which are fully documented in `docs/miner.md` and account for 40% of total subnet rewards combined. This isn't a deprecation (like Sundae Bar's Letta removal) — it's the opposite: two entirely new reward mechanisms were **added** without the top-level pitch ever being updated to mention them. If you only read the README, you'd think this is purely a TSP-solving subnet; it's not, anymore.

## Goal
Originally: solve NP-hard graph/routing optimization problems (Traveling Salesman Problem and its variants) via decentralized competition — real-world-applicable to logistics, delivery routing, and network design. As of the current codebase, the mission has expanded to include **portfolio rebalancing and copy-trading** through a companion platform called **TaoTrader** (`taotrader.xyz`) — miners can additionally act as trading "Leaders" whose on-chain portfolio moves other users can copy, turning part of the subnet into a DeFi-adjacent incentivized-trading product layered on top of the original combinatorial-optimization one.

## What a miner does — two genuinely separate paths

### Path 1: Graph-problem solving (the original mission, 60% of total rewards)
1. Run the miner neuron (`python3 -m neurons.miner --netuid 43 ...`), which listens for validator-generated synthetic routing problems and responds with a solution within a **20-second default timeout**.
2. Solve using one of four provided reference solvers — **Nearest Neighbour** (fast heuristic, also the scoring benchmark), **Dynamic Programming** (exact but exponential, impractical past ~20 nodes), **Beam Search** (tunable heuristic), **Hybrid Pointer Network** (a trained attention-based neural solver, pretrained weights shipped in the repo) — or bring your own solver.
3. Supports both coordinate input (undirected graphs) and edge input (directed graphs), and multiple problem variants beyond plain TSP: **TSP, MTSP (multi-depot), MDMTSP, CMDMTSP/RCMDMTSP (constrained variants)**, each scored and weighted separately within the 60% bucket (see Scoring).

### Path 2: TaoTrader "Leader" (copy-trading, 20% of total rewards)
A completely different activity — no solver code, no neuron loop:
1. Sign up at `taotrader.xyz/yield/signup`, choose the "Leader" role, connect your wallet.
2. Enter and verify ownership of your **SN43 miner hotkey** (signature-verified).
3. **Fund the linked coldkey with 5–15 TAO** (free + staked balance combined) — both a floor and a ceiling; you cannot transfer TAO in or out of this account once active.
4. Activate leader status and manage a portfolio (rebalancing across subnets) that other users can choose to copy-trade.
5. Rebalance within a **300-block adjustment window**, then face a mandatory **6,900-block no-trade cooldown** before your next rebalance — an explicit anti-scalping guard.

### Path 3: Organic portfolio rebalancing (20% of total rewards)
Documented far more thinly than the other two — appears to be a related but distinct real-request (non-synthetic) portfolio-rebalancing reward stream, separate from the Leader/copy-trading metrics. The repo's `docs/organic_db.md` and `graphite/validator/organic_forward.py` are the places to look if you want to pursue this path specifically; I did not find it explained in comparable depth to the other two.

## Scoring / evaluation

**Total reward split** (from `docs/miner.md`, the only place this is documented at all):
- **60%** — the original synthetic graph/routing problems, itself split: TSP 10% (of the 60%, i.e. 6% of total), MTSP 10% (6% of total), MDMTSP 20% (12% of total), CMDMTSP/RCMDMTSP 40% (24% of total) — the constrained multi-depot variant dominates this bucket.
- **20%** — organic portfolio rebalancing (thinly documented; see above).
- **20%** — TaoTrader Leader/copy-trading, scored hourly on six weighted metrics: **Sharpe Ratio (55% — by far the dominant factor)**, Historical Daily P&L (10%), Volume Traded (10%), Number of Copy Traders (10%), Max Drawdown (10%), Notional Value of Copy Traders (5%).

**Graph-problem scoring** (`graphite/validator/reward.py`): each miner's submitted solution is compared against (a) the best solution submitted by the cohort of miners answering that same challenge, and (b) a benchmark — the **Nearest Neighbour greedy solver** — computed independently by the validator. Relative performance against the cohort's best answer drives your reward; falling short of the greedy benchmark gets you **penalized**, not just scored lower — beating a simple, fast heuristic is a hard floor, not a nice-to-have.

**Leader scoring**: computed **hourly**, dominated by risk-adjusted return (Sharpe Ratio at 55% of that bucket's weight) rather than raw profit — a Leader who takes big, lucky wins without controlling drawdown scores worse than one with steadier, risk-controlled returns.

## Hardware / device
Confirmed from `min_compute.yml` — no GPU required for either role handling the graph-problem path:
- **Miner**: 4+ CPU cores @ 2.5GHz (8 recommended), 8GB RAM (16 recommended), 10GB storage, GPU **not required**. TSP heuristics are CPU-bound; even the neural Hybrid Pointer Network solver ships as a small pretrained model, not something requiring training-scale compute from you.
- **Validator**: 4+ CPU cores, 16GB RAM (32 recommended), SSD storage with real IOPS requirements (1000 min / 5000 recommended) — no GPU either.
- **TaoTrader Leader path**: no compute at all — it's a web-platform trading activity, not a running neuron. The real "hardware" requirement there is 5–15 TAO of locked capital, not a machine.

## Third-party / dependencies
- **TaoTrader** (`taotrader.xyz`) — the separate web platform hosting the Leader/copy-trading system; a real external dependency for that reward stream, operated by (presumably) the same team but as a distinct product.
- **Weights & Biases (wandb)** — referenced in validator setup docs (`static/wandb-settings.png`) for distance/scoring logging.
- **`yield_server`** — referenced in `docs/validator.md` as a separate, apparently open-sourced backend component validators need for the yield/portfolio subsystem's proxy generation and database schema — not fully contained in this repo.
- **Bittensor / Subtensor** — standard registration and `set_weights`; no GPU-cloud, no LLM-API, no TEE dependency for the core graph-solving path.

## How to win
**Graph-problem path:**
1. **Beat the greedy Nearest-Neighbour benchmark decisively** — falling short is an explicit penalty, not just a low score, so this is a hard floor to clear before relative-ranking against other miners even matters.
2. **The reward-weighted problem mix favors constrained multi-depot variants** (CMDMTSP/RCMDMTSP alone is 24% of total subnet rewards, 4x plain TSP's share) — if you're going to specialize your solver development effort, that's where the emission-weighted payoff is largest.
3. **Bring your own solver past the provided four** — the docs explicitly frame the shipped Greedy/Beam/DP/HPN solvers as a floor to build on, not a ceiling; reward is relative to the cohort's best answer, so out-innovating other miners is the actual game, not just beating the benchmark.
4. **Respect the 20-second response timeout** — a correct-but-late solution presumably scores no better than a wrong one; solver speed matters alongside solution quality.

**TaoTrader Leader path:**
1. **Optimize risk-adjusted return, not raw profit** — Sharpe Ratio is 55% of this bucket's score; a steady, drawdown-controlled strategy beats a volatile high-return one.
2. **Build a track record that attracts copy-traders** — Number of Copy Traders (10%) and Notional Value of Copy Traders (5%) are separate, real scoring factors, so a strategy that's *visibly* trustworthy (not just quantitatively good) compounds your score.
3. **Plan around the no-trade cooldown** — 6,900 blocks (multiple hours) of lockout after every rebalance means you can't react to the market freely; strategy needs to account for this constraint, not fight it.
4. **Understand the capital lock**: no TAO transfers in or out while active, and a hard 5–15 TAO band — this is a real, illiquid commitment, not a passive yield product you can exit anytime.

## Key files
- `docs/miner.md` — the only document that explains the full three-way reward split; read this instead of the README for anything beyond pure TSP mechanics.
- `graphite/validator/reward.py` — the graph-problem scoring implementation (cohort-relative + greedy-benchmark penalty).
- `graphite/solvers/` — all four reference solvers plus the multi-depot/portfolio variants (`greedy_solver_multi_*.py`, `greedy_portfolio_solver.py`).
- `graphite/yield_protocol.py` / `graphite/validator/yield_forward.py` — the Leader/copy-trading protocol and scoring dispatch (thin — most of the real logic likely lives in the separate `yield_server` backend, not in this repo).
- `graphite/validator/organic_forward.py` + `docs/organic_db.md` — the least-documented of the three reward streams.
- `min_compute.yml` — confirms no GPU requirement for either miner or validator role on the graph-solving path.

## Run / submit commands
```bash
# Graph-problem miner
python3 -m neurons.miner --netuid 43 --subtensor.network finney \
  --wallet.name NAME --wallet.hotkey HOTKEY \
  --logging.debug --axon.port PORT --blacklist.force_validator_permit True
# or via pm2:
pm2 start neurons/miner.py --name graphite_miner --interpreter python -- \
  --netuid 43 --subtensor.network finney --wallet.name NAME --wallet.hotkey HOTKEY \
  --axon.port PORT --blacklist.force_validator_permit True
```
TaoTrader Leader path has no CLI — it's entirely the web signup flow at `taotrader.xyz/yield/signup` (sign in → choose Leader role → connect wallet → verify hotkey ownership via signature → fund coldkey 5–15 TAO → activate).

## Verdict
**A subnet that's grown well beyond its own pitch, in a way that materially changes what "mining here" means depending on which path you take.** The graph-optimization side is a mature, low-hardware-barrier (CPU-only), genuinely useful combinatorial-optimization competition with real anti-cheating structure (a hard benchmark floor, cohort-relative scoring). The TaoTrader Leader path is something else entirely — a real-capital, real-risk trading activity with meaningful lockup constraints, sitting inside the same subnet's reward pool. Before choosing a path, be honest about which skill you actually have: solver/algorithm engineering for the graph-problem 60%, or genuine risk-adjusted trading skill (and TAO to lock up) for the Leader 20%. Don't assume the README's TSP framing is the whole story — verify the current split and metric weights at the source (`docs/miner.md`) since this subnet has clearly kept expanding past what its own front door describes.
