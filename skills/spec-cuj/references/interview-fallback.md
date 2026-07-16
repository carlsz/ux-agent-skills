# Interview — built-in fallback question set

Used **only when [`agent-skills:interview-me`](https://github.com/addyosmani/agent-skills) is
not installed.** Prefer that skill when it's available: it is purpose-built for driving an
interview to confidence, and this set is a smaller thing.

When you use this instead, **say so** — tell the user `interview-me` isn't installed, that
you're using the built-in questions, and offer to install it. Never auto-install, and never
degrade silently: they should know which interview they got.

## How to run it

**One question at a time. Wait for the answer. Follow up before moving on.**

A wall of questions gets a wall of shallow answers, and it throws away the follow-up — which
is usually where the real answer is. The questions below are a spine, not a script: if an
answer is vague, the [`cuj-author`](../../../agents/cuj-author.md) refusals apply and you ask
again. Getting one journey right beats getting three written down.

Read the draft back before writing anything. When they correct you, **the correction is the
answer** — record that, not your paraphrase of it.

## The questions

### 1. Who is this for — specifically?
> "Who does this journey? Not 'users' — describe one person, and what they already have when
> they arrive."

Fills `actor`. Reject "the user" / "everyone". You want *"Returning user with 3-10 existing
tasks, opens the app daily to capture new ones"*. If the honest answer really is everyone,
this journey isn't critical — it's generic. Say so.

### 2. What are they here to get done?
> "What outcome are they after? And what does *done* look like **to them**?"

Fills `goal`. An outcome, not a feature list. "Capture a new task without navigating away",
not "the form has a title field and a save button".

### 3. Where do they start?
> "What screen or URL are they on when this begins?"

Fills `entry_point`.

### 4. What has to be true before they begin?
> "What state is the app in already? Logged in? Existing data? Anything they had to do first?"

Fills `preconditions` — things that are **true**, not things they **do**. This split matters:
if setup hides inside step 1, then *failing to set up* looks identical to *the journey being
broken*, and a verification run reports a catastrophe for what was really "couldn't run this".

### 5. Walk me through it. What's the first thing they do?
> "…and what do they **see** happen?"

Fills `steps[0]`. The second half of that question is the one that matters. Push until the
answer is **observable**:

| They say | Ask |
|----------|-----|
| "It works" | "If I were watching over your shoulder — what would I see?" |
| "The state updates" | "What changes on screen?" |
| "It saves" | "How would you know it saved? What would prove it?" |

### 6. And then? *(repeat until the goal is reached)*
> "What's next — and what do they see happen?"

Fills the remaining `steps`. One action per step: "fill out the form and submit" is two.
Findings cite `step <n>`, so a bundled step points at a range and diagnoses nothing.

### 7. Afterwards — how do you know it really worked?
> "The steps all did what you said. What must still be true a minute later, or after a
> reload, for this to have actually succeeded?"

Fills `success_criteria`. **Don't let this become a restatement of the last step.** The
question is deliberately about *after*, because a journey can pass every step and still lose
the data on reload — and if the criteria just echo step N, that whole class of silent failure
is invisible.

### 8. If this broke tomorrow, what breaks for the business?
> "Not 'would it be bad' — what specifically stops working, and for whom?"

Fills `criticality`. Then **rank it against the journeys already in `.ux/cujs/`**. It's a
forced ranking, not a mood: if everything is `critical`, nothing is, and the severity cap
that reads this field stops meaning anything.

### 9. What is this journey deliberately *not* about?
> "What related things should I leave out — separate journeys, edge cases, other paths?"

Fills `## Out of scope`. This stops scope creep now, and later it stops a verification run
inventing coverage it never had.

### 10. Why does this journey exist?
> "Two or three sentences — why does this matter enough to write down?"

Fills `## Narrative`. This is the part a reviewer argues with, and the thing that justifies
the `criticality` in question 8.

## When they can't answer

**Record the gap and stop.** Do not fill it in for them.

An incomplete journey marked incomplete beats a fabricated one that looks finished. A guessed
step doesn't just mislead once — it becomes the standard every future verification run is
graded against, and it will pass, because you wrote it to match what you imagined.
