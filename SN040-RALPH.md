# SN40 — Ralph (Open Model Compression)

| | |
|---|---|
| **netuid** | 40 (`Ralph`, symbol `ן`) |
| **What it is now** | **v2 — open model compression.** Compress a pinned `Qwen/Qwen3-8B` into fewer bits without touching its architecture |
| **What it was** | **v1 — decentralized autonomous AI research** (a training-recipe king-of-the-hill). The site labels those results *"Archived · v1 … the pretraining-recipe subnet that v2 replaced"* |
| **Owner hotkey** | `5HijSRHd9wUmk51UE8Kia7vmx6kD2jwqJLn9bY1frQ4aiTUs` — **UID 0** |
| **Owner coldkey** | `5HeKCDfdTyk5gttniUXWVGvf6xSpbJJG86thJcZnqNZjThoU` |
| **Code (v2, current)** | https://github.com/RalphLabsAI/ralph-v2 — public, pushed 2026-09-01 |
| **Code (v1, superseded)** | https://github.com/RalphLabsAI/ralph — last commit **2026-07-03** |
| **Local checkouts** | `/root/Bittensor/40/ralph` (v1) · `/root/Bittensor/40/ralph-v2` (v2, fetched today) |
| **Sites** | https://ralphlabs.ai · [/models](https://www.ralphlabs.ai/models) · [/dashboard](https://www.ralphlabs.ai/dashboard) · [/run](https://www.ralphlabs.ai/run) · [/research](https://www.ralphlabs.ai/research) |
| **Registered at block** | 8,409,860 |
| **Live state (2026-09-07, block ~9,013,000)** | **5 rounds scored, round 6 next** |
| **Price** | 0.003994 TAO/ן (**≈ $1.02**) · tao_in τ1,811 · alpha_in 453,522 · alpha_out 409,930 |
| **UIDs** | 256 registered · **1 with incentive** · 7 permits · 6 with dividends |
| **On-chain commitments** | **158** (131 bare sha256, 5 in the v2 JSON format, 22 other) |
| **Registration cost** | **0.99 TAO (~$253)** — among the most expensive in the folder |

> **Read §4.3 before anything else.** The v2 mechanism is live and has scored five
> rounds with four published crowns. **Every one of those four crown-holders
> currently earns zero on chain**, while a single UID that holds no crown takes
> 100 % of the miner pool. The repo itself supplies the likely reason.

---

## 1 · Goal — in plain terms

Take one model everybody already knows — `Qwen/Qwen3-8B`, 16.38 GB at bf16 — and
store it in **as few bits as possible without changing its architecture**, so it
still runs, on a phone.

The README's framing is the clearest statement of what makes this different from
distillation:

> *"This is not a smaller model trained to imitate a bigger one. It is the model
> you already know, stored differently — **smaller, not dumber**. A submission
> whose shape does not match the parent is refused before any weights load."*

The product is downloadable weights. Each bit tier has a reigning crown, published
as a plain GGUF you can put on an iPhone and run offline.

**Positioning, in the repo's own words:** SN3 trains full-precision models on a
frozen architecture (compression out of scope); SN97 fine-tunes a fixed model with
quantization banned; SN120 runs RL on full-size students. *"Nobody owns the
efficiency axis"* — v2 is the claim on that quadrant.

---

## 2 · What you do as a miner

**You compress the model privately, however you like, then commit a hash.** The
subnet never inspects your method — only your artifact.

```bash
# 1. compress Qwen/Qwen3-8B however you want — GPTQ, AWQ, bitsandbytes, your own
#    scheme. safetensors or GGUF, architecture unchanged.

# 2. COMMIT FIRST — seals a hash of your exact bytes before the round exists
python -m miner.submit commit --ckpt ./my-compressed-qwen3 --tier ternary \
    --uri hf://<you>/<repo>@<rev> --wallet <w> --hotkey <hk> --netuid 40

# 3. reveal after the round opens
python -m miner.submit reveal --ckpt ./my-compressed-qwen3 --wallet <w> --hotkey <hk>
```

### The six gates, in order — nothing loads your weights until all six pass

