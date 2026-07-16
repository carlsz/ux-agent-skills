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

The schema is deliberately small — ten keys. A journey is written by a human answering
an interview, so every required field has to earn its place: anything derivable from the
filename, from git, or from another field is ceremony, and ceremony is what makes people
stop writing journeys.

Usage:
    python3 scripts/validate_cuj.py <cuj.md> [<cuj.md> ...]   # per-file
    python3 scripts/validate_cuj.py --dir  .ux/cujs           # + cross-file checks
    python3 scripts/validate_cuj.py --index .ux/cujs          # print the index block

Exit code 0 = all valid; 1 = at least one violation (printed to stderr); 2 = usage.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REQUIRED_KEYS = ["id", "schema", "title", "actor", "goal", "criticality", "entry_point",
                 "preconditions", "steps", "success_criteria"]

# Criticality is not decoration: `audit-cuj` clamps finding severity by it, so a level
# outside this set has no defined cap.
CRITICALITY = ["critical", "high", "medium", "low"]

# CUJ files record no author, and no provenance block at all — git history answers when,
# how, and by whom, and answers it honestly, unlike hand-maintained fields that go stale
# the moment someone forgets. Rejected rather than merely undocumented: a privacy rule
# that isn't executable is a comment.
FORBIDDEN_KEYS = ["author", "authored", "by", "email"]

ID_RE = re.compile(r"^CUJ-\d{3}$")
# The filename carries the slug — there is no `slug` key, because a field whose only job
# is to be checked against the filename is ceremony. The id stays in frontmatter (reports
# cite it), so it is the one thing that can still disagree with the name on disk.
FILENAME_RE = re.compile(r"^(CUJ-\d{3})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")

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
    """The id, and the filename that carries it plus the slug."""
    errors: list[str] = []

    cuj_id = fm.get("id")
    if not (isinstance(cuj_id, str) and ID_RE.match(cuj_id)):
        errors.append(f"'id' must match CUJ-NNN (three digits), got {cuj_id!r}")

    match = FILENAME_RE.match(path.name)
    if not match:
        errors.append(
            f"filename {path.name!r} must be '<id>-<slug>.md' — a CUJ-NNN id and a "
            f"lowercase kebab-case slug (e.g. 'CUJ-001-add-a-task.md')")
    elif isinstance(cuj_id, str) and match.group(1) != cuj_id:
        # The generated index links by filename while reports cite the frontmatter id.
        # If they disagree, the host's SPEC.md points at one journey and every finding
        # names another.
        errors.append(
            f"filename {path.name!r} declares id {match.group(1)!r} but frontmatter "
            f"says {cuj_id!r}")

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


def _check_no_provenance(fm: dict) -> list[str]:
    """CUJ files carry no author and no provenance block.

    Git already records who wrote a journey, when, and through how many revisions — and
    records it honestly, unlike hand-maintained frontmatter that goes stale the moment
    someone forgets to bump it. An unbumped revision is worse than no revision, because
    it lies with confidence.

    Enforced rather than documented, because no PII in the artifact beats a rule about
    handling PII in the artifact.
    """
    return [
        f"{key!r} must not appear — CUJ files record no author or provenance; "
        f"git history answers who/when/which revision"
        for key in FORBIDDEN_KEYS if key in fm
    ]


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

    for field in ("title", "actor", "goal", "entry_point"):
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
    errors += _check_no_provenance(fm)
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
