# SN119 — CapabilityForge Next (Training-Data Improvement)

| | |
|---|---|
| **netuid** | 119 (`CapabilityForge Next`, symbol `Ⲃ`) |
| **Chain description** | *"rewards traceable training-data improvements that measurably enhance the accuracy, reasoning, clarity, age appropriateness, and safety of learning-oriented AI through reproducible evaluation"* |
| **Owner hotkey** | `5HMwvi1dHWCBHTNTtizL5peRBwqvd8HtGrTVouN51p75JNd4` — **holds UID 0** |
| **Owner coldkey** | `5GbLENPLG8Takn1puaz5HorPmrFtDT7i2PojiJsqutbaGwWu` |
| **Code** | https://github.com/capabilityforge-next/capabilityforge |
| **Repo contents** | **`README.md` (32 lines), `.gitignore` (2 lines), 2 images. No code.** |
| **Repo created** | **2026-09-09 13:06 UTC** — *today*. Single commit, "Initial commit" |
| **GitHub account created** | **2026-09-08** — *yesterday*. Type: **User**, not an organisation. 1 public repo |
| **Local checkout** | `/root/Bittensor/119/capabilityforge` @ `33e2ade` |
| **Subnet URL** | *(empty on chain)* |
| **Discord** | A **channel link inside the Bittensor Discord** (guild `799672011265015819`), not a project server |
| **Registered at block** | **5,740,660** — the slot long predates this project |
| **Live state (2026-09-09, block ~9,047,000)** | **0 on-chain commitments** |
| **Price** | 0.002774 TAO/Ⲃ (**≈ $0.71**) · tao_in τ3,401 · alpha_in 1,226,125 · alpha_out 1,630,628 |
| **UIDs** | 256 registered · **1 with incentive (the owner)** · 11 permits · 10 with dividends |
| **Registration cost** | **0.0005 TAO (~$0.13)** |

> ## ⚠️ Read this first
>
> **There is no implementation to analyse.** The complete public artifact for
> Subnet 119 is a **32-line marketing README and a logo**, committed today by a
> GitHub account created yesterday. There is no miner code, no validator code, no
> protocol specification, no scoring definition, no data format, no tests, and no
> submission mechanism. There are **zero commitments on chain**.
>
> Meanwhile the subnet draws full emission, and **the owner's own UID takes 100 %
> of the miner pool** — about **$2,096/day**, with total owner capture at
> **61.6 %** of emission (~$3,149/day).
>
> Every section below reports what I could verify. Several are short because
> there is nothing there to report.

---

## 1 · Goal — what the README claims

The stated aim is an incentive network for **discovering training-data
improvements** that make learning-oriented AI more accurate, clearer, more
age-appropriate and safer.

> *"CapabilityForge Next is Bittensor Subnet 119—an incentive network for
> discovering training-data improvements that make learning-oriented AI more
> accurate, clear, age-appropriate, and safe."*

Initial scope is **mathematics and the natural sciences**, chosen because
*"answers, reasoning steps, calculations, and explanations can be evaluated
objectively."* The README says scope may expand to more subjects, languages and
learner profiles *"as reliable evaluation standards become available."*

The pitch is a genuinely reasonable one — data quality is a real bottleneck, and
education is a domain where age-appropriateness and safety matter. **The problem
is not the idea. It is that nothing has been built to implement it.**

---

## 2 · What you do as a miner

**Unknown, and not currently possible.**

The README gives four bullets and a five-word pipeline:

> - **Miners** generate bounded synthetic or appropriately licensed data patches with record-level provenance.
> - **Validators** check data rights, privacy, lineage, duplication, contamination, and evaluation leakage.
> - Qualified patches are tested against a frozen baseline under identical training and evaluation conditions.
> - Rewards reflect measurable capability improvements—not dataset size, compute expenditure, or unverified claims.

```text
GENERATE → VERIFY → TRAIN → EVALUATE → REWARD
```

That is the entire published description of the mechanism. What is **not**
specified, anywhere:

| Question a miner must answer | Published? |
|---|---|
| What is a "data patch"? Format, schema, size bounds? | **No** |
| How do I submit one? HTTP, chain commitment, HF repo? | **No** |
| What is the "frozen baseline" model? | **No** |
| What are the evaluation sets? | **No** |
| How is "record-level provenance" expressed or checked? | **No** |
| How is a score computed from an improvement? | **No** |
| How are scores converted to weights? | **No** |
| Rounds, cadence, deadlines? | **No** |
| Is there miner software? | **No** |
| Are there hardware requirements? | **No** |

