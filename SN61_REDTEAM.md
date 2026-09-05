# RedTeam — Subnet 61 (SN61)

**Miners build Dockerized bots that beat browser-automation/bot detection, and vice versa.** Repo analyzed: `/home/vps-project/Bittensor/RedTeam` (`RedTeamSubnet/RedTeam` — the core validator/subnet library and challenge config, **not** the runnable miner node) · netuid **61** mainnet, spec version **4.9.6** (matches the `docs.theredteam.io/4.9/` URLs given).

> ⚠️ **The docs site contradicts itself on which challenges are active — and so does this repo's own `docs/` folder.** `docs.theredteam.io/4.9/miner/` lists three active challenges (AB Sniffer, Humanize Behaviour, Anti-Detect Automation Detection) with only "Device Fingerprinter" tagged `(Inactive)`. But `docs.theredteam.io/4.9/challenges/` explicitly lists **Humanize Behaviour and ADA as inactive** alongside FlowPrint/FlowRadar/Device Fingerprinter/Historical Fingerprinter. The tie-breaker is the file the validator actually loads at runtime, `src/redteam_core/challenge_pool/active_challenges.yaml` — it defines exactly **two** challenges: `ab_sniffer_v6` and `bot_virus_v1`. Bot Virus isn't mentioned in `docs/miner/README.md`'s challenge list at all, despite carrying the *larger* incentive weight of the two (0.6 vs 0.4). Trust the yaml, not either doc page.
>
> ⚠️ **The "decay" mechanism is not linear, and not over 14 days.** `docs.theredteam.io/4.9/` describes "points decay linearly over 14 days." The actual code (`ABSChallengeManager`/`BVChallengeManager.get_challenge_scores`, identical in both live challenges) is: **zero decay for the first 10 days** (`stable_period_days`), then a **parabolic (quadratic) falloff** from day 10 to day 15 (`expiration_days`) — `decay_factor = 1 - progress**2`, not linear — reaching exactly zero at day 15, plus a small separate saturating exponential penalty (`exp(-0.002 * min(days, 10))`, ≤~2%) layered on top. Practical effect: you have a genuine 10-day grace window with **no** decay at all, then a fast quadratic drop-off in the last third of the window, not a steady 14-day slide.
>
> ⚠️ **This repo is not the miner node.** `RedTeamSubnet/RedTeam` is the core library the validator runs (challenge configs, scoring aggregation, the `Commit` synapse). The actual thing you run to mine is a separate repo, `github.com/RedTeamSubnet/miner`, referenced throughout the docs but not present in this checkout.

## Goal
Turn adversarial browser-automation skills — normally used to build bots that evade detection, or detectors that catch them — into a paid, structured competition, with the resulting detectors/evasion techniques licensable to real enterprises (1inch DEX aggregator is cited as an integration client). Framed by the team as "channel red-team skills into legitimate, rewarding work." The subnet is explicitly modular: challenges rotate in and out over time (six are already retired: FlowPrint v1/v2→FlowRadar v2, Device Fingerprinter, Historical Fingerprinter, ADA, Humanize Behaviour), so the two live today (AB Sniffer, Bot Virus) are a snapshot, not the permanent challenge set.

## What a miner does
1. **Pick a live challenge** — currently only `ab_sniffer_v6` (detect 9 named automation frameworks: `nodriver`, `seleniumbase`, `seleniumdriverless`, `patchright`, `puppeteer-extra`, `zendriver`, `botasaurus`, `pydoll`, generic `headless`) or `bot_virus_v1` (build a containerized browser bot that itself evades detection — the inverse task, and the higher-weighted one).
2. **Build a solution as a Node.js-SDK Docker image** targeting Ubuntu 24.04 (amd64). For AB Sniffer specifically: browser-fingerprinting-based detection is explicitly disallowed — you must key off automation-framework behavioral signatures, not generic device fingerprints, and must not false-positive on genuine headed/headless human browsers.
3. **Push the image to a *private* Docker Hub repository** (public exposes your solution to competitors who can copy it), generate a **read-only Personal Access Token**, and reference the image by its exact **SHA256 digest** (not a mutable tag) in `active_commit.yaml`: `<challenge_name>---<username>/<repo>@sha256:<digest>`. Only one commit per challenge per day is accepted — extras are silently ignored, not queued.
4. **Run the separate `RedTeamSubnet/miner` node continuously** (Docker Compose) with your wallet/hotkey and Docker Hub PAT configured — the node handles the real, on-chain **commit-reveal** exchange with validators via a custom `Commit` bittensor `Synapse` (`src/redteam_core/protocol.py`): it Fernet-encrypts `challenge_name---docker_hub_id`, holds the decryption key secret for `COMMIT_COOLDOWN` (24h, `RT_COMMIT_COOLDOWN`), then reveals it — so competitors can't see or copy your Docker Hub reference until a full day after you committed to it. This is a real, code-verified commit-reveal scheme (unlike some subnets where a README's crypto-sounding claim turns out to be marketing).
5. **Wait for daily scoring** and monitor results on `dashboard.theredteam.io`.

