# SN78 — UMI (ASL→English Translation) · *pre-activation*

> ⚠️ **Read this first.** Netuid 78 on finney is **still named `Vocence` on chain**.
> UMI hardcodes `NETUID = 78` and its README says *"SN78 is active on mainnet, but
> UMI translation weights are not."* The subnet's **owner coldkey has changed**
> since my 2026-08-19 Vocence analysis — consistent with the slot being
> transferred to the UMI team — but the rename, the mechanism, and the emissions
> have **not** switched over. Today SN78 pays a legacy mechanism, not UMI.
> This document therefore analyses **a protocol you cannot yet mine**.

| | |
|---|---|
| **netuid** | 78 (chain name **`Vocence`**, symbol `و`) |
| **Chain identity (unchanged)** | github `vocence-78/vocence` · url `vocence.ai` · discord `TWmfwJAtXG` · *"The voice layer for decentralized intelligence"* |
| **Owner hotkey** | `5Fk765B4CRBekwErwE5VxvveWhHztHSfsnsLt8cbDayDWsuk` — **UID 0** (unchanged) |
| **Owner coldkey** | `5GvYz1tBVJdVGtdeJFAcDbiRQcmKDcXicT98pxnKzU3cxVQ3` — **CHANGED** (was `5FnQCJW2Rm1BijNBUJzPetcpZx43RWutYiyaxA8j88fy9i9L` on 2026-08-19) |
| **UMI code** | https://github.com/Umi-BitSign/umi @ `576ddf7` (2026-09-01, "Add finalized SN78 observer API") · **Apache-2.0** · v0.1.0 |
| **Local checkout** | `/root/Bittensor/78/umi` |
| **UMI site** | https://www.umi.vision (live, Next.js) · `api.umi.vision` not yet resolving |
| **Registered at block** | 7,966,145 |
| **Live state (2026-09-03, block 8,983,511)** | tempo 360 |
| **Price** | 0.004646 TAO/و (**≈ $1.189**) · tao_in τ1,583.36 · alpha_in 340,809 · alpha_out 918,953 |
| **Price move** | **+122 %** vs my 2026-08-19 read of 0.002090 TAO |
| **UIDs** | 256 registered · **1 earning (UID 98, 100 %)** · 7 permits · 5 with dividends |
| **On-chain commitments** | **1** — and it is a legacy Vocence-format model claim |
| **Registration cost** | **0.0005 TAO** (~$0.13) |
| **Prior analysis** | [`SN78-VOCENCE-ANALYSIS.md`](SN078-VOCENCE-HISTORICAL.md) (2026-08-19) |

---

## 1. Goal of the subnet

UMI is building *"a trust-minimized translation layer at the boundary between
people and machines."* Its first — and deliberately only — mechanism is:

> **Miners translate raw American Sign Language video into English text.
> Validators score sealed, signed responses against references that were fixed
> before assignment.**

The scoping discipline is explicit: later tasks (other directions, other forms of
human–machine interaction) each require a separate protocol extension, and only
when the task has *"an independently useful output and a reproducible,
adversarially tested mechanism."*

### The six-stage cycle

1. A **challenge publisher** prepares consented ASL clips plus independent English
   references, **encrypts the references to a future drand Quicknet round**, and
   anchors a canonical pool manifest.
2. The candidate pool **closes before the selection seed exists**. Validators then
   use a *post-close* randomness round to pick batches and miners — so neither
   publishers nor validators can choose work after seeing the seed.
3. Validators anchor their exact assignment set, then send authenticated raw-video
   challenges. Miners return bounded, signed envelopes **timelocked to the
   ground-truth reveal round**.
4. After `response_close_round`, validators anchor the exact sealed envelope (or a
   failure marker) for **every** request. At `reveal_round` they open miner answers
   and references *together* and score with deterministic CER/WER. **Missing or
   invalid work stays in the denominator and scores zero.**
5. Each validator computes its own weights. Under the shadow policy it records the
   projected row **without submitting**.
6. Evidence publishes only after the validator's timelocked weights are revealed
   and applied on chain.

### Why the design is unusual

The ordering constraints are the whole point, and they are stated as rules:

- The emission-bearing score is a **pure function** of committed inputs, signed
  responses, revealed references, and a versioned policy hash.
- **Every validator computes its own scores.** *"Importing another validator's
  score database, ranking, or weight vector is a protocol violation."* Shared
  score APIs are explicitly ineligible as validator inputs.
- Ground truth is fixed **before** assignment and concealed until all responses
  close.
- **Miner answers stay timelock-sealed until reveal**, and validators anchor the
  sealed set *first* — so a validator cannot read answers and insert copies.
- **No trusted hardware** anywhere in the scoring trust boundary. No model-as-judge.
- Owner-controlled parameters **cannot regrade a committed batch**.

That last set is a direct answer to the failure modes I found in SN90 (operator
is the only evidence source) and SN47 (published code ≠ running code).

---

## 2. What you would do as a miner

**Today: nothing.** UMI weights are inactive and cannot be activated by the shipped
code (§4.1). What follows is the specified role.

You run **one HTTP service**. No chain writes from the miner process at all.

