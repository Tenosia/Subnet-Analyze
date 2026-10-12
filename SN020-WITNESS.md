# SN20 — Witness (Agentic Video Understanding)

| | |
|---|---|
| **netuid** | 20 (`Witness`, symbol `υ`) |
| **Chain description** | *"Decentralized models to understand video"* |
| **Tagline** | *"Understand video. Not just watch it."* |
| **Owner hotkey** | `5ED4s3B3syimeARcw2gEDZVErvQeLz26jd9XCk9KczqpwW2Q` — **holds UID 240** |
| **Owner coldkey** | `5CFVA7aPkGRYhYThumb9UQkPPZv7kzm2ieREHVjxecaYqi3u` |
| **Code** | https://github.com/witnessvision/witness_subnet — public, 57 files, real implementation |
| **Local checkout** | `/root/Bittensor/20/witness_subnet` (created today) |
| **Site** | https://witnessvision.io · contact `contact@witnessvision.io` · [Discord](https://discord.gg/P2Y93BRYyC) |
| **Registered at block** | **1,970,929** — one of the oldest slots in this folder |
| **Live state (2026-09-10)** | site banner: **"RESEARCH PREVIEW · RECORDED DEVELOPMENT TRACES · PUBLIC LAUNCH PENDING VALIDATION"** |
| **Price** | 0.002669 TAO/υ (**≈ $0.68**) · tao_in τ6,914 · alpha_in 2,590,074 · alpha_out 3,282,525 |
| **UIDs** | 256 registered · **1 with incentive (the owner)** · 11 permits · 10 with dividends |
| **On-chain commitments** | 1 |
| **Registration cost** | **0.000527 TAO (~$0.13)** |

> **The short version.** A genuinely well-built codebase for a hard and unusual
> problem — agents that *choose what to look at* in a video, under a metered
> observation budget, scored against private ground truth. The engineering is
> real: three frozen scorer versions, 11 test modules, a working local dry-run
> that needs no wallet or GPU. **But it is explicitly a research preview that
> has not publicly launched**, and on chain the owner's own UID takes 100 % of
> the miner pool.

---

## 1 · Goal — in plain terms

Most video benchmarks hand a model the whole video and ask a question. Witness
asks something harder and more realistic:

> *"An agent must connect events over time, recover dialogue and visible text,
> and answer questions using the evidence it observes. Witness makes those
> outputs explicit and **measures the observations used to produce them**."*

The agent doesn't get the video. It gets a **budget** and a set of tools, and it
must decide *which frames to fetch, which seconds of audio to listen to, and
whether to pull a transcript*. Every one of those calls is metered by the
validator. Then it must hand back a **structured reconstruction** of what
happened, which is scored against reference labels it never sees.

The site's phrase for it is the clearest summary: **"Understanding, with a
receipt."**

What makes this different from the usual video subnet is that **efficiency is
part of the score**. Two agents that reconstruct the scene equally well do not
tie — the one that looked at less wins.

---

## 2 · What you do as a miner

**You implement one method.** The repository ships a base miner that returns an
empty reconstruction; your job is to replace that with real inference.

```python
from witness.subnet.miner import WitnessMiner
from witness.subnet.protocol import WitnessTask

class MyMiner(WitnessMiner):
    async def reconstruct(self, task: WitnessTask) -> dict[str, Any]:
        response = await super().reconstruct(task)
        # 1. read task.task_spec — duration, fps, QA IDs/questions
        # 2. plan observations within task.budget and task.deadline_s
        # 3. query tools via task.tool_base_url and task.session_id
        # 4. run your own inference, fill the response from observed evidence
        # 5. return before the deadline
        return response
```

The repo is explicit that this is the *only* thing you should override:

> *"Do not override `forward()` just to add inference; keeping the inherited
> method preserves the base miner's concurrency and timeout handling."*

And that the model is entirely yours: *"No trained miner, model weights or
private evaluation data are distributed here."*

### The five observation tools

You get a **session** the validator created — you cannot make your own — and
five calls against it:

| Tool | What it costs you |
|---|---|
| `get_frame` / `get_frames` | **visual tokens** — 14×14-pixel patches: `ceil(w/14) × ceil(h/14) × frames` |
| `get_audio` | **audio seconds** requested |
| `get_transcript` / `search_transcript` | **transcript characters** returned |

