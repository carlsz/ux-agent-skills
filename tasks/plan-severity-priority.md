# PLAN — One scored scale: priority (P0–P3), with severity as its stated input

Implementation plan revising [`SPEC.md`](../SPEC.md) **§4** (the rubric) and **§9.4** (the CUJ
mapping), and bumping the report contract to **schema 3**. Read-only planning artifact — no code
changes are made by this document.

- **Spec:** [SPEC.md §4](../SPEC.md), [§9.4](../SPEC.md); contract
  [`report-contract.md`](../skills/usability-audit/references/report-contract.md)
- **Date:** 2026-11-11
- **Plugin:** `ux-agent-skills` v0.6.1 → **0.7.0** (minor: the contract changes shape)
- **Approach:** vertical slices. Slice 1 is prose-only and ships alone — it fixes the reported
  pain without touching the schema, so it does not wait on the rest.

---

## 1. What we're building

Today the suite has **one** rating scale and **two** incompatible meanings for it.

[Contract §4](../skills/usability-audit/references/report-contract.md) presents 0–4 as Nielsen's
severity ratings and links the NN/g article. [SPEC §9.4](../SPEC.md) defines the same 0–4 for
`audit-cuj` as a *task-impact* ladder — 4 is a blocked journey with no workaround, 3 is "workaround
required", 2 is "journey unaffected". Those are different instruments wearing the same numbers. An
S3 from the usability auditor and an S3 from the CUJ auditor are not the same claim, and nothing in
the contract says so.

That is the real source of the borderline-call problem. It is not the 0/1 boundary in isolation —
it is that neither auditor has a stated method for landing on a number. §4 gives five one-line
labels and no derivation; §9.4 gives a derivation for a scale it doesn't share with §4.

**We resolve it with one scored scale, not two.** The reader of a findings-only report asks one
question — *what do I fix first?* — so the report answers that question with one number, and shows
the reasoning that produced it underneath:

- **P0–P3 — priority.** The scored scale. Drives finding headings, summary counts, `index.md`
  columns, prioritized-fix ordering, and the roll-up. This is §9.4's existing ladder, relabelled
  and generalized to every auditor.
- **Severity — the stated input.** NN/g's frequency × impact × persistence, written out per
  finding as `S1`–`S4` with its justification. Not aggregated, not an index column, not a second
  badge. It exists so a reader can check the call and overrule it.

**Not building:** a second scored axis, per-dimension quality scores, a `/20` total, positive
findings, a systemic-patterns section, remediation commands, or any new component. No new
`SKILL.md`, no new persona.

---

## 2. Prior art that shapes the plan

**§9.4 is already a priority ladder.** Its rows map almost exactly onto the P-scale the market
uses. We are not inventing a vocabulary; we are naming one the repo already shipped, and extending
it to the auditors that lack it.

**Renaming the scale fixes the clamp bug.** §9.4 caps the score by `criticality` (`medium` max 3,
`low` max 2). While the field is called *severity*, that cap falsifies an observation: a genuine
catastrophe on a low-criticality journey is recorded as a 2, which sits badly against
[contract §6](../skills/usability-audit/references/report-contract.md)'s honesty rule. Once the
scored field is **priority**, the same cap is simply correct — a blocked low-criticality journey
really is P2. No second axis is needed to fix this.

**`criticality` is user-declared, not inferred.** It comes from the CUJ file the user authored via
`/ux-spec`, which is what makes adjusting by it honest. Findings with no journey behind them are
unadjusted and say so.

**Impeccable**, the reference this request came from, tags findings `P0–P3` but its skill file
calls that field *severity* and defines it purely by task impact — it renamed one axis rather than
splitting two. Worth taking: the P-label wording, the long-tail rule, the inflation guard. Worth
leaving: its 0–4 per-dimension quality scores, which are ascending-good and would collide.

---

## 3. The scale

### P0–P3 — scored, structural