There is no `pyproject.toml`, no `requirements.txt`, no `neurons/`, no
`docs/`, no `min_compute.yml`. The repository is 674 KB, and essentially all of
it is the two image files.

**Practical consequence: you cannot mine this subnet today.** Not "it's hard" or
"you need a GPU" — there is no artifact to produce and no channel to submit it
through. The **zero on-chain commitments** confirm nobody else has found one
either.

---

## 3 · Scoring logic

**Not published.**

The README states what the network intends to measure:

> - factual accuracy and task completion;
> - reasoning quality and correct use of steps and units;
> - calibration and honest handling of uncertainty;
> - clear, helpful, and age-appropriate communication;
> - safety without unnecessary refusal.

And an eligibility claim:

> *"Youth safety and data responsibility are mandatory. Private information,
> real-minor personal data, hidden evaluation content, and materials without
> suitable usage rights are not eligible."*

These are objectives, not a mechanism. There is no formula, no threshold, no
weight-conversion rule, no anti-gaming design, and no statement of how a
validator decides between two competing patches.

For contrast, every other subnet in this folder publishes its scoring in code:
SN103 ships `contribution.py` with exact weights I could recompute to five
decimals; SN92 publishes an exclusive-hypervolume rule and a public API that
reproduces the leaderboard; SN40 publishes a 500-line observer-KL derivation.
**SN119 publishes five bullet points.**

---

## 4 · Live competition landscape

### 4.1 One earner, and it is the owner

| | |
|---|---|
| UIDs with non-zero incentive | **1** |
| That UID | **UID 0** — verified identical to `subnet.owner_hotkey`, and its coldkey identical to `owner_coldkey` |
| Its incentive | **1.000000** |

Six validators set weights, unanimously:

| Setter | Stake | Weight |
|---|---|---|
| UID 175 | 151,959 | **100 % → UID 0** |
| UID 0 (owner) | 108,808 | **100 % → UID 0** |
| UID 174 | 58,893 | **100 % → UID 0** |
| UID 173 | 40,974 | **100 % → UID 0** |
| UID 34 | 30,590 | **100 % → UID 0** |
| UID 172 | 23,403 | **100 % → UID 0** |

### 4.2 Zero commitments

`get_all_commitments(119)` returns **0**. Across every other subnet in this
folder that uses on-chain submission, this number is in the tens or hundreds
(SN40: 158, SN25: 263, SN93: 59, SN92: 59). Here nothing has ever been committed
by anyone, which is consistent with there being no defined submission format.

### 4.3 The public presence is one day old

| Fact | Value |
|---|---|
| GitHub account `capabilityforge-next` created | **2026-09-08** |
| Account type | **User** (not an organisation) |
| Public repos | **1** |
| Repository created | **2026-09-09 13:06 UTC** |
| Last push | 2026-09-09 13:54 UTC |
| Commits | **1** — *"Initial commit"* |
| Stars / forks / open issues | 0 / 0 / 0 |
| Language detected by GitHub | **none** |

The chain identity's `subnet_url` field is **empty**, and the `discord` field
points at a **channel inside the general Bittensor Discord** rather than a
project server. There is no website, no whitepaper, no documentation site.

### 4.4 The slot is old; the project is not

The subnet registered at block **5,740,660**, which places the *slot* far earlier
than this project. The name "CapabilityForge **Next**" itself implies a
predecessor. I could not establish the prior identity from public sources and am
**not asserting one** — but a one-day-old identity on a long-registered slot is
the same repurposing pattern seen on SN29 (`coldint`→`hoτfloaτ`), SN36
(`Leoma`→`automata`), SN78 (`Vocence`→`UMI`) and SN25 (`Mainframe`→`UR`).

---

## 5 · Economics

Subnet emits **7,200 α/day**; 18 % owner / 41 % miner / 41 % validator →
**miner pool = 2,952 α/day**.

At α = 0.002774 TAO and TAO ≈ $256 → **α ≈ $0.71**:

| | α/day | USD/day |
|---|---|---|
| Miner pool (face value) | 2,952 | **$2,096** |
| **UID 0 (owner) — 100 % of it** | **2,952** | **$2,096** (~$62,900/mo) |
| Every other UID | **0** | **$0** |
| **Owner total** (18 % cut + 100 % incentive + 6.34 % dividends) | **4,435** | **$3,149/day — 61.6 % of emission** |

