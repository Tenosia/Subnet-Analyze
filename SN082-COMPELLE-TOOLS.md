# SN82 tooling — `compelle-watch` & `compelle-lab`

Two tools built for mining **Compelle, Bittensor netuid 82**. They solve the two halves of the problem:

| Tool | Question it answers | Runs |
| --- | --- | --- |
| **`compelle-watch`** | *What is happening on the subnet right now?* | continuously, as a service |
| **`compelle-lab`** | *Is my strategy actually good enough?* | on demand, offline |

> **Why two?** SN82 gives you **one commitment per UID, permanently** — a new commitment hash wipes your Elo back to 1000 *and* resets your king-of-the-hill streak ([`validator.py:568`](compelle-validator/compelle/validator.py#L568)). So all experimentation must happen **before** you register. `compelle-lab` is where you experiment; `compelle-watch` is how you know when to move.

Companion analysis: [SN82-COMPELLE-ANALYSIS.md](SN082-COMPELLE.md).

---

## Contents

1. [The subnet in one page](#1-the-subnet-in-one-page)
2. [compelle-watch](#2-compelle-watch)
3. [compelle-lab](#3-compelle-lab)
4. [Data sources & APIs](#4-data-sources--apis)
5. [The workflow, end to end](#5-the-workflow-end-to-end)
6. [Operations](#6-operations)
7. [Design notes & limits](#7-design-notes--limits)

---

## 1. The subnet in one page

Compelle pairs miners in **Pro/Con LLM debates**. You do not run a model — you commit a **written debate strategy** on chain, and validators use it as the system prompt for their debater. Judges score the transcript; Elo moves; the king takes **100% of miner emission**.

Constants both tools mirror from validator **v0.5.0** (`compelle-watch/lib/koth.py` cites the source line for each):

| Constant | Value | Meaning |
| --- | --- | --- |
| `KOTH_DEFENSE_MARGIN` | **200.0** | challenger must lead the king's Elo by this |
| `KOTH_DETHRONE_EPOCHS` | **20** | …and hold it this many consecutive epochs (~24 h) |
| `KOTH_FIGHT_TOPICS` | **100** | title fight = 100 topics × 2 seats = **200 games** |
| `KOTH_FIGHT_ALPHA` | **0.01** | significance bar (→ **117 of 200** wins needed) |
| `KOTH_FIGHT_MIN_DECIDED` | **80** | fewer decided = inconclusive, king holds |
| `KOTH_TAIL_EPOCHS` | 5 | deposed king keeps 5% this long |
| `ELIGIBILITY_WINDOW_BLOCKS` | **200** | commit within ~40 min of registering, **every update too** |
| `MAX_STRATEGY_BYTES` | **65,536** | resolved strategy cap |
| `ELO_K_FACTOR` / `ELO_INITIAL` | 32.0 / 1000.0 | standard Elo |
| `EPOCH_SECONDS` | 4320 | 72-minute epochs |
| `MAX_TURNS` | 5 | per side |
| `DEBATER_MODEL` | `zai-org/GLM-5.2-TEE` | validator-supplied |
| `JUDGE_PANEL` | `DeepSeek-V3.2-TEE`, `GLM-5.1-TEE` | 2-model panel, majority |

Network baseline from `/api/stats` (**389,118 debates**): `pro_win_pct 37.7` · `con_win_pct 47.1` · `concession_pct 9.2`.

---

## 2. `compelle-watch`

**Goal:** know the state of the crown race without watching a website, and get told when something changes that affects your plan.

Location: `/root/compelle-watch/` · Service: `compelle-watch.service` · Port: **8082**

### Run

```bash
systemctl status compelle-watch          # already enabled at boot
journalctl -u compelle-watch -f          # live log

compelle-watch status                    # terminal summary
compelle-watch alerts -n 30              # recent alerts
compelle-watch collect --chain           # force one cycle incl. chain read
compelle-watch render > board.html       # static HTML snapshot
compelle-watch serve --port 8082         # run in foreground (service does this)
```

### Dashboard

```
http://46.225.140.58:8082
```

| Route | Returns |
| --- | --- |
| `/` | the board (auto-refresh 60 s, light/dark toggle) |
| `/strategies` | index of all mirrored strategies |
| `/strategy?uid=N` | one miner's full strategy, rendered |
| `/strategy/raw?uid=N` | that strategy as `text/plain` |
| `/api/snapshot` | the whole current snapshot as JSON |
| `/api/alerts` | alert feed as JSON |
| `/api/strategies` | strategy index as JSON |
| `/healthz` | `{"ok":true,"age_s":N}` — 503 if the snapshot is stale |

Panels: **stat tiles** (king, crown pay/day, field size, Elo spread, entry cost, α price) · **Race to the crown** (top contenders as progress across the +200 margin, target marked) · **Goal to be winner** (the three gates with live numbers, top right) · **Miner board** (all UIDs, Elo bars, gap to crown, strategy size — click a UID to read it) · **Alerts** · **Epochs & validators** · **Upstream watch** (config.json, commits, tags, live topics).

### Alerts

Written to `state/alerts.jsonl` + `state/alerts.log`, and shown in the dashboard feed.

| Kind | Severity | Fires when |
| --- | --- | --- |
| `crown_flip` | **critical** | the weight-holding hotkey changes |
| `crown_vacant` | **critical** | nobody holds weight |
| `challenger_over_bar` | **critical** | a rival clears king Elo + 200 (gate 1) |
| `config_change` | **critical** | `compelle/config.json` commit — the consensus contract |
| `challenger_near` | high | a rival comes within 50 Elo of the bar |
| `strategy_change` | high | a UID's strategy hash changes (slot turned over) |
| `tier_change` | high | real ↔ ineligible (intent classifier, or window miss) |
| `repo_release` | high | new git tag |
| `weights_failing` | high | ≥6 of last 20 epochs failed `set_weights` |
| `epoch_stall` | high | no epoch for >2× cadence |
| `earning_uids` | high | count of earning UIDs changes (normally 1) |
| `reg_closed` | high | registration closed on netuid 82 |
| `elo_leader` | medium | the Elo leader changes (≠ the king) |
| `topics_rotated` | medium | topic gist revision changed |
| `repo_commit` | medium | new validator commit |
| `miner_leave`, `reg_cost`, `alpha_price` | medium | roster / cost / price moves |
| `miner_join`, `crown_seen`, `watch_start` | info | — |

### Strategy mirror

Every cycle writes all rivals' full strategies to disk:

```
/root/compelle-watch/strategies/
  index.json              uid, hotkey, tier, elo, weight, bytes, sha256, file
  all_strategies.json     the same + full strategy text
  uid-014_5EUAgjbvyLHT.txt   one .txt per miner  (60 files, ~6 MB)
  archive/<sha12>.txt     content-addressed history
```

Files are only rewritten when the content hash changes, so steady-state IO is near zero. **This mirror is what `compelle-lab` competes against.**

### Layout

```
compelle-watch/
  compelle-watch          CLI entry point
  lib/sources.py          all collectors (HTTP + chain subprocess)
  lib/collect.py          builds one snapshot, derives crown maths
  lib/koth.py             validator constants + binomial significance
  lib/alerts.py           snapshot diffing → alert rules
  lib/strategies.py       strategy mirror to disk
  lib/store.py            atomic snapshot/alert persistence
  lib/render.py           HTML dashboard + strategy viewer
  lib/server.py           HTTP server + background collect loop
  state/                  snapshot.json, previous.json, alerts.*
```

---

## 3. `compelle-lab`

**Goal:** find out whether a strategy beats the king **before** you spend a registration and lock yourself in forever.

Location: `/root/compelle-lab/`

### What makes it trustworthy

The lab loads the validator's **own `compelle/config.json`** at runtime. It does not reimplement the game — it reuses:

- the exact `game_prompt` (with `{topic} {side} {strategy} {context} {date}`)
- the exact `judge_prompt` (with `{topic} {transcript}`)
- the same debater model and 2-model judge panel
- 5 turns per side, temp 0.6, 3072 max tokens per turn
- the same Δ concession rule (symbol + ≥50 chars ends the debate in the opponent's favour)
- the same `Elo` class, K=32, initial 1000, draw penalty 1.6
- the same thinking-tag stripping and `[Speaker]: text` transcript format

Upgrade the validator checkout and the lab follows automatically.

### Setup

```bash
export COMPELLE_API_KEY=cpk_...      # Chutes
# or
export COMPELLE_API_KEY=sk-or-...    # OpenRouter
```

Provider is auto-detected from the key prefix. **You pay for lab inference** (validators pay for the real thing — mining itself needs no key).

### Commands

```bash
cd /root/compelle-lab

./lab check --a strategies/mine.txt          # FREE — run before anything
./lab topics -n 10                           # what the subnet is debating now
./lab cost --topics 8                        # estimate spend + wall time

./lab fight --a strategies/mine.txt --b king --topics 8
./lab gauntlet --a strategies/mine.txt --rivals 5 --topics 4
```

Strategy references accept **three forms**: a local file path, `uid:N` (any live miner from the mirror), or `king` (whoever currently holds weight).

**`check`** — free, offline, no API. Validates size cap, invisible/directional Unicode, control characters, and the four intent-classifier tripwires (fake transcript markers, verdict declarations, judge impersonation, self-scoring rubrics). Run it before every commit.

**`fight`** — head-to-head. Every topic is played **both seats**, so the Con advantage (47.1% vs 37.7% network-wide) cancels. This is the same construction the validator uses for a title fight, and the only honest way to compare two strategies.

**`gauntlet`** — your strategy against the top N live miners, with a summary table.

### Reading the output

```
                              mine            king-uid15
  ------------------------------------------------------
  wins                           9                     5
  losses                         5                     9
  draws                          2                     2
  conceded away                  0                     1
  as Pro (w/n)                 4/8                   3/8
  as Con (w/n)                 5/8                   2/8
  win rate (decided)         64.3%                 35.7%
  Elo                       1041.2                 958.8
  ------------------------------------------------------
  games 16  decided 14  voids 0
  Elo delta (mine - king-uid15): +82.4
  >>> short of the +200 crown margin by 117.6
```

Read **`as Pro` vs `as Con` separately** — a strategy that only wins from Con is fragile, because seats are balanced across the tournament. `conceded away` is a direct loss cause worth 9.2% of all debates network-wide.

The Elo figure starts both sides at 1000 over one small sample; it is a **head-to-head strength signal**, not a predicted on-chain rating. On chain, Elo accumulates across the whole field over many epochs.

Results are saved to `results/<tag>-<timestamp>.json` including full transcripts, so you can read *why* a debate was lost.

### Registration tool

`register-and-commit.py` does registration and commitment **in one process**, because the 200-block window is where people lose their burn.

```bash
# validate the payload before any TAO moves
/root/beam/.venv/bin/python register-and-commit.py \
  --wallet mycold --hotkey myhot \
  --commit "gist:<id>/<40-hex-sha>" --dry-run

# go live
/root/beam/.venv/bin/python register-and-commit.py \
  --wallet mycold --hotkey myhot \
  --commit "gist:<id>/<40-hex-sha>" --max-burn-tao 1.0
```

Before spending anything it: enforces the exact `gist:<id>/<40-hex-sha>` form (a bare `gist:<id>` is rejected by the validator's anti-swap rule), fetches the pinned revision, checks the resolved size against 65,536 bytes, scans for invisible Unicode, and reads the live burn. After registering it prints your deadline block and retries the commit up to 5×, aborting loudly if fewer than 3 blocks remain.

### Layout

```
compelle-lab/
  lab                        CLI entry point
  register-and-commit.py     the 40-minute window, done safely
  lib/harness.py             LLM client, debate loop, judge panel, Elo
  lib/arena.py               head-to-head, tournaments, reports
  strategies/                your candidates
  results/                   saved matchups incl. transcripts
```

---

## 4. Data sources & APIs

### Consumed by `compelle-watch`

| Source | Endpoint | Cadence | Used for |
| --- | --- | --- | --- |
| Compelle miners | `https://compelle.com/api/miners` | 5 min | uid, hotkey, tier, Elo, weight, **full strategy text** |
| Compelle status | `https://compelle.com/api/status` | 5 min | last epoch, validator version |
| Compelle epochs | `https://compelle.com/api/epochs` | 5 min | epoch history, `set_weights` outcomes |
| GitHub commits | `api.github.com/repos/compelle/compelle-validator/commits` | 5 min | validator changes |
| GitHub — config only | `…/commits?path=compelle/config.json` | 5 min | **consensus-contract changes** |
| GitHub tags | `…/tags` | 5 min | releases |
| Topics gist | `api.github.com/gists/60e5f119…` | 5 min | live motions, rotation revision |
| Bittensor chain | `finney`, netuid 82 | every 6th cycle | price, burn, block, incentive, permits, immunity |

GitHub is unauthenticated (60 req/hr per IP); the tool spends 4 per cycle, well inside budget.

Chain reads run as a `nice -n 19` subprocess against `/root/beam/.venv/bin/python` (bittensor 10.5.0 already installed there) — no second install, and a slow RPC can never stall the collector.

### Other useful Compelle endpoints (not polled)

| Endpoint | Returns |
| --- | --- |
| `/api/stats` | lifetime aggregate — `pro_win_pct`, `con_win_pct`, `concession_pct`, debate counts |
| `/api/games` | recent games with winner, reason, topic, turns |
| `/api/epoch/<block>` | one epoch: validators, miners, all games |

### Consumed by `compelle-lab`

| Source | Used for |
| --- | --- |
| `/root/Bittensor/compelle-validator/compelle/config.json` | prompts, models, turn limits, Elo constants |
| `/root/compelle-watch/strategies/` | rival strategies (`uid:N`, `king`) |
| `/root/compelle-watch/state/snapshot.json` | live topic rotation |
| Chutes `llm.chutes.ai/v1/chat/completions` **or** OpenRouter | debate + judge inference |

Local dependency: **the lab reads the watcher's mirror.** Run `compelle-watch collect` if the mirror is stale.

### Zero credentials for mining itself

Mining SN82 needs **no API key, no server, no GPU**. The only key anywhere here is for `compelle-lab`'s offline testing, and it never leaves your machine.

---

## 5. The workflow, end to end

```
  PHASE 0  research                          FREE
    read every rival's strategy in compelle-watch/strategies/
    read the judge prompt (it is the complete spec of what wins)
    ./lab topics ; curl /api/games
        │
  PHASE 1  build 4–6 candidate families      FREE
    different reasoning algorithms, not wording variants
    field median is ~41 KB — write a specification, not a paragraph
        │
  PHASE 2  test offline                      ~$0.10 per matchup
    ./lab check      → must PASS everything
    ./lab fight --b king
    ./lab gauntlet --rivals 5
    iterate until you beat the king on BOTH seats
        │
  PHASE 3  publish the gist                  FREE
    single file, copy the full 40-hex revision SHA
    ./register-and-commit.py --dry-run
        │
  PHASE 4  register + commit                 ~$0.11
    ONE command, inside the 200-block window
        │
  PHASE 5  monitor                           FREE
    compelle-watch status / alerts
    DO NOT re-commit — it wipes Elo and the streak
```

### The three gates to the crown

```
1. Elo ≥ king + 200
2. hold it 20 consecutive epochs (~24 h)
3. win 117 of 200 title-fight games (α = 0.01)
```

The dashboard's top-right panel computes all three live.

---

## 6. Operations

### Service

```bash
systemctl status  compelle-watch
systemctl restart compelle-watch
journalctl -u compelle-watch -f
curl -s localhost:8082/healthz
```

Unit is deliberately subordinate to the BEAM fleet:

```ini
Nice=19
IOSchedulingClass=idle
CPUQuota=25%
MemoryMax=400M
OOMScoreAdjust=800     # beam sits at -900; the kernel reaps this first
```

Steady state ≈ **30–37 MB** RAM.

### Disk

| Path | Size |
| --- | --- |
| `compelle-watch/strategies/` | ~6 MB (60 strategies + archive) |
| `compelle-watch/state/` | ~5 MB (alerts capped at 2000 entries) |
| `compelle-lab/` | <1 MB + saved results |

### Network exposure

Port 8082 binds `0.0.0.0`. To make it local-only (VSCode forwarding still works):

```bash
sed -i 's/--port 8082/--host 127.0.0.1 --port 8082/' /etc/systemd/system/compelle-watch.service
systemctl daemon-reload && systemctl restart compelle-watch
```

### Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| `no snapshot yet` | `compelle-watch collect --chain` |
| chain fields blank | beam venv unreachable; `/root/beam/.venv/bin/python -c "import bittensor"` |
| dashboard stale, `/healthz` 503 | collector wedged — `systemctl restart compelle-watch` |
| `lab` says strategy not found | run `compelle-watch collect` to refresh the mirror |
| `lab` LLM errors | key wrong prefix, out of credit, or model renamed in `config.json` |
| alerts silent after upgrade | expected — the first cycle after a wipe re-seeds and emits `watch_start` |

---

## 7. Design notes & limits

**What the lab does *not* model.** Swiss pairing order, chain-derived topic selection, cross-validator stake weighting (`stake ** 0.25`), the validator's tie **deliberation** round, and Yuma consensus. None of these change who wins a debate, but they do mean lab Elo ≠ on-chain Elo. A tie in the lab is reported as a draw directly, making it marginally more draw-prone than production — the safe direction for a screening tool.

**Non-determinism is inherent.** The validator's own README says it plainly: debater and judge calls run at non-zero temperature, and validators converge over many epochs via Yuma rather than agreeing per-epoch. Small samples are noisy; a 16-game result is a signal, not a verdict.

**Constants drift.** Everything mirrored in `koth.py` cites its validator source line. When `config_change` or `repo_release` fires, re-check them — that alert exists precisely because the consensus contract can move.

**The strategy mirror is a snapshot, not history.** Rewrites happen only on hash change, and `archive/` keeps content-addressed copies, but a strategy that appears and vanishes between two 5-minute cycles is missed.

**Elo leader ≠ king.** The most counter-intuitive property of SN82, and both tools surface it deliberately: the king has been as low as **#10 by Elo** while taking 100% of emission. Ranking high is not the goal; clearing three gates is.

---

*Built 2026-08-19 against compelle-validator v0.5.0. Subnet analysis: [SN82-COMPELLE-ANALYSIS.md](SN082-COMPELLE.md).*
