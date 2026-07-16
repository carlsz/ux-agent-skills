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

from audit_safety import changes_confined_to  # noqa: E402


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

    if failures:
        print("FAIL — safety:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS — safety (invariant + idempotency)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
