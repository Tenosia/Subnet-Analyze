# SN118 Ditto — Engineering Deep-Dive

Companion to [SN118_DITTO.md](SN118-DITTO.md). Code-grounded from the four core repos cloned into `Bittensor/`: `ditto-subnet` (chain/incentive), `dittobench-api` (Go scorer), `dittobench-datagen` (Go dataset+grader), `ditto-harness` (Rust memory engine), plus `dittobench-starter-kit` (the miner you edit).

> **The one-sentence model:** everyone runs the **same frozen LLM** (`openai/gpt-oss-20b` for the current v7/v8 contract) on a **fresh, per-agent, unpredictable dataset**, and you win by building the **best memory-retrieval + tool-calling harness around that model** — scored by a **deterministic, judge-free, publicly reproducible grader**. Latency and token cost do **not** move your score.

---

## 1. Repo map

| Repo | Lang | Role | You edit? |
|---|---|---|---|
| `dittobench-starter-kit` | Rust | the harness you submit (baseline + practice + submit) | **YES** |
| `ditto-harness` | Rust | the memory/agent crate the kit depends on (retrieval pipeline) | pinned dep; you override its traits |
| `dittobench-api` | Go | the scorer + the ticket-scoped inference broker (validator side) | no (but defines how you're scored) |
| `dittobench-datagen` | Go | deterministic dataset generator + judge-free grader (public) | no (but defines what you're scored on) |
| `ditto-subnet` | Python | chain: incentive/weights (Pylon), CLI, screener, sandbox, validator | no (you use its `ditto` CLI) |

---

## 2. Incentive / emission mechanics (`ditto-subnet/ditto/validator/`)

**King-of-the-Hill, top-5 only** — frozen constants (`config.py`), not env-tunable:
- `KOTH_RANK_SHARES = (0.65, 0.14, 0.10, 0.07, 0.04)` → champion + next 4 distinct miners. **Everyone else earns 0.**
- 100% of miner emission follows this vector (`MINER_EMISSION_SHARE = 1.0`).
- **No eligible miners → 100% burned** to SN118 UID 0 (not paid to the owner).

**Eligibility:** a run must cover the **full profile** (`MIN_ELIGIBLE_CASES = 100`; full ≈ 114–351 cases depending on bench version). Smoke/practice runs are dropped from the weight fold. Non-positive composite → nothing.

**Dethrone hysteresis (`_beats`):** a challenger must beat the incumbent by an **indifference band = max(0.007 composite points, statistical band)**. The statistical band is a `z=1.64` (one-sided 95%) test over **shared CRN seeds** (paired when possible) — so you must be *provably* better, not lucky. Near the ceiling (champ > 0.60) the band **shrinks** (`exp(-2·(champ-0.60))`) to keep the crown contestable toward 1.0.

**Ties → incumbent keeps the crown**, folded in **first-seen order**. Practical consequence: **first-to-submit wins ties, and a copied harness (which at best ties) never earns.**

**One slot per coldkey** (captured at payment time) — rotated/multiple hotkeys of one owner compete for the *same* slot; owner-link attestations don't add a slot.

**Weight setting:** the validator computes the deterministic vector from the public ledger; **Pylon** (identity service) does UID resolution + commit-reveal + the on-chain extrinsic. **Tempo = 72 min.** Weights commit then reveal one epoch later, and Yuma clips at 50% stake — so **incentive shows 0.00000 until >50% of stake carries you, then jumps** to full value. Budget **~2.5–4.5 h** from first score to visible incentive.

**Dereg/immunity:** handled at chain level (not in this repo). A hotkey off the metagraph is excluded; re-registering the same hotkey restores eligibility (scores/payments are retained). Version by re-submitting under the **same hotkey + exact agent name**; your **highest eligible version** represents you, so a worse update never replaces your best.

---

## 3. Submission lifecycle (`ditto-subnet`)

**CLI:** `ditto --network finney upload --path agent.tgz --name <n> --coldkey <ck> --hotkey <hk>` · `ditto status <id>` · `ditto verify --path …` (local size/gzip/tar only — **not** a real screen) · `ditto attest …` (owner-links).

**State machine:** `uploaded → screening → screening_passed|screening_failed → evaluating → scored → live` (+ `quarantined`, `ath_pending_review`, `banned`). Evaluated by **up to 3 independent validators → median score**.

**Fee:** **0.04 TAO** (platform-controlled, fetched at upload; = 40,000,000 rao). **Coldkey pays, hotkey receives incentive.** Byte-identical resubmits bank a reusable credit. A **15-min exclusive admission slot** + 24 h payment-proof reuse window; per-coldkey submission cooldown.

**Tarball rules:** gzip, **≤ 20 MiB**, `Dockerfile` at root, safe relative paths, ≤20,000 members, ≤64 MiB unpacked. (Enforced screener-side, not by local `verify`.)

**Screening (platform-operated):** `docker build` → run detached with caps → poll `GET /health` until 2xx → **source review** (L1 `gpt-5.6-luna`, L2 `kimi-k3`, L3 critic) for copy/plagiarism + benchmark-gaming. Only objective failures (unsafe archive, build failure, `/health` fail) are hard rejects; copy/behavioral flags **quarantine for human review**. **Forking the public starter kit is allowed; copying another miner is not** (lexical + semantic fingerprints across miners). On pass, the exact image is saved+hashed and bound into a signed verdict, so validators **load the screened image** (no rebuild).

**Sandbox (untrusted execution):** miner containers run in a **privileged nested Docker (DinD)** executor, but each miner container is **non-root (UID 65532), read-only rootfs, all caps dropped, no-new-privileges, mem 3g / cpu 2 / pids 512 / tmpfs 512m**, no wallet/socket/host mounts. **Network egress is default-deny**: only the ticket broker (`:11436`) and an OpenRouter TLS shim (`:11437`) are reachable; metadata, RFC1918, public internet, and DNS bypasses are **rejected loudly** (tcp-reset). You cannot phone home or fetch anything at scored time.

**Timing:** validators sweep the `evaluating` queue every 30 s; a single run cap is 75 min (bounded by ticket TTL, currently ~30–90 min). Screening + benchmark: "minutes to hours" by queue.

---

## 4. The exact scoring formula (`dittobench-api/internal/scorer/`)

**Base:** `composite = 0.5 · tool_mean + 0.5 · memory_mean` (each is pure accuracy). Then multiplied by **integrity gates** (`composite = round6(base · gate)`).

**Tool score** (per case): `0.4 · name-F1 + 0.4 · arg-F1 + 0.2 · trajectory`.
- **name-F1** = F1 of tool-name selection (missing *and* extra calls hurt).
- **arg-F1** = F1 of value-correct required args (numeric = exact whole-token; **argument stuffing rejected**).
- **trajectory** = order-credit × (1 − over-budget penalty).
- **v7 strict:** a **forbidden arg → case 0**; a fully **reversed multi-hop chain → 0** (order multiplies the whole score); over-budget penalty **doubled**; a self-report disagreeing with observed calls **halves** the case.
- **Observed execution is authoritative** — the validator serves a mock tool endpoint; if a tool case is never executed through it, **scored = 0** (practice caps at 0.05). A `preflight:` probe requires one served-tool call before scoring begins.

**Memory score** (per case) — deterministic per `answer_kind` (`value`, `number`, `money`, `direction`, `list`, `ordered_list`, `duration`, `reversal`, `persistence`, `decline`, `acknowledge`, `chitchat`). **Checked first, these zero the case:** bait-tool called, forbidden value surfaced (injection/cross-user/canary), **any distractor value present in slot OR prose** (anti-shotgun), whole-self-table **dump guard**, or **abstaining on an answerable question**. Under v8 the `answer` slot is authoritative (prose is fallback only).

**Integrity gates** (each ≤ 1.0; they multiply). v7 penalties are far harsher than v3–v6:

| Gate | What it punishes | v3–v6 max | **v7 max** |
|---|---|---|---|
| tool-efficiency | overshooting expected call budget (saturates ~+3 extra) | −15% | **−40%** |
| metamorphic-consistency | answering paraphrase twins inconsistently | −15% | **−40%** |
| transform-audit | brittleness when a fact is re-asked under a transform | −15% (obs.) | **−40% (enforced)** |
| memory-over-call | calling a non-memory action tool on a pure recall question | −10% | **−25%** |
| canary-integrity | echoing a canary **bait** nonce (a leak) | ×0.5 | **×0.25** |
| conversational-sanity | mishandling greetings / no-save-verb declaratives (floor) | 0.5 | **0.25 floor** |
| token-efficiency | — | ×[0.9,1] (v5) | **×1.0 (neutral — quality only)** |

So even a high-accuracy harness can be gutted ~50%+ by failing several gates. **Integrity discipline ≈ as important as raw retrieval.**

**Relative-efficiency bonus** (platform side, strictly upside, capped **5–10%**): per epoch cohort, runs at/below the 25th-percentile chat-token cost get a bonus — but only if `composite ≥ Q_min` **and** `memory_mean ≥ M_min` (you can't buy efficiency by gutting memory). Miner-reported tokens are ignored (audited from the model proxy).

---

## 5. The HTTP contract (`dittobench-api/internal/runner/`)

Serve on **:8080**:
- `GET /health` → any 2xx (probed first; 10 s).
- `POST /seed` → `SeedRequest{user_id?, wave?, pairs[], subjects[], links[]}` → `SeedResponse{pairs,subjects,links}`. One call per **wave** (full profile = 5 waves). Deadline 5 min (v7: 15 min).
- `POST /run` → one case:
  ```
  RunRequest  { case_id, system_prompt, user_input, tools[], bench_version(v7+), tool_endpoint?, user_id? }
  RunResponse { final_text, tool_calls[], prompt_tokens, output_tokens, latency_ms(IGNORED),
                answer?, abstain?, confidence? }
  ```
  Per-case timeout 120 s (v7: 5 min); up to 3 retries on transient 429/5xx. **You call the served `tool_endpoint`** (POST `{case_id,name,args,hop}` → `{result,error}`) — memory tools are never served there (they're yours).

**Populate `answer` with the bare value; set `abstain:true` only on genuine decline cases.** Never enumerate rejected candidates anywhere (distractor scan covers slot **and** prose).

---

## 6. Anti-cheat design (why memorization/copying can't work)

- **Per-agent, commit-before-reveal seed:** `seed = SHA-256(block_hash ‖ agent_id)` where the block **postdates** your frozen commit → unpredictable, and **unique to your agent** (a leaked dataset is useless to anyone else; there's no shared answer key).
- **Per-run rotation:** every submit draws a fresh crypto-random seed; generation is a pure function of `(seed, bench_version)`, so a version bump rotates the entire rendered surface ("public treadmill") — a pattern-matcher decays, a reasoner doesn't.
- **Frozen model behind a ticket-scoped broker:** the broker holds the platform key in-process, **overwrites your model field** with the locked one, and **drops any provider key in your container env** — you cannot route around `gpt-oss-20b`. Sessions are source-IP-bound, run-bound, TTL ≤ 2 h.
- **Reproduce-under-transform audit:** ~15% of cases re-ask the same fact under a seed-derived transform — **invariance** (rephrase; answer unchanged) or **covariance** (~10%; answer *changes*, e.g. prior-state on an update chain). A memorized answer becomes *wrong* under covariance.
- **Needle gating (result-usage):** the answer needle is served **only by the case's bearer tool**, with a decoy number in a per-seed sentence; "grab the first/any number" surfaces the **decoy → whole case 0**. Dependent chains (job-id / URL / retry) only reveal the needle when you thread the served value.
- **Canary multi-decoy + shape families:** a scrubber that deletes injection payloads also deletes its own required answers (same per-seed token shape) → self-defeating.
- **Red-team CI:** standing baselines (omniscient dumper, label counter, cessation-grepper, shape-scrubber, rarity-retriever) must all score ~0 or the build fails. The benchmark is *designed* so only genuine reasoning scores.
- **Deterministic & publicly reproducible:** anyone can regenerate the dataset from the seed and re-run the public grader over your signed transcript — the number must match. No hidden judge.

---

## 7. What you're scored on (task families, `dittobench-datagen`)

**Memory families** (weighted; `computed-answer` is up-weighted to 10): single-session-recall, multi-session, temporal-reasoning, knowledge-update, preference(+application), contradiction, abstention, injection-resistance, assistant-recall, aggregation-count, computed-answer, point-in-time, canary — plus the **v7 reasoning-required** families that break non-reasoning harnesses: **multi-hop-deep** (3-hop joins), **lifecycle-deep-read** (save→update→update→read chains), **near-miss-abstention** (entity disambiguation with the sibling's value seeded as a distractor), **temporal-arithmetic** (aggregate quantities across sessions), **injection-composed**, **subscription-own/attributed** (provenance: "my X" vs "@friend's X"). v8 adds a single **shared procedural world** where routes depend on seeded prior context.

**Tool families** (37-tool catalog): single-tool routing (memory/web/image/calendar/email/agent/settings…), **discrimination traps** (`route_memory_not_web`, `agent_run_not_read`, `image_edit_not_create`, `no_tool`, `abstention`, `arg_hallucination`…), multi-tool, and high-value **result-usage / dependent-chain** cases (`web_result_usage`, `link_chain_result_usage`, `job_chain_recovery_result_usage`, `entity_lookup_chain`).

**Where the points are (stock/champion scores ~0 — your headroom):**
- **multi-hop-deep** (~0.00 weak-champ), **lifecycle-deep-read** (~0.005), **near-miss-abstention** (~0.006), **temporal-arithmetic** (~0.007) → together **~24% of the memory suite**, nearly all recoverable by real reasoning.
- **computed-answer** (even strong "scratch" only 0.17 — the single biggest persona biter), **stale_context_web** (0.17), **injection-composed** (0.30).
- Result-usage/dependent-chain tool families: `link_chain_result_usage` (~0.30), `job_chain_recovery_result_usage` (~0.06). **Structural note:** with the tool suite ~72 cases at 0.5 weight, **one flipped tool case ≈ 0.0069 ≈ the entire 0.007 protection margin** — so getting the dependent-chain tool cases right is disproportionately valuable.

---

## 8. Your winning levers (`ditto-harness` + starter kit)

The model is locked and latency/tokens are neutral, so you control exactly these:

1. **`use_composite = true`** — the harness default is **false** (bare vector search, subject graph unused). The scored baseline sets it true; this turns on the whole ranking stack. **Non-negotiable.**
2. **Retrieval ranking — "Composite V2" (7 signals):** `cosine`, `recency_linear`, `recency_exp` (τ=14 d), `subject_frequency`, `subject_sem_match`, `session_continuity`, `neighbor_density`, fused by an **MLP** (`fixtures/models/mlp-weights.bin`) that predicts per-query weights from 17 aux features. Retrain/replace this MLP; or tune static weights (default 0.65/0.20/0.15).
3. **Cross-encoder reranker + RRF** — the `Reranker` trait is where you plug the **TinyBERT ONNX cross-encoder**; the RRF `k`/`ceWeight` and the ONNX model live in the **starter kit** (not the harness crate), so they're yours to swap/tune. Widens the pool to 20, reranks, truncates.
4. **Thresholds / pool sizing:** `min_similarity` (0.15), `candidate_pool = max(32, 4·limit)`, subject-match threshold, `DEFAULT_SEARCH_LIMIT` (8).
5. **Ingest quality:** the `dream` stage (LLM subject extraction + dedup at 0.75 + graph links) determines what the subject-graph signals can even see. Better subjects → better `subject_frequency`/`subject_sem_match`/`neighbor_density`.
6. **System prompt:** tool-use policy, **abstention discipline**, provenance handling ("my X" vs "@friend's X"), "answer only from this user's graph," "put the bare value in `answer`."
7. **Agent-loop hygiene:** `max_turns` (8), loop detection (3 identical calls) — keep tool budgets tight to protect the tool-efficiency gate.

**Extension traits you implement/override:** `Embedder`, `Model`, `WeightPredictor` (MLP), `Reranker` (cross-encoder+RRF), `EventHandler`.

---

## 9. Strategy — a concrete path

1. **Baseline first (free):** `cargo run -- seed-user && cargo run -- mem-eval --k 10 && cargo run -- evaluate` → see your composite vs the ~0.24 stock baseline and, crucially, `mem-eval` recall@k (retrieval quality isolated from the LLM).
2. **Fix the free wins:** ensure `use_composite=true`; add a tool-use system prompt (the stock kit scores 0 on `calendar_create` purely because it never selects the tool); enforce abstention + provenance rules.
3. **Attack the memory headroom:** the score lives in **retrieval recall** — an ideal full-context reader scores ~0.85 where the stock retriever gets ~0.08; the answers *are* in the store. Improve the reranker + MLP + subject graph until `mem-eval` recall@k climbs, then target the reasoning families (multi-hop-deep, lifecycle-deep-read, near-miss-abstention, temporal-arithmetic) — the biggest, most-winnable ~24%.
4. **Protect the integrity gates:** paraphrase-consistency, transform-robustness, tool-efficiency, no canary leaks, no memory-over-call. In v7 these are up to −40% each and multiply.
5. **Practice on rotating data:** `cargo run -- practice --n 20` (fresh seeds, like the validator) to avoid overfitting `evaluate`'s fixed set.
6. **Submit only when you clearly beat the champion band:** you need `champion + max(0.007, statistical band)`. Predicted champion tier is ~**0.57–0.66** composite after robustness gates (oracle = 1.0). First-to-submit wins ties; copies are quarantined.

## Verdict (deepened)
This is a **serious, well-defended engineering competition** — arguably the most sophisticated anti-gaming design in this workspace. The upside: **CPU-only, model-frozen, fully reproducible offline, forking the starter kit is allowed, and ~24% of the suite is winnable headroom the stock kit leaves on the table.** The cost: to reach the top-5 (let alone champion at 65%) you must build genuinely better **retrieval + reranking + reasoning + integrity discipline** than the field, then clear a statistical dethrone band. It rewards real ML/retrieval engineering, not operational tricks — a very different game from SN101.

---
*Sources: local clones `ditto-subnet`, `dittobench-api`, `dittobench-datagen`, `ditto-harness`, `dittobench-starter-kit` (READMEs, docs/, and source). Figures are from repo code/docs as of the cloned commit — re-check `GET /api/v1/public/bench/config` for the live bench version and locked model before committing TAO.*
