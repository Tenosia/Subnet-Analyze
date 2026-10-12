#!/usr/bin/env python3
"""Watch every subnet's GitHub repos and on-chain state; log changes to notification.md.

GitHub change detection uses `git ls-remote`, which is NOT subject to the REST API
rate limit. The API is called only when a change is detected, to describe it.

Chain state is read directly from finney — the same data taostats displays, but
authoritative and unscrapeable.

Usage:  python3 watch.py            # detect + log changes
        python3 watch.py --init     # establish baseline, log nothing
"""
from __future__ import annotations
import hashlib, json, os, re, subprocess, sys, urllib.request
from html import unescape as html_unescape
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE = HERE / ".watch-state.json"
NOTIFY = HERE / "notification.md"
PY = "/root/beam/.venv/bin/python"

# subnet -> repos.  "p" = the subnet's own code; "r" = a referenced dependency.
REPOS: dict[int, list[tuple[str, str]]] = {
    14: [("latent-to/cacheon", "p")],
    18: [("Orpheus-AI/Zeus", "p")],
    20: [("witnessvision/witness_subnet", "p")],
    25: [("urfoundation/sn", "p"), ("urnetwork/connect", "p"), ("urnetwork/server", "p"), ("urnetwork/sdk", "p")],
    26: [("0xsigurd/Perturb", "p")],
    28: [("taostat/gm-validator", "p"), ("taostat/gm-miner", "p")],
    29: [("coldint/sn29", "p")],
    34: [("BitMind-AI/bitmind-subnet", "p")],
    35: [("General-Tao-Ventures/cartha-validator", "p"), ("General-Tao-Ventures/cartha-cli", "p")],
    36: [("EpagoFoundation/epago", "p"), ("RendixNetwork/leoma", "r")],
    38: [("chronollm/sn38", "p")],
    40: [("RalphLabsAI/ralph-v2", "p"), ("RalphLabsAI/ralph", "p"), ("RalphLabsAI/recipe", "p")],
    43: [("GraphiteAI/Graphite-Subnet", "p")],
    47: [("center196/feval", "p")],
    53: [("hanlinai/engy", "p")],
    54: [("yanez-compliance/MIID-subnet", "p")],
    58: [("greevils-ai/greevils-validator", "p"), ("greevils-ai/greevils-cli", "p"),
         ("greevils-ai/greevils-docs", "p"), ("greevils-ai/greevils-public-harness", "p")],
    60: [("Bitsec-AI/sandbox", "p")],
    61: [("RedTeamSubnet/RedTeam", "p"), ("RedTeamSubnet/miner", "p")],
    71: [("leadpoet/leadpoet", "p")],
    76: [("heroncovelabs/ormas-subnet", "p")],  # netuid 76 re-registered 2026-09-05 as Ormas;
        # the former praxi-labs/phylax-subnet is not a continuation and is no longer watched
    78: [("Umi-BitSign/umi", "p"), ("vocence-78/vocence", "r")],
    79: [("taos-im/sn-79", "p")],
    80: [("openroboto-ai/openroboto-subnet", "p"), ("openroboto-ai/openroboto-evaluation", "p")],
    82: [("compelle/compelle-validator", "p")],
    90: [("KubeTEE-AI/kubetee-subnet", "p")],
    92: [("microtensor-io/microtensor-subnet", "p")],
    93: [("bitcast-network/bitcast", "p")],
    103: [("Capcomp-AI/capability-composition-subnet", "p"), ("Capcomp-AI/lora-merger-engine", "p")],
    105: [("Beam-Network/beam", "p"), ("Beam-Network/beam-core-public", "p")],
    107: [("minos-protocol/minos_subnet", "p")],
    108: [("TatsuProject/ChipForge_SN108", "p"),
          ("TatsuProject/chipforge_eda_server", "r")],  # EDA server produces the only score that matters
    114: [("DendriteHQ/SOMA", "p")],
    118: [("ditto-assistant/ditto-subnet", "p"), ("ditto-assistant/dittobench-starter-kit", "p")],
    119: [("capabilityforge-next/capabilityforge", "p")],
    120: [("AffineFoundation/affine", "p"), ("AffineFoundation/affine-cortex", "p")],
    121: [("sundae-bar/sb-validator", "p"), ("sundae-bar/bittensor-subnet", "p")],
    123: [("Barbariandev/MANTIS", "p")],
    124: [("swarm-subnet/swarm", "p")],
    127: [("astridintelligence/sn-127", "p")],
}
NETUIDS = [14,18,20,25,26,28,29,34,35,36,38,40,43,47,53,54,58,60,61,71,76,78,79,80,82,
           90,92,93,101,103,105,107,108,114,118,119,120,121,123,124,127]

