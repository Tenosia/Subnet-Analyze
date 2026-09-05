# Sundae Bar — Subnet 121 (SN121)

**AI "skill" evaluation for a single commercial generalist agent.** Repos: `/home/vps-project/Bittensor/sundae-bar-subnet` (`sundae-bar/bittensor-subnet` — README/marketing only, no code) + `/home/vps-project/Bittensor/sb-validator` (`sundae-bar/sb-validator` — the actual validator, TypeScript, v1.0.21, Docker) + `/home/vps-project/Bittensor/sn121-ch-data` (one challenge's fixture data) · netuid **121** (finney).

> **Archetype: rubric-scored submission contest, majority-burn emissions.** Miners submit a scored artifact; an LLM-judge pipeline grades it; the current #1 miner is paid — but only a **minority share** of weight (20% by default), with the rest **burned every cycle**, not distributed. Closer to Tag101/Leadpoet's "CPU + LLM API" archetype than to Affine/Zeus's GPU-training archetype.
>
> ⚠️ **Accuracy caveat — the marketing README is stale.** `sundae-bar/bittensor-subnet`'s `README.md` (the project's public face, and the site copy at sundaebar.ai/subnetalpha.ai) describes a **Letta-based agent track**: miners build stateful agents in the Letta framework, submitted as `.af` files, evaluated via `letta-evals`. The actual validator repo (`sb-validator`, actively maintained, last commit within the past few weeks vs. the README repo's last real content commit months earlier) states explicitly: *"Removed agent track (`.af`): earlier releases also shipped a Letta-based agent track... Agent challenges were retired in favour of skills, and that stack has now been removed — the validator is skill-only, the Docker image no longer bundles Python."* **The live mechanism is `SKILL.md` submission + `sbevals` grading, not Letta agents.** Every "how a miner does" claim below reflects the shipped validator, not the framework-agnostic Letta pitch on the website.
>
> ⚠️ **Business-structure caveat.** SN121 is owned/operated by **Sundae Bar Plc**, a company listed on the London Stock Exchange's AIM market (ticker **SBAR**), formed from a 2025 merger of Ora Technology PLC and Kondor AI PLC. This is the only subnet in this workspace's series owned by a publicly-traded company — emissions are explicitly tied to that company's commercial revenue (see Economics below), which is a different risk profile than a foundation/DAO-run subnet.

## Goal
Train, benchmark, and continuously improve **one flagship "generalist" commercial AI agent** through open competition, then deploy the current-best version on sundae_bar's enterprise marketplace (businesses rent it for HR, marketing, finance, coding-assistant workflows, etc. — see `assets/subnet121_flow.jpg`: client submits a brief → SN121 miners develop against it → validators score via AETS → winner is deployed to that client **and** listed generally on the marketplace for anyone to rent). Revenue from that commercial usage flows back to fund miner emissions (see Economics).

## What a miner does
Per the shipped validator, a submission is a **skill**: a `SKILL.md` file (a structured instruction/spec document), not a fine-tuned model or a hosted service.
1. Write a `SKILL.md` against a **Generalist Challenge** — `sundae_bar` defines the challenge (e.g. the business-documents-retrieval example in `sn121-ch-data`: org charts, PTO policy, expense policy, escalation matrices as the task's knowledge base) and ships a corresponding `suite.yaml` (datasets + targets + rubric + graders).
2. Submit the `SKILL.md` (mechanism: **not in any public repo I found** — no miner CLI/template exists in the `sundae-bar` GitHub org; this almost certainly happens via the coordinator API (`api.sundaebar.ai`) or a web dashboard, not a locally-run miner process. If you're planning to mine, this is the first thing to get confirmed directly from the team/Discord rather than assumed from any repo here.)
3. The validator's `sbevals` sidecar service loads a **test agent** with your `SKILL.md`, has it make live LLM calls to produce outputs for the challenge's dataset, then scores those outputs with **LLM-as-judge graders** defined in `suite.yaml`.
4. All submitted skills are required to be fully open-source and are publicly archived — no closed-source submissions.

## Scoring / evaluation
- **Rubric-based, weighted metrics** (README example): Task Completion 35% (deterministic schema/graders), Reasoning Quality 25% (LLM judge), Retrieval Accuracy 20% (exact+semantic match), Tool-Use Efficacy 20% — weights sum to 100%, with pass/fail gate conditions that zero out low-quality submissions before ranking (`overall_gate_passed` in the coordinator API contract).
- Each rubric runs **multiple seeds, across multiple validators**, and is aggregated into a single consensus score per submission (`docs/coordinator-api-prd.md`).
- **Leaderboard, not central weight file:** the coordinator (`GET /api/v2/validators/competitions/active`) serves the current competition's leaderboard as **read-only data** — `{miner_hotkey, best_score, submitted_at}` per miner. It does **not** tell the validator what weight to set (that endpoint was explicitly retired — see `docs/coordinator-api-prd.md` §6).
- **Each validator independently, deterministically picks the winner**: highest `best_score`; ties broken by earliest `submitted_at`, then hotkey — reproducible, so every honest validator converges on the same winner from the same public data.
- **Reproducibility/anti-fraud:** every scored result is pushed back to the coordinator with a `sha256` integrity hash over the canonical scoring inputs (`src/integrity.ts`); the public web app recomputes the hash to prove the displayed leaderboard matches what the validator actually scored.

### Emissions mechanism — this is the part most likely to surprise a new miner
`sb-validator`'s `weight-policy.ts`/`weights.ts` (documented in its README, "Bittensor Weights Configuration"):
- Every cycle (`BITTENSOR_WEIGHTS_INTERVAL_MINUTES`, default **30 min**, or immediately on a leaderboard change): resolve the current #1 miner's hotkey → metagraph UID, then set weights as **`EMISSIONS_PERCENT` (default `0.2` = 20%) to that UID, and the remaining ~80% burned to UID 0.**
- If there's no active competition, or no resolvable winner: **100% burned.**
- Framed as **"time at the top takes all"** — whoever holds #1 longest accumulates the most emissions over a competition's life — but even at #1 permanently, you only ever receive 20% of the subnet's emissions; the other 80% is destroyed, not redistributed. This is a materially different economic shape from Affine (winner gets 100%) or Tag101 (top-3 split most of it) — budget your expectations accordingly.
- **Revenue-backed scaling (business layer, not yet in validator code):** per the marketing README, once sundae_bar's enterprise platform generates rental revenue from the deployed agent, emissions become "fully collateralized by buyback inflows" — e.g. a $25k rental: $2.5k to sundae_bar ops, $22.5k to ALPHA(121) buybacks, of which up to $17.5k (70% of revenue) is the miner emissions cap, remainder to subnet liquidity. **This buyback/revenue mechanism is not visible in any code I could inspect** — it's a stated business model, not something you can currently verify on-chain or in a repo.

## Hardware / device
Confirmed from `sb-validator/min_compute.yml` and its README's "System Requirements" — **no GPU anywhere in this subnet**, miner or validator:
- **Miner** (per `min_compute.yml`, though note: this file is templated per Bittensor convention and may not reflect an actual miner process, given no miner code was found): 1-2 vCPU, 2-4 GB RAM, 5-10 GB SSD, Linux/Docker. GPU explicitly `required: false` — "miners also rely on third-party APIs."
- **Validator** (from the real, running validator): 1-2 vCPU, 2-4 GB RAM, 5-10 GB disk (mostly Docker images), stable internet (10 Mbps down / 5 Mbps up minimum) for API calls. GPU `required: false` — "all model inference is handled via third-party API calls." Runs via `docker compose up -d` (validator + `sbevals` sidecar + `watchtower` auto-updater).
- This is the CPU+API archetype (like Tag101/Leadpoet), not the GPU-training archetype (like Zeus/Affine) — the compute burden is pushed onto whichever LLM provider you call, billed per-token, not onto your own hardware.

## Third-party / dependencies
- **LLM providers** (per-challenge `suite.yaml` picks the provider — hold keys for whichever you expect): **Chutes** and **OpenRouter** are explicitly "primary for most skill challenges"; also supported: OpenAI, Anthropic (Claude), Google (Gemini), Together AI. This is both the miner's cost center (your skill's test-agent calls) and the validator's (LLM-as-judge grading calls) — as a miner your `SKILL.md`'s design should account for what it costs the *validator* to run it, since a badly-specified skill that burns huge amounts of judge-LLM tokens is presumably not viewed favorably even if not explicitly penalized in the visible rubric.
- **sundae_bar coordinator API** (`api.sundaebar.ai`) — the orchestration layer: task queue, submission intake, leaderboard, result storage. Closed-source (not in the public org).
- **`sbevals`** — sundae_bar's in-house skill-evaluation engine (`sundaebarai/sn121-skill-evals` on Docker Hub), closed-source, runs alongside the validator.
- **Bittensor / Subtensor** — unusually, `sb-validator` talks to the chain via **`@polkadot/api`** directly (a Node.js/TypeScript stack), not the Python `bittensor` SDK most subnets use. Chain endpoint (`wss://entrypoint-finney.opentensor.ai:443`) and netuid (121) are hardcoded, not configurable.
- **Docker Hub** — both `sundaebarai/sn121-validator` and `sundaebarai/sn121-skill-evals` images are pulled, not built, in the standard quick-start.
- **Sentry** (optional) — validator error/weight-submission monitoring.
- Historical/removed: Letta server + pgvector Postgres (the deprecated agent track) — don't set these up, the current compose stack doesn't include them.

## How to win
1. **Get the real submission mechanism confirmed before building anything** — this is the biggest open question. No public miner template/CLI exists; the marketing site's Letta-agent instructions are stale. Ask in the project's Discord/docs for the actual `SKILL.md` submission endpoint or dashboard.
2. **Optimize against the rubric, not vibes** — deterministic graders (schema validity, exact/semantic match) are worth more combined (55%) than the LLM-judge "reasoning quality" score (25%) in the sample rubric; make sure outputs are structurally correct before polishing prose quality.
3. **Watch the pass/fail gate** — a failed `overall_gate_passed` zeroes your score outright regardless of partial quality elsewhere.
4. **Time-at-the-top is the real game, not one-shot submission** — since weight is recomputed every 30 minutes (or immediately on a leaderboard change) and pays whoever is *currently* #1, holding the top spot for the whole competition window matters more than a single strong initial score; watch for challengers and be ready to resubmit/improve.
5. **Internalize the 20/80 split** — even a dominant, unchallenged #1 position caps your take at `EMISSIONS_PERCENT` (20% by default) of the subnet's weight; the rest is burned. Model your expected returns on that, not on a winner-take-all assumption.
6. **The commercial/revenue layer is the real long-term upside** (per the marketing narrative) but is unverifiable from code today — treat "your agent gets deployed commercially and funds future emissions" as a stated intent, not a guaranteed, auditable mechanism, until you can see it implemented.
7. **Everything is open-source by design** — your submitted skill is publicly archived; expect competitors to iterate on visible techniques (this cuts both ways: you can also learn from every other archived submission).

## Key files
- `sundae-bar/bittensor-subnet` `README.md` — the project pitch (Letta-agent framing; **stale relative to shipped code**), the rubric example, and the revenue-buyback economic model narrative.
- `sundae-bar/bittensor-subnet/assets/subnet121_flow.jpg` / `subnet121_value.jpg` — the client-brief → agent-dev → AETS-eval → deploy → marketplace-listing flow, and the emissions/buyback "virtuous cycle" diagram.
- `sb-validator/README.md` — the actual, current, code-accurate description of how submissions are evaluated and how weights are set.
- `sb-validator/min_compute.yml` — formal hardware spec (Bittensor-standard file).
- `sb-validator/.env.example` — every config knob + which LLM-provider keys are needed.
- `sb-validator/src/weight-policy.ts`, `src/weights.ts` — the deterministic winner-selection + 20/80 burn-split logic.
- `sb-validator/src/integrity.ts` — the canonical-JSON sha256 scheme used to make the leaderboard independently verifiable.
- `sb-validator/docs/coordinator-api-prd.md` — the coordinator↔validator API contract (competitions/active, task metadata, result submission) — the clearest single document on the actual data flow.
- `sn121-ch-data/` — one real challenge's fixture data (business org/policy documents), useful as a concrete sense of task difficulty even without a `suite.yaml`/rubric definition alongside it in this repo.

## Run / submit commands
**Validator (fully documented, works today):**
```bash
git clone https://github.com/sundae-bar/sb-validator.git && cd sb-validator
cp .env.example .env
# edit .env: VALIDATOR_MNEMONIC (registered SN121 hotkey w/ validator permit),
# API_URL=https://api.sundaebar.ai/api/v2/validators, SBEVALS_API_KEY,
# CHUTES_API_KEY and/or OPENROUTER_API_KEY at minimum
docker compose up -d
curl http://localhost:8080/health     # validator
curl http://localhost:8080/competition  # current leaderboard + this validator's weight vote
```
Requires a Bittensor hotkey already **registered on netuid 121 (finney) holding a validator permit** — the validator never registers/stakes for you (`btcli subnet register --netuid 121`, per Bittensor's own docs, first).

**Miner: no public command exists.** There is no `sb-miner` repo, no CLI, no `SKILL.md` submission example in the `sundae-bar` GitHub org as of this analysis. Register your hotkey the standard way (`btcli subnet register --netuid 121`), but the actual "how do I submit a skill" step needs to come from the team directly — treat any instructions you find elsewhere (Discord, the marketing site's Letta-agent walkthrough) with the same staleness suspicion flagged above until you've confirmed them against `sb-validator`'s current behavior.

## Verdict
**Lowest hardware barrier of the six subnets analyzed here (no GPU, CPU+API only, like Tag101/Leadpoet) — but the most operationally uncertain to actually start mining on.** The public-facing docs (website, GitHub README, third-party listing sites) describe a Letta-agent framework that the shipped validator has already retired in favor of a `SKILL.md`+LLM-judge model, and no public repo documents the miner-side submission flow at all — you'd be flying blind on "how do I actually submit" without going outside these repos. Economically, understand going in that the on-chain emissions mechanism burns ~80% of weight by design (20% cap to the leader), with the larger promised upside sitting in an unverifiable, business-narrative revenue-share tied to a small-cap AIM-listed company rather than in code you can currently audit. Worth watching as the tooling matures; not yet a subnet I'd treat as "ready to mine" the way the other five are.