| # | Gate | Fails if |
|---|---|---|
| 1 | economics | not registered, or no bond outside your one free evaluation |
| 2 | safety | pickles, remote code, or files that are not weights |
| 3 | tier fit | parameter count or dtype headers inconsistent |
| 4 | **bit budget** | measured bits/weight over the tier cap — **read from tensor DATA, not the dtype header** |
| 5 | **pinned parent** | architecture or weight-element count does not match `Qwen/Qwen3-8B` |
| 6 | commit-reveal | bytes do not hash to what you committed before the nonce existed |

### The bit tiers

| tier | max bits/weight | ≈ size at 8B | emission share |
|---|---|---|---|
| `binary` | 1.15 | 1.18 GB | **40 %** |
| `ternary` | 1.75 | 1.79 GB | 25 % |
| `sub2` | 2.0 *(see §11)* | 2.05 GB | 20 % |
| `sub4` | 4.0 | 4.10 GB | 15 % |

**The hardest tier pays the most.** Binary carries 40 % of the miner pool.

### The format trap — this has already cost real miners their entry

> **"The crown has to run on a phone."** A format mainline `llama.cpp` cannot
> execute on Apple GPU is rejected at intake *"no matter how good its retention
> would have been — we score on an H100 where it might run perfectly well, and
> reject it anyway."*

| | |
|---|---|
| **Use** | `Q1_0`, `Q2_0`, `IQ1_S`, `IQ1_M`, `IQ2_XXS`, the `Q*_K` family |
| **Rejected** | **`TQ1_0`, `TQ2_0`** — mainline has no Metal kernel for either |

The `TQ*` types are the obvious pick by name (~1.1 and ~2.1 bits), pack
beautifully, and run fine on CUDA. They have no Metal kernel. `TQ1_0` *"has
already cost two miners their entry, including the only `binary` submission this
subnet has ever received."*

Check before committing, with the validator's own code:

```bash
python -m eval.bitrate path/to/model.gguf   # what intake will measure
python -m eval.precheck                     # header-measures the whole pending field
```

`precheck` is worth noting: **it shows you every competitor's pending artifact and
what intake will decide about it — without downloading a single model.**

### The other self-inflicted rejection

> *"`content_hash` covers the whole directory … a hash of your local pre-upload
> file misses whatever the repo actually serves. **Two miners lost round entries
> to this.**"*

Download your own HF repo at the revision you will commit, hash *that directory*,
and commit that.

---

## 3 · Scoring logic — "semantic equivalence by downstream effect"

This is the most interesting part of the subnet and the reason it is not just
another quantization leaderboard.

### 3.1 Why the obvious metrics were rejected

> *"Every distillation-KOTH before this got gamed the same way. Score **token
> agreement with the teacher** and you pay for style: **SN97's KL-crowned king
> mimicked 'wait, let me reconsider' filler, never produced an answer, and was
> worse than the un-finetuned base on 5/5 reasoning benchmarks.** Score
> **generated questions** and you pay for question-answering: probe formats are
> public, so fitting them is a cheap narrow skill that transfers to nothing."*

Naming another subnet's failure mode as the design constraint is unusual and, on
the evidence, correct.

### 3.2 What is measured instead

Two steps are equivalent when they move an **independent observer model** into the
same predictive state:

1. From a trajectory prefix `K`, the **pinned parent** produces its step; so does
   the miner's compressed model.
2. The observer continues from `K + parent_step` → call that continuation `C`.
3. Measure the observer's per-position distribution over **the same `C`**,
   conditioned on `K + parent_step`, on `K + miner_step`, and on `K` alone.

That yields disagreement `s`, parent effect `d_G`, and miner effect `d_A`. The
score rewards **effect similarity** (low `s`) and **effect magnitude**
(low `|d_A − d_G|`), both normalised by `d_G` so it is scale-invariant.

**There is no style channel.** A paraphrase carrying the same information scores
**0.80**; doing nothing scores **0.14**; moving the observer the wrong way scores
**0.02**.

### 3.3 Three properties that keep it honest

- **The observer is drawn from the round nonce** — you cannot pre-fit which
  grader you will face.
- **Discards are decided by the parent's effect alone.** Samples where the parent
  moves the observer nowhere are dropped — *"but never based on miner output, or a
  miner could bury its hard samples by emitting bland steps."*
