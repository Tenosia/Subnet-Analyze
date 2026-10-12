# SN108 — ChipForge (Decentralised Silicon Design)

**Analysed:** 2026-09-30 · **Chain read live from finney at block 9,181,361** · TAO ≈ $304.89

| | |
|---|---|
| **netuid** | 108 (`ChipForge`, symbol `Զ`) |
| **Operator** | **Tatsu** (`TatsuProject`) · `hi@chipforge.io` |
| **Tagline** | *"Miners anywhere compete to build chips that accelerate AI."* |
| **Owner hotkey** | `5HjH8ZqfoWG6SS6UTvLHEmQVBA6gjTCdpcy7wveoDGWSPZwk` — **is UID 0, the "burn" UID** |
| **Owner coldkey** | `5FBwsAvvKjhe7bGSdtVSAaxm7huJAcWFZRb9WRpJJmrVUvoB` |
| **Code** | https://github.com/TatsuProject/ChipForge_SN108 — **MIT**, ~4,900 lines of Python |
| **Local checkout** | `/root/Bittensor/108/ChipForge_SN108` (HEAD `6591d91`, 2026-09-25) |
| **Site / docs** | https://www.chipforge.io/ · https://docs.chipforge.io/ (Mintlify, ~60 pages) |
| **Challenge server** | `https://api.chipforge.io` — **unreachable from a general host** (see §4.2) |
| **EDA server** | https://github.com/TatsuProject/chipforge_eda_server (separate repo) |
| **Registered at block** | **9,111,253 ≈ 2026-09-20 — 9.7 days old** |
| **Price** | 0.004442 TAO/Զ ≈ **$1.35** · tao_in **τ510** · alpha_in 114,749 · **alpha_out 0** |
| **Emission** | **`alpha_out_emission = 0`, `moving_price = 0` — the subnet emits nothing yet** |
| **UIDs** | 62 registered · 1 with incentive (owner) · 3 vpermits · 2 with dividends |
| **On-chain commitments** | 0 |
| **Registration cost** | **τ0.5 ≈ $152** — expensive, ~1,000× the τ0.0005 floor most subnets sit at |