Cost is measured by the validator, not reported by you:

> *"Validator cost is snapshotted from the server-owned store under its lock when
> the task closes… **Miner cost claims are never used**."*

### What you must return

A structured JSON reconstruction with seven fields:

| Field | Content |
|---|---|
| `events` | `{t, actor, action, object}` — action from a fixed 18-verb vocabulary |
| `dialogue` | `{speaker, start, end, text}` |
| `shots` | `{start, end}` — cut boundaries |
| `on_screen_text` | `{start, end, text}` |
| `audio_events` | `{t, kind}` — `beep` / `door_slam` / `alarm` |
| **`intentional_errors`** | `{t, type, ...}` — deliberately planted faults you must *catch* |
| `qa` | answers keyed by the task's question IDs |

That sixth field is the most interesting part of the design. The scene generator
plants deliberate faults and you are scored on **detecting** them:

```
continuity · repeated_shot · tint_change · foreign_shot
audio_visual_contradiction · misleading_subtitle
```

`misleading_subtitle` and `audio_visual_contradiction` are the sharp ones — they
require cross-checking what is *said* against what is *shown*. An agent that
only reads the transcript cannot find them.

Answers are normalised SQuAD-style (NFKC, casefold, articles stripped), and
actions accept ~40 synonyms (`walks in` → `enter`, `grabs` → `pick_up`), so you
are not penalised for phrasing.

---

## 3 · Scoring logic

### 3.1 Quality — a weighted blend across seven axes

From `witness/score_v18.py` (the current frozen scorer):

```python
WEIGHTS = {
    "events":             0.25,
    "dialogue":           0.20,
    "qa":                 0.20,
    "intentional_errors": 0.15,
    "shots":              0.10,
    "on_screen_text":     0.05,
    "audio_events":       0.05,
}
```

**Events, dialogue and QA are 65 % of quality.** Event timing tolerance tightens
with tier: **0.50 s / 0.375 s / 0.25 s** for tiers 1 / 2 / 3.

### 3.2 The eligibility gate — absolute *and* relative

```
quality >= max( tier_minimum, 0.35, 0.8 × best_quality_for_scene )
```

Tier minima are frozen at **0.70 / 0.65 / 0.60**, and the docs are explicit that
*"a relative gate cannot weaken them."*

That `0.8 × best` term is the one that bites: **you must be within 20 % of the
best miner on that scene**, whoever it is. Clearing the absolute floor is not
enough if someone else is far ahead.

### 3.3 The score — quality discounted by what you looked at

```
score = quality × efficiency_factor
efficiency_factor = max(0, 1 − 0.30 × total_cost / cost_ref)
```

`LAMBDA = 0.30`, so spending the full reference budget costs you **30 % of your
score**. Worked through:

| quality | cost / cost_ref | efficiency | **final score** |
|---|---|---|---|
| 0.95 | 1.0 (full budget) | 0.700 | **0.665** |
| 0.85 | 0.5 | 0.850 | **0.723** |
| **0.85** | **0.2** | **0.940** | **0.799** |
| 0.95 | 0.2 | 0.940 | **0.893** |

> **Read the middle two rows.** A miner at **0.85 quality using a fifth of the
> budget beats a miner at 0.95 quality using all of it** — 0.799 vs 0.665. That
> is the whole thesis of the subnet expressed as arithmetic: *cheap and good
> beats expensive and slightly better.*

But note the gate comes first. Cutting observation until quality drops below
`0.8 × best` scores **zero**, not a small number. The optimisation is
constrained, not free.

### 3.4 Anti-gaming

| Mechanism | Effect |
|---|---|
| **Duplicate collapse** | *"Identical canonical reconstruction hashes from multiple UIDs divide each matching score by the number of UIDs sharing it"* — copying splits the reward |
| **Validator-owned metering** | Cost comes from the server's locked store; miner claims are ignored entirely |
| **No self-scoring** | *"do not return a self-assigned score or substitute miner-side cost estimates"* |
| **Sessions are validator-created** | The public tool server **rejects `POST /session`** |
| **Degraded observer** | Responses from a degraded observation path *"receive no reward"* |
| **Non-responders** | Zero weight |

### 3.5 Weights

Scene scores are averaged, folded into an EMA, positive eligible scores
normalised, and **a configured burn share added to the burn UID**. If nobody has
a positive eligible score, *"the full vector goes to the valid burn UID."*

