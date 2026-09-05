# Leadpoet — Subnet 71 (SN71)

**AI B2B sales-lead generation ("AI sales intelligence, built on Bittensor").** Repo: `/home/vps-project/leadpoet` (`leadpoet/leadpoet`) · netuid **71** (finney).

> **Archetype: data / service pipeline** (CPU + APIs, on-demand). Miners produce **qualified sales leads** — decision-maker contacts at companies matching a client's Ideal Customer Profile (ICP), with verifiable intent evidence.
>
> **Architecture note:** the live logic runs in a hosted **AWS-Nitro TEE gateway** (`gateway/`) + `validator_models/`. The old `Leadpoet/validator/reward.py` and the `LeadRequest` axon synapse are **legacy/`[DEPRECATED]`** paths.

## Two contribution tracks
1. **Fulfillment** — compete on real client ICP requests by submitting enriched leads (the main earning loop).
2. **Research Lab** — direct compute + a hosted "auto-research loop" to improve a private AI sourcing model against a sealed benchmark (pays compute reimbursement + an improvement bounty).

## What a miner does (Fulfillment loop)
Entry point: **`neurons/miner.py`** (`main()`; startup menu: 1 Auto-Research / 2 Fulfillment / 3 Resume Credit-Blocked / 4 Submit API Source).

- Polls the gateway every 30s (`fulfillment_loop` → `_source_fulfillment_leads`). Each request carries an **ICP** dict + `num_leads`.
- Sources leads (`miner_models/Main_fulfillment_model/discovery.py`), then follows a **commit–reveal** protocol: hash each lead → `gateway_submit_fulfillment_commit` (commit window) → `gateway_reveal_fulfillment` (full data after window closes). This is a **gateway HTTP** flow, not the axon synapse.
- Per-request cap: you may commit `num_leads × 1.5` (`FULFILLMENT_MINER_SUBMISSION_MULTIPLIER`); only the top `num_leads` win.

**Lead schema you submit** (`FulfillmentLead`, `gateway/fulfillment/models.py`): `full_name`, `email?`, `linkedin_url`, `phone?`; `business`, `company_linkedin`, `company_website`, `employee_count`, HQ country/state/city, `industry`, `sub_industry`, `description` (≥30 chars, must match the real company); contact geo; `role`, `role_type`, `seniority`; **`intent_signals` (≥1 required)** + optional `attribute_evidence`. Intent `source` ∈ {linkedin, job_board, social_media, news, github, review_site, company_website, wikipedia, other}.

**On "auto-research lab":** it's real but **hosted on the TEE gateway**, not on your box. You only supply an OpenRouter key + a research direction + a small TAO loop-start fee (~$2). **No persistent crawler** in the fulfillment miner — it sources **on-demand per request** (reference model uses Perplexity `sonar-pro` + ScrapingDog + TrueList).

## Scoring / evaluation
Core scorer `gateway/fulfillment/scoring.py` — a **three-tier gate-then-score** pipeline:
- **Tier 1 — ICP-fit gate** (deterministic): industry, sub-industry, role, role_type, seniority, geo, employee-count range, exclusion list, in-batch duplicate company. Any mismatch → **0**.
- **Tier 1.5/1.7 — LLM gates**: semantic industry/region match, intent pre-check; rejects bare `linkedin.com/company/<slug>` intent URLs.
- **Tier 2 — data accuracy**: DNS/MX/DNSBL/domain-age checks; **email verification** (TrueList); **person verification** (LinkedIn role match via ScrapingDog/Apify); **company verification** + reputation; required-attribute checks (Perplexity Sonar).
- **Tier 3 — intent scoring**: per-signal LLM scoring, time-decay, **peak-weighted aggregation** (best signal dominates + diminishing breadth bonus, capped 60). Threshold `FULFILLMENT_MIN_INTENT_SCORE=5.0`; required buyer signals are a hard gate.

**Dedup / novelty (the key mechanism):** in-batch duplicate company → reject; duplicate intent **domain** → signal skipped; **structural similarity** (templated descriptions) → whole lead zeroed. Cross-cycle + cross-chain dedup (`lifecycle.py::_resolve_chain_topk`) means **a company can win only ONE slot** across all generations of a request chain — no reward for a company already won.