Validator dividends are separately concentrated: UID 45 holds **62.5 %** with
1,072,118 stake.

### Costs to participate

| Item | Cost |
|---|---|
| Registration | **0.0005 TAO ≈ $0.13** |
| Everything else | **Unknowable** — no hardware spec, no software, no submission path |

---

## 6 · How to become a winner

**You cannot, today.** There is no way to participate, so there is no strategy to
give. What follows is what I would actually do.

### Priority 1 — Do not register, and do not buy α on this thesis

$0.13 is trivially cheap, but a UID here buys access to nothing. There is no
software to run and no artifact to submit. Registering would mean holding a slot
on a subnet whose owner currently takes 100 % of the miner pool.

### Priority 2 — Ask three specific questions before spending anything

The chain identity gives a Discord channel in the main Bittensor server. Ask
there, publicly:

1. **When will miner and validator software be published?** The repo is a README.
2. **What is the submission format for a "data patch"?** Nothing on chain suggests
   one exists — commitments are at zero.
3. **What is the frozen baseline model and the evaluation set?** Without both,
   *"tested against a frozen baseline under identical conditions"* is not checkable.

### Priority 3 — Judge the project on whether code appears, not on the README

The README is well written and the goal is defensible. That is not evidence of
anything. The signals that would change my assessment, in order:

- Miner and validator code in the repository
- A published scoring rule specific enough to recompute
- **Any** non-zero commitment count on chain
- **Any** UID other than the owner's showing non-zero incentive

Until at least the first of those appears, this is a subnet drawing ~$3,149/day of
emission against a 32-line document.

### Priority 4 — If the domain interests you, there are working alternatives now

If what attracted you is *training-data quality and reproducible evaluation*,
subnets in this folder that ship code and pay miners today include **SN92
MicroTensor** (certified inference systems, 9 earners, public API that reproduces
the frontier), **SN103 Capcomp** (LoRA composition, 10 earners, scores
re-derivable to five decimals), and **SN123 MANTIS** / **SN79 MVTRX** for
genuinely contested fields. Any of them lets you start this week.

---

## 7 · Rules you must keep

**None published.** The README states eligibility exclusions — no private
information, no real-minor personal data, no hidden evaluation content, no
materials without usage rights — but there is no stated enforcement mechanism, no
gate definition, and no consequence table.

---

## 8 · Device conditions

**Not published.** No `min_compute.yml`, no hardware section, no dependency list.

Inferring from the described pipeline (*GENERATE → VERIFY → TRAIN → EVALUATE*),
a validator would need to **train and evaluate a model per submitted patch**,
which is a GPU-heavy workload — plausibly the most expensive validator role in
this folder. But that is my inference from four bullet points, not a
specification, and nothing in the repository confirms it.

> **Against your BEAM box (2 cores / 3.7 GB, Hetzner CX22, 46.225.140.58):**
> unanswerable. There is nothing to install and nothing to run.

---

## 9 · Third-party conditions

**Not published.** No dependencies are declared. From the README's language, a
working implementation would plausibly need a pinned baseline model, evaluation
corpora, and dataset-licensing/provenance tooling — but none is named.

The only external dependency I can verify is **GitHub**, hosting the README, and
**finney** for registration and weights.

---

## 10 · Risks

1. **There is no implementation.** A 32-line README and a logo. No miner code, no
   validator code, no protocol, no scoring rule, no tests. This is the entire
   published artifact.

2. **The public presence is one day old.** GitHub user created 2026-09-08,
   repository created 2026-09-09, one commit, zero stars, no language detected —
   on a slot registered at block 5,740,660.

3. **The owner takes 100 % of the miner pool** (~$2,096/day) and **61.6 % of all
   emission** (~$3,149/day), by unanimous weight from six validators, while no
   mechanism exists for anyone else to earn.

4. **Zero on-chain commitments.** No miner has submitted anything, which is
   consistent with there being no defined way to submit.

5. **No website, no whitepaper, no project Discord.** The chain `subnet_url` field
   is empty and the `discord` field points at a channel in the general Bittensor
   server.