# Chain fields worth an alert, with the minimum move that counts as news.
# alpha price is noisy, so only a large swing is reported.
THRESHOLDS = {"earners": 0, "uids": 0, "commitments": 0, "top_uid": 0,
              "owner_pct": 2.0, "alpha_usd_pct": 15.0, "top_incentive": 0.05}


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def ls_remote(repo: str) -> dict:
    """All refs for a repo, via git ls-remote. No REST API, no rate limit."""
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}
    try:
        out = subprocess.run(["git", "ls-remote", f"https://github.com/{repo}"],
                             capture_output=True, text=True, timeout=45, env=env)
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    if out.returncode != 0:
        err = (out.stderr or "").lower()
        if "could not read username" in err or "authentication" in err:
            return {"status": "private"}
        if "not found" in err or "repository not found" in err:
            return {"status": "missing"}
        return {"status": "error", "detail": (out.stderr or "").strip()[:120]}
    head, tags, n_refs = "", {}, 0
    for line in out.stdout.splitlines():
        if "\t" not in line:
            continue
        sha, ref = line.split("\t", 1)
        n_refs += 1
        if ref == "HEAD":
            head = sha
        elif ref.startswith("refs/tags/") and not ref.endswith("^{}"):
            tags[ref] = sha
    # Only HEAD and tags are tracked. Feature/PR branches churn constantly on
    # active repos (ditto-subnet carries ~2,950 refs) and are pure noise.
    return {"status": "ok", "head": head, "n_refs": n_refs, "n_tags": len(tags),
            "tags_digest": hashlib.sha256(
                json.dumps(tags, sort_keys=True).encode()).hexdigest()[:16]}


