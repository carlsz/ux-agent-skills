#!/usr/bin/env python3
"""Executable spec for the `.ux/cujs` CUJ file contract.

The human-readable contract lives in `skills/spec-cuj/references/cuj-contract.md`; this
test encodes its machine-checkable invariants via `scripts/validate_cuj.py` and asserts
that conforming journeys pass while known-malformed ones fail.

Two checks here have no analogue in the report contract, because a CUJ is a living
document rather than a write-once artifact:

* **Cross-file** — duplicate ids and filename/slug mismatches are invisible to a per-file
  validator, and both break the generated index.
* **Index idempotency** — the SPEC.md block is a pure function of the CUJ directory, and
  regeneration must be byte-identical or it silently churns the host's SPEC.md.

Run: `python3 tests/test_cuj_contract.py` (exit 0 = pass, 1 = fail).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from validate_cuj import render_index, validate, validate_dir  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "cujs"


def _expect_valid(path: Path) -> list[str]:
    errors = validate(path)
    if errors:
        return [f"expected VALID but got errors: {path.name}: {errors}"]
    return []


def _expect_invalid(path: Path, needle: str) -> list[str]:
    errors = validate(path)
    if not errors:
        return [f"expected INVALID but passed: {path.name}"]
    if not any(needle in e for e in errors):
        return [f"{path.name}: expected an error mentioning {needle!r}, got {errors}"]
    return []


def _expect_valid_dir(path: Path) -> list[str]:
    errors = validate_dir(path)
    if errors:
        return [f"expected VALID dir but got errors: {path.name}: {errors}"]
    return []


def _expect_invalid_dir(path: Path, needle: str) -> list[str]:
    errors = validate_dir(path)
    if not errors:
        return [f"expected INVALID dir but passed: {path.name}"]
    if not any(needle in e for e in errors):
        return [f"{path.name}: expected a dir error mentioning {needle!r}, got {errors}"]
    return []


def check_index_idempotent() -> list[str]:
    """Regenerating the index over an unchanged directory must be byte-identical.

    The block is spliced into the HOST's SPEC.md. If two runs over the same journeys
    differ by so much as a byte, every audit churns the host's spec and the diff the
    skill shows the user becomes noise.
    """
    first = render_index(FIXTURES / "valid")
    second = render_index(FIXTURES / "valid")
    if first != second:
        return ["render_index is not idempotent: two runs over an unchanged directory "
                "produced different output"]
    return []


def check_index_shape() -> list[str]:
    """The block carries its markers, one row per CUJ, sorted by id."""
    errors: list[str] = []
    block = render_index(FIXTURES / "valid")

    if "BEGIN ux-agent-skills:cuj-index" not in block:
        errors.append("index block missing its BEGIN marker")
    if "END ux-agent-skills:cuj-index" not in block:
        errors.append("index block missing its END marker")

    for column in ("ID", "Journey", "Actor", "Criticality", "Goal", "File"):
        if column not in block:
            errors.append(f"index block missing the {column!r} column")

    rows = [ln for ln in block.splitlines() if ln.startswith("| CUJ-")]
    if len(rows) != 2:
        errors.append(f"index block has {len(rows)} data rows, expected 2")
    elif not (rows[0].startswith("| CUJ-001") and rows[1].startswith("| CUJ-002")):
        errors.append(f"index rows not sorted by id: {[r[:12] for r in rows]}")

    # The link must be the <id>-<slug>.md filename, or the host's SPEC.md dead-links.
    if "CUJ-001-add-a-task.md" not in block:
        errors.append("index block does not link CUJ-001 by its <id>-<slug>.md filename")

    return errors


def main() -> int:
    failures: list[str] = []

    # Conforming journeys validate cleanly.
    failures += _expect_valid(FIXTURES / "valid" / "CUJ-001-add-a-task.md")
    failures += _expect_valid(FIXTURES / "valid" / "CUJ-002-complete-a-task.md")
    failures += _expect_valid_dir(FIXTURES / "valid")

    # Each malformed journey is rejected for the right reason.
    failures += _expect_invalid(FIXTURES / "invalid" / "CUJ-003-blank-expect.md", "expect")
    failures += _expect_invalid(FIXTURES / "invalid" / "CUJ-004-bad-criticality.md",
                                "criticality")
    failures += _expect_invalid(FIXTURES / "invalid" / "CUJ-005-no-steps.md", "steps")
    failures += _expect_invalid(FIXTURES / "invalid" / "CUJ-006-missing-provenance.md",
                                "authored")
    failures += _expect_invalid(FIXTURES / "invalid" / "CUJ-007-noncontiguous.md",
                                "contiguous")
    failures += _expect_invalid(FIXTURES / "invalid" / "CUJ-008-wrong-name.md", "filename")
    # No PII: provenance records no author. Enforced, not merely documented (SPEC §9.7).
    failures += _expect_invalid(FIXTURES / "invalid" / "CUJ-009-authored-by.md", "by")

    # Cross-file: a duplicate id is invisible per-file but breaks the index and makes
    # every "CUJ-010 step <n>" citation ambiguous.
    failures += _expect_invalid_dir(FIXTURES / "dupes", "duplicate")

    # The generated SPEC.md index block.
    failures += check_index_idempotent()
    failures += check_index_shape()

    if failures:
        print("FAIL — CUJ contract:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS — CUJ contract (13 checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
