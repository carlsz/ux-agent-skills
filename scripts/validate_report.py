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
                 "frameworks", "summary"]
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
SEVERITY_KEYS = ["sev4", "sev3", "sev2", "sev1"]  # sev0 is intentionally absent

# --- roll-up vocabulary (contract §9) ----------------------------------------------------

# A suite roll-up is a sibling document type, not an auditor report: it has no single
# `auditor`, `mode`, or `frameworks`, so it validates through its own path.
ROLLUP_REQUIRED_KEYS = ["kind", "schema", "version", "date", "target", "scope", "verdict",
                        "verdict_reason", "auditors_ran", "auditors_skipped", "summary"]
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

    Any catastrophe (sev4) or major (sev3) blocks the release; everything else ships.
    This is deliberately total and mechanical: five runs of the same app produced five
    different verdicts from the same facts — two of them opposite on identical counts —
    because the gate lived in prose ("any auditor reports a sev3 blocker") and left the
    auditor to decide what counted as a blocker. A derived verdict cannot drift.
    """
    return "NO-GO" if (summary.get("sev4") or summary.get("sev3")) else "GO"

# A finding is a level-3 heading tagged with its severity, e.g. "### [sev3] Foo".
FINDING_RE = re.compile(r"^###\s+\[sev([0-4])\]", re.MULTILINE)
# The optional `## Walkthrough` section (§5) and the markdown images inside it.
WALKTHROUGH_RE = re.compile(r"^##\s+Walkthrough\s*$", re.MULTILINE | re.IGNORECASE)
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
# The five labelled fields every finding block must contain.
FINDING_FIELDS = ["Issue Description", "Framework Violation", "Severity",
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

    if fm.get("schema") != 2:
        errors.append("frontmatter 'schema' must equal 2")

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

    if "sev0" in summary:
        errors.append("summary must not contain 'sev0' (severity 0 findings are omitted)")

    for key in ["total"] + SEVERITY_KEYS:
        if key not in summary:
            errors.append(f"summary missing required key: {key!r}")
        elif not isinstance(summary[key], int) or summary[key] < 0:
            errors.append(f"summary {key!r} must be a non-negative integer")

    # Counts must reconcile: total == sum of per-severity counts.
    if all(isinstance(summary.get(k), int) for k in ["total"] + SEVERITY_KEYS):
        by_sev = sum(summary[k] for k in SEVERITY_KEYS)
        if summary["total"] != by_sev:
            errors.append(
                f"summary 'total' ({summary['total']}) != sum of sev1-4 ({by_sev})")

        # Findings in the body must match the declared counts.
        found = FINDING_RE.findall(body)
        if any(sev == "0" for sev in found):
            errors.append("body contains a [sev0] finding; severity 0 must be omitted")
        graded = [s for s in found if s != "0"]
        if len(graded) != summary["total"]:
            errors.append(
                f"summary 'total' ({summary['total']}) != findings in body ({len(graded)})")
        for sev_key in SEVERITY_KEYS:
            n = sum(1 for s in graded if s == sev_key[-1])
            if n != summary[sev_key]:
                errors.append(
                    f"summary {sev_key!r} ({summary[sev_key]}) != [sev{sev_key[-1]}] "
                    f"findings in body ({n})")

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

    if fm.get("schema") != 2:
        errors.append("rollup frontmatter 'schema' must equal 2")

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

    if "sev0" in summary:
        errors.append("rollup summary must not contain 'sev0'")

    for key in ["total"] + SEVERITY_KEYS:
        if key not in summary:
            errors.append(f"rollup summary missing required key: {key!r}")
        elif not isinstance(summary[key], int) or summary[key] < 0:
            errors.append(f"rollup summary {key!r} must be a non-negative integer")

    if not all(isinstance(summary.get(k), int) for k in ["total"] + SEVERITY_KEYS):
        return errors

    by_sev = sum(summary[k] for k in SEVERITY_KEYS)
    if summary["total"] != by_sev:
        errors.append(
            f"rollup summary 'total' ({summary['total']}) != sum of sev1-4 ({by_sev})")

    verdict = str(fm.get("verdict", "")).strip().upper()
    if verdict in ROLLUP_VERDICTS:
        expected = derive_verdict(summary)
        if verdict != expected:
            errors.append(
                f"rollup 'verdict' is {verdict!r} but the counts derive {expected!r} "
                f"(sev4={summary['sev4']}, sev3={summary['sev3']}); the gate is mechanical")
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
    return _check_rollup_frontmatter(fm) + _check_rollup_summary(fm)


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
        return _check_rollup_frontmatter(fm) + _check_rollup_summary(fm)

    errors = _check_frontmatter(fm)
    errors += _check_summary(fm, body)
    errors += _check_finding_fields(body)
    errors += _check_coverage(body)
    errors += _check_walkthrough(body)
    return errors


INDEX_COLUMNS = ["Date (UTC)", "Auditor", "Scope", "Sev4", "Sev3", "Sev2", "Sev1",
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
        for sev_cell in cells[3:7]:  # Sev4..Sev1
            if not sev_cell.isdigit():
                errors.append(f"index severity cell not an integer: {sev_cell!r} in {ln!r}")
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
