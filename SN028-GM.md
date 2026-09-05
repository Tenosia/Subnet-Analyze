# gm — Subnet 28 (SN28)

**Confidential LLM-API inference marketplace, paid on real revenue share — not model/attack quality.** Repos: `/home/vps-project/Bittensor/gm-miner` (`taostat/gm-miner`, Rust, `gmcli` CLI + miner container image) + `/home/vps-project/Bittensor/gm-validator` (`taostat/gm-validator`, Python, weight-setter only) · netuid **28** mainnet (482 testnet).

> **Archetype: cloud-hosted TEE reseller, revenue-proportional emissions.** This is unlike every other subnet in this series. A miner doesn't train a model, run inference locally, or attack anything — they deploy a TEE-attested proxy (on Phala Cloud, a *paid third-party cloud*, not their own hardware) that forwards real buyer traffic to real LLM providers (Anthropic/OpenAI/Google/etc.) using the miner's own API keys, at a small discount off retail. Emissions are then a direct, formulaic function of **actual USD revenue processed** that epoch — there's no LLM-judge grading, no ML benchmark, no adversarial verification. The validator does not even independently verify correctness; it trusts a centrally-published, already-computed cost ledger.
>
> ⚠️ **Accuracy note: the third-party listing is describing a retired version of this subnet.** `subnetalpha.ai` says "validators score responses using accuracy metrics (RMSE/MAE)" — that's leftover from GM's stated origin as "an S&P 500 forecasting oracle" before it pivoted to an LLM gateway. The current `gm-validator` code has no RMSE/MAE anywhere; scoring is pure `consumed_usd / pool_usd`. Don't plan around the RMSE/MAE description.

## Goal
Give buyers "private, drop-in access to frontier AI models" — point an existing OpenAI/Anthropic/Gemini SDK at gm's gateway, change only the base URL and API key, and get identical behavior, but routed through a network of independently-operated, TEE-attested (Intel TDX) proxies so that "neither operators nor host machines see buyer content or miners' upstream keys" (`gm-miner/README.md`). The subnet's economic engine is literally an API reseller marketplace: miners supply upstream provider capacity at a discount off retail, buyers get privacy guarantees plus (presumably) a lower price than going direct, and TAO emissions are the incentive to keep enough diverse, reliable, discounted capacity online.

## What a miner does
Entirely orchestrated by the `gmcli` Rust CLI (`gmcli init` runs all of this, detecting/skipping completed steps):
1. **Register a Bittensor hotkey** on netuid 28 (`gmcli register-hotkey`, either bring-your-own ss58 or assisted via `btcli`) — `gmcli` never signs an on-chain extrinsic itself.
2. **Log in** to the gm registry via Taostats device-code OAuth (`gmcli login`).
3. **Bring your own provider API keys** — Anthropic, OpenAI, Google, Chutes, Z.ai, Moonshot, DeepInfra, KubeTEE, or Bedrock/Azure OpenAI/Microsoft Foundry behind the Anthropic/OpenAI routes (`gmcli set-api-keys`). These are encrypted client-side into the CVM's environment — gm's own infrastructure never sees them.
4. **Deploy to Phala Cloud** (`gmcli deploy`) — this is the part with no local-hardware equivalent in any other subnet analyzed here: the actual workload (an Envoy data-plane proxy + a Rust attestation daemon, `attestd`) runs inside a Phala Cloud **Confidential VM (CVM)**, a paid third-party TEE cloud service, not the operator's own machine. `deploy` builds/verifies the image hash against the registry's approved versions and registers the worker in one step.
5. **Declare products and prices** (`gmcli declare-products --discount-pct N`) — for each model you're willing to serve, you set a discount off retail (0–99.90%); you keep `(100 − discount)%` of what the buyer pays per token, across a 10-dimension price vector (input, output, prompt-cache read/write at 5m/1h, audio in/out, cache storage, long-context in/out). Undeclared/withdrawn offers don't route traffic to you.
6. **Get selected by the gateway's routing logic** — `gmcli pricing` shows your rank against the field on whatever scalar the gateway actually routes on; a **sourcing route** (`gmcli sources`) lets you serve an existing buyer-facing product more cheaply through a different upstream (e.g. DeepInfra serving `zai/glm-5.2`) even though it's not in your own declared catalog.
7. **Real buyer traffic gets proxied through your worker**, and your earned revenue for that traffic (in nano-dollars) is what determines your weight next epoch — see Scoring below.

## Scoring / evaluation
Fully code-grounded from `gm-validator/validator/src/gm_validator/{scoring.py,alpha_economics.py}`:

