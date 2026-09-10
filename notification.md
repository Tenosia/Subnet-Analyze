# Change Notifications

Automated watch log for every subnet in this folder — **GitHub repositories** and
**on-chain state**. Newest entries first.

Run the watcher with:

```bash
python3 watch.py          # detect changes and append them below
python3 watch.py --init   # reset the baseline without logging
```

## What is watched

**GitHub — 58 repositories across 38 subnets.** Detection uses `git ls-remote`,
which reads every ref (branches, tags, HEAD) and is **not subject to the GitHub
API rate limit**, so all repos can be checked on every run. The REST API is called
only *after* a change is detected, to describe what landed. Repos are tagged
*(referenced dependency)* where they belong to a third party rather than the
subnet team.

A repo becoming **private**, **deleted** or **newly public** is logged too — that
transition has already mattered twice in this folder.

**Websites — the URL each subnet publishes on chain.** 35 sites tracked. The URL
is read from the chain identity each run, so a newly-added subnet is covered
automatically and a *change of URL* is itself reported. The fingerprint is
deliberately coarse — HTTP status, `<title>`, the set of link targets, and text
length in 5 % buckets — because most of these are dashboards with live counters
and hashing the page would fire every hour. It reports outages, redesigns,
retitles and new/removed pages; it does not report a ticking number.

**Chain identity — GitHub repo, website and description.** Any change is logged.
This is the earliest repurposing signal there is: the identity fields move before
the subnet name does.

**Chain — all 39 subnets, read directly from finney.** This is the same data
taostats displays, taken from the source rather than scraped, so it cannot break
on a page redesign and needs no API key. Per subnet:

| Field | Logged when |
|---|---|
| Earning UIDs | any change |
| Top earner (UID) | any change — flagged if it becomes the owner's own hotkey |
| Top earner incentive | moves ≥ 0.05 |
| On-chain commitments | any change |
| Owner capture % | moves ≥ 2.0 pp |
| α price (USD) | moves ≥ 15 % |
| Registered UIDs | any change |
| **Subnet name** | any change — the repurposing signal |

α price is deliberately given a wide band: it moves constantly, and only a large
swing is news. Everything else is reported on any movement.

## How to read an entry

Each run appends one dated section with up to three parts — **GitHub** (commit
subjects that landed), **Chain** (the metric that moved, before → after) and
**Websites** (what changed about the site). An empty run writes nothing.

Both this log and the [comparison table](compare-table.md) are served as a live
dashboard on port 8090 of this host.

---

<!-- entries below, newest first -->

## 2026-09-10 13:53 UTC

### Websites