**Consensus + rewards:** multi-validator consensus is **v_trust × stake weighted** (`consensus.py`). Winners = top-K (K = `num_leads`) by consensus score, one per company; ties split. Economics (`gateway/fulfillment/config.py`): `Z_PERCENT=0.004` per winning lead **per epoch** for `L_EPOCHS=100` epochs (≈5-day runway; epoch ≈72 min) — one win keeps paying for days (de-reg protection).

## Hardware / device
- Only stated requirements are software: **Python 3.9/3.10**, a Bittensor wallet, `bittensor==10.5.0` + `bittensor-cli`. `torch`/GPU deps are commented out in `requirements.txt`.
- Heavy compute (TEE scoring, research-lab benchmarking) runs **gateway-side**. A fulfillment miner needs a **modest CPU box** with network + third-party API keys — **no GPU**.

## Third-party / API dependencies
- **Fulfillment miner:** `SCRAPINGDOG_API_KEY`, `OPENROUTER_KEY`, `TRUELIST_API_KEY` (Perplexity `sonar-pro` via OpenRouter); optional `APIFY_API_TOKEN`, `TRYFUNDABLE_API_KEY`.
- **Research-Lab miner:** OpenRouter API key + management key + TAO loop-start fee.
- **Validator** (for reference): Supabase, TrueList/ZeroBounce, ScrapingDog, OpenRouter, optional Companies House; free rep-score sources (Wayback, SEC EDGAR, GDELT, WHOIS/DNSBL). Infra: Supabase, Firestore, Arweave, AWS Nitro TEE.

## How to win
- **Exact ICP fit** — Tier 1 is a hard gate; any field mismatch = 0.
- **Verifiable accuracy** — real company (LinkedIn), real person whose LinkedIn role matches, deliverable email, accurate ≥30-char description matching the website.
- **Strong, recent, correctly-sourced intent** — one excellent verifiable signal beats many weak ones; declared `source` must match the URL category and the quoted snippet must actually appear on the page; satisfy every required buyer signal.
- **Company novelty** — target companies **not already held** in the request chain (duplicates never win twice).
- **Speed** — poll fast, commit within the ~72-min window; over-commit to `num_leads×1.5` to absorb validation flakiness.
- **Avoid anti-gaming trips:** templated descriptions (`structural_similarity_detected`→0), fabricated/zero-confidence signals, duplicate domains, bare-LinkedIn intent URLs, date-hiding to dodge decay. Full rubric in `model_evaluation_rules.md`.

## Key files
- `neurons/miner.py` — miner entry point (mode menu, commit-reveal loop, research-lab flows).
- `miner_models/Main_fulfillment_model/discovery.py` — reference sourcing model (Perplexity + ScrapingDog + TrueList) — **what you customize**.
- `gateway/fulfillment/models.py` — `FulfillmentLead` / `FulfillmentICP` schema (exactly what to submit).
- `gateway/fulfillment/scoring.py` — the validator scoring pipeline.
- `gateway/fulfillment/lifecycle.py` — winner selection + cross-cycle/cross-chain dedup (novelty).
- `gateway/fulfillment/config.py` — reward economics (`Z_PERCENT`, `L_EPOCHS`, thresholds).
- `model_evaluation_rules.md` — anti-gaming rubric.

## Run commands
```bash
git clone https://github.com/leadpoet/leadpoet.git && cd leadpoet
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt && pip install -e .
pip install "bittensor==10.5.0" "bittensor-cli>=1.0.0"
btcli wallet create

btcli subnet register --netuid 71 --subtensor.network finney \
  --wallet.name miner --wallet.hotkey default

export SCRAPINGDOG_API_KEY=... OPENROUTER_KEY=... TRUELIST_API_KEY=...
python neurons/miner.py --wallet_name miner --wallet_hotkey default \
  --netuid 71 --subtensor_network finney       # then choose mode 2 (Fulfillment)
```

## Verdict
**Medium difficulty, data-quality game.** No GPU, but you pay for real API calls (scraping + LLM + email verification) and win on **ICP-exact, verifiable, novel leads with strong intent**. Your edge is a better sourcing/enrichment pipeline than the reference model — and picking companies nobody else has claimed.

> ⚠️ *Accuracy caveat: the exact epoch→emission wiring (`_get_fulfillment_emission_share` in the 600 KB `neurons/validator.py`) was cited from config comments, not read line-by-line.*
