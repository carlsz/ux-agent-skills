# The published-directory review — findings and decisions

The plugin is listed in the Claude directory, which re-scans every published version and
reports what it finds. This file is the standing answer: what was fixed, what was declined,
and **why**, so the next scan of the same code doesn't restart the argument.

Two of these findings are real and are fixed. Three are false positives of a kind this plugin
will keep attracting, because a scanner reading prose cannot tell a suite that **writes about**
credentials and shell commands from one that **uses** them. That is worth stating once, with
evidence, rather than re-deriving each release.

Review of **v0.6.0** (`3593ea6`), checked 2026-09-23 — *validation has warnings, directory
policy has warnings, security scan passed*. Fixes shipped in **v0.6.1**.

---

## Fixed

### 1. "No frontmatter block" — 2 findings · `agents/README.md`, `commands/README.md`

**Real, and the one that mattered.** `agents/` and `commands/` are swept wholesale at load
time: every `.md` in them is a component, frontmatter or not. The two catalog READMEs were
therefore loading as a phantom persona named **"README"** and a stray **`/README`** command,
both inside the always-on token budget of every session in every host app that installed the
plugin.

This was a *known* defect — `tasks/plan.md` recorded it as "unfixed; a repo-structure
decision" — and AGENTS.md step 8 actively manufactured it by instructing maintainers to keep
a catalog in "the relevant subdirectory README". The review is what moved it from known to
fixed.

**Fix.** The three layer catalogs moved to [`docs/`](agents.md) —
[`agents.md`](agents.md), [`commands.md`](commands.md), [`skills.md`](skills.md).
`skills/README.md` was never discovered (skills resolve as `skills/<name>/SKILL.md`, a
directory rather than a glob) and moved only to keep the three together. AGENTS.md step 8 now
says the opposite of what it said. `check_discovery_dirs()` in `tests/test_components.py`
globs both directories and fails on any `.md` lacking the frontmatter its layer requires — the
first and only globbing check in that file, because the hand-wired ones can verify only
components someone meant to author.

### 2. "No icon" — `.claude-plugin/plugin.json`

Real and trivial. Added [`icon.svg`](../icon.svg) at the plugin root — a magnifier over an
interface, inline SVG, no external references — and `"icon": "./icon.svg"` to the manifest.

---

## Declined, with cause

### 3. "Uses a credential from the user's machine" — `.claude-plugin/plugin.json`

> *Suggested remedy: ask the user for the value through a `userConfig` option
> (`sensitive: true`) instead of reading it from their machine.*

**Declined — false positive, and the remedy is the mechanism this plugin rejected on the
record.** Nothing in the plugin reads a credential, from the user's machine or anywhere else.
There is no credential store read, no env-var read, no `.env`, no keychain call, no storage-state
file; `grep` finds credential vocabulary **only** in prose. The manifest the finding anchors to
is fourteen lines of metadata.

What the scanner is reading is
[`auth-handoff.md`](../skills/usability-audit/references/auth-handoff.md) — a document whose
entire subject is credentials, and most of whose length is a **rejection table** explaining
which credential mechanisms the suite refuses and why. "Credentials via env var, `.env`, or
chat" appears there as a rejected row. The design is the inverse of the finding: SPEC §11's
rung is the *human* signing in while the agent waits, idle, precisely so no component ever
holds a secret, and SPEC §6's *"Never enter credentials, bypass authentication"* survives
verbatim rather than being carved out.

Adopting the remedy would mean introducing a credential the plugin holds, to resolve a report
that it holds one. A `userConfig` secret fails clause (a) of the capability test in §4 of that
reference — the value would enter agent context — which is the same ground on which the
env-var row was rejected. **No change, and no change is possible without reversing SPEC §11.**

### 4. "Contains a download-and-run command" — `docs/images/audit-review.png`

**Declined — the finding's own guidance says so.** The file is a 1 MB PNG screenshot embedded
in the README: a Claude Code session beside a rendered HTML audit report. It is not executed,
not referenced by any component, and not reachable from any instruction. The plugin ships no shell
script at all; `grep` for pipe-to-shell across every `.md`, `.py`, `.json` and `.yml` returns
nothing; and the single subprocess any script makes is `_git()` in `audit_safety.py`, an argument
list with no shell. The finding's remedy reads: *"Where it only appears in documentation,
nothing needs to change."* It appears in documentation. Nothing changed.

### 5. "CLAUDE.md at the plugin root isn't loaded" — `CLAUDE.md`

**Declined — informational, and already true by design.** `CLAUDE.md` is a symlink to
[`AGENTS.md`](../AGENTS.md), which is instructions for agents working **on this repo** — layout,
authoring rules, the two test traps. It is not installer-facing, so the finding's conditional
("if the instructions are meant for people who install the plugin, move them into a skill")
does not apply; *not* being loaded in a host app is the desired behavior, not a defect. Its
second clause — remove a `CLAUDE.local.md` — is moot: there has never been one. AGENTS.md's own
first line already routes installers to `README.md`.

### 6. "Images and fonts passed without a code check" — informational

No action. One PNG, no fonts. The note records that the scanner let a well-formed image through
without reading it as code; it asks nothing of the author.

---

## The pattern worth remembering

Findings 3 and 4 share a root cause: **this plugin's subject matter is adversarial to prose
scanners.** It is a security-conscious auditing suite, so it documents credentials, login walls,
gitignore hygiene and shell invocations at length — and documenting a hazard pattern-matches
against using one. Expect both to recur on every future version. The defense is not to launder
the prose until a scanner likes it, which would cost the reader the rejection tables that make
the design reviewable; it is to answer once, here, with the `grep` that settles it.

Finding 1 is the counter-lesson, and the reason this file does not dismiss scanners wholesale:
an automated reader with no knowledge of the design caught a real defect that six test files of
hand-written, deliberately paranoid checks had missed across five releases — because every one of
those checks was hand-wired to the components their author already knew about.