| | Criterion | When |
|---|---|---|
| **P0** | Blocks the task — no workaround exists | Immediately |
| **P1** | A workaround is required but costly or non-obvious; the flow appears to succeed but doesn't (silent failure); or a WCAG AA failure | Before release |
| **P2** | An obvious workaround exists; task completion unaffected | Next improvement pass |
| **P3** | No effect on task completion — cosmetic | After higher priorities |
| — | Not a problem | **Omit entirely.** Not counted, not listed |

**Derivation, per finding, in this order:**

1. **Classify task impact** against the ladder above.
2. **Assess severity** by NN/g's three factors — frequency (how many users meet it), impact (how
   hard to overcome), persistence (once, or every time) — and record it as `S1`–`S4`.
3. **Adjust by declared `criticality`:** `critical`/`high` unchanged; `medium` demote one step;
   `low` demote two (floor P3). Unadjusted and disclosed when no journey backs the finding.

Severity informs step 1 and is reported, but does not mechanically determine P. A reader who
disagrees with the criticality input can see all three stages and re-rank.

### What a finding looks like

```markdown
### [P1] Payment button has no visible keyboard focus

- **Issue Description:** Tabbing reaches the button, but nothing indicates it is focused.
- **Framework Violation:** Nielsen #1 — Visibility of System Status; WCAG 2.4.7.
- **Priority:** P1 — WCAG AA failure, no workaround for keyboard users; journey
  criticality `high`, unadjusted.
- **Severity:** S3 (major) — affects every keyboard and screen-reader user (frequency),
  cannot be worked around (impact), recurs on every visit (persistence).
- **Evidence:** ./assets/usability-checkout-mid-flow.png
- **Recommended Fix:** Add a visible `:focus-visible` style; verify through the full flow.
```

One number in the heading. The reasoning sits underneath for anyone who wants to argue with it.

---

## 4. Design decisions

1. **Schema 3, with the 2 path kept.** [`validate_report.py:76`](../scripts/validate_report.py) is
   a flat `!= 2`; it becomes a dispatch. Schema 2 reports keep validating forever — the contract's
   own history rule says a report records the contract it was born under and is never rewritten.
2. **`summary` carries `P0..P3`**, reconciling against `total`. One count set, one reconciliation.
3. **Finding heading:** `### [PN] <short title>`.
4. **Six finding fields:** `Priority` joins the existing five. `Severity` stays, but its
   justification must now name the three factors.
5. **Index columns become `P0 P1 P2 P3`.** The index is a triage queue.
6. **The roll-up's go/no-go verdict is replaced**, not renamed, by a priority distribution
   (`2 × P0 · 5 × P1 · 11 × P2`) plus the highest-priority finding. A ship/don't-ship call needs
   release context the suite does not have and §6 forbids it from inventing. Roll-up frontmatter
   sits outside the report contract, so this costs no schema change.
7. **Renderer class names stay `.sev4` etc.** They are private to
   [`render_report_html.py`](../scripts/render_report_html.py), and
   [`test_render_html.py:122`](../tests/test_render_html.py) asserts on them.

**Rejected — two scored axes (S and P both structural).** Considered and dropped: it put two
numbers with opposite directions in every heading, doubled the count sets and reconciliation, added
an index column set and a second badge, and introduced a failure mode where the two scales turn out
near-diagonal and the second earns nothing. Everything it bought for the reader — seeing the
inputs, being able to overrule — is delivered by the Severity field at a fraction of the surface.

---

## 5. Dependency graph

```
Slice 1  §4: three factors + long-tail rule + inflation guard   ← ships alone, prose only
   │
   └── (independent — no schema, no validator)

Slice 2  schema 3 dispatch + P scale + fixtures
   │
   ├── Slice 3  the derivation: ladder, 6th field, criticality adjustment
   │       │
   │       ├── Slice 4  renderer: P badges, priority bar
   │       │
   │       └── Slice 5  roll-up: distribution replaces verdict
   │
   └────────────────── Slice 6  docs / evals / CHANGELOG / version
```

