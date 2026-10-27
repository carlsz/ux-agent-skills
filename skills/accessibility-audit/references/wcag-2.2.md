# WCAG 2.2 — the audit lens

The success criteria, organized by **what you can observe and what proves it**. This is
not a remediation guide: for the corrected markup and ARIA patterns, read
[`web-quality-skills:accessibility`](https://github.com/addyosmani/web-quality-skills)
and its `references/WCAG.md`, which pair every rule with its fix. This file answers the
auditor's question instead — *how do I know whether this app passes, and what do I write
down?*

Three things govern everything below.

**A level is not a priority.** `A` / `AA` / `AAA` says how central a rule is to the
standard. The grade comes from impact on the user the defect affects — see the report
contract's [*A conformance level is not a
priority*](../../usability-audit/references/report-contract.md#a-conformance-level-is-not-a-priority).
Cite the level; grade the impact.

**Most of this is unobservable from source.** The *Evidence* column below says what a
claim actually rests on. Where it names a runtime observation, a static run can only find
markup that *looks* wrong — that finding is `potential — unverified`, and it never becomes
a conformance claim.

**Score only what you checked.** Each criterion you evaluate becomes one `health` item
(§4.1). Criteria you did not reach go in the appendix's coverage list, not in the
scorecard as passes.

---

## Perceivable

| Criterion | What to check | Evidence it rests on |
|-----------|---------------|----------------------|
| **1.1.1** Non-text content (A) | Every `img`, icon button, chart and media has a text alternative; decorative images have an *empty* alt, not a missing one | Markup, or the accessibility tree's name for the node |
| **1.2.x** Time-based media (A/AA) | Captions, transcript, audio description | The media element and its tracks; n/a when the surface has no media |
| **1.3.1** Info and relationships (A) | Headings, lists, tables and form groupings are *marked up* as such, not simulated with styling | Markup + accessibility tree |
| **1.3.5** Identify input purpose (AA) | `autocomplete` on fields collecting the user's own data | Markup |
| **1.4.1** Use of colour (A) | No state is conveyed by colour alone — error, selected, required | Render; a greyscale screenshot settles it |
| **1.4.3** Contrast, minimum (AA) | 4.5:1 normal text, 3:1 large text, against the *computed* background | **Computed** colours, measured. A token pair read from CSS is an estimate until the render confirms what actually composites |
| **1.4.10** Reflow (AA) | No horizontal scroll at 320px-equivalent width | Render at that viewport |
| **1.4.11** Non-text contrast (AA) | 3:1 for control boundaries, focus indicators, meaningful graphics | Measured on the render |
| **1.4.12** Text spacing (AA) | Nothing clips or overlaps with spacing overrides applied | Render with the override |

## Operable

| Criterion | What to check | Evidence it rests on |
|-----------|---------------|----------------------|
| **2.1.1** Keyboard (A) | Every interactive element reachable and operable by keyboard alone | Keyboard interaction. A `div` with an `onClick` and no `tabindex`/role is the classic failure |
| **2.1.2** No keyboard trap (A) | Focus can always leave — especially modals and embeds | Keyboard interaction |
| **2.4.1** Bypass blocks (A) | Skip link or landmark structure | Markup + accessibility tree |
| **2.4.3** Focus order (A) | Tab order follows the visual/logical order; a dialog moves focus in and restores it on close | Keyboard interaction, step by step |
| **2.4.4** Link purpose (A) | Link text makes sense out of context — not "click here", not a bare URL | Markup or rendered text |
| **2.4.7** Focus visible (AA) | A visible indicator on every focusable element; `outline: none` without a replacement fails | Render, screenshotted. **Capture this one** — a reader will not take it on trust |
| **2.4.11** Focus not obscured (AA, 2.2) | The focused element is not hidden behind a sticky header or toast | Render while tabbing |
| **2.5.7** Dragging movements (AA, 2.2) | Any drag interaction has a single-pointer alternative | Interaction |
| **2.5.8** Target size, minimum (AA, 2.2) | 24×24 CSS px, or adequate spacing | Measured on the render |
| **2.2.x** Enough time (A/AA) | Timeouts can be extended or turned off | Interaction; n/a with no timed content |
| **2.3.1** Three flashes (A) | No content flashes more than three times a second | Render |
| **2.3.3** Animation from interactions (AAA) | `prefers-reduced-motion` respected | Media-query behaviour on the render |

## Understandable

| Criterion | What to check | Evidence it rests on |
|-----------|---------------|----------------------|
| **3.1.1** Language of page (A) | `<html lang>` present and correct | Markup |
| **3.2.3 / 3.2.4** Consistent navigation and identification (AA) | Repeated components appear in the same order and are named consistently | Across several screens |
| **3.2.6** Consistent help (A, 2.2) | Help affordances in a consistent place | Across several screens |
| **3.3.1** Error identification (A) | The error is *described in text*, and says which field | Triggered error state on the render |
| **3.3.2** Labels or instructions (A) | Every input has a programmatic label — placeholder alone is not a label | Accessibility tree |
| **3.3.3** Error suggestion (AA) | The message says how to fix it, when that is knowable | Triggered error state |
| **3.3.7** Redundant entry (A, 2.2) | Information already given is not demanded again | Multi-step flow |
| **3.3.8** Accessible authentication (AA, 2.2) | No cognitive-function test without an alternative; paste into password fields is allowed | The auth screen — observe only, never authenticate |

## Robust

| Criterion | What to check | Evidence it rests on |
|-----------|---------------|----------------------|
| **4.1.2** Name, role, value (A) | Every control exposes all three; custom widgets carry the right role and state | Accessibility tree. This is where "it works with a mouse" and "it exists for assistive tech" diverge |
| **4.1.3** Status messages (AA) | Async status reaches assistive tech without stealing focus — live region or equivalent | Markup *and* an observed update |

---

## Grading, in this lens

The tie-breakers are the contract's (§4). What is particular here is **who** "the user" is:
read every rule as being about the user this defect affects.

| Shape of defect | Typical grade | Why |
|-----------------|---------------|-----|
| A control that assistive tech cannot identify or operate, on a required path | `P0` | *Impossible* for that user, tie-breaker 2 — not merely difficult |
| A keyboard trap in a modal the flow depends on | `P0` | The user cannot leave; no workaround |
| Focus order that scatters, so the form is completable only by guesswork | `P1` | Significant difficulty, not impossibility |
| An optional field with no programmatic label | `P2` | A workaround exists: skip it |
| Secondary caption at 4.3:1 against 4.5:1 | `P2` | Read with mild effort |
| A AAA-level nicety on a non-critical surface | `P3` | Little real impact |

Two of those are the characteristic mistakes of this lens, in opposite directions. Filing
the first row as `P2` because a sighted mouse user is unaffected is how a blocker becomes
polish. Filing the fifth as `P1` because "AA is a legal requirement" is pricing the letter
instead of the impact — and it is what made the suite's `GO` unreachable.

**Every failed criterion is a finding**, including the `P3`s. A team under a conformance
obligation reads the findings and the scorecard; the release gate is about impact and does
not claim to be a compliance attestation.

## What automated tooling does and does not settle

axe-core and Lighthouse catch roughly a third of WCAG failures, and almost none of the
judgement-bound ones: whether alt text is *meaningful*, whether focus order is *logical*,
whether an error message *identifies* the error, whether a live region announces at a
useful moment. Carry the tool's output as evidence where you ran it, name the tool in
`frameworks`, and state in the appendix what it covered. **"0 violations" is a statement
about the tool, never about the app.**
