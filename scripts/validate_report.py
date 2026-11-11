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
KNOWN_SCHEMAS = (2, 3)

# Rating vocabulary, per schema — §4 changed instrument at schema 3.
#
#   schema 2: the scored field is SEVERITY (sev4 worst). `sev0` is a non-finding and must
#             never appear, as a summary key or as a heading.
#   schema 3: the scored field is PRIORITY (P0 first in the queue, P3 last). Severity is
#             still assessed and still reported per finding, but is no longer aggregated,
#             so schema 3 has no forbidden rank: "not a problem" is simply never filed.
#
# Schema 2 is a PERMANENT path, not a deprecation. A report records the contract it was
# born under and is never rewritten (contract §"Schema history"), so a 2 written in 2026
# must still validate in 2036.
RATING = {
    2: {
        "keys": ["sev4", "sev3", "sev2", "sev1"],
        "tag": "sev",
        "pattern": re.compile(r"^###\s+\[sev(\d+)\]", re.MULTILINE),
        "ranks": {"1", "2", "3", "4"},
        "omitted": "0",
        "fields": ["Issue Description", "Framework Violation", "Severity",
                   "Evidence", "Recommended Fix"],
    },
    3: {
        "keys": ["P0", "P1", "P2", "P3"],
        "tag": "P",
        "pattern": re.compile(r"^###\s+\[P(\d+)\]", re.MULTILINE),
        "ranks": {"0", "1", "2", "3"},
        "omitted": None,
        "fields": ["Issue Description", "Framework Violation", "Priority", "Severity",
                   "Evidence", "Recommended Fix"],
    },
}

# The optional `## Walkthrough` section (§5) and the markdown images inside it.
WALKTHROUGH_RE = re.compile(r"^##\s+Walkthrough\s*$", re.MULTILINE | re.IGNORECASE)
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
# Finding fields are per-schema — see RATING[...]["fields"].


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

    schema = fm.get("schema")
    if type(schema) is not int or schema not in KNOWN_SCHEMAS:
        errors.append(
            f"frontmatter 'schema' must be one of {list(KNOWN_SCHEMAS)} "
            f"(an integer), got {schema!r}")

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
    """Counts must reconcile against the body, in the vocabulary of this report's schema."""
    errors: list[str] = []
    summary = fm.get("summary")
    if not isinstance(summary, dict):
        errors.append("frontmatter 'summary' must be a mapping")
        return errors

    spec = RATING.get(fm.get("schema"))
    if spec is None:
        return errors  # unknown schema: already reported by _check_frontmatter

    schema, keys = fm["schema"], spec["keys"]
    other_schema = 3 if schema == 2 else 2
    other = RATING[other_schema]

    # A half-migrated report: this schema's shape carrying the other's vocabulary. Caught
    # explicitly because the count checks below would otherwise report it as a pile of
    # missing keys, which reads like a malformed report rather than a mismatched one.
    foreign = sorted(k for k in other["keys"] if k in summary)
    if foreign:
        errors.append(
            f"summary uses schema-{other_schema} keys {foreign} in a schema-{schema} report")

    if spec["omitted"] is not None:
        forbidden = f"{spec['tag']}{spec['omitted']}"
        if forbidden in summary:
            errors.append(
                f"summary must not contain {forbidden!r} "
                f"(rank {spec['omitted']} findings are omitted)")

    for key in ["total"] + keys:
        if key not in summary:
            # Name casing as the cause when that is what it is. The keys are `P0`-`P3`
            # while the ROLL-UP's own `priorities:` map used to be lowercase, so `p0:` is
            # the natural slip -- and a bare "missing required key" sent the author looking
            # for an absent key rather than a miscased one.
            wrong_case = next((k for k in summary if str(k).lower() == key.lower()
                               and str(k) != key), None)
            if wrong_case is not None:
                errors.append(
                    f"summary has {wrong_case!r} but the key is {key!r} "
                    f"(summary keys are case-sensitive)")
            else:
                errors.append(f"summary missing required key: {key!r}")
        elif not isinstance(summary[key], int) or summary[key] < 0:
            errors.append(f"summary {key!r} must be a non-negative integer")

    if all(isinstance(summary.get(k), int) for k in ["total"] + keys):
        by_rank = sum(summary[k] for k in keys)
        if summary["total"] != by_rank:
            errors.append(
                f"summary 'total' ({summary['total']}) != sum of "
                f"{keys[0]}-{keys[-1]} ({by_rank})")

        found = spec["pattern"].findall(body)
        if spec["omitted"] is not None and spec["omitted"] in found:
            errors.append(
                f"body contains a [{spec['tag']}{spec['omitted']}] finding; "
                f"rank {spec['omitted']} must be omitted")
        stray = sorted({r for r in found
                        if r not in spec["ranks"] and r != spec["omitted"]})
        if stray:
            errors.append(
                f"body has finding heading(s) outside the "
                f"{spec['tag']}{min(spec['ranks'])}-{spec['tag']}{max(spec['ranks'])} "
                f"range: {stray}")

        graded = [r for r in found if r in spec["ranks"]]
        if len(graded) != summary["total"]:
            errors.append(
                f"summary 'total' ({summary['total']}) != findings in body ({len(graded)})")
        for key in keys:
            n = sum(1 for r in graded if r == key[-1])
            if n != summary[key]:
                errors.append(
                    f"summary {key!r} ({summary[key]}) != [{key}] findings in body ({n})")

    # The other half of the migration check: right summary, wrong headings.
    if other["pattern"].search(body):
        errors.append(
            f"body uses [{other['tag']}N] finding headings in a schema-{schema} report")

    return errors


