#!/usr/bin/env python3
"""Validate a `.ux/cujs` critical user journey against the CUJ file contract.

Encodes the machine-checkable invariants documented in
`skills/spec-cuj/references/cuj-contract.md`. Reused by the `spec-cuj` skill to
self-check a journey it just authored, by `audit-cuj` to reject a malformed journey
BEFORE walking it (half-verifying garbage is worse than refusing), and by the contract
test suite.

Also renders the generated CUJ index block for the host's SPEC.md. That lives here
rather than in the skill for one reason: the block is a pure function of the CUJ
directory, and only a script can promise byte-identical regeneration. An agent
rewriting the table from memory cannot, and the block is spliced into a file the user
owns.

Usage:
    python3 scripts/validate_cuj.py <cuj.md> [<cuj.md> ...]   # per-file
    python3 scripts/validate_cuj.py --dir  .ux/cujs           # + cross-file checks
    python3 scripts/validate_cuj.py --index .ux/cujs          # print the index block

Exit code 0 = all valid; 1 = at least one violation (printed to stderr); 2 = usage.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

import yaml

REQUIRED_KEYS = ["id", "slug", "schema", "title", "actor", "actor_description", "goal",
                 "criticality", "entry_point", "preconditions", "steps",
                 "success_criteria", "authored"]

# Criticality is not decoration: `audit-cuj` clamps finding severity by it, so a level
# outside this set has no defined cap.
CRITICALITY = ["critical", "high", "medium", "low"]
METHODS = {"interview", "interview-fallback", "manual", "imported"}

AUTHORED_KEYS = ["date", "method", "revision"]
# Provenance records WHEN and HOW, never WHO. Git history answers "who decided this
# mattered" more honestly than a self-reported field that goes stale the moment someone
# else edits the file — and no PII in the artifact beats a rule about handling it.
AUTHORED_FORBIDDEN = ["by", "author", "email"]

ID_RE = re.compile(r"^CUJ-\d{3}$")
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

REQUIRED_HEADINGS = ["## Narrative", "## Out of scope"]

# Where CUJs live relative to the host repo root — the index links through this, so it
# is the contract's path, not the directory we happened to read from.
CUJ_DIR_REL = ".ux/cujs"

INDEX_BEGIN = ("<!-- BEGIN ux-agent-skills:cuj-index — generated from .ux/cujs/; "
               "edit the CUJ files, not this table -->")
INDEX_END = "<!-- END ux-agent-skills:cuj-index -->"
INDEX_COLUMNS = ["ID", "Journey", "Actor", "Criticality", "Goal", "File"]
GOAL_MAX = 100


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


def _check_identity(fm: dict, path: Path) -> list[str]:
    """id/slug patterns, and the filename they jointly determine."""
    errors: list[str] = []

    cuj_id = fm.get("id")
    if not (isinstance(cuj_id, str) and ID_RE.match(cuj_id)):
        errors.append(f"'id' must match CUJ-NNN (three digits), got {cuj_id!r}")

    slug = fm.get("slug")
    if not (isinstance(slug, str) and SLUG_RE.match(slug)):
        errors.append(f"'slug' must be lowercase kebab-case, got {slug!r}")

    # The generated index links by <id>-<slug>.md; a mismatch is a dead link in the
    # host's SPEC.md, which is why this is worth failing over.
    if isinstance(cuj_id, str) and isinstance(slug, str):
        expected = f"{cuj_id}-{slug}.md"
        if path.name != expected:
            errors.append(
                f"filename {path.name!r} must equal '<id>-<slug>.md' ({expected!r})")

    if fm.get("schema") != 1:
        errors.append("'schema' must equal 1")

    return errors


def _check_steps(fm: dict) -> list[str]:
    """Steps are ordered, contiguous, and every one has an observable outcome."""
    errors: list[str] = []
    steps = fm.get("steps")

    if not isinstance(steps, list) or not steps:
        errors.append("'steps' must be a non-empty list")
        return errors

    for i, step in enumerate(steps):
        label = f"step {i + 1}"
        if not isinstance(step, dict):
            errors.append(f"{label}: must be a mapping with 'n', 'action', 'expect'")
            continue

        # Findings cite "step <n>" by number, so the numbering has to be trustworthy.
        if step.get("n") != i + 1:
            errors.append(
                f"{label}: step numbers must be contiguous 1..N in order, "
                f"got n={step.get('n')!r} at position {i + 1}")

        for field in ("action", "expect"):
            value = step.get(field)
            if not (isinstance(value, str) and value.strip()):
                errors.append(f"{label}: {field!r} must be a non-empty string")

    return errors


def _check_authored(fm: dict) -> list[str]:
    errors: list[str] = []
    authored = fm.get("authored")

    if not isinstance(authored, dict):
        if "authored" in fm:
            errors.append("'authored' must be a mapping with date, method, revision")
        return errors

    for key in AUTHORED_KEYS:
        if key not in authored:
            errors.append(f"'authored' missing required key: {key!r}")

    for forbidden in AUTHORED_FORBIDDEN:
        if forbidden in authored:
            errors.append(
                f"'authored' must not contain {forbidden!r} — CUJ files record no "
                f"author (no PII); git history already answers who wrote this")

    date = authored.get("date")
    if isinstance(date, datetime):
        pass  # PyYAML parsed an ISO timestamp — fine.
    elif isinstance(date, str):
        try:
            datetime.fromisoformat(date.replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"'authored.date' is not ISO-8601: {date!r}")
    elif "date" in authored:
        errors.append("'authored.date' must be an ISO-8601 string")

    method = authored.get("method")
    if "method" in authored and method not in METHODS:
        errors.append(
            f"'authored.method' must be one of {sorted(METHODS)}, got {method!r}")

    revision = authored.get("revision")
    if "revision" in authored and (not isinstance(revision, int)
                                   or isinstance(revision, bool) or revision < 1):
        errors.append(f"'authored.revision' must be a positive integer, got {revision!r}")

    return errors


def _check_body(body: str) -> list[str]:
    """The narrative carries what YAML cannot — why the journey matters, and its edges.

    Note what is NOT checked: the body must not restate the steps. A CUJ is a living
    document, so duplicating frontmatter into prose would only guarantee drift.
    """
    errors: list[str] = []
    for heading in REQUIRED_HEADINGS:
        if heading.lower() not in body.lower():
            errors.append(f"body missing the {heading!r} section")
    return errors


def validate(path: str | Path) -> list[str]:
    """Return a list of contract violations for the CUJ at `path` ([] = valid)."""
    path = Path(path)
    if not path.exists():
        return [f"file not found: {path}"]
    text = path.read_text(encoding="utf-8")

    fm, body = _split_frontmatter(text)
    if fm is None:
        return [body]  # body holds the error message in the failure case

    errors: list[str] = []
    for key in REQUIRED_KEYS:
        if key not in fm:
            errors.append(f"frontmatter missing required key: {key!r}")

    errors += _check_identity(fm, path)

    for field in ("title", "actor", "actor_description", "goal", "entry_point"):
        if field in fm and not (isinstance(fm[field], str) and fm[field].strip()):
            errors.append(f"{field!r} must be a non-empty string")

    criticality = fm.get("criticality")
    if criticality not in CRITICALITY:
        errors.append(
            f"'criticality' must be one of {CRITICALITY}, got {criticality!r}")

    for field in ("preconditions", "success_criteria"):
        value = fm.get(field)
        if not isinstance(value, list) or not value:
            errors.append(f"{field!r} must be a non-empty list")
        elif any(not (isinstance(v, str) and v.strip()) for v in value):
            errors.append(f"{field!r} entries must be non-empty strings")

    errors += _check_steps(fm)
    errors += _check_authored(fm)
    errors += _check_body(body)
    return errors


def _cuj_files(directory: str | Path) -> list[Path]:
    """Every CUJ file in `directory`, in deterministic order."""
    return sorted(Path(directory).glob("CUJ-*.md"))


def validate_dir(directory: str | Path) -> list[str]:
    """Per-file violations plus the cross-file ones a single file cannot reveal.

    A duplicate id is the one that matters: it breaks the generated index AND makes
    every report's "CUJ-0NN step <n>" citation ambiguous about which journey it means.
    """
    directory = Path(directory)
    if not directory.is_dir():
        return [f"directory not found: {directory}"]

    files = _cuj_files(directory)
    if not files:
        return [f"no CUJ files found in {directory}"]

    errors: list[str] = []
    seen: dict[str, str] = {}
    for path in files:
        for err in validate(path):
            errors.append(f"{path.name}: {err}")

        fm, _ = _split_frontmatter(path.read_text(encoding="utf-8"))
        if not isinstance(fm, dict):
            continue
        cuj_id = fm.get("id")
        if not isinstance(cuj_id, str):
            continue
        if cuj_id in seen:
            errors.append(
                f"duplicate id {cuj_id!r}: claimed by both {seen[cuj_id]!r} and "
                f"{path.name!r}")
        else:
            seen[cuj_id] = path.name

    return errors


def _cell(value: object) -> str:
    """Render a value as a markdown table cell: single-line, pipes escaped."""
    text = " ".join(str(value).split())
    return text.replace("|", "\\|")


def _truncate(text: str, limit: int = GOAL_MAX) -> str:
    """Trim to `limit` chars on a word boundary, with an ellipsis if trimmed."""
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip()
    return f"{cut}…"


def render_index(directory: str | Path, link_prefix: str = CUJ_DIR_REL) -> str:
    """Return the marker-wrapped CUJ index block for the host's SPEC.md.

    Deterministic by construction: every cell derives from frontmatter and rows sort by
    id, so two runs over an unchanged directory are byte-identical. Nothing in the block
    is user-authored, which is what makes splicing it safe — there is nothing to
    preserve between the markers.
    """
    rows: list[str] = []
    for path in _cuj_files(directory):
        fm, _ = _split_frontmatter(path.read_text(encoding="utf-8"))
        if not isinstance(fm, dict):
            continue
        link = f"{link_prefix}/{path.name}"
        rows.append("| " + " | ".join([
            _cell(fm.get("id", "")),
            _cell(fm.get("title", "")),
            _cell(fm.get("actor", "")),
            _cell(fm.get("criticality", "")),
            _truncate(_cell(fm.get("goal", ""))),
            f"[{link}]({link})",
        ]) + " |")

    rows.sort()  # by id — ids are fixed-width, so lexical order is numeric order

    lines = [
        INDEX_BEGIN,
        "| " + " | ".join(INDEX_COLUMNS) + " |",
        "|" + "|".join("---" for _ in INDEX_COLUMNS) + "|",
        *rows,
        INDEX_END,
    ]
    return "\n".join(lines) + "\n"


def _report(label: str, errors: list[str]) -> bool:
    if errors:
        print(f"INVALID: {label}", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return False
    print(f"valid: {label}")
    return True


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--index":
        if len(argv) < 2:
            print("usage: validate_cuj.py --index <dir>", file=sys.stderr)
            return 2
        print(render_index(argv[1]), end="")
        return 0

    if argv and argv[0] == "--dir":
        if len(argv) < 2:
            print("usage: validate_cuj.py --dir <dir>", file=sys.stderr)
            return 2
        return 0 if _report(argv[1], validate_dir(argv[1])) else 1

    if not argv:
        print("usage: validate_cuj.py <cuj.md> [...]  |  --dir <dir>  |  --index <dir>",
              file=sys.stderr)
        return 2

    ok = True
    for arg in argv:
        ok = _report(arg, validate(arg)) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
