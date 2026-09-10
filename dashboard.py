#!/usr/bin/env python3
"""Live dashboard for the subnet watcher.

  /                 change log, paginated by day, two columns
  /?day=YYYY-MM-DD  one specific day
  /compare          the all-subnets comparison table
  /<name>.md        any analysis file, served as PLAIN TEXT
Everything is read from disk per request, so the hourly cron's output shows up
immediately with no restart.
"""
from __future__ import annotations
import html, json, re
from collections import OrderedDict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import markdown

HERE = Path(__file__).resolve().parent
NOTIFY, COMPARE, STATE = HERE / "notification.md", HERE / "compare-table.md", HERE / ".watch-state.json"
PORT = 8090
MARKER = "<!-- entries below, newest first -->"
MD = markdown.Markdown(extensions=["tables", "sane_lists"])
DOC = markdown.Markdown(extensions=["tables", "sane_lists", "fenced_code", "toc", "attr_list"])
INLINE = markdown.Markdown()

CSS = """
*{box-sizing:border-box}
body{margin:0;background:#0d1117;color:#c9d1d9;
 font:15px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1320px;margin:0 auto;padding:24px 22px 80px}
.wide{max-width:1680px}
header{display:flex;align-items:baseline;gap:13px;flex-wrap:wrap}
h1{font-size:21px;margin:0;letter-spacing:-.3px;color:#e6edf3}
.sub{color:#7d8590;font-size:13px}
nav{display:flex;gap:6px;margin:15px 0 18px;flex-wrap:wrap}
nav a{padding:6px 13px;border-radius:7px;font-size:13.5px;color:#8b949e;
 border:1px solid #30363d;background:#161b22;text-decoration:none}
nav a:hover{color:#e6edf3;border-color:#484f58}
nav a.on{color:#e6edf3;border-color:#388bfd;background:#132a52}
.bar{display:flex;gap:9px;flex-wrap:wrap;margin:0 0 18px}
.card{background:#161b22;border:1px solid #30363d;border-radius:9px;padding:10px 14px;min-width:100px}
.card .k{font-size:10.5px;text-transform:uppercase;letter-spacing:.7px;color:#7d8590}
.card .v{font-size:19px;font-weight:650;color:#e6edf3;margin-top:2px}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:7px;vertical-align:1px}
.live .dot{background:#3fb950;box-shadow:0 0 0 3px #3fb95022}
.stale .dot{background:#d29922;box-shadow:0 0 0 3px #d2992222}
.status{font-size:12.5px;color:#7d8590;margin-bottom:16px}
.pulse{animation:p 2s ease-in-out infinite}@keyframes p{50%{opacity:.45}}
.days{display:flex;gap:5px;flex-wrap:wrap;margin:0 0 20px;padding:11px 13px;
 background:#0f141b;border:1px solid #21262d;border-radius:9px;align-items:center}
.days .lbl{font-size:10.5px;text-transform:uppercase;letter-spacing:.8px;color:#6e7681;margin-right:5px}
.days a{padding:4px 10px;border-radius:6px;font-size:12.5px;color:#8b949e;
 border:1px solid #30363d;text-decoration:none;white-space:nowrap}
.days a:hover{color:#e6edf3;border-color:#484f58}
.days a.on{background:#1f6feb;border-color:#1f6feb;color:#fff;font-weight:600}
.days a .n{opacity:.6;font-size:11px;margin-left:4px}
.cols{column-count:2;column-gap:20px}
@media(max-width:980px){.cols{column-count:1}}
.run{break-inside:avoid;page-break-inside:avoid;margin:0 0 20px;
 border:1px solid #30363d;border-radius:10px;overflow:hidden;background:#0f141b}
.run>.t{padding:9px 14px;background:#161b22;border-bottom:1px solid #30363d;
 font-size:13px;font-weight:650;color:#e6edf3;letter-spacing:.2px}
.run>.t .ago{float:right;font-weight:400;color:#6e7681;font-size:11.5px}
.run.newest{border-color:#238636}.run.newest>.t{background:#12261a;border-bottom-color:#238636}
.sec{padding:10px 14px 4px}
.sec>.h{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#6e7681;margin:0 0 8px}
.it{border-left:2px solid #30363d;padding:0 0 0 11px;margin:0 0 11px}
.it.gh{border-left-color:#8957e5}.it.ch{border-left-color:#1f6feb}.it.we{border-left-color:#d29922}
.it>.n{font-size:13.5px;color:#e6edf3;font-weight:600;margin-bottom:3px}
.it>.n a{color:#58a6ff;font-weight:400;font-size:12.5px}
.it ul{margin:0;padding:0;list-style:none}
.it li{font-size:13px;color:#adbac7;margin:2px 0;padding-left:13px;position:relative}
.it li:before{content:"";position:absolute;left:2px;top:8px;width:4px;height:4px;
 border-radius:50%;background:#484f58}
.it li.msg{color:#8b949e;font-size:12.5px;font-family:ui-monospace,Menlo,monospace;
 padding-left:16px}
.it li.msg:before{content:"";left:5px;width:3px;height:3px;background:#3d444d}
.prose{padding:12px 15px;font-size:13.5px}
.prose h2,.prose h3{font-size:13px;color:#e6edf3;margin:12px 0 5px}
code{background:#1f2937;padding:1.5px 5px;border-radius:4px;font-size:12px;
 font-family:ui-monospace,SFMono-Regular,Menlo,monospace;color:#a5d6ff}
a{color:#58a6ff;text-decoration:none}a:hover{text-decoration:underline}
strong{color:#e6edf3}
.tbl{overflow-x:auto;margin:14px 0;border:1px solid #30363d;border-radius:9px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border-bottom:1px solid #21262d;border-right:1px solid #21262d;padding:8px 11px;
 text-align:left;vertical-align:top}
th{background:#161b22;color:#7d8590;font-size:11px;text-transform:uppercase;
 letter-spacing:.5px;position:sticky;top:0;white-space:nowrap}
tbody tr:hover{background:#161b2288}
td:first-child{white-space:nowrap;font-weight:600}
blockquote{border-left:3px solid #30363d;margin:10px 0;padding:2px 0 2px 13px;color:#8b949e}
.empty{color:#7d8590;font-style:italic;padding:26px 0}
footer{margin-top:40px;padding-top:15px;border-top:1px solid #21262d;color:#6e7681;font-size:12.5px}
.priv{list-style:none;padding:0;margin:5px 0 0;font-size:12.5px;color:#7d8590}
/* ---- document view ---- */
.doc{display:grid;grid-template-columns:230px minmax(0,1fr);gap:34px;align-items:start}
@media(max-width:900px){.doc{grid-template-columns:1fr}.toc{position:static!important;max-height:none!important}}
.toc{position:sticky;top:18px;max-height:82vh;overflow:auto;font-size:12.5px;
 border:1px solid #21262d;border-radius:9px;background:#0f141b;padding:12px 6px 12px 12px}
.toc .lbl{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#6e7681;margin:0 0 7px}
.toc a{display:block;padding:3px 6px;border-radius:5px;color:#8b949e;line-height:1.35}
.toc a:hover{background:#161b22;color:#e6edf3;text-decoration:none}
.toc a.l3{padding-left:17px;font-size:12px;color:#6e7681}
.docbody{max-width:860px;font-size:15px;line-height:1.72;color:#c9d1d9}
.docbody h1{font-size:26px;margin:0 0 6px;color:#e6edf3;letter-spacing:-.4px;line-height:1.25}
.docbody h2{font-size:19px;margin:36px 0 12px;padding:0 0 8px;color:#e6edf3;
 background:none;border:0;border-bottom:1px solid #21262d;border-radius:0;font-weight:650}
.docbody h3{font-size:15.5px;margin:26px 0 8px;color:#e6edf3;text-transform:none;
 letter-spacing:0;font-weight:650}
.docbody h4{font-size:14px;margin:20px 0 6px;color:#adbac7;font-weight:650}
.docbody p{margin:12px 0}
.docbody ul,.docbody ol{margin:12px 0;padding-left:24px}
.docbody li{margin:5px 0;color:#c9d1d9;font-size:15px}
.docbody li::marker{color:#6e7681}
.docbody blockquote{border-left:3px solid #388bfd;background:#0f1b2d;margin:16px 0;
 padding:12px 16px;border-radius:0 8px 8px 0;color:#adbac7}
.docbody blockquote strong{color:#e6edf3}
.docbody pre{background:#0f141b;border:1px solid #21262d;border-radius:9px;
 padding:13px 15px;overflow-x:auto;margin:14px 0}
.docbody pre code{background:none;padding:0;color:#adbac7;font-size:12.8px;line-height:1.55}
.docbody table{font-size:14px}
.docbody th{position:static}
.docbody hr{margin:30px 0}
.docbody a{border-bottom:1px solid #1f4b8f}
.docbody a:hover{border-bottom-color:#58a6ff;text-decoration:none}
.dochead{display:flex;justify-content:space-between;align-items:center;gap:14px;
 flex-wrap:wrap;margin:0 0 4px}
.meta{font-size:12.5px;color:#6e7681}
"""