```bash
btcli subnets register --netuid 78 --network finney \
  --wallet umi --wallet-hotkey miner --mev-shield     # MEV Shield REQUIRED here

umi-miner \
  --wallet-name umi --hotkey miner \
  --translator your_package.model:translate \
  --validator-hotkey 5F... \
  --video-host challenges.example.org \
  --listen-host 0.0.0.0 --port 8091 \
  --nonce-db /var/lib/umi/nonces.sqlite3

btcli tx serve-axon --netuid 78 --ip YOUR_PUBLIC_IP --port 8091 \
  --network finney --wallet umi --wallet-hotkey miner --no-mev-shield
```

### The translation backend

```python
async def translate(video: bytes, request) -> str:
    return await your_model.translate_asl(video)
```

- **No placeholder fallback** — the miner refuses to start without a real callable.
- Async is required by default; a sync plugin needs `--allow-unsafe-sync-translator`
  and runs in a bounded thread pool. The docs are blunt: *"Python cannot terminate a
  hung worker thread, so such a backend must implement its own cancellation."*
- Inference concurrency defaults to **1**.
- Any fetch/decode/inference failure emits a **signed, timelocked error response
  that scores zero** — you are never silently absent.

### Network hardening (unusually strict)

Production video fetches resolve the allowlisted hostname **once per attempt**,
reject any non-public result, **pin the connection to one deterministic IP**, and
preserve the original Host authority and TLS SNI. Proxy env vars are ignored.
HTTPS/443 only unless you explicitly add `--video-port`.

The default nonce store is in-memory; `--nonce-db` gives a transactional SQLite
store for one host. **A multi-host deployment needs an external atomic replay store
that this repository does not ship** — stated plainly.

---

## 3. Scoring logic

### 3.1 Deterministic exact scoring

`src/umi/scoring.py` computes WER and CER in **exact `Fraction` arithmetic** — no
floats anywhere in the scoring path. Every input that could change the answer is
fingerprinted:

```python
def scoring_environment() -> dict[str, str]:
    return {
        "schema": "umi-component-scoring-environment/1",
        "python_implementation": ..., "python_version": ...,
        "unicode_data_version": unicodedata.unidata_version,
        "regex_distribution_version": version("regex"),
        "bittensor_distribution_version": version("bittensor"),
        "scoring_source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
    }
```

Replay checks the recorded Python, Unicode, regex and scorer versions **before**
recomputing. Normalization is traced step by step (original → NFKC → lowercase →
normalized → tokens → graphemes) and every step is recorded.

That is the most rigorous scoring-determinism story of any subnet I have analysed —
stricter than SN103's (which compares outcomes because SVD is not bitwise
reproducible) and stricter than SN47's (which needs a canonical-token rule to
tolerate GPU non-determinism). UMI simply has no floating point to disagree about.

### 3.2 Strata and accuracy

```python
STRATUM_WEIGHTS = {
    "fingerspelling":   Fraction(3, 20),   # 15 %
    "short_utterance":  Fraction(7, 20),   # 35 %
    "continuous":       Fraction(1, 2),    # 50 %
}
```

The stratum label is **deliberately visible** in the request — *"the task type is
not a secret, the content is."*

### 3.3 Utility

```python
def utility_score(accuracy, quality_floor):
    margin = max(0, clamp_unit(accuracy) - clamp_unit(quality_floor))
    return clamp_unit(margin * margin)
```

```
U_i = max(0, A_i − 0.10)²
```

Weights are submitted **proportional to `U_i`**, with the chain's canonical
normalization and quantization. **Uniform fallback weights are forbidden.** If the
count of positive utilities falls below the live `MinAllowedWeights`, a validator
**must skip** the update and raise a health alert.

### 3.4 ⚠️ The quality floor may not be reachable

The whitepaper says so itself, twice:

> *"Do models clear the `0.10` floor? **Not yet demonstrated** under UMI's exact
> normalization, reference, stratum, assignment-failure, and rolling-score rules.
> The value is an initial calibration candidate, not a reported model result."*

> *"At publication, no protocol-comparable distribution has yet demonstrated that
> current models clear `0.10`."*

Raw-video ASL→English translation at ≥10 % weighted accuracy under exact WER/CER
with no partial credit is a genuinely hard bar. **Whether any miner can score above
zero is an open empirical question the subnet has not yet answered.**

### 3.5 Rolling state

| Parameter | Value |
|---|---|
| Window stride | **360 blocks** (~72 min) |
| Emission-bearing clips per batch | 12 |
| Batches selected per window | 2, from **distinct publisher control groups** |
| Miner panel per validator per window | up to **32** |
| Rolling score window | **4 valid batches** |
| Score max age | **4 windows** |
| Minimum assigned clips | 12; ≥2 per stratum |
| Canaries | 10 % per batch (2 zero-weight at launch), CER/WER hit threshold 0.50 |
| Max clip | **15 s, 1280×720, 30 fps, 16 MiB** |
| Max hypothesis | 4 KiB / 128 tokens / 512 graphemes |
| Response window | 60 s |
| Semantic / pose / latency weight | **0** |

Score state is keyed by the miner's **chain-reported hotkey root** — *"a UID change
cannot reset history."*

### 3.6 Emission split

There is no UMI-specific split. §4.6 describes the stock Bittensor arrangement:
~18 % owner cut, remainder divided between miner incentive and validator-side
allocation, with a variable root-staker share. **Owner revenue is explicitly not
earmarked for challenge data** — the owner *may* fund the founding publisher group,
*"that does not create a protocol entitlement for any publisher."*