- **Worst-slice aggregation** over (observer × language × depth), so a strong
  slice cannot buy a weak one.

The exam itself is derived from `H(commit_root ‖ round_nonce)` — a block hash
drawn **after** the commitment window closes. *"You cannot pre-fit an exam that
does not exist yet, or a grader you cannot name."*

Corpus: **~42M verified trajectories** across reasoning, agentic-code, dialogue
and non-Latin sources. And the anti-overfit argument is elegant: the pre-fit
attack is "memorise the parent's step at every `K`", which requires running the
parent across the corpus and training the student to match — **that is
distillation. The cheat and the job are the same activity.**

### 3.4 What you earn

| | |
|---|---|
| **King of the tier** | **80 %** of that tier's emission |
| **Best challenger with a strictly positive paired margin** | **20 %** |
| Everyone else | **nothing** |

- **Dethrone** needs a **0.05** worst-slice margin — *"below that a dethrone is a
  coin flip rather than a result, because 0.05 is what the paired bootstrap can
  resolve at this exam size."*
- **But you get paid without the crown:** beat the king by **0.01** on the same
  exam with the paired lower bound above zero and you take the 20 %.

That two-tier structure is a deliberate fix — you can earn while working toward
the crown, rather than needing to clear the full moat before seeing anything.

### 3.5 Anti-gaming is economic, not detective

> *"The last team proved you **cannot detect** copying on a shared base. v2 makes
> gaming **unprofitable** instead."*

- **A copy earns nothing.** An unchanged artifact is not re-scored at all; a
  near-copy scores what the original scores, putting its paired margin at zero.
- **One artifact has one owner** — if two hotkeys commit the same bytes, the
  earlier commitment wins and the later is refused, with the winning block named
  in the signed record.
- **Genre-overfit gate** (stale-vs-fresh diff-in-diff), armed by default.
- **Anti-grind economics** — one free eval per **coldkey**, a per-coldkey round
  cap, and a bond refunded only when you improve **your own** best.

And explicitly: *"**Start from the reigning crown if you want to.** Improving a
published artifact is the compounding this trail exists for — not an attack on
it."*

### 3.6 Auditability

Scoring is GPU-expensive; **checking is CPU-cheap**. Four levels:

```bash
python -m eval.rerun record.json                        # L0 arithmetic, free, no GPU
python -m eval.rerun record.json --pool items.jsonl     # + L1 re-derive the exam
  ... --observer <hf>                                   # + L2 re-derive the grades
  ... --artifacts ./ckpts                               # + L3 bind to the models
```

Exit `0` reproduced · `1` diverged · `2` incomplete. *"Skipping the expensive
levels exits 2, never 0 — nobody can call a round verified by running the cheap
half."*

And the threat model is stated plainly: *"The adversary assumed throughout is **the
operator holding the signing key**, so a valid signature attributes a record and
never validates it."*

---

## 4 · Live competition landscape

### 4.1 Five rounds scored, four crowns published

From the operator's dashboard (*"5 rounds scored · round 6 next"*) and the models
page:

| tier | crown holder | bits/weight | size | retention | crowned | dashboard margin |
|---|---|---|---|---|---|---|
| `binary` 40 % | `5FWBzRrdkMK4…` (**UID 158**) | 1.1477 | 1.91 GB | 0.2385 | round 3 | −0.0120 · **defended** |
| `ternary` 25 % | `5HNA3Fegavpu…` (**UID 159**) | 1.714 | 2.46 GB | 0.2537 | round 5 | **+0.0701 — challenger earns 20 %** |
| `sub2` 20 % | `5FnTBc78cqo4…` (**UID 160**) | 2.1587 | 2.82 GB | 0.2830 | round 3 | +0.0000 · defended |
| `sub4` 15 % | `5DhxLJrXRdPf…` (**UID 135**) | 4.00 | 4.61 GB | 0.3007 | round 1 | +0.0000 · defended |

Published weights are credited to two builders: **`tensor-tailor`** holds
binary, ternary and sub2; **`andreas11112`** holds sub4.

**Round 5:** 9 scored + 4 re-scored · 5 rejected · 12 unchanged, not re-scored ·
144 exam items · *binary held · ternary dethroned · sub2 held · sub4 held*.

