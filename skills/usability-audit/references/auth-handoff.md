# Auth Handoff — reaching signed-in surfaces

The shared procedure for auditing what sits **behind a login wall**. Cited by
[`usability-audit`](../SKILL.md), [`audit-cuj`](../../audit-cuj/SKILL.md), and
[`ux-audit`](../../ux-audit/SKILL.md) — one owner, consumers link across, exactly as with
the [report contract](./report-contract.md).

Specified in [SPEC.md §11](../../../SPEC.md). **Nothing here weakens the findings-only
invariant**: an authenticated auditor still writes nowhere but `.ux/audits/`.

> **The one-line version.** The *user* signs in; the auditor waits, confirms, and resumes.
> The agent never holds a credential, so SPEC §6's *"Never enter credentials, bypass
> authentication"* is preserved verbatim rather than carved out.

---

## 1. Why this exists

Every screen behind a login wall used to be a coverage gap. That made the suite rigorous
about the small part of a product in front of the wall and silent about the large part
behind it — and the large part is where the critical journeys live.

**The credential is not the interesting risk.** Behind auth, every screenshot carries the
account's name and email in the app chrome, and every observed-value line quotes real
records. Those images are embedded inline and can be committed. So the procedure below
spends more of its rules on **what an authenticated run leaves behind** (§6) than on how it
gets in (§2) — because that is where the leak actually is.

---

## 2. The rung — five beats

This is a **pre-flight**: it runs before the audit workflow proper, at every entry point.
Auditors navigate to the target as their first act anyway, so the probe costs nothing.

### Beat 1 — Observe the wall

Navigate to the target (`entry_point` for a journey, the in-scope route otherwise) and
**confirm the gate is actually there**. Record what it said *verbatim* — the redirect, the
form's heading, the visible strings.

> *Auth-gated* is an **observation, never an assumption**. An auditor that assumes a wall it
> never saw has fabricated a coverage gap, which is the same defect as fabricating a
> finding. This is L0's discipline applied to the gate itself.

Also run, in the host repo:

```
git ls-files .ux/audits/
```

Its answer changes what you say in beat 2. See §6.

### Beat 2 — Ask once, naming everything

An **ask-first** gate in SPEC §6's sense: you ask before reaching the gated screens, and you
do not proceed on silence. One interruption, and it must carry all of:

1. **The wall you observed**, verbatim.
2. **What it unblocks** — the journey ids and criticality, or the scope.
3. **The hygiene ask**: *use a throwaway or seeded account, not production* — with the
   reason, that every step is about to be screenshotted into `.ux/audits/assets/`.
4. **The artifact posture** for this repo (§6), including the `.gitignore` line and the
   fact that **you cannot apply it yourself**.
5. **The way out** — declining is a first-class answer that produces an honest skip, not a
   failure.

### Beat 3 — The user signs in

In the browser the auditor is already driving. The auditor is **idle**: it types nothing,
reads nothing, stores nothing. Do not narrate, poll, or screenshot during this beat.

### Beat 4 — Re-observe and confirm

On "done", **verify the session actually holds** before proceeding — navigate again and
observe. A failed or abandoned login must never be recorded as a satisfied rung; that would
manufacture the very state the audit is supposed to test for.

Then record **the rung, not the identity** (§5).

### Beat 5 — Resume, or skip with a named cause

Session confirmed → return to the workflow (for `audit-cuj`, back to **L0** to re-check the
precondition against the now-authenticated app). Declined or unanswered → the existing skip
path, with a named cause and a `Repair:` line.

---

## 3. The rung's own precondition — an attended surface

The rung requires an **attended, human-visible browser surface**: a human must be able to
*touch* the browser the auditor drives. A headless browser has no seat for them.

Where none is available, the rung **cannot be attempted**, and the report must say exactly
that. It is **not** a decline:

| Situation | Recorded as |
|---|---|
| User was asked and said no | `declined by user` |
| No attended browser surface (headless, scheduled, unattended) | `handoff unavailable — no attended browser surface` |