def _check_finding_fields(body: str, schema: int | None) -> list[str]:
    """Each finding block must carry the labelled fields its schema requires."""
    spec = RATING.get(schema)
    if spec is None:
        return []
    errors: list[str] = []
    matches = list(spec["pattern"].finditer(body))
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        block = body[start:end]
        heading = body[start:body.index("\n", start) if "\n" in body[start:] else end]
        missing = [f for f in spec["fields"] if f not in block]
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
    errors += _check_finding_fields(body, fm.get("schema"))
    errors += _check_coverage(body)
    errors += _check_walkthrough(body)
    return errors


# The index is append-only and SHARED across runs and schemas, so its columns cannot
# simply change at schema 3 — rewriting prior rows is forbidden. Both shapes are therefore
# valid, and a file may carry a legacy table with a new-shaped one appended below it. An
# index keeps the shape it was created with; the first schema-3 run in a host that already
# has one starts a second table rather than migrating the first.
INDEX_COLUMNS_BY_SHAPE = {
    "severity": ["Date (UTC)", "Auditor", "Scope", "Sev4", "Sev3", "Sev2", "Sev1",
                 "Report"],
    "priority": ["Date (UTC)", "Auditor", "Scope", "P0", "P1", "P2", "P3", "Report"],
}


def _table_cells(line: str) -> list[str]:
    """Split a markdown table row into trimmed cells (ignoring the outer pipes)."""
    return [c.strip() for c in line.strip().strip("|").split("|")]


def validate_index(path: str | Path) -> list[str]:
    """Return contract violations for a `.ux/audits/index.md` ([] = valid).

    The index is append-only: this checks structure (a recognised header row + column
    count + integer count cells), not history, since prior rows must never be rewritten.
    A file may hold more than one table — a legacy severity-shaped one and a
    priority-shaped one below it — so each header governs the rows beneath it until the
    next header. Lines that are not table rows are skipped, which is what lets a heading
    sit between the two tables.
    """
    path = Path(path)
    if not path.exists():
        return [f"index not found: {path}"]
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]

    header_idxs = [i for i, ln in enumerate(lines)
                   if ln.lstrip().startswith("|")
                   and "Date (UTC)" in ln and "Report" in ln]
    if not header_idxs:
        return ["index missing the table header row (columns: "
                f"{INDEX_COLUMNS_BY_SHAPE['priority']})"]

    errors: list[str] = []
    for n, h in enumerate(header_idxs):
        header = _table_cells(lines[h])
        cols = next((c for c in INDEX_COLUMNS_BY_SHAPE.values() if header == c), None)
        if cols is None:
            errors.append(
                "index header has wrong columns: expected one of "
                f"{list(INDEX_COLUMNS_BY_SHAPE.values())}, got {header}")
            continue
        stop = header_idxs[n + 1] if n + 1 < len(header_idxs) else len(lines)
        for ln in lines[h + 1:stop]:
            if not ln.lstrip().startswith("|"):
                continue  # prose between tables, e.g. a heading
            cells = _table_cells(ln)
            if set("".join(cells)) <= set("-: "):  # separator row
                continue
            if len(cells) != len(cols):
                errors.append(
                    f"index row has {len(cells)} columns, expected {len(cols)}: {ln!r}")
                continue
            for cell in cells[3:7]:  # the four count columns, whichever shape
                if not cell.isdigit():
                    errors.append(f"index count cell not an integer: {cell!r} in {ln!r}")
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
