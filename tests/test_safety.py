#!/usr/bin/env python3
"""Exercise the auditor's safety invariant and idempotency in a real temp git repo.

The invariant: after an audit, the host repo has changes ONLY under `.ux/audits/`.
Idempotency: a second run creates a new timestamped report and appends the index —
it never overwrites or deletes a prior report.

These are the guarantees a host owner relies on to run the auditor without fear. We
verify them mechanically here via `scripts/audit_safety.changes_confined_to`.

Run: `python3 tests/test_safety.py` (exit 0 = pass, 1 = fail).
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_safety import EXTRA_BY_PROFILE, changes_confined_to  # noqa: E402

# Bind to the PROFILES, not to the function's defaults. The profiles are what the CLI
# resolves and therefore what every auditor actually runs under; asserting against a
# hand-passed allowlist would leave a widened profile undetected.
AUDIT = EXTRA_BY_PROFILE["audit"]
AUTHORING = EXTRA_BY_PROFILE["authoring"]


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   capture_output=True, text=True)


def _init_repo(repo: Path) -> None:
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t.t")
    _git(repo, "config", "user.name", "t")
    (repo / "app.tsx").write_text("export const App = () => null;\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "baseline")


def _write_report(repo: Path, name: str) -> Path:
    audits = repo / ".ux" / "audits"
    audits.mkdir(parents=True, exist_ok=True)
    report = audits / name
    report.write_text(f"# report {name}\n")
    index = audits / "index.md"
    header = "" if index.exists() else "# Audit index\n\n| Date | Report |\n|--|--|\n"
    with index.open("a") as fh:
        fh.write(header + f"| now | [r]({name}) |\n")
    return report


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _init_repo(repo)

        # Run 1: a report written under .ux/audits/ is confined.
        _write_report(repo, "usability-20260715-100000.md")
        v = changes_confined_to(repo, ".ux/audits/")
        if v:
            failures.append(f"run 1 should be confined, got violations: {v}")

        # A stray write OUTSIDE .ux/audits/ must be detected as a violation.
        (repo / "app.tsx").write_text("// mutated by mistake\n")
        v = changes_confined_to(repo, ".ux/audits/")
        if not any("app.tsx" in x for x in v):
            failures.append(f"a write to app.tsx must be flagged, got: {v}")
        (repo / "app.tsx").write_text("export const App = () => null;\n")  # revert

        # Run 2: idempotency — new timestamped file, first report untouched, 2 reports.
        first = repo / ".ux" / "audits" / "usability-20260715-100000.md"
        first_before = first.read_text()
        _write_report(repo, "usability-20260715-110000.md")
        if first.read_text() != first_before:
            failures.append("run 2 overwrote the run 1 report (not append-only)")
        reports = sorted((repo / ".ux" / "audits").glob("usability-*.md"))
        if len(reports) != 2:
            failures.append(f"expected 2 reports after run 2, found {len(reports)}")
        index_rows = (repo / ".ux" / "audits" / "index.md").read_text().count("[r](")
        if index_rows != 2:
            failures.append(f"expected 2 index rows after run 2, found {index_rows}")
        v = changes_confined_to(repo, ".ux/audits/")
        if v:
            failures.append(f"run 2 should be confined, got violations: {v}")

        # --- The authoring allowlist (/ux-spec) -----------------------------------
        # /ux-spec writes .ux/cujs/ and the host's SPEC.md. That is an OPT-IN widening
        # for authoring only; the audit invariant above must survive it untouched.
        (repo / ".ux" / "cujs").mkdir(parents=True, exist_ok=True)
        (repo / ".ux" / "cujs" / "CUJ-001-add-a-task.md").write_text("# CUJ-001\n")
        (repo / "SPEC.md").write_text("# Spec\n\n## Critical User Journeys\n")

        # 1. THE INVARIANT DOES NOT WEAKEN. This is the assertion the whole allowlist
        #    design exists to protect: an AUDIT run that touched .ux/cujs/ or SPEC.md is
        #    still a violation. If this ever passes, the suite's safety story is gone.
        #    Note it resolves the `audit` PROFILE rather than passing an allowlist by
        #    hand — otherwise widening that profile would go undetected here, which is
        #    the precise mistake this assertion exists to prevent.
        v = changes_confined_to(repo, ".ux/audits/", allow=AUDIT)
        if not any(".ux/cujs" in x for x in v):
            failures.append(f"audit profile must still flag .ux/cujs/, got: {v}")
        if not any("SPEC.md" in x for x in v):
            failures.append(f"audit profile must still flag SPEC.md, got: {v}")

        # 2. The authoring profile permits exactly those two paths.
        v = changes_confined_to(repo, ".ux/audits/", allow=AUTHORING)
        if v:
            failures.append(f"authoring profile should permit .ux/cujs/ + SPEC.md, got: {v}")

        # 3. Authoring is not a licence to touch host code — findings-only still means
        #    never editing host application code.
        (repo / "app.tsx").write_text("// mutated during authoring\n")
        v = changes_confined_to(repo, ".ux/audits/", allow=AUTHORING)
        if not any("app.tsx" in x for x in v):
            failures.append(f"authoring profile must still flag app.tsx, got: {v}")
        (repo / "app.tsx").write_text("export const App = () => null;\n")  # revert

        # 4. Prefix confusion. A naive startswith() would read "SPEC.md" as permitting
        #    SPEC.md.bak, and ".ux/cujs" as permitting .ux/cujs-evil/. An allowlist that
        #    silently widens to neighbouring paths is worse than no allowlist.
        (repo / "SPEC.md.bak").write_text("# sneaky\n")
        (repo / ".ux" / "cujs-evil").mkdir(parents=True, exist_ok=True)
        (repo / ".ux" / "cujs-evil" / "x.md").write_text("# sneaky\n")
        v = changes_confined_to(repo, ".ux/audits/", allow=AUTHORING)
        if not any("SPEC.md.bak" in x for x in v):
            failures.append(f"'SPEC.md' must be an exact match, not a prefix: {v}")
        if not any("cujs-evil" in x for x in v):
            failures.append(f"'.ux/cujs/' must be a directory prefix, not a substring: {v}")

    if failures:
        print("FAIL — safety:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS — safety (invariant + idempotency)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
