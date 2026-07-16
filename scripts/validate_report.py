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
KNOWN_FRAMEWORKS = {"nielsen-10", "shneiderman-8", "ai-heuristics", "npcis"}
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
        unknown = [f for f in frameworks if f not in KNOWN_FRAMEWORKS]
        if unknown:
            errors.append(f"frontmatter 'frameworks' has unknown entries: {unknown}")

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
    return errors


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: validate_report.py <report.md> [...]", file=sys.stderr)
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