The docs are unusually careful about what submission proves:

> *"Finalization of a commitment does not prove weights are active after reveal;
> `weights_applied` remains unknown until separately verified on chain."*

---

## 4 · Live competition landscape

### 4.1 The subnet has not publicly launched

Three independent statements, all from the project itself:

**The site banner:**
> **RESEARCH PREVIEW · RECORDED DEVELOPMENT TRACES · PUBLIC LAUNCH PENDING VALIDATION**

(The dashboard is marked *"COMING SOON"*.)

**The README:**
> *"Research preview: independent benchmark validation and production reward
> validation remain unresolved. **The historical default scorer has known reward
> weaknesses.** Local tests and dry runs do not establish production readiness."*

**The miner guide:**
> *"Obtain the intended network, subnet UID and registration requirements **from
> the subnet operator**. CLI defaults are not confirmation of a public Witness
> deployment."*

The shipped `.env.example` reinforces this — it reads `WITNESS_NETUID=1`, a
placeholder, not 20.

### 4.2 The chain matches

| | |
|---|---|
| UIDs with incentive | **1** |
| That UID | **240 — verified identical to `owner_hotkey` and `owner_coldkey`** |
| Its incentive | **1.000000** |
| Weight setters | **1** (UID 79, stake 60,161) → 100 % to UID 240 |
| On-chain commitments | 1 |

Dividends are concentrated too: UID 240 holds **48.98 %** with 1.24M stake, then
UID 49 at 19.3 % and UID 144 at 16.7 %.

### 4.3 But the code is real

This is not a README-only project. The repository contains a working system:

| | |
|---|---|
| Modules | 57 files — scene generation, TTS, rendering, observation server, metering, three scorers, recomposition |
| **Frozen scorers** | `score_v16` / `score_v17` / **`score_v18`** (635 lines), each pinned by SHA256 so historical rounds re-score identically |
| Tests | **11 test modules** including one per scorer version |
| Local dry-run | Works with **no wallet, no GPU, no chain, no credentials** |

The scorer freezing is a good detail — v1.8 carries
`Frozen origin SHA256: 2183b183…` and states *"prior scoring versions remain
unchanged for reproducible historical reports."*

You can run the whole thing right now:

```bash
python3 -m venv .venv && .venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m witness.gen --seed 101 --tier 1 --out data/scenes/quickstart
.venv/bin/witness-validator --dry-run --once --allow-unlocked \
    --scenes 1 --scene data/scenes/quickstart --round-root rounds/quickstart
```

### 4.4 One caveat the project raises about its own benchmark

> *"The default transcript mode uses **historical label-derived hints**;
> independent evaluation requires audio-derived observations or no transcript."*

In plain terms: by default the transcript tool can leak information derived from
the labels, so scores obtained with it are not an independent measurement. Any
real benchmark run has to disable it or derive transcripts from audio. That the
team says so unprompted is a good sign; that it is still the default is a real
limitation.

---

## 5 · Economics

Subnet emits **7,200 α/day**; 18 % owner / 41 % miner / 41 % validator →
**miner pool = 2,952 α/day**.

At α = 0.002669 TAO and TAO ≈ $256 → **α ≈ $0.68**:

| | α/day | USD/day |
|---|---|---|
| Miner pool (face value) | 2,952 | **$2,017** |
| **UID 240 (owner) — 100 % of it** | **2,952** | **$2,017** (~$60,500/mo) |
| Every other UID | **0** | **$0** |
| **Owner total** (18 % cut + 100 % incentive + 49 % dividends) | **5,694** | **$3,891/day — 79.1 % of emission** |

### Costs to participate

| Item | Cost |
|---|---|
| Registration | **0.000527 TAO ≈ $0.13** |
| Runtime deps | Python 3.11+, **FFmpeg/ffprobe**, **eSpeak NG** — all free apt packages |
| Local development | **No GPU, no wallet, no chain** — the dry-run is genuinely free |
| Serving | Public IP + reachable axon port |
| **The real cost** | **A video-understanding model.** Nothing is shipped; you bring frame/audio inference and a tool-use policy |
| GPU | Not stated anywhere. Realistically required for competitive inference — but note **inference can be remote**, the protocol is provider-agnostic |

---

## 6 · How to become a winner

### Priority 1 — Confirm the subnet is actually open before investing

