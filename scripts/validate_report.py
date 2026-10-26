#!/usr/bin/env python3
"""Validate a `.ux/audits` report against the shared report contract.

Encodes the machine-checkable invariants documented in
`skills/usability-audit/references/report-contract.md`. Reused by the audit skill
to self-check its output before finalizing a report, and by the contract test suite.

Usage:
    python3 scripts/validate_report.py <report.md> [<report.md> ...]

Exit code 0 = all valid; 1 = at least one report has errors (printed to stderr).
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

import yaml

REQUIRED_KEYS = ["auditor", "schema", "version", "date", "target", "mode", "scope",
                 "frameworks", "summary", "health"]
KNOWN_MODES = {"live", "static", "hybrid"}

# Framework vocabulary is PER-AUDITOR — the contract is auditor-agnostic, so each suite
# member declares its own set. An auditor absent from this map (a new suite member) is
# accepted as long as its frameworks are non-empty strings, keeping the contract
# forward-compatible; known auditors are checked against their vocabulary.
FRAMEWORKS_BY_AUDITOR = {
    "usability": {"nielsen-10", "shneiderman-8", "ai-heuristics", "npcis"},
    "accessibility": {"wcag-2.2", "wcag-2.1", "aria"},
    "web-performance": {"core-web-vitals", "lighthouse", "rail"},
    # `cuj` is the odd one out: the others cite external standards, but CUJ verification
    # has none — the host's own journey files ARE the standard. So these name which lens
    # the run could actually apply, which makes the list a machine-readable statement of
    # how much it proved: a static run honestly emits `cuj-contract` alone, because it
    # traced source without completing the task or observing persistence.
    "cuj": {"cuj-contract", "task-completion", "success-criteria"},
}
# Schema 3: P0-P3 replaces sev4-sev1. The tag says what to DO, not just how bad it is.
PRIORITY_KEYS = ["p0", "p1", "p2", "p3"]
PRIORITY_ACTION = {"p0": "fix immediately", "p1": "fix before release",
                   "p2": "fix in the next pass", "p3": "fix if time allows"}
# Band thresholds for `health.pct` (contract §4.1), highest floor first.
BANDS = [(90, "Excellent"), (70, "Good"), (50, "Acceptable"), (30, "Poor"), (0, "Critical")]
# A run with nothing gradable is "Unscored" — never 0% (reads catastrophic) and never
# 100% (reads like a clean pass). See `_check_health`.
UNSCORED = "Unscored"


def band_for(pct: int) -> str:
    """The band a health percentage falls into."""
    return next(name for floor, name in BANDS if pct >= floor)

# --- roll-up vocabulary (contract §9) ----------------------------------------------------

# A suite roll-up is a sibling document type, not an auditor report: it has no single
# `auditor`, `mode`, or `frameworks`, so it validates through its own path.
ROLLUP_REQUIRED_KEYS = ["kind", "schema", "version", "date", "target", "scope", "verdict",
                        "verdict_reason", "auditors_ran", "auditors_skipped", "summary",
                        "health"]
ROLLUP_VERDICTS = {"GO", "NO-GO"}


def is_rollup(fm: dict) -> bool:
    """True when this frontmatter describes a suite roll-up rather than an auditor report.

    The contract (§9) specifies `kind: rollup`. Two other spellings are *read* because
    reports are append-only historical records and roll-ups predating §9 must keep
    rendering: `report: rollup`, and the `rollup: true` the HTML renderer originally
    looked for. Writing either is still a contract violation — `validate_rollup` rejects
    them. Tolerated on read, never blessed on write.
    """
    if fm.get("rollup"):
        return True
    return any(str(fm.get(k, "")).strip().lower() == "rollup" for k in ("kind", "report"))


def derive_verdict(summary: dict) -> str:
    """The go/no-go gate, as a function of the counts rather than a judgment call.

    Any P0 (fix immediately) or P1 (fix before release) blocks; everything else ships.
    The gate reads straight off the rubric rather than reinterpreting it.
    This is deliberately total and mechanical: five runs of the same app produced five
    different verdicts from the same facts — two of them opposite on identical counts —
    because the gate lived in prose ("any auditor reports a sev3 blocker") and left the
    auditor to decide what counted as a blocker. A derived verdict cannot drift.
    """
    return "NO-GO" if (summary.get("p0") or summary.get("p1")) else "GO"

# A finding is a level-3 heading tagged with its priority, e.g. "### [P1] Foo".
FINDING_RE = re.compile(r"^###\s+\[P([0-3])\]", re.MULTILINE)
# Tags from the superseded schema-2 scale, and out-of-range P-levels. Detected so a stale
# report fails with "this is the old scale" rather than a baffling count mismatch.
LEGACY_TAG_RE = re.compile(r"^###\s+\[(sev\d|P[4-9]|P\d\d+)\]", re.MULTILINE | re.IGNORECASE)
# The optional `## Walkthrough` section (§5) and the markdown images inside it.
WALKTHROUGH_RE = re.compile(r"^##\s+Walkthrough\s*$", re.MULTILINE | re.IGNORECASE)
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
# The five labelled fields every finding block must contain.
FINDING_FIELDS = ["Issue Description", "Framework Violation", "Priority",
                  "Evidence", "Recommended Fix"]


def _split_frontmatter(text: str) -> tuple[dict, str] | tuple[None, str]:
    """Return (frontmatter_dict, body) or (None, error_message)."""
    if not text.startswith("---"):
        return None, "missing YAML frontmatter (file must start with '---')"
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, "unterminated YAML frontmatter (needs a closing '---')"
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        return None, f"frontmatter is not valid YAML: {exc}"
    if not isinstance(fm, dict):
        return None, "frontmatter did not parse to a mapping"
    return fm, parts[2]


def _check_frontmatter(fm: dict) -> list[str]:
    errors: list[str] = []

    for key in REQUIRED_KEYS:
        if key not in fm:
            errors.append(f"frontmatter missing required key: {key!r}")

    if fm.get("schema") != 3:
        errors.append("frontmatter 'schema' must equal 3")

    mode = fm.get("mode")
    if mode not in KNOWN_MODES:
        errors.append(f"frontmatter 'mode' must be one of {sorted(KNOWN_MODES)}, got {mode!r}")

    date = fm.get("date")
    if isinstance(date, datetime):
        pass  # PyYAML parsed an ISO timestamp — fine.
    elif isinstance(date, str):
        try:
            datetime.fromisoformat(date.replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"frontmatter 'date' is not ISO-8601: {date!r}")
    else:
        errors.append("frontmatter 'date' must be an ISO-8601 string")

    for field in ("auditor", "target", "scope"):
        if field in fm and not (isinstance(fm[field], str) and fm[field].strip()):
            errors.append(f"frontmatter {field!r} must be a non-empty string")

    frameworks = fm.get("frameworks")
    if not isinstance(frameworks, list) or not frameworks:
        errors.append("frontmatter 'frameworks' must be a non-empty list")
    else:
        vocab = FRAMEWORKS_BY_AUDITOR.get(fm.get("auditor"))
        if vocab is not None:
            unknown = [f for f in frameworks if f not in vocab]
            if unknown:
                errors.append(
                    f"frontmatter 'frameworks' has entries unknown to auditor "
                    f"{fm.get('auditor')!r}: {unknown}")
        elif any(not (isinstance(f, str) and f.strip()) for f in frameworks):
            # Unknown auditor: no vocabulary to check against, but entries must be
            # non-empty strings.
            errors.append("frontmatter 'frameworks' entries must be non-empty strings")

    return errors


def _check_summary(fm: dict, body: str) -> list[str]:
    errors: list[str] = []
    summary = fm.get("summary")
    if not isinstance(summary, dict):
        errors.append("frontmatter 'summary' must be a mapping")
        return errors

    stale = [k for k in summary if re.fullmatch(r"sev\d", str(k), re.IGNORECASE)]
    if stale:
        errors.append(
            f"summary uses the superseded severity scale {sorted(stale)}; schema 3 counts "
            f"are {PRIORITY_KEYS} (sev4->p0, sev3->p1, sev2->p2, sev1->p3)")

    for key in ["total"] + PRIORITY_KEYS:
        if key not in summary:
            errors.append(f"summary missing required key: {key!r}")
        elif not isinstance(summary[key], int) or summary[key] < 0:
            errors.append(f"summary {key!r} must be a non-negative integer")

    # A tag outside P0-P3 is reported for what it is, not as a count mismatch.
    for tag in sorted(set(LEGACY_TAG_RE.findall(body))):
        errors.append(
            f"body contains a [{tag}] finding; schema 3 tags findings P0-P3 (§4)")

    if all(isinstance(summary.get(k), int) for k in ["total"] + PRIORITY_KEYS):
        by_pri = sum(summary[k] for k in PRIORITY_KEYS)
        if summary["total"] != by_pri:
            errors.append(
                f"summary 'total' ({summary['total']}) != sum of p0-p3 ({by_pri})")

        # Findings in the body must match the declared counts.
        found = FINDING_RE.findall(body)
        if len(found) != summary["total"]:
            errors.append(
                f"summary 'total' ({summary['total']}) != findings in body ({len(found)})")
        for key in PRIORITY_KEYS:
            n = sum(1 for level in found if level == key[-1])
            if n != summary[key]:
                errors.append(
                    f"summary {key!r} ({summary[key]}) != [{key.upper()}] findings in "
                    f"body ({n})")

    return errors


def _check_health(fm: dict) -> list[str]:
    """Validate the `health` scorecard (contract §4.1) against its own items.

    `score`, `max`, `pct` and `band` are all DERIVED. Checking them against `items` is the
    whole point: a headline number nobody can reconcile with its rows is exactly the kind
    of unfalsifiable claim this suite exists to avoid.
    """
    errors: list[str] = []
    health = fm.get("health")
    if not isinstance(health, dict):
        if "health" in fm:
            errors.append("frontmatter 'health' must be a mapping")
        return errors

    items = health.get("items")
    if not isinstance(items, list) or not items:
        errors.append("health 'items' must be a non-empty list")
        return errors

    rubric = health.get("rubric")
    frameworks = fm.get("frameworks") or []
    if not (isinstance(rubric, str) and rubric.strip()):
        errors.append("health 'rubric' must be a non-empty string")
    elif isinstance(frameworks, list) and rubric not in frameworks:
        errors.append(
            f"health 'rubric' ({rubric!r}) is not in 'frameworks' {frameworks}; the "
            f"scorecard cannot cite a lens the run did not apply")

    score = maximum = 0
    for idx, item in enumerate(items):
        where = f"health item {idx}"
        if not isinstance(item, dict) or not str(item.get("item", "")).strip():
            errors.append(f"{where} must be a mapping with a non-empty 'item'")
            continue
        where = f"health item {item['item']!r}"
        of = item.get("of", 4)
        if not isinstance(of, int) or of <= 0:
            errors.append(f"{where}: 'of' must be a positive integer")
            continue
        got = item.get("score", "missing")
        note = str(item.get("note", "")).strip()
        if got is None:                       # not applicable
            if not note:
                errors.append(f"{where}: an n/a item must carry a 'note' saying why")
            continue
        if not isinstance(got, int) or not 0 <= got <= of:
            errors.append(f"{where}: 'score' must be null or an integer in 0..{of}")
            continue
        # A weak score is an assertion until it says what it is based on.
        if got * 2 <= of and not note:
            errors.append(
                f"{where}: scored {got}/{of} and must carry a 'note' — an unexplained low "
                f"score is an assertion, not a finding")
        score += got
        maximum += of

    if maximum == 0:
        # Every item n/a: the run inspected nothing it could grade. That is a real state —
        # a static or all-skipped run — and it must be sayable WITHOUT inventing a number.
        # 0% would read as catastrophic and 100% as a clean pass; both are lies. The honest
        # record is an explicit "unscored", which the roll-up can then refuse to average in.
        for key, want in (("score", 0), ("max", 0), ("pct", None), ("band", "Unscored")):
            if health.get(key) != want:
                errors.append(
                    f"health has no applicable items, so {key!r} must be {want!r} "
                    f"(got {health.get(key)!r}) — an unscored run says so rather than "
                    f"reporting a percentage it did not earn")
        return errors

    if health.get("band") == "Unscored" or health.get("pct") is None:
        errors.append(
            f"health is marked unscored but {maximum // 1} point(s) were applicable; "
            f"'Unscored' is only for a run with no gradable item")
        return errors

    pct = round(100 * score / maximum)
    for key, want in (("score", score), ("max", maximum), ("pct", pct)):
        if health.get(key) != want:
            errors.append(
                f"health {key!r} is {health.get(key)!r} but its items derive {want}")
    if health.get("band") != band_for(pct):
        errors.append(
            f"health 'band' is {health.get('band')!r} but {pct}% is {band_for(pct)!r}")
    return errors


def _check_finding_fields(body: str) -> list[str]:
    """Each finding block must carry the five labelled fields."""
    errors: list[str] = []
    matches = list(FINDING_RE.finditer(body))
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        block = body[start:end]
        heading = body[start:body.index("\n", start) if "\n" in body[start:] else end]
        missing = [f for f in FINDING_FIELDS if f not in block]
        if missing:
            errors.append(f"finding {heading.strip()!r} missing fields: {missing}")
    return errors


def _check_coverage(body: str) -> list[str]:
    """The report must own an Appendix that states coverage honestly.

    Coverage honesty is a first-class contract rule: a report that never says what it
    did NOT inspect reads as "covered everything" when it may not have. Require an
    Appendix section and an explicit coverage / not-inspected statement.
    """
    low = body.lower()
    errors: list[str] = []
    if "## appendix" not in low:
        errors.append("report missing the '## Appendix' section (coverage honesty)")
    if "not inspected" not in low and "coverage" not in low:
        errors.append(
            "report appendix must state coverage — what was 'not inspected' / a "
            "'coverage' note; silent gaps are prohibited")
    return errors


def _check_walkthrough(body: str) -> list[str]:
    """Light validation of the optional `## Walkthrough` section (§5).

    The section is optional (live/hybrid only) — its absence is never an error. When
    present, every embedded image path must be relative and under `./assets/`, so the
    walk-through stays inside the auditor's write boundary and renders from the report's
    own directory. This checks the reference shape, not that the file exists on disk.
    """
    m = WALKTHROUGH_RE.search(body)
    if m is None:
        return []
    # Section runs from its heading to the next `## ` heading (or end of body).
    start = m.end()
    nxt = re.search(r"^##\s", body[start:], re.MULTILINE)
    section = body[start:start + nxt.start()] if nxt else body[start:]

    errors: list[str] = []
    for path in (p.strip() for p in IMAGE_RE.findall(section)):
        under_assets = path.startswith("./assets/") or path.startswith("assets/")
        if not under_assets or ".." in path:
            errors.append(
                f"walkthrough image path must be relative and under './assets/': {path!r}")
    return errors


def _check_rollup_frontmatter(fm: dict) -> list[str]:
    """Validate a suite roll-up's frontmatter against contract §9."""
    errors: list[str] = []

    for key in ROLLUP_REQUIRED_KEYS:
        if key not in fm:
            errors.append(f"rollup frontmatter missing required key: {key!r}")

    # The discriminator itself: `kind: rollup` is the spelling. `report:`/`rollup:` still
    # READ as a roll-up (see `is_rollup`) so historical files render, but writing one is a
    # violation — otherwise the drift that broke the dashboard quietly re-accumulates.
    if str(fm.get("kind", "")).strip().lower() != "rollup":
        legacy = [k for k in ("report", "rollup") if fm.get(k)]
        errors.append(
            f"rollup must carry 'kind: rollup'"
            + (f" (found the legacy discriminator {legacy[0]!r} instead)" if legacy else ""))

    if fm.get("schema") != 3:
        errors.append("rollup frontmatter 'schema' must equal 3")

    date = fm.get("date")
    if isinstance(date, datetime):
        pass
    elif isinstance(date, str):
        try:
            datetime.fromisoformat(date.replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"rollup frontmatter 'date' is not ISO-8601: {date!r}")
    else:
        errors.append("rollup frontmatter 'date' must be an ISO-8601 string")

    for field in ("target", "scope", "verdict_reason"):
        if field in fm and not (isinstance(fm[field], str) and fm[field].strip()):
            errors.append(f"rollup frontmatter {field!r} must be a non-empty string")

    # `verdict` is a bare machine-readable token. Prose belongs in `verdict_reason`: the
    # renderer tests this value to colour the go/no-go banner, so "GO — all journeys pass"
    # is not a GO to a machine, and every roll-up written that way rendered as a red NO-GO.
    verdict = fm.get("verdict")
    if verdict is not None:
        token = str(verdict).strip().upper()
        if token not in ROLLUP_VERDICTS:
            hint = ""
            if token.split(" ")[0].split("—")[0].strip() in ROLLUP_VERDICTS:
                hint = " — put the explanation in 'verdict_reason', not here"
            errors.append(
                f"rollup 'verdict' must be one of {sorted(ROLLUP_VERDICTS)}, "
                f"got {str(verdict)!r}{hint}")

    ran = fm.get("auditors_ran")
    if "auditors_ran" in fm and (not isinstance(ran, list) or not ran):
        errors.append("rollup 'auditors_ran' must be a non-empty list")

    # Every skipped auditor carries its reason. The suite's rule is that a skipped auditor
    # must never read as a clean pass; making the reason structural is what enforces it.
    skipped = fm.get("auditors_skipped")
    if "auditors_skipped" in fm:
        if not isinstance(skipped, list):
            errors.append("rollup 'auditors_skipped' must be a list (empty when none)")
        else:
            for entry in skipped:
                if not isinstance(entry, dict) or not str(entry.get("auditor", "")).strip():
                    errors.append(
                        f"rollup 'auditors_skipped' entry must be a mapping with an "
                        f"'auditor' key: {entry!r}")
                elif not str(entry.get("reason", "")).strip():
                    errors.append(
                        f"rollup skipped auditor {entry.get('auditor')!r} has no 'reason'; "
                        f"a silent skip reads as a pass")

    return errors


