# Subnet 114 — SOMA 🧩

> **Decentralized compression + MCP infrastructure — but the LIVE competition is a token-efficient SWE coding-agent contest.** Miners make an AI coding agent resolve real GitHub issues while spending far fewer tokens than a baseline.

- Site: https://thesoma.ai · Repo: https://github.com/DendriteHQ/SOMA
- Market: https://subnetalpha.ai/subnet/soma/ · Team: **Dendrite** (~50 eng)
- *Snapshot as of 2026-07-31 — figures change.*

---

## ⚠️ Marketing vs. reality
The website sells **context/CoT compression + a marketplace of MCP servers**. But the repo's incentive code (as of mid-2026) scores a **software-engineering agent on SWE-bench**. The compression DNA is applied *to a coding agent*. **Build for the SWE competition, not "compression" or "MCP servers."**

## 1. Purpose & goal
Long-term: be the compression layer that cuts AI token spend (~50%) and a production MCP-server marketplace. Live competition: **make a coding agent (running a frozen DeepSeek V4 Pro) match/beat a baseline's issue-resolution rate at a fraction of the token cost.**

## 2. What miners do
Submit a **Python solution (`main()` entry point)** that plugs into a fixed agent harness. You may **only** add compression markers (`[[CMP]]`, `[[Omitted]]`, …) and loop-detection guards — **no semantic rewrites**, no obfuscated code. Effectively a **context/CoT compression + loop-guard module**.
```bash
cd miner && python3 miner/upload_miner_with_openrouter_key.py   # submit solution + OpenRouter key
```
Cycle (2 weeks): **submission window → screening/qualification → live competition**. One solution per hotkey per cycle.

## 3. Scoring & incentive mechanism
Three benchmarks: `swebench_verified` (**50%**), `swe_explorer_explore` (25%), `swe_explorer_edit` (25%). Scored on **resolve-rate vs baseline AND token compression** jointly:
- Token weighting: `T = 1.0·input + 0.1·cached_input + 3.0·output` → **output tokens are 3× costly; cached input near-free**.
- Compression ratio `r = clamp(ln(T_base/T_miner), −2, +2)`.
- Resolve gating: penalty if you solve `< floor(0.8×baseline)`; bonus if you solve **more** than baseline.
- **Layered tournament (L0/L1/L2, 7 elements):** top miner **wins each element's weight** (ties split); `INC = Σ won-weights / Σ all × (1 − burn)`. Winner-take-per-element → collapses to winner-take-most if one miner dominates all.

## 4. How to win
1. **Optimize the joint objective** — never drop below `0.8×baseline` resolves to save tokens.
2. **Attack output tokens first** (3× weight) — trim generated reasoning/tool chatter.
3. **Exploit caching** (0.1× weight) — push tokens into cached input.
4. **Kill loops** (low-risk token savings).
5. **Solve hard tasks** the baseline couldn't (hard-boost).
6. **Specialize** an element (e.g. `swe_explorer_explore`) if you can't be globally best (mind its quality gate).

## 5. Hardware / device
Light for miners — you develop/upload code; the platform runs eval. Published spec (validator): **4 CPU / 16 GB / 500 GB** (200 GB in one place). **No GPU** (inference via API).

## 6. Third-party services (you pay inference!)
- **OpenRouter** account — you submit your key; the platform runs your agent **on your key → you fund inference**.
- Model fixed: **DeepSeek V4 Pro** via the DeepSeek provider on OpenRouter. Enable the DeepSeek provider + both "train on request data" privacy settings.

## 7. Tech stack
Python/FastAPI (`mcp_platform`, routes for miner/validator/scoring/sandbox/incentive), `validator` (SWEbench + SWE Explorer evaluators, chain weight setter), `sandbox_service` (Docker execution, tiktoken), `gateway` (AWS SSM). SWE-bench Verified + proprietary SWE Explorer benchmark.

## 8. Economics & status
Alpha ~$3.13, mcap ~$1.23M (mid-2026); very active dev. **Pay-your-own-inference** model + a burn ratio + winner-take-most tournament → a builder's subnet, not passive yield. Model your OpenRouter spend vs expected alpha first.

## 9. Honest take
Purest "agent-engineering + token-efficiency" skill test. Moving target (already pivoted compression → SWE-bench; re-qualify every 2 weeks). Watch the repo `dev` branch + Discord. Best fit if you're strong at agent/context engineering and can absorb inference cost.
