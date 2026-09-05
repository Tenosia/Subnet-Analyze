# Bitsec — Subnet 60 (SN60)

**AI security agents that find real vulnerabilities in real, previously-audited smart contract codebases.** Repo: `/home/vps-project/Bittensor/sandbox` (`Bitsec-AI/sandbox`, Python) · netuid **60** mainnet.

> ⚠️ **subnetalpha.ai links to the wrong, dormant repo.** It lists `github.com/Bitsec-AI/subnet` — last pushed **2025-08-28**, about a year stale. The org's actual live codebase is `Bitsec-AI/sandbox` ("sandbox for bitsec v2"), last pushed **2026-08-10** (days ago at analysis time) and versioned as build 55. This is the same "third-party listing points at a superseded repo" pattern seen elsewhere in this series — always confirm which repo an org is actively shipping to before reading code as ground truth.
>
> ⚠️ **The on-chain synapse layer is dead code — all real work happens off-chain via a REST platform.** `neurons/miner.py` and `neurons/validator.py` are the *unmodified* Bittensor subnet template (the miner literally just doubles a dummy number; nothing in `forward()` was ever customized). Miners never talk to validators directly over the wire. Instead, everything — agent submission, sandboxed execution, LLM-judged scoring, and top-agent ranking — goes through `bitsec.ai`'s REST API (`validator/platform_client.py`), authenticated by signing a JSON payload with your wallet hotkey. The chain is used only for registration and for the validator's periodic `set_weights` call, fed by scores the validator fetches wholesale from the platform every ~60s (see below). This is a fully platform-mediated subnet wearing bittensor's registration/weights layer as a thin shell.
>
> ⚠️ **Live incentive data pulled directly from the platform API shows one miner currently capturing the entire non-burn reward pool**, because the payout code ranks by *agent*, not by *hotkey* (see "Scoring" below) — a concrete, verified instance of a real design gap, not a hypothetical.

## Goal
Replace expensive, slow human security auditors with AI agents. docs.bitsec.ai frames the problem directly: the industry spent an estimated $1.5B on human security researchers in 2025 and still let over $2.5B in losses through. Bitsec's plan is to have miner-built agents scan code (its own "Bitsec Scanner" product) and hunt live bug bounties ("Bitsec Hunter," worth $100k–$1M per critical finding on real programs), sharing bounty revenue back with the miners whose agents found the bug. The subnet is the training/proving ground: miners' agents get scored against real, previously-disclosed vulnerabilities from historic code4rena/cantina/sherlock audit competitions before ever touching a live bounty.

