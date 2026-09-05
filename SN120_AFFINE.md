# Affine — Subnet 120 (SN120)

**Incentivized RL / reasoning-model competition.** Repo: `/home/vps-project/affine-cortex` (`AffineFoundation/affine-cortex`, package `affine.io`, CLI `af`) · netuid **120** (finney).

> **Archetype: ML model competition, winner-take-all.** A miner submits a **fine-tuned LLM** (as a HuggingFace model reference committed on-chain); the validator side evaluates it head-to-head against the reigning **champion** across reasoning environments. The single champion takes **all** emissions until dethroned.
>
> ⚠️ **Accuracy caveat:** `skill/references/scoring-deep-dive.md` describes an OLD multi-stage Pareto pipeline whose files (`stage2_pareto.py`, etc.) **don't exist** in this repo. The live mechanism is the champion-vs-challenger contest below (`scorer/comparator.py` + `scheduler/flow.py` + `scorer/weight_writer.py`).

## Goal
"Commoditize reasoning" by directing a permissionless crowd at RL/reasoning tasks (coding, program abduction/deduction, agentic tasks). Claims to be sybil-/decoy-/copy-/overfitting-proof (`README.md`). You find a model that is **strictly better on ≥1 eval environment without regressing on the others**.

## What a miner does
A miner submits a **model reference on-chain, not a running service** (`docs/MINER.md`, `affine/src/miner/commands.py`):
1. Train/fine-tune a model locally; upload weights to a **public HuggingFace repo** (repo name must **end with your hotkey**).
2. Commit `{"model": <hf_repo>, "revision": <sha>}` on chain (`af miner-deploy` does HF upload + commit; or `af commit` for an existing revision; `af pull <UID>` fetches the current champion to iterate on).
3. The validator/backend **hosts inference** for your model — **miners do NOT host inference.**

Every valid miner enters a **challenger queue ordered by `first_block`** (earliest commit first). One challenger at a time is deployed and evaluated head-to-head against the champion.

**Hard submission constraints** (`monitor/miners_monitor.py`, `utils/model_size_checker.py`):
- **Exactly ONE commit per hotkey** — a second commit permanently invalidates you.
- HF repo name must end with the hotkey; model must be **public**.
- **Architecture allow-list:** only **Qwen3-32B** (dense) or **Qwen3.6-35B-A3B MoE** (`qwen3_5_moe`); new submissions must be Qwen3.6-35B-A3B fine-tunes. Quantized configs rejected (matches config fields, not file size).
- Chat template must exist, be < 100k chars, and pass an **LLM security audit** (looks for embedded benchmark solvers / answer injection).

## Scoring / evaluation
A sequential, **winner-take-all champion/challenger tournament** (`scheduler/flow.py::FlowScheduler.tick()`):
- Per block tick: refresh the task pool, ensure the champion is deployed + sampled, pick the next challenger, deploy it, sample **both on the same task_ids**, run the comparator.
- **Dethrone rule** (`scorer/comparator.py::WindowComparator`): per env, classify the challenger vs champion as **dominant** (`chal > champ + 0.03` margin), **not_worse** (within ~2% tolerance), or **worse**. Production uses **partial Pareto** (`WIN_MIN_DOMINANT_ENVS = 1`): the challenger must be **dominant in ≥1 env AND not_worse in all the rest**. Any regression → it loses. An early-regression short-circuit ends a losing battle as soon as one env is definitively regressed.
- **Emissions** (`scorer/weight_writer.py`): winner weight **1.0**, everyone else **0.0**. The champion takes all emissions until dethroned; losing challengers are **permanently terminated** and the queue advances.
- **Task pool** refreshed every `WINDOW_BLOCKS = 7200` (~24h) between battles, oversampled ~10%.

**Environments** (`affine/core/environments.py` + `database/system_config.json`) — the catalog has ~20; the current seed marks **enabled_for_scoring: SWE-INFINITE, DISTILL-V2, TERMINAL** (verify the live backend `system_config` before targeting — it can differ). Others (REASONING, INSTRUCTION-GYM, TOKEN-EFFICIENCY) are sampling-only "shadow" envs. Per-env: SWE-* = SWE-bench software-engineering agent tasks; DISTILL-V2 = KL/CE distillation vs teacher rollouts; TERMINAL = terminal/agentic; ABD/DED = abduction/deduction reasoning; CDE/LGC/PRINT = code/logic/program-synthesis; etc.

