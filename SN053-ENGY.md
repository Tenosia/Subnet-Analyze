# Subnet 53 — Engy ⚡

> **Verified inference for frontier open models.** Permissionless GPU miners serve real LLM traffic through one OpenAI/Anthropic-compatible endpoint (`api.engy.ai`); every response carries a cryptographic **TOPLOC** proof that the *claimed* model actually ran. "The proof pins the math, not the machine." By **Hanlin AI** (founder Ning Ren, ex-Google AI).

- Site/API: https://engy.ai · Provider (miner keys): https://provider.engy.ai
- Repo: https://github.com/hanlinai/engy · Local: `/home/Project/engy`
- Market: https://subnetalpha.ai/subnet/engy/ · Company: https://hanlin.ai
- *Snapshot as of 2026-08-04 — figures change.*

---

## 1. Purpose & goal
When you buy LLM inference on someone else's GPU, how do you know they ran the real model and not a cheaper quantized/distilled knockoff? Engy answers with an **activation fingerprint (TOPLOC)** on every response, verified out-of-band by validators — **no TEEs / trusted hardware**. The product is **decentralized, verifiable inference-as-a-service**: buyers hit one endpoint with prepaid billing; permissionless GPU miners serve the tokens; validators verify a sample and set weights. Models: Qwen3.6-35B-A3B, GLM-5.2, Kimi K3. (Replaced Hanlin's earlier "Efficient Frontier" trading subnet.)

## 2. Players
| Role | Runs | Job |
|---|---|---|
| **Miner** | GPU + sglang + proof | Serves a committed model, attaches a TOPLOC proof to every response, posts collateral. **Dials out** to the gateway (no inbound port). |
| **Gateway** (`api.engy.ai`) | Entry/router/SLA | OpenAI/Anthropic API, auth, prepaid billing, capacity-aware load-balancing, proof capture. Zero data retention. |
| **Validator** | CPU-only, on-chain weights | Verifies the master-signed epoch result, submits weights (~every 120 blocks). |
| **Chain** | netuid 53 | Weights → emissions under Yuma consensus. |

## 3. What miners do
1. Put the **canonical checkpoint** on local disk (e.g. `Qwen/Qwen3.6-35B-A3B-FP8`).
2. Start an **sglang serve** with `--enable-return-hidden-states` (+ tool-call/reasoning parsers), with `miner/` on `PYTHONPATH`.
3. Run **`engy_miner.py`** — dials the gateway over websocket, tokenizes, calls sglang `/generate`, reads the per-token final hidden state, builds the **TOPLOC proof**, returns completion + proof. One process: connect → generate → prove → answer.
4. Declare **`MAX_INFLIGHT`** (concurrency, **min 8**), authenticate with a **miner key** from `provider.engy.ai`, post collateral.

```bash
pip install "sglang>=0.4.6" toploc transformers torch numpy requests websockets
# serve (ref: 4× RTX 4090, tp-size 4, context 262144, FP8)
PYTHONPATH=/path/to/engy/miner python -m sglang.launch_server \
  --model-path /data/models/Qwen/Qwen3.6-35B-A3B-FP8 --tp-size 4 \
  --enable-return-hidden-states --enable-cache-report --context-length 262144 ...
# miner
GW=wss://api.engy.ai/gw MINER_KEY=<key> MODEL=qwen3.6-35b-a3b MAX_INFLIGHT=<≥8> \
  python miner/engy_miner.py --checkpoint /data/models/Qwen/Qwen3.6-35B-A3B-FP8 \
  --serve-url http://127.0.0.1:8000
```

**Admission gate:** a new miner first serves **synthetic probe traffic** (no buyer, no weight). Must pass **(a)** serve correctly (≥99% acceptance, latency in SLA) and **(b)** TOPLOC proof matches the canonical checkpoint → becomes **active** (equal peer of the 1st-party cluster). Degrade → **pulled within ~1 min**, must re-prove.