Publishers **receive no subnet emission** and bear their own production and review
cost. That is a real, unfunded cost centre in the design.

---

## 4. Live competition landscape

### 4.1 UMI is not running — and the code enforces that

```python
translation_weights_active: Literal[False]
```

This is a **type-level** guarantee: the shipped schema cannot express `True`. Not a
config default — the type. Activation requires a *new policy hash* with
`translation_weights_active: true` plus a published activation block.

The README's own list of what is missing is long and unusually candid:

- no active scoring policy can be constructed;
- the shadow runner has **no finalized chain collector, no storage-proof verifier,
  no real response timelocks, no ground-truth decryption, no weight submission**;
- resource accounting exists as primitives but is **not wired** through the HTTP stages;
- nonempty publisher-fault strikes are **disabled**;
- shadow rolling state **is not a persistent multi-window state machine**;
- source-conditioned monitoring is **specified but not wired in**;
- no general live incident classifier, submission-pause state, or resume workflow;
- **FFmpeg runs as a child process with no repository-enforced RSS limit** — you must
  supply an OS/container memory limit yourself;
- *"the external publisher, miner-utility, metric-validity, challenge-supply,
  economics, and soak gates in the whitepaper have not passed."*

And: *"`component_test_no_weight` and `shadow_rehearsal_no_weight` are local
engineering results. Neither is `calibration_no_weight`, protocol conformance, or
activation evidence."*

### 4.2 What SN78 actually pays today

```
 uid  incentive     emission        stake    divid  vperm
  98  1.000000      147.601        3099.6  0.00000  True    ← 100 % of the miner pool
   0  0.000000      104.267     1105185.0  0.70640  True    ← owner
 200  0.000000       36.495      388208.5  0.24724  True
```

`E[98] = 147.601 α/tempo = 0.41 × 360` — the entire miner pool.

**UID 98's axon is `0.0.0.0:0`.** It serves nothing. It holds 3,099.6 stake and a
validator permit.

Weight matrix — 6 of 9 setters concentrate on it:

| Setter | Stake | Weight |
|---|---|---|
| UID 0 (owner) | 1,105,185 | **100 % → UID 98** |
| UID 200 | 388,209 | **100 % → UID 98** |
| UID 198 | 31,258 | **100 % → UID 98** |
| UID 210 | 27,932 | **100 % → UID 98** |
| UID 211 | 13,931 | **100 % → UID 98** |
| UID 187 | 0 | **100 % → UID 98** |
| UID 110 | 148,783 | 100 % → UID 0 |
| UID 199 | 3 | 100 % → UID 0 |
| UID 217 | 0 | 100 % → UID 197 |

**Exactly one on-chain commitment exists**, and it is a legacy Vocence-shaped model
claim, not a UMI artifact:

```json
UID 206 → {"model_name": "CornAI0124/sn78-s65",
           "model_revision": "b8738ad9c2a76395775b0178045f28fc751bb024", ...}
```

So the subnet is paying a mechanism that is neither UMI nor visibly the Vocence
mechanism I documented in August — one non-serving UID, by validator consensus.

### 4.3 Ownership changed hands

| | 2026-08-19 | 2026-09-03 |
|---|---|---|
| Owner hotkey | `5Fk765B4CRBekw…` | `5Fk765B4CRBekw…` (same) |
| **Owner coldkey** | `5FnQCJW2Rm1BijNBUJzPetcpZx43RWutYiyaxA8j88fy9i9L` | **`5GvYz1tBVJdVGtdeJFAcDbiRQcmKDcXicT98pxnKzU3cxVQ3`** |
| Chain name | Vocence | Vocence (unchanged) |
| Price | 0.002090 TAO | **0.004646 TAO (+122 %)** |

A coldkey change with the hotkey retained is the signature of a **subnet slot
transfer**. UMI hardcoding `NETUID = 78` and shipping an "SN78 observer API" is
consistent with UMI being the new owner. **I could not confirm the buyer from chain
data alone** — the identity record still points at Vocence, so this is inference,
not proof.

### 4.4 Repo quality — the best of the six analysed

| | |
|---|---|
| Whitepaper | **2,683-line** protocol README + LaTeX source + compiled PDF |
| Tests | **30 files, 251 test functions** |
| CI | ruff check + ruff format + pytest on Python **3.10 / 3.12 / 3.14** |
| Source | ~13,920 lines across 24 modules |
| Licence | **Apache-2.0** |
| Extras | `roadmap/bitsign-mvp/` with design + spec + pilot plan in LaTeX; `docs/DASHBOARD_API.md` |

The adversarially-tested offline primitives listed include canonical policy hashing,
runtime and imported-module pins, bounded media decoding, strict portable timelock
parsing, publisher pool certificates, post-close selection, three pre-reveal anchor
sets, copy-bound authentication evidence, canaries, spent-state replay, rolling
eligibility, exact weight projection, and deterministic audit-bundle replay.

The whitepaper also credits its influences by name — Score Vision, Apex,
OpenRoboto, Chutes audit, Data Universe — which is rare and makes the design
lineage checkable.

---

## 5. Miner economics

