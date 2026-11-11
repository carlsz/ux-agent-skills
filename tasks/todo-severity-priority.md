# TODO — One scored scale: priority (P0–P3), severity as its stated input

Execution companion to [`plan-severity-priority.md`](./plan-severity-priority.md). Slice 1 is
specified in full; later slices are stubs until slice 1 lands.

**Slice 1 ships alone.** It is prose-only: no schema change, no validator change, no fixture
change. It fixes the borderline-call problem in the vocabulary the suite uses *today* — the
`sevN` → `PN` rename is slice 2, and mixing the two here would make slice 2's diff unreadable.

---

## Slice 1 — The rubric discriminator ⭐ *(first: fixes the reported pain, blocks nothing)*

**The problem it solves.** [Contract §4](../skills/usability-audit/references/report-contract.md)
gives five one-line labels and no method. An auditor at the 0/1 margin has a number to produce and
nothing to produce it with, so it guesses — and two runs guess differently. Nielsen's scale was
designed to be *averaged across 3–5 evaluators*, which is what smooths that margin; a single agent
has no such smoothing. Restoring his three factors gives the margin something to answer.

### T1.1 — Contract §4 gains the derivation
- [x] §4 states *how* to land on a score, not just what the scores mean.
- **Files:** `skills/usability-audit/references/report-contract.md` (§4).
- **Acceptance:** §4 names Nielsen's three factors — **frequency** (how many users meet it),
  **impact** (how hard to overcome), **persistence** (once, or every time) — as the operative
  method, and requires the Severity field's justification to reference them. The 0-vs-1 test is
  stated in one line: **1 means a user notices; 0 means no user behaviour changes.** The existing
  0–4 table and the NN/g link both survive. Vocabulary stays `sevN`.
- **Verify:** `python3 tests/test_docs.py` (the NN/g link and relative links still resolve);
  `python3 tests/test_report_contract.py` (prose-only — fixtures must be untouched and still pass).
- **Deps:** none.

### T1.2 — Contract §4 gains the two guards
- [x] A rubric without a volume control produces a long tail; one without a ceiling produces
      inflation. Neither is currently addressed.
- **Files:** `skills/usability-audit/references/report-contract.md` (§4).
- **Acceptance:** two operative instructions, phrased as rules and not as advice — (a) a long tail
  of cosmetic findings buries the ones that matter, so `sev1` is for what genuinely warrants a
  reader's attention; (b) not every finding can be a `sev4`, and a report where most are has
  mis-rated rather than found a catastrophe.
- **Why the contract and not only the personas:** `ux-audit` maps *external* tool output onto this
  scale ([`SKILL.md:110`](../skills/ux-audit/SKILL.md)) without going through either persona. A
  guard that lives only in a persona does not reach the accessibility or web-performance findings.
- **Verify:** `python3 tests/test_docs.py`.
- **Deps:** T1.1.

### T1.3 — SPEC §4 mirrors the method
- [x] `SPEC.md` §4 carries the same table and would now understate the contract.
- **Files:** `SPEC.md` (§4, *Severity rubric*, ~line 196).
- **Acceptance:** the three factors appear as design rationale — *why* this scale is reproducible —
  plus a one-line pointer that the contract is the operative form, matching the existing
  contract → `validate_report.py` "executable form" convention. Do not duplicate the full
  procedure in both files.
- **Verify:** `python3 tests/test_docs.py`.
- **Deps:** T1.1.

### T1.4 — Name the §4 ↔ §9.4 divergence
- [x] The honest half, and the one most likely to be skipped. §4 presents 0–4 as Nielsen's
      severity; [`SPEC.md:533`](../SPEC.md) §9.4 defines the same 0–4 for `audit-cuj` as a
      task-impact ladder. Both are shipping, and nothing tells a reader they are different
      instruments.
- **Files:** `SPEC.md` (§4 and §9.4).
- **Acceptance:** §4 records that `audit-cuj` derives its score by a different method (§9.4) and
  that the two numbers are **not interchangeable**; §9.4 says the same in reverse. Written as a
  statement of current fact — **no reference to the plan, the slices, or a future reconciliation**;
  shipped docs do not carry planning vocabulary.
- **Not in scope:** fixing the divergence. That is slice 3, where one ladder replaces both. Slice 1
  only stops the contract from implying a single method where two exist.
- **Verify:** `python3 tests/test_docs.py`.
- **Deps:** T1.1.

### T1.5 — Both personas reach the method
- [x] `usability-auditor` restates the 0–4 table inline (lines 60–68) and would otherwise keep a
      methodless copy; `cuj-auditor` needs the same reachability for its own scale.
- **Files:** `agents/usability-auditor.md` (§*Severity scale*, and the Rules list at line 106),
  `agents/cuj-auditor.md` (§*Severity: classify, then clamp*).