## Scoring
Fully code-grounded from `src/redteam_core/challenge_pool/active_challenges.yaml`, `src/redteam_core/validator/miner_manager.py`, `src/redteam_core/validator/challenge_manager.py`, and the two live challenges' own manager code (`ab-sniffer-challenge` and `bot-virus-challenge` repos, fetched directly since their code lives in git submodules this checkout didn't have initialized):

**Per-submission (`ABSChallengeManager`/`BVChallengeManager.update_miner_scores` — both challenges share the identical formula, only the raw-score floor differs):**
- A raw `score` (0-1, challenge-specific — the actual detection/evasion logic lives in the challenge's own container, not visible from the core repo) and a `penalty`/similarity score against the pool of prior best submissions.
- **Acceptance gate**: `0 ≤ penalty ≤ comparison_min_acceptable_score` (0.6 for both live challenges — matches the AB Sniffer doc's "over 60% similarity = rejected") **and** `score ≥ min_score` (**0.4** for `ab_sniffer_v6`, a much stricter **0.85** for `bot_virus_v1` — the bot-evasion challenge has a far higher raw quality bar despite paying more).
- If accepted, score is then scaled down by an eased similarity-penalty curve (`_adjust_score_by_similarity` — full credit below 40% similarity, a smooth eased reduction from 40-60%, harsher beyond) and the commit is added to a capped pool of the challenge's **15 best unique commits** (`max_unique_commits`) used as future comparison references.

**Aggregation to on-chain weight (`get_challenge_scores` per challenge, then `MinerManager._get_challenge_scores`):**
- Time decay applied to each miner's *best* commit (see warning above: 10-day flat, then quadratic to zero by day 15) — **you must actively resubmit within the window to avoid falling off**, not "eventually" as a slow linear docs description implies.
- A **softmax with temperature 0.2** (`reward_temperature`) converts decayed scores into a normalized distribution *within each challenge* — a low temperature, meaning small raw-score gaps translate into large weight-share gaps (winner-take-most-flavored, not a gentle proportional split).
- Each challenge's normalized scores are then multiplied by its `challenge_incentive_weight` (**AB Sniffer 0.4 / Bot Virus 0.6** currently) and summed. If a challenge has zero total score (nobody has an accepted submission), its weight is **redistributed proportionally to the other active challenges**, not burned — a subnet with only one working challenge currently would give that challenge 100% of weight.
- **`ALPHA_BURN_WEIGHT` (defined as 0.5 in `config/main.py`) is currently unused** — `MinerManager.get_onchain_scores` sets `final_scores = challenge_scores` with the entire alpha-burn code path commented out. Despite the constant existing at 50%, **100% of on-chain weight currently comes from challenge performance alone.**
- **Anti-sybil dedup (`exclude_same_miner`)**: before final normalization, submissions are grouped by axon IP, then merged further if they share a **coldkey** or a **Docker Hub username** across different IPs — within each merged group, only the single best score survives; everything else in that group is zeroed. This directly forecloses the "run several hotkeys/agents to occupy multiple top ranks" gap found live on SN60/Bitsec — worth noting as a real point of contrast between two subnets analyzed back-to-back in this series.

## Hardware / device
Genuinely light, and consistent between the docs and what the code implies:
- **Miner node** (per `docs/getting-started/miner.md`): 2+ CPU cores, 8GB+ RAM, 50GB+ storage, Linux (Ubuntu 22.04 LTS+ recommended), Docker + Docker Compose, Python ≥3.10 — this just runs the commit-reveal coordination, not your actual solution.
- **Your challenge solution container** itself is resource-capped by the validator's own run config (`miner_container_run_kwargs` in `active_challenges.yaml`): 4 CPU cores, 12GB memory limit for both live challenges — plan your solution to run within that envelope, since it's what actually gets evaluated.
- No GPU anywhere in this subnet's stack — this is a browser-automation/behavioral-detection problem, not an ML-training one.

## Third-party / dependencies
- **Docker Hub** — a funded/free account works, but you need a **private repository** (public defeats the anti-copying design) and a read-only **Personal Access Token**; "one Docker Hub username per `active_commit.yaml`" is enforced (mixing usernames across challenges breaks pull auth).
- **`RedTeamSubnet/miner`** — the actual node repo you run; separate from the analyzed repo.
- **`RedTeamSubnet/ab-sniffer-challenge`** / **`RedTeamSubnet/bot-virus-challenge`** — the two live challenges' own repos (wired into this repo as git submodules, not checked out by default); this is where challenge-specific solving logic and testing manuals actually live.
- **`storage-api.theredteam.io`** — where miner submission state is persisted validator-side.
- **`dashboard.theredteam.io`** — the live leaderboard/monitoring UI; check here for current standings rather than any static doc.

## How to win
1. **Bot Virus (0.6 weight) outweighs AB Sniffer (0.4)**, but demands a much higher raw score to even qualify (0.85 vs 0.4 minimum) — it's the harder, better-paid path; AB Sniffer is the more accessible entry point given a 0.4 floor.
2. **Originality is scored, not just quality** — the similarity/penalty gate caps out at 60% resemblance to the current best-15 pool per challenge; converging on the same well-known technique as existing top miners caps your effective score even if your raw detection/evasion quality is high.
3. **Time your resubmissions to the 10-day stable window** — since decay is flat for 10 days then drops quadratically to zero by day 15, refreshing your commit just before day 10 (rather than waiting until it's visibly decaying) keeps you consistently in the undecayed band.
4. **Watch for one-hotkey-per-entity enforcement** — unlike some other subnets, running multiple hotkeys/submissions from the same coldkey, IP, or Docker Hub username here nets you the same single best score, not a multiplied payout; there's no advantage to spreading submissions across identities on this subnet.
5. **A near-zero softmax temperature (0.2) means close races are winner-take-most** within a challenge — incremental raw-score improvements over the current top submitters are disproportionately rewarded versus a merely "acceptable" solution sitting mid-pack.
6. **The challenge roster itself rotates** — six challenges have already been retired; watch `active_challenges.yaml` (or the dashboard) directly rather than assuming today's two challenges (or their versions — currently `v6`/`v1`) stay fixed.

## Key files
- `src/redteam_core/challenge_pool/active_challenges.yaml` — the actual live challenge roster, weights, and thresholds; the single source of truth over either doc page.
- `src/redteam_core/validator/miner_manager.py` — on-chain weight aggregation (`get_onchain_scores`, `exclude_same_miner`, challenge-weight redistribution).
- `src/redteam_core/validator/challenge_manager.py` — the abstract base class + unique-commit-pool tracking (`max_unique_commits`).
- `src/redteam_core/protocol.py` — the real `Commit` synapse implementing Fernet-based commit-reveal.
- `src/redteam_core/config/main.py` — global constants (`COMMIT_COOLDOWN`, `EPOCH_LENGTH`, `CHALLENGE_SCORES_WEIGHT`/`ALPHA_BURN_WEIGHT` — the latter currently dead).
- `ab_challenge/challenge_manager.py` (`ab-sniffer-challenge` repo) / `bv_challenge/challenge_manager.py` (`bot-virus-challenge` repo) — the actual decay/softmax/similarity-adjustment formulas (identical structure, different thresholds).
- `docs/miner/workflow/` (1-5) — the step-by-step build/publish/submit/monitor guide within this repo.

## Run / submit commands
```bash
# Core repo (this checkout) — validator/library code and challenge configs, reference only for a miner
git clone https://github.com/RedTeamSubnet/RedTeam.git

# The actual miner node — separate repo
mkdir -p ~/workspaces/projects/redteam61 && cd ~/workspaces/projects/redteam61
git clone https://github.com/RedTeamSubnet/miner.git && cd miner

cp ./templates/configs/active_commit.yaml ./volumes/configs/agent-miner/active_commit.yaml
# edit with: <challenge_name>---<docker_username>/<repo>@sha256:<digest>
# e.g. ab_sniffer_v6---my_username/my_repo@sha256:abc123...

cp ./templates/configs/personal_access_token.txt ./volumes/configs/agent-miner/personal_access_token.txt
# paste your Docker Hub read-only PAT

cp .env.example .env
# set RT_BTCLI_WALLET_DIR, RT_MINER_WALLET_NAME, RT_MINER_HOTKEY_NAME

./compose.sh validate
./compose.sh start -l

btcli subnet show --netuid 61
btcli wallet overview --wallet-path ~/.bittensor/wallets --wallet-name my_wallet --wallet-hotkey my_hotkey --netuid 61 --verbose
```

## Verdict
**A legitimate, narrowly-scoped cybersecurity subnet with real code behind its anti-plagiarism claims** — the commit-reveal encryption is an actual working `Synapse`, not a documentation-only promise, and the same-entity dedup logic genuinely closes the multi-submission gap that another subnet analyzed in this same series (SN60/Bitsec) currently has wide open. The barrier to entry is low on hardware (no GPU, light CPU/RAM) but the real skill bar is a specialized one — browser-automation internals and anti-detection engineering, a narrower niche than general ML or LLM-agent work. Don't trust either docs page's list of "active" challenges or the "linear 14-day decay" framing; both are superseded by `active_challenges.yaml` and the challenge managers' actual parabolic decay math, respectively. Since this repo is the core library rather than the runnable miner, budget time to also pull `RedTeamSubnet/miner` and the specific challenge repo(s) you intend to compete on before you can actually start.
