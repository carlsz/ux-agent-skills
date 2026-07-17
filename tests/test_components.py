#!/usr/bin/env python3
"""Structural checks for the usability-auditor triad (persona / skill / command).

These files ARE the auditor's behavior — their instructions are the product — so the
"tests" assert that the safety-critical invariants and wiring are present and can't be
silently dropped. Prose quality is a human-review concern; this guards structure.

Run: `python3 tests/test_components.py` (exit 0 = pass, 1 = fail).
"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def _frontmatter(path: Path) -> tuple[dict | None, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    return yaml.safe_load(parts[1]), parts[2]


def _require(cond: bool, msg: str, bucket: list[str]) -> None:
    if not cond:
        bucket.append(msg)


def _asks_first(low: str) -> bool:
    """True if the body states an ask-first gate, in any of its usual spellings.

    Deliberately NOT a bare `"ask" in low`: that substring is also satisfied by the word
    "task", and a to-do app is this suite's running example — so the loose form is one
    edit away from silently passing forever. Accepts the hyphenated adjective too
    ("the write is ask-first"), which reads better in prose than a bare imperative.
    """
    return any(p in low for p in ("ask before", "ask first", "ask-first"))


def check_persona() -> list[str]:
    errs: list[str] = []
    path = ROOT / "agents" / "usability-auditor.md"
    if not path.exists():
        return [f"missing {path.relative_to(ROOT)}"]
    fm, body = _frontmatter(path)
    _require(isinstance(fm, dict), "persona: frontmatter must parse to a mapping", errs)
    if isinstance(fm, dict):
        _require(fm.get("name") == "usability-auditor",
                 "persona: frontmatter 'name' must be 'usability-auditor'", errs)
        _require(bool(str(fm.get("description", "")).strip()),
                 "persona: frontmatter needs a non-empty 'description'", errs)
        desc = str(fm.get("description", "")).lower()
        _require(any(t in desc for t in ["usability", "heuristic", "ux audit"]),
                 "persona: description should carry a trigger phrase "
                 "(usability / heuristic / UX audit)", errs)
    low = body.lower()
    # Safety-critical boundary: findings-only, never edits host code.
    _require("never" in low and ("edit" in low or "modif" in low) and "host" in low,
             "persona: must state the never-edit-host-code boundary", errs)
    # Render-vs-source honesty rule.
    _require("unverified" in low or "render" in low,
             "persona: must state the render-vs-source honesty rule", errs)
    # Output format = 0-4 severity report.
    _require("severity" in low and "0" in body and "4" in body,
             "persona: must define the 0-4 severity output format", errs)
    # All four frameworks (Phase 3), applied — not deferred.
    for fw in ("nielsen", "shneiderman", "npcis"):
        _require(fw in low, f"persona: must reference the {fw} framework", errs)
    _require("ai design" in low or "ai-heuristics" in low or "ai heuristic" in low,
             "persona: must reference the AI design heuristics", errs)
    _require("not yet in scope" not in low and "not yet supported" not in low,
             "persona: frameworks must be applied, not deferred (stale Phase-1 wording)",
             errs)
    return errs


def check_skill() -> list[str]:
    errs: list[str] = []
    path = ROOT / "skills" / "usability-audit" / "SKILL.md"
    if not path.exists():
        return [f"missing {path.relative_to(ROOT)}"]
    fm, body = _frontmatter(path)
    _require(isinstance(fm, dict), "skill: frontmatter must parse to a mapping", errs)
    if isinstance(fm, dict):
        _require(bool(str(fm.get("name", "")).strip()),
                 "skill: frontmatter needs a 'name'", errs)
        _require(bool(str(fm.get("description", "")).strip()),
                 "skill: frontmatter needs a non-empty 'description'", errs)
    low = body.lower()
    _require(".ux/audits" in low,
             "skill: must document writing reports to .ux/audits", errs)
    _require("report-contract" in low,
             "skill: must reference the shared report-contract", errs)
    _require("nielsen" in low, "skill: must apply Nielsen's heuristics", errs)
    _require("static" in low, "skill: must describe the static evaluation mode", errs)
    _require("unverified" in low,
             "skill: static-mode runtime findings must be labeled unverified", errs)
    _require("exit" in low or "done when" in low or "acceptance" in low,
             "skill: must state explicit exit criteria", errs)
    # Safety invariant restated at the workflow level.
    _require("never" in low and "outside" in low,
             "skill: must forbid writing outside .ux/audits", errs)
    # Phase 2 — live evidence gathering.
    _require("live" in low, "skill: must describe the live evaluation mode", errs)
    _require("screenshot" in low, "skill: live mode must capture screenshots", errs)
    _require("assets" in low, "skill: screenshots go under .ux/audits/assets", errs)
    _require("navigate" in low or "browser" in low,
             "skill: live mode must drive a browser (navigate the app)", errs)
    _require("ask" in low and ("server" in low or "navigat" in low),
             "skill: must require asking before starting a server / navigating", errs)
    _require("verified" in low,
             "skill: live-mode runtime findings are verified (vs static's unverified)", errs)
    # T2.2 — hybrid auto mode-selection.
    _require("hybrid" in low, "skill: must describe hybrid mode", errs)
    _require("prefer" in low and "live" in low,
             "skill: hybrid must prefer live when a URL / dev server is available", errs)
    _require("fall" in low and "back" in low,
             "skill: hybrid must fall back to static when no live target", errs)
    _require("actual" in low or "actually" in low,
             "skill: must record the mode actually used (not the one requested)", errs)
    _require("gap" in low or "not inspected" in low,
             "skill: must log coverage gaps, never silently", errs)
    # T3.2 — all four frameworks applied, findings grouped + de-duped by framework.
    for fw in ("nielsen", "shneiderman", "npcis"):
        _require(fw in low, f"skill: must apply the {fw} framework", errs)
    _require("ai design" in low or "ai-heuristics" in low or "ai heuristic" in low,
             "skill: must apply the AI design heuristics", errs)
    _require("dedup" in low or "de-dup" in low or "duplicat" in low,
             "skill: must de-duplicate overlapping findings across frameworks", errs)
    _require("primary" in low,
             "skill: overlapping findings attributed to a primary framework", errs)
    _require("arrive in a later phase" not in low and "later phase" not in low,
             "skill: frameworks must be applied now, not deferred to a later phase", errs)
    return errs


def check_command() -> list[str]:
    errs: list[str] = []
    path = ROOT / "commands" / "usability-audit.md"
    if not path.exists():
        return [f"missing {path.relative_to(ROOT)}"]
    fm, body = _frontmatter(path)
    _require(isinstance(fm, dict), "command: frontmatter must parse to a mapping", errs)
    if isinstance(fm, dict):
        _require(bool(str(fm.get("name", "")).strip()),
                 "command: frontmatter needs a 'name'", errs)
        _require(bool(str(fm.get("description", "")).strip()),
                 "command: frontmatter needs a non-empty 'description'", errs)
    low = body.lower()
    # Thin wiring: routes to the skill / persona.
    _require("usability-audit" in low or "usability-auditor" in low,
             "command: must invoke the usability-audit skill / persona", errs)
    # Documents its arguments.
    for arg in ("target", "scope", "mode"):
        _require(arg in low, f"command: must document the {arg!r} argument", errs)
    # T2.2 — all three modes supported (no longer static-only).
    for mode in ("static", "live", "hybrid"):
        _require(mode in low, f"command: must document the {mode!r} mode", errs)
    return errs


def check_rollup_skill() -> list[str]:
    """The suite roll-up skill fans out to auditors and normalizes into the contract."""
    errs: list[str] = []
    path = ROOT / "skills" / "ux-audit" / "SKILL.md"
    if not path.exists():
        return [f"missing {path.relative_to(ROOT)}"]
    fm, body = _frontmatter(path)
    _require(isinstance(fm, dict), "rollup skill: frontmatter must parse to a mapping",
             errs)
    if isinstance(fm, dict):
        _require(bool(str(fm.get("name", "")).strip()),
                 "rollup skill: frontmatter needs a 'name'", errs)
        _require(bool(str(fm.get("description", "")).strip()),
                 "rollup skill: frontmatter needs a non-empty 'description'", errs)
    low = body.lower()
    # Fans out to all three auditors.
    for auditor in ("usability", "accessibility", "web-performance"):
        _require(auditor in low, f"rollup skill: must fan out to the {auditor} auditor",
                 errs)
    # Wraps the external web-quality-skills suite for a11y + performance.
    _require("web-quality-skills" in low,
             "rollup skill: must wrap the web-quality-skills suite", errs)
    # Normalizes into the shared contract.
    _require("report-contract" in low or "shared contract" in low,
             "rollup skill: must normalize into the shared report contract", errs)
    _require("normaliz" in low or "map" in low,
             "rollup skill: must map external findings to the 0-4 severity scale", errs)
    _require(".ux/audits" in low,
             "rollup skill: must write into .ux/audits", errs)
    # Resilience: skip missing auditors, disclosed honestly.
    _require(("skip" in low or "not installed" in low or "unavailable" in low)
             and "note" in low,
             "rollup skill: must skip unavailable auditors and disclose it", errs)
    # Produces a combined roll-up / verdict.
    _require("roll-up" in low or "rollup" in low or "go/no-go" in low or "verdict" in low,
             "rollup skill: must produce a combined roll-up / verdict", errs)
    # Safety boundary restated.
    _require("never" in low and "outside" in low,
             "rollup skill: must forbid writing outside .ux/audits", errs)
    return errs


def check_rollup_command() -> list[str]:
    errs: list[str] = []
    path = ROOT / "commands" / "ux-audit.md"
    if not path.exists():
        return [f"missing {path.relative_to(ROOT)}"]
    fm, body = _frontmatter(path)
    _require(isinstance(fm, dict), "rollup command: frontmatter must parse to a mapping",
             errs)
    if isinstance(fm, dict):
        _require(bool(str(fm.get("name", "")).strip()),
                 "rollup command: frontmatter needs a 'name'", errs)
        _require(bool(str(fm.get("description", "")).strip()),
                 "rollup command: frontmatter needs a non-empty 'description'", errs)
    low = body.lower()
    _require("ux-audit" in low, "rollup command: must invoke the ux-audit skill", errs)
    for arg in ("target", "scope", "only"):
        _require(arg in low, f"rollup command: must document the {arg!r} argument", errs)
    return errs


def check_cuj_author_persona() -> list[str]:
    """The interviewer persona. Its value is REFUSAL, so that is what we assert.

    Everything this persona rejects is a thing the validator structurally cannot: an
    unobservable `expect` ("it works") parses as a perfectly good string, and "the user"
    is a valid actor as far as YAML is concerned. If these refusals drift out of the
    prose, nothing else in the system catches it.
    """
    errs: list[str] = []
    path = ROOT / "agents" / "cuj-author.md"
    if not path.exists():
        return [f"missing {path.relative_to(ROOT)}"]
    fm, body = _frontmatter(path)
    _require(isinstance(fm, dict), "cuj-author: frontmatter must parse to a mapping", errs)
    if isinstance(fm, dict):
        _require(fm.get("name") == "cuj-author",
                 "cuj-author: frontmatter 'name' must be 'cuj-author'", errs)
        desc = str(fm.get("description", "")).lower()
        _require(bool(desc.strip()),
                 "cuj-author: frontmatter needs a non-empty 'description'", errs)
        _require("journey" in desc or "cuj" in desc,
                 "cuj-author: description should carry a trigger phrase (journey / CUJ)",
                 errs)
    low = body.lower()
    _require("interview" in low, "cuj-author: must describe interviewing the user", errs)
    _require(".ux/cujs" in low, "cuj-author: must state where journeys are written", errs)
    _require("cuj-contract" in low,
             "cuj-author: must point at the CUJ file contract", errs)
    # The refusals — each one is a rule the validator cannot enforce.
    _require("observable" in low,
             "cuj-author: must demand an observable expected outcome per step", errs)
    _require("the user" in low and "actor" in low,
             "cuj-author: must reject \"the user\" and demand a specific actor", errs)
    # Checkpoint E: `"criticality" in low` was the original check here. It passed green
    # while the persona folded completely on criticality — the word was present, the rule
    # was not. Assert the mechanism instead: the rating is EARNED from what breaks.
    _require("criticality" in low and "earn" in low,
             "cuj-author: criticality must be earned from what breaks, not asserted", errs)
    _require("never invent" in low or "fabricat" in low,
             "cuj-author: must never invent a step the user didn't state", errs)
    # Checkpoint E, the serious one: asked to defend a rule that was wrong, it invented a
    # supporting fact (a journey that did not exist), credited it to the user, and called
    # the matter settled. Inventing *agreement* is the never-invent rule breaking in the
    # one direction nothing else catches — a fabricated step is at least visible in the
    # file; a fabricated reason lives only in the conversation.
    # NOTE the single term. This was `"manufactur" in low or "invent" in low and
    # "agreement" in low`, which is vacuous twice over: `and` binds tighter than `or`, so
    # it degrades to ("invent" and "agreement") — and both words appear all over this
    # persona for unrelated reasons. Excising the rule left the check green. Every
    # vacuous check in this build came from the same instinct: a broad fallback term in a
    # disjunction. If a rewrite renames this rule, fail loudly and update the check on
    # purpose.
    _require("manufactur" in low,
             "cuj-author: must never manufacture a justification for the user's answer",
             errs)
    # Checkpoint E: interview-me's house style leads with a confident hypothesis and
    # invites confirmation. That laundered a FALSE step (a click on an autofocused input)
    # into a critical journey — invention with consent on it is still invention.
    _require("guess" in low,
             "cuj-author: must refuse to offer leading guesses the user can confirm", errs)
    # ...and the fix for that must not overshoot into deriving expects FROM the source,
    # which would make the journey test the app against itself and never fail.
    _require("never supplies" in low or "never generate" in low,
             "cuj-author: source may CHECK a recalled detail but never supply the expect",
             errs)
    # Checkpoint E: "captured on a previous day" is unsatisfiable through the UI, so the
    # journey reports 'skipped' forever — and never running looks nothing like failing.
    _require("establish" in low,
             "cuj-author: must reject preconditions nobody can establish", errs)
    # Checkpoint E re-run: establishable ONCE isn't enough. "Nothing harvested today" is
    # true on run 1 and false forever after, so run 2 fails a HEALTHY app — the mirror of
    # every other failure guarded against here, and just as corrosive: a check that cries
    # wolf gets muted, and a muted check is a deleted one.
    _require("twice in a row" in low or "re-establish" in low,
             "cuj-author: must reject preconditions that expire between runs", errs)
    # Checkpoint E re-run, the worst moment: it offered to `cp` validate_cuj.py into the
    # user's .ux/ to dodge a permission prompt, and recommended it as the cleaner path —
    # the suite's own no-litter promise arguing against itself.
    _require("route around" in low,
             "cuj-author: must never route around a permission gate or copy tooling into "
             "the host repo", errs)
    # Checkpoint E re-run: it labelled a turn "Question 4 of ~7" and then asked four
    # things. "One question at a time" has to be countable or it is decoration.
    _require("one `?`" in low,
             "cuj-author: 'one question at a time' must be stated countably (one '?')",
             errs)
    # Boundary: the host's SPEC.md is ask-first, and host code is off limits entirely.
    _require(_asks_first(low) and "spec.md" in low,
             "cuj-author: must ask before writing the host's SPEC.md", errs)
    _require("never" in low and ("edit" in low or "modif" in low) and "host" in low,
             "cuj-author: must state the never-edit-host-code boundary", errs)
    return errs


def check_cuj_auditor_persona() -> list[str]:
    """The verifier persona — the INVERSE of usability-auditor.

    usability-auditor holds four frameworks and an opinion about good design. This one
    holds neither: the host's journey file is the entire rubric, and the only question is
    whether the app did what the file says. So the checks here assert the absence of
    judgement as much as the presence of process — an auditor that starts editorialising
    about the design has stopped verifying and started auditing, which is a different
    persona's job.
    """
    errs: list[str] = []
    path = ROOT / "agents" / "cuj-auditor.md"
    if not path.exists():
        return [f"missing {path.relative_to(ROOT)}"]
    fm, body = _frontmatter(path)
    _require(isinstance(fm, dict), "cuj-auditor: frontmatter must parse to a mapping", errs)
    if isinstance(fm, dict):
        _require(fm.get("name") == "cuj-auditor",
                 "cuj-auditor: frontmatter 'name' must be 'cuj-auditor'", errs)
        desc = str(fm.get("description", "")).lower()
        _require(bool(desc.strip()),
                 "cuj-auditor: frontmatter needs a non-empty 'description'", errs)
        _require("journey" in desc or "cuj" in desc,
                 "cuj-auditor: description should carry a trigger phrase (journey / CUJ)",
                 errs)
    low = body.lower()
    _require(".ux/audits" in low, "cuj-auditor: must state where reports are written", errs)
    _require("cuj-contract" in low, "cuj-auditor: must point at the CUJ file contract", errs)
    # The point of view, stated as a negative. This is the whole persona: the journey is
    # the rubric, so an opinion about the design is out of scope by construction.
    _require("no heuristics" in low,
             "cuj-auditor: must state that it holds no heuristics", errs)
    _require("do not evaluate the design" in low,
             "cuj-auditor: must state that it executes the contract, not judges the design",
             errs)
    # The two-stage severity mapping (SPEC §9.4). `"criticality" in low` is the exact
    # check that went green through a total behavioural failure in Checkpoint E — the word
    # proves nothing. Assert the MECHANISM: classify first, then clamp by the journey's
    # own rating.
    _require("clamp" in low,
             "cuj-auditor: severity must be clamped by the journey's criticality", errs)
    _require("severity" in low and "0" in body and "4" in body,
             "cuj-auditor: must state the 0-4 severity scale", errs)
    # A passing step is severity 0, and severity 0 is a non-finding. If passing steps ever
    # leak into the findings list, `total: 0` stops meaning "passed" and the whole
    # report-shape contract for this auditor collapses.
    _require("appendix" in low,
             "cuj-auditor: passing steps must go in the Appendix", errs)
    _require("never as a finding" in low,
             "cuj-auditor: a passing step is sev0 and must never be emitted as a finding",
             errs)
    # `total: 0` is this auditor's SUCCESS state — unique in the suite. The counts are the
    # only thing distinguishing it from a run that checked nothing.
    _require("total: 0" in low,
             "cuj-auditor: must state that a passing journey is total: 0", errs)
    _require("denominator" in low,
             "cuj-auditor: must state that N counts journeys selected, not journeys run",
             errs)
    # The violation citation format: reports are useless if they don't name the step.
    _require("step" in low and "cuj-001" in low,
             "cuj-auditor: must show the '<CUJ-id> ... step <n>' violation format", errs)
    # Render-vs-source honesty, inherited from the suite (report contract §6).
    _require("potential — unverified" in low,
             "cuj-auditor: must label static-mode findings 'potential — unverified'", errs)
    # Findings-only. For THIS auditor the tempting edit isn't host code — it's the journey
    # file that just failed. Softening a journey to match what the app does is grading your
    # own homework, and it is the one maker/checker collision v2 can actually suffer.
    _require("never" in low and ("edit" in low or "modif" in low) and "host" in low,
             "cuj-auditor: must state the never-edit-host-code boundary", errs)
    _require(".ux/cujs" in low,
             "cuj-auditor: must state that it never repairs the journey it is grading",
             errs)
    return errs


def check_spec_cuj_skill() -> list[str]:
    """The authoring workflow: interview -> write -> validate -> ask -> splice."""
    errs: list[str] = []
    path = ROOT / "skills" / "spec-cuj" / "SKILL.md"
    if not path.exists():
        return [f"missing {path.relative_to(ROOT)}"]
    fm, body = _frontmatter(path)
    _require(isinstance(fm, dict), "spec-cuj: frontmatter must parse to a mapping", errs)
    if isinstance(fm, dict):
        _require(fm.get("name") == "spec-cuj",
                 "spec-cuj: frontmatter 'name' must match the directory ('spec-cuj')",
                 errs)
        _require(bool(str(fm.get("description", "")).strip()),
                 "spec-cuj: frontmatter needs a non-empty 'description'", errs)
    low = body.lower()
    _require(".ux/cujs" in low, "spec-cuj: must write journeys to .ux/cujs", errs)
    _require("cuj-contract" in low, "spec-cuj: must reference the CUJ file contract", errs)
    _require("cuj-author" in low, "spec-cuj: must invoke the cuj-author persona", errs)
    # The interview, and its graceful degradation.
    _require("interview-me" in low,
             "spec-cuj: must drive agent-skills:interview-me when available", errs)
    _require("fallback" in low or "not installed" in low,
             "spec-cuj: must fall back when interview-me is unavailable", errs)
    _require("disclos" in low or "say so" in low or "tell the user" in low,
             "spec-cuj: must disclose when it fell back (never a silent degrade)", errs)
    _require("offer" in low and "install" in low,
             "spec-cuj: must offer to install interview-me, never auto-install", errs)
    # The index splice — the one place it touches a file the user owns.
    # Checkpoint E: interview-me doesn't know this schema and will finish without ever
    # asking entry_point or criticality — and an unasked field silently becomes an
    # invented one. The skill owns the gap, whichever interview is driving.
    _require("guess" in low,
             "spec-cuj: must forbid leading guesses (interview-me's style conflicts "
             "with never-invent)", errs)
    _require("establish" in low,
             "spec-cuj: must self-check that preconditions are establishable", errs)
    _require("twice in a row" in low,
             "spec-cuj: must self-check that preconditions survive a second run", errs)
    _require("route around" in low,
             "spec-cuj: must never route around a permission gate or copy tooling into "
             "the host repo", errs)
    _require("validate_cuj" in low,
             "spec-cuj: must self-check its output with validate_cuj.py", errs)
    _require("--index" in low,
             "spec-cuj: must GENERATE the index block, not write the table by hand", errs)
    _require("marker" in low,
             "spec-cuj: must only replace bytes between the index markers", errs)
    _require(_asks_first(low) and "spec.md" in low,
             "spec-cuj: must ask before writing the host's SPEC.md", errs)
    _require("diff" in low,
             "spec-cuj: must show the diff before splicing the host's SPEC.md", errs)
    _require("declin" in low or "if they say no" in low,
             "spec-cuj: must handle a declined SPEC.md write (journeys stand alone)",
             errs)
    # Safety.
    _require("audit_safety" in low and "authoring" in low,
             "spec-cuj: must confirm its footprint with the authoring safety profile",
             errs)
    _require("never" in low and ("edit" in low or "modif" in low) and "host" in low,
             "spec-cuj: must state the never-edit-host-code boundary", errs)
    _require("exit" in low or "done when" in low or "acceptance" in low,
             "spec-cuj: must state explicit exit criteria", errs)
    return errs


def check_audit_cuj_skill() -> list[str]:
    """The verification workflow: select -> validate -> establish -> replay -> grade.

    Most of these guard ONE failure mode with many faces: a verifier that reports success
    without having verified anything. `total: 0` is this auditor's success state, so an
    all-skipped run is byte-identical to a clean pass and valid against the shared report
    contract — no validator can catch it, which leaves this prose as the only guard.
    """
    errs: list[str] = []
    path = ROOT / "skills" / "audit-cuj" / "SKILL.md"
    if not path.exists():
        return [f"missing {path.relative_to(ROOT)}"]
    fm, body = _frontmatter(path)
    _require(isinstance(fm, dict), "audit-cuj: frontmatter must parse to a mapping", errs)
    if isinstance(fm, dict):
        _require(fm.get("name") == "audit-cuj",
                 "audit-cuj: frontmatter 'name' must match the directory ('audit-cuj')",
                 errs)
        _require(bool(str(fm.get("description", "")).strip()),
                 "audit-cuj: frontmatter needs a non-empty 'description'", errs)
    low = body.lower()
    _require(".ux/cujs" in low, "audit-cuj: must read journeys from .ux/cujs", errs)
    _require(".ux/audits" in low, "audit-cuj: must write its report to .ux/audits", errs)
    _require("cuj-contract" in low, "audit-cuj: must reference the CUJ file contract", errs)
    _require("cuj-auditor" in low, "audit-cuj: must invoke the cuj-auditor persona", errs)
    _require("validate_cuj" in low,
             "audit-cuj: must validate a journey before walking it", errs)

    # --- The empty sets. All three are vacuous-pass routes; v1 shipped the first one. ---
    # Zero journeys: "all journeys passed" is trivially true against no journeys.
    _require("no cujs authored" in low,
             "audit-cuj: absent/empty .ux/cujs must stop and say so, never an empty pass",
             errs)
    # Zero steps observed: total: 0 + everything skipped == a clean pass, structurally.
    _require("denominator" in low,
             "audit-cuj: N must count journeys selected, not journeys run", errs)
    _require("total: 0" in low,
             "audit-cuj: must state that total: 0 is the SUCCESS state for this auditor",
             errs)
    # The vacuous absence criterion — v1's empty-set trap wearing v2's clothes. A criterion
    # like "'Buy milk' is absent after reload" passes when the app is broken, unless the
    # baseline proved 'Buy milk' was there to begin with.
    _require("vacuously true" in low,
             "audit-cuj: an absence criterion needs a non-empty baseline to be falsifiable",
             errs)

    # --- The precondition ladder (the question Phase 9 inherited). ---
    _require("precondition ladder" in low,
             "audit-cuj: must define the ordered precondition ladder", errs)
    _require("observe before establishing" in low,
             "audit-cuj: L0 — must observe the baseline before establishing state", errs)
    _require("setup journey" in low,
             "audit-cuj: L1 — must allow replaying another CUJ to establish state", errs)
    # The anti-laundering gate, and the highest-value check in this file. A setup journey
    # whose STEPS passed but whose success_criteria failed has not established anything —
    # it has proved the app is broken. Without this clause, CUJ-001's silent-data-loss bug
    # establishes CUJ-002's precondition and CUJ-002 passes BECAUSE the app is broken.
    _require("passed its own success_criteria" in low,
             "audit-cuj: a setup journey establishes a precondition ONLY if it passed its "
             "own success_criteria", errs)
    _require("rung" in low,
             "audit-cuj: the Appendix must record which ladder rungs were attempted", errs)
    # The hard stop. Injected state is state no user can reach, so a journey verified
    # against it proves nothing — this is a correctness rule, not only a safety one.
    _require("evaluate_script" in low,
             "audit-cuj: must forbid injecting state the UI cannot reach", errs)
    # The no-alibi rule — this is what saves Checkpoint F. CUJ-001's precondition ("at
    # least one existing task") is reachable only via the add-task flow CUJ-001 exists to
    # test. Naive ladder => breaking add-task makes CUJ-001 SKIP and the sev4 vanishes,
    # failing SPEC §9.8's detection criterion exactly when it matters most.
    _require("no-alibi" in low,
             "audit-cuj: a precondition failure must never alibi the journey it belongs to",
             errs)
    _require("self-referential" in low,
             "audit-cuj: a self-referential precondition must be graded from a bare "
             "entry_point, not skipped", errs)

    # --- Skips: honest, counted, and never a finding. ---
    _require("precondition unmet" in low,
             "audit-cuj: must report an unestablishable precondition as skipped", errs)
    _require("a skip is not a finding" in low,
             "audit-cuj: a skip carries no severity — it is not a sev4", errs)
    _require("do not open a second finding" in low,
             "audit-cuj: a cascade must not double-count one bug as two findings", errs)
    _require("also blocks" in low,
             "audit-cuj: the blocker's finding must carry the cascade's blast radius", errs)

    # --- Grading and report shape. ---
    _require("clamp" in low,
             "audit-cuj: severity must be clamped by the journey's criticality", errs)
    _require("verbatim" in low,
             "audit-cuj: must grade against the verbatim expect, never a paraphrase", errs)
    _require("one report per run" in low,
             "audit-cuj: one report per run keeps index.md rows 1:1 with runs", errs)
    _require("success_criteria" in low,
             "audit-cuj: must evaluate success_criteria after the steps complete", errs)
    # Static mode cannot produce a verified pass — the render-vs-source rule in frontmatter.
    _require("potential — unverified" in low,
             "audit-cuj: static findings must be labelled 'potential — unverified'", errs)
    _require("task-completion" in low,
             "audit-cuj: must state when task-completion is claimable (live/hybrid only)",
             errs)
    for mode in ("static", "live", "hybrid"):
        _require(mode in low, f"audit-cuj: must handle {mode} mode", errs)

    # --- Boundaries. ---
    _require("audit_safety" in low,
             "audit-cuj: must confirm its footprint with the default audit profile", errs)
    _require("never" in low and ("edit" in low or "modif" in low) and "host" in low,
             "audit-cuj: must state the never-edit-host-code boundary", errs)
    _require("route around" in low,
             "audit-cuj: must never route around a permission gate or copy tooling into "
             "the host repo", errs)
    _require("exit" in low or "done when" in low or "acceptance" in low,
             "audit-cuj: must state explicit exit criteria", errs)
    return errs


def check_ux_spec_command() -> list[str]:
    errs: list[str] = []
    path = ROOT / "commands" / "ux-spec.md"
    if not path.exists():
        return [f"missing {path.relative_to(ROOT)}"]
    fm, body = _frontmatter(path)
    _require(isinstance(fm, dict), "ux-spec command: frontmatter must parse to a mapping",
             errs)
    if isinstance(fm, dict):
        _require(fm.get("name") == "ux-spec",
                 "ux-spec command: frontmatter 'name' must be 'ux-spec'", errs)
        _require(bool(str(fm.get("description", "")).strip()),
                 "ux-spec command: frontmatter needs a non-empty 'description'", errs)
        _require(bool(str(fm.get("argument-hint", "")).strip()),
                 "ux-spec command: frontmatter needs an 'argument-hint'", errs)
    low = body.lower()
    _require("spec-cuj" in low, "ux-spec command: must invoke the spec-cuj skill", errs)
    _require("cuj-author" in low, "ux-spec command: must invoke the cuj-author persona",
             errs)
    _require("--cuj" in low, "ux-spec command: must document the '--cuj' argument", errs)
    _require(".ux/cujs" in low, "ux-spec command: must say where journeys are written",
             errs)
    # This is the one command in the suite that writes outside .ux/ — its entry point
    # should say so, rather than surprising the user once the interview is over.
    _require(_asks_first(low) and "spec.md" in low,
             "ux-spec command: must state that the host's SPEC.md write is ask-first",
             errs)
    return errs


def check_audit_cuj_command() -> list[str]:
    errs: list[str] = []
    path = ROOT / "commands" / "audit-cuj.md"
    if not path.exists():
        return [f"missing {path.relative_to(ROOT)}"]
    fm, body = _frontmatter(path)
    _require(isinstance(fm, dict),
             "audit-cuj command: frontmatter must parse to a mapping", errs)
    if isinstance(fm, dict):
        _require(fm.get("name") == "audit-cuj",
                 "audit-cuj command: frontmatter 'name' must be 'audit-cuj'", errs)
        _require(bool(str(fm.get("description", "")).strip()),
                 "audit-cuj command: frontmatter needs a non-empty 'description'", errs)
        _require(bool(str(fm.get("argument-hint", "")).strip()),
                 "audit-cuj command: frontmatter needs an 'argument-hint'", errs)
    low = body.lower()
    _require("audit-cuj" in low, "audit-cuj command: must invoke the audit-cuj skill", errs)
    _require("cuj-auditor" in low,
             "audit-cuj command: must invoke the cuj-auditor persona", errs)
    for arg in ("target", "--cuj", "--mode"):
        _require(arg in low, f"audit-cuj command: must document the {arg!r} argument", errs)
    for val in ("critical", "static", "live", "hybrid"):
        _require(val in low, f"audit-cuj command: must document the {val!r} value", errs)
    _require(".ux/cujs" in low,
             "audit-cuj command: must say where journeys are read from", errs)
    _require(".ux/audits" in low,
             "audit-cuj command: must say where the report is written", errs)
    # The entry point should state the guarantee that distinguishes this auditor: an empty
    # .ux/cujs stops the run. A user who sees a clean report from a repo with no journeys
    # would reasonably read it as a pass.
    _require("no cujs authored" in low,
             "audit-cuj command: must state that an empty .ux/cujs stops rather than passes",
             errs)
    return errs


def check_cuj_references() -> list[str]:
    """spec-cuj's skill-local references must exist and carry their defining terms."""
    errs: list[str] = []
    refs = ROOT / "skills" / "spec-cuj" / "references"
    expected = {
        "cuj-contract.md": ["actor", "precondition", "step", "expect", "success_criteria",
                            "criticality", "observable"],
        "interview-fallback.md": ["actor", "goal", "out of scope", "criticality",
                                  "observable"],
    }
    for fname, terms in expected.items():
        path = refs / fname
        if not path.exists():
            errs.append(f"missing reference: skills/spec-cuj/references/{fname}")
            continue
        low = path.read_text(encoding="utf-8").lower()
        for term in terms:
            _require(term in low, f"{fname}: must cover {term!r}", errs)
    return errs


