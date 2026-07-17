---
name: ux-spec
description: Interview you to define your app's critical user journeys, write each to .ux/cujs, and regenerate the journey index in your SPEC.md. Invokes the cuj-author persona via the spec-cuj skill.
argument-hint: "[--cuj <id>]"
---

# /ux-spec

Define what your app is **for**. This interviews you one question at a time, turns your
answers into critical user journeys under `.ux/cujs/`, and regenerates the journey index in
your `SPEC.md`. Thin entry point — the [`spec-cuj`](../skills/spec-cuj/SKILL.md) skill does
the work, driving the [`cuj-author`](../agents/cuj-author.md) persona.

The journeys you write here are what [`/cuj-audit`](./cuj-audit.md) later replays against your
running app to tell you which step broke.

## Arguments

`$ARGUMENTS`:

- **`--cuj <id>`** — revise an existing journey instead of authoring a new one, e.g.
  `/ux-spec --cuj CUJ-001`. Omit to author the next one.

There is no `target`: journeys describe your product, not a URL.

## Behavior

1. Validate any journeys already in `.ux/cujs/`, and compute the next free id.
2. Invoke the `spec-cuj` skill, which drives
   [`agent-skills:interview-me`](https://github.com/addyosmani/agent-skills) when it's
   installed and falls back to its own question set — telling you which — when it isn't.
3. Read the drafted journey back to you for confirmation, then write
   `.ux/cujs/<id>-<slug>.md` and self-check it.
4. Regenerate the `SPEC.md` index block — **asking first, with the diff**.

## What to expect from the interview

It moves quickly where it can and slows down where it counts. For the descriptive parts — who
the actor is, where they start, what they do — it leads with a **guess** you just confirm or
correct, so most of the interview is fast. It only opens up and pushes back on the parts a
later verification is graded against:

- **"Users"** isn't an actor. Who specifically, and what do they already have?
- **"It works"** isn't an expected outcome. What would you *see*? — asked open, never as a
  guess you can wave through with "yes", because this is the line `audit-cuj` scores against.
- **`critical` has to be earned.** It won't ask how important a journey is, it'll ask what
  breaks if it fails — and grade from that. Two journeys that both kill the product are both
  critical, and it should say so rather than invent a spread.

If you don't know something, say so: it records the gap rather than inventing an answer.

## Guarantees

- **Never edits your application code.** It captures what you say about your app.
- **`.ux/cujs/` is written freely**; **your `SPEC.md` is ask-first**, always with a diff, and
  only ever the block between the `ux-agent-skills:cuj-index` markers. Prose around it is
  untouched, and declining leaves the file alone — the journeys still stand.
- **Records no author, date, or revision.** Git already answers those, and no PII goes into
  your repo.
- **Never installs anything** — it offers.