Reporting the second as the first blames a user who was never asked. Unattended operation
is a **non-goal** (SPEC §11.1); in that context today's honest skip is the correct outcome.

---

## 4. What may satisfy the rung — a capability test, not a vendor

The suite names **no browser and no password manager** — SPEC §5.1 says *"a browser MCP"* on
purpose, and that portability is defended, not incidental. A mechanism may satisfy beat 3
when **both** clauses hold:

> **(a)** The secret **never enters agent context** — the agent may request, a human
> approves, and the value passes directly to the page.
>
> **(b)** The resulting session lands in a **browser context isolated from the user's daily
> profile**.

Clause (a) is the obvious one and rarely discriminates. **Clause (b) does the real work**,
for the reason in §1: a mechanism that authenticates flawlessly into a browser full of
production sessions, other tabs, and personal bookmarks has made the artifact problem worse
while solving a problem that was not open.

| Mechanism | (a) | (b) | Verdict |
|---|:--:|:--:|---|
| **Human handoff** (§2) | ✅ agent types nothing | ✅ whichever context it drives | **The rung.** Zero dependencies — no harness feature, no host cooperation, no file on disk. That is why it is the *floor*, not a fallback. |
| **App-side test login** (seeded account, dev-only route) | ✅ no credential exists to leak | ✅ | Qualifies, but needs host-app cooperation so it cannot be *the* rung. Recommended configuration instead — §5. |
| **Agent-mediated password-manager autofill** | ✅ value never in context | ❌ | **Rejected.** Its purpose is to drive the user's real browser *with existing sessions* — clause (b) inverted. Rejected for failing (b), **not** for being a particular product: a mechanism meeting both clauses qualifies whatever its vendor. |
| **Saved session material** (storage-state file, exported profile) | ✅ | ⚠️ depends | **Rejected here.** It exists to serve unattended runs, a non-goal, and puts live session tokens in a file the auditor would have to reference. Revisit only alongside CI support. |
| **Credentials via env var, `.env`, or chat** | ❌ | — | **Rejected.** Fails (a) outright, and independently collides with SPEC §6 and with host-harness rules that prohibit an agent entering credentials at all. |

**Why the rejections are written down.** The password-manager path keeps looking attractive
because it optimises the surface that is *already safe*. Stating the test means the next
proposal is measured against two clauses instead of relitigated from scratch.

---

## 5. The recommended host configuration

Not a rung and not enforced — the setup to **recommend**, because it dissolves both surfaces
instead of managing either:

- **A seeded, non-production account** with synthetic data. Nothing sensitive is ever
  captured, so nothing needs redacting. This is SPEC §9.7's principle applied to pixels:
  **no PII in the artifact beats a rule about handling PII in the artifact.**
- **A dedicated audit browser profile**, kept signed in to that account between runs. This
  is *not* the rejected "saved session material": the auditor never reads, references,
  copies, or writes the profile — it drives whatever browser it is handed. The distinction
  is **who touches the session material**, and here nobody but the browser does.

---

## 6. The artifact posture — the surface that actually leaks

When a run authenticates, **recommend ignoring `.ux/audits/` wholesale** — reports, assets,
and the derived `.html` alike — and recommend it **at the moment auth is established**, not
at report-write time, which is too late if anything auto-commits.

Wholesale, because narrower rules do not hold:

- [`render_report_html.py`](../../../scripts/render_report_html.py) base64-embeds every
  `./assets/*` image into the `.html` written beside the `.md`. Ignoring the PNGs leaves
  their bytes riding into git inside the companion.