def _check_rollup_summary(fm: dict) -> list[str]:
    """Counts reconcile, and the verdict follows from them."""
    errors: list[str] = []
    summary = fm.get("summary")
    if not isinstance(summary, dict):
        if "summary" in fm:
            errors.append("rollup 'summary' must be a mapping")
        return errors

    stale = [k for k in summary if re.fullmatch(r"sev\d", str(k), re.IGNORECASE)]
    if stale:
        errors.append(
            f"rollup summary uses the superseded severity scale {sorted(stale)}; "
            f"schema 3 counts are {PRIORITY_KEYS}")

    for key in ["total"] + PRIORITY_KEYS:
        if key not in summary:
            errors.append(f"rollup summary missing required key: {key!r}")
        elif not isinstance(summary[key], int) or summary[key] < 0:
            errors.append(f"rollup summary {key!r} must be a non-negative integer")

    if not all(isinstance(summary.get(k), int) for k in ["total"] + PRIORITY_KEYS):
        return errors

    by_pri = sum(summary[k] for k in PRIORITY_KEYS)
    if summary["total"] != by_pri:
        errors.append(
            f"rollup summary 'total' ({summary['total']}) != sum of p0-p3 ({by_pri})")

    verdict = str(fm.get("verdict", "")).strip().upper()
    if verdict in ROLLUP_VERDICTS:
        expected = derive_verdict(summary)
        if verdict != expected:
            errors.append(
                f"rollup 'verdict' is {verdict!r} but the counts derive {expected!r} "
                f"(p0={summary['p0']}, p1={summary['p1']}); the gate is mechanical")
    return errors


