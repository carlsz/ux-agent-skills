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

# A finding is a level-3 heading tagged with its severity, e.g. "### [sev3] Foo".
FINDING_RE = re.compile(r"^###\s+\[sev([0-4])\]", re.MULTILINE)
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

    if fm.get("schema") != 1:
        errors.append("frontmatter 'schema' must equal 1")

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


def validate(path: str | Path) -> list[str]:
    """Return a list of contract violations for the report at `path` ([] = valid)."""
    path = Path(path)
    if not path.exists():
        return [f"file not found: {path}"]
    text = path.read_text(encoding="utf-8")

    fm, body = _split_frontmatter(text)
    if fm is None:
        return [body]  # body holds the error message in the failure case

    errors = _check_frontmatter(fm)
    errors += _check_summary(fm, body)
    errors += _check_finding_fields(body)
    errors += _check_coverage(body)
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