Slices 2 and 3 **must land in one release** — shipping the relabel without the derivation means a
second schema bump later, and three validator paths to carry forever.

---

## 6. Vertical slices & checkpoints

| # | Slice | Delivers | Size |
|---|-------|----------|------|
| 1 | **The rubric discriminator** | Three factors in §4 + SPEC §4; long-tail rule; inflation guard | S |
| 2 | **Schema 3 + the P scale** | Dispatch validator; `P0..P3` keys; `[PN]` headings; index columns; both fixture sets | M |
| 3 | **The derivation** | §9.4's ladder generalized; `Priority` field; criticality adjustment | M |
| 4 | **Renderer** | P badge, priority bar replacing the severity bar | S |
| 5 | **Roll-up** | Priority distribution replaces the go/no-go banner | M |
| 6 | **Docs & release** | README / SPEC / AGENTS / CHANGELOG / evals / 0.7.0 | M |

⛳ **Checkpoints** after 1, 3 and 6.

---

## 7. Verification strategy

- **Both schemas validate.** Keep every current fixture at `schema: 2` unchanged — they are the
  regression test that old reports still pass. Add schema-3 twins.
- **New invalid fixtures:** `priority-mismatch.md` (P counts ≠ total), a `[P?]`-absent heading, and
  one whose Severity field states no factors.
- **The loud trap does not fire.** No new `SKILL.md` ⇒ `test_evals.py` stays green and **no new
  eval case is needed**. Existing cases asserting on `sev`/go-no-go wording do need updating:
  `ux-audit.json` (including a trigger prompt reading "go/no-go UX verdict"), `render-report.json`,
  `audit-cuj.json`, `usability-audit.json`.
- **The silent trap does.** In [`test_components.py`](../tests/test_components.py):
  - `"severity" in low and "0" in body and "4" in body` (130, 467) still passes — severity survives
    as a reported field.
  - the `"clamp"` assertions (465, 656) need rewording: the clamp now applies to priority.
  - `check_rollup_skill()`'s verdict check (296) is an `or` chain including `"rollup"`, so it stays
    green with the verdict gone — **dropping it is exactly the kind of change this suite would not
    catch.** Add an explicit assertion that the roll-up reports a priority distribution.
  - add an assertion that both auditor personas state the three factors, so severity cannot decay
    into an unjustified number.

---

## 8. Risks & boundaries

- **Severity becoming decoration.** It is no longer structural, so nothing breaks if an auditor
  writes `S3` with a hand-wave. That is the main risk of this design, and the reason slice 1 ships
  first and the persona assertion above exists: the three factors must appear, or the NN/g citation
  is false advertising.
- **Two schema bumps if sequenced wrong** — see the dependency graph note on slices 2 and 3.
- **`docs/images/audit-review.png` goes stale** the moment the roll-up banner changes.
  Regenerating it needs a dogfood run against Sprout; budget for it in slice 6.
- **Findings-only is unchanged.** Priority is a recommendation to a human, not a plan the suite
  executes. No remediation commands, no auto-fix, no writes outside `.ux/audits/`.

---

## 9. Decisions

**Resolved with the human (this thread):**

- One scored scale, not two. Severity is retained as NN/g-grounded reasoning per finding, reported
  as `S1`–`S4`, but never aggregated — the report must stay legible to the human in the loop.
- `sevN` → the scored field becomes `PN`; the surviving `SN` appears only in the Severity field.
- Drop the binary go/no-go rather than renaming it.

**Open:**

- **Non-journey criticality** — unadjusted-and-disclosed (the plan's assumption) vs. an optional
  `criticality` argument on `/usability-audit` and `/ux-audit`.
- **A narrow verdict.** Impeccable keeps a binary pass/fail scoped to one observable dimension
  rather than a ship call. If the roll-up wants *a* verdict, that is the shape that survives §6 —
  but the plan currently drops it entirely.