## 4. The proof (TOPLOC)
Each checkpoint (arch + weights + quantization) is pinned as a 32-byte `model_root`. Every response carries a locality-sensitive **activation fingerprint** (async tee, ~0 GPU cost). A validator holding the canonical checkpoint re-runs the sampled prompt and compares top-k. Model spec `qwen3.6-35b-a3b`: `toploc_k=128`, `toploc_v=40` (mismatch threshold), `toploc_p=0.99`. Score = mean top-k mismatch / 128; a P99 threshold decides `cheat`.
- **Honest FP8** (4090 ~0.18, 5090 ~0.23) → **pass**; **INT4 cheat** claiming FP8 root ~0.55 → **caught**. Heterogeneous consumer GPUs are fine.
- A sampled **GEMM-recompute** audit is built but not yet the gate (rolling out for GLM-5.2 / Kimi K3). Today: **TOPLOC-only**.

## 5. Scoring & how to win
Weekly epochs, per **(miner, model)**, integer fixed-point.
```
score = floor( Σ tokens(r) × score_rate[model] / 1000 )   if every gate passes, else 0
```
- **Counted requests:** HTTP **2xx AND `cost_micro > 0`** (real *paid* traffic only → anti-wash-trading). Miner-attributable failures = **502 / 504**.
- **`score_rate[model]`** = blended µUSD/1k-tokens the team sets (capacity lever, discount-immune).
- **Gates** (fail any → 0 this epoch, clean next):

| Gate | Grain | Fails when |
|---|---|---|
| Acceptance | (miner, model) | 2xx < 99% |
| TTFT p99 | (miner, model) | > model `qual_ttft_p99_ms` |
| TPOT p99 | (miner, model) | > model `qual_tpot_p99_ms` |
| Cheat | miner | cheat verdicts > 1% |

Weight = share of Σ score onto 65535. **Burn:** no billed traffic → owner hotkey. Fresh key starts at 0.

**How to win — maximize served paid tokens:**
1. **Throughput/capacity** — routing is **equal round-robin** among eligible workers, so your share ≈ your capacity ÷ total eligible. More GPUs = more earnings.
2. **Set `MAX_INFLIGHT` right** = `--max-running-requests × dp-size` (under → underdriven; over → timeouts/abandoned).
3. **Meet the SLA hard** — ≥99% acceptance, low TTFT/TPOT p99 (fast GPUs, healthy serve).
4. **Serve honestly** (canonical FP8; TOPLOC catches quant-cheats).
5. **Uptime** — circuit breaker drops degraded miners in ~1 min.
6. **Cache locality** — prefix affinity rewards stable serves.

## 6. Device / hardware
| Role | GPU | Notes |
|---|---|---|
| **Miner** | **Required** | Ref: **4× RTX 4090 (24 GB)**, `Qwen3.6-35B-A3B-FP8`, tp-size 4, context 262144. Consumer GPUs fine (4090/5090 both pass); enough VRAM to fit FP8. Dials out — no inbound port. |
| **Validator** | **None (CPU-only)** | No GPU, no DB. Just a Bittensor wallet; verifies sr25519-signed epoch result, submits weights ~every 120 blocks. Docker + Watchtower auto-update. |

## 7. Third-party / dependencies
- **sglang ≥ 0.4.6** + `toploc, transformers, torch, numpy, requests, websockets`.
- **Miner key** from `provider.engy.ai` (gateway admission).
- **Model checkpoint** (pinned canonical weights, e.g. Hugging Face `Qwen/Qwen3.6-35B-A3B-FP8`, GLM-5.2).
- **Gateway** `wss://api.engy.ai/gw`; **Bittensor** wallet + collateral (netuid 53).
- **No external inference cost / API fee** — you *are* the service; buyers pay, you earn.

## 8. Economics & status
Alpha ~$2.62 (0.0136 TAO), mcap ~$13.9M, **256/256 slots full** (fully subscribed), emissions ~0.50 TAO/block, owner cut 18%. Reported APY (~1132%) is volatile — treat with heavy salt.

## 9. Honest take
Closest thing to a **real GPU-inference business** on Bittensor — same infra/ops family as Beam (SN105) but for LLM serving, not bandwidth. **Reward tracks real paid API demand routed to you**, so earnings depend on both your capacity/SLA *and* buyer volume (no demand → weight burns to owner). Barrier: real hardware (a multi-4090 rig ~$6–8k or rented GPUs) + a strict SLA (99%+ acceptance, latency p99). **Best fit: GPU/infra operators** who can run fast, reliable, honest inference. Copying is irrelevant (it's capacity, not a model); cheating is caught by TOPLOC. Validating is trivially cheap (CPU-only) if you just want exposure.