- The Markdown leaks independently of both: *"Observed: row reads `Invoice #4417 — Acme
  Corp`"* is PII no image-level rule touches.

### 6.1 `.gitignore` does not untrack — check first

This is what beat 1's `git ls-files .ux/audits/` is for.

| `git ls-files .ux/audits/` | What it means | What to say |
|---|---|---|
| **empty** | Untracked. The ignore line will work. | Recommend the line; proceed on the user's word. |
| **non-empty** | **Already tracked.** Git keeps tracking what it already tracks, so the ignore line is *decorative* and the next capture commits over the top. | Say so plainly, name the tracked paths, and let the user choose: untrack first (`git rm --cached -r .ux/audits/`), or accept the capture knowingly. Never write behind a false sense of safety. |

### 6.2 The recommendation, verbatim

The auditor **does not write the host's `.gitignore`** — that is outside the audit profile's
allowlist ([`audit_safety.py`](../../../scripts/audit_safety.py),
`EXTRA_BY_PROFILE["audit"] == ()`), and the emptiness of that tuple is load-bearing.
Recommend and let the user apply:

```
# Authenticated UX audit output — screenshots and quoted records of a live account
.ux/audits/
```

### 6.3 Prefer structural description to verbatim quotation

Ignoring files does nothing about the report *text*. There is a clean line:

- **App-authored strings** — labels, placeholders, button copy, error messages — are
  exactly what an auditor must quote verbatim. Quote them.
- **User-authored data** — record contents, names, amounts, addresses — should be
  **described structurally**: *"the top invoice row"*, not *"Invoice #4417 — Acme Corp —
  $12,400"*.

The finding is just as actionable either way; only the leak differs.

### 6.4 The invariant still applies

An authenticated run is still checked by
[`audit_safety.py`](../../../scripts/audit_safety.py), and `writes_under()` keeps the
auditor's own writes observable even once `.ux/audits/` is ignored — so "nothing escaped"
cannot be satisfied by a run that wrote nothing (SPEC §5.2). The CLI enforces both halves:
it exits 1 on *"no writes were observed"* and prints the writes when it passes.

**Take the `--snapshot` before the handoff, not after.** Under an ignored `.ux/audits/`,
previous runs' reports are still sitting in the working tree; the baseline is what stops them
from answering "were writes observed?" on this run's behalf.

---

## 7. Never — once a live session exists

These govern what becomes tempting only **after** beat 4, a threat surface that does not
exist in an unauthenticated run.

- **Never read, transcribe, or store session material.** No cookies, `localStorage`,
  `sessionStorage`, or tokens. A single `evaluate_script` lifts `document.cookie` into the
  transcript — a second, independent reason for the ban the precondition ladder already
  imposes on `evaluate_script` for state injection.
- **Never read back a filled credential field.** Where a mechanism satisfies clause (a) by
  keeping a value out of context, that guarantee holds only until the agent goes looking.
  It is a rule, not a property to lean on.
- **Never leave the audited scope while a session is live.** No account, billing, or
  settings pages the scope did not name. An authenticated session is not a licence to
  browse, and anything you see there lands in a report.
- **Never record the account identity.** No `account:` frontmatter key, no email, no vault
  or profile item name, anywhere in a report. This is SPEC §9.7's `author:` precedent
  applied unchanged — *PII in a file that ships in the host's repo.* Record the **rung**,
  not who satisfied it.
- **Never log the user out or tear the session down.** A logout is a **state reset**, which
  the ladder's L2.5 permits only when a journey names it. Leave the session exactly as
  found and **say so** (§8).

> **The asymmetry, stated because it reads as inconsistent.** The *session* is left alone,
> but any credential *grant* a mechanism issued is **released at end of run**. A session is
> app state the user may care about; a grant is not, and releasing it has no destructive
> side effect.

---

## 8. Recording it — the report and the hand-back

### In the report

**No new frontmatter key.** The `## Appendix` carries one line:

```markdown
## Appendix
- Access: auth-gated; satisfied at L3 (user handoff). Account not recorded.
```

Other forms, by outcome:

```markdown
- Access: auth-gated; declined by user. Gated screens below are not inspected.
- Access: auth-gated; handoff unavailable — no attended browser surface.
```

A gated screen **reached** via handoff is **no longer a coverage gap** and must not be
listed as one ([report contract §5](./report-contract.md)). Only screens that stayed
unreached belong under *Coverage / not inspected*.

### In the closing summary

State what the run left behind — an explicit hand-back, not a silent one:

- the browser is **still signed in**, and why the auditor did not log out;
- whether `.ux/audits/` is still uncommitted-and-unignored, if so.