### 4.2 What retention actually means here

Retention `1.0` = indistinguishable from the parent. **`~0.135` is the floor for
contributing nothing.** The crowns sit at **0.19 – 0.30** — well above the floor,
far below the parent. The operator is explicit that this *"is not a capability
benchmark, and a high retention does not by itself mean a model is good at any
particular task."*

### 4.3 ⚠️ Every crown-holder earns zero

This is the finding that matters most, and I verified it directly.

| Dashboard says | UID | On-chain incentive | On-chain emission |
|---|---|---|---|
| binary — 40 % of tier | 158 | **0.000000** | **0.000** |
| ternary — 25 % | 159 | **0.000000** | **0.000** |
| sub2 — 20 % | 160 | **0.000000** | **0.000** |
| sub4 — 15 % | 135 | **0.000000** | **0.000** |

Meanwhile the on-chain weight vector is unanimous and points somewhere else:

| Setter | Stake | Weight |
|---|---|---|
| UID 0 (owner) | 763,208 | **100 % → UID 124** |
| UID 6 | 282,114 | **100 % → UID 124** |
| UID 149 | 159,140 | **100 % → UID 124** |
| UID 72, 4, 44 | smaller | **100 % → UID 124** |
| UID 175 | 944 | 100 % → UID 214 |