- **Acceptance:** each persona's severity section **names the three factors and links to contract
  §4** rather than restating the procedure — the one-owner/consumers-link-across rule that
  `report-contract.md` and `auth-handoff.md` already follow. Each Rules list gains the long-tail
  rule and the inflation guard as one-liners.
- **No change needed:** [`usability-audit/SKILL.md:100`](../skills/usability-audit/SKILL.md)
  already defers to *"the severity rubric from the contract"*, so it inherits T1.1 for free.
  Confirm this rather than editing it.
- **Verify:** `python3 tests/test_components.py`.
- **Deps:** T1.1, T1.2.
- **Delivered (corrects the acceptance above).** `cuj-auditor` did **not** get the three
  factors. Its stage-1 ladder is task impact, so claiming Nielsen's factors there would
  contradict T1.4's divergence note in the same release. It carries the divergence note
  instead — *"they are different claims"* — plus both guards. `usability-auditor` got the
  factors as specified. The test wiring follows the same split.

### T1.6 — Test wiring (**the silent trap**)
- [x] **No test asserts on the contract's prose.** `test_docs.py:40` opens it for link-checking
      only, and `test_components.py:160,255` merely check that the *skills* mention the string
      `report-contract`. So without this task every edit above can be reverted and the whole
      suite stays green.
- **Files:** `tests/test_components.py`.
- **Acceptance:** a new `check_severity_rubric()` following
  [`check_auth_handoff_reference()`](../tests/test_components.py)'s shape — it is a procedure, not
  a framework lens, so it does **not** belong in `check_references()`. It `_flatten()`s the
  contract (hard-wrapped prose: a probe like `"no user behaviour changes"` breaks the moment a
  sentence rewraps), asserts the three factor names, the 0/1 test, and both guards, and is wired
  into `CHECKS`. Add a per-persona assertion that each names the three factors.
- **Verify:** `python3 tests/test_components.py`; then delete one factor from the contract and
  confirm it goes **red** — an unwired check is the failure mode this task exists to prevent.
- **Deps:** T1.1–T1.5.

### ⛳ Checkpoint 1 — the margin is reproducible
- [x] All 7 `tests/test_*.py` green.
- [x] `check_severity_rubric()` is in `CHECKS` and fails when a factor is removed (verified by
      deliberate break, not by reading the code).
- [ ] **Calibration spot-check — NOT SATISFIED.** Take 5 borderline findings, re-rate them under
      the new §4 blind, and confirm the 0/1 calls are reproducible. **Blocked:** every fixture
      carries `sev1: 0` and `grep -rn '^### \[sev1\]' tests/fixtures/` returns nothing — the
      corpus never exercises the margin this slice exists to fix. A real calibration needs a live
      Sprout run (host repo, not in this worktree). Slice 2 rewrites the fixtures anyway; add a
      `sev1` case there and calibrate then. This is the only item that tests whether the slice
      *worked* rather than whether it landed, so it stays open.
- [x] **No rename leaked in:** `grep -rn '\bS[0-4]\b' <changed files>` → 0 hits. Slice 1 must not
      half-introduce slice 2's vocabulary.
- [x] No fixture under `tests/fixtures/` modified — `git diff --stat` confirms prose files only.
- [ ] **Human review** — the three factors are the whole basis for keeping the NN/g citation. If
      they read as decoration, the slice has not done its job.

---

## Slice 2 — The contract speaks schema 3