6. **Every claim in the README is currently unfalsifiable.** *"Rewards reflect
   measurable capability improvements"* cannot be checked without a published
   metric, baseline, or evaluation set. Compare SN40, which publishes its
   observer-KL derivation and a four-level CPU audit path precisely so an outsider
   can falsify a crown.

7. **Repurposed slot with an unestablished history.** The name implies a
   predecessor; I could not determine what SN119 was before, and that history is
   not disclosed in the repository.

8. **The stated domain carries elevated duty of care.** The subnet's own framing
   is *learning-oriented AI* with *youth safety* as *"mandatory"*. Handling
   education data for minors responsibly requires exactly the enforcement
   machinery — provenance checks, privacy gates, leakage detection — that is
   asserted in the README and implemented nowhere.

---

## 11 · Documentation notes

There is one document. It contains no falsifiable technical claim, so there is
nothing to check it against.

| Element | Status |
|---|---|
| Mechanism description | Four bullets and a five-word pipeline |
| Scoring rule | Absent |
| Data format | Absent |
| Baseline model | Absent |
| Evaluation sets | Absent |
| Hardware requirements | Absent |
| Dependencies | Absent |
| Miner / validator software | Absent |
| Website | Chain field is empty |

---

## 12 · Verdict

**Subnet 119 is, as published today, a README.**

I want to be precise rather than dismissive. The stated goal — rewarding
traceable training-data improvements for educational AI, scored on accuracy,
reasoning, calibration, age-appropriateness and safety — is a legitimate and
under-served problem. The document is literate and the domain framing is
sensible. Someone thought about what to say.

But an incentive network is a mechanism, and **no mechanism has been published**.
There is no definition of a data patch, no submission path, no baseline, no
evaluation set, no scoring function, no weight rule, and no software for either
role. The GitHub account was created yesterday and the repository today, with one
commit and no code. On chain there are zero commitments, and six validators
unanimously direct 100 % of the miner pool to the owner's own UID.

That combination puts SN119 in a different category from the other pre-launch
subnets in this folder. **SN78 UMI** is not live either — but it ships a
2,683-line whitepaper, 251 tests, and a type-level guarantee that it *cannot*
set weights until its gates pass. **SN25 UR** is not live on mainnet — but it
ships ~18,000 lines of specification, an audited contract suite at 75/75, and a
four-year-old product with real users. Both refuse to pay themselves while
incomplete. SN119 has none of that documentation and is taking the emission
anyway.

**I am not alleging bad faith**, and a project can be one day old and still be
real — code may land next week. But on today's evidence there is nothing to
evaluate, nothing to mine, and no way for an outsider to check any claim made.

### Recommended path

1. **Do not register and do not buy α on this thesis.** Not because $0.13 is a
   risk, but because a UID grants access to nothing that exists.
2. **Ask the three questions in §6.2 publicly**, in the linked Bittensor Discord
   channel. They are answerable in a paragraph if the work exists.
3. **Re-check in 30 days.** The single decisive signal is whether *code* appears
   in the repository — not more documentation.
4. **Watch one number:** any UID other than UID 0 showing non-zero incentive.
   Until that changes, this subnet has never paid a miner.
5. **If the problem domain interests you now**, SN92, SN103, SN123 and SN79 all
   ship code, pay miners today, and let you start this week.

---

## 13 · Sources

**Code**
- https://github.com/capabilityforge-next/capabilityforge @ `33e2ade`
  ("Initial commit", 2026-09-09 17:30 +0800) — `README.md` (32 lines),
  `.gitignore` (2 lines), `images/logo.png`, `images/intro.jpg`
- Local: `/root/Bittensor/119/capabilityforge`

**GitHub API** (fetched 2026-09-09)
- `/users/capabilityforge-next` — type `User`, created **2026-09-08**, 1 public repo
- `/repos/capabilityforge-next/capabilityforge` — created **2026-09-09T13:06:28Z**,
  0 stars, 0 forks, language `null`
- `/orgs/capabilityforge-next` — **404 Not Found** (it is a user account, not an org)

**Chain** (finney, block ~9,047,000)
- `Subtensor.subnet(119)`, `metagraph(119)`, `weights(119)`, `recycle(119)`,
  `get_subnet_hyperparameters(119)`, `SubnetIdentitiesV3(119)`
- `get_all_commitments(119)` — **0 commitments**

**Price reference**
- TAO ≈ $256 → α ≈ $0.71 at 0.002774 TAO/α