**UID 124 holds no crown** (hotkey `5HTERMEJg8W2g6gi…`, coldkey distinct from the
owner's) and takes **100 % of the miner pool — 2,952 α/day ≈ $3,018/day.**

**The repo supplies the likely explanation**, in its own "Not yet done" section:

> *"**Weights have never been set by this validator.** It runs read-only by
> default and will keep doing so until there is something worth crowning; a second
> signer on a live hotkey fights the first."*

So the coherent reading is: **the v2 validator scores rounds and publishes crowns
but does not pay them**, while the on-chain weights come from a separate,
older process still pointing at UID 124. That is inference on my part — the
dashboard simultaneously reports *"chain writes live"*, which cuts the other way —
but the observable facts are not in doubt: **the four miners who won are not being
paid, and the one being paid did not win.**

### 4.4 Other stale claims in the v2 README

The repo pushed 2026-09-01; the network has moved past parts of it:

- *"**No miner has ever submitted anything.**"* — the chain carries 158
  commitments, five in the v2 JSON format, and the dashboard has scored 5 rounds
  with 9 artifacts in round 5 alone.
- *"`TQ1_0` … cost two miners their entry, including **the only `binary`
  submission this subnet has ever received**."* — binary has been **crowned since
  round 3** at 1.1477 bits.

Both read as an honest snapshot that the network then overtook.

---

## 5 · Economics

Subnet emits **1.000 α/block = 7,200 α/day**; 18 % owner cut, 41 % miners, 41 %
validator dividends → **miner pool = 2,952 α/day**.

At α = 0.003994 TAO and TAO ≈ $256 → **α ≈ $1.02** → miner pool ≈ **$3,018/day**.

### What is actually happening

| | α/day | USD/day |
|---|---|---|
| **UID 124 (holds no crown)** | **2,952** | **$3,018** (~$90,500/mo) |
| All four crown-holders | **0** | **$0** |
| Owner UID 0 (18 % cut + 61.8 % dividends, **0 incentive**) | 3,121 | **$3,190 — 43.3 % of emission** |

### What the published mechanism would pay

If the 40/25/20/15 tier split and 80/20 king–challenger split were live:

| tier | tier α/day | **king** | **best challenger** |
|---|---|---|---|
| `binary` | 1,181 | 945 α ≈ **$966/day** | 236 α ≈ $241/day |
| `ternary` | 738 | 590 α ≈ **$604/day** | 148 α ≈ $151/day |
| `sub2` | 590 | 472 α ≈ **$483/day** | 118 α ≈ $121/day |
| `sub4` | 443 | 354 α ≈ **$362/day** | 89 α ≈ $91/day |

Four crowns plus four challenger slots = **eight paid positions**, which would be
a genuinely healthy structure. None of it is reaching miners today.

### Costs

| Item | Cost |
|---|---|
| **Registration** | **0.99 TAO ≈ $253** — among the most expensive in the folder |
| Bond | One free evaluation per **coldkey**; a bond for extras, refunded only when you beat your own best |
| **GPU** | Enough to hold and quantize an 8B model — a 24 GB card is workable, more is better. **You compress offline; you never serve.** |
| Storage / bandwidth | Hugging Face hosting of multi-GB GGUFs |
| Uptime | **None** — commit, reveal, done |

---

## 6 · How to become a winner

**Do not spend $253 on registration until §4.3 is resolved.** That is the whole
of the near-term advice. Everything below is what to do if it is.

### Priority 1 — Ask the operator why crowns are not being paid

Four miners have won tiers across five scored rounds and hold zero incentive,
while an uncrowned UID takes the entire pool. The repo says the v2 validator runs
read-only; the dashboard says chain writes are live. **Those cannot both describe
today.** The org runs public
[Discussions](https://github.com/orgs/RalphLabsAI/discussions) — ask there, in
public, and the answer benefits everyone.

### Priority 2 — Target `sub2`, then `binary`

The README's own steer, and the numbers support it:

> *"**If you want a crown this month, `sub2` is the better target.** A `Q2_0` body
> with a higher-precision embedding measures ~2.23 against a 2.3 cap, it is
> reachable with **stock `llama-quantize`**, and the tier is uncrowned because its
> only entrant so far fails the degeneracy gate."*

That guidance is now partly stale — sub2 **is** crowned (0.2830, UID 160) — but
the underlying point holds: sub2 is the tier you can reach with off-the-shelf
tooling. Its dashboard margin is **+0.0000**, meaning the incumbent is undefended
by anything but the 0.05 moat.

**`binary` carries 40 % of the pool** and is where the real money is. It is also
genuinely hard (§Priority 3).

### Priority 3 — Understand what `binary` actually requires

The README corrects itself here, and the correction is the most useful paragraph
in the repo:

> *"**Binary is a research tier. Stock `llama-quantize` will not get you there,
> and we were wrong to imply otherwise.**"* A miner ran it end to end and reported
> perplexity in the millions.

The reason: `llama.cpp` supplies kernels that **run** 1-bit weights, not a method
that **produces** good ones. Round-to-nearest with group scales throws away the
information at one bit regardless of the importance matrix.

So you must **produce the 1-bit weights yourself, then export to `Q1_0`.** Two
published PTQ frameworks need no retraining:

| | |
|---|---|
| [**BiLLM**](https://github.com/Aaronhuang-778/BiLLM) (ICML 2024) | salient/non-salient split, binary residual approximation. **8.41 ppl on LLaMA2-70B at 1.08 bit** |
| [**ARB-LLM**](https://github.com/ZHITENGLI/ARB-LLM) | alternating refined binarization with row/column scaling |

**1.08 bit fits under the 1.15 cap** with room for a 2-bit embedding on top. The
operator is straight about the gap: *"We have not run either on Qwen3-8B ourselves
— we are pointing at the state of the art, not handing you a verified recipe, and
the export path in particular is unproven."*

### Priority 4 — Exploit the per-tensor headroom

The bit gate for GGUF reads **type names per tensor**, averaged by parameter count.
On Qwen3-8B the token embedding is **7.60 %** of parameters:

- `--token-embedding-type Q2_K` → measures **1.0760** ✅ passes binary
- embedding **and** output both at `Q2_K` → **1.1520** ❌ just misses 1.15

**Per-tensor mixing is fully supported and is where your headroom is.**
Per-*weight* salience is not — a BiLLM-style scheme carrying ~1.1 bits has no GGML
type that expresses it. The tier is *"a bound on information that llama.cpp can
represent and run."*

### Priority 5 — Never touch `TQ1_0` or `TQ2_0`

They are the obvious choice by name, they pack beautifully, they run on your CUDA
box, and **there is no Metal kernel** so they cannot run on a phone. Two miners
have already lost entries to this. Run `python -m eval.bitrate` first, every time.

### Priority 6 — Hash the served bytes, not the local file

Download your own HF repo at the exact revision you will commit, hash *that
directory*, commit *that*. Two more miners lost entries here.

### Priority 7 — Scout with `precheck`, and aim at the weakest margin

```bash
python -m eval.precheck   # header-measures the entire pending field, no downloads
```

Then pick your target from the dashboard's margins. Today `sub2` and `sub4` both
sit at **+0.0000** — nobody is pushing them. `ternary` was just dethroned by
+0.0701, so it is contested. `binary` is defended at −0.0120, i.e. the nearest
challenger is *behind*.

### The path

1. Ask about §4.3 in the public Discussions. **Wait for an answer.**
2. If it resolves: register (0.99 TAO ≈ $253) and use your one free per-coldkey eval.
3. Start at `sub2` with stock `llama-quantize` to learn the pipeline end to end.
4. Move to `binary` with BiLLM or ARB-LLM — 40 % of the pool, and the export path
   is unproven, which is exactly where an edge is available.
5. `eval.bitrate` → `eval.precheck` → hash the served directory → commit → reveal.

---

## 7 · Rules you must keep

| Rule | Consequence if broken |
|---|---|
| Architecture and weight-element count match `Qwen/Qwen3-8B` | Refused **before any weights load** |
| Measured bits/weight ≤ tier cap (read from tensor **data**) | Rejected at intake |
| Format runs on Apple GPU — **no `TQ1_0` / `TQ2_0`** | Rejected regardless of retention |
| No pickles, no remote code, no non-weight files | Rejected at the safety gate |
| Commit the hash of the **served** directory, before the round nonce exists | Commit-reveal mismatch, recorded as served ≠ committed |
| Registered, and bonded beyond your one free per-coldkey eval | Rejected at the economics gate |
| Don't submit bytes another hotkey committed earlier | Refused; the earlier block is named in the record |
| Beat the king by **0.05** worst-slice to take the crown | No dethrone |
| Beat the king by **0.01** with paired LCB > 0 | Otherwise you earn nothing at all |
| A 4-bit model in a 16-bit container | Credited for compression achieved **and** rejected as unshippable |

---

## 8 · Device conditions

### Miner

| | |
|---|---|
| **GPU** | Enough to hold and quantize Qwen3-8B — 24 GB workable, more comfortable. v1 docs referenced H100 boxes |
| **Serving** | **None.** You compress offline and commit a hash |
| **Uptime** | **None.** Commit, reveal, done |
| Disk / bandwidth | Multi-GB GGUFs, hosted on Hugging Face |
| Tooling | `llama.cpp` (`llama-quantize`), optionally BiLLM / ARB-LLM for the binary tier |
| Local checks | `eval.bitrate`, `eval.precheck` — **stdlib only, no GPU** |

### Validator

| | |
|---|---|
| **GPU** | **Required** — runs the observer scoring |
| Determinism | Score is only meaningful against a recorded `(gpu, batch_size, attn_implementation)` — all three now in the signed manifest |
| Sandbox | **Needs `bubblewrap`** for the code canary |
| Default mode | **Read-only** — it does not set weights unless told to |

### Auditor

| | |
|---|---|
| **GPU** | **None for L0/L1** — *"auditors run on CPU, so anyone can check a crown without a datacentre"* |

> **Against your BEAM box (2 cores / 3.7 GB, Hetzner CX22):** it can run
> **`eval.bitrate`, `eval.precheck` and L0/L1 audits** — genuinely useful, and
> free. It **cannot** compress an 8B model (that needs a real GPU elsewhere) and
> cannot validate.

---

## 9 · Third-party conditions

| Dependency | Role | Failure mode |
|---|---|---|
| **Hugging Face** | The pinned parent `Qwen/Qwen3-8B`, every artifact, every published crown | Total dependency for artifact delivery |
| **`llama.cpp` / GGUF** | The format, the bit accounting, **and the eligibility rule** | The gate is literally *"must have a Metal kernel"* — upstream llama.cpp decides what can win |
| **Apple Metal** | Defines which quant types are admissible | A third party's kernel coverage is a consensus input |
| **Observer model pool** | Grades every submission; drawn from the round nonce | Pinned per round and named in the record |
| **Trajectory corpus** | ~42M verified trajectories (reasoning, agentic-code, dialogue, non-Latin) | SWE-ZERO deduped to ≤5 rollouts/task |
| **`bubblewrap`** | Sandboxes the code canary on the validator | Validator cannot run the canary without it |
| **Weights & Biases** | v1 experiment tracking (`ralphlabs-hub/ralph`) | Observational |
| **finney** | Registration, commit-reveal, weights, audit anchor | The anchor chain *"has never been committed by a real chain"* per the repo |

---

## 10 · Risks

1. **The crowns are not being paid.** Four winners across five scored rounds hold
   **zero** incentive; one uncrowned UID takes 100 % of the miner pool. Until this
   is explained, a crown has no demonstrated cash value — which makes the $253
   registration a bet on a mechanism that has never paid a miner.

2. **Registration is $253 and the outcome is unproven.** The most expensive entry
   in the folder except SN103, on a subnet where no miner has yet been observed
   earning from the published mechanism.

3. **The subnet pivoted wholesale.** v1 (autonomous AI research / training recipes)
   was replaced by v2 (model compression). The v1 repo is 2 months stale and its
   results are explicitly archived. A second pivot is not impossible.

4. **The v2 README is already behind its own network** — it says no miner has ever
   submitted and that binary has never been successfully entered; both are false
   as of round 5. Honest snapshots, but you cannot treat the doc as current.

5. **Retention tops out at 0.30 against a parent of 1.0**, on a floor of 0.135.
   The crowns are much closer to "contributing nothing" than to "indistinguishable
   from the parent." Whether a 0.24-retention binary model is *useful* is not what
   this metric answers, and the operator says so.

6. **The score saturates at the bottom.** Perturbing all weights, the score falls
   monotonically only to σ=0.05 then flattens at 0.43–0.57 and wobbles — *"the
   metric cannot tell a broken model from a very broken model."* Mitigated by the
   capability canary and by the wobble being below the dethrone margin, but it is
   the closest thing here to scoring well while being useless.

7. **Determinism is a property of the box.** The H100 returned four different
   outputs from four identical `generate()` calls until the attention
   implementation was pinned. Cross-GPU, boxes still generate different step text.

8. **The audit anchor has never landed on mainnet.** `A_n = H(A_{n-1} ‖ digest)`
   is implemented but *"no `commit_audit_root` call has landed on mainnet. Until
   one does, the strongest guarantee here is untested on the network it is for."*

9. **Owner captures 43.3 % of emission** — but note it takes **zero** miner
   incentive; that figure is the 18 % cut plus 61.8 % of validator dividends.

10. **Non-Latin coverage is Hindi and Chinese only**, while *"the published
    evidence for low-bit collapse is Persian and Cyrillic, so the pool does not
    yet test where the proof is."*

11. **`eval/budget.py`** (score-at-budget / convergence gate) is written and tested
    but **not wired into the crown path.**

---

## 11 · Documentation notes

The v2 README is among the most honest in this folder — it corrects itself in
place (*"we were wrong to imply otherwise"*), credits miners who diagnosed bugs,
and carries a "Not yet done" section most projects would omit. The defects are
staleness, not spin.

| Claim | Where | Reality |
|---|---|---|
| *"No miner has ever submitted anything"* | v2 README, "Not yet done" | 158 on-chain commitments; 5 rounds scored; 9 artifacts in round 5 |
| *"the only `binary` submission this subnet has ever received"* failed on `TQ1_0` | v2 README, "Formats that can win" | `binary` has been crowned since **round 3** at 1.1477 bits |
| *"`sub2` … is uncrowned"* | v2 README, "How to reach the binary tier" | Crowned round 3, retention 0.2830 |
| `sub2` cap listed as **2.0** | v2 README tier table | Prose in the same file says *"~2.23 against a **2.3** cap"*, and the live crown measures **2.1587**. The table is wrong |
| *"Weights have never been set by this validator"* | v2 README | Dashboard reports *"chain writes live"*. One of the two is out of date |
| v1 repo presented as "The core: Ralph protocol" | GitHub org description | Superseded by v2; site archives v1 results |

---

## 12 · Verdict

**Ralph v2 has the most carefully-reasoned scoring metric of any subnet in this
folder, and the widest gap between that metric and what the chain pays.**

The metric design deserves the attention. It starts by naming exactly how the
previous generation was gamed — SN97's KL-crowned king that *"mimicked 'wait, let
me reconsider' filler, never produced an answer, and was worse than the
un-finetuned base on 5/5 reasoning benchmarks"* — and then builds something with
no style channel at all. Scoring a compressed model by **how it moves an
independent, nonce-drawn observer**, aggregated over the **worst** slice of
(observer × language × depth), with discards decided by the *parent's* effect so a
miner cannot bury hard samples, is a genuinely good answer to a hard problem. The
anti-overfit argument — that the only pre-fit attack *is* distillation, so the
cheat and the job are the same activity — is the kind of reasoning most subnets
never attempt.

The surrounding engineering matches. Anti-gaming is **economic rather than
detective**, on the stated grounds that the last team proved detection doesn't
work. Auditors run on CPU at four cost levels, and skipping the expensive ones
exits `2`, never `0`. The threat model names the operator's own signing key as the
adversary. `eval.precheck` lets you see the entire pending field without
downloading anything. And the README corrects its own errors in place and credits
the miners who found them.

**Then you look at the chain.** Five rounds scored, four crowns published with
downloadable weights and named builders — and **all four crown-holders earn
exactly zero**, while a single UID holding no crown takes 100 % of the miner pool,
about $3,018/day. The repo's own "Not yet done" section says the v2 validator
*"runs read-only by default"* and has never set weights, which would explain it
completely; the dashboard says chain writes are live, which would not. Either way,
**this subnet has not yet been observed paying a miner for winning.**

That is the whole investment case, and it is unresolved. Registration costs $253 —
one of the highest here — for entry to a mechanism whose published payout table
(eight paid positions across four tiers, 80/20 king–challenger) is excellent on
paper and has never reached anyone's wallet.

### Recommended path

1. **Ask in the public [Discussions](https://github.com/orgs/RalphLabsAI/discussions)
   why crown-holders hold zero incentive while UID 124 takes the pool.** Do not
   spend $253 first.
2. **Meanwhile, everything useful is free.** Clone `ralph-v2`, run
   `eval.bitrate` and `eval.precheck`, and run an L0/L1 audit of a published round
   — all CPU-only, all on the Hetzner box, no registration needed.
3. **If it resolves:** start at `sub2` with stock `llama-quantize` to learn the
   pipeline, then attack **`binary`** — 40 % of the pool, an unproven export path,
   and two published PTQ frameworks (BiLLM, ARB-LLM) nobody has yet run on
   Qwen3-8B.
4. **Never `TQ1_0`/`TQ2_0`; hash the served directory, not your local file.** Four
   miner entries have already been lost to those two mistakes alone.
5. **Watch one signal above all:** whether any crown-holding UID starts showing
   non-zero incentive. That single number tells you whether this subnet pays for
   winning.

---

## 13 · Sources

**Code**
- https://github.com/RalphLabsAI/ralph-v2 (current, pushed 2026-09-01) — `README.md`, `experiments.md`
- https://github.com/RalphLabsAI/ralph (v1, last commit 2026-07-03)
- Local: `/root/Bittensor/40/ralph-v2`, `/root/Bittensor/40/ralph`

**Live operator sites** (fetched 2026-09-07)
- [ralphlabs.ai](https://www.ralphlabs.ai/) · [/models](https://www.ralphlabs.ai/models) — four crowns, bits, retention, builders
- [/dashboard](https://www.ralphlabs.ai/dashboard) — 5 rounds scored, tier shares, per-tier margins
- [/run](https://www.ralphlabs.ai/run) · [/research](https://www.ralphlabs.ai/research)

**Chain** (finney, block ~9,013,000)
- `Subtensor.subnet(40)`, `metagraph(40)`, `weights(40)`, `recycle(40)`,
  `get_all_commitments(40)` — 158 commitments

**Reference**
- https://taostats.io/subnets/40/metagraph
- [BiLLM](https://github.com/Aaronhuang-778/BiLLM) · [ARB-LLM](https://github.com/ZHITENGLI/ARB-LLM)

**Price reference**
- TAO ≈ $256 → α ≈ $1.02 at 0.003994 TAO/α