def md_inline(t: str) -> str:
    INLINE.reset()
    h = INLINE.convert(t).strip()
    return h[3:-4] if h.startswith("<p>") and h.endswith("</p>") else h


def stats() -> dict:
    try:
        s = json.loads(STATE.read_text())
    except Exception:
        return {}
    gh, sites = s.get("github", {}), s.get("sites", {})
    priv = [(v["netuid"], k) for k, v in gh.items() if v.get("status") == "private"]
    down = [(k, v.get("url", "")) for k, v in sites.items()
            if not str(v.get("status", "")).startswith("ok")]
    checked, age = s.get("checked", "—"), ""
    try:
        t = datetime.strptime(checked, "%Y-%m-%d %H:%M UTC").replace(tzinfo=timezone.utc)
        m = int((datetime.now(timezone.utc) - t).total_seconds() // 60)
        age = f"{m} min ago" if m < 90 else f"{m // 60} h ago"
    except Exception:
        pass
    return {"repos": len(gh), "reachable": sum(1 for v in gh.values() if v.get("status") == "ok"),
            "private": sorted(priv), "sites": len(sites), "sites_up": len(sites) - len(down),
            "down": sorted(down), "subnets": len(s.get("chain", {})), "checked": checked,
            "age": age, "stale": age.endswith("h ago")}


def parse_log() -> list[dict]:
    """notification.md -> [{date, time, title, sections:[{name, items:[{head, lines}]}], prose}]"""
    try:
        raw = NOTIFY.read_text()
    except Exception:
        return []
    body = raw.split(MARKER, 1)[1] if MARKER in raw else raw
    runs, cur, sec = [], None, None
    for line in body.splitlines():
        m = re.match(r"^## (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) UTC(.*)$", line)
        if m:
            cur = {"date": m.group(1), "time": m.group(2),
                   "title": m.group(3).strip(" —"), "sections": [], "prose": []}
            runs.append(cur); sec = None
            continue
        if cur is None:
            continue
        m = re.match(r"^### (.+)$", line)
        if m:
            sec = {"name": m.group(1).strip(), "items": []}
            cur["sections"].append(sec); continue
        m = re.match(r"^- (.+)$", line)
        if m and sec is not None:
            sec["items"].append({"head": m.group(1), "lines": []}); continue
        m = re.match(r"^ {2,}- (.+)$", line)
        if m and sec is not None and sec["items"]:
            sec["items"][-1]["lines"].append(m.group(1)); continue
        if sec is None and line.strip():
            cur["prose"].append(line)
    return runs


def run_html(r: dict, newest: bool) -> str:
    kind = {"github": "gh", "chain": "ch", "websites": "we"}
    parts = [f"<div class='run{' newest' if newest else ''}'><div class=t>"
             f"{r['time']} UTC{(' · ' + html.escape(r['title'])) if r['title'] else ''}"
             f"{'<span class=ago>latest</span>' if newest else ''}</div>"]
    for s in r["sections"]:
        k = kind.get(s["name"].lower(), "ch")
        parts.append(f"<div class=sec><div class=h>{html.escape(s['name'])}</div>")
        for it in s["items"]:
            lis = "".join(
                f"<li class='{'msg' if l.startswith('· ') else ''}'>"
                f"{md_inline(l[2:] if l.startswith('· ') else l)}</li>"
                for l in it["lines"])
            parts.append(f"<div class='it {k}'><div class=n>{md_inline(it['head'])}</div>"
                         f"<ul>{lis}</ul></div>")
        parts.append("</div>")
    if r["prose"]:
        MD.reset()
        p = MD.convert("\n".join(r["prose"]))
        p = p.replace("<table>", "<div class=tbl><table>").replace("</table>", "</table></div>")
        parts.append(f"<div class=prose>{p}</div>")
    return "".join(parts) + "</div>"


def log_page(day: str | None) -> str:
    st, runs = stats(), parse_log()
    by_day: OrderedDict[str, list] = OrderedDict()
    for r in runs:
        by_day.setdefault(r["date"], []).append(r)
    days = list(by_day)
    if not days:
        return shell("Subnet Watch", "/", "", "<p class=empty>No entries yet.</p>", True)
    sel = day if day in by_day else days[0]
    chips = "".join(
        f"<a href='/?day={d}'{' class=on' if d == sel else ''}>{d}"
        f"<span class=n>{len(by_day[d])}</span></a>" for d in days)
    newest_run = runs[0] if runs else None
    cards = "".join(run_html(r, r is newest_run) for r in by_day[sel])
    priv = "".join(f"<li>SN{u} · <code>{html.escape(x)}</code></li>" for u, x in st.get("private", []))
    down = "".join(f"<li>SN{u} · <code>{html.escape(x)}</code></li>" for u, x in st.get("down", []))
    aside = ""
    if priv or down:
        col = lambda t, v: (f"<div><div class=k style='font-size:10.5px;text-transform:uppercase;"
                            f"letter-spacing:.7px;color:#7d8590'>{t}</div><ul class=priv>{v}</ul></div>")
        aside = ("<div style='display:flex;gap:30px;flex-wrap:wrap;margin:-6px 0 18px'>"
                 + (col("Private repos", priv) if priv else "")
                 + (col("Sites down", down) if down else "") + "</div>")
    head = (f"<div class='status {'stale' if st.get('stale') else 'live'}'>"
            f"<span class='dot pulse'></span><span id=age>Last check: "
            f"{html.escape(st.get('checked', '—'))} · {html.escape(st.get('age') or '—')}</span>"
            f" · cron hourly at :17 · page refreshes every 60s</div>"
            f"<div class=bar>"
            f"<div class=card><div class=k>Subnets</div><div class=v>{st.get('subnets', 0)}</div></div>"
            f"<div class=card><div class=k>Repos</div><div class=v>{st.get('reachable', 0)}"
            f"<span style='font-size:13px;color:#7d8590'>/{st.get('repos', 0)}</span></div></div>"
            f"<div class=card><div class=k>Websites</div><div class=v>{st.get('sites_up', 0)}"
            f"<span style='font-size:13px;color:#7d8590'>/{st.get('sites', 0)}</span></div></div>"
            f"<div class=card><div class=k>Runs logged</div><div class=v>{len(runs)}</div></div>"
            f"<div class=card><div class=k>Days</div><div class=v>{len(days)}</div></div>"
            f"</div>{aside}"
            f"<div class=days><span class=lbl>Day</span>{chips}</div>")
    return shell(f"Subnet Watch — {sel}", "/", head, f"<div class=cols>{cards}</div>", True)


def compare_page() -> str:
    st = stats()
    try:
        MD.reset()
        b = MD.convert(COMPARE.read_text())
        b = b.replace("<table>", "<div class=tbl><table>").replace("</table>", "</table></div>")
    except Exception:
        b = "<p class=empty>compare-table.md not found.</p>"
    head = (f"<div class=status>All {st.get('subnets', 0)} subnets · regenerated whenever one is "
            f"added · chain figures read at a single block height · click any file to read it</div>")
    return shell("Subnet Watch — compare", "/compare", head, b, False, wide=True)


def doc_page(name: str, text: str) -> str:
    DOC.reset()
    body = DOC.convert(text)
    body = body.replace("<table>", "<div class=tbl><table>").replace("</table>", "</table></div>")
    toc = []
    for t in getattr(DOC, "toc_tokens", []):
        toc.append(f"<a href='#{t['id']}'>{html.escape(t['name'])[:58]}</a>")
        for c in t.get("children", []):
            toc.append(f"<a class=l3 href='#{c['id']}'>{html.escape(c['name'])[:52]}</a>")
    lines = text.count(chr(10)) + 1
    kb = round(len(text.encode()) / 1024)
    head = (f"<div class=dochead><span class=meta>{html.escape(name)} · {lines:,} lines · {kb} KB</span>"
            f"<span><a href='/{name}?raw=1'>raw text</a> · "
            f"<a href='/files'>all files</a></span></div>")
    inner = (f"<div class=doc><aside class=toc><div class=lbl>Contents</div>"
             f"{''.join(toc)}</aside><article class=docbody>{body}</article></div>"
             if toc else f"<article class=docbody>{body}</article>")
    return shell(f"{name} — Subnet Watch", "/files", head, inner, False, wide=True)


def files_page() -> str:
    rows = []
    for f in sorted(HERE.glob("SN*.md")):
        t = f.read_text(errors="replace")
        first = next((l.lstrip("# ").strip() for l in t.splitlines() if l.startswith("# ")), f.stem)
        rows.append(f"<tr><td><a href='/{f.name}'>{f.name}</a></td>"
                    f"<td>{html.escape(first)[:96]}</td>"
                    f"<td>{t.count(chr(10)) + 1:,}</td>"
                    f"<td>{round(f.stat().st_size / 1024)} KB</td></tr>")
    extra = "".join(f"<tr><td><a href='/{n}'>{n}</a></td><td>{d}</td><td></td><td></td></tr>"
                    for n, d in (("compare-table.md", "All-subnets comparison"),
                                 ("notification.md", "Change log"),
                                 ("README.md", "Folder index")))
    return shell("Files — Subnet Watch", "/files",
                 f"<div class=status>{len(rows)} subnet analyses · click any file to read it</div>",
                 f"<div class=tbl><table><thead><tr><th>File</th><th>Title</th>"
                 f"<th>Lines</th><th>Size</th></tr></thead><tbody>{extra}{''.join(rows)}"
                 f"</tbody></table></div>", False, wide=True)


def shell(title, on, head, body, poll, wide=False) -> str:
    nav = "".join(f"<a href='{h}'{' class=on' if h == on else ''}>{t}</a>"
                  for h, t in (("/", "Change log"), ("/compare", "Compare table"), ("/files", "Files")))
    js = ("<script>setInterval(async()=>{try{const u=new URL(location.href);"
          "const r=await fetch('/api/state',{cache:'no-store'});const d=await r.json();"
          "const e=document.getElementById('age');"
          "if(e)e.textContent='Last check: '+d.checked+' · '+d.age;"
          "if(d.checked!==window.__c){window.__c=d.checked;location.reload();}"
          "}catch(e){}},60000);</script>") if poll else ""
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>"
            f"<div class='wrap{' wide' if wide else ''}'>"
            f"<header><h1>Bittensor Subnet Watch</h1>"
            f"<span class=sub>GitHub · websites · on-chain</span></header><nav>{nav}</nav>"
            f"{head}{body}<footer>Read live from disk on every request — nothing cached. "
            f"{html.escape(str(HERE))}</footer></div>{js}</body></html>")


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, body: bytes, ctype: str, code: int = 200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        p = u.path.rstrip("/") or "/"
        if p == "/api/state":
            st = stats()
            self._send(json.dumps({"checked": st.get("checked", "—"),
                                   "age": st.get("age", "")}).encode(),
                       "application/json; charset=utf-8")
        elif p == "/":
            day = (parse_qs(u.query).get("day") or [None])[0]
            self._send(log_page(day).encode(), "text/html; charset=utf-8")
        elif p == "/compare":
            self._send(compare_page().encode(), "text/html; charset=utf-8")
        elif p == "/raw":
            self._send(NOTIFY.read_bytes(), "text/plain; charset=utf-8")
        elif p == "/compare/raw":
            self._send(COMPARE.read_bytes(), "text/plain; charset=utf-8")
        elif p == "/files":
            self._send(files_page().encode(), "text/html; charset=utf-8")
        elif p.endswith(".md"):
            f = (HERE / Path(p).name).resolve()
            if f.parent != HERE or not f.is_file():
                self._send(b"not found", "text/plain", 404)
            elif (parse_qs(u.query).get("raw") or [""])[0]:
                self._send(f.read_bytes(), "text/plain; charset=utf-8")
            else:
                self._send(doc_page(f.name, f.read_text(errors="replace")).encode(),
                           "text/html; charset=utf-8")
        else:
            self._send(b"not found", "text/plain", 404)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"dashboard on :{PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