Subnet emits **1.000 α/block = 7,200 α/day**; 18 % owner cut, 41 % miners, 41 %
validator dividends → **miner pool = 2,952 α/day**.

At α = 0.004646 TAO and TAO ≈ $256 → **α ≈ $1.189**:

### Today (legacy mechanism)

| Recipient | Share | α/day | TAO/day | USD/day | USD/mo |
|---|---|---|---|---|---|
| **UID 98** (axon `0.0.0.0:0`) | **100 %** | **2,952** | **13.71** | **~$3,511** | **~$105,300** |
| Owner UID 0 (18 % cut + 70.6 % dividends) | — | 3,381 | 15.71 | **~$4,022** | ~$120,700 |
| Everyone else | 0 % | 0 | 0 | **$0** | $0 |

**Owner captures 47.0 % of total emission.**

### Under UMI, if activated

Weights are proportional to `U_i = max(0, A_i − 0.10)²`, with a panel of up to 32
miners per validator per window. Nothing is reserved, nothing is burned by the
mechanism, and the squared curve concentrates reward hard toward the top.

Two structural cautions:

- **If nobody clears 0.10, every `U_i` is zero.** Validators must then skip the
  weight update entirely (uniform fallback is forbidden), and three consecutive
  such windows is a declared incident.
- **Publishers earn nothing.** Challenge production and human reference review are
  paid by the publishers themselves. At 2 batches × 12 clips per 72-minute window
  that is ~480 consented, human-referenced ASL clips per day, single-use for
  benchmark eligibility. That supply cost is the subnet's real bottleneck, and the
  whitepaper requires a **90-day challenge-supply runway** before activation.

### Costs

| Item | Cost |
|---|---|
| Registration | **0.0005 TAO ≈ $0.13** (cheapest of the six analysed) |
| Registration constraint | **MEV Shield required** for the coldkey-signed registration |
| GPU | Not specified in the repo — but an ASL video→text model realistically needs **24–80 GB VRAM** |
| FFmpeg/FFprobe | Required for policy construction, shadow rehearsal, media inspection, tests |
| Public IP + port | Required (`serve-axon`); miner is a public HTTP service |
| Memory discipline | You must impose an OS/container RSS limit — the repo does not |
| Model | **This is the entire cost.** Nobody ships an ASL translator that clears 0.10 |

---

## 6. How to become a winner

**You cannot earn from UMI today.** `translation_weights_active` is `Literal[False]`
and the activation gates are unpassed. Everything below is preparation.

### Priority 1 — Confirm the ownership and rename before investing.

The chain still says Vocence. Ask UMI directly: are you the owner of netuid 78, and
when does the identity record, the mechanism, and the emission switch to UMI? Until
the chain identity says UMI, **any effort here is an option on a transition that has
not happened.** Their GitHub is public and the whitepaper lists contacts.

### Priority 2 — Understand that the real problem is the model, not the protocol.

Unlike every other subnet in this series, the mechanism is not where you compete.
It is fully specified, deterministic, and published. The competition is a single
hard ML question:

> **Can you translate raw 15-second ASL video to English at ≥10 % weighted accuracy
> under exact WER/CER with no partial credit?**

Nobody has demonstrated this under UMI's rules. Public ASL translation research is
roughly at that frontier and the protocol's normalization is unforgiving.

Concretely, weight your effort by the strata: **continuous signing is 50 %**,
short utterance 35 %, fingerspelling only 15 %. Fingerspelling is the easiest
sub-task and the least valuable — do not over-invest there.

### Priority 3 — Build against the component test *now*.

This is the highest-value action available today, and it is free:

```bash
umi-demo --output component-runs/demo
umi-validator replay --bundle component-runs/demo/bundle
```

Runs in under 20 s with dev hotkeys, in-process transport, fixture video and a
deterministic translator. Then wire your real model in via
`--translator your_package.model:translate` and run `umi-validator prepare` /
`run-once` / `replay` against your own clips. **You can measure your exact protocol
accuracy offline, with no chain and no registration**, before anyone else can.

### Priority 4 — Register early and cheaply, but know what it buys.

0.0005 TAO ≈ $0.13. Registration is per-hotkey and one-time. Holding a UID through
the transition costs almost nothing and may matter if activation brings a
registration rush. Use `--mev-shield` — the pinned client requires it.

### Priority 5 — Engineer for the failure modes, not just accuracy.

The gates that will actually eliminate people:

- **Missing work stays in the denominator and scores zero.** A 60-second response
  window with concurrency 1 means a slow model is a zero, not a delay.
- Max 2 request transmissions and 2 response bodies per assignment; 2 video fetch
  attempts per actor/video/window. No retries beyond that.
- 34 MiB wire cap per assignment; 64 KiB request and response bodies.
- Canaries at 10 % per batch with a 0.50 CER/WER hit threshold.
- You must supply your own container memory limit around FFmpeg.
- Multi-host serving needs a replay store the repo does not ship — **run one host
  per serving hotkey** until you build one.

### Priority 6 — Watch the activation gates, not the roadmap.

Activation requires, at minimum: a 30-day soak (`minimum_soak_duration_seconds`
2,592,000) at ≥ **0.95 valid-window rate** over ≥30 scheduled windows; **≥4
independently administered validators** each publishing a `umi-validator-economics/1`
report showing ≥ **1.25×** direct-cost coverage; **≥ 2 × M_gate miners sustaining
positive utility** across a full ten-tempo gate; a 90-day challenge-supply runway;
publisher collateral locked on chain; and an `activation_equivalence_digest` that
the activated policy must reproduce byte-for-byte.

