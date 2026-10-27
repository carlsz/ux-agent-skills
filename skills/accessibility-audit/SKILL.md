---
name: accessibility-audit
description: Audit a host app against WCAG 2.2 and write a priority-scored accessibility report to .ux/audits, grading each criterion by its impact on the user it affects. Use for "accessibility audit", "a11y audit", "WCAG review", "screen reader audit", or "is this accessible".
---

# Accessibility Audit

Drive the [`accessibility-auditor`](../../agents/accessibility-auditor.md) persona through
a WCAG 2.2 inspection and emit a report that conforms to the
[shared report contract](../usability-audit/references/report-contract.md), with
`auditor: accessibility`.

**Framework:** [WCAG 2.2, as an audit lens](./references/wcag-2.2.md) — organized by what
you can observe and what evidence proves it. Remediation patterns live in the external
[`web-quality-skills:accessibility`](https://github.com/addyosmani/web-quality-skills)
skill; read it for the fix wording and **never for its posture** — that skill is written
for a maker who will apply the change, and this one reports instead (see Boundaries).

**Evaluation modes:** `static` (read source), `live` (drive the running app in a browser),
and `hybrid` (both). Unlike the other auditors, the mode here changes **what can be
claimed at all**: most WCAG criteria are only observable at runtime, so a static run finds
markup that looks wrong and cannot establish conformance. Mode is auto-selected by default
(step 1); `--mode` forces one.

---

## Inputs

- `target` — a URL (live mode) or a repo path/glob (static mode). If omitted, infer from
  the running dev server or the repo's UI source.
- `--scope` — narrow the audit to a flow/area (e.g. "checkout"). Optional.
- `--mode static | live | hybrid` — force an evidence-gathering mode. Optional; default is
  auto (see step 1).

## Workflow

1. **Scope the audit and select the mode.** Resolve `target` and `--scope`, and identify
   the host repo root (where `.ux/` will live). Then choose the mode:
   - If `--mode` is given, use it.
   - Otherwise **auto-select**: **prefer live** when a target URL is given or a dev server
     is already running/detectable; **fall back to static** when no running app is
     reachable. Use **hybrid** when both a URL and the source are available — observe the
     render for the runtime criteria and use the source to locate the `file:line` a fix
     belongs to.
   - Record the mode you **actually** used (not the one requested) in the report
     frontmatter and appendix — a requested `live` that fell back because no server was
     reachable is reported as `static`, with the reason.
   List the surfaces you intend to cover.

2. **Read the lens and the contract.** Load [the WCAG audit lens](./references/wcag-2.2.md)
   and the [report contract](../usability-audit/references/report-contract.md), including
   §4's *A conformance level is not a priority*. Cite criteria from the reference; do not
   recite them from memory. Decide from the lens which criteria are **in scope for this
   surface** — a surface with no media does not get 1.2.x, and saying so is not a gap.

3. **Gather evidence** using the selected mode:

   ### Static mode (source)
   Read the in-scope components, markup, routes, copy and design tokens. You can settle
   the markup-bound criteria honestly: `1.1.1` alt text, `1.3.1` structure, `3.1.1` page
   language, `3.3.2` labels, `2.1.1` handlers on non-interactive elements, `4.1.2` roles on
   custom widgets. Capture `file:line` for each. Everything that depends on the render —
   contrast, focus order, focus visibility, target size, reflow, live-region announcement
   — is **`potential — unverified`** here, with the reason; see step 5.

   ### Live mode (render)
   Inspect the running app through a browser (browser MCP). **Ask the user first** before
   starting or restarting a dev server and before navigating the browser to any URL — do
   not launch a server or navigate unprompted.
   - **Read the accessibility tree** for each in-scope screen: names, roles, states. This
     is the primary instrument of this audit, not a supplement — it is what separates "it
     works with a mouse" from "it exists for assistive technology".
   - **Tab through the whole flow** and record the focus order, whether every interactive
     element is reachable, whether focus is ever trapped, and whether the indicator is
     visible at each stop.
   - **Measure** what the criteria state as numbers: contrast ratios against the
     **computed** background, target sizes in CSS px, reflow at 320px-equivalent width. A
     token pair read from CSS is an estimate until the render confirms what composites.
   - **Trigger the error and status states** — submit an invalid form, start an async
     action — and observe whether the message identifies the error in text and whether the
     update reaches assistive technology.
   - **Screenshot** each key state (initial, focus-visible, error, success, empty) and save
     each as `accessibility-<scope-slug>-<state>.png` inside **this run's own** asset
     directory, `.ux/audits/assets/<report-stem>/` — the report filename you will write in
     step 7 without its `.md`, so the images and the report that cites them share one
     lifecycle and no later run can overwrite them (report contract §1). Embed them inline
     (`![alt](./assets/<report-stem>/…)`) — in findings for evidence, and assembled into
     the `## Walkthrough` section (step 7).
   - **Automated tooling is optional and bounded.** If you run axe-core or Lighthouse,
     carry its output as evidence and add the tool to `frameworks`. It settles a minority
     of the criteria and none of the judgement-bound ones — see step 6.
   - **Auth pre-flight.** Never enter credentials or bypass auth yourself. When the
     in-scope flow runs into a login wall, run the **auth handoff** —
     [`auth-handoff.md`](../usability-audit/references/auth-handoff.md) — as a pre-flight,
     *before* walking the flow: observe the wall and record it verbatim, ask once (naming
     the wall, the scope it unblocks, and the throwaway-account ask), let the **user** sign
     in, then re-observe to confirm the session holds and continue. Record the outcome as
     the report's `Access:` line.
     - A gated screen **reached this way is audited, not a coverage gap** — do not list it
       under *Coverage / not inspected*.
     - Declined, or **no attended browser surface** (headless — nobody could be asked, so
       it is not a decline), → the gated screens stay skipped with that exact reason.
     - Once a session is live, the §7 Never list applies: no session material, no
       credential read-back, no wandering outside scope, no recorded account identity, no
       logout.
     - Auditing the sign-in screen itself (3.3.8, labels, focus) is in scope and needs no
       session: observe it, never authenticate against it.

4. **Grade by impact on the user the defect affects, citing the level.** For each failure,
   write the five fields: Issue
   Description (what fails, **for whom**, in which assistive context), Framework Violation
   (criterion number, name and level, cited exactly), Priority, Evidence, Recommended Fix.
   The level goes in the citation and **never decides the grade** — apply the contract's
   tie-breakers reading "the user" as the user this defect affects. An unlabeled control on
   a required path is `P0` because it is *impossible* for that user, not `P2` because a
   sighted mouse user is unaffected; a secondary caption slightly under the contrast
   minimum is `P2`, and that is not softening it. **Every failed criterion is a finding**,
   including the `P3`s — a low grade is never permission to leave it out.

5. **Apply the render-vs-source honesty rule.** It binds harder here than in any other
   auditor, because most of WCAG is a runtime property:
   - In **live** mode, a criterion you observed or measured is stated as **verified**,
     backed by the measurement, the accessibility-tree excerpt or the screenshot.
   - In **static** mode, every runtime-bound finding is labeled **`potential —
     unverified`** in the Evidence field with the reason, and the appendix states that a
     static run **cannot establish conformance** — it can only find markup that looks
     wrong. Never assert an unobserved runtime behavior as fact.

6. **State what the tooling did and did not cover.** If you ran axe-core or Lighthouse,
   name it in `frameworks` and say in the appendix which criteria it covered. **Never
   report "0 automated violations" as "accessible"**: automated tooling detects roughly a
   third of WCAG failures and almost none of the judgement-bound ones — whether alt text is
   meaningful, focus order logical, an error message identifying, a live region timely. A
   clean tool run over an unexamined surface is the most confident-sounding false pass this
   suite can produce, so the appendix carries the gap explicitly.

7. **Write the report.** Create `.ux/`, `.ux/audits/`, and this run's
   `.ux/audits/assets/<report-stem>/` in the host repo if absent. Write
   `.ux/audits/accessibility-<YYYYMMDD>-<HHMMSS>.md` (UTC clock) with the frontmatter
   schema (`auditor: accessibility`, `frameworks: [wcag-2.2]` plus any tool you actually
   ran), executive summary, prioritized fixes, findings, and an appendix. Score the
   `health` block with **one item per criterion you actually checked**, `rubric: wcag-2.2`,
   each `of: 4` — see the exit criteria for what that must and must not contain. In
   **live/hybrid** mode, add a `## Walkthrough` section (report contract §5) after
   `## Findings` and before `## Appendix`: one `### <state>` per captured key state, each
   embedding its screenshot inline. Omit the section in static mode (nothing was captured).

8. **Append to the index.** Add one row for this run to `.ux/audits/index.md` — create the
   file with the contract's header if it doesn't exist. The index is **append-only**: add
   your row, never rewrite or reorder prior rows (they may belong to earlier runs or other
   auditors). The row records date, auditor, scope, the four priority counts and the health
   percentage, linking to the report file.

9. **Self-check before finishing.** Ensure `summary` counts reconcile with the findings in
   the body and no tag outside `P0`-`P3` appears. Validate the report and index with
   [`scripts/validate_report.py`](../../scripts/validate_report.py) — `validate_report.py
   <report>` and `validate_report.py --index .ux/audits/index.md`. Then confirm the safety
   invariant with [`scripts/audit_safety.py`](../../scripts/audit_safety.py)
   `<host-repo>`. It checks **both halves** of the invariant (SPEC §5.2) and exits 0 only if
   both hold: nothing changed outside `.ux/audits/`, **and** the writes you just made inside
   it were observed — it prints them. Exit 1 with *"no writes were observed"* means the run
   produced nothing; that is a real failure for an auditor, not a formality, and it is the
   only signal you get once `.ux/audits/` is gitignored and `git status` has gone quiet.

10. **Render the HTML companion.** After the report validates, generate its self-contained
    HTML view beside the Markdown:

    ```
    python3 scripts/render_report_html.py .ux/audits/accessibility-<timestamp>.md
    python3 scripts/render_report_html.py --index .ux/audits/index.md
    ```

    The `.html` is a derived view — the Markdown stays the source of truth. Both files are
    written under `.ux/audits/`, so the safety invariant is unaffected. (The same view is
    available on demand via `/ux-review`.)

## Boundaries

- **Findings only.** Never edit, refactor, or "fix" host application code. This boundary is
  under more pressure here than anywhere else in the suite: an accessibility defect usually
  has an obvious small fix sitting right beside it, and the reference material you read is
  written in a ❌/✅ idiom whose whole purpose is to be applied. Read it for the wording of
  the recommendation; put that wording in the **Recommended Fix** field and nowhere else.
- **Never write outside `.ux/audits/`** in the host repo. That is the auditor's safety
  invariant; any other created/modified file is a failure.
- **Ask first** before starting a dev server, navigating a browser, installing anything,
  or reaching auth-gated screens — the handshake for the last one is the auth handoff
  ([`auth-handoff.md`](../usability-audit/references/auth-handoff.md)).
- **Once a session is live**, never read or store session material (cookies, `localStorage`,
  tokens), never read back a filled credential field, never leave the audited scope, never
  record the account identity, and never log the user out. An authenticated run is a
  **capture** risk before it is an access problem: recommend ignoring `.ux/audits/`
  wholesale, and describe user data structurally rather than quoting it.
- **Setup side-effects are not audit writes, but disclose them.** Getting the app running
  for live mode may require a user-authorized install/build, which can modify host files
  like a lockfile. Take the safety baseline **after** any authorized setup (or revert setup
  changes first) so it measures the audit's footprint, and note the side-effect in the
  appendix rather than letting it read as an audit write.
- **Never fabricate** criteria, measurements, priorities or evidence. A contrast ratio you
  did not compute is not a measurement, and a criterion you did not check is not a pass.

## Exit criteria (done when)

- A timestamped `accessibility-*` report exists under `.ux/audits/` and validates against
  the contract.
- One row was appended to `.ux/audits/index.md` (created if absent), with no prior rows
  rewritten.
- Every finding cites its criterion by number, name and level, and carries a `P0`-`P3`
  priority with its action, evidence, and a fix. **Every failed criterion is present as a
  finding**, at whatever priority it earned.
- No finding's priority was taken from its conformance level. Each Priority field names the
  **affected user** and the tie-breaker that decided it, per §4's *A conformance level is
  not a priority*.
- The `health` scorecard carries **one item per criterion actually checked and no others** —
  including the ones that passed, so a clean area is legible — **deriving each score from
  the findings rather than judging it a second time** (§4.1: an item scores the P-number of
  the worst finding citing it, `4` when none does, so the lowest item score equals the worst
  priority in `summary`), with a `note` on every marked-down or n/a item naming the finding
  behind it. A criterion that was **not evaluated** appears in the appendix's coverage list
  and **not** in the scorecard: enumerating criteria you did not check is a false coverage
  claim, and a long scorecard reads as thoroughness. `score`/`max` reconcile with the items;
  **`pct` is the priority index over `summary`, not `score / max`** (§4.1), so a lens that
  enumerates more criteria cannot score higher for the same defects.
- Runtime-bound findings are `verified` (live) or `potential — unverified` (static),
  matching the mode actually used, and a static run says in the appendix that it **cannot
  establish conformance**.
- If automated tooling ran, the appendix says what it covered, and **no "0 violations"
  result is reported as "accessible"**.
- Live-mode screenshots are saved under this run's own `.ux/audits/assets/<report-stem>/`,
  embedded inline in findings, and assembled into a `## Walkthrough` section (omitted in
  static mode). `validate_report.py` derives that directory from the report's filename, so
  an embed pointing at another run's captures fails the report.
- The appendix names every in-scope surface not inspected, every criterion not evaluated,
  and every assistive technology not exercised.
- `audit_safety.py` exits 0 on **both** halves: nothing changed outside `.ux/audits/`,
  **and** the writes this run made inside it were observed and listed. (`git status` alone
  is not the check — once `.ux/audits/` is gitignored it shows nothing, which a run that
  wrote nothing satisfies identically.)
