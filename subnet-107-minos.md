# Subnet 107 — Minos 🧬

> **Decentralized genomic variant-calling competition.** "The Foundational Layer of Genomics." Miners tune variant-caller hyperparameters to identify hidden mutations in synthetic genomes; accuracy is the only thing that matters.

- Site: https://theminos.ai · Docs: https://docs.theminos.ai/overview
- Repo: https://github.com/minos-protocol/minos_subnet
- Market: https://subnetalpha.ai/subnet/minos/
- *Snapshot as of 2026-07-31 — figures change.*

---

## 1. Purpose & goal
Sequencing a genome fell from ~$1M to <$200; the bottleneck is now *interpreting* the DNA. "Variant calling" = identifying where an individual's DNA differs from the reference. No single tool is best across all contexts, so Minos turns it into a permanent incentivized benchmark. Long-term: build the world's largest validated synthetic-genome dataset and a consensus meta-caller for clinical use.

## 2. What miners do
Every **72 minutes** the platform (via **HelixForge**) generates a challenge genome — a BAM file with **hidden synthetic mutations** + a private truth VCF. Each round a miner:
1. Downloads the mutated BAM (presigned URL).
2. Runs one caller — **GATK HaplotypeCaller**, **Google DeepVariant**, or **BCFtools** (FreeBayes deprecated 2026-05-09) — with **their own tuned hyperparameters**.
3. **Submits the hyperparameter config** (JSON). That config is the graded answer.

Test risk-free: `bash start-miner.sh --demo` (no wallet) / `--practice` (real chr20/21 samples).

## 3. Scoring & incentive mechanism
**AdvancedScorer** (per round, normalized 0–1):

| Component | Weight |
|---|---|
| Core F1 | **60%** |
| Completeness (recall) | 15% |
| FP-rate penalty | 15% |
| Quality (Ti/Tv, Het/Hom) | 10% |

Graded with **hap.py** vs the truth set. **Winner-take-most:** validators **burn 87%** of weight, the **top current-round miner gets 10%**, ranks **#2–#10 split 3%** (0.8 geometric decay). **Eligibility:** must score in **≥10 of the last 20 rounds**.

## 4. How to win
- **Floor:** DeepVariant, `model_type=WGS` (WES silently breaks WGS BAMs) — consistent high scores, minimal tuning.
- **Ceiling:** GATK — set **`pcr_indel_model=NONE`** (GIAB is PCR-free; highest-leverage change), tune `standard_min_confidence_threshold_for_calling` (20–40), `min_base_quality_score` (10–50).
- Fix **F1 first** (60%); slight precision bias beats reckless recall.
- **Protect eligibility** ruthlessly (NTP sync, PM2 supervision, no timeouts).
- **Prepare for Phase 2** (custom variant-calling code) — where real ML skill will dominate.

## 5. Hardware / device
| Role | CPU | RAM | Disk |
|---|---|---|---|
| Miner | ≥4 cores | 8–16 GB (16 for DeepVariant) | ≥60 GB |
| Validator | ≥8 cores | ≥32 GB | ≥100 GB |

**No GPU required** (CPU Docker images). Linux (Ubuntu 20.04+) preferred.

## 6. Third-party services
- Platform API `https://api.theminos.ai` (tasks, truth data, scoring)
- Storage: Cloudflare R2 (primary), AWS S3 (fallback), Hippius/SN75 (decentralized) — all via presigned URLs
- Docker images (pinned): GATK 4.5.0.0, DeepVariant 1.5.0, BCFtools 1.20, SAMtools 1.20, hap.py

## 7. Tech stack & setup
Python 3.10+, Docker 20.10+, Bittensor SDK, PM2 (optional).
```bash
git clone https://github.com/minos-protocol/minos_subnet && cd minos_subnet
bash install.sh
bash start-miner.sh --demo        # test, no TAO
bash pm2-miner.sh                 # go live (register hotkey on netuid 107 first)
```
`.env`: `NETUID=107`, `WALLET_NAME/HOTKEY`, `MINER_TEMPLATE=gatk|deepvariant|bcftools`, `PLATFORM_URL`, `STORAGE_PRIMARY_BACKEND`.

## 8. Economics & status
- **~87% burn** + near-winner-take-all → only ~top miner earns meaningfully.
- ~1 active miner / 1 of 64 slots filled at snapshot → **open champion seat**, but verify alpha price vs. registration + compute cost.
- Roadmap: Phase 1 hyperparameter tuning (active) → Phase 2 custom code → Phase 3 SVs/CNVs → Phase 4 consensus caller → Phase 5 clinical product.

## 9. Honest take
Genuinely differentiated (produces a real scientific artifact, not another LLM subnet). Low hardware barrier (no GPU). But harsh economics (87% burn, winner-take-most) mean it rewards a small number of expert operators, not passive miners. **Best path:** reliably-eligible GATK config tuned for PCR-free WGS, DeepVariant as a floor, and get ready for Phase 2.