That is a *lot* of unpassed gates. The honest read is that activation is **months
away at best**, and the miner-utility gate may not be passable with current models.

### The path

1. Ask UMI to confirm ownership of 78 and the activation timeline.
2. `pip install -e '.[dev]'`, install FFmpeg, run `umi-demo` and the test suite today.
3. Build or fine-tune an ASL→English model and measure it with
   `umi-validator run-once` on your own clips. **This number is the whole game.**
4. Register a hotkey (~$0.13) to hold a UID.
5. Re-evaluate only when (a) the chain identity says UMI, (b) a shadow accuracy
   distribution is published showing miners above 0.10, and (c) the soak has begun.

---

## 7. Rules you must keep

| Rule | Consequence if broken |
|---|---|
| Miner must expose a real async translator callable | Process refuses to start — no placeholder fallback |
| Respond within the 60 s response window | Scored **zero**; stays in the denominator |
| Response envelope timelocked to `reveal_round` | Non-conforming envelope is a failure marker |
| ≤ 2 request transmissions, ≤ 2 response bodies per assignment | Further attempts refused |
| ≤ 2 video fetch attempts per actor/video/window | Fetch failure → signed zero-score error |
| ≤ 64 KiB request/response body, ≤ 16 KiB headers, ≤ 34 MiB wire per assignment | Rejected |
| Hypothesis ≤ 4 KiB / 128 tokens / 512 graphemes | Rejected |
| Video-host allowlist; HTTPS 443 unless `--video-port` | Fetch refused; proxy env vars ignored |
| Register with `--mev-shield` | Pinned client rejects the intent |
| One serving hotkey per nonce database | Replay protection breaks across hosts |
| Impose your own FFmpeg memory limit | Unbounded child RSS — repo does not enforce it |
| Validators: compute your own scores | *"Importing another validator's score database, ranking, or weight vector is a protocol violation"* |
| Validators: never submit uniform fallback weights | Forbidden; skip the update and alert instead |
| Validators: no UMI weight call while `translation_weights_active: false` | Protocol violation |

---

## 8. Device / hardware conditions

### Miner

| | |
|---|---|
| Python | **3.10 – 3.14** |
| Required binaries | **FFmpeg + FFprobe** |
| Runtime pin | `bittensor==11.1.0` (SDK + wallet + btcli in one package) |
| Transport | bittensor v11 **HTTP** model — no Axon/Dendrite/Synapse classes |
| Network | **Public IP + open port** (`serve-axon`), outbound to Quicknet and the video host |
| GPU | **Not specified by the repo** — but the task is video→text translation, so realistically **24–80 GB VRAM** |
| Media | Clips ≤ 15 s, ≤ 1280×720, 30 fps, ≤ 16 MiB |
| Concurrency | Defaults to **1**; raise with `--max-inference-concurrency` |
| Memory | **You must run inside an OS/container memory limit** — FFmpeg child RSS is unbounded |
| State | `--nonce-db` SQLite per host; multi-host needs an external store you build |

### Validator

| | |
|---|---|
| GPU | **None for scoring** — WER/CER is exact integer/Fraction arithmetic |
| Required | FFmpeg/FFprobe, outbound to drand Quicknet, chain access |
| Bandwidth | Up to **40 GiB per validator per window** (`maximum_validator_window_wire_bytes`) |
| Storage | Audit bundles ≤ 384 MiB each excluding raw video |
| Economics | Must publish a `umi-validator-economics/1` report; **≥1.25× cost coverage** required for activation |

### Observer (public API)

```bash
umi-observer --listen-host 127.0.0.1 --port 8092 --trusted-host api.umi.vision
```

Read-only, always-on host. *"The process loads no wallet and contains no signing or
transaction path."*

> **Against your BEAM box (2 cores / 3.7 GB):** it can run the **observer** and, at a
> stretch, a **validator** (no GPU needed for scoring — though 40 GiB/window of wire
> traffic is a real constraint on a small VPS). It **cannot** host a competitive
> miner: that needs a GPU large enough for an ASL video model plus a public IP.

---

## 9. Third-party conditions

| Dependency | Role | Failure mode |
|---|---|---|
| **drand Quicknet** | Timelock encryption for ground truth *and* miner responses; post-close selection randomness | **Load-bearing.** Both `umi-demo` and replay need outbound access to fetch round signatures. A Quicknet outage stalls reveal. |
| **FFmpeg / FFprobe** | Bounded media decoding; the **policy-pinned decoder's** RGB24 output defines the frame digest | Consensus-critical — the decoder's content hash is pinned in policy |
| **`bittensor==11.1.0`** | Chain, wallet, btcli, HTTP transport | Hard pin. ⚠️ Your `/root/beam/.venv` has **10.5.0** — UMI needs its own venv |
| **Challenge publishers** | Consented ASL clips + ≥3 human English references per clip | **The real bottleneck.** Publishers earn no emission and bear all cost. At launch: exactly 3 active publisher hotkeys and control groups |
| **MEV Shield** | Required for the coldkey-signed registration intent | Registration refused without it |
| **`api.umi.vision`** | Observer API for `umi.vision` dashboard | Not yet resolving; the Vercel route is a same-origin proxy, not the collector |
| **finney** | Registration, anchors, timelocked commit-reveal weights (version 4) | Weight reveal period = 1 subnet epoch, verified against live state |
| **`regex`, Unicode data** | Grapheme segmentation for CER | **Version-pinned in the scoring environment** — a version bump changes scores and is detected at replay |