- **SN101 Tag101** · [http://tag101.ai](http://tag101.ai)
    - site links changed (8 → 8 targets)


## 2026-09-10 13:41 UTC — watcher tuned (no subnet change)

The first 21 hourly runs surfaced two sources of noise, now filtered:

- **Feature/PR branch churn.** Active repos carry thousands of transient refs
  (`ditto-assistant/ditto-subnet` has ~2,950; `leadpoet/leadpoet` ~418) and were
  reporting "refs changed, HEAD unchanged" every hour. The watcher now keys on
  **HEAD plus tags only**, so a real commit or release is reported and branch
  churn is not.
- **A rotating top earner.** On contested subnets the leading UID legitimately
  changes each tempo — SN28 SayGM alone flapped between UIDs 3/65/72/91/221
  overnight. A top-earner change is now reported only when the **owner-status
  flips** or the **lead incentive moves ≥ 0.05**, so a genuine takeover still
  shows and a normal reshuffle does not.

Baseline re-established. Entries below this line use the tighter rules.


## 2026-09-10 13:18 UTC

### GitHub

- **SN14** · [`latent-to/cacheon`](https://github.com/latent-to/cacheon)
    - branches/tags changed (136 → 139 refs); HEAD unchanged
- **SN25** · [`urfoundation/sn`](https://github.com/urfoundation/sn)
    - 2 new commit(s), 4 file(s) changed
    - · fix(sim-testnet): bind carried evidence actions to deployed companion
    - · chore(testnet): pin carried evidence target repair source
- **SN25** · [`urnetwork/server`](https://github.com/urnetwork/server)
    - 2 new commit(s), 3 file(s) changed
    - · accept authenticated IRQ self-check fields
    - · Merge branch 'main' of github.com:urnetwork/server
- **SN71** · [`leadpoet/leadpoet`](https://github.com/leadpoet/leadpoet)
    - branches/tags changed (418 → 418 refs); HEAD unchanged
- **SN118** · [`ditto-assistant/ditto-subnet`](https://github.com/ditto-assistant/ditto-subnet)
    - branches/tags changed (2948 → 2954 refs); HEAD unchanged

### Chain

- **SN28 SayGM**
    - **earning UIDs 59 → 42** (-17)
    - **top earner changed: UID 221 → UID 3** — now the **owner's own hotkey**
    - owner capture 50.3% → 56.9%
- **SN43 Graphite**
    - **top earner changed: UID 20 → UID 177**
    - owner capture 90.4% → 59.0%
- **SN79 MVTRX**
    - **earning UIDs 223 → 221** (-2)


## 2026-09-10 12:18 UTC

### Chain

- **SN28 SayGM**
    - **earning UIDs 65 → 59** (-6)
    - owner capture 43.3% → 50.3%
- **SN43 Graphite**
    - **top earner changed: UID 74 → UID 20** — now the **owner's own hotkey**
    - owner capture 59.0% → 90.4%
- **SN79 MVTRX**
    - **earning UIDs 225 → 223** (-2)
- **SN105 Beam**
    - **earning UIDs 213 → 214** (+1)
    - **top earner changed: UID 87 → UID 238**
- **SN107 Minos**
    - **top earner changed: UID 37 → UID 11**


## 2026-09-10 11:18 UTC

### GitHub

- **SN71** · [`leadpoet/leadpoet`](https://github.com/leadpoet/leadpoet)
    - 6 new commit(s), 1 file(s) changed
    - · docs: explain the open source agent competition
    - · docs: state midnight continuous evaluation timing
    - · docs: note per-hotkey admission and daily capacity
    - · Merge remote-tracking branch 'origin/main' into codex/competition-readme-final-20260910
    - · Merge remote-tracking branch 'origin/main' into codex/competition-readme-final-20260910
    - · Merge remote-tracking branch 'origin/main' into codex/competition-readme-final-20260910
- **SN118** · [`ditto-assistant/ditto-subnet`](https://github.com/ditto-assistant/ditto-subnet)
    - 1 new commit(s), 2 file(s) changed
    - · fix(coding): tolerate protected probe credentials (#1774)

### Chain

- **SN34 BitMind**
    - on-chain commitments 362 → 361 (-1)
- **SN54 Yanez**
    - **earning UIDs 108 → 107** (-1)
- **SN105 Beam**
    - **earning UIDs 214 → 213** (-1)
- **SN107 Minos**
    - **top earner changed: UID 5 → UID 37**


## 2026-09-10 10:18 UTC

### GitHub

- **SN25** · [`urfoundation/sn`](https://github.com/urfoundation/sn)
    - 2 new commit(s), 3 file(s) changed
    - · crv4: accept reviewed runtime 455 validator stake layout
    - · testnet: bind release lock to runtime 455 stake compatibility
- **SN38** · [`chronollm/sn38`](https://github.com/chronollm/sn38)
    - branches/tags changed (44 → 47 refs); HEAD unchanged
- **SN71** · [`leadpoet/leadpoet`](https://github.com/leadpoet/leadpoet)
    - 3 new commit(s), 7 file(s) changed
    - · Accept valid empty Arena Full results
    - · Scope baseline promotion guard to chain
    - · Strengthen chain scope baseline regressions

### Chain

- **SN18 Zeus**
    - top earner incentive 0.4110 → 0.6051
- **SN28 SayGM**
    - **earning UIDs 45 → 65** (+20)
    - **top earner changed: UID 72 → UID 221**
- **SN43 Graphite**
    - **top earner changed: UID 155 → UID 74**
- **SN61 RedTeam**
    - **earning UIDs 40 → 39** (-1)
- **SN105 Beam**
    - **earning UIDs 215 → 214** (-1)
- **SN107 Minos**
    - **top earner changed: UID 56 → UID 5**


## 2026-09-10 09:18 UTC

### GitHub

- **SN25** · [`urfoundation/sn`](https://github.com/urfoundation/sn)
    - branches/tags changed (293 → 296 refs); HEAD unchanged
- **SN25** · [`urnetwork/connect`](https://github.com/urnetwork/connect)
    - 1 new commit(s), 2 file(s) changed
    - · 2026.9.10-1042298530 ip security and blocker update
- **SN25** · [`urnetwork/server`](https://github.com/urnetwork/server)
    - branches/tags changed (2631 → 2634 refs); HEAD unchanged
- **SN25** · [`urnetwork/sdk`](https://github.com/urnetwork/sdk)
    - branches/tags changed (2403 → 2406 refs); HEAD unchanged
- **SN71** · [`leadpoet/leadpoet`](https://github.com/leadpoet/leadpoet)
    - 3 new commit(s), 5 file(s) changed
    - · Remove retired Source Add fallback from champion caps
    - · Bind champion cap cleanup to protected source
    - · Provision Full epoch cutover authority
- **SN118** · [`ditto-assistant/ditto-subnet`](https://github.com/ditto-assistant/ditto-subnet)
    - branches/tags changed (2947 → 2947 refs); HEAD unchanged

### Chain

- **SN28 SayGM**
    - **earning UIDs 46 → 45** (-1)
    - **top earner changed: UID 3 → UID 72**
    - owner capture 55.4% → 43.4%
- **SN34 BitMind**
    - **earning UIDs 139 → 141** (+2)
- **SN43 Graphite**
    - **top earner changed: UID 20 → UID 155**
    - owner capture 90.4% → 58.9%
- **SN79 MVTRX**
    - **earning UIDs 222 → 225** (+3)
- **SN105 Beam**
    - **earning UIDs 214 → 215** (+1)


## 2026-09-10 08:18 UTC

### GitHub

- **SN71** · [`leadpoet/leadpoet`](https://github.com/leadpoet/leadpoet)
    - branches/tags changed (418 → 418 refs); HEAD unchanged

### Chain

- **SN28 SayGM**
    - **earning UIDs 65 → 46** (-19)
    - **top earner changed: UID 72 → UID 3** — now the **owner's own hotkey**
    - owner capture 49.4% → 55.4%
- **SN34 BitMind**
    - on-chain commitments 363 → 362 (-1)
- **SN43 Graphite**
    - **top earner changed: UID 155 → UID 20** — now the **owner's own hotkey**
    - owner capture 58.9% → 90.4%
- **SN54 Yanez**
    - **earning UIDs 104 → 108** (+4)
- **SN79 MVTRX**
    - **earning UIDs 228 → 222** (-6)
- **SN107 Minos**
    - **top earner changed: UID 37 → UID 56**


## 2026-09-10 07:18 UTC

### GitHub

- **SN118** · [`ditto-assistant/ditto-subnet`](https://github.com/ditto-assistant/ditto-subnet)
    - 1 new commit(s), 5 file(s) changed
    - · chore(release): v0.250.0 [skip ci]

### Chain

- **SN28 SayGM**
    - **earning UIDs 33 → 65** (+32)
    - **top earner changed: UID 91 → UID 72**
    - owner capture 54.5% → 49.4%
- **SN43 Graphite**
    - **top earner changed: UID 102 → UID 155**
- **SN54 Yanez**
    - **earning UIDs 105 → 104** (-1)
- **SN79 MVTRX**
    - **earning UIDs 225 → 228** (+3)
- **SN101 Tag101**
    - **earning UIDs 199 → 246** (+47)


## 2026-09-10 06:18 UTC

### GitHub

- **SN14** · [`latent-to/cacheon`](https://github.com/latent-to/cacheon)
    - availability changed: `timeout` → `ok`
- **SN25** · [`urfoundation/sn`](https://github.com/urfoundation/sn)
    - branches/tags changed (290 → 293 refs); HEAD unchanged
- **SN25** · [`urnetwork/connect`](https://github.com/urnetwork/connect)
    - 1 new commit(s), 2 file(s) changed
    - · 2026.9.9-1042199790 ip security and blocker update
- **SN25** · [`urnetwork/server`](https://github.com/urnetwork/server)
    - branches/tags changed (2628 → 2631 refs); HEAD unchanged
- **SN25** · [`urnetwork/sdk`](https://github.com/urnetwork/sdk)
    - branches/tags changed (2400 → 2403 refs); HEAD unchanged
- **SN71** · [`leadpoet/leadpoet`](https://github.com/leadpoet/leadpoet)
    - 4 new commit(s), 9 file(s) changed
    - · Classify complete unproven industry evidence
    - · Cover combined company fit insufficiency
    - · Protect fit insufficiency classification
    - · Advance competition stages when work is ready
- **SN79** · [`taos-im/sn-79`](https://github.com/taos-im/sn-79)
    - availability changed: `error` → `ok`
- **SN80** · [`openroboto-ai/openroboto-subnet`](https://github.com/openroboto-ai/openroboto-subnet)
    - availability changed: `timeout` → `ok`
- **SN80** · [`openroboto-ai/openroboto-evaluation`](https://github.com/openroboto-ai/openroboto-evaluation)
    - availability changed: `timeout` → `ok`
- **SN82** · [`compelle/compelle-validator`](https://github.com/compelle/compelle-validator)
    - availability changed: `timeout` → `ok`
- **SN118** · [`ditto-assistant/ditto-subnet`](https://github.com/ditto-assistant/ditto-subnet)
    - 3 new commit(s), 37 file(s) changed
    - · fix(preview): dispatch stack previews by hand and stop the slot leak (#1772)
    - · chore(deps): bump six pinned GitHub Actions to verified upstream tags (#1749)
    - · fix(ansible): fail the converge when a team member has no SSH key (#1761)

### Chain

- **SN34 BitMind**
    - on-chain commitments 364 → 363 (-1)
- **SN107 Minos**
    - **top earner changed: UID 24 → UID 37**
- **SN118 Ditto**
    - **top earner changed: UID 43 → UID 96**
- **SN120 Affine**
    - **top earner changed: UID 162 → UID 60**


## 2026-09-10 05:30 UTC

### GitHub

- **SN14** · [`latent-to/cacheon`](https://github.com/latent-to/cacheon)
    - availability changed: `ok` → `timeout`
- **SN25** · [`urfoundation/sn`](https://github.com/urfoundation/sn)
    - 2 new commit(s), 4 file(s) changed
    - · Retry bounded Substrate reads after historical capacity refusals
    - · Bind release lock to Substrate capacity recovery
- **SN25** · [`urnetwork/server`](https://github.com/urnetwork/server)
    - branches/tags changed (2626 → 2628 refs); HEAD unchanged
- **SN40** · [`RalphLabsAI/ralph-v2`](https://github.com/RalphLabsAI/ralph-v2)
    - 3 new commit(s), 9 file(s) changed
    - · The plan does not get to choose the margin
    - · Crown on the displayed metric, with persistence and a floor rule
    - · Merge pull request #15 from RalphLabsAI/feat/point-margin-persistence
- **SN71** · [`leadpoet/leadpoet`](https://github.com/leadpoet/leadpoet)
    - 3 new commit(s), 13 file(s) changed
    - · Document auditor archive override and protect official default
    - · Fix Full Arena score count evidence assembly
    - · Preserve validated page final URLs
- **SN79** · [`taos-im/sn-79`](https://github.com/taos-im/sn-79)
    - availability changed: `ok` → `error`
- **SN80** · [`openroboto-ai/openroboto-subnet`](https://github.com/openroboto-ai/openroboto-subnet)
    - availability changed: `ok` → `timeout`
- **SN80** · [`openroboto-ai/openroboto-evaluation`](https://github.com/openroboto-ai/openroboto-evaluation)
    - availability changed: `ok` → `timeout`
- **SN82** · [`compelle/compelle-validator`](https://github.com/compelle/compelle-validator)
    - availability changed: `ok` → `timeout`
- **SN118** · [`ditto-assistant/ditto-subnet`](https://github.com/ditto-assistant/ditto-subnet)
    - 3 new commit(s), 44 file(s) changed
    - · feat(validator): shadow router track for SN118 DittoBench (model-unlocked, big-four harnesses) (#1730)
    - · chore(release): v0.249.0 [skip ci]
    - · feat(coding): add protected Hippius capability probe (#1771)

### Chain

- **SN28 SayGM**
    - **earning UIDs 40 → 33** (-7)
    - **top earner changed: UID 72 → UID 91**
    - owner capture 42.5% → 54.5%
- **SN79 MVTRX**
    - **earning UIDs 221 → 225** (+4)
- **SN105 Beam**
    - **earning UIDs 213 → 214** (+1)
- **SN107 Minos**
    - **top earner changed: UID 5 → UID 24**


## 2026-09-10 04:18 UTC

### GitHub

- **SN25** · [`urfoundation/sn`](https://github.com/urfoundation/sn)
    - branches/tags changed (287 → 290 refs); HEAD unchanged
- **SN25** · [`urnetwork/server`](https://github.com/urnetwork/server)
    - branches/tags changed (2623 → 2626 refs); HEAD unchanged
- **SN25** · [`urnetwork/sdk`](https://github.com/urnetwork/sdk)
    - branches/tags changed (2397 → 2400 refs); HEAD unchanged
- **SN71** · [`leadpoet/leadpoet`](https://github.com/leadpoet/leadpoet)
    - 2 new commit(s), 5 file(s) changed
    - · Analyze restored parity data and retain storage failure causes
    - · Update restore checks for required clone analysis
- **SN118** · [`ditto-assistant/ditto-subnet`](https://github.com/ditto-assistant/ditto-subnet)
    - 7 new commit(s), 46 file(s) changed
    - · fix(infra): preserve postgres password on day-two converge (#1769)
    - · feat(infra): narrow coding postgres guest admission (#1770)
    - · feat(router): add shadow-only router starter kit and CI (#1705)
    - · chore(release): v0.248.0 [skip ci]
    - · feat(platform): grade router submissions in shadow mode without ranking them (#1707)
    - · feat(screening-protocol): screen shadow routers for held-out generalization (#1708)
    - · feat(coding-datagen): wire open datasets with rotating held-out sets (#1709)

### Chain

- **SN18 Zeus**
    - top earner incentive 0.5110 → 0.4110
    - owner capture 44.3% → 52.0%
- **SN28 SayGM**
    - **earning UIDs 61 → 40** (-21)
    - **top earner changed: UID 65 → UID 72**
- **SN34 BitMind**
    - on-chain commitments 365 → 364 (-1)
- **SN43 Graphite**
    - **top earner changed: UID 20 → UID 102**
    - owner capture 90.4% → 58.9%
- **SN54 Yanez**
    - **earning UIDs 104 → 105** (+1)
- **SN79 MVTRX**
    - **earning UIDs 220 → 221** (+1)
- **SN101 Tag101**
    - **earning UIDs 246 → 199** (-47)
- **SN107 Minos**
    - **earning UIDs 19 → 20** (+1)
- **SN124 Swarm**
    - on-chain commitments 847 → 849 (+2)


## 2026-09-10 03:18 UTC

### GitHub

- **SN25** · [`urfoundation/sn`](https://github.com/urfoundation/sn)
    - 4 new commit(s), 4 file(s) changed
    - · Preserve malformed Substrate response refusal during read recovery
    - · Bind testnet release lock to strict read error classification
    - · Allow shared recovery time after historical EVM capacity refusals
    - · Bind testnet release lock to historical EVM cooldown
- **SN25** · [`urnetwork/connect`](https://github.com/urnetwork/connect)
    - 1 new commit(s), 2 file(s) changed
    - · 2026.9.9-1042101210 ip security and blocker update
- **SN118** · [`ditto-assistant/ditto-subnet`](https://github.com/ditto-assistant/ditto-subnet)
    - 2 new commit(s), 46 file(s) changed
    - · feat(dashboard): apply the Ditto brand kit and typography kit (#1765)
    - · chore(release): v0.247.0 [skip ci]

### Chain

- **SN28 SayGM**
    - **earning UIDs 38 → 61** (+23)
    - **top earner changed: UID 72 → UID 65**
    - owner capture 49.1% → 42.9%
- **SN34 BitMind**
    - **earning UIDs 117 → 139** (+22)
    - on-chain commitments 364 → 365 (+1)
- **SN43 Graphite**
    - **top earner changed: UID 177 → UID 20** — now the **owner's own hotkey**
    - owner capture 58.9% → 90.4%
- **SN79 MVTRX**
    - **earning UIDs 222 → 220** (-2)
- **SN105 Beam**
    - **earning UIDs 212 → 213** (+1)
- **SN107 Minos**
    - **earning UIDs 20 → 19** (-1)
    - **top earner changed: UID 37 → UID 5**


## 2026-09-10 02:18 UTC

### GitHub

- **SN25** · [`urfoundation/sn`](https://github.com/urfoundation/sn)
    - 4 new commit(s), 4 file(s) changed
    - · Retry interrupted read-only Substrate calls on the shared client
    - · Bind testnet release lock to Substrate read recovery
    - · Declare the existing WebSocket dependency directly
    - · Refresh testnet lock after WebSocket dependency declaration
- **SN40** · [`RalphLabsAI/ralph-v2`](https://github.com/RalphLabsAI/ralph-v2)
    - branches/tags changed (21 → 22 refs); HEAD unchanged
- **SN71** · [`leadpoet/leadpoet`](https://github.com/leadpoet/leadpoet)
    - 5 new commit(s), 4 file(s) changed
    - · Repair homepage-bound domain conflicts
    - · Bind reviewed identity repair for attested release
    - · Classify cited noncanonical size as insufficient
    - · Bind final fit classification for release
    - · Accept company-bound exchange ticker stage proof
- **SN118** · [`ditto-assistant/ditto-subnet`](https://github.com/ditto-assistant/ditto-subnet)
    - branches/tags changed (2939 → 2945 refs); HEAD unchanged

### Chain

- **SN28 SayGM**
    - **top earner changed: UID 65 → UID 72**
    - owner capture 42.7% → 49.1%
- **SN43 Graphite**
    - **top earner changed: UID 74 → UID 177**
- **SN79 MVTRX**
    - **earning UIDs 221 → 222** (+1)
- **SN107 Minos**
    - **top earner changed: UID 99 → UID 37**


## 2026-09-10 01:18 UTC

### GitHub

- **SN25** · [`urfoundation/sn`](https://github.com/urfoundation/sn)
    - 2 new commit(s), 3 file(s) changed
    - · Retry public EVM historical read capacity refusals
    - · Bind testnet release to historical RPC retry repair
- **SN25** · [`urnetwork/connect`](https://github.com/urnetwork/connect)
    - 1 new commit(s), 2 file(s) changed
    - · 2026.9.9-1042000000 ip security and blocker update
- **SN25** · [`urnetwork/server`](https://github.com/urnetwork/server)
    - branches/tags changed (2620 → 2623 refs); HEAD unchanged
- **SN25** · [`urnetwork/sdk`](https://github.com/urnetwork/sdk)
    - branches/tags changed (2394 → 2397 refs); HEAD unchanged
- **SN71** · [`leadpoet/leadpoet`](https://github.com/leadpoet/leadpoet)
    - 1 new commit(s), 1 file(s) changed
    - · Remove retired API-source submission instructions
- **SN118** · [`ditto-assistant/ditto-subnet`](https://github.com/ditto-assistant/ditto-subnet)
    - 1 new commit(s), 5 file(s) changed
    - · fix(infra): default the Hetzner screener fleet to Ditto Inference (#1764)

### Chain

- **SN28 SayGM**
    - **earning UIDs 63 → 38** (-25)
- **SN34 BitMind**
    - **earning UIDs 110 → 117** (+7)
- **SN43 Graphite**
    - **top earner changed: UID 20 → UID 74**
    - owner capture 90.4% → 58.9%
- **SN54 Yanez**
    - **earning UIDs 103 → 104** (+1)
- **SN79 MVTRX**
    - **top earner changed: UID 208 → UID 64**


## 2026-09-10 00:18 UTC

### GitHub

- **SN25** · [`urfoundation/sn`](https://github.com/urfoundation/sn)
    - 2 new commit(s), 3 file(s) changed
    - · Fix bootstrap policy verification after activation
    - · Lock bootstrap policy resume verification repair
- **SN25** · [`urnetwork/connect`](https://github.com/urnetwork/connect)
    - branches/tags changed (2691 → 2692 refs); HEAD unchanged
- **SN25** · [`urnetwork/sdk`](https://github.com/urnetwork/sdk)
    - branches/tags changed (2393 → 2394 refs); HEAD unchanged
- **SN28** · [`taostat/gm-miner`](https://github.com/taostat/gm-miner)
    - branches/tags changed (411 → 411 refs); HEAD unchanged
- **SN78** · [`Umi-BitSign/umi`](https://github.com/Umi-BitSign/umi)
    - 1 new commit(s), 4 file(s) changed
    - · Fix Python 3.10 supervisor timeouts
- **SN118** · [`ditto-assistant/ditto-subnet`](https://github.com/ditto-assistant/ditto-subnet)
    - branches/tags changed (2938 → 2938 refs); HEAD unchanged

### Chain

- **SN28 SayGM**
    - **earning UIDs 39 → 63** (+24)
- **SN118 Ditto**
    - **top earner changed: UID 104 → UID 43**


## 2026-09-09 23:18 UTC

### GitHub

- **SN25** · [`urfoundation/sn`](https://github.com/urfoundation/sn)
    - 1 new commit(s), 1 file(s) changed
    - · Lock the reviewed soak candidate with manifest authentication repair
- **SN25** · [`urnetwork/connect`](https://github.com/urnetwork/connect)
    - 11 new commit(s), 9 file(s) changed
    - · Ignore evaluation epoch ping cancellations
    - · Bound network tests by forward progress
    - · API spec: the onboarding program contract
    - · API spec: onboarding and analytics as strict OpenAPI 3.1 — tags, camelCase operationIds, closed client-event o
    - · API spec: auth-client time_zone and locale land with the campaign engine; Brevo webhook tag, template_id, cust
    - · Spec: onboarding admin results and experiments endpoints as deployed
    - · API spec: points leaderboard seek_rank, prev_cursor and row position
    - · 2026.9.9-1041947070 ip security and blocker update
- **SN25** · [`urnetwork/server`](https://github.com/urnetwork/server)
    - branches/tags changed (2617 → 2620 refs); HEAD unchanged
- **SN25** · [`urnetwork/sdk`](https://github.com/urnetwork/sdk)
    - 8 new commit(s), 26 file(s) changed
    - · Onboarding program: plan-response tier/offer/experiments, offer issue, closed client events with a persisted q
    - · Onboarding: export the event flush interval as millis for gomobile; regenerate the C ABI and the TS types
    - · C ABI headers: the client event flush interval constant in millis
    - · C ABI: export the client event queue as a handle with its methods, and carry product_updates through the json 
    - · Auth client args: time_zone and locale for the onboarding campaign's local-time sends and template language
    - · Auth client args: time_zone and locale in the C ABI headers and the TS types; wire round-trip test
    - · Represent unavailable points epoch metrics
    - · Points leaderboard: seek to a rank, page both ways, scroll label tiers
- **SN28** · [`taostat/gm-miner`](https://github.com/taostat/gm-miner)
    - 1 new commit(s), 2 file(s) changed
    - · chore: release v0.4.17 (#249)
- **SN61** · [`RedTeamSubnet/RedTeam`](https://github.com/RedTeamSubnet/RedTeam)
    - branches/tags changed (248 → 248 refs); HEAD unchanged
- **SN71** · [`leadpoet/leadpoet`](https://github.com/leadpoet/leadpoet)
    - 6 new commit(s), 8 file(s) changed
    - · Reject superseded public and PE stage proof
    - · Keep prospective stage claims unavailable
    - · Keep Arena migration tests stable when migrations are added
    - · Reject future primary company-stage claims
    - · Block encoded Arena credential echoes
    - · Cover encoded miner-key echoes through provider routes
- **SN78** · [`Umi-BitSign/umi`](https://github.com/Umi-BitSign/umi)
    - 2 new commit(s), 3 file(s) changed
    - · Use a private pytest temp root in CI
    - · Fix bootstrap pilot replay permissions
- **SN118** · [`ditto-assistant/ditto-subnet`](https://github.com/ditto-assistant/ditto-subnet)
    - 6 new commit(s), 57 file(s) changed
    - · fix(infra): allow Terraform to manage screener IAP policy (#1762)
    - · fix(platform): show final policy rejection evidence only (#1763)
    - · feat(screener): route private review through Ditto Inference (#1693)
    - · chore(release): v0.246.0 [skip ci]
    - · fix(pylon): align weight reveals with stateful chain epochs (#1756)
    - · chore(release): v0.246.1 [skip ci]

### Chain

- **SN43 Graphite**
    - **top earner changed: UID 102 → UID 20** — now the **owner's own hotkey**
    - owner capture 58.9% → 90.4%
- **SN54 Yanez**
    - **earning UIDs 98 → 103** (+5)
- **SN76 nun**
    - registered UIDs 72 → 74
- **SN78 Umi**
    - **earning UIDs 1 → 0** (-1)
    - top earner incentive 1.0000 → 0.0000
    - owner capture 59.3% → 18.0%
- **SN79 MVTRX**
    - **earning UIDs 216 → 221** (+5)
- **SN82 Compelle**
    - on-chain commitments 1008 → 1007 (-1)
- **SN105 Beam**
    - **earning UIDs 211 → 212** (+1)
- **SN107 Minos**
    - **top earner changed: UID 36 → UID 99**


## 2026-09-09 22:18 UTC

### GitHub

- **SN14** · [`latent-to/cacheon`](https://github.com/latent-to/cacheon)
    - branches/tags changed (137 → 136 refs); HEAD unchanged
- **SN25** · [`urfoundation/sn`](https://github.com/urfoundation/sn)
    - 1 new commit(s), 7 file(s) changed
    - · Authenticate runtime manifests once per operation and parallelize independent slow tests
- **SN25** · [`urnetwork/server`](https://github.com/urnetwork/server)
    - 22 new commit(s), 131 file(s) changed
    - · Run Main predeploy tasks over LAN
    - · bringyourctl onboarding webhook-ensure: a disabled campaign is a plain refusal, not a panic
    - · fixes
    - · Distinguish unavailable points epoch metrics
    - · Discover Stripe subscriptions before account deletion
    - · Escalate sustained Subtensor stalls
    - · Points leaderboard: seek to any position, page in both directions
    - · Preserve published migration order in schema audit
- **SN40** · [`RalphLabsAI/ralph-v2`](https://github.com/RalphLabsAI/ralph-v2)
    - branches/tags changed (20 → 21 refs); HEAD unchanged
- **SN61** · [`RedTeamSubnet/RedTeam`](https://github.com/RedTeamSubnet/RedTeam)
    - 3 new commit(s), 4 file(s) changed
    - · feat: limit the number of unique reference commits based on configuration for compare all
    - · version: bump version to '4.10.4'.
    - · docs: update changelog version '4.10.4'
- **SN71** · [`leadpoet/leadpoet`](https://github.com/leadpoet/leadpoet)
    - 4 new commit(s), 4 file(s) changed
    - · Reject funding-service descriptions as company stage evidence
    - · Classify unproven identity evidence without retry
    - · Bind protected scorer to unproven identity classification
    - · Preserve retries for unresolved homepage transport failures
- **SN78** · [`Umi-BitSign/umi`](https://github.com/Umi-BitSign/umi)
    - 2 new commit(s), 29 file(s) changed
    - · Add audited bootstrap worker and directive feed
    - · Fix OCI archive annotation verification
- **SN118** · [`ditto-assistant/ditto-subnet`](https://github.com/ditto-assistant/ditto-subnet)
    - 5 new commit(s), 33 file(s) changed
    - · fix(ansible): install team SSH keys, so host access survives the bootstrap (#1759)
    - · feat(infra): admit native coding host to postgres (#1760)
    - · fix(infra): let screeners pull signed releases (#1754)
    - · chore(release): v0.245.0 [skip ci]
    - · feat(infra): grant the fleet x509 identity access to the Ditto review key (#1719)

### Chain

- **SN26 Perturb**
    - **top earner changed: UID 126 → UID 64**
- **SN28 SayGM**
    - **earning UIDs 49 → 39** (-10)
    - **top earner changed: UID 91 → UID 65**
- **SN43 Graphite**
    - **top earner changed: UID 20 → UID 102**
    - owner capture 90.4% → 58.9%
- **SN54 Yanez**
    - **earning UIDs 99 → 98** (-1)
- **SN71 Leadpoet**
    - **earning UIDs 78 → 1** (-77)
    - top earner incentive 0.7094 → 1.0000
    - owner capture 70.4% → 82.3%
- **SN79 MVTRX**
    - **earning UIDs 215 → 216** (+1)
- **SN107 Minos**
    - **top earner changed: UID 56 → UID 36**
- **SN118 Ditto**
    - **top earner changed: UID 43 → UID 104**


## 2026-09-09 21:18 UTC

### GitHub

- **SN14** · [`latent-to/cacheon`](https://github.com/latent-to/cacheon)
    - 1 new commit(s), 68 file(s) changed
    - · Add prefill qualification and dashboard throughput and latency metrics (#114)
- **SN25** · [`urfoundation/sn`](https://github.com/urfoundation/sn)
    - 3 new commit(s), 7 file(s) changed
    - · Restore retired alpha spending and raise approved reserve repair allowance
    - · Lock corrected alpha accounting and prioritize soak launch gate
    - · Refresh launch lock for incoming server checkpoint
- **SN71** · [`leadpoet/leadpoet`](https://github.com/leadpoet/leadpoet)
    - 9 new commit(s), 29 file(s) changed
    - · Guard Arena refill waits without owned work
    - · Keep infrastructure gap regression limited to one claim
    - · Require stage-specific scorer evidence
    - · Bind protected scorer workflow to stage proof correction
    - · Fix competition judge deadlines, failure retention, and daily capacity
    - · Merge remote-tracking branch 'origin/main' into codex/arena-miner-report2-20260909
    - · Allow capacity migration alongside read-only production snapshots
    - · Merge remote-tracking branch 'origin/main' into codex/competition-release-hardening-20260909
- **SN118** · [`ditto-assistant/ditto-subnet`](https://github.com/ditto-assistant/ditto-subnet)
    - 1 new commit(s), 4 file(s) changed
    - · fix(infra): include sysctl in native daemon path (#1758)

### Chain

- **SN28 SayGM**
    - **earning UIDs 52 → 49** (-3)
    - **top earner changed: UID 65 → UID 91**
- **SN34 BitMind**
    - on-chain commitments 365 → 364 (-1)
- **SN43 Graphite**
    - **top earner changed: UID 74 → UID 20** — now the **owner's own hotkey**
    - owner capture 58.9% → 90.4%
- **SN54 Yanez**
    - **earning UIDs 100 → 99** (-1)
- **SN61 RedTeam**
    - **earning UIDs 42 → 40** (-2)
- **SN79 MVTRX**
    - **earning UIDs 217 → 215** (-2)
- **SN107 Minos**
    - **top earner changed: UID 5 → UID 56**


## 2026-09-09 20:18 UTC

### GitHub

- **SN25** · [`urfoundation/sn`](https://github.com/urfoundation/sn)
    - 1 new commit(s), 3 file(s) changed
    - · Refresh launch source lock and parallel gate handoff
- **SN25** · [`urnetwork/server`](https://github.com/urnetwork/server)
    - 1 new commit(s), 6 file(s) changed
    - · preflight safe staging evaluation
- **SN36** · [`EpagoFoundation/epago`](https://github.com/EpagoFoundation/epago)
    - 13 new commit(s), 17 file(s) changed
    - · Prove a bridge term means the same thing in both papers
    - · Merge pull request #3 from EpagoFoundation/fix/bridge-sense-check
    - · Read sealed-pool paths from the operator's box, not the contract
    - · Merge pull request #4 from EpagoFoundation/fix/pool-paths-from-env
    - · Name the release a sealed generation still generates from
    - · Docs: say what the state directory holds and where the corpus comes from
    - · Merge pull request #5 from EpagoFoundation/fix/sealed-release-tasks
    - · Merge pull request #6 from EpagoFoundation/staging
- **SN71** · [`leadpoet/leadpoet`](https://github.com/leadpoet/leadpoet)
    - 5 new commit(s), 12 file(s) changed
    - · Recover historical Source Add allocation frontier
    - · Bind historical frontier recovery source
    - · Cover historical frontier projection pairs
    - · Accept retained Source Add allocation weights
    - · Allow bounded cold preparation in parity Fast rehearsal
- **SN78** · [`Umi-BitSign/umi`](https://github.com/Umi-BitSign/umi)
    - 1 new commit(s), 17 file(s) changed
    - · Add prerequisite-gated validator supervisor
- **SN118** · [`ditto-assistant/ditto-subnet`](https://github.com/ditto-assistant/ditto-subnet)
    - 2 new commit(s), 4 file(s) changed
    - · fix(infra): pin approved native Docker candidates (#1755)
    - · fix(infra): recover pinned native Docker packages (#1757)

### Chain

- **SN28 SayGM**
    - **earning UIDs 65 → 52** (-13)
    - **top earner changed: UID 72 → UID 65**
- **SN34 BitMind**
    - **earning UIDs 109 → 110** (+1)
- **SN36 Epago**
    - owner capture 61.7% → 63.9%
- **SN43 Graphite**
    - **top earner changed: UID 155 → UID 74**
- **SN47 Feval**
    - **earning UIDs 2 → 1** (-1)
    - top earner incentive 0.9027 → 1.0000
    - owner capture 78.8% → 82.4%
- **SN79 MVTRX**
    - **earning UIDs 216 → 217** (+1)
- **SN107 Minos**
    - **top earner changed: UID 37 → UID 5**
- **SN124 Swarm**
    - **top earner changed: UID 24 → UID 177**


## 2026-09-09 19:18 UTC

### GitHub

- **SN25** · [`urfoundation/sn`](https://github.com/urfoundation/sn)
    - 1 new commit(s), 4 file(s) changed
    - · Preserve gate identity on cancellation and refresh unused upgrade approval
- **SN36** · [`EpagoFoundation/epago`](https://github.com/EpagoFoundation/epago)
    - branches/tags changed (11 → 7 refs); HEAD unchanged


## 2026-09-09 19:12 UTC

### GitHub

- **SN36** · [`EpagoFoundation/epago`](https://github.com/EpagoFoundation/epago)
    - branches/tags changed (13 → 11 refs); HEAD unchanged


## 2026-09-09 19:10 UTC — baseline established

First run. No changes to report; this records the starting state that every later
run is compared against.

**GitHub:** 56 of 58 repositories reachable across 38 subnets.
Two are private and will be reported if that ever changes:
- SN103 · `Capcomp-AI/lora-merger-engine`
- SN120 · `AffineFoundation/affine-cortex`

**Chain:** 39 subnets snapshotted from finney.

### ⚠️ One finding from the first run

**SN36 has been renamed again — `automata` → `Epago`.** Netuid 36 has now carried
three identities in a matter of weeks:

| | |
|---|---|
| Was | `Leoma` — AI video generation (the subnet [`SN036-LEOMA.md`](SN036-LEOMA.md) describes) |
| Then | `automata` — 3 UIDs, `alpha_out = 0`, owner held 100 % |
| **Now** | **`Epago`** — *"THE OPEN INTELLIGENCE LAYER FOR HUMANS AND AGENTS"* |

New identity on chain: repo [`EpagoFoundation/epago`](https://github.com/EpagoFoundation/epago),
site [epago.ai](https://epago.ai/). Same owner hotkey and registration block as
`automata`, but **`alpha_out` has gone from 0 to 69,227** — it is now emitting.
Still 3 UIDs, 1 earner.

`EpagoFoundation/epago` has been added to the watch list; `RendixNetwork/leoma`
is retained as a reference. **`SN036-LEOMA.md` now describes two occupants ago and
needs re-analysis.**