## What a miner does
1. Build an agent in `miner/agent.py` exposing `agent_main()`, returning a JSON report with a top-level `vulnerabilities` list. The shipped reference implementation (38KB, a real working baseline, not a stub) is a tool-calling loop against an LLM with three tools: `list_files`, `read_file`, `report_vulnerabilities`. It uses `qwen/qwen3.6-35b-a3b` (via OpenRouter) for structured JSON extraction and can route reasoning-heavy passes to `tngtech/DeepSeek-TNG-R1T2-Chimera-TEE`. Nothing stops a miner from swapping in static analysis (Slither, etc.), better prompting, or an entirely different model — the baseline is a floor, not a ceiling.
2. Register on the Bitsec platform (`bitsec.py miner create`, separate from bittensor registration) and submit the agent code plus an **OpenRouter API key** (`bitsec.py miner submit` — the CLI rejects any key that isn't prefixed `sk-or-`, so Chutes/other providers can't be used for miner-side inference even though they're used validator-side).
3. Iterate locally through three escalating checks before submitting: `miner execute-agent` (run the agent directly on one project), `miner run-no-docker` (local execution + scoring, project selection controlled via `project_keys` in `MockPlatformClient.get_job_run_agent`), then `miner run` (the full Docker Compose flow that mirrors production).
4. On the real network, the validator's `SandboxManager` pulls your submitted agent code, runs it in an isolated Docker sandbox against a validator-assigned real codebase, and captures its report.

## Scoring
Fully code-grounded from `validator/scorer.py`, `validator/evaluator.py`, and `validator/top_agents.py`, plus a **live API pull** against the production platform:

**Per-project evaluation (LLM-judge fuzzy matching, not exact string match):**
- The validator loads a curated benchmark of real disclosed vulnerabilities (`validator/curated-highs-only-2025-08-08.json` — the filename itself signals only **high-severity** findings are currently scored) for actual audited projects pulled from `GET /api/projects/` — live-verified to include real code4rena/cantina/sherlock competition repos: Superposition, LoopFi, SecondSwap, BakerFi, Kinetiq, Uniswap's `calibur` ("minimal-delegation"), and others.
- For each expected vulnerability, `ScaBenchScorerV2` asks a judge LLM (`moonshotai/Kimi-K3-TEE`, run through a Chutes proxy on the validator side, `x-request-phase: evaluation`) whether any of the agent's reported findings match it — a chunked, prefiltered (lexical + filename/function-hint similarity), confidence-scored comparison, not exact string matching. A match needs correct contract, correct function, matching root cause, and consistent impact description; confidence ≥0.75 auto-accepts.
- Produces `detection_rate` (recall), `precision`, and `f1_score` per project; a project only "PASS"es if `detection_rate == 1.0` (every expected high-severity bug found). The exact translation from these per-project metrics into a platform-side agent ranking is **not visible in this repo** — that aggregation happens server-side on bitsec.ai.

**Weight-setting (the part that actually moves TAO, `validator/top_agents.py::split_top_agent_scores`):**
- Every forward-loop tick (`template/validator/forward.py`, ~60s), the validator calls `GET /api/agents/top-with-burn/` and **overwrites its entire `self.scores` array** from the response — this is not an incremental EMA like most bittensor subnets, it's a full replace each cycle, driven entirely by the platform's current ranking.
- The response shape: a ranked `agents` list (each entry: `agent_id` + `hotkey`), a `burn` entry (`hotkey` + `percentage`), and a `payout_structure_pct` list (percentage-of-non-burn-pool per rank, by list position).
- Split logic: `burn_fraction` = burn percentage ÷ 100 (server-controlled, can change any cycle). For each rank `i` in `payout_structure_pct`, that percentage of the **remaining** (post-burn) pool goes to `agents[i]`'s hotkey. Any rank beyond the end of `payout_structure_pct`, any slot whose agent's hotkey isn't currently registered on the subnet's metagraph, and any unallocated remainder of `payout_structure_pct` (if it doesn't sum to 100) — all of that redirects into `burn_fraction` instead.
- **Live pull on 2026-08-13** (`curl https://bitsec.ai/api/agents/top-with-burn/`) returned: `burn.percentage = 50`, `payout_structure_pct = [70, 30]` — i.e. **only the top 2 ranked agents get paid at all**, currently split 70/30 of the post-burn 50% (→ 35% and 15% of total subnet weight), with the remaining 50% burned outright. Every other listed agent gets exactly 0%.
- **The real finding:** the `agents` list is ranked by *agent submission*, not deduplicated by *hotkey*. In the live response, the top **8 of 10** listed agent slots (ranks 0 through 7 — including *both* paid ranks 0 and 1) belonged to the **same hotkey**, which had submitted at least 8 separate agent versions (`agent_id`s 2836, 2835, 2775, 2834, 2783, 2847, 2846, 2848). Because `split_top_agent_scores` maps `payout_structure_pct[i]` to `valid_agents[i]`'s hotkey without deduplication, that one hotkey's UID received `new_scores[uid] += 0.35` *and* `+= 0.15` — the entire 50% non-burn allocation went to a single miner, simply because their agent versions occupied both paid ranks simultaneously. The only other hotkey present (ranks 8-9) earned 0%, as would any other miner not in the top 2 slots by rank.

## Hardware / device
`min_compute.yml` says `gpu.required: True`, 8GB min VRAM, 24GB recommended — this reads as unmodified boilerplate carried over from the original bittensor subnet template and does not match the actual "v2 sandbox" architecture, where the agent calls a cloud LLM API (OpenRouter) rather than running local inference. In practice, per the README's own requirements list: **Docker, Python 3.11+, `uv`**, a Bittensor wallet, and a **funded OpenRouter (miner) / Chutes (validator) API key** — no GPU is exercised by anything in this repo. Budget for real, ongoing per-request LLM API spend instead of a hardware purchase; the cost moved to a cloud API bill, same pattern seen on gm/SN28.

## Third-party / dependencies
- **OpenRouter** — required, funded API key for miner-side agent inference; the CLI validates the key prefix (`sk-or-`) at submit time.
- **Chutes** — required, funded API key for validator-side judge-model scoring (`CHUTES_API_KEY`); validators are explicitly told registration alone isn't enough — **the Bitsec team must manually activate your validator on the platform** before you receive any validation work.
- **Docker** — both roles; miners for local test/submit flow, validators for sandboxed agent execution (real, isolated project containers) plus an internal proxy container (`bitsec-net`, port 8087) that meters/relays LLM calls and reports usage stats back to the platform (`docs/proxy_metrics_platform_handover.md`).
- **code4rena / cantina / sherlock** — the source of the real audited codebases used as benchmark projects; not a Bitsec-run service, but the ground-truth data provenance.
- **`verify/generate.py` + `verify/verify.py`** — a standalone coldkey-sign/verify utility, unrelated to the automated scoring pipeline; looks intended for out-of-band identity proofs (e.g. proving hotkey ownership to the Bitsec team over Discord).

## How to win
1. **The platform, not the chain, decides who gets paid — optimize for the ScaBench-style judge, not a bittensor-native metric.** Detection rate against real, disclosed high-severity vulnerabilities is what's measured; false positives hurt precision but the code only gates "PASS" on `detection_rate == 1.0`, so recall on real bugs matters most.
2. **Multiple agent submissions under one hotkey can occupy multiple paid ranks simultaneously**, per the live data above — if your hotkey can place 2+ distinct agent versions in the top-N ranked slots, `split_top_agent_scores` pays all of them into the same UID. This is a real, currently-exploitable-looking mechanic, not a theoretical one; whether the Bitsec team intends this or will patch it (e.g. dedupe-by-hotkey) is unknown from the repo alone.
3. **The payout curve and burn rate are platform-controlled and change independently of any code push** — `payout_structure_pct` and `burn.percentage` are live server values (currently `[70,30]` and `50%`), not repo constants. Re-check `GET /api/agents/top-with-burn/` periodically rather than assuming the split you read about stays fixed.
4. **Improve the baseline agent, don't just run it as-is** — it's a genuine starting point (tool-calling loop + 2 models), not a placeholder; realistic upside is in tool selection (adding static analysis / Slither-style structural checks alongside the LLM), better chunking of large codebases, and reducing false positives that would otherwise dilute precision on borderline calls.
5. **Iterate through the three local-check tiers before ever submitting** — `execute-agent` → `run-no-docker` → `run` (Docker) — the middle tier lets you edit `project_keys` in `MockPlatformClient.get_job_run_agent` to test against specific historic projects and see your own detection rate before it counts for anything.

## Key files
- `validator/top_agents.py` — the entire on-chain weight-setting logic (`split_top_agent_scores`); read this before anything else if you want to understand what actually earns TAO.
- `validator/platform_client.py` — every REST endpoint the subnet actually uses (`agents/top-with-burn/`, `agents/submit/`, `jobs/runs/...`); the real "protocol" of this subnet.
- `validator/scorer.py` — the ScaBench LLM-judge matching logic (`ScaBenchScorerV2`), prompts and all.
- `validator/evaluator.py` — wires the scorer to the curated benchmark file and platform submission.
- `validator/manager.py` (`SandboxManager`) — the execution/scoring queue loop, Docker sandboxing, proxy lifecycle.
- `miner/agent.py` — the reference agent implementation; your actual competitive surface.
- `neurons/miner.py` / `neurons/validator.py` — vestigial bittensor template code; confirm for yourself it's unused rather than trusting this summary, since a future version could wire it up.
- `min_compute.yml` — stale/boilerplate; do not use for hardware planning (see warning above).

## Run / submit commands
```bash
git clone https://github.com/Bitsec-AI/sandbox.git && cd sandbox
uv sync

# Miner
echo "INFERENCE_API_KEY=your_openrouter_key" > .env
uv run ./bitsec.py miner create you@example.com "My Miner Name" --wallet my_wallet
export INFERENCE_API_KEY=your_openrouter_key
uv run ./bitsec.py miner execute-agent      # iterate on miner/agent.py directly
uv run ./bitsec.py miner run-no-docker      # local scoring against benchmark projects
uv run ./bitsec.py miner run                # full Docker-based local flow
uv run ./bitsec.py miner submit --wallet my_wallet   # prompts for your sk-or- OpenRouter key

# Validator (requires manual activation by the Bitsec team — see warning above)
cp .env-validator-example .env   # set CHUTES_API_KEY
uv run ./bitsec.py validator create validator@example.com "My Validator" --wallet validator
docker compose -f docker-compose.validator.yaml up --build -d
```

## Verdict
**A real, well-instrumented LLM-agent security subnet with a genuine commercial thesis (bug-bounty revenue share) and a benchmark built from actual disclosed vulnerabilities rather than synthetic toy data.** The architecture is honest about being platform-mediated — the README itself says "if the docs and this repository disagree, treat the code in this repository as the source of truth," and the bittensor synapse layer is openly unused boilerplate rather than a misleading facade. The standout finding is the live-verified rank-based payout not deduplicating by hotkey, which right now concentrates the *entire* non-burn reward pool (50% of total weight) onto one miner running multiple agent submissions — worth confirming directly against the live endpoint before mining here, since both the payout curve and this behavior could change without any git commit. Budget for real, recurring OpenRouter spend rather than a GPU purchase; the min_compute.yml GPU requirement does not reflect how this subnet actually runs.