def _check_rollup_health(fm: dict) -> list[str]:
    """The suite scorecard: a mean of its members, and a trend that may be empty.

    `trend` holds PRIOR runs only. It is allowed to be `[]` — an authenticated run is
    advised to gitignore `.ux/audits/` wholesale, so in those repos there is no history to
    read, and an absent trend must degrade to "no prior runs" rather than look broken.
    """
    errors: list[str] = []
    health = fm.get("health")
    if not isinstance(health, dict):
        if "health" in fm:
            errors.append("rollup 'health' must be a mapping")
        return errors

    auditors = health.get("auditors")
    if not isinstance(auditors, list) or not auditors:
        errors.append("rollup health 'auditors' must be a non-empty list")
        auditors = []

    pcts = []
    for entry in auditors:
        if not isinstance(entry, dict) or not str(entry.get("auditor", "")).strip():
            errors.append(f"rollup health auditor entry needs an 'auditor': {entry!r}")
            continue
        pct = entry.get("pct")
        if not isinstance(pct, int) or not 0 <= pct <= 100:
            errors.append(f"rollup health {entry['auditor']!r}: 'pct' must be 0..100")
            continue
        if entry.get("band") != band_for(pct):
            errors.append(
                f"rollup health {entry['auditor']!r}: band is {entry.get('band')!r} but "
                f"{pct}% is {band_for(pct)!r}")
        pcts.append(pct)

    if pcts:
        want = round(sum(pcts) / len(pcts))
        if health.get("pct") != want:
            errors.append(
                f"rollup health 'pct' is {health.get('pct')!r} but its {len(pcts)} "
                f"auditors mean {want}")
        if isinstance(health.get("pct"), int) and health.get("band") != band_for(health["pct"]):
            errors.append(
                f"rollup health 'band' is {health.get('band')!r} but "
                f"{health['pct']}% is {band_for(health['pct'])!r}")

    trend = health.get("trend")
    if not isinstance(trend, list):
        errors.append("rollup health 'trend' must be a list ([] when there is no history)")
    elif any(not isinstance(t, int) or not 0 <= t <= 100 for t in trend):
        errors.append("rollup health 'trend' entries must be integers in 0..100")
    elif trend and health.get("pct") in trend[-1:]:
        errors.append(
            "rollup health 'trend' ends with this run's own 'pct'; trend holds PRIOR runs "
            "only, so the current score is not repeated in it")
    return errors


