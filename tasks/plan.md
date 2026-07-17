# PLAN — Usability Auditor

Implementation plan for [`SPEC.md`](../SPEC.md). Read-only planning artifact — no code
changes are made by this document.

- **Spec:** [SPEC.md](../SPEC.md)
- **Date:** 2026-07-15
- **Approach:** vertical slices — each phase delivers one complete, runnable path, then
  the next thickens it. No horizontal "build all references, then all personas" layering.

---

## 1. What we're building (recap)

The plugin's standard triad — **persona** (`agents/usability-auditor.md`), **skill**
(`skills/usability-audit/SKILL.md`), **command** (`commands/usability-audit.md`) — plus
the **shared `.ux/audits` report contract** every future suite auditor (a11y, perf)
inherits. Findings-only: it never edits host application code.

## 2. Prior art that shapes the plan

- **v1 sibling repo** (`../ux-agent-skills`) already ships auditor personas
  (`accessibility-auditor`, `performance-auditor`) with YAML frontmatter + trigger
  phrases, and a `/ux-ship` parallel fan-out that merges auditor reports into a go/no-go.
  Our shared contract is what makes that fan-out possible for the suite. We reboot in v2
  rather than copy, but we match the frontmatter and reporting conventions.
- **Render-vs-source honesty rule** (from the ecosystem web-performance-auditor's
  "metric-honesty rule" and v1's `contract-vs-render`): a usability claim about what a
  user *perceives at runtime* (system-status feedback, error recovery, interaction
  latency) cannot be asserted from static source. **In static mode, such findings are
  labeled `potential — unverified` and the report says why.** This is a first-class
  requirement, folded into Slice 1 and enforced in Slice 4.

## 3. Dependency graph

```
                 ┌─────────────────────────┐
                 │ Report contract (§3.4)  │  ← foundational, shared by whole suite
                 └───────────┬─────────────┘
                             │
   references/ (Nielsen ✓)   │
        │                    │
        ▼                    ▼
   ┌─────────┐        ┌──────────────┐        ┌──────────────┐
   │ Persona │◄───────│    Skill     │◄───────│   Command    │
   └─────────┘        └──────────────┘        └──────────────┘
        ▲                    ▲
        │                    │
   3 more framework refs     hybrid live-mode + index + validation
   (Shneiderman, AI, NPCIS)  (Slices 2 & 4)
        (Slice 3)
                             │
                             ▼
                     ┌──────────────┐
                     │ Docs/Release │  ← depends on everything
                     └──────────────┘
```

**Leaf inputs:** the report contract + Nielsen reference (already in `references/`).
**Everything downstream** builds on those. Command is the last wiring step per slice.

## 4. Vertical slices (phases)

Each slice is independently demoable end-to-end.

### Phase 1 — Walking skeleton (static, Nielsen-only) ⭐ MVP
The thinnest complete path: `/ux-agent-skills:usability-audit <repo-path>` reads host
source, applies **Nielsen's 10** only, and writes ONE valid report to `.ux/audits/`
conforming to the shared contract — including the render-vs-source honesty labeling.
Proves the contract, the write location, and the safety invariant before any breadth.

**Delivers:** report contract doc, minimal persona, static-path skill, command wiring,
a real report file. **Frameworks:** Nielsen only. **Mode:** static only.

→ **CHECKPOINT A** — human reviews a real generated report + the contract before we
  invest in breadth. Cheapest point to correct format/severity/tone.

### Phase 2 — Live & hybrid evidence
Add browser-MCP live inspection: navigate a target URL, screenshot key states into
`.ux/audits/assets/`, exercise flows, read the a11y/DOM tree. Implement the hybrid
auto-selection logic and record actual `mode` in frontmatter. Runtime heuristics now get
*verified* (not `potential`) findings. Ask-first gates on server start / navigation.

**Delivers:** live + hybrid skill paths, asset capture, mode detection.

### Phase 3 — Full four-framework stack
Author the three remaining skill-local references (`shneiderman-8`,
`ai-design-heuristics`, `npcis`) and expand persona knowledge base + skill evaluation to
apply all four, mapping every finding to its exact framework citation.

**Delivers:** complete framework coverage per SPEC §4.

→ **CHECKPOINT B** — human reviews a full-stack live report for finding quality,
  framework attribution accuracy, and false-positive rate.

### Phase 4 — Contract hardening & suite portability
Rolling `index.md` append; frontmatter schema validation (counts == findings);
coverage/appendix honesty (no silent gaps); idempotency (new file, never overwrite);
the safety invariant test; and a mock second auditor (`auditor: accessibility`) proving
the contract is portable across the suite.

**Delivers:** the guarantees in SPEC §5.2 + §3.4 index behavior.

### Phase 5 — Docs & release
README section (auditor + shared report contract), CHANGELOG entry, `plugin validate`,
and a dogfood run against a real sample flow.

→ **CHECKPOINT C** — go/no-go: dogfood report is genuinely useful; DoD (SPEC §7) met.

## 5. Slicing rationale

- **Contract first, in Phase 1** — it's the suite-wide interface; getting it wrong later
  is expensive. Phase 1 already emits a report, so we validate the contract immediately.
- **Static before live** — static is the zero-dependency path (no running app, no browser
  gating), so it's the fastest route to a demoable report and to locking the format.
- **Breadth (frameworks) after depth (one working path)** — avoids authoring four
  reference files before we know the report shape is right.
- **Hardening after behavior** — validation/index/portability are meaningful only once
  reports actually exist.

## 6. Risks & mitigations

| Risk | Mitigation |
|------|-----------|
| Report format churns after references exist → rework | Lock format at Checkpoint A, before Phase 3 breadth. |
| Auditor edits host code (violates findings-only) | Safety-invariant test in Phase 4; boundary stated in persona + skill from Phase 1. |
| Static-mode findings over-assert runtime behavior | Render-vs-source honesty rule enforced from Phase 1; verified in Phase 4. |
| Browser gating (auth, no dev server) blocks live mode | Hybrid auto-fallback to static; ask-first gates; coverage gaps logged, never silent. |
| Contract not actually reusable by a11y/perf | Mock-second-auditor portability test in Phase 4. |
| Over-copying v1 instead of a clean v2 reboot | Treat v1 as pattern reference only; author fresh against this spec. |

## 7. Verification spine (applies every phase)

After any phase that runs an audit: `git status` in the host repo shows changes **only**
under `.ux/audits/`. Report frontmatter parses; `summary` counts equal findings by
severity. Every finding has evidence + framework citation + fix. No fabricated findings.

## 8. Out of scope (deferred to future suite work)

Meta-command fan-out (`/ux-agent-skills:audit` running all auditors), report
diffing/regression tracking across runs, retention/pruning. The contract enables all
three later; none are built now.

*(Fan-out shipped in Phase 6. Report diffing and retention remain deferred.)*

---

# PLAN — Critical User Journeys (CUJs)

Implementation plan for [`SPEC.md` §9](../SPEC.md). Second capability in the same plugin;
sections 1–8 above cover the usability auditor and still hold unchanged.

- **Spec:** [SPEC.md](../SPEC.md) §9 — approved 2026-07-16
- **Date:** 2026-07-16
- **Approach:** foundations first (three independent, individually-green landings), then
  two vertical slices — author a journey end-to-end, then verify one end-to-end.

## 9. What we're building (recap)

Two triads plus a new file contract. `/ux-spec` interviews the user and writes canonical
journeys to `.ux/cujs/` in the host repo, splicing a generated index into the host's
`SPEC.md`. `/cuj-audit` replays a stored journey against the running app and reports the
exact step that broke, as an `auditor: cuj` report under `.ux/audits/` using the **existing**
shared contract. `audit-cuj` joins the `/ux-audit` fan-out as a fourth suite member.

## 10. What shapes this plan

> ### ⚠️ v1 already has a CUJ system. This is a deliberate reboot, not greenfield.
>
> The sibling repo [`../ux-agent-skills`](../../ux-agent-skills) (v1, actively developed —
> 0.7.0) **already ships a mature CUJ implementation**: `.ux/cujs/<name>.md`, a `spec-cuj`
> skill, a `verify-cuj` skill, `/ux-spec`, `/ux-review`, and `references/cuj-template.md`.
> Same paths, same skill names, same command names. **v1 and v2 cannot be installed
> together** — they collide on marketplace name, plugin name, `/ux-spec`, `spec-cuj`, and the
> `.ux/cujs/` directory itself, in incompatible formats.
>
> This was missed during planning: exploration grepped only this repo, found one README line,
> and concluded "greenfield". §2 above cites v1 as prior art for *auditor personas* and did
> not mention that it owns the CUJ concept outright. It does.
>
> **The decision (2026-07-16): v2 is a deliberate reboot.** Where the two differ:
>
> | | v1 | v2 (this plan) |
> |---|----|----|
> | Journey shape | intent + 4–6 touchpoints + measurable criteria | 10-key frontmatter, per-step observable `expect` |
> | Criteria | numeric thresholds (`< 60s p95`), tied to `DESIGN.md` §7/§8 | observable outcomes, plus post-journey `success_criteria` |
> | Validation | LLM lint via `ux-auditor` | `scripts/validate_cuj.py` + fixtures + CI |
> | Verification | `verify-cuj` — renders, screenshots, diffs `.ux/goldens/` | `audit-cuj` (Phase 9, unbuilt) |
> | Reporting | own audit trail | the shared `.ux/audits` report contract (`auditor: cuj`) |
>
> **Before building Phase 9, read v1's `skills/verify-cuj/SKILL.md`.** It solves the same
> problem and is hardened against three real false-pass incidents we would otherwise
> rediscover: the **empty-set trap** (a "X appears 0 times" criterion is vacuously true
> against zero files — "zero files found is a FAIL, never a pass"), the **contract-vs-render
> doctrine** (a green lint is not evidence about the render), and the **maker/checker guard**
> (a fresh context must grade work it did not make). Rebooting the format is a choice;
> rediscovering those bugs is not.

- **The report contract is reused, not extended.** `auditor: cuj` needs one entry in
  `FRAMEWORKS_BY_AUDITOR` and nothing else. Any pressure to add frontmatter keys is
  pressure to erode comparability — it goes in the Appendix instead (SPEC §9.4).
- **The two test traps (AGENTS.md §"The two test traps") drive the commit boundaries.**
  `test_evals.py` globs `skills/*/SKILL.md` and reds *instantly* without a matching eval
  case — so each SKILL.md and its case land in **one commit**. `test_components.py` and
  `DOC_FILES` are hardcoded and fail **silent** — so every new component's `check_*()` and
  doc path land with the component, never "later".
- **`/ux-spec` is the plugin's first host write outside `.ux/`.** The audit invariant must
  come out of this *unchanged*: an audit run that touches `.ux/cujs/` is still a violation.
  That is a test (T7.5), not a promise.
- **Idempotency is only achievable because the index block is a pure function of
  `.ux/cujs/`.** Hence a script generates it (`validate_cuj.py --index`), never prose.

## 11. Dependency graph

```
   SPEC §9 ✅ (approved — was PS)
       │
       ├──────────────┬──────────────────┐
       ▼              ▼                  ▼
  ┌──────────┐  ┌─────────────┐   ┌──────────────┐
  │ T7.1-7.3 │  │    T7.4     │   │    T7.5      │   ← mutually independent,
  │ CUJ      │  │ cuj auditor │   │ safety       │     each lands green alone
  │ contract │  │ registered  │   │ allowlist    │
  └────┬─────┘  └──────┬──────┘   └──────┬───────┘
       │               │                 │
       │               │                 │  ✅ CHECKPOINT D
       ├───────────────┼─────────────────┤
       ▼               │                 ▼
  ┌─────────────────────────────────────────────┐
  │ Phase 8 — authoring path (/ux-spec)  ⭐      │  needs contract + allowlist
  └────────────────────┬────────────────────────┘
                       │  ✅ CHECKPOINT E
                       ▼
  ┌─────────────────────────────────────────────┐
  │ Phase 9 — verification path (/cuj-audit)    │  needs contract + registration
  └────────────────────┬────────────────────────┘
                       │  ✅ CHECKPOINT F
                       ▼
              Phase 10 — roll-up  →  Phase 11 — docs/release
```

**Leaf input:** the approved SPEC §9. **Phase 9 depends on Phase 8** only for its behavioral
eval (Sprout has no journeys until `/ux-spec` authors some) — the code paths are independent.

## 12. Vertical slices (phases)

### Phase 7 — Foundations (contract, registration, safety)
Three landings that touch nothing user-facing and are mutually independent: the CUJ file
contract + its validator + its tests; the `cuj` entry in the report validator + fixtures;
the `audit_safety.py` allowlist + its tests. Each leaves CI green on its own and can be
reviewed separately. **Doing these first de-risks the whole capability** — the schema, the
contract reuse, and the safety story are exactly the parts that are expensive to change once
two skills depend on them.

→ **CHECKPOINT D** — human reviews `cuj-contract.md` and a hand-authored sample CUJ. Cheapest
  point to correct the schema, before any skill is written against it.

### Phase 8 — Authoring path (`/ux-spec`) ⭐ first demoable slice
The thinnest complete path: interview → draft → write `.ux/cujs/<id>-<slug>.md` → validate →
ask → splice the host `SPEC.md` index. Includes the `interview-me` fallback with disclosure.

→ **CHECKPOINT E** — human authors a real CUJ against Sprout by answering the interview.
  Reviews journey quality (is `expect` genuinely observable?), the ask-first gate, and the
  index splice. **Stop here for sign-off** — this is the interview's tone and rigor, and it's
  the part a spec can't fully pin down.

### Phase 9 — Verification path (`/cuj-audit`)
Select → validate → replay live → grade (classify, then clamp by `criticality`) → one report
per run → index row. Static mode traces source only and cannot produce a verified pass.

→ **CHECKPOINT F** — **the detection test.** Break a journey deliberately in Sprout; require a
  sev4 naming the correct step. A verifier that only ever passes is worthless, and this is the
  only check that proves it detects rather than narrates.

### Phase 10 — Suite roll-up
`audit-cuj` joins the `/ux-audit` fan-out as a fourth, **conditional** member — skipped with a
reason when `.ux/cujs/` is empty, never a silent pass.

### Phase 11 — Docs & release
README / AGENTS / sub-READMEs / CHANGELOG / `plugin.json` → 0.3.0.

→ **CHECKPOINT G** — go/no-go against SPEC §9.8.

## 13. Slicing rationale

- **Foundations before skills, and all three in parallel** — they share no code, each is
  independently reviewable, and every one of them is a thing that's costly to change later.
- **Author before verify** — there is nothing to verify until journeys exist, and the CUJ
  schema gets its real stress test from a human answering an interview, not from fixtures.
- **Detection proven before roll-up** — no point wiring a fourth auditor into the go/no-go
  before we know it can fail a broken app.
- **Docs last** — same as Phases 1–5; they describe what actually shipped.

## 14. Risks & mitigations

| Risk | Mitigation |
|------|-----------|
| `/ux-spec`'s host write silently widens the audit invariant | `allow` is keyword-only; T7.5 asserts an audit-profile call **still flags** `.ux/cujs/`. Widening cannot happen by accident. |
| Allowlist prefix confusion (`SPEC.md.bak`, `.ux/cujs-evil/`) | Trailing-slash = directory, bare = exact match; both cases are explicit regression tests in T7.5. |
| Index regeneration clobbers user prose | Block is a pure function of `.ux/cujs/`; only bytes between markers are replaced; byte-identical test in T7.3; skill shows the diff before splicing. |
| Interview produces vague CUJs ("it works") | The `cuj-author` persona's value is *refusal* — unobservable `expect` is a statically unenforceable judgement, so it lives in the persona and is reviewed at Checkpoint E. |
| A passing journey (`total: 0`) reads as "ran nothing" | Executive summary leads with "N/N journeys passed, M steps verified"; roll-up must not read a *skipped* run as a *passed* one (Appendix "not observed" is the discriminator). |
| Adding 2 skills re-rolls TF-IDF and breaks existing `top_k: 1` positives | `run_evals.py` is an acceptance gate on T8.3 **and** T9.3 — all four skills, not just the new one. |
| CUJ files leak PII | `authored` has no author field, and T7.2/T7.3 make a stray `authored.by` a **rejection**, not a comment. |
| A new skill goes unverified (silent trap) | Every phase's `check_*()` + `DOC_FILES` edits are acceptance criteria of the same task, not follow-ups. |

## 14a. What Checkpoints D–E actually taught us

Two live runs of `/ux-spec` against Sprout. Everything mechanical held; **every defect was in
the layer no test can reach**, and one class of defect was in the tests themselves. Phase 9
inherits all of it.

### The tests lie in a specific, repeatable way

Four checks in `test_components.py` were written, passed green, and **asserted nothing**:

- `"criticality" in low` — the word was present, the rule was absent. It stayed green through
  a total behavioural failure.
- `"ask" in low` — also satisfied by the word "t**ask**", and this suite's running example is
  a to-do app.
- `"manufactur" in low or "invent" in low and "agreement" in low` — `and` binds tighter than
  `or`, so it degrades to the fallback, and both fallback words appear everywhere.

**Every one came from the same instinct: a broad fallback term in a disjunction.** Prefer one
specific term and let a rewrite fail loudly.

**Mutation-test every check you write, and print the residue.** Three separate mutations
"proved" a check vacuous when the *mutation* was broken — replacing `manufactur` with
`manufacture` leaves the substring intact; excising one of two accepted synonyms leaves the
concept intact. Verify the term is really gone (`grep -c` → 0) before believing the verdict.

### Prose defects the runs found (all now fixed — don't regress them)

| Found | Rule it produced |
|---|---|
| Folded on criticality, then **invented a supporting fact** to justify it | Never manufacture a justification. Inventing *agreement* is still inventing — and worse, because a fabricated step is visible in the file while a fabricated reason lives only in the chat. |
| `interview-me`'s `GUESS:` style laundered a **false** step into a journey | ~~Never offer a guess the user can confirm with "yes".~~ **Superseded — see §14b.** Source may **check** a recalled detail, never **supply** an `expect` — a journey derived from the code tests the app against itself and can never fail. (The source rule stands; the blanket guess ban was too broad.) |
| Narrative colour became an unsatisfiable precondition | Preconditions must be establishable from a fresh install… |
| "Nothing harvested today" — true on run 1, false forever after | …**and re-establishable on a second run.** This one is the mirror: not a journey a broken app passes, but a journey a **working app fails**. A check that cries wolf gets muted, and a muted check is deleted. |
| Offered to `cp validate_cuj.py` into the host repo to dodge a permission gate | Never route around a gate; never copy tooling into the host repo. Blocked and honest beats unblocked and littering. |
| "Question 4 of ~7", then asked four things | "One question at a time" is countable: one `?` per turn. |
| Summarised validator output instead of pasting it | Show the tool's real output. A skill arguing that unfalsifiable claims are worthless cannot launder its own. |

### Open, and inherited by Phase 9

- **How does the verifier establish a precondition?** The interview asks *what must be true*;
  nothing yet says *how a verifier gets there*. `audit-cuj` has to answer this or every
  stateful journey reports "skipped".
- **The `interview-me` fallback branch has never executed** — it was installed on both runs.
  ~200 lines of `references/interview-fallback.md` are untested.
- **`agents/README.md` loads as a phantom persona named "README"** (no frontmatter, but
  components are discovered as `agents/*.md`); `commands/README.md` likewise. Both are in the
  always-on token budget. AGENTS.md step 8 *instructs* maintaining those catalogs, so the
  convention manufactures them. Unfixed — it's a repo-structure decision.
- **A directory install resolves the plugin root to the dev tree**, so the harness gates the
  skill's reads of its own references. And the install is a **snapshot**: run
  `claude plugin marketplace update ux-agent-skills` or you test yesterday's code.

## 14b. Scoped guessing — the Checkpoint-E guess ban, refined (2026-07)

Checkpoint E banned `interview-me`'s guesses outright after one guessed step ("click the
autofocused input → it focuses") got a "yeah, right" and entered a `critical` journey. The
ban held, but a live authoring run proved its cost: `interview-me`'s whole method is a guess
per question, so a no-guess interview is ~20 open questions with the engine removed —
laborious, and no better than the fallback.

**The refinement: guess the description, elicit the oracle.** The sycophancy failure only
bites on the three fields something downstream is *graded* against — each step's `expect` and
the `success_criteria` (`audit-cuj`'s pass/fail) and `criticality` (the severity clamp).
Those stay `elicited, never guessed`. The other seven descriptive fields may be guessed
freely; nothing scores them, and a guessed **action** is still tripwired by its `expect`
being asked open. This is the same line the persona already drew for source ("checks, never
supplies the `expect`"), generalized: a guess — from the model or the source — proposes
framing but never supplies what gets graded.

Both original incidents stay guarded (the false `expect`; the folded `criticality`). Recorded
here because it reverses an approved Checkpoint-E rule, the way the `audit_safety` baseline
and `version` provenance reversals were. Expressed in `agents/cuj-author.md`,
`skills/spec-cuj/SKILL.md`, `references/interview-fallback.md`, `commands/ux-spec.md`, SPEC
§9.5; the two `"guess" in low` checks were rewritten to assert the scoped rule (a bare
`"guess"` now passes vacuously — the §14a disease), anchored on `elicited, never guessed` and
`guess freely`.

## 15. Verification spine (applies every phase)

All five suites stay green throughout — `for t in tests/test_*.py; do python3 "$t"; done`.
Additionally: any phase touching a skill description re-runs `python3 evals/run_evals.py`;
any phase touching the host re-runs `scripts/audit_safety.py` under **both** profiles.

## 16. Out of scope

Report diffing across runs; `.ux/cujs/` retention; CUJs as a CI gate; generating E2E tests
from journeys; auto-deriving audit scope from CUJs. All are enabled by this work; none are
built now.