- **The validator does not score anything itself.** A separate, gm-operated **epoch-finalizer** service is "the single source of truth" for per-request cost derivation, publishing `aggregated.jsonl` (per-`(miner, product)` rows with `earnings_ndollars`/`surcharge_ndollars`) and `epoch_summary.json` (alpha price + emissions snapshot, both chain-read) to a **public-read S3 bucket** (`gm-mainnet`) each epoch. The validator mirrors these artifacts and explicitly does **not** re-derive cost or re-verify hashes/signatures — it only converts the published numbers into a weight vector. This is a materially higher-trust design than SN26 (Perturb, which has real cryptographic/statistical re-verification) — correctness here rests entirely on the finalizer being honest and bug-free, not on independent validator checking.
- **Per-miner score** = sum of `earnings_ndollars + surcharge_ndollars` across every product served that epoch — i.e., real dollar revenue you generated for buyers, nothing else.
- **Cap-and-burn weight formula** (`alpha_economics.py::compute_epoch_weights`): `pool_usd = emissions_alpha × 0.41 (MINER_EMISSION_PCT) × alpha_price_usd`, then `weight_i = consumed_usd_i / pool_usd` for each miner. The miner pool is sized at a fixed **41%** of the epoch's alpha emission (in USD terms) — real revenue is your share of that fixed pool, not of total emissions directly.
  - **Under-subscribed** (total miner revenue < pool): the shortfall routes to the **subnet-owner UID** as burn (`SUBNET_OWNER_UID = 3` on mainnet — notably *not* UID 0, unlike SN121/SN26).
  - **Over-subscribed** (total miner revenue > pool): weights renormalize proportionally down so the vector still sums to exactly `MAX_WEIGHT` (65535) — meaning if the subnet's real transaction volume grows large, your payout per dollar of revenue shrinks rather than the reward pool expanding; you're sharing a fixed pie once demand exceeds it.
  - **Floor + water-filling**: any miner with strictly positive revenue is floored to at least 1 u16 unit (so a tiny earner isn't truncated to zero), funded from burn dust; if flooring pushes the sum over budget, the surplus is reclaimed from the *heaviest* miners via a proportional "water-filling" trim so no smaller miner ever ends up worse off than a larger one. All of this runs in exact integer/`Decimal` arithmetic — no floats until the final weight cast.
- **Epoch length**: `BLOCKS_PER_EPOCH = 361` (≈ one Bittensor tempo, roughly ~72 minutes at 12s/block).
- **No quality/accuracy scoring exists in the current code** — a well-behaving miner earns purely by successfully routing real, paid traffic. Reliability matters only insofar as it affects whether the gateway keeps routing to you and whether requests complete successfully (hence count as `earnings_ndollars`), not via any explicit accuracy metric.

## Hardware / device
**Unlike every other subnet in this series, there is no local GPU/CPU/RAM sizing requirement to publish** — neither repo has a `min_compute.yml`-equivalent, and for good reason: the actual workload doesn't run on the operator's own machine.
- **Your own machine** only needs to run `gmcli` (a small Rust CLI binary — install via a shell script, `~/.cargo/bin`) to configure, deploy, and monitor. This is laptop-tier.
- **The real compute cost is a cloud bill, not hardware you own**: a **funded Phala Cloud account** (`cloud.phala.network`) is required — `gmcli deploy` provisions and pays for an Intel TDX Confidential VM there. Budget for Phala Cloud CVM costs, not for GPUs/servers.
- **Software prerequisites**: `phala` npm CLI (`npm i -g phala`) for the underlying Phala Cloud deploy calls, and (only for the assisted hotkey-registration/earnings-lookup flows) `btcli`.
- This makes SN28 the lowest local-hardware-barrier subnet analyzed here — even lower than the CPU-only ones (Tag101/Leadpoet/Sundae Bar), since you're not running the workload locally at all, only orchestrating a remote deployment and holding your own upstream provider API keys.

## Third-party / dependencies
- **Phala Cloud** — the TEE hosting provider; a paid, funded account is mandatory. This is the subnet's single biggest infrastructure dependency and a real centralization point: if Phala Cloud has an outage or policy change, every miner is affected simultaneously.
- **LLM upstream providers** (bring-your-own keys, at least one required): Anthropic, OpenAI, Google, Chutes, Z.ai, Moonshot, DeepInfra, KubeTEE, plus AWS Bedrock / Azure OpenAI / Microsoft Foundry as alternate transports for the Anthropic/OpenAI routes. DeepInfra and KubeTEE are "sourcing" upstreams — they don't appear as their own buyer-facing products, they let you serve an *existing* product (e.g. `zai/glm-5.2`) more cheaply.
- **Taostats** — OAuth login/identity provider for the gm registry (`gmcli login`), and the org (`taostat`) that publishes both repos.
- **S3-compatible object storage** (OVH, `s3.gra.io.cloud.ovh.net` on mainnet) — where the gm-operated finalizer publishes the epoch artifacts the validator reads; public-read on mainnet, no credentials needed validator-side.
- **`btcli`** — needed only for the assisted hotkey-registration flow and `gmcli earnings`; not needed at all if you register elsewhere and pass `--hotkey-ss58` directly.
- **Docker + `docker compose` v2** — how the validator itself runs (detached, `restart: unless-stopped`, survives SSH disconnects/reboots).

## How to win
1. **Have real, reliable upstream API capacity, not a clever algorithm.** There's no model or attack to optimize — you earn by successfully serving real paid traffic through your own provider keys. Uptime and correctly-configured keys directly gate whether you earn at all.
2. **Price competitively but sustainably** — `--discount-pct` is a direct trade: a bigger discount likely wins more routed traffic (per `gmcli pricing`'s rank-against-the-field framing) but shrinks your per-request margin; `0` = full retail margin, up to `99.90` = razor-thin margin to guarantee non-zero revenue.
3. **Cover multiple providers/products** — more declared offers means more chances to be the selected route for a given buyer request; `gmcli sources` surfaces cheaper-upstream routes you may be able to serve that you're not currently offering.
4. **Watch the fixed-pool dynamic** — since the miner pool is a fixed 41% of epoch alpha (in USD terms), growth in total subnet transaction volume dilutes everyone's payout-per-dollar once demand exceeds the pool; there's no way to "out-earn" the pool ceiling collectively, only to capture a larger share of it.
5. **Get the TEE attestation right — it's a hard gate, not a formality.** `attestd`'s Azure owner-capture verification (if using Foundry/Azure upstreams) and the RA-TLS certificate minting are fail-closed boot gates; a misconfigured Foundry resource (the Application Insights connection Azure attaches by default) will restart-loop your miner indefinitely until fixed (`docs/foundry-setup.md`). Run `gmcli doctor` before every deploy — it's the documented first diagnostic step.
6. **Redundancy via multiple workers** — `gmcli worker add` attaches additional Phala CVMs under the same hotkey for more serving capacity/resilience, distinct from registering a second hotkey.

## Key files
- `gm-miner/README.md` + `gm-miner/CLAUDE.md` — extraordinarily detailed operator + architecture docs; the CLAUDE.md in particular documents dozens of subtle design decisions (money-formatting precision, table-width invariants, the declare/confirm race) worth reading if you're actually going to operate this.
- `gm-miner/docs/foundry-setup.md`, `docs/multi-key-slots.md`, `docs/sourcing.md` — the three operator docs most likely to save you a debugging session.
- `gm-miner/cli/src/commands/deploy.rs`, `wizard.rs` — the actual onboarding/deploy orchestration.
- `gm-miner/cli/src/pricing.rs` — the exact discount→absolute-price conversion (integer basis points, no floats).
- `gm-validator/README.md` + `gm-validator/CLAUDE.md` — validator setup and full architecture.
- `gm-validator/validator/src/gm_validator/alpha_economics.py` — the cap+burn weight formula (`compute_epoch_weights`, `normalize_weights`) — read this before assuming any specific payout percentage.
- `gm-validator/validator/src/gm_validator/scoring.py` — how `aggregated.jsonl` rows become per-miner USD totals.
- `gm-validator/.env.mainnet` — the actual live mainnet config values (pool %, burn UID, epoch length, S3 bucket).

## Run / submit commands
**Miner:**
```bash
npm i -g phala && phala auth login          # or set PHALA_API_KEY; needs a funded Phala Cloud account
curl --proto '=https' --tlsv1.2 -LsSf \
  https://github.com/taostat/gm-miner/releases/latest/download/gmcli-installer.sh | sh

gmcli init          # mainnet (netuid 28) — guided: hotkey -> login -> keys -> deploy -> declare products
# or step by step:
gmcli register-hotkey --hotkey-ss58 <ss58>          # or --wallet/--hotkey via btcli
gmcli login
gmcli set-api-keys --anthropic sk-ant-... --openai sk-...
gmcli doctor                                        # preflight before paying for a deploy
gmcli deploy
gmcli declare-products --discount-pct 5
gmcli status
gmcli earnings
```

**Validator:**
```bash
git clone https://github.com/taostat/gm-validator && cd gm-validator
btcli subnet register --netuid 28 --network finney --wallet.name <coldkey> --wallet.hotkey <hotkey>
cp .env.mainnet .env
# edit .env -> BITTENSOR_HOTKEY_SEED=<your hotkey mnemonic or 0x seed>
docker compose up -d --build
docker compose logs -f validator
```
No S3 credentials needed on mainnet (public-read bucket); everything else needed is already in the bundled `.env.mainnet`.

## Verdict
**The lowest local-hardware barrier and most economically transparent subnet in this series — but also the most centralized-by-design and the least "AI work" of any of them.** There's nothing to train, attack, or grade; winning is a business-operations problem (reliable uptime, competitive pricing, broad provider coverage, correct TEE attestation) layered on real commercial LLM-API reselling, with your TAO reward mechanically pinned to real USD revenue via a clean, well-tested (extensive `alpha_economics`/`scoring` unit tests) cap-and-burn formula. The tradeoff: the validator performs **no independent verification** of the underlying cost ledger at all — correctness rests entirely on a single gm-operated finalizer service being honest, which is a meaningfully different trust model than every ML-competition subnet in this series where the validator itself re-derives the score. If that finalizer is compromised or wrong, every validator on the subnet inherits the error identically. Good fit if you already run production LLM-API business and want a TAO-denominated revenue stream on top of it; a poor fit if you were expecting an ML/security research angle like Zeus, Affine, or Perturb.
