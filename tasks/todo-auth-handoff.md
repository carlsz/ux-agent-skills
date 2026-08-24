# TODO — Authenticated audits (the handoff rung)

Task list for [`plan-auth-handoff.md`](./plan-auth-handoff.md). Grouped by vertical slice; each
delivers one complete authenticated path. `[ ]` = todo, `[~]` = in progress, `[x]` = done.

Every task carries **Files**, **Acceptance**, **Verify**, **Deps**. Checkpoints (⛳) are
human-review gates between slices — stop and get sign-off before crossing.

---

## Slice 1 — The safety floor ⭐ *(first: the only executable change)*

### T1.1 — `writes_under()`, pathspec-scoped
- [x] Add a helper that observes writes under a prefix **even when the prefix is gitignored**.
- **Files:** `scripts/audit_safety.py`.
- **Acceptance:** runs `git status --porcelain -uall --ignored=matching -- <prefix>` so it can
  only ever see the prefix; reuses the existing porcelain-v1 line parsing (including the
  `R old -> new` case) rather than duplicating it; `_dirty_paths()` is **unmodified**;
  `changes_confined_to()` is **unmodified**.
- **Verify:** `python3 tests/test_safety.py` still green (no behaviour change yet).
- **Deps:** none (foundational).

### T1.2 — Regression cases for the ignored prefix
- [x] Prove the invariant survives a gitignored `.ux/audits/`, and that the naive fix's failure
      mode is actually excluded.
- **Files:** `tests/test_safety.py`.
- **Acceptance:** case A — temp repo with `.ux/audits/` in `.gitignore`, write a report, assert
  `writes_under()` is **non-empty** *and* `changes_confined_to()` is `[]`. Case B — an ignored
  `node_modules/` **outside** the prefix produces **no** violation and does not appear in
  `writes_under()`. Reuses `_init_repo` / `_write_report`.
- **Verify:** `python3 tests/test_safety.py` — both new cases pass.
- **Deps:** T1.1.

### T1.3 — Reword §5.2's invariant so an empty set cannot satisfy it
- [x] Item 4 currently reads *"`git status` shows changes only under `.ux/audits/`"*, which is
      trivially true when the prefix is ignored.
- **Files:** `SPEC.md` (§5.2 item 4).
- **Acceptance:** the invariant requires **both** that writes were observed under the prefix and
  that nothing changed outside it; names `writes_under()` as the mechanism.
- **Verify:** `python3 tests/test_docs.py`.
- **Deps:** T1.1.

### ⛳ Checkpoint 1 — the floor holds
- [x] `python3 tests/test_safety.py` green, both new cases included.
- [x] `changes_confined_to()` behaviourally unchanged on a repo with a populated `.gitignore`.
- [ ] **Human review** — the only code change in the whole feature, and the only place a
      plausible-looking implementation (`--ignored` on `_dirty_paths()`) breaks every audit.

---

## Slice 2 — The shared reference

### T2.1 — `auth-handoff.md`
- [x] New shared reference: the contract three skills inherit.
- **Files:** `skills/usability-audit/references/auth-handoff.md` (new).
- **Acceptance:** states the **five beats** (observe the wall verbatim → ask once naming URL /
  blocker / scope / hygiene → user signs in → re-observe and confirm → resume or skip with a
  named cause); the **attended-surface precondition** and that headless is *cannot attempt*, not
  *declined*; the **two-clause capability test** plus its rejection table; the **recommended host
  configuration** (seeded account + dedicated audit profile); the **Never list** (no session
  material, no credential read-back, no leaving scope, no recorded identity, no logout); the
  **artifact posture** with the `git ls-files .ux/audits/` check and the literal `.gitignore`
  recommendation text; and the grant-vs-session asymmetry.
- **Verify:** `python3 tests/test_docs.py` once T2.4 lands.
- **Deps:** Checkpoint 1.

### T2.2 — Report contract: the `Access:` line
- [x] The Appendix currently cites *"auth-gated screens"* as a canonical coverage gap; a screen
      reached via handoff is no longer one.
- **Files:** `skills/usability-audit/references/report-contract.md`.
- **Acceptance:** documents `Access: auth-gated; satisfied at L<n> (<rung>). Account not
  recorded.`; states that only *unreached* gated screens remain coverage gaps; **no schema
  change** — `validate_report.py` and `schema: 2` untouched.
- **Verify:** `python3 tests/test_report_contract.py`; `python3 tests/test_docs.py`.
- **Deps:** T2.1.

### T2.3 — §6 boundary entries
- [x] Fold §11.5's Ask-first and Never entries into §6, the suite-wide boundary index.
- **Files:** `SPEC.md` (§6).
- **Acceptance:** *"Never enter credentials, bypass authentication"* is preserved **verbatim**;
  Ask-first gains the handoff and the capture-while-tracked case; Never gains the five session
  rules; §6's existing "Reaching auth-gated screens" line points at the rung instead of
  dead-ending.
- **Verify:** `python3 tests/test_docs.py`.
- **Deps:** T2.1.

### T2.4 — Test wiring (**the silent trap**)
- [x] The new reference is unverified until hand-wired — nothing globs it.
- **Files:** `tests/test_components.py`, `tests/test_docs.py`.
- **Acceptance:** `check_auth_handoff_reference()` asserts the file exists and covers the five
  beats, both clauses, and every Never; it is added to the **`CHECKS` tuple**; the path is added
  to **`DOC_FILES`**. `test_evals.py` is **not** touched (no new skill ⇒ no eval case).