Notably **absent**: no Hugging Face dependency for the mechanism, no operator-run
scoring API, no TEE, no closed-source engine. The trust surface is genuinely small.

---

## 10. Risks

1. **UMI does not run on SN78 today, and the code guarantees it cannot.**
   `translation_weights_active: Literal[False]` is type-level. Everything in this
   document describes a specification, not a live market.

2. **The chain still says Vocence.** The identity record, github link, URL and
   discord all point at the previous project. Only the owner *coldkey* changed. If
   the transfer falls through, this analysis describes a protocol with no subnet.

3. **The quality floor may be unreachable.** UMI's own words: no protocol-comparable
   distribution has demonstrated that current models clear 0.10. If none does,
   every `U_i` is zero, no weights can be submitted, and the mechanism stalls by
   design. **This is the single largest risk and it is an ML risk, not a design one.**

4. **A non-serving UID takes 100 % of miner emission right now.** UID 98's axon is
   `0.0.0.0:0`. Six of nine weight-setters, including the owner and the largest
   external validator, concentrate on it. Whatever mechanism is producing that
   consensus is not in any public repository I can find.

5. **Owner captures 47 % of emission** — 18 % cut plus 70.6 % of validator dividends.

6. **Publishers are an unfunded cost centre.** ~480 consented, human-referenced,
   single-use ASL clips per day, with zero emission to the people producing them.
   The founding control group bears it. If publisher supply fails, the subnet has
   no challenges. A 90-day runway is required before activation for exactly this
   reason.

7. **The founding publisher is not independent.** Stated outright: *"the founding
   publisher control group may prepare every calibration reference… Locks,
   canaries, and audit bundles make behavior more attributable; they do not make
   that source independent."*

8. **Activation gates are numerous and unpassed.** External publisher, miner-utility,
   metric-validity, challenge-supply, economics and soak gates all fail today.
   Realistically months away, with no guarantee any of them pass.

9. **Large amounts of specified-but-unwired machinery.** No finalized chain
   collector, no storage-proof verifier, no real response timelocks in the shadow
   runner, no ground-truth decryption, no weight submission, no persistent rolling
   state, no live incident classifier. The gap between the whitepaper and the
   executable is wide and the README says so.

10. **Unbounded FFmpeg child RSS.** *"any process that invokes media inspection must
    run inside an OS or container memory limit."* A miner that ignores this is one
    malicious clip away from OOM.

11. **No multi-host replay store.** Single-host serving only until you build one.

12. **drand Quicknet is a hard external dependency** for both timelock directions
    and for post-close selection. No fallback is specified.

13. **Validator economics are unproven.** The whitepaper is explicit that conformance
    does not establish positive return, and requires ≥4 validators to *demonstrate*
    1.25× cost coverage before activation. That gate could simply fail.

14. **Alpha is up 122 % in two weeks** on a subnet whose stated product does not yet
    run. Whatever is driving that price is not UMI translation revenue.

---

## 11. Documentation defects found

Remarkably few. This is the most internally consistent codebase in the series.

| Observation | Where | Note |
|---|---|---|
| Chain identity still Vocence | `SubnetIdentitiesV3(78)` | github/url/discord/description all point at the prior project. Not a UMI repo defect — but it means an outsider reading the chain finds the wrong protocol |
| `api.umi.vision` does not resolve | README §"Run the public observer API" | The observer is documented as the collector and the Vercel route as a proxy; the API host is not yet up |
| Legacy commitment format still on chain | UID 206 | `{"model_name": ..., "model_revision": ...}` — a Vocence-era claim, inert under UMI |
| Whitepaper §2.1 table row is orphaned | `whitepaper/README.md:117` | `## 2. Launch profile` opens a table whose header renders before §2.1 — cosmetic |

Everything I checked in `scoring.py`, `policy.py` and the whitepaper's §15
parameter table **agreed exactly** — strata weights 15/35/50, quality floor 1/10,
utility exponent 2, window stride 360, 12 clips, 2 batches, rolling 4, score max age
4, soak 30 windows at 0.95. The README's status section matches the code's
`Literal[False]`. That level of doc/code agreement is what SN47 and SN90 lacked.

---

## 12. Verdict

### Against the subnets analysed in this series

