---
name: spec-cuj
description: Interview the user one question at a time to author critical user journeys, then store each as its own .ux/cujs file with actor, preconditions, numbered steps and expected outcomes, and regenerate the journey index in the host SPEC.md. Use for "define a CUJ", "author journeys", "write our user journeys", "ux spec".
---

# Spec CUJ — author a critical user journey

Interview the person who knows the product, and turn what they say into a **critical user
journey**: a durable, executable description of something the app exists to do. Each journey
becomes one file in `.ux/cujs/` conforming to the
[CUJ file contract](references/cuj-contract.md), and the host's `SPEC.md` gets a generated
index pointing at them.

Adopt the [`cuj-author`](../../agents/cuj-author.md) persona. Its refusals are the whole
point of this skill: [`validate_cuj.py`](../../scripts/validate_cuj.py) can reject an *empty*
expected outcome, but only a person reading English can reject an *unobservable* one. "It
works" parses fine and verifies never.

**This skill writes to the host repo.** Journeys go in `.ux/cujs/` freely; the host's
`SPEC.md` is **ask-first**, always with a diff.

---

## Inputs

- `--cuj <id>` — revise an existing journey instead of authoring a new one. Optional.
- No target argument: journeys describe the whole app, not a URL.

## Workflow

1. **Locate the host repo root and read what's already there.**
   Run `python3 scripts/validate_cuj.py --dir .ux/cujs` first if the directory exists.
   **Never author on top of a broken directory** — fix or report the existing violations
   before adding to them. Read the existing journeys: you need them for step 6's forced
   ranking, and to avoid writing a near-duplicate of one.

   Compute the next free `id` (`CUJ-001` if none exist). If `.ux/cujs/` is absent, create it
   — no need to ask.

2. **Pick the interview.**
   Check whether `agent-skills:interview-me` is available.

   - **Available** → drive it, one question at a time, until you're confident you have the
     journey.
   - **Not installed** → fall back to [`references/interview-fallback.md`](references/interview-fallback.md),
     and **disclose it**: tell the user `interview-me` isn't installed and you're using the
     built-in question set. **Offer to install it; never auto-install.** They should know
     which interview they got.

   Never degrade silently. A missing dependency that nobody mentions is indistinguishable
   from a worse tool.

3. **Interview — one question at a time.**
   Wait for each answer and follow up before moving on. A wall of questions gets a wall of
   shallow answers and throws away the follow-up, which is where the real answer lives.

   Apply the persona's refusals as you go — especially the **observable-outcome** bar on
   every step's `expect`. Walk the journey *with* them in order, asking "…and then what do
   you **see** happen?" after each action.

   **Never invent.** If they can't answer something, record the gap and stop. An incomplete
   journey marked incomplete beats a fabricated one that looks finished — a guessed step
   becomes the standard `audit-cuj` grades against forever, and it will pass, because you
   wrote it to match what you imagined.

4. **Draft, and read it back.**
   Show the journey — actor, goal, criticality, every step and its expected outcome, the
   success criteria — and get confirmation **before writing anything**. When they correct
   you, the correction is the answer: record that, not your paraphrase.

5. **Write** `.ux/cujs/<id>-<slug>.md`.
   The filename carries the slug; there is no `slug` key. Ten keys, no provenance block, no
   author — see the contract. Body is `## Narrative` and `## Out of scope`.

6. **Self-check.**
   ```
   python3 scripts/validate_cuj.py .ux/cujs/<id>-<slug>.md
   python3 scripts/validate_cuj.py --dir .ux/cujs
   ```
   The `--dir` pass is not redundant: it catches duplicate ids and filename/frontmatter
   mismatches, which a single file structurally cannot reveal. Fix anything it reports
   before continuing.

   Then sanity-check the ranking: if this journey is `critical`, is it genuinely on par with
   the others already marked `critical`? If everything is critical, nothing is.

7. **Regenerate the host's `SPEC.md` index — and ASK first.**
   ```
   python3 scripts/validate_cuj.py --index .ux/cujs
   ```
   **Generate the block. Never write that table by hand or from memory** — the block is a
   pure function of `.ux/cujs/`, and only a script keeps regeneration byte-identical. An
   agent re-rendering it from memory breaks that quietly.

   Then:
   - Replace **only the bytes between the `ux-agent-skills:cuj-index` markers**. Everything
     above and below is theirs and stays untouched.
   - **Show the diff and ask before writing.** This is the one file you touch that the user
     owns.
   - **Markers absent, or no `SPEC.md` at all** → ask before inserting the section or
     creating the file. Append at the end; never reorder their existing sections.
   - **If they decline, stop.** The journey files stand alone — the index is a convenience,
     not the source of truth. Say that, so declining doesn't feel like losing the work.

8. **Confirm the footprint.**
   ```
   python3 scripts/audit_safety.py <host-repo> --profile authoring
   ```
   The `authoring` profile permits `.ux/cujs/` and `SPEC.md`. If it reports anything else,
   you touched something you shouldn't have — revert it. Note this is the **only** skill in
   the suite that runs a profile other than `audit`.

## Boundaries

- **Never edit, refactor, or "fix" host application code.** You capture what the user tells
  you about their app; you don't change it. Journeys and the SPEC.md index block are the
  only things you write.
- **`.ux/cujs/` needs no permission.** Creating it and writing journeys there is expected.
- **The host's `SPEC.md` is ask-first**, with a diff, and only ever the marker block.
- **Never fabricate** a step, actor, precondition, or criticality.
- **Never record an author**, date, revision, or capture method. Git answers all of it.
  `validate_cuj.py` rejects `author` / `authored` / `by` / `email` outright.
- **Never install anything** — offer, and let the user decide.

## Exit criteria (done when)

- One or more `.ux/cujs/<id>-<slug>.md` exist and pass **both** `validate_cuj.py <file>` and
  `validate_cuj.py --dir .ux/cujs`.
- Every step has an `expect` naming something a person or a browser can **observe** — no "it
  works", no "the state updates".
- `success_criteria` says something true *after* the journey, not a restatement of the last
  step.
- The user confirmed the draft before it was written.
- The host's `SPEC.md` index is regenerated **or** the user declined and was told the
  journeys stand alone. If written: generated by `--index`, spliced only between the markers,
  diff shown first.
- If `interview-me` was unavailable, the fallback was used **and disclosed**.
- `audit_safety.py --profile authoring` reports every change confined to `.ux/cujs/` and
  `SPEC.md`.