def validate_rollup(path: str | Path) -> list[str]:
    """Return contract violations for a `rollup-*.md` suite roll-up ([] = valid).

    A roll-up is not an auditor report: it has no `auditor`, `mode`, or `frameworks`, it
    carries no `[sevN]` finding blocks of its own (it links to the member reports that
    own them), and it has `## Notes` where a report has `## Appendix` — so the coverage
    and finding-field checks do not apply to it.
    """
    path = Path(path)
    if not path.exists():
        return [f"file not found: {path}"]
    fm, body = _split_frontmatter(path.read_text(encoding="utf-8"))
    if fm is None:
        return [body]
    return (_check_rollup_frontmatter(fm) + _check_rollup_summary(fm)
            + _check_rollup_health(fm))


def validate(path: str | Path) -> list[str]:
    """Return a list of contract violations for the report at `path` ([] = valid).

    Dispatches on the document type: a suite roll-up (§9) validates through
    `validate_rollup`, everything else as an auditor report (§3-§6).
    """
    path = Path(path)
    if not path.exists():
        return [f"file not found: {path}"]
    text = path.read_text(encoding="utf-8")

    fm, body = _split_frontmatter(text)
    if fm is None:
        return [body]  # body holds the error message in the failure case

    if is_rollup(fm):
        return (_check_rollup_frontmatter(fm) + _check_rollup_summary(fm)
                + _check_rollup_health(fm))

    errors = _check_frontmatter(fm)
    errors += _check_summary(fm, body)
    errors += _check_health(fm)
    errors += _check_finding_fields(body)
    errors += _check_coverage(body)
    errors += _check_walkthrough(body)
    return errors