## Hardware / device
- **Miner:** a **GPU box to train/fine-tune** a ~32–35B model (Qwen3-32B or Qwen3.6-35B-A3B MoE), then upload to HF. Miners **don't host inference**, so no serving hardware needed. (Repo gives no formal miner GPU table, but fine-tuning a 32–35B model implies serious multi-GPU / high-VRAM compute.)
- **Validator** (lightweight weight-setter): 2 cores / 4 GB / 20 GB, no GPU.
- **Backend/inference** (operator-run, the heavy part): per-window inference via **Targon serverless** or a GPU fleet (Lium B200/B300, sglang/vllm); anti-copy worker needs a GPU with ≥64 GB VRAM.

## Third-party / dependencies
- **HuggingFace** (model hosting, `HF_TOKEN` write scope for miners).
- **Bittensor / Subtensor** (`bittensor>=10.5`, `NETUID=120`).
- Operator/backend (not needed to mine): **Targon** (inference API), **Lium** (GPU autoscale), **Cloudflare R2** (rollout/dataset storage), **Docker Hub** (SWE task images), DynamoDB + Redis (backend state), a template-audit LLM API. Historical **Chutes** dependency (`API_KEY`/`CHUTES_API_KEY`).

## How to win
1. `af pull` the current champion, then **fine-tune / distill / RL-train** it into a model that is **dominant (≥3% margin) on at least one enabled scoring env and not-worse (within 2%) on every other**. Currently that means **SWE-INFINITE, DISTILL-V2, TERMINAL** — verify live config first.
2. **Never regress** on any scoring env — partial-Pareto winner-take-all means a single regression loses the whole battle.
3. **Commit early** — the queue is ordered by `first_block`; earliest committer among equals is favored, and the champion is never its own challenger.
4. **Stay within the architecture allow-list** (Qwen3.6-35B-A3B fine-tune) and pass the chat-template audit.
5. **Anti-copy is real:** the CEAC subsystem (`affine/src/anticopy/`) teacher-forces candidates through shared rollouts and compares per-token logprobs — a near-identical copy of an earlier miner is flagged `copy_of_hotkey` and invalidated. You must genuinely improve, not clone the champion.

## Key files
- `README.md` — purpose + champion/challenger mechanism.
- `docs/MINER.md` / `docs/VALIDATOR.md` — miner submission / validator ops + hardware.
- `affine/core/environments.py` — full env catalog (image, mem, required vars).
- `affine/database/system_config.json` — which envs are enabled for sampling/scoring.
- `affine/src/scheduler/flow.py` — the block-tick contest driver.
- `affine/src/scorer/comparator.py` — the Pareto-with-tolerance dethrone rule.
- `affine/src/scorer/challenger_queue.py` — first_block-ordered challenger queue.
- `affine/src/scorer/weight_writer.py` — winner=1.0 / others=0.0.
- `affine/src/miner/commands.py` — `pull` / `commit` / `miner-deploy`.
- `affine/utils/model_size_checker.py` — architecture allow-list.
- `affine/src/anticopy/*` — CEAC copy detection.

## Run / submit commands
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/AffineFoundation/affine-cortex.git && cd affine-cortex
uv venv && source .venv/bin/activate && uv pip install -e .

btcli subnet register --netuid 120
af pull <UID> --model-path ./model_path        # baseline champion to iterate on
# ... train/fine-tune into ./model_path ...
af eval --env affine:ded-v2 --base-url http://localhost:8000/v1 \
        --model myuser/affine-model --samples 10     # local sanity check

af miner-deploy --repo myuser/affine-model-<hotkey> -p ./model_path   # upload + commit
# or, if already uploaded:  af commit --repo myuser/affine-model-<hotkey> --revision <SHA>
af get-rank ; af get-scores --top 10 ; af get-weights                 # status
```
> Repo name must end with your hotkey; repo must be public; **only ONE commit per hotkey ever.**

## Verdict
**The hardest of the five.** Winner-take-all, one-shot commit, a required ~32–35B architecture, real anti-copy, and you must beat an actively-defended champion **without regressing anywhere**. Needs serious GPU budget + ML/RL expertise. High risk, high reward — but a losing challenger is terminated with nothing.
