# Subnet 118 — Ditto 🧠

> **King-of-the-hill competition to build the best agent-memory harness.** Miners submit a Rust harness scored on tool-calling accuracy + memory recall against a fresh anti-cheat dataset with a frozen model. Feeds the live Ditto memory assistant (heyditto.ai).

- Docs: https://heyditto.ai/docs · Leaderboard: https://platform-api.heyditto.ai (a.k.a. dittobench.ai)
- Org: https://github.com/orgs/ditto-assistant/repositories (miner kit: `dittobench-starter-kit`)
- Market: https://subnetalpha.ai/subnet/ditto/
- *Snapshot as of 2026-07-31 — figures change.*

---

## 1. Purpose & goal
Consumer product: an AI assistant with long-term memory (760+ users, 37k+ conversations). Subnet: **crowdsource the best memory-retrieval + tool-calling engine** via competition (DittoBench). The **model and latency are frozen** → a pure algorithmic-skill race on retrieval + orchestration.

## 2. What miners do
Fork **`dittobench-starter-kit`** (Rust), improve three levers in `src/baseline.rs` — **memory retrieval, tool use, orchestration** — then submit a Docker tarball. The platform builds it, runs it **one-shot** (you host nothing / no port-forwarding), and probes 3 endpoints:

| Endpoint | Timeout |
|---|---|
| `GET /health` | 10 s |
| `POST /seed` | 5 min/wave |
| `POST /run` → `RunResponse` | 60 s/case |

```bash
cargo run -- seed-user      # load memory DB
cargo run -- evaluate       # fixed local score
cargo run -- practice --n 20# rotating (anti-overfit)
cargo run -- submit         # build tarball → ditto upload (~$5, hotkey on netuid 118)
```

## 3. Scoring & incentive mechanism
`composite = (0.5·tool + 0.5·memory) × efficiency × consistency × canary`
- **tool** = `0.4·name_F1 + 0.4·argument_F1 + 0.2·trajectory`
- **memory** = recall@k (LongMemEval) + abstention + timestamp/ordering + per-user isolation
- **Integrity multipliers scale the whole score:** canary (echo bait ×0.5, honest miss ×0.85), metamorphic-consistency, tool-efficiency. Transform audit re-asks reworded questions; **duplicate detection** rejects copies.
- Judge-free/deterministic, fresh dataset per run, median across validators.

## 4. Economics & status ⚠️ **LIVE and saturated**
King-of-the-hill: **champion ~65–90%** of emissions, next 4 split the rest, everyone else 0. **Dethrone requires >5% relative margin** — so a champion at ~0.97 is *mathematically unbeatable* (5% over 0.971 > 1.0). New strong miners only get **tail ranks (14/10/7%)**, which need **~0.93+**.
- Live leaderboard: top ~0.976, champion 0.971, median 0.729, 294 miners, 6 validators.
- **Biggest filters:** "Docker image build failed" rejects most submissions; duplicate detection holds near-copies. **Originality + a clean build are requirements, not options.**

## 5. How to win
1. **Memory retrieval quality** (the hard half). Key internal finding: the harness only injects the **top-2 memories in full** (`PROMPT_DETAILED_SEED_ROOT_COUNT=2`) — deeper hits are title-only, so answer values in memory #3+ never reach the model. Inject full-text top-K yourself.
2. Default composite weights (`cosine 0.65 / recency 0.20 / frequency 0.15`) **bury old/rare needles** — de-weight recency/frequency for recall.
3. **Canary lexical index** (exact-match for `VK-…` codes embeddings miss).
4. **Injection-resistance guard** (frozen model obeys embedded overrides otherwise).
5. **Be original** (duplicate detection) and **build clean** (Docker).

## 6. Hardware / device
**CPU only, 8 GB RAM, no GPU.** Ollama `embeddinggemma` (~1 GB) for embeddings.

## 7. Third-party services
- **Ollama** (required, local embeddings). **OpenRouter** (optional, local practice chat).
- Platform relay serves the **frozen model** on-chain (GPT-OSS-20B for v7 in code; docs cite Qwen3-32B for v6) — no key passes through your harness.

## 8. Tech stack
Rust; `ditto-harness` (Turso/SQLite vector store, `rig-core`, `napi-rs`); MLP weight predictor (217k params); cross-encoder rerank (TinyBERT-L2 ONNX). Org also: `ditto-platform` (Py/FastAPI), `ditto-subnet` (`ditto upload` CLI), `dittobench-api` (Go).

## 9. Honest take
The most "pure skill" subnet (frozen model + latency), best fit for Rust + information-retrieval engineers. **But it's live and saturated** — the crown is locked at ~0.97, tails need ~0.93+, and a 0.5x local harness is far off. Don't pay $5 to submit a weak harness. Either commit to pushing toward ~0.93 *with originality*, or treat it as a learning exercise and reassess ROI.