def gh_api(path: str):
    """One REST call. Only used to describe a change we already detected."""
    try:
        req = urllib.request.Request(f"https://api.github.com{path}",
                                     headers={"User-Agent": "subnet-watch",
                                              "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.load(r)
    except Exception:
        return None


def describe_commits(repo: str, old: str, new: str) -> list[str]:
    """Human-readable summary of what landed between two SHAs."""
    cmp = gh_api(f"/repos/{repo}/compare/{old}...{new}") if old else None
    if cmp and isinstance(cmp.get("commits"), list):
        msgs = [c["commit"]["message"].splitlines()[0][:110] for c in cmp["commits"][-8:]]
        n, files = cmp.get("total_commits", len(msgs)), len(cmp.get("files") or [])
        head = [f"{n} new commit(s), {files} file(s) changed"] if files else [f"{n} new commit(s)"]
        return head + [f"· {m}" for m in msgs]
    c = gh_api(f"/repos/{repo}/commits/{new}")
    if c:
        return [f"new HEAD — {c['commit']['message'].splitlines()[0][:110]}"]
    return ["HEAD moved (details unavailable)"]



def _norm_url(u: str) -> str:
    u = (u or "").strip()
    if not u:
        return ""
    return u if u.startswith(("http://", "https://")) else "https://" + u


def site_probe(url: str) -> dict:
    """Coarse fingerprint of a website.

    Deliberately NOT a hash of the whole page: most of these are dashboards with
    live counters, and hashing the text would fire every hour. We track status,
    <title>, the set of internal link targets, and text length in 5% buckets —
    so a redesign, a new/removed page, a retitle or an outage is reported and a
    ticking number is not.
    """
    import urllib.error
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; subnet-watch/1.0)"})
        with urllib.request.urlopen(req, timeout=25) as r:
            code = r.getcode()
            raw = r.read(600_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return {"status": f"http {e.code}"}
    except Exception as e:
        return {"status": "unreachable", "detail": type(e).__name__}
    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
    if m:
        title = re.sub(r"\s+", " ", html_unescape(m.group(1))).strip()[:120]
    links = sorted({h for h in re.findall(r'href="([^"#?]{2,120})"', raw)
                    if not h.startswith(("mailto:", "javascript:", "data:"))})
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return {"status": f"ok {code}", "title": title, "n_links": len(links),
            "links_digest": hashlib.sha256("|".join(links).encode()).hexdigest()[:16],
            "size_bucket": round(len(text) / max(len(text) * 0.05, 1))}


def diff_identity(old: dict, new: dict) -> list[str]:
    ev = []
    for key, label in (("gh", "GitHub repo"), ("url", "website"),
                       ("desc", "chain description")):
        o, n = (old.get(key) or "").strip(), (new.get(key) or "").strip()
        if o != n:
            if key == "desc":
                ev.append(f"**chain {label} changed** — now: *{n[:140]}*")
            else:
                ev.append(f"**chain {label}: `{o or '(empty)'}` → `{n or '(empty)'}`**")
    return ev


def diff_site(old: dict, new: dict) -> list[str]:
    if not old or not new:
        return []
    ev = []
    if old.get("status") != new.get("status"):
        ev.append(f"site {old.get('status')} → **{new.get('status')}**")
    if new.get("status", "").startswith("ok"):
        if old.get("title") != new.get("title"):
            ev.append(f"page title: \u201c{old.get('title','')}\u201d → **\u201c{new.get('title','')}\u201d**")
        if old.get("links_digest") != new.get("links_digest"):
            ev.append(f"site links changed ({old.get('n_links')} → {new.get('n_links')} targets)")
        elif old.get("size_bucket") != new.get("size_bucket"):
            ev.append("page content changed materially (>5% of text)")
    return ev


def chain_snapshot() -> dict:
    """Read the metrics taostats surfaces, straight from finney."""
    code = f'''
import bittensor as bt, numpy as np, json
st = bt.Subtensor("finney"); TAO = 256.0; MP = 0.41*7200
out = {{}}
for n in {NETUIDS!r}:
    try:
        sn = st.subnet(n); m = st.metagraph(n)
        I = np.array(m.I); D = np.array(m.D); p = float(sn.price)
        ow = sn.owner_hotkey
        ou = m.hotkeys.index(ow) if ow in m.hotkeys else -1
        oi = float(I[ou]) if ou >= 0 else 0.0
        od = float(D[ou]) if ou >= 0 else 0.0
        t = int(np.argmax(I))
        try: nc = len(st.get_all_commitments(n))
        except Exception: nc = None
        idt = {{}}
        try:
            r = st.query_subtensor("SubnetIdentitiesV3", params=[n])
            for a in ("value", "serialize"):
                if hasattr(r, a):
                    v = getattr(r, a); r = v() if callable(v) else v; break
            if isinstance(r, dict):
                idt = {{"gh": (r.get("github_repo") or "").strip(),
                       "url": (r.get("subnet_url") or "").strip(),
                       "desc": (r.get("description") or "").strip()}}
        except Exception: pass
        out[str(n)] = dict(name=str(sn.subnet_name), alpha_usd=round(p*TAO, 4),
            earners=int((I > 0).sum()), uids=int(m.n.item()),
            top_uid=t, top_incentive=round(float(I[t]), 4),
            top_is_owner=bool(m.hotkeys[t] == ow),
            owner_pct=round(100*(0.18*7200 + oi*MP + od*MP)/7200, 2),
            commitments=nc, identity=idt)
    except Exception as e:
        out[str(n)] = dict(error=str(e)[:80])
print("@@JSON@@" + json.dumps(out))
'''
    r = subprocess.run(["nice", "-n", "19", PY, "-c", code],
                       capture_output=True, text=True, timeout=900)
    for line in r.stdout.splitlines():
        if line.startswith("@@JSON@@"):
            return json.loads(line[8:])
    raise RuntimeError(f"chain snapshot failed: {r.stderr[-400:]}")


def diff_chain(net: str, old: dict, new: dict) -> list[str]:
    if "error" in new or "error" in old:
        return []
    ev = []
    if new["earners"] != old["earners"]:
        d = new["earners"] - old["earners"]
        ev.append(f"**earning UIDs {old['earners']} → {new['earners']}** ({d:+d})")
    if new["top_uid"] != old["top_uid"]:
        # Contested subnets rotate their top UID every tempo; that is not news.
        # Report only when owner-status flips, or the lead genuinely moves.
        owner_flip = new["top_is_owner"] != old.get("top_is_owner", False)
        big_move = abs(new["top_incentive"] - old["top_incentive"]) >= THRESHOLDS["top_incentive"]
        if owner_flip or big_move:
            ev.append(f"**top earner changed: UID {old['top_uid']} → UID {new['top_uid']}**"
                      + (" — now the **owner's own hotkey**" if new["top_is_owner"]
                         else " — no longer the owner's hotkey" if owner_flip else ""))
    elif abs(new["top_incentive"] - old["top_incentive"]) >= THRESHOLDS["top_incentive"]:
        ev.append(f"top earner incentive {old['top_incentive']:.4f} → {new['top_incentive']:.4f}")
    if old.get("commitments") is not None and new.get("commitments") is not None \
       and new["commitments"] != old["commitments"]:
        ev.append(f"on-chain commitments {old['commitments']} → {new['commitments']} "
                  f"({new['commitments'] - old['commitments']:+d})")
    if abs(new["owner_pct"] - old["owner_pct"]) >= THRESHOLDS["owner_pct"]:
        ev.append(f"owner capture {old['owner_pct']:.1f}% → {new['owner_pct']:.1f}%")
    if old["alpha_usd"] > 0:
        pct = 100*(new["alpha_usd"] - old["alpha_usd"])/old["alpha_usd"]
        if abs(pct) >= THRESHOLDS["alpha_usd_pct"]:
            ev.append(f"α ${old['alpha_usd']:.4f} → ${new['alpha_usd']:.4f} ({pct:+.1f}%)")
    if new["uids"] != old["uids"]:
        ev.append(f"registered UIDs {old['uids']} → {new['uids']}")
    if new["name"] != old["name"]:
        ev.append(f"⚠️ **subnet renamed on chain: `{old['name']}` → `{new['name']}`**")
    return ev


def main() -> int:
    init = "--init" in sys.argv
    state = json.loads(STATE.read_text()) if STATE.exists() else {"github": {}, "chain": {}, "sites": {}}

    gh_new, gh_events = {}, []
    for net, repos in sorted(REPOS.items()):
        for repo, kind in repos:
            info = ls_remote(repo)
            gh_new[repo] = {**info, "netuid": net, "kind": kind}
            prev = state["github"].get(repo)
            if init or not prev:
                continue
            if prev.get("status") != info.get("status"):
                gh_events.append((net, repo, kind,
                    [f"availability changed: `{prev.get('status')}` → `{info.get('status')}`"]))
            elif info.get("status") == "ok":
                lines = []
                if prev.get("head") != info.get("head"):
                    lines = describe_commits(repo, prev.get("head", ""), info["head"])
                elif prev.get("tags_digest") != info.get("tags_digest"):
                    lines = [f"tags changed ({prev.get('n_tags')} → {info.get('n_tags')}); HEAD unchanged"]
                if lines:
                    gh_events.append((net, repo, kind, lines))

    chain_new = chain_snapshot()
    chain_events = []
    for net, cur in sorted(chain_new.items(), key=lambda kv: int(kv[0])):
        prev = state["chain"].get(net)
        if init or not prev:
            continue
        ev = diff_chain(net, prev, cur)
        ev += diff_identity(prev.get("identity") or {}, cur.get("identity") or {})
        if ev:
            chain_events.append((int(net), cur.get("name", "?"), ev))

    # Websites: the URL each subnet publishes on chain, so a new subnet is
    # covered automatically and a URL change is itself detected above.
    site_new, site_events = {}, []
    for net, cur in sorted(chain_new.items(), key=lambda kv: int(kv[0])):
        url = _norm_url(((cur.get("identity") or {}).get("url")))
        if not url:
            continue
        probe = site_probe(url)
        probe["url"] = url
        site_new[net] = probe
        prev = (state.get("sites") or {}).get(net)
        if init or not prev or prev.get("url") != url:
            continue
        ev = diff_site(prev, probe)
        if ev:
            site_events.append((int(net), cur.get("name", "?"), url, ev))

    STATE.write_text(json.dumps({"github": gh_new, "chain": chain_new,
                                 "sites": site_new, "checked": now()}, indent=1))

    if init:
        ok = sum(1 for v in gh_new.values() if v.get("status") == "ok")
        up = sum(1 for v in site_new.values() if v.get("status", "").startswith("ok"))
        print(f"baseline set — {ok}/{len(gh_new)} repos reachable, "
              f"{up}/{len(site_new)} sites up, {len(chain_new)} subnets")
        return 0
    if not gh_events and not chain_events and not site_events:
        print(f"{now()} — no changes")
        return 0

    out = [f"\n## {now()}\n"]
    if gh_events:
        out.append("### GitHub\n")
        for net, repo, kind, lines in gh_events:
            tag = "" if kind == "p" else " *(referenced dependency)*"
            out.append(f"- **SN{net}** · [`{repo}`](https://github.com/{repo}){tag}")
            out.extend(f"    - {l}" for l in lines)
        out.append("")
    if chain_events:
        out.append("### Chain\n")
        for net, name, ev in chain_events:
            out.append(f"- **SN{net} {name}**")
            out.extend(f"    - {e}" for e in ev)
        out.append("")
    if site_events:
        out.append("### Websites\n")
        for net, name, url, ev in site_events:
            out.append(f"- **SN{net} {name}** · [{url}]({url})")
            out.extend(f"    - {e}" for e in ev)
        out.append("")

    body = NOTIFY.read_text() if NOTIFY.exists() else ""
    marker = "<!-- entries below, newest first -->"
    entry = "\n".join(out)
    NOTIFY.write_text(body.replace(marker, marker + "\n" + entry, 1)
                      if marker in body else body + entry)
    print(f"{now()} — logged {len(gh_events)} GitHub + {len(chain_events)} chain "
          f"+ {len(site_events)} website change(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