def check_references() -> list[str]:
    """The skill-local framework lenses must exist and carry their defining terms."""
    errs: list[str] = []
    refs = ROOT / "skills" / "usability-audit" / "references"
    expected = {
        "shneiderman-8.md": ["consistency", "informative feedback", "closure",
                              "reversal", "locus of control", "memory load"],
        "ai-design-heuristics.md": ["expectation", "explain", "correct"],
        "npcis.md": ["navigation", "presentation", "content", "interaction", "strategy"],
    }
    for fname, terms in expected.items():
        path = refs / fname
        if not path.exists():
            errs.append(f"missing reference: skills/usability-audit/references/{fname}")
            continue
        low = path.read_text(encoding="utf-8").lower()
        for term in terms:
            _require(term in low, f"{fname}: must cover {term!r}", errs)
    return errs


# Hand-maintained ON PURPOSE, and this is the suite's sharpest edge: nothing globs these.
# A component whose check isn't listed here is a component nothing verifies, and the suite
# stays green while it goes unchecked — the quiet failure AGENTS.md calls the silent trap.
# Adding a component means adding its check HERE, in the same commit.
CHECKS = (
    check_persona, check_skill, check_command, check_references,
    check_rollup_skill, check_rollup_command,
    check_cuj_author_persona, check_spec_cuj_skill, check_ux_spec_command,
    check_cuj_references,
    check_cuj_auditor_persona, check_audit_cuj_skill, check_audit_cuj_command,
)


def main() -> int:
    failures = [err for check in CHECKS for err in check()]
    if failures:
        print("FAIL — components:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"PASS — components ({len(CHECKS)} checks: personas, skills, commands, "
          f"references, roll-up)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