> **Read this first.** Three things determine whether SN108 is worth your time, and
> none of them are in the marketing:
>
> **1. Nothing is being emitted.** `alpha_out_emission = 0` and `moving_price = 0.0`.
> A dTAO subnet earns emission in proportion to its *moving* price, and a
> newly-registered subnet's moving price starts at zero and only begins tracking
> spot after the owner's `start_call`. SN108 is 9.7 days old and still at zero.
> For comparison, SN76 Ormas sat in exactly this state when I analysed it on
> 2026-09-14; at 24.7 days old it now emits normally. **SN108 will probably start
> — but it has not, and until it does no miner earns anything.**
>
> **2. When it does start, the shipped default pays the winner 10 %, not 100 %.**
> The docs say winner-takes-all. [`neurons/validator.py:825`](#) sets
> `--miner_emission_percentage` default to **10.0**, and the remaining 90 % is
> weighted to **UID 0 — which is the owner's own hotkey.** See §3.3. This is the
> single most important number in the repo and it is not in any document.
>
> **3. The entry fee is τ0.5 ≈ $152.** That is unusually high, and you pay it to
> join a subnet that currently pays zero.

---

## 1 · Goal — in plain terms

ChipForge is the first Bittensor subnet where **the deliverable is silicon**.

> *"Participants download specifications, leverage AI tools, and submit complete
> Verilog/SystemVerilog implementations. The highest-quality designs earn rewards
> while contributing to fully manufacturable chips."*

The structure is a rolling design contest:

```
Challenge posted  →  you download the spec + test cases
                  →  you write a RISC-V CPU core in Verilog/SystemVerilog
                  →  you zip it (≤10 MB) and submit via the CLI
                  →  validators pull it and hand it to the ChipForge EDA server
                  →  Verilator simulates it; OpenLane synthesises it (sky130nm PDK)
                  →  you get one number: Overall Score, 0–1
                  →  highest score above threshold takes the emission stream
```

Current challenge categories are **RISC-V based processors** and **AI
accelerators**. The roadmap runs from an RV32IMCK core (Phase 1, mid-November)
through an NPU (Phase 2) to **tape-out and fabrication readiness by November 2026**
(Phase 5). The owner claims a completed, validated **RV32IMCK core** already
exists — full ISA compliance at 120 MHz on sky130nm, with a claim that a 22–28 nm
node *"will definitely give a clock close to 1 GHz."*

This is a genuinely different subnet from anything else in this folder. It is not
ML. It is **hardware engineering**, and the skill it wants is not transferable
from any other subnet here.

---

## 2 · What you do as a miner

There is no model to train and no server to keep online for scoring. The loop is
manual and CLI-driven:

```bash
python3 python_scripts/miner_cli.py status        # is a challenge active?
python3 python_scripts/miner_cli.py download      # get spec + test cases
#   ... you design an RV32 CPU core in Verilog/SystemVerilog ...
python3 python_scripts/miner_cli.py submit solution.zip --dry_run    # validate
python3 python_scripts/miner_cli.py submit solution.zip --check_status
```

**The submission** is a ZIP containing `.v`/`.sv` sources, optionally a testbench,
constraints, and a README.

| Constraint | Value |
|---|---|
| Max ZIP size | **10 MB** |
| Submissions per hotkey per challenge | **5** |
| Challenge-server rate limit | **5 requests per IP per hour** |
| Batch download window | 10 minutes |
| Batch evaluation window | 20 minutes |

**Five submissions per challenge is the constraint that shapes everything.** You
cannot iterate against the scorer. Each of your five shots must be a considered
improvement, verified locally first, because a wasted submission is 20 % of your
budget for that challenge.

### The axon is theatre

`neurons/miner.py` serves an axon, but the only synapse in the protocol is
`SimpleMessage` (a 17-line file), and the handler does nothing but acknowledge
`CHALLENGE_ACTIVE:` and `BATCH_COMPLETE:` notifications with `"OK"`. The
blacklist function returns `False, ""` — **it blacklists nobody**.

Scoring never touches your axon. It is a convenience notification channel, and
you could poll the challenge server instead. Note it anyway for device planning:
the shipped miner calls `axon.serve()` and `axon.start()`, so it wants a public
IP and an open port.

---

## 3 · Scoring — the part that decides everything

### 3.1 The formula

From [`docs.chipforge.io/whitepaper/methodology/dynamic`](https://docs.chipforge.io/whitepaper/methodology/dynamic):

```
IF F_c ≥ Threshold_Func :
    O_c = ( W_Func·F_c  +  W_Area·Area  +  W_Perf·P_c ) / Total_W

IF F_c <  Threshold_Func :
    O_c = 0
```

**The functionality gate is hard.** Below the threshold your score is exactly
zero no matter how small or fast your design is. Area and speed only matter once
the core is correct enough.

The three components:

| Metric | How it is measured | Formula |
|---|---|---|
| **Functionality** `F_c` | Test suites run on the official RISC-V ISA simulator **SPIKE** to make the golden output; your design runs the same tests under **Verilator** | `F_c = N_correct / N_total` (instructions matching golden), 0–1 |
| **Performance** `P_c` | **IPC** from simulation × **F_max** from OpenLane timing analysis | `IPS = IPC × F_max`, normalised against a benchmark IPS |
| **Area** | Synthesised with **OpenLane/Yosys** targeting the **sky130nm PDK** | inversely proportional to µm², normalised against a per-challenge target |
| **Power** | **Not evaluated.** Reserved for the NPU phase | — |

> ⚠️ **`W_Func`, `W_Area`, `W_Perf` and `Threshold_Func` are loaded from a
> server-side `weights.json`.** They are not in the repo, not on chain, and not
> published. The operator can re-weight the competition at any time and you
> would not know until your score moved.

### 3.2 Two ratchets, not one

To get paid, a submission must clear **both** of these — and this is where the
code says more than the docs:

```python
# neurons/validator_utils/batch_processor.py:202-208
if hotkey and overall_score > new_best_score:                # ratchet 1: local best
    if overall_score > evaluation_baseline_snapshot:         # ratchet 2: server baseline
        new_best_score = overall_score
        new_champion = hotkey
    else:
        logger.info("... beats previous but does NOT beat baseline snapshot - not eligible")
```

- **Ratchet 1** — the current challenge-wide best score, tracked by the validator.
- **Ratchet 2** — `winner_baseline_score`, fetched **fresh from the challenge
  server before every evaluation**. The server sets this number. You cannot see
  it, and it can move between your submissions.

And in the emission manager, the winner's score **never resets downward**:

```python
# emission_manager.py — winner period expires
self.current_winner = None
# DO NOT reset current_winner_score - keep it for future comparisons
```

So after a champion is crowned at score X and their reward window lapses, **every
future submission — including the champion's own — must strictly exceed X.**
Equality burns:

```python
if current_best_score == self.current_winner_score:
    logger.debug("... already rewarded, now burning")
```

The docs call this the **Mandatory Improvement Rule**:

> *"a Miner who wins the emission is guaranteed that reward for a minimum of 48
> hours… **However, after that 48-hour period, the current winning Miner must
> submit an even higher-scoring solution than their previous best to remain
> eligible.**"*

**This is a treadmill, not a throne.** Winning once buys you 48 hours. Staying
paid requires beating yourself, forever, five submissions at a time.

### 3.3 ⚠️ The 10 % default — docs say 100 %, code says 10

The whitepaper is unambiguous that this is winner-takes-all with real-time
emission switching. The code is not:

```python
# neurons/validator.py:825
parser.add_argument("--miner_emission_percentage", type=float, default=10.0,
```

```python
# tests/test_config.py:40
assert config.miner_emission_percentage == 10.0
```

The test **pins** the default at 10. And `weight_manager.set_winner_weights`
splits accordingly:

```python
miner_fraction = miner_emission_percentage / 100.0     # 0.10
burn_fraction  = 1.0 - miner_fraction                  # 0.90
uids    = [0, winner_uid]
weights = [burn_fraction, miner_fraction]              # [0.90, 0.10]
```

Meanwhile `emission_manager.py:47` carries a comment reading
`"Value comes from --miner_emission_percentage CLI arg (hardcoded default: 100)."`
— **the comment contradicts the actual default in the same repository.**

**And UID 0 is not a burn address.** The chain says UID 0's hotkey is
`5HjH8ZqfoWG6SS6UTvLHEmQVBA6gjTCdpcy7wveoDGWSPZwk`, which is exactly the subnet
owner's hotkey, carrying 602,328 Զ of stake. Weight sent to UID 0 mints alpha to
the owner. Calling it "burned" throughout the code and logs
(`f"{100 - miner_emission_percentage:.0f}% burned (UID 0)"`) is, at minimum,
misleading.

So on the shipped defaults, a miner who designs a winning RISC-V core takes
**10 % of the miner pool for 48 hours**, and the owner takes the other 90 %.
Validators *can* pass `--miner_emission_percentage 100`; nothing in the repo
suggests they do, and the test suite asserts they don't.

### 3.4 Four emission phases

`EmissionManager.should_burn_emissions()` runs a state machine:

| Phase | Behaviour |
|---|---|
| `initial_burn` | Everything to UID 0 until the first scoring submission appears |
| `normal` | Active challenge with a qualifying submission → pay the champion |
| `winner_reward` | Champion's guaranteed window (`TOTAL_HOURS_FOR_WINNER_REWARD`) |
| `burn_until_submission` | Window lapsed, nobody has beaten the standing score → **everything to UID 0** |

Note the default window in code is **0.5 hours**:

```python
self.local_winner_reward_hours = float(os.getenv('TOTAL_HOURS_FOR_WINNER_REWARD', '0.5'))
```

`.env.example` sets `48`, and the challenge server can override it live via
`update_winner_reward_hours_from_server()`. **The operator controls how long you
stay paid, from a server you cannot see.** A validator that starts without an
`.env` gives its winner 30 minutes.

The fallback in every unhandled case is the same: `return True` — burn.

---

## 4 · Live state

### 4.1 The chain

| | |
|---|---|
| Registered | block **9,111,253 ≈ 2026-09-20**, **9.7 days ago** |
| `alpha_out_emission` | **0.0** |
| `moving_price` | **0.0** (spot price 0.004442) |
| `sum(E)` across all UIDs | **0.0** |
| UIDs | 62 of 256 |
| UIDs with incentive | **1** — UID 0, the owner, at `I = 1.0000` |
| Validator permits | 3 |
| UIDs with dividends | 2 — UID 1 (97.66 %, 375,156 stake), UID 2 (2.34 %) |
| Weight setters | **2** — UID 1 and UID 2, **both 100 % → UID 0** |
| On-chain commitments | **0** |
| tao_in | **τ510** — very thin |
| subnet_volume | 1.05 |

Both live validators are doing exactly what `set_burn_weights()` does: 1.0 to
UID 0, 0.0 to everyone else. That is the `initial_burn` phase working as designed
— there has been no qualifying submission. **61 registered UIDs, and not one of
them has produced a scoring design.**

### 4.2 The challenge server does not answer

`api.chipforge.io` resolves (`3.151.67.131`, AWS) but **every connection attempt
times out** — HTTPS/443, HTTP/80 and HTTP/8000, three retries each, 15 s timeouts:

```
try1 https 443 -> 000 (15.00s)   http :8000 -> 000   http :80 -> 000
```

This may be an IP allowlist for registered participants rather than an outage —
I cannot distinguish the two from outside. But it is worth weighing against the
README, which documents a **"5 requests per IP per hour"** public rate limit,
implying a publicly reachable service. **Before you spend τ0.5, confirm in
Discord that you can reach the challenge server**, because without it you cannot
download a challenge or submit anything.

The marketing site and the docs site are both up and substantial.

### 4.3 Validators are couriers, not judges

This is structurally important. The validator does **not** compute your score:

```python
# api_client.py:_transform_eda_response
return {
    'overall_score':      final_score.get('overall', 0.0),
    'functionality_score': final_score.get('func_score', 0.0),
    ...
}
```

`final_score` comes straight out of the **ChipForge EDA server's** response. The
validator downloads your ZIP, POSTs it to the EDA server, and relays whatever
number comes back. If the EDA server errors or times out, the validator calls
`_generate_fallback_evaluation()` — which marks your submission **0.0 across the
board**, not "unknown":

```python
"""Generate fallback evaluation when EDA server fails - marks as FAILED"""
```

**An infrastructure failure on the operator's side is scored as your design
failing.** With five submissions per challenge, an EDA outage during your batch
window costs you a fifth of your budget and you have no recourse in the code.

Between the server-side `weights.json`, the server-side `winner_baseline_score`,
the server-controlled reward window, and the EDA server producing the only score
that matters, **the decentralised part of this subnet is the design work. The
judging is centralised in full.**

---

## 5 · What a miner would earn

**Today: nothing.** `alpha_out_emission = 0`.

When emission starts, on shipped defaults:

```
your share = 10 % of the miner pool, for 48 hours, if your score is the strict maximum
           = 0 % otherwise
```

There is no second place. There is no proportional tail. `calculate_weights()`
gives `weight 1` to `sorted_miners[0]` and nothing to anyone else.

### Costs

| Item | Cost |
|---|---|
| **Registration** | **τ0.5 ≈ $152** — three orders of magnitude above the τ0.0005 floor |
| GPU | **None** |
| Machine (stated) | 8 cores / 24 GB / 30 GB disk minimum; 16 cores / 32 GB recommended |
| Local EDA toolchain | Verilator, Yosys, Icarus, OpenLane + sky130 PDK — free, but a real setup |
| **The real cost** | **Your time.** A competitive RV32IMCK core is weeks of skilled RTL work |
| Iteration budget | **5 submissions per challenge.** No cheap retries |

**The risk profile is unusually harsh.** You pay $152 up front, invest weeks of
specialist engineering, get five shots, and if someone else's score is one
ten-thousandth higher you earn exactly zero. Then, if you do win, you have 48
hours before you must beat your own best.

---

## 6 · How to become a winner

### Priority 1 — Do not register until emission is on

Check `alpha_out_emission` and `moving_price` yourself before spending τ0.5:

```bash
btcli subnet show --netuid 108
```

Both are zero right now. Registering today buys you a seat in a contest with no
prize pool, and you cannot reach the challenge server to compete anyway. The
watchdog in this folder now tracks exactly this — you will see it in
[`notification.md`](notification.md) the day it changes.

### Priority 2 — Clear the functionality gate before optimising anything

`O_c = 0` below `Threshold_Func`. A beautifully small, blazingly fast core that
fails 3 % of the instruction trace scores **zero**, and loses to a bloated slow
core that passes. Get `F_c` to 1.0 against SPIKE first; tune area and F_max
second. This is the opposite of the instinct most optimisation-minded engineers
have.

### Priority 3 — Reproduce the scorer locally, exactly

You get five submissions. Build the operator's pipeline on your own machine:

- **SPIKE** to generate golden outputs for the instruction traces
- **Verilator** for the DUT run → gives you `F_c` and IPC
- **OpenLane/Yosys @ sky130nm** for area (µm²) and `F_max` → gives you `Area` and,
  with IPC, `IPS = IPC × F_max`

You can compute your own `F_c`, `Area` and `P_c` before ever submitting. What you
**cannot** compute is `O_c`, because `W_Func`/`W_Area`/`W_Perf` live in a
server-side `weights.json` you have never seen. **Ask for those weights in
Discord.** Without them you are optimising a weighted sum with unknown weights —
and the sensible hedge is to maximise `F_c` to 1.0 and then push whichever of
area or IPS is cheaper for your design.

### Priority 4 — Understand that you are racing a ratchet, not a field

61 UIDs and zero qualifying submissions means the standing bar is currently
**nothing**. The first person to submit a working RV32I core takes the crown.
That is a genuine first-mover opening — *if* the subnet turns on.

But the same code means the crown decays. Plan for the 48-hour cycle from the
start: hold improvements in reserve rather than shipping your best work
immediately, because you will need a strictly better score within two days of
winning, and you only get five submissions per challenge to produce it.

### Priority 5 — Ask these five questions before committing

1. **When is `start_call` being made?** Emission is zero and `moving_price` is 0.
2. **Is `api.chipforge.io` IP-allowlisted?** I cannot reach it on any port.
3. **What is `--miner_emission_percentage` actually set to on the live
   validators** — 10 or 100? The repo default and its test say 10.
4. **What is in `weights.json`** — the three metric weights and `Threshold_Func`?
5. **What is `TOTAL_HOURS_FOR_WINNER_REWARD` on the server** — 48, or the code's 0.5?

`hi@chipforge.io` and the Discord channel are on the chain identity.

---

## 7 · Rules you must keep

| Rule | Consequence |
|---|---|
| `F_c ≥ Threshold_Func` | Below it, `O_c = 0` regardless of area and speed |
| Beat the challenge-wide best **strictly** | A tie is burned, not shared |
| Beat the server's `winner_baseline_score` | Fails ratchet 2 → *"not eligible for reward"* |
| Beat **your own** previous best after 48 h | Mandatory Improvement Rule; otherwise burn |
| ≤ 5 submissions per hotkey per challenge | Hard cap; wasted attempts don't come back |
| ZIP ≤ 10 MB, valid archive, `.v`/`.sv` inside | Rejected by the CLI before upload |
| ≤ 5 challenge-server requests per IP per hour | Rate-limited |
| Ed25519-signed calls, timestamp within 10 min | Replay protection; signature failures reject |
| Keep your coldkey off the ban list | `banned_coldkeys.json` — permanent and per-challenge bans, synced from the server; a banned winner's emission is burned entirely |

---

## 8 · Device conditions

| | |
|---|---|
| **GPU** | **None required** |
| CPU | 8 physical cores minimum, **16 recommended**; 2.5 GHz min, 3.0 GHz recommended |
| RAM | **24 GB minimum, 32 GB recommended** |
| Disk | 30–35 GB |
| OS | Ubuntu 20.04 min / 24.04 recommended |
| Bandwidth | 30 Mbps down / 20 Mbps up |
| Python | **3.12**, and **Bittensor 10.5.0 pinned** — the repo explicitly stays on the 10.x line because *"Bittensor 11 removed the `axon`/`dendrite`/`Synapse` networking layer"* |
| Network | The shipped miner calls `axon.serve()`/`axon.start()` → public IP + open port (notifications only, not scoring) |
| **The real requirement** | **An RTL engineer** and a local Verilator + Yosys + OpenLane + sky130 PDK toolchain |

> **Against your BEAM box (2 cores / 3.7 GB, Hetzner CX22):** **not viable.** The
> stated minimum is 8 cores and 24 GB, and that is an honest number — OpenLane
> place-and-route on a CPU core is memory-hungry and slow. You would need a
> materially larger machine, and separately you would need the RTL skills, which
> are the actual barrier.
>
> Note also the **Bittensor 10.5.0 pin**: this will conflict with any environment
> you have on the 11.x line, so it wants its own conda env at minimum.

---

## 9 · Third-party conditions

| Dependency | Role | Note |
|---|---|---|
| **`api.chipforge.io` challenge server** | Hosts challenges, accepts submissions, sets `winner_baseline_score`, controls the reward window | **Operator-run, closed-source, currently unreachable from here.** Single point of failure |
| **ChipForge EDA server** | **Produces the only score that matters** | Operator-run at https://github.com/TatsuProject/chipforge_eda_server. A failure or timeout scores your design **0.0** |
| **`weights.json`** | `W_Func`, `W_Area`, `W_Perf`, `Threshold_Func` | Server-side, **unpublished**, changeable at any time |
| **SPIKE** (RISC-V ISA simulator) | Generates golden reference output | Open source; you can run it locally |
| **Verilator** | Functional simulation → `F_c`, IPC | Open source |
| **OpenLane / Yosys + sky130 PDK** | Synthesis, P&R, timing → area, `F_max` | Open source (Google/SkyWater) |
| **Tatsu** | Subnet owner, validator operator, challenge server, EDA server, and **UID 0** | Every judging component is theirs |
| **finney** | Registration, weights | **Currently emitting nothing** |

---

## 10 · Risks

1. **The subnet emits nothing.** `alpha_out_emission = 0`, `moving_price = 0`,
   `sum(E) = 0`. Nine days in.

2. **Registration costs τ0.5 ≈ $152** — ~1,000× the usual floor — to join a
   subnet that currently pays zero and whose submission endpoint I cannot reach.

3. **The winner's default share is 10 %, not 100 %.** The whitepaper says
   winner-takes-all; `validator.py:825` and `test_config.py:40` say 10, and the
   other 90 % goes to UID 0.

4. **UID 0 is the owner's hotkey, not a burn address.** Everything the code and
   logs describe as "burned" is credited to the owner's own stake.

5. **A code comment contradicts the code.** `emission_manager.py:47` says
   *"hardcoded default: 100"*; the actual default is 10.

6. **The challenge server is unreachable** on 443, 80 and 8000. Possibly an
   allowlist, possibly down — either way, unverifiable from outside.

7. **All judging inputs are operator-controlled and unpublished:** the metric
   weights, the functionality threshold, the qualifying baseline, the reward
   window duration, and the EDA server that computes the score.

8. **An operator-side EDA failure scores your design 0.0**, indistinguishably
   from a broken design, and costs one of your five submissions.

9. **Five submissions per challenge** with an unknown scoring function is a very
   thin iteration budget.

10. **The mandatory improvement ratchet never resets downward.** Once a score is
    set, it stands as the bar even after the winner is cleared, so the subnet can
    fall into permanent `burn_until_submission` if the standing score is too high
    for anyone to beat.

11. **`Threshold_Func` can be set to make the subnet unwinnable** and there is no
    on-chain record of its value. Zero commitments means nothing is published.

12. **The default reward window in code is 0.5 hours**, not the 48 advertised, and
    the server can change it live.

13. **Documentation quality is poor in the repo** (see §11) even though the
    external docs site is good.

14. **Skill illiquidity.** Weeks of RTL work for a subnet-specific challenge is
    not transferable to any other subnet in this folder if SN108 stalls.

15. **Bittensor 10.5.0 pin** — the repo cannot move to 11.x without rewriting its
    networking layer, so it is on a deprecated SDK line.

---

## 11 · Documentation notes

Split personality: **an excellent external docs site and a careless repository.**

**Good** — [docs.chipforge.io](https://docs.chipforge.io/) is a ~60-page Mintlify
whitepaper with the actual scoring formula, normalisation method, per-metric
methodology (SPIKE/Verilator/OpenLane named explicitly), the winner-takes-all
emission loop, a five-phase roadmap with dates, and a market analysis. Genuinely
more scoring detail than most subnets in this folder publish. Serves `llms.txt`.

**Bad** — three of the four files in `docs/`:

| File | Problem |
|---|---|
| `docs/Technical_Guide.md` | **Copy-pasted from a different Tatsu subnet.** It is the *Document Understanding Subnet* guide: it tells you to `git clone Document_Understanding_Subnet`, `apt-get install tesseract-ocr`, install a **YOLO checkbox detector**, and register on **netuid 54 / testnet 236**. Nothing in it relates to chip design. A miner following `docs/Technical_Guide.md` ends up on the wrong subnet |
| `docs/running_on_mainnet.md` | Unmodified `bittensor-subnet-template` boilerplate — tells you how to *create a subnet*, not how to mine this one |
| `docs/running_on_testnet.md`, `docs/running_on_staging.md` | Same boilerplate |

So the only repo documentation that describes ChipForge is `README.md` and
`MINER_CLI_COMMANDS.md`. The README is decent — it documents the CLI, the
constraints, the rate limits, the batch windows, and states winner-takes-all
plainly.

**Also worth noting**, to the operator's credit, the README does *not* hide the
burn mechanic: *"Emission burning occurs when no submissions exceed quality
thresholds"* and *"Only submissions that beat the current challenge-wide best
score receive rewards."* Both are accurate. What is missing everywhere is the
10 % split and the fact that UID 0 is the owner.

**Engineering quality is reasonable:** MIT licensed, ~4,900 lines, 7 test modules
(config, environment, live chain, protocol, signing, transport, weight manager),
pinned `requirements-lock.txt`, a documented reason for staying on Bittensor 10.x,
crash-recovery logic in the emission manager, and structured `evaluation_details`
returned to miners so they can diagnose failures (Verilator build logs, OpenLane
area/fmax/wns). That last one is a real courtesy that most subnets skip.

---

## 12 · Verdict

**The most technically ambitious subnet in this folder, attached to the most
operator-controlled scoring system in it.**

The ambition is real and I do not want to undersell it. Every other subnet here
produces bits — a model, a signal, a classification, a git branch. ChipForge is
trying to produce **silicon**, with a tape-out target of November 2026, and the
scoring method is the genuine industry one: SPIKE for golden reference, Verilator
for functional simulation, OpenLane on the sky130 PDK for area and timing. The
PPA+F formula is published with its actual algebra. The hard functionality gate
is the correct design choice. And the owner has apparently already validated an
RV32IMCK core at 120 MHz. Nobody else in this folder is attempting anything like
this.

**But look at who decides what you earn.** The metric weights and the
functionality threshold live in a `weights.json` you cannot read. The qualifying
baseline is fetched from the operator's server before every evaluation. The
length of your reward window is pushed live from the same server. The only score
that matters is computed by the operator's EDA server, and validators just relay
it — if that server times out, your design is recorded as a **0.0 failure**. There
are zero on-chain commitments, so none of this is auditable. The decentralised
part of ChipForge is the labour. The judgment is entirely centralised.

**Then there is the 10 %.** The whitepaper promises winner-takes-all with
real-time emission switching. The shipped validator default sends the winner
**10 %** and routes **90 % to UID 0** — which the chain shows is the owner's own
hotkey with 602,328 Զ staked, not a burn address. A comment three files away
insists the default is 100. I do not know whether the live validators override
it; I do know the repo's own test suite asserts the value is 10. **Anyone
considering weeks of RTL work here should get that number confirmed in writing
first.**

And right now none of it is live. Emission is zero, `moving_price` is zero, 61
UIDs have produced no qualifying submission, both validators are weighting 100 %
to the owner, and I cannot reach the challenge server on any port. SN76 Ormas
looked exactly like this sixteen days ago and has since started normally, so the
zero is probably a matter of time rather than abandonment — but "probably" is
doing real work in that sentence, and the τ0.5 entry fee makes guessing expensive.

### Recommended path

1. **Do not register yet.** τ0.5 ≈ $152 for a seat in a contest with no prize
   pool and no reachable submission endpoint. Wait for `alpha_out_emission > 0`.
2. **Ask the five questions in §6.5 in Discord** — especially the real
   `miner_emission_percentage` and the contents of `weights.json`. The answers
   change whether this is worth weeks of your time.
3. **If you are not an RTL engineer, stop here.** This is not a subnet you can
   enter with general ML or ops skill, and the skills do not transfer out.
4. **If you are**, build the local toolchain now — SPIKE, Verilator, OpenLane +
   sky130 — while it is free to do so. With 61 UIDs and zero qualifying
   submissions, the first working RV32I core takes an uncontested crown.
5. **Budget for the treadmill, not the throne.** 48 hours per win, five
   submissions per challenge, and a ratchet that never falls. Hold improvements
   in reserve.
6. **Watch three numbers:** `alpha_out_emission` going non-zero, a UID other than
   0 showing incentive, and the challenge server answering. The watchdog now
   tracks the repo, `chipforge.io` and the chain identity for exactly this.

---

## 13 · Sources

**Code** (MIT, HEAD `6591d91`, 2026-09-25)
- https://github.com/TatsuProject/ChipForge_SN108
- Local: `/root/Bittensor/108/ChipForge_SN108`
- `README.md` (388 ln), `MINER_CLI_COMMANDS.md` (256 ln), `chipforge/protocol.py` (17 ln),
  `neurons/miner.py` (416 ln), `neurons/validator.py` (848 ln),
  `neurons/validator_utils/api_client.py` (978 ln), `emission_manager.py` (419 ln),
  `weight_manager.py` (241 ln), `batch_processor.py` (297 ln),
  `banned_coldkeys.py` (140 ln), `python_scripts/miner_cli.py` (731 ln), 7 test modules
- Referenced: https://github.com/TatsuProject/chipforge_eda_server

**Key code citations**
- `neurons/validator.py:825` — `--miner_emission_percentage` default **10.0**
- `tests/test_config.py:40` — asserts the default is **10.0**
- `neurons/validator_utils/emission_manager.py:47` — comment claiming default **100**
- `emission_manager.py:37` — `TOTAL_HOURS_FOR_WINNER_REWARD` default **'0.5'**
- `weight_manager.py:57-60` — burn = weight 1.0 → UID 0
- `batch_processor.py:202-208` — the two-ratchet eligibility test
- `api_client.py:_generate_fallback_evaluation` — EDA failure scores **0.0**

**Docs** (fetched 2026-09-30)
- https://docs.chipforge.io/llms.txt (~60 pages)
- `/whitepaper/methodology/dynamic` — the `O_c` formula and `Threshold_Func` gate
- `/whitepaper/methodology/detailed` — SPIKE, Verilator, OpenLane, `F_c = N_correct/N_total`, `IPS = IPC × F_max`
- `/whitepaper/methodology/normal` — 0–1 normalisation
- `/whitepaper/incentive/loop` — winner-takes-all, 48-hour guarantee, Mandatory Improvement Rule
- `/whitepaper/incentive/game` — integrity claims
- `/whitepaper/progress/risc` — RV32IMCK core, 120 MHz @ sky130nm
- `/whitepaper/roadmap/ph1`–`ph5` — through tape-out, November 2026
- https://www.chipforge.io/ — 200 OK
- `https://api.chipforge.io` — **unreachable**, 443/80/8000, 3 retries each

**Chain** (finney, block 9,181,361)
- `Subtensor.subnet(108)`, `metagraph(108)`, `weights(108)`, `recycle(108)`,
  `get_all_commitments(108)`, `SubnetIdentitiesV3(108)`
- `alpha_out_emission = 0`, `moving_price = 0`, `sum(E) = 0`, registered block 9,111,253
- UID 0 hotkey == `owner_hotkey`, stake 602,328 Զ
- recycle = **τ0.5**

**Price reference**
- TAO = **$304.89** (CoinGecko, 2026-09-30) → Զ ≈ $1.35 at 0.004442 TAO/Զ
