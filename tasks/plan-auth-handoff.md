# PLAN — Authenticated audits (the handoff rung)

Implementation plan for [`SPEC.md`](../SPEC.md) **§11**. Read-only planning artifact — no code
changes are made by this document.

- **Spec:** [SPEC.md §11](../SPEC.md)
- **Date:** 2026-08-24
- **Plugin:** `ux-agent-skills` v0.5.1 → next
- **Approach:** vertical slices — each delivers one complete authenticated path. The one
  executable change goes **first**, because it is the only place a plausible-looking
  implementation actively breaks the suite.

---

## 1. What we're building

Every screen behind a login wall is currently a coverage gap. The precondition ladder in
[`audit-cuj/SKILL.md`](../skills/audit-cuj/SKILL.md) ends at *"L3 — Ask the user"* without
defining what *supplied* means, and [§6](../SPEC.md) forbids the obvious reading (*"Never enter
credentials, bypass authentication"*). The result: the suite is rigorous about the small part of
a product in front of the wall and silent about the large part behind it.

§11 gives L3 a real handshake — **the human signs in, the auditor waits and resumes**. The agent
never holds a secret, so §6's Never survives *unchanged*.

The non-obvious half, and the reason this is more than a prompt change: **the credential was
never the biggest leak — the evidence is.** Behind auth, every screenshot carries the account's
name and email in the app chrome and every observed-value line quotes real records. §10 embeds
those inline; §8 encourages committing them. So the same change that enables authenticated
audits must also change what an authenticated run is willing to leave in the host repo.

**Not building:** unattended/CI operation, a credential store, a session-material format, login
automation, or any new component. No new `SKILL.md`, no new persona, no schema change.

---

## 2. The user flow this enables

The whole point of the six slices. Written as the user experiences it.

### Flow A — a single auth-gated journey (`/cuj-audit CUJ-003`)

**1. Pre-flight.** After validating journeys and fixing the mode, the auditor navigates to
`entry_point` and finds a wall. It records what it saw **verbatim** — *auth-gated* must be an
observation, never an assumption. It also runs `git ls-files .ux/audits/` to learn whether the
directory is already tracked.

**2. One interruption, everything named:**

```
CUJ-003 "Export a report" needs a signed-in session.

  Wall observed:  https://app.example.com/reports → redirected to /login,
                  form reads "Sign in to Acme"
  Unblocks:       CUJ-003 (criticality: critical), plus 4 steps of CUJ-005

Please sign in yourself in the browser I'm driving — I won't type, read, or
store anything. Use a throwaway or seeded account, not production: I'm about
to screenshot every step, and those images land in .ux/audits/assets/.

Before I capture anything, two housekeeping notes:

  · .ux/audits/ is currently NOT tracked by git. Add this line to .gitignore
    and an authenticated run stays local:

        .ux/audits/

  · I can't write .gitignore myself — that's outside my allowlist. It's yours
    to apply.

Tell me when you're signed in, or say skip and I'll record CUJ-003 as
"precondition unmet" with the reason.
```

**3. The user signs in** — in the browser the auditor is already driving. The auditor is idle:
it types nothing, reads nothing, stores nothing.

**4. Confirm and resume.** On "done", the auditor **re-observes** to verify the session actually
holds (a failed login must not read as success), records *the rung, not the identity*, and
replays the journey normally. Screenshots, walkthrough, findings — all unchanged.

**5. The report.** No new frontmatter key. The Appendix gains one line:

```markdown
## Appendix
- Access: auth-gated; satisfied at L3 (user handoff). Account not recorded.
```

**6. Hand-back.** The closing summary states what the run left behind:

```
Report: .ux/audits/cuj-20260824-142317.md (3 findings, 1 sev3)

The browser is still signed in as the account you used — I don't log out,
since that's a state reset no journey named. Sign out when you're done.
Reminder: .ux/audits/ isn't gitignored yet; those screenshots are of a live
account.
```

### Flow B — the roll-up (`/ux-audit https://app.example.com`)

The handoff is a **pre-flight for the whole fan-out**, before any auditor runs: one probe, one
interruption, and every auditor — native and external alike — inherits the session. Without it a
four-auditor fan-out could stop and ask partway through, after minutes of work.

### Flow C — declined, or no seat for the human

Declined → the existing skip path, with a named cause and a `Repair:` line. Headless or
unattended → the rung **cannot be attempted**; the report says so and never reports it as a
decline the user made. This is today's behaviour, now correctly labelled.

---

## 3. Prior art that shapes the plan

| Existing thing | What it gives us |
|---|---|
| The **precondition ladder** (`audit-cuj` step 4) | L0/L1/L2/L2.5/L3 with "record every rung attempted". The handoff is L3 *finally succeeding* — no new structure. |
| **`report-contract.md`** as a shared reference | The cite-don't-restate precedent: one owner, consumers link across. `auth-handoff.md` follows it exactly. |
| The **`## Appendix` → Coverage** section | Already the home for "auth-gated screens". Needs nuance (a screen reached via handoff is no longer a gap) plus the `Access:` line — no schema change. |
| **`audit_safety.py` `snapshot()` / `changes_confined_to()`** | The invariant machinery. Slice 1 extends it rather than replacing it. |
| The **`author:` rejection** (§9.7, `cuj-contract.md` §8) | *"No PII in the artifact beats a rule about handling PII in the artifact."* Governs the whole feature — it is why there is no `account:` key and why a seeded account beats redaction. |
| **`test_components.py` `CHECKS` tuple** | The silent trap. A new reference is unverified until hand-wired here. |

---

## 4. Design decisions

- **Pre-flight, not lazy.** The rung fires as a pre-flight step at every entry point. Single
  auditors navigate to the target first anyway, so it costs them nothing, and the reference
  specifies **one** trigger point instead of two.
- **One shared reference, cited not restated.** Restating the handshake across three skills
  guarantees drift.
- **`EXTRA_BY_PROFILE["audit"]` stays `()`.** The auditor *recommends* the `.gitignore` line;
  the user applies it. Widening the baseline profile so an auditor can edit a root-level file
  costs more than the convenience is worth.
- **The capability test is vendor-neutral.** Two clauses — (a) the secret never enters agent
  context, (b) the session lands in a context isolated from the user's daily profile. Clause (b)
  does the real work and is why agent-mediated password-manager autofill is rejected: not for
  being a product, but for failing (b).
- **Only one test trap fires.** No new `SKILL.md` ⇒ `test_evals.py` stays green and **no eval
  case is needed**. `test_components.py`'s silent trap still applies.

---

## 5. Dependency graph

```
SPEC §11
   │
   ├── Slice 1  audit_safety.py + test_safety.py + §5.2 wording   ← independent, highest risk
   │                     │
   │                     └── unblocks the wholesale-ignore posture
   │
   ├── Slice 2  auth-handoff.md + §6 + report-contract appendix
   │            + check_auth_handoff_reference + DOC_FILES
   │                     │
   │            ┌────────┼────────────────┐
   │            │        │                │
   │       Slice 3   Slice 4          Slice 5
   │       (cuj)     (usability)      (roll-up pre-flight)
   │            └────────┴────────────────┘
   │                     │
   └───────────────── Slice 6  README / AGENTS / CHANGELOG / version
```

Slices 3–5 are independent of one another once Slice 2 lands.

---

## 6. Vertical slices & checkpoints

| # | Slice | Delivers | Size |
|---|-------|----------|------|
| 1 | **The safety floor** | The invariant still sees writes under an ignored prefix | S |
| 2 | **The shared reference** | `auth-handoff.md` + §6 + contract appendix, test-wired | M |
| 3 | **The CUJ path** | L3 succeeds end to end; persona Nevers | S |
| 4 | **The usability path** | Live-mode pre-flight; persona Nevers | S |
| 5 | **The roll-up pre-flight** | One handoff for the whole fan-out | S |
| 6 | **Docs & release** | README / AGENTS / CHANGELOG / version | M |

⛳ **Checkpoints** after 1, 2, 4, and 6 — see [`todo-auth-handoff.md`](./todo-auth-handoff.md).

### Slice 1 in detail — the one place a naive fix breaks things

Today [`_dirty_paths()`](../scripts/audit_safety.py) runs `git status --porcelain -uall`
**without `--ignored`**. Once `.ux/audits/` is ignored, the auditor's own writes vanish from the
snapshot, and §5.2's invariant passes identically whether a full report was written or nothing
at all — it degrades from *verified confined* to *saw nothing*.

**The trap:** adding `--ignored=matching` to `_dirty_paths()` is **wrong**. It would list every
ignored file in the repo (`node_modules/`, `.venv/`, build output), and each one outside the
prefix would register as a violation. Every audit would fail.

**The fix:** leave `_dirty_paths()` alone; add a **pathspec-scoped** helper that can only ever
see the prefix. Ignored-ness becomes visible where it is needed and stays invisible where it
would do damage; `changes_confined_to()` remains the violation scan, behaviourally unchanged.

**Delivered (corrects the sketch above).** Probing git showed the single-command version does
not work. `git status --porcelain -uall --ignored=matching -- <prefix>` is pathspec-safe, but
when the ignore rule names the *directory* the directory itself is the match, so the whole
prefix collapses to one `!! .ux/audits/` entry — per-file granularity is lost — and it still
sees nothing when the prefix is **not** ignored, which is the state of every repo that has not
applied the recommendation. `writes_under()` therefore unions two pathspec-scoped commands:

```python
git status --porcelain -uall -- <prefix>                  # tracked-modified + untracked
git ls-files -o -i --exclude-standard -- <prefix>         # ignored, individually
```

Verified to return the identical per-file list across all four prefix states (not ignored,
ignored, tracked-and-ignored, nothing written), and a **mutation check** confirms the new
`test_safety.py` cases fail against the naive `--ignored` implementation.

---

## 7. Verification strategy

```bash
for t in tests/test_*.py; do echo "--- $t"; python3 "$t"; done
```

**Testable:** the reference exists and states the five beats, both clauses, and every Never;
all three skills link it; `writes_under()` sees writes under an ignored prefix;
`changes_confined_to()` is unperturbed by unrelated ignored files; `EXTRA_BY_PROFILE["audit"]`
is still `()`; the new path is in `DOC_FILES`; the new check is in `CHECKS`.

**Not testable, and said plainly rather than faked:** the handshake itself — agent behaviour
with a human in the loop. It is a documentation-and-persona guarantee.

**Dogfood.** `claude --plugin-dir .` against an auth-gated app (e.g.
[Sprout](https://github.com/carlsz/sprout)): run `/cuj-audit` on a journey whose precondition
needs a session; confirm the prompt names the wall, the scope, and the hygiene ask; **decline
once** and confirm the skip reads honestly; then accept and confirm the Appendix records the
rung and **not** the account.

---

## 8. Risks & boundaries

| Risk | Impact | Mitigation |
|------|--------|------------|
| Naive `--ignored` flip makes every ignored file a violation | **High** | Pathspec-scoped helper; Slice 1 first, with an explicit regression case |
| External roll-up auditors write outside `.ux/audits/` while authenticated | Med | Accepted (decision §9.1). `changes_confined_to()` still detects it — after the write, not before. README note |
| User applies no `.gitignore` and commits a real account's screenshots | Med | `git ls-files` check + recommendation at **auth time**, not report time; the seeded-account ask is in the prompt itself |
| The handshake is untestable | Med | Stated in §11.7 rather than papered over with a test that proves nothing |
| Prose drift between the reference and three citing skills | Low | Cite-don't-restate; `check_auth_handoff_reference` asserts the terms |

**Boundaries preserved.** Findings-only is untouched. §6's *"Never enter credentials, bypass
authentication"* is preserved **verbatim** — the rung is the human doing it, not the auditor.
Writes stay confined to `.ux/audits/`; the auditor never writes the host's `.gitignore`.

---

## 9. Decisions (resolved with the human)

1. **Mechanism: human handoff only.** Not storage-state, not a dev-login affordance, not
   password-manager autofill. Handoff is the only mechanism with *zero* dependencies, which
   makes it the correct floor rather than a fallback.
2. **Attended only.** Unattended/CI is a non-goal; headless degrades to today's honest skip.
3. **Artifact posture: recommend ignoring `.ux/audits/` wholesale** — reports, assets, and the
   derived `.html` alike. Narrower rules do not hold: `render_report_html.py` base64-embeds the
   images into the HTML, and the Markdown quotes real records independently of both.
4. **Session teardown: leave it, and say so.** A logout is a state reset, which L2.5 permits
   only when a journey names it. Credential *grants*, by contrast, are released at end of run —
   a session is app state the user may care about, a grant is not.
5. **Placement: a shared reference both (all three) skills link.**
6. **Roll-up: external auditors run normally** when authenticated; containment is the wholesale
   ignore. *(Risk accepted and recorded above.)*
7. **Timing: pre-flight, once, before any auditor runs.**
8. **`tasks/` filenames follow the repo's suffix convention** (`-auth-handoff`), not the generic
   `plan.md`/`todo.md` the `/agent-skills:plan` template names — those hold the original v0.2.0
   usability-auditor plan and are historical.