**Boundary adjusted from the plan.** The plan's table put the `Priority` *field* in slice 3.
Moved here: the field is part of the shape the validator enforces, and leaving it out means
writing every schema-3 fixture twice. The seam is now **contract vs. consumers** — slice 2 is
the contract, validator and fixtures; slice 3 is the skills and personas that produce reports
against it. Slice 3 keeps the derivation (§9.4's ladder generalized, the criticality
adjustment, removing T1.4's divergence note).

### T2.1 — Validator: dispatch on `schema`
- [x] `validate_report.py:76` is a flat `!= 2`. Schema-2 reports must keep validating forever
      (contract history rule), so the rating vocabulary becomes per-schema.
- **Files:** `scripts/validate_report.py`.
- **Acceptance:** `KNOWN_SCHEMAS = (2, 3)`; `RATING_KEYS`, the finding-heading regex and
  `FINDING_FIELDS` all keyed by schema. Schema 2 = `sev4..sev1` / `[sevN]` / 5 fields /
  reject `sev0`. Schema 3 = `P0..P3` / `[PN]` / 6 fields (`Priority` added). Reconciliation
  and the body-vs-summary count checks work off the dispatched vocabulary, not a module
  constant. Unknown schema → one clear error, not a crash.
- **Verify:** `python3 tests/test_report_contract.py` green on the unchanged schema-2 fixtures
  **before** any fixture is added — that is the regression proof.
- **Deps:** none.

### T2.2 — Validator: the index accepts either shape
- [x] The index is append-only and shared across runs, so its columns cannot simply change.
- **Files:** `scripts/validate_report.py`.
- **Acceptance:** `validate_index()` accepts the legacy `Sev4..Sev1` header **or** the new
  `P0..P3` header, and checks integer cells positionally in whichever it found. A file
  carrying a legacy table and a new-shaped table below it validates.
- **Open question this exposes:** how a host with an existing index transitions. Documented
  in the contract (T2.3) as *keep the shape you were created with, append a new table below
  when the first schema-3 run lands* — never rewrite prior rows.
- **Verify:** `python3 tests/test_report_contract.py`.
- **Deps:** T2.1.

### T2.3 — Contract: schema 3
- [x] §3, §4, §5 and §7 all describe schema 2 only.
- **Files:** `skills/usability-audit/references/report-contract.md`.
- **Acceptance:** schema history note extended; §3 `summary` shows `P0..P3`; §4 gains the P
  ladder (P0 blocks / P1 significant difficulty or WCAG AA / P2 workaround exists / P3 no
  effect) while **keeping slice 1's severity rubric intact as the reported input**; §5's
  heading becomes `### [PN]` and the field list gains `Priority`; §7 documents both index
  shapes and the transition. Schema-2 behaviour stays documented, not deleted.
- **Verify:** `python3 tests/test_docs.py`, `python3 tests/test_components.py`.
- **Deps:** T2.1.

### T2.4 — Fixtures: regression set + schema-3 twins
- [x] Prove old reports still pass and new ones validate.
- **Files:** `tests/fixtures/valid/`, `tests/fixtures/invalid/`.
- **Acceptance:** every existing fixture stays at `schema: 2`, byte-identical where possible —
  they are the regression proof. Add schema-3 twins. Add schema-3 invalid cases:
  priority/total mismatch, a `[P4]` heading (out of range), and a finding missing `Priority`.
  **Add the `sev1`/`P3` case the slice-1 checkpoint could not calibrate against.**
- **Verify:** `python3 tests/test_report_contract.py`.
- **Deps:** T2.1, T2.3.

### T2.5 — Test the dispatch, both directions
- [x] A dispatch that silently accepts anything is worse than the flat check it replaced.
- **Files:** `tests/test_report_contract.py`.
- **Acceptance:** schema-2 fixtures validate; schema-3 fixtures validate; a schema-2 report
  using `[P1]` headings **fails**; a schema-3 report using `[sev3]` headings **fails**;
  `schema: 4` fails with a clear message.
- **Verify:** `python3 tests/test_report_contract.py`.
- **Deps:** T2.4.

### ⛳ Checkpoint 2 — both schemas live
- [x] All 7 `tests/test_*.py` green.
- [x] Schema-2 fixtures unmodified: `git diff --stat tests/fixtures/` shows additions only.
- [x] Cross-schema confusion fails, verified by deliberate break in both directions.
- [x] **Known gap, opened deliberately.** `render_report_html.py` imports the schema-2
      `FINDING_RE` and so renders a schema-3 report with **zero findings** — exit 0, no
      warning, every finding silently dropped. Measured, not assumed: the schema-3 fixture
      renders 0 cards where the schema-2 one renders 2. Slice 4 closes it. Until then,
      nothing should render a schema-3 report, and slice 4 must not be skipped or
      reordered after slice 5.
- [ ] **Human review** — schema 3 is permanent once a report is written against it.

## Slice 3 — The consumers speak schema 3

**Two corrections to the plan, both found while surveying.**

1. **The clamp is a cap, not a demotion.** The plan's §3 said `medium` → demote one step,
   `low` → demote two. §9.4 actually caps (`medium` max 3, `low` max 2), and the two differ
   for mid-range findings: a `sev3` on a `low` journey caps to `sev2` (one step) but would
   *demote* to `sev1` (two steps). Slice 3 uses a **floor on P** — `medium` no more urgent
   than `P1`, `low` no more urgent than `P2` — which reproduces the existing cap exactly
   under the `sev4→P0 … sev1→P3` mapping. A floor is still a clamp, so
   `test_components.py`'s `"clamp" in low` probes stay valid; only their messages change.

2. **`cuj-auditor` needs the three factors after all.** Slice 1's T1.5 deliberately withheld
   them because its ladder was task impact. Schema 3 requires *both* a `Priority` and a
   `Severity` field on every finding, so the CUJ auditor now assesses both — and that is
   precisely what resolves the divergence T1.4 documented. Each instrument gets its own
   field instead of sharing one scale.

### T3.1 — SPEC §9.4: the shared ladder, and the clamp moves to P
- [x] Stage 1 is a task-impact ladder that duplicates contract §4's; stage 2 caps severity.
- **Files:** `SPEC.md` (§9.4).
- **Acceptance:** stage 1 cites contract §4's `P0`–`P3` ladder rather than restating a
  parallel one, keeping the journey-specific wording for what each rung means (blocked /
  workaround or silent failure / observable mismatch / cosmetic). Stage 2 clamps **priority**
  by `criticality` as a floor: `critical`/`high` unclamped, `medium` no more urgent than
  `P1`, `low` no more urgent than `P2`. A CUJ finding also carries a `Severity` derived from
  §4's three factors. Every justification still names both stages.
- **Verify:** `python3 tests/test_docs.py`.
- **Deps:** none.

### T3.2 — Remove the divergence notes
- [x] T1.4 documented a divergence that this slice removes. Leaving the note in would be a
      lie in the other direction.
- **Files:** `SPEC.md` (§4 and §9.4).
- **Acceptance:** both *"not interchangeable"* / *"different claims"* notes are gone, because
  both auditors now score priority on one ladder and severity on one rubric.
- **Verify:** `grep -c "not interchangeable" SPEC.md` → 0.
- **Deps:** T3.1.

### T3.3 — The CUJ side
- [x] **Files:** `agents/cuj-auditor.md`, `skills/audit-cuj/SKILL.md`,
  `skills/spec-cuj/references/cuj-contract.md`, `skills/spec-cuj/SKILL.md`,
  `scripts/validate_cuj.py` (comment only).
- **Acceptance:** findings are headed `### [PN]` with six fields; stage 1 is the shared P
  ladder, stage 2 the criticality floor on P; severity comes from the three factors; a pass
  is still *not a finding* and `total: 0` still means the journeys passed. `criticality`'s
  description changes from *"caps finding severity"* to *"clamps finding priority"*
  everywhere, including `validate_cuj.py:39`'s comment.
- **Verify:** `python3 tests/test_components.py`, `python3 tests/test_cuj_contract.py`.
- **Deps:** T3.1.

### T3.4 — The usability side
- [x] **Files:** `agents/usability-auditor.md`, `skills/usability-audit/SKILL.md`.
- **Acceptance:** output format is `### [PN]` + six fields; the P ladder is stated or cited;
  the prioritized-fix ordering and the index row are in P counts. Slice 1's three factors and
  both guards survive intact — this slice adds priority, it does not remove severity.
- **Verify:** `python3 tests/test_components.py`.
- **Deps:** T3.1.

### T3.5 — The roll-up's external mapping
- [x] `ux-audit` maps WCAG and Core Web Vitals findings onto the 0–4 severity scale. Those
      tools never produced a severity in the first place — they produce conformance failures
      and measured bands, which map to *priority* far more honestly.
- **Files:** `skills/ux-audit/SKILL.md`.
- **Acceptance:** the mapping targets `P0`–`P3` (Level A blocker on a core flow → P0/P1;
  Level AA → P1; minor/AAA → P2; cosmetic → P3; CWV "poor" → P1, "needs improvement" → P2;
  potential-only anti-pattern → P2/P3 labelled potential). The go/no-go verdict wording is
  **left alone** — slice 5 owns it.
- **Verify:** `python3 tests/test_components.py`, `python3 tests/test_evals.py`.
- **Deps:** T3.1.

### T3.6 — Test rewiring
- [x] **Files:** `tests/test_components.py`.
- **Acceptance:** the two `"clamp"` assertions keep their probe and get messages naming
  priority. Add: both personas state the P ladder; `cuj-auditor` names the three factors
  (reversing T1.5's deliberate omission); the `"different claims"` assertion added in slice 1
  is **removed**, since T3.2 removes what it asserted.
- **Verify:** `python3 tests/test_components.py`, plus a deliberate break on one new probe.
- **Deps:** T3.3, T3.4.

### ⛳ Checkpoint 3 — one ladder, one rubric, two fields
- [x] All 7 `tests/test_*.py` green.
- [x] `grep -rn "not interchangeable\|different claims" SPEC.md agents/` → 0 hits.
- [x] No consumer still tells an auditor to emit `[sevN]`: `grep -rn "\[sevN\]\|\[sev0\]" agents/ skills/*/SKILL.md` returns only schema-2 historical references.
- [x] **Two of my own bugs, caught by the suite rather than by review.** (a) `\u00a7` was
      double-escaped in the slice-1 and slice-2 edit scripts and landed literally in
      `test_components.py` — in six places, four of them inside *error-message strings*, so a
      failing check printed `report-contract \u00a74:` to the user. Fixed. (b) Rewrapping a
      line in `audit-cuj/SKILL.md` split `a skip is not a finding` across a newline, and that
      probe reads `body.lower()`, not `_flatten(body)` — exactly the hard-wrap trap
      `_flatten`'s docstring was written about. Rewrapped rather than loosening the probe.
- [ ] **Human review** — the CUJ auditor now rates two things per finding where it rated one.
      If the Severity field reads as filler on journey findings, the divergence was resolved
      on paper only.

## Slice 4 — The renderer speaks both schemas

Closes the gap slice 2 opened deliberately: every auditor now emits `[PN]`, and the renderer
still reads `[sevN]`, so a report rendered today loses **every finding, silently, at exit 0**.

### T4.1 — A per-schema rating view
- [x] `render_report_html.py` imports the schema-2 `FINDING_RE` and hardcodes `sev` in the
      heading strip, the badge, the summary bar and the card classes.
- **Files:** `scripts/render_report_html.py`.
- **Acceptance:** a `RATING_VIEW` table keyed by schema supplies the heading pattern, the
  strip pattern, display order, labels, summary-key format and the **ramp position**. The
  CSS ramp is positional — 4 is hottest, 1 coolest — so `P0` renders in the `sev4` colour
  and the stylesheet is untouched. `test_render_html.py:122`'s `.finding sev` probe keeps
  working for both schemas because the *class* stays positional while the *badge text*
  follows the schema.
- **Verify:** `python3 tests/test_render_html.py`.
- **Deps:** none.

### T4.2 — Don't silently render nothing
- [x] A report whose `schema` is absent or unrecognised must not fall through to "zero
      findings" — that is exactly the failure this slice exists to fix, and a future
      schema 4 would reproduce it.
- **Files:** `scripts/render_report_html.py`.
- **Acceptance:** an unknown schema picks the vocabulary **the body actually uses**, by
  trying each pattern, rather than defaulting blindly.
- **Verify:** render a fixture with `schema:` mangled; findings still appear.
- **Deps:** T4.1.

### T4.3 — The `Priority` field renders
- [x] `FINDING_FIELD_RE` lists five field names; a sixth field is invisible to it.
- **Files:** `scripts/render_report_html.py`.
- **Acceptance:** `Priority` joins the alternation and the card's row order, between
  Violation and Severity. A schema-2 card simply has no Priority row.
- **Verify:** `python3 tests/test_render_html.py`.
- **Deps:** T4.1.

### T4.4 — Tests cover both schemas
- [x] The inline fixture in `test_render_html.py` is schema 2 only.
- **Files:** `tests/test_render_html.py`.
- **Acceptance:** a schema-3 inline fixture alongside it; assert the `P1` badge text, the
  `sev3` ramp class on that card, a rendered Priority row, and that the schema-2 fixture
  still renders identically. Assert the real schema-3 report fixture renders its 3 findings.
- **Verify:** `python3 tests/test_render_html.py`, plus a deliberate break.
- **Deps:** T4.1–T4.3.

### ⛳ Checkpoint 4 — nothing renders empty
- [x] All 7 `tests/test_*.py` green.
- [x] `tests/fixtures/valid/usability-20261111-143000.md` renders **3** finding cards
      (it rendered 0 before this slice — the number that proves the gap is closed).
- [x] The schema-2 fixture still renders 2.
- [x] **Regression proven, with the diagnostic slice 2 lacked.** Forcing `_view()` back to
      schema-2-only reproduces the gap, and the suite now says so in the exact terms that
      were missing: *"usability-20261111-143000: 0 finding cards, summary.total is 3"*.
      Adding the schema-3 report to the existing per-report sweep is what bought that — the
      cards-reconcile-with-total check already existed and simply had nothing to catch.
- [x] **Self-caught while writing the tests:** a failure message contained a stray
      non-English word, and a badge assertion was brittle string-slicing that would pass on
      malformed HTML. Both replaced with explicit per-badge checks.
- [ ] **Human review.**

## Side work — charset guard *(out of band, done)*

Not a slice. It came out of slice 4's self-caught stray non-English word: that slip sat in an
f-string in a failure branch, so a green suite could never have surfaced it, and the product
here is prose — the personas' instructions *are* the behaviour.

- [x] **`tests/test_charset.py`.** Flags Unicode letters (`L*`) and invisible/format
      characters (`Cf`/`Zs`/`Cc`) across every tracked text file. Category-based, not an
      enumerated allowlist: the repo legitimately uses 38 distinct non-ASCII glyphs (em
      dashes, box drawing, `§`, `≥`, arrows, emoji), and an enumeration would need editing
      whenever prose grew one — which is how a guard becomes a nuisance and gets deleted.
- [x] **It globs `git ls-files`,** deliberately unlike `DOC_FILES` in `test_docs.py`. The
      whole value is covering the file nobody thought to list. Same reasoning as
      `check_discovery_dirs()` being the one glob in `test_components.py`.
- [x] **Both empty allowlists are kept present** (`ALLOWED_INVISIBLE`, `ALLOWED_LETTERS`),
      for the reason `EXTRA_BY_PROFILE["audit"]` stays `()`: the empty collection records
      that the exception was considered, so widening it is a conscious act with a reason.
- [x] **`_self_check()` runs from `main()`** — five planted samples (a foreign-script
      word, a homoglyph inside an English word, a ZWSP, an NBSP, a Trojan-Source bidi
      override) must yield exact finding counts, and the deliberate glyph set must come back
      unflagged. Both halves matter: without the second, an over-flagging scanner would pass.
      A green run therefore means *clean*, not *never looked*. Same discipline as
      `test_safety.py` asserting through `audit_safety.main()`.
- [x] **Mutation-proved, both directions.** Monkeypatching `scan_text` to stop flagging
      letters makes the self-check report *"a foreign-script word should yield 6 finding(s),
      got 0"*; making it flag every non-ASCII byte trips the deliberate-punctuation half. So
      the self-check is not vacuous.
- [x] **The samples are built with `chr()` from code points — not literals, and not `\u`
      escapes.** This is the sharpest thing the guard found, and it found it on its author:
      the file was first written with `\u0434…` escapes, and those were emitted as the
      literal characters they denote. The self-check still passed, because `"\u0434"` and
      the literal are the same runtime string — the *source* was wrong, not the behaviour.
      Only scanning this file revealed it: 16 findings, including a trailing comment in
      Cyrillic that I had not intended to write at all. `chr(0x434)` has no literal form to
      collapse into. The docstring says so, because the obvious "simplification" re-breaks it.
- [x] **Found 3 real pre-existing defects**, end-to-end through `main()`: zero-width spaces
      at `scripts/render_report_html.py:12` (×2) and `tests/test_render_html.py:6`, all in
      docstrings after a slash (the typographic line-break hint), from `d23d90a8`/`6dd902bd`
      on 2026-07-17. Removed. That catch *is* the end-to-end proof; no planting needed.
- [x] **Measured what the existing suite would have done.** A Cyrillic homoglyph planted (in
      memory) into `agents/usability-auditor.md` is caught by the guard at `3:162` and missed
      by `test_components.py` and `test_docs.py`. The probes are substring checks, and
      `"usability audit"` occurs 3× in that file — so even a homoglyph *inside* a probed
      phrase leaves the other occurrences matching and the suite green.
- [x] **No wiring needed.** CI loops over `tests/test_*.py`, so the file is picked up
      automatically — it dodges both test traps.
- [ ] **Slice 6 owes it a line** in AGENTS.md's "Running the checks" block.
- [ ] **Human review.**

- [x] **It recurred three times while being written about** — in the guard's own
      docstring, in its samples, and in this very checklist entry. Each time the guard
      caught it within one command. That is the whole argument for having it: the slip is
      not rare, it is invisible, and no amount of care substitutes for a scan.

**Known limit, stated plainly:** this catches foreign-script letters, invisibles and
homoglyphs. It cannot catch an *English* word that does not belong — which in a
Markdown-is-the-product repo is the larger risk, and still rests on reading the diff.

## Slice 5 — Roll-up

Replace the binary verdict with a priority distribution. Plan §9 resolved this as *drop*, not
rename: a ship call needs release context SPEC §6 forbids the suite from inventing, and the
borderline-call confusion the user reported came from forcing a binary onto a judgement.

**Two things the plan's stub missed, found while reading:**

1. **No roll-up fixture exists.** `grep -rln rollup tests/fixtures/` is empty, so
   `_render_rollup()` (`render_report_html.py:675`) is *entirely untested* — the dashboard has
   no regression net at all. Slice 4's lesson applies: build the net before changing the thing.
2. **The eval case cannot wait for slice 6.** `evals/cases/ux-audit.json:7` is a **positive**
   trigger reading *"Give me a go/no-go UX verdict across all the quality auditors"*. Tier 2
   builds its corpus from each `SKILL.md` description, so dropping "go/no-go" from the
   description breaks that positive immediately. The plan's §7 put eval updates in slice 6;
   that sequencing is wrong and this slice absorbs the `ux-audit.json` part.

**The design hazard to respect.** Dropping the verdict does not remove the false-clean read,
it *moves* it: `0 × P0 · 0 × P1` reads as "ship it" to a human exactly as a GO banner did. So
the distribution must never stand alone — coverage sits adjacent to it, and an all-zero
distribution from a run that skipped auditors renders as a *warn*, not a pass. This mirrors the
cuj `total: 0` verified-pass vs. nothing-verified split the renderer already implements.

### T5.1 — A roll-up fixture, before any change
- [x] `tests/fixtures/valid/rollup-20261111-150000.md` — 3 auditors run, 1 skipped with a
      reason, a priority distribution, a named top finding, an `Access:` line.
- [x] `rollup-20261111-160000.md` for the hazard: all-zero counts with 3 of 4 auditors
      skipped, which must not render as a clean pass.
- [x] **Baseline measured before changing anything**, and it justified building the net
      first: with `verdict` absent the old renderer emitted
      `banner verdict nogo` + `🔴` + **an empty `<b></b>`** — a blank red alarm — for *both*
      fixtures. Nothing had ever rendered a rollup in tests, so nothing caught it.
- [x] Both wired into `test_render_html.py` for determinism + self-containment.

### T5.2 — Frontmatter: `verdict` out, `priorities` in
- [x] `verdict: go|no-go` → `priorities: {p0,p1,p2,p3}`, plus `auditors_skipped`. No schema
      bump: roll-up frontmatter is outside the report contract and `validate_report.py`
      never reads a rollup (verified by grep, not assumed). `auditors_skipped` was already
      the intended shape in `tasks/plan-html-report.md:60`.

### T5.3 — The renderer's dashboard
- [x] `_distribution_banner()` replaces the verdict banner. Ramp from the worst non-empty
      priority: P0 → `alert`, P1 → `warn`, else `info`. No GO/NO-GO word, no pass/fail icon.
- [x] All-zero + skips → `warn headline` *"No findings, partial coverage … not a clean bill
      of health"*. All-zero + full coverage → `pass headline`. Same discriminator
      `_pass_banner()` draws for a cuj `total: 0`.
- [x] **CSS renamed, not just rewired.** A class literally named `.nogo` cannot survive
      dropping the go/no-go call: `.nogo` → `.alert`, `.verdict` → `.headline`, `.go` deleted
      (it duplicated `.pass`), and `text-transform:uppercase` dropped — it existed to shout
      GO/NO-GO. Checked first that no test asserted on any of them; only `banner pass` /
      `banner warn` are asserted, and both are reused.

### T5.4 — The skill
- [x] Step 6 rewritten: distribution + the highest-priority finding **named** (a count says
      how much, not what broke) + coverage + an explicit *"no overall go/no-go verdict, and
      this is deliberate"* with the §6 reason. Residual `sev4`/`sev3` wording gone.
- [x] Step 2's `Access:` rationale now attaches to the distribution; step 8 and the exit
      criteria updated.

### T5.5 — Description and routing *(absorbed from slice 6)*
- [x] Description states the real output **and keeps `"go/no-go UX verdict"` as a trigger
      phrase.** Users will type it for years; routing them correctly and then being honest
      about the output beats failing to route. `test_evals.py`: **15/15 rank-1**, so the
      positive trigger in `ux-audit.json:7` is still satisfied.
- [x] **Slice boundary corrected mid-slice.** The spec above deferred all docs to slice 6,
      but that conflated *stale wording* with a *false statement*. Anything asserting the
      roll-up **produces** a go/no-go became untrue, so it moved into this slice: `SPEC.md`
      §9.5 + §10.6, `AGENTS.md`, `commands/ux-audit.md`, `commands/ux-review.md`,
      `skills/render-report/SKILL.md`, `evals/cases/ux-audit.json`,
      `evals/cases/render-report.json`, `evals/README.md`. The eval `expected_output`
      strings were the sharpest case: a Tier 3 run would have graded against a verdict that
      no longer exists.

### T5.6 — The silent trap, for real this time
- [x] The `or` chain is gone, replaced by five probes: `priorities:` present, the
      distribution headline, the named worst finding, the no-ship-call statement, and the
      empty-is-not-a-pass rule. The no-ship-call probe is asserted in the **positive**,
      because "go/no-go" still appears in the body in the sentence explaining its absence —
      a `not in` probe would be both fragile and backwards.
- [x] Fixed the stale message at the `"normaliz" or "map"` probe: it still said *"the 0-4
      severity scale"*. Slice 3 changed the mapping and missed the message.

### ⛳ Checkpoint 5 — the distribution cannot read as a pass it did not earn
- [x] Both fixtures render; `alert headline` with a P0 present, `warn headline` for all-zero
      with skips, and `banner pass` absent from the latter.
- [x] **Regression-proved, and the proof itself needed correcting.** On a fully gutted skill
      the old `or` chain is **green** while all five new probes **fail**. My first attempt
      gutted the raw body and "highest-priority finding" survived — because at `SKILL.md:194`
      the phrase straddles a line break and `_flatten()` rejoins it. The probe was right and
      my proof was wrong; it is also a live demonstration of why `_flatten()` exists.
- [x] Full suite green, `test_evals.py` and `test_charset.py` included.
- [ ] **Human review.**

**Deliberately left for slice 6:** README (5 places), CHANGELOG (2), AGENTS.md (1),
`docs/skills.md` (2), `commands/ux-audit.md`, `commands/ux-review.md`,
`skills/render-report/SKILL.md`, `evals/cases/render-report.json`, `evals/README.md`. Those
describe the dashboard rather than produce it, and `render-report` renders whatever the
roll-up contains — its own wording is downstream.

## Slice 6 — Docs & release

### T6.1 — The residue slices 1-5 left behind
The sweep for stale vocabulary found **more than the earlier slice records claimed**, which is
the honest headline of this slice. 23 substitutions, and three of them mattered:

- [x] **Every component `description` still said "severity-scored"** - `agents/cuj-auditor.md`,
      `agents/usability-auditor.md`, `commands/cuj-audit.md`, `commands/usability-audit.md`.
      Slices 1-5 rewrote bodies and never touched a single description. These are the
      user-facing one-liners and the agent-routing text, so they were the most visible stale
      surface in the repo.
- [x] **`cuj-auditor`'s two Rules guards were still `sev`.** Slice 3's record says "guards
      reworded to P3/P0" - it had done `usability-auditor`'s only. `P3` is now what the bottom
      of the scale is for, and "not every finding can be a `P0`".
- [x] **SPEC's canonical frontmatter example still showed `schema: 2` and `sev4..sev1`.** That
      block is the most-copied artifact in the spec; anyone implementing a new auditor from it
      would have emitted schema 2.
- [x] Plus: the contract's count-reconciliation clause, `SPEC.md` 1/2.1/6/7 prose, the
      `task-completion` lens ("separates `P0` from `P1`"), the testing-strategy fixtures,
      `usability-auditor`'s `S3 - major` example, `commands/usability-audit.md`, the renderer's
      module docstring, "severity-badged" wherever it described the HTML, and three
      `test_components.py` failure messages.

### T6.2 — SPEC's rubric had no priority ladder
- [x] `### Severity rubric (0-4 ...)` is retitled **"Rating rubric - priority is scored,
      severity is its stated input"** and now shows the `P0`-`P3` ladder *first*, with the
      severity table below it marked as never aggregated. Slice 1 added the derivation
      rationale here and correctly deferred the operative form to `report-contract.md` 4, but
      it left the scored ladder itself undocumented in the spec.
- [x] The index example gains the `P0..P3` header plus a note that a legacy `Sev4..Sev1` table
      is kept and appended below, never translated.
- [x] **I mis-stated this mid-slice** and corrected it in place: I said SPEC had no rubric
      section and the plan's "4" reference was wrong. It is wrong about the *title* - 4 is
      "Code / authoring style" - but the rubric is a subsection of it, so the plan was right.

### T6.3 — A grammar bug held in place by its own test
- [x] `cuj-auditor.md` read *"severity 0 is **never as a finding**"*. The probe demanded that
      exact broken string, so fixing the prose would have failed CI. Prose fixed; the probe now
      matches the substantive rule (`"never a finding"` or `"never emitted as findings at any
      priority"`) instead of a heading fragment, and `flat` was added to that check's scope.

### T6.4 — README, docs and the screenshot
- [x] README: the rubric paragraph now states the P ladder and severity-as-input; the roll-up
      paragraph states the distribution **and that there is deliberately no go/no-go verdict**;
      badges, matrices and both worked examples updated. The worked finding is now a real
      schema-3 finding with all six fields, not a relabelled heading.
- [x] `docs/agents.md`, `docs/skills.md` updated.
- [x] **`test_docs.py` now requires `"priority"` in the README** - the required-terms list
      never mentioned the scored scale at all.
- [ ] **`docs/images/audit-review.png` cannot be regenerated here.** It needs a live
      `/ux-audit` run against a host app. Rather than caption a stale image with new
      vocabulary - which would describe pixels that do not exist - the README now carries a
      blockquote saying the capture is from 0.6.1, what it shows, and that the prose is
      authoritative until it is retaken. **Open item for a dogfood run.**

### T6.5 — Release
- [x] `plugin.json` 0.6.1 -> **0.7.0** (minor: the contract changed shape).
      `marketplace.json` carries no `version` field, so there was nothing to mirror - only
      `dependencies` is mirrored there, and it is unchanged.
- [x] CHANGELOG 0.7.0 entry: Changed / Added / Fixed / Known, naming the old vocabulary where
      it explains what was replaced. Earlier entries are untouched - they record what past
      versions did.
- [x] AGENTS.md: the recipe's "0-4 severity format" becomes the priority format, its quoted
      example description is resynced, and the "Running the checks" block gains
      **`test_cuj_contract.py`** (missing since it was written - not something this work broke)
      and `test_charset.py`.
- [x] Remaining eval cases: `usability-audit.json`, `audit-cuj.json`. The `[sev0]` expectation
      had no schema-3 equivalent, since a non-problem has no rung on the P ladder at all - it
      is now "never emitted as a finding at any priority". The clamp expectation now describes
      a floor on priority with severity rated independently.

### ⛳ Checkpoint 6 — nothing stale is left unexplained
- [x] A classifying sweep over every tracked text file: each remaining `sev`/`go-no-go` hit is
      accounted for by a stated reason - schema-2 regression fixtures, the permanent validator
      path, the positional `.sev` colour ramp, contract notes explicitly marked "(Schema 2:)",
      the kept trigger phrase, sentences stating the verdict's *absence*, and CHANGELOG history.
      **Zero unexplained hits outside `tasks/`.**
- [x] `tasks/*.md` left as-is: tracked planning records for *earlier* features (auth-handoff,
      html-report, the original build). Rewriting them would falsify history, the same
      principle that protects the CHANGELOG.
- [x] Full suite green, all 8 files.
- [ ] **Human review.**
- [ ] **Not committed.** Six slices now sit uncommitted in one worktree.