INDEX_COLUMNS = ["Date (UTC)", "Auditor", "Scope", "P0", "P1", "P2", "P3", "Health",
                 "Report"]


def _table_cells(line: str) -> list[str]:
    """Split a markdown table row into trimmed cells (ignoring the outer pipes)."""
    return [c.strip() for c in line.strip().strip("|").split("|")]


def validate_index(path: str | Path) -> list[str]:
    """Return contract violations for a `.ux/audits/index.md` ([] = valid).

    The index is append-only: this checks structure (header row + column count +
    integer severity cells), not history, since prior rows must never be rewritten.
    """
    path = Path(path)
    if not path.exists():
        return [f"index not found: {path}"]
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]

    header_idx = next((i for i, ln in enumerate(lines)
                       if "Date (UTC)" in ln and "Report" in ln), None)
    if header_idx is None:
        return [f"index missing the table header row (columns: {INDEX_COLUMNS})"]

    header = _table_cells(lines[header_idx])
    if header != INDEX_COLUMNS:
        return [f"index header has wrong columns: expected {INDEX_COLUMNS}, got {header}"]

    errors: list[str] = []
    # Data rows follow the header separator (|---|---|). Skip the separator line.
    for ln in lines[header_idx + 1:]:
        cells = _table_cells(ln)
        if set("".join(cells)) <= set("-: "):  # separator row
            continue
        if len(cells) != len(INDEX_COLUMNS):
            errors.append(
                f"index row has {len(cells)} columns, expected {len(INDEX_COLUMNS)}: {ln!r}")
            continue
        for cell in cells[3:7]:  # P0..P3
            if not cell.isdigit():
                errors.append(f"index priority cell not an integer: {cell!r} in {ln!r}")
        health = cells[7]
        # A report with no scorecard writes an em dash; anything else must be a percentage.
        if health != "\u2014" and not (health.isdigit() and 0 <= int(health) <= 100):
            errors.append(
                f"index health cell must be 0-100 or '\u2014': {health!r} in {ln!r}")
    return errors


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--index":
        rest = argv[1:] or ["index.md"]
        ok = True
        for arg in rest:
            errors = validate_index(arg)
            if errors:
                ok = False
                print(f"INVALID index: {arg}", file=sys.stderr)
                for e in errors:
                    print(f"  - {e}", file=sys.stderr)
            else:
                print(f"valid index: {arg}")
        return 0 if ok else 1
    if not argv:
        print("usage: validate_report.py <report.md> [...]  |  --index <index.md>",
              file=sys.stderr)
        return 2
    ok = True
    for arg in argv:
        errors = validate(arg)
        if errors:
            ok = False
            print(f"INVALID: {arg}", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
        else:
            print(f"valid: {arg}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