| | **SN78 UMI** | **SN58 Greevils** | **SN47 Feval** | **SN103 Capcomp** | **SN90 KubeTEE** |
|---|---|---|---|---|---|
| Task | ASL video → English | Hyperliquid trading | LoRA eval | LoRA composition | Confidential compute |
| **Live?** | **No — type-level disabled** | Yes | Yes | Yes | Yes |
| Entry cost | **0.0005 TAO ≈ $0.13** | 0.10 TAO + $25k capital | 0.05 TAO ≈ $12.80 | 1 TAO ≈ $256 | 0.0005 TAO + $1.5M–4M |
| Miner hardware | GPU + public IP | None (human lane) | One 24–48 GB GPU | One 32–48 GB GPU | 8-node TDX cluster |
| Validator GPU | **None** | None | 32 GB | 4× 32 GB | 4× 32 GB |
| Miners earning | **0 (from UMI)** | 1 of 256 | 0 | 7 of 25 | 1 of 95 |
| Owner capture | 47.0 % | 41.5 % | 100 % of miner pool | 76.6 % | 67.7 % |
| Scoring determinism | **Exact Fractions, env-fingerprinted** | Exact, from HL data | Canonical-token rule | Re-derivable to 5 dp | Label matching |
| Doc/code agreement | **Exact** | Exact (2 stale docstrings) | **Contradictory** | Exact | Prose overstates code |
| Tests | **251 across 30 files, CI on 3 Pythons** | Substantial | **None** | Adversarial suite | 35 tests |
| Whitepaper | **2,683 lines + LaTeX + PDF** | 300-line incentive spec | 56-line README | Extensive | Extensive |
| Blocking risk | **Task may be impossible at 0.10** | Two chain anomalies | Repo ≠ live network | Noise > dethrone margin | Can't participate |

### All ten subnets, one snapshot

Every figure in this table was **re-read live from finney on 2026-09-03** (block
8,984,103, TAO ≈ $256) so the rows are directly comparable to each other. The
per-document economics sections above use the α price at each document's own
analysis date and will differ.

| Subnet | Task | Miner deliverable | Miner GPU | Entry cost | α (USD) | Earning / UIDs | Top earner $/day | Owner capture | The catch |
|---|---|---|---|---|---|---|---|---|---|
| **SN47 Feval** | Verifiable LoRA eval | Adapter + published rollouts | 24–48 GB | $12.80 | $0.72 | **1 / 129** | $2,139 ← **owner** | **68.8 %** | Published repo ≠ live network; owner takes the whole miner pool via a `{0: 1.0}` fallback |
| **SN58 Greevils** | TEE algo-trading on Hyperliquid | Agent in a TDX VM, or a plain HL account | none (VM ~$145/mo) | $25.60 + ~$25k capital | $2.29 | 1 / 256 | $6,747 | 41.3 % | Sole earner holds no on-chain commitment; zero `gva1` approvals exist |
| **SN76 Phylax** | AI supply-chain security attestation | One Python file (`agent_main`) | **none** | $25.60 + ~$21/attempt | $0.60 | **21 / 256** | $364 | 40.5 % | Your track's rounds have to actually be scheduled |
| **SN78 Vocence → UMI** | ASL→English translation *(pre-activation)* | HTTP translator service | yes, 24–80 GB | $0.13 | $1.11 | 1 / 256 | $3,290 | 46.9 % | UMI weights type-level disabled; chain still says Vocence; the 0.10 floor is unproven |
| **SN79 MVTRX** | Agent-based market simulation | Always-on trading bot | **none** | $25.41 | $1.68 | **210 / 256** | $444 | 59.0 % | A genuine quant-trading skill gate; latency is scored |
| **SN80 OpenRoboto** | Fine-tune π0.5 VLA robotics | HF checkpoint | yes, A100-class | $0.13 + ~$19/attempt | $3.72 | 2 / 256 | $8,891 ← **owner** | 56.1 % | 81 % of the miner pool sits on the operator's UID 0 |
| **SN82 Compelle** | Adversarial LLM debate | A prompt, committed on chain | **none** | $0.13 | $0.88 | 1 / **64** | $2,599 | **28.8 %** | Incumbent-protected winner-take-all on 64 slots |
| **SN90 KubeTEE** | DePIN confidential compute | A TDX GPU cluster | 8-node TDX datacenter | $0.13 + **$1.5M–4M** | $8.10 | 2 / 97 | $18,715 ← **owner** | 66.6 % | Onboarding is operator-gated — you cannot join |
| **SN92 MicroTensor** | Certified inference systems | ONNX/GGUF artifact + 128-byte pointer | training only (RTX 3090+) | $25.60 | $0.86 | **9 / 256** | $646 | **39.2 %** *(0 % of the miner pool)* | Docs name the wrong paying track — `code` pays 0, `extract` pays all |
| **SN103 Capcomp** | LoRA composition | One JSON merge recipe | 32–48 GB | **$256.00** | $3.02 | **10 / 105** | $8,012 | 55.1 % | Dethrone margin sits ~24× below measurement noise |

**What the snapshot says.** Four of the ten have a functioning competitive field:
**SN79** (210 earners), **SN76** (21), **SN103** (10) and **SN92** (9). Five pay
exactly one UID, and on **SN47, SN80 and SN90** the single top earner *is* the
owner's own UID. Owner capture runs 28.8 – 68.8 %, and **SN92 is the only one
whose owner draws nothing at all from the miner pool** — its 39.2 % is the 18 %
protocol cut plus staked dividends, nothing else. Alpha prices moved materially
between the individual analyses and this snapshot (**SN78 +122 %** since August,
**SN90 −14 %** since its own writeup), so read every USD column as a same-day
comparison, not a forecast.

