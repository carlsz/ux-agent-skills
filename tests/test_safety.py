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

import contextlib
import io
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import audit_safety  # noqa: E402
from audit_safety import (  # noqa: E402
    EXTRA_BY_PROFILE, changes_confined_to, snapshot, writes_under,
)

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


def _cli(repo: Path, *args: str) -> int:
    """Run the CLI exactly as a skill's self-check step does, and return its exit code.

    Asserted through `audit_safety.main()` rather than the library functions, because the
    gap this guards is precisely that a correct library function can be wired into nothing.
    `writes_under()` shipped unreachable once; a test that only ever imports it would not
    have noticed, and would not notice it becoming unreachable again.
    """
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        return audit_safety.main([str(repo), *args])


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
        (repo / "SPEC.md.bak").unlink()
        (repo / ".ux" / "cujs-evil" / "x.md").unlink()
        (repo / ".ux" / "cujs-evil").rmdir()
        (repo / "SPEC.md").unlink()
        (repo / ".ux" / "cujs" / "CUJ-001-add-a-task.md").unlink()

        # --- The baseline (found by Checkpoint F) ---------------------------------
        # With no baseline this script diffs the working tree against HEAD, so it cannot
        # tell "the agent edited host code" from "the repo was already dirty". That is
        # fatal for the regression-check use case that /cuj-audit exists to serve: "did
        # my refactor break a journey?" means the tree is dirty with the refactor BY
        # DEFINITION, so the check fires on the user's own work every single run. A check
        # that cries wolf gets muted, and a muted check is a deleted one.
        (repo / "app.tsx").write_text("// the user's own uncommitted refactor\n")
        base = snapshot(repo)

        # 5. Pre-existing dirt belongs to the USER, not to the agent.
        _write_report(repo, "cuj-20260716-120000.md")
        v = changes_confined_to(repo, ".ux/audits/", allow=AUDIT, baseline=base)
        if v:
            failures.append(f"a pre-existing dirty file must not be blamed on the agent: {v}")

        # 6. THE ONE THAT MATTERS, and the reason the baseline is content-addressed
        #    rather than a set of paths. In the primary use case the dirty files ARE the
        #    app files under audit — so "ignore paths that were already dirty" would blind
        #    the check precisely where it must see, letting an agent edit any of them
        #    undetected. That would weaken the invariant SPEC §9.6 calls critical, in
        #    exchange for fixing a false positive. Digests keep both.
        (repo / "app.tsx").write_text("// the user's refactor, SILENTLY EDITED by the agent\n")
        v = changes_confined_to(repo, ".ux/audits/", allow=AUDIT, baseline=base)
        if not any("app.tsx" in x for x in v):
            failures.append(
                f"an agent edit to an ALREADY-DIRTY file must still be flagged: {v}")

        # 7. Restoring the baseline content clears it again (no false positive on churn).
        (repo / "app.tsx").write_text("// the user's own uncommitted refactor\n")
        v = changes_confined_to(repo, ".ux/audits/", allow=AUDIT, baseline=base)
        if v:
            failures.append(f"restoring baseline content should clear the violation: {v}")

        # 8. No baseline => exactly the old behavior. Like `allow`, the baseline is
        #    keyword-only and opt-in: the invariant must never weaken by default, and a
        #    caller that passes nothing gets the strict check it had before.
        v = changes_confined_to(repo, ".ux/audits/", allow=AUDIT)
        if not any("app.tsx" in x for x in v):
            failures.append(f"without a baseline, any dirty file is still a violation: {v}")

        # 9. A file the agent CREATES is never in the baseline, so it is always caught.
        (repo / "sneaky.ts").write_text("// created by the agent mid-audit\n")
        v = changes_confined_to(repo, ".ux/audits/", allow=AUDIT, baseline=base)
        if not any("sneaky.ts" in x for x in v):
            failures.append(f"a file created after the baseline must be flagged: {v}")

    # ---------------------------------------------------------------------------------
    # An authenticated run recommends ignoring `.ux/audits/` wholesale (SPEC §11.6), so
    # from then on the invariant must certify a set `git status` alone cannot see.
    # ---------------------------------------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _init_repo(repo)
        (repo / "node_modules").mkdir()
        (repo / "node_modules" / "index.js").write_text("// vendored\n")
        (repo / ".gitignore").write_text(".ux/audits/\nnode_modules/\n")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-qm", "ignore audits + vendor")

        # 10. The invariant is not vacuous BEFORE the run: nothing written, nothing seen.
        #     This is the assertion that fails if `writes_under` ever silently returns a
        #     constant — without it, case 11 would pass on a broken implementation.
        if writes_under(repo, ".ux/audits/"):
            failures.append("no report written yet, but writes_under saw something")

        _write_report(repo, "usability-20260824-090000.md")

        # 11. THE CASE THIS ALL EXISTS FOR. With the prefix ignored, plain `git status`
        #     is blind to the report, so `changes_confined_to` passes trivially. The run
        #     must still be able to prove it wrote what it claims to have written.
        w = writes_under(repo, ".ux/audits/")
        if not any("usability-20260824-090000.md" in x for x in w):
            failures.append(f"writes under an IGNORED prefix must stay observable: {w}")
        if not any("index.md" in x for x in w):
            failures.append(f"every write under an ignored prefix, not just the first: {w}")
        v = changes_confined_to(repo, ".ux/audits/", allow=AUDIT)
        if v:
            failures.append(f"an ignored prefix is still confined, not a violation: {v}")

        # 12. The regression that guards the obvious-but-wrong fix. Putting `--ignored`
        #     on `_dirty_paths()` would make it see EVERY ignored path in the host repo,
        #     and each one outside the prefix would read as an escape — `node_modules/`
        #     would fail every audit in every normal repo.
        v = changes_confined_to(repo, ".ux/audits/", allow=AUDIT)
        if any("node_modules" in x for x in v):
            failures.append(f"ignored paths OUTSIDE the prefix are not violations: {v}")
        w = writes_under(repo, ".ux/audits/")
        if any("node_modules" in x for x in w):
            failures.append(f"writes_under is pathspec-scoped; node_modules is not ours: {w}")

        # 13. The posture is a RECOMMENDATION, so the un-ignored repo is just as real a
        #     case. Same call, same answer — the auditor cannot know which repo it is in.
        (repo / ".gitignore").write_text("node_modules/\n")
        w = writes_under(repo, ".ux/audits/")
        if not any("usability-20260824-090000.md" in x for x in w):
            failures.append(f"writes must be observable when the prefix is NOT ignored: {w}")

    # ---------------------------------------------------------------------------------
    # The positive half must be reachable from the COMMAND LINE. Every skill's self-check
    # step runs `python3 scripts/audit_safety.py <host-repo>`; a `writes_under()` that only
    # the test suite calls leaves the vacuous pass exactly where it was.
    # ---------------------------------------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _init_repo(repo)
        (repo / ".gitignore").write_text(".ux/audits/\n")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-qm", "ignore audits")

        # 14. THE WIRING CASE. Ignored prefix, nothing written: `changes_confined_to()` is
        #     empty, so the negative half alone would exit 0 and certify a run that did
        #     nothing. The CLI must exit 1.
        if _cli(repo) != 1:
            failures.append("CLI: an ignored prefix + zero writes must NOT exit 0 — "
                            "that is the vacuous pass the positive half exists to close")

        # 15. ...and --allow-no-writes is the deliberate, typed-on-purpose escape hatch,
        #     so a genuinely write-free run is still expressible.
        if _cli(repo, "--allow-no-writes") != 0:
            failures.append("CLI: --allow-no-writes must permit a write-free run")

        # 16. A real report under the ignored prefix satisfies both halves.
        _write_report(repo, "usability-20260824-100000.md")
        if _cli(repo) != 0:
            failures.append("CLI: a report written under an ignored prefix must exit 0")

        # 17. The baseline is what keeps the positive half honest on the SECOND run.
        #     Prior reports linger under an ignored prefix forever, so without content
        #     digests they would answer "were writes observed?" for every later run —
        #     the same vacuity as case 14, one level up. `snapshot()` must therefore see
        #     ignored files, which `_dirty_paths()` alone cannot.
        base = snapshot(repo)
        if not any("usability-20260824-100000.md" in k for k in base):
            failures.append(f"snapshot must digest ignored files under the prefix: {base}")
        if writes_under(repo, ".ux/audits/", baseline=base):
            failures.append("a prior run's report is not THIS run's write")
        _write_report(repo, "usability-20260824-110000.md")
        w = writes_under(repo, ".ux/audits/", baseline=base)
        if not any("usability-20260824-110000.md" in x for x in w):
            failures.append(f"the new report must read as this run's write: {w}")
        if any("usability-20260824-100000.md" in x for x in w):
            failures.append(f"the untouched prior report must not: {w}")

        # 18. The authoring profile writes to `.ux/cujs/`, NOT `.ux/audits/`. Requiring
        #     writes under the default prefix alone would fail every /ux-spec run.
        (repo / ".ux" / "cujs").mkdir(parents=True, exist_ok=True)
        (repo / ".ux" / "cujs" / "checkout.md").write_text("# journey\n")
        if _cli(repo, "--profile", "authoring") != 0:
            failures.append("CLI: authoring writes land in .ux/cujs/ and must satisfy "
                            "the positive half")

    # ---------------------------------------------------------------------------------
    # Paths git C-quotes. The two halves of the union quote DIFFERENT subsets, so without
    # `-z` the same file gets two spellings and neither matches a file on disk.
    # ---------------------------------------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _init_repo(repo)
        awkward = "usability-caf\u00e9 flow-20260824-120000.md"
        for ignored in (True, False):
            (repo / ".gitignore").write_text(".ux/audits/\n" if ignored else "\n")
            _write_report(repo, awkward)
            w = writes_under(repo, ".ux/audits/")
            # 19. The returned path must name a file that actually EXISTS. An escaped
            #     spelling digests to "" via _digest(), so the baseline would forgive it
            #     forever — a silent hole, not a cosmetic one.
            missing = [x for x in w if not (repo / x).exists()]
            if missing:
                failures.append(f"writes_under returned unusable paths "
                                f"(ignored={ignored}): {missing}")
            if not any(x.endswith(awkward) for x in w):
                failures.append(f"a C-quoted path must survive verbatim "
                                f"(ignored={ignored}): {w}")

    if failures:
        print("FAIL — safety:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS — safety (invariant + idempotency + writes_under + CLI wiring)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