The miner guide tells you to *"obtain the intended network, subnet UID and
registration requirements from the subnet operator"* and warns that CLI defaults
are not confirmation of a deployment. The site says launch is pending. The chain
shows the owner taking everything.

Ask in [Discord](https://discord.gg/P2Y93BRYyC) or at `contact@witnessvision.io`:
**is SN20 accepting miners today, and what is the current scoring configuration?**
That is a one-sentence answer and it determines everything below.

### Priority 2 — Meanwhile, everything you need to build is free and local

This is the strongest thing about Witness for a prospective miner. You can
develop the *entire* competitive artifact with no registration, no wallet and no
GPU:

```bash
.venv/bin/python -m witness.gen --seed 101 --tier 1 --out data/scenes/dev
.venv/bin/witness-validator --dry-run --once --allow-unlocked ...
```

The scene generator, the observation server, the metering and **the exact frozen
scorer** are all in the repo. You can measure your own quality and efficiency
before anyone else sees you. Very few subnets in this folder hand you the grader.

### Priority 3 — Optimise the observation policy, not just the model

This is where the subnet is actually won. Quality is 65 % events + dialogue + QA,
but the *score* is `quality × (1 − 0.30 × cost/cost_ref)`. From §3.3, **0.85
quality at 20 % budget beats 0.95 quality at full budget.**

Concretely, the cost function tells you where to save:

```
visual_tokens = ceil(w/14) × ceil(h/14) × frames
```

Visual cost is **quadratic in resolution and linear in frame count**. Halving
the requested frame dimension cuts that frame's cost ~4×. So the levers are:

- **Fetch fewer frames, chosen well.** Shot boundaries and event timestamps are
  what you need; sampling uniformly is the naive strategy.
- **Fetch them smaller** where you only need coarse structure, larger only where
  you must read `on_screen_text`.
- **Use `search_transcript` rather than `get_transcript`** — you pay per
  character *returned*, so a targeted search is far cheaper than pulling the lot.
- **Budget audio deliberately** — you pay per second requested, and
  `audio_events` are only 5 % of quality. But you cannot catch
  `audio_visual_contradiction` without it, and that sits inside the 15 %
  `intentional_errors` bucket.

### Priority 4 — Do not starve quality below the relative gate

The gate is `max(tier_minimum, 0.35, 0.8 × best_quality_for_scene)`. Efficiency
is worthless if you fall under it — you score **zero**, not a reduced amount. The
right shape is: hit the gate reliably first, *then* cut cost.

Because the gate is relative to the best miner on that scene, in a contested
field the floor rises with the leader. Budget headroom accordingly.

### Priority 5 — Target `intentional_errors` — it is 15 % and structurally hard

Detecting planted faults is the second-largest single bucket after events, and
two of the six types (`audio_visual_contradiction`, `misleading_subtitle`)
require cross-modal checking. A transcript-only agent gets them all wrong. If
you build genuine audio↔visual comparison, that is 15 % of quality most
competitors will leave on the table.

### Priority 6 — Respect the mechanics that zero you out

- Use the **assigned `session_id`**; you cannot create sessions and must not try.
- **Never touch reference labels.** Stated as a prohibition.
- **Return before the deadline** — propagate cancellation, use non-blocking
  inference. The template returns empty on timeout, which scores nothing.
- **Do not submit a self-assigned score or your own cost estimate.**
- **Do not copy** — identical reconstruction hashes split the reward across every
  UID sharing them.

### The path

1. Ask the operator whether SN20 is open. **Wait for the answer.**
2. Regardless: clone the repo, `apt install ffmpeg espeak-ng`, run the dry-run.
   It costs nothing and needs no GPU.
3. Generate scenes across all three tiers; build `reconstruct()` in a separate
   package as the docs instruct.
4. Score yourself with the shipped `score_v18` and tune the **cost/quality
   frontier**, not quality alone.
5. Register (~$0.13) only once you clear the tier minimum locally with budget to
   spare.

---

## 7 · Rules you must keep

| Rule | Consequence |
|---|---|
| Use the validator-assigned `session_id` | You cannot create one — `POST /session` is rejected |
| Never access validator reference labels | Stated prohibition |
| Return before `task.deadline_s` | Empty response → no reward |
| Quality ≥ `max(tier_min, 0.35, 0.8 × best)` | Below → **zero**, not reduced |
| Tier minima 0.70 / 0.65 / 0.60 | A relative gate cannot weaken them |
| Stay inside `task.budget` | Cost is metered by the validator, not by you |
| No self-assigned score or cost claim | Ignored; miner cost claims are never used |
| Don't submit an identical reconstruction to another UID | Score divided across all sharers |
| Don't override `forward()` | Breaks the base miner's concurrency and timeout handling |
| Degraded-observer responses | Receive no reward |
| Actions from the fixed 18-verb vocabulary | Synonyms are mapped; unknown actions are not |

---

## 8 · Device conditions

### Miner

| | |
|---|---|
| Python | **3.11+** |
| System packages | **`ffmpeg`**, **`espeak-ng`** (apt) |
| **GPU** | **Not specified.** The protocol is model- and provider-agnostic — inference may be remote |
| Local development | **No GPU, no wallet, no chain, no credentials** |
| Serving | Public IP + reachable axon port; `--external-ip` / `--external-port` if NAT'd |
| Concurrency | `--concurrency` bounds admission; returns `busy` when full |

### Validator

| | |
|---|---|
| Hardware | **Not documented** — the guide points to the operator for requirements |
| Work | Generate private scenes, run the observation server, meter sessions, score, submit weights under commit-reveal |
| Storage | Round artifacts under `--round-root`, private scenes under `private/` |

> **Against your BEAM box (2 cores / 3.7 GB, Hetzner CX22):** it can run
> `witness.gen`, the dry-run validator and the shipped scorer — genuinely useful
> for developing and measuring a strategy, free. It **cannot** host competitive
> video inference; that needs a GPU elsewhere, though the protocol lets that be
> a remote provider rather than the miner box itself.

---

## 9 · Third-party conditions

| Dependency | Role | Note |
|---|---|---|
| **FFmpeg / ffprobe** | Video decode and scene rendering | Required for generation, scoring and the test suite |
| **eSpeak NG** | TTS for synthetic dialogue in generated scenes | Required runtime library |
| **The validator's observation server** | The only way a miner sees the video | Validator-owned; sessions cannot be self-created |
| **Private reference labels** | Ground truth | Never distributed — *"No trained miner, model weights or private evaluation data are distributed here"* |
| **Your inference provider** | Whatever you choose | Protocol is provider-agnostic; bounded external requests required |
| **finney** | Registration, commit-reveal weights | `commit_reveal_weights_enabled = True` |

Notably **absent**: no LLM judge, no hosted scoring API, no external dataset
dependency. Scenes are synthetically generated and scored deterministically.

---

## 10 · Risks

1. **It has not publicly launched.** Site banner, README and miner guide all say
   so independently, and the shipped `.env.example` carries a placeholder netuid.

2. **The owner's UID takes 100 % of the miner pool** (~$2,017/day), with total
   owner capture at **79.1 %** of emission — among the highest in this folder.

3. **The project says its own scorer has problems.** *"The historical default
   scorer has known reward weaknesses"* and *"production reward validation
   remains open."* Three scorer versions in the repo is evidence of active
   iteration, not of a settled metric.

4. **The default transcript mode may leak label-derived hints**, so scores
   obtained with defaults are not an independent measurement.

5. **A single weight setter.** One validator (UID 79) is setting weights; there
   is no consensus to speak of yet.

6. **A repurposed, very old slot.** Registered at block 1,970,929 — long before
   this project. The prior occupant is not disclosed in the repository.

7. **The relative gate can lock out newcomers.** `0.8 × best_quality_for_scene`
   means a strong incumbent raises the floor for everyone. Combined with the
   absolute tier minima (0.70 at tier 1), a mid-quality agent earns nothing at all.

8. **No hardware guidance anywhere**, for miners or validators. You cannot size
   the investment from the documentation.

9. **The competitive artifact is entirely yours to build.** No model, no
   observation strategy, no provider integration is shipped. That is honest, but
   it means the real cost is a video-understanding system you must supply.

10. **Dividends are concentrated** — the owner holds 49 %, and the top three
    hotkeys hold ~85 %.

---

## 11 · Documentation notes

Unusually careful. The repository repeatedly marks the boundary between what is
built and what is validated, which is rarer than it should be.

| Observation | Detail |
|---|---|
| Research-preview warning | Stated in README, on the site banner, and in the miner guide |
| Scorer honesty | *"The historical default scorer has known reward weaknesses"* |
| Transcript caveat | Default mode may use label-derived hints; flagged unprompted |
| Weight-submission honesty | *"Finalization … does not prove weights are active after reveal"* |
| Frozen scorers | v1.6/v1.7/v1.8 each SHA-pinned for reproducible re-scoring |
| `.env.example` netuid | Reads **1**, not 20 — a placeholder, consistent with "not launched" |
| Validator hardware | Not documented; deferred to the operator |

---

## 12 · Verdict

**Witness is a serious piece of engineering pointed at a genuinely hard problem,
sitting on a subnet that has not turned its incentive on.**

The problem is well chosen. "Understand this video" is a benchmark that has been
gamed to death; "understand this video *and account for every frame you looked
at*" is much harder to fake, and the metering is validator-owned so a miner
cannot lie about its own cost. Making **efficiency multiplicative with quality**
means the subnet rewards agents that decide *what to look at* — which is the
actual research question in agentic video, not a proxy for it. The
`intentional_errors` axis, with planted `audio_visual_contradiction` and
`misleading_subtitle` faults, forces cross-modal reasoning that a
transcript-scraping agent cannot fake.

The engineering matches. Three SHA-frozen scorer versions so historical rounds
re-score identically, 11 test modules, deterministic synthetic scene generation,
and a local dry-run that runs with **no wallet, no GPU and no chain**. Handing
prospective miners the exact grader is a real advantage and few subnets here do it.

**And the documentation is more honest than most.** It says its default scorer
has known reward weaknesses. It says the default transcript mode may leak
label-derived hints. It says finalizing a weight commitment does not prove the
weights applied. It tells you the CLI defaults are *not* confirmation of a
deployment. None of that had to be written down.

**What holds it back is that none of it is live.** The site says launch is
pending validation, the miner guide sends you to the operator for the netuid,
and on chain a single validator directs 100 % of the miner pool to the owner's
own UID — with total owner capture at 79.1 %. This sits in the same category as
SN78 UMI and SN25 UR: real work, honestly labelled, not yet paying anyone.

The distinguishing feature versus those two is **how much you can do while you
wait**. UMI's weights are type-level disabled and UR is testnet-first, but
neither hands you a working local harness. Witness does.

### Recommended path

1. **Ask whether SN20 is open to miners and what scoring config is current** —
   Discord or `contact@witnessvision.io`. Everything downstream depends on it.
2. **Start building now anyway; it is free.** `apt install ffmpeg espeak-ng`,
   clone, run the dry-run. No GPU, no wallet, no registration.
3. **Optimise the cost/quality frontier, not quality.** 0.85 quality at 20 %
   budget beats 0.95 at full budget — but falling under `0.8 × best` scores zero,
   so hit the gate first and cut cost second.
4. **Build genuine cross-modal detection** for `intentional_errors` — 15 % of
   quality that transcript-only agents cannot reach.
5. **Watch one number:** any UID other than 240 showing non-zero incentive. Until
   that changes, this subnet has never paid a miner.
6. **Watch one page:** the site's *"DASHBOARD · COMING SOON"* and the
   research-preview banner. When those change, the launch has happened — and the
   watchdog is now tracking that site.

---

## 13 · Sources

**Code**
- https://github.com/witnessvision/witness_subnet — 57 files
- Local: `/root/Bittensor/20/witness_subnet`
- `README.md`, `docs/miner.md`, `docs/validator.md`, `witness/score_v18.py`
  (635 ln), `witness/score/scorer.py`, `witness/contract.py`,
  `witness/tools/metering.py`, `.env.example`

**Site** (fetched 2026-09-10)
- https://witnessvision.io — banner: *"RESEARCH PREVIEW · RECORDED DEVELOPMENT
  TRACES · PUBLIC LAUNCH PENDING VALIDATION"*; dashboard *"COMING SOON"*

**Chain** (finney)
- `Subtensor.subnet(20)`, `metagraph(20)`, `weights(20)`, `recycle(20)`,
  `get_all_commitments(20)`, `get_subnet_hyperparameters(20)`,
  `SubnetIdentitiesV3(20)`

**Reference**
- https://taostats.io/subnets/20/metagraph

**Price reference**
- TAO ≈ $256 → α ≈ $0.68 at 0.002669 TAO/α