**Where a newcomer can actually compete today**, ranked: **SN79 MVTRX** (210
paying seats, $25 entry, no GPU, free testnet) → **SN92 MicroTensor** (9 paying
seats on a geometric curve where rank 8 still earns ~⅓ of rank 1, one consumer
GPU for training only, public API that hands you the whole frontier) → **SN76
Phylax** (21 seats, no GPU, local corpus to iterate against) → **SN103 Capcomp**
(10 seats, contested, but $256 entry and a noise-dominated throne) → **SN82
Compelle** ($0.13, one seat, incumbent protected). The remaining five are either
operator-gated, pre-activation, or paying a single UID that is often the owner's.

### Assessment

**UMI is the most carefully specified subnet in this series and the only one that
is honest enough to refuse to turn itself on.**

The engineering is of a different standard. Exact `Fraction` scoring with a full
environment fingerprint — Python version, Unicode version, regex version, scorer
source hash — checked at replay before recomputation. Ground truth timelocked to a
future drand round. Miner responses *also* timelocked, with the sealed set anchored
before reveal so a validator cannot read and copy answers. Candidate pool closes
before the selection seed exists. Missing work stays in the denominator. Importing
another validator's scores is a stated protocol violation. Owner parameters cannot
regrade a committed batch. 251 tests, CI across three Python versions, Apache-2.0,
and a 2,683-line whitepaper that credits its influences by name.

Most striking is `translation_weights_active: Literal[False]` — the shipped type
*cannot represent* an active policy. Compare that with SN47, where the "burn"
constant silently pays the owner, or SN90, where "no attestation means no
emissions" is a substring match on a label. UMI's README enumerates its own
missing pieces across a dozen bullets and labels its passing tests *"local
engineering results… not activation evidence."*

**And none of that changes the fact that you cannot mine it.** SN78 pays 100 % of
its miner pool to a UID whose axon is `0.0.0.0:0`, by consensus of six validators
including the owner, under a mechanism that is in no public repository. The chain
identity still says Vocence. Alpha is up 122 % in two weeks on a product that does
not run.

**The deepest risk is not the transition — it is the task.** UMI states plainly
that no protocol-comparable distribution has shown a model clearing 0.10 accuracy
under its rules. Every other subnet here has a mechanism risk you can engineer
around. UMI has an ML risk it cannot design away: if raw-video ASL→English at
exact WER/CER is beyond current models, the protocol works perfectly and pays
nobody, forever. The design anticipates this — the floor is explicitly
"calibrated, not assumed," and a shadow distribution must be published before
activation — which is the right call and also an admission that the core question
is open.

### Recommended path

1. **Do not treat this as a mining opportunity yet.** There is nothing to mine. Any
   capital deployed today is a bet on a transition the chain has not recorded.
2. **Confirm the ownership and rename with UMI directly.** Until the chain identity
   reads UMI, the slot's status is inference.
3. **Register a hotkey anyway — $0.13.** Cheapest option in the series, and it holds
   a UID through any activation rush.
4. **Do the one thing that has real option value today: measure the task.**
   `pip install -e '.[dev]'`, install FFmpeg, run `umi-demo`, then wire a real ASL
   model into `umi-validator run-once` on your own clips. **Your accuracy number
   against the 0.10 floor tells you whether this subnet is investable at all** —
   and you can learn it offline, for free, before the field does.
5. **Weight model effort toward continuous signing (50 %)**, not fingerspelling (15 %).
6. **Track three signals**, in order: the chain identity changing to UMI; a published
   shadow accuracy distribution showing miners above 0.10; and `soak_start_window_index`
   being fixed with the soak actually beginning. Only the second one tells you the
   subnet can ever pay.
7. **Meanwhile, if you want SN78 exposure, understand what you are buying.** Today's
   emission is a legacy mechanism paying one non-serving UID, and the owner takes
   47 %. That is the asset, not UMI.

---

## 13. Sources

**Code**
- https://github.com/Umi-BitSign/umi @ `576ddf7` (2026-09-01) — Apache-2.0, v0.1.0
- Local: `/root/Bittensor/78/umi`
- `README.md` (308 lines), `whitepaper/README.md` (2,683 lines),
  `whitepaper/UMI-Whitepaper.pdf`, `whitepaper/main.tex`, `whitepaper/specification.tex`
- `src/umi/scoring.py`, `policy.py`, `shadow.py`, `chain_evidence.py`, `miner.py`,
  `validator.py`, `observer.py`, `resources.py`, `drand.py`, `media.py`
- `docs/DASHBOARD_API.md`, `roadmap/bitsign-mvp/`, `.github/workflows/ci.yml`
- 30 test files / 251 test functions

**Chain** (finney, block 8,983,511)
- `Subtensor.subnet(78)`, `metagraph(78)`, `weights(78)`, `recycle(78)`
- `get_all_commitments(78)` — **1** commitment, legacy format
- `SubnetIdentitiesV3(78)` — still `Vocence`

**Endpoints probed**
- `https://umi.vision` → 308 → `https://www.umi.vision/` 200 (Next.js)
- `https://api.umi.vision/v1/network` — not resolving
- `https://www.umi.vision/api/v1/network` — 404

**Prior work**
- `/root/Bittensor/SN78-VOCENCE-ANALYSIS.md` (2026-08-19) — source of the earlier
  owner coldkey and price used in the comparison

**Price reference**
- TAO ≈ $256 → α ≈ $1.189 at 0.004646 TAO/α