- **Verify:** `python3 tests/test_components.py` (check count rises 15 → 16);
  `python3 tests/test_docs.py`.
- **Deps:** T2.1, T2.2, T2.3.

### ⛳ Checkpoint 2 — the contract
- [x] Components + docs + report-contract green; the new check is in `CHECKS`.
- [ ] **Human review of `auth-handoff.md`** — three skills inherit it, and prose is where this
      feature actually lives.

---

## Slice 3 — The CUJ path, end to end

### T3.1 — L3 gets a success path
- [x] Rewrite ladder rung L3 to cite the reference instead of dead-ending, and land the
      pre-flight in step 3 (mode / reach the app).
- **Files:** `skills/audit-cuj/SKILL.md`.
- **Acceptance:** L3 cites `auth-handoff.md` rather than restating it; the **hard stop below
  L3** (no fixtures, no seed scripts, no `evaluate_script` injection) is unchanged; the
  **no-alibi rule** and self-referential-precondition handling are unchanged; a decline still
  produces a skip with a named cause and a `Repair:` line; the rung records "attempted" the way
  every other rung does.
- **Verify:** `python3 tests/test_components.py` (`check_audit_cuj_skill`);
  `python3 tests/test_docs.py`.
- **Deps:** Checkpoint 2.

### T3.2 — `cuj-auditor` persona Nevers
- [x] The persona gains the rules that only become tempting once a live session exists.
- **Files:** `agents/cuj-auditor.md`.
- **Acceptance:** all five Nevers present; the existing render-vs-source, walk-through-capture,
  and "a skip is not a finding" rules are untouched.
- **Verify:** `python3 tests/test_components.py` (`check_cuj_auditor_persona`).
- **Deps:** T3.1.

---

## Slice 4 — The usability path, end to end

### T4.1 — Live-mode pre-flight
- [x] Replace *"Do not enter credentials or bypass auth to reach gated screens; record those as
      skipped with the reason"* with the pre-flight plus a citation.
- **Files:** `skills/usability-audit/SKILL.md`.
- **Acceptance:** live-mode step runs the pre-flight and cites `auth-handoff.md`; the
  **render-vs-source honesty rule** and the **setup-side-effects** paragraph are untouched; the
  coverage-gap rule still applies to gated screens that were *not* reached.
- **Verify:** `python3 tests/test_components.py` (`check_skill`); `python3 tests/test_docs.py`.
- **Deps:** Checkpoint 2.

### T4.2 — `usability-auditor` persona Nevers
- [x] Same five Nevers; stop treating auth-gated as an unconditional gap.
- **Files:** `agents/usability-auditor.md`.
- **Acceptance:** the "Never fabricate" rule's *"(auth-gated, no running app)"* aside is
  reworded so a reached-via-handoff screen is not miscounted as skipped.
- **Verify:** `python3 tests/test_components.py` (`check_persona`).
- **Deps:** T4.1.

### ⛳ Checkpoint 3 — both native auditors
- [x] Full suite green (7 files).
- [x] **Manual:** read the L3 decline path end to end and confirm a skip still reads honestly —
      named cause, `Repair:` line, no severity inflation.

---

## Slice 5 — The roll-up pre-flight

### T5.1 — One handoff for the whole fan-out
- [x] Add a pre-flight before the step-2 fan-out: probe the target once, hand off if walled, and
      let every auditor inherit the session.
- **Files:** `skills/ux-audit/SKILL.md`, `commands/ux-audit.md`.
- **Acceptance:** the pre-flight precedes fan-out so the user is interrupted **once**, before
  work starts; external auditors (`web-quality-skills:accessibility`, `:performance`) run
  normally; the roll-up discloses that the run was authenticated so the go/no-go dashboard does
  not read as anonymous; existing skip disclosures (not-installed / opt-in / no-CUJs) unchanged.
- **Verify:** `python3 tests/test_components.py` (`check_rollup_skill`, `check_rollup_command`);
  `python3 tests/test_docs.py`.
- **Deps:** Slices 3 and 4.

---

## Slice 6 — Docs & release

### T6.1 — README + AGENTS
- [x] Document the flow and the recommended host configuration.
- **Files:** `README.md`, `AGENTS.md`.
- **Acceptance:** README gains an authenticated-audit section (the flow, the seeded-account
  recommendation, the `.gitignore` posture, and the accepted external-auditor risk); AGENTS
  notes that `auth-handoff.md` is a **shared reference cited by three skills** and that a new
  reference must be hand-wired into `CHECKS`.
- **Verify:** `python3 tests/test_docs.py` (README literals + links).
- **Deps:** Slice 5.

### T6.2 — CHANGELOG, version, §11 status
- [x] Release wiring.
- **Files:** `CHANGELOG.md`, `.claude-plugin/plugin.json`, `SPEC.md` (§11 header).
- **Acceptance:** CHANGELOG entry describes the rung and the artifact posture; `plugin.json`
  version bumped (mirror into `marketplace.json` only if `dependencies` changed — they do not);
  §11 Status flips from *Draft — awaiting approval*.
- **Verify:** full suite.
- **Deps:** T6.1.

### ⛳ Checkpoint 4 — complete
- [x] `for t in tests/test_*.py; do python3 "$t"; done` — all 7 green.
- [x] Every box in [SPEC §11.8](../SPEC.md) ticks.
- [ ] **Dogfood:** `claude --plugin-dir .` against an auth-gated app — decline once (skip reads
      honestly), then accept (Appendix records the rung, **not** the account).
- [ ] Ready for review.
