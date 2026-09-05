# Ditto — Subnet 118 (SN118)

**Agent memory + tool-use benchmark ("DittoBench").** Org: [`ditto-assistant`](https://github.com/orgs/ditto-assistant/repositories) · product: [heyditto.ai](https://heyditto.ai/docs/) · netuid **118** (finney).

> 📎 **Engineering deep-dive (code-grounded from all 5 repos):** [SN118_DITTO_DEEPDIVE.md](SN118_DITTO_DEEPDIVE.md) — exact scoring formula, integrity gates, anti-cheat design, task families, and the harness internals you tune.

> **Archetype: agent/harness engineering competition, king-of-the-hill.** You don't train a model and you don't run a data pipeline — you submit a **containerized "agent-memory harness"** (code) that is benchmarked on **memory recall + tool-calling accuracy** against a *frozen* LLM and a *fresh* dataset. Closest cousin in this workspace: **Ridges (SN62)** — submit an agent, get benchmarked, winner-take-most. **CPU-only, 8 GB RAM, no GPU.**

## Purpose
Ditto is a persistent-memory AI assistant: it remembers you across weeks/months, clusters conversations into "Subjects," and builds a personal knowledge graph. The consumer app (heyditto.ai) is the product; the **subnet crowdsources the best memory+agent engine** behind it. Tagline: *"The Ditto Agent OS and Harness enable SOTA memory, healing, and speed for 1/100th of the frontier cost."* The subnet answers one question: **which harness best (a) recalls the right facts from a memory haystack and (b) calls the right tools with the right arguments** — using the same locked model for everyone.

## What a miner does
Build and submit a **Docker-containerized harness** that implements the fixed DittoBench HTTP contract — **3 endpoints on port 8080**:

| Endpoint | Purpose | Timeout |
|---|---|---|
| `GET /health` | health check | 10 s startup |
| `POST /seed` | install a fresh **memory haystack** (persona facts), delivered in staged waves | 5 min/wave |
| `POST /run` | given `RunRequest` (system prompt + user input + tool catalog) → return `RunResponse` (final text, observed tool calls, token counts, latency) | 60 s/case |

- **Language-agnostic:** the reference is Rust, but Python/TS/Go/Java/C++ are fine as long as they honor the HTTP contract.
- **Submit the entire buildable project** as a tarball with the `Dockerfile` at the root, **capped at 20 MB** (including any bundled model weights).
- Submit via the `ditto` CLI with a registered hotkey and pay the **~0.04 TAO eval fee**; your tarball flows `uploaded → screening → evaluating → scored` (or `screening_failed` if the Docker build or `/health` fails).

## Scoring — DittoBench
**Composite = `0.5 · tool_mean + 0.5 · memory_mean`**, then multiplied by **three bounded integrity factors** (tool-efficiency, canary/injection-resistance, paraphrase-consistency). Latency is measured but **not scored**; a case that exceeds its timeout scores **zero**.

- **Tool accuracy** = `0.4 · name-F1 + 0.4 · arg-F1 + 0.2 · trajectory` (call order + extra-call discipline). The validator observes *actual* tool execution through the tool endpoint.
- **Memory recall** = retrieval recall over seeded facts, graded per `answer_kind` (value, number, list, ordered list, duration, reversal, decline), with **distractor zeroing** so decoys can't be gamed.
- **Scoring is deterministic** — a pure function of `(dataset, transcript)`, reproducible by anyone from the public `dittobench-datagen` module.

### Anti-cheat (this is the core of the design)
- **Fresh procedural dataset every eval** — every submit rotates the seed, so "no two evaluations match and a memorized lookup table cannot score." Memorization is useless; only a genuinely correct harness scores.
- **Frozen inference model** — the validator locks chat to **Qwen3-32B in a TEE** (Trusted Execution Environment); local practice uses `gpt-oss-20b`. Model identity is frozen in code + the platform-issued ticket, so **you compete on the harness, not the model**.
- **Reproduce-under-transform audits** — a fraction of cases are rephrased/semantically shifted to catch surface-form hardcoding.
- **Originality checks** — byte match, normalized source, and semantic code embeddings flag copying.

### Emissions — king-of-the-hill
- **Only the top 5 earn:** `65% / 14% / 10% / 7% / 4%` to the champion and the next four distinct miners; **everyone else earns nothing.**
- A challenger must beat the incumbent's composite by a **0.007-point hysteresis** to dethrone it (prevents noisy flip-flopping).
- **No eligible miners → 100% of miner emission is burned.**

## Hardware / device
**8 GB RAM is sufficient. No GPU required** (unless you bundle your own local LLM — which is capped by the 20 MB tarball anyway). The reference stack (Ollama embeddings + ONNX reranker + SQLite) runs on **CPU**. This is a **low-hardware subnet** — well suited to a modest VPS.

## Tech stack (reference harness)
- **Rust** core (`ditto-harness` crate, pinned as a dependency by the starter kit).
- **Embedded Turso / SQLite** with native vector search (brute-force F32, 768-dim per user).
- **Embeddings:** Ollama `embeddinggemma` (768-dim).
- **Reranker:** TinyBERT-L2 **ONNX** cross-encoder.
- **Model clients:** `rig-core` (Ollama, OpenRouter, vLLM, Chutes).
- **Ranking pipeline:** "Composite V2" — 7 retrieval signals fused by an **MLP weight predictor**, then optional **cross-encoder rerank via Reciprocal Rank Fusion (RRF)**.
- **Scored chat model:** `gpt-oss-20b` (platform relay) / Qwen3-32B in TEE on the validator side.

## Third-party dependencies
- **Docker** (rootless build) — required for both practice and submission.
- **Ollama** — local embeddings (`embeddinggemma`) for practice.
- **OpenRouter API key** — *optional, local practice only* (NOT used in scored runs; the platform relays the locked model).
- **Bittensor wallet** + the `ditto` CLI (from `ditto-subnet`).

## How to win
Because the **model is frozen and latency isn't scored**, the entire game is three tunable levers (all in the starter kit):

1. **Retrieval quality (memory half of the score):** tune the **MLP fusion weights** (`fixtures/models/mlp-weights.bin`), swap/improve the **cross-encoder ONNX** reranker, tune **RRF params** (`k`, `ceWeight`), add a **lexical/hybrid index** for canary cases, and make sure you handle *every* LongMemEval answer kind (value/number/list/ordered/duration/reversal/decline).
2. **Tool-calling (tool half of the score):** maximize tool **name-F1** + **arg-F1**, keep the **trajectory** tight (no redundant/extra calls), and **abstain** correctly when no tool applies.
3. **System prompt:** a strong tool-use policy + abstention rules.

Plus: **pass the integrity multipliers** (don't leak canaries, stay consistent across paraphrases, be tool-efficient) and **submit genuinely original code** (semantic-embedding copy detection). **Practice offline for free** before paying to submit:

```bash
# in dittobench-starter-kit
cargo build
ollama serve & ollama pull embeddinggemma
cargo run -- seed-user                 # load bundled LongMemEval seed user
cargo run -- mem-eval --k 10           # retrieval recall only (no LLM needed)
cargo run -- evaluate                  # fixed reproducible case set
cargo run -- practice --n 20           # rotating random dataset (anti-overfit)
cargo run -- playground                # interactive agent chat UI
cargo run -- serve --port 8080         # run the harness server
cargo run -- submit                    # package dittobench-submission.tgz

# then, via the ditto-subnet CLI (registered hotkey, ~0.04 TAO fee):
ditto upload --path dittobench-submission.tgz --name <name> --coldkey <ck> --hotkey <hk>
```

## Key repositories
| Repo | Lang | What it is |
|---|---|---|
| **`dittobench-starter-kit`** | Rust | **Start here** — baseline miner harness, offline practice runner, scorer, submit flow |
| `ditto-harness` | Rust | the portable agent + memory harness (vector retrieval + learned ranking); pinned dep of the kit |
| `dittobench-api` | Go | off-chain **practice API** — fresh-per-request datasets, harness runner, scoring |
| `dittobench-datagen` | Go | deterministic dataset + grading logic (public, reproducible) |
| `ditto-subnet` | Python | core subnet + the `ditto` CLI (upload/submit/status) |
| `ditto-platform` | Python | API server, validators, benchmarking, dashboard |
| `ditto-screener` | Python | platform-operated screening worker |

`PROTOCOL.md` in the starter kit is the authoritative `RunRequest`/`RunResponse` shape.

## Verdict
**A great fit for a modest VPS (CPU-only, 8 GB RAM) and a strong engineering game** — no model training, no GPU, no data-sourcing costs; you win purely on **retrieval + tool-calling + prompt** craft, and you can iterate for free offline before paying the small submit fee. **But it's steeply winner-take-most:** only the **top 5** earn (champion takes 65%), and you must beat the incumbent by a hysteresis margin to take the throne. If the field is thin (reports suggest very few active miners), that's an opening — but expect the reward to concentrate hard on #1.

---
*Sources: [subnetalpha.ai/subnet/ditto](https://subnetalpha.ai/subnet/ditto/), [heyditto.ai/docs](https://heyditto.ai/docs/), and the [ditto-assistant GitHub org](https://github.com/orgs/ditto-assistant/repositories) (dittobench-starter-kit, ditto-harness, dittobench-api, ditto-subnet READMEs). Figures (fees, 20 MB cap, 65/14/10/7/4 split, 0.007 hysteresis, Qwen3-32B TEE) are from repo READMEs via automated fetch — verify against the live repos before committing TAO.*
