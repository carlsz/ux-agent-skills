#!/usr/bin/env python3
"""Check the plugin's safety invariant: host-repo changes stay where they belong.

This suite is **findings-only**, which means precisely one thing: *it never edits host
application code.* Two profiles express that, and the difference between them is the
whole point of this module.

    audit      → .ux/audits/                       every auditor, unchanged
    authoring  → .ux/audits/, .ux/cujs/, SPEC.md   /ux-spec only

An **auditor** writes reports and nothing else. `/ux-spec` also writes journeys the user
dictated during an interview, and — after asking, showing the diff — splices a generated
index into the host's `SPEC.md`. Those are the user's own words captured through the
agent, not the agent editing their app. Everything outside the active profile is a
violation in both cases.

Widening is **opt-in and explicit**: `allow` is keyword-only, so an allowlist can never
be passed positionally where `prefix` was expected. The audit invariant cannot weaken by
accident — only by someone typing `allow=` on purpose. `baseline` is keyword-only for the
same reason.

    python3 scripts/audit_safety.py <host-repo-dir> --snapshot > base.json   # at run START
    python3 scripts/audit_safety.py <host-repo-dir> [--profile P] [--baseline base.json]

Exit 0 = confined (safe); 1 = a change escaped the profile; 2 = usage/other error.

**Why a baseline exists.** Git tells you the tree differs from HEAD; it does not tell you
*who* made it differ. With no baseline this script must assume the repo was clean when the
agent started, so every pre-existing edit is attributed to the agent. That assumption is
wrong in the case that matters most: "did my refactor break a journey?" means the tree is
dirty with the refactor **by definition**, so `/cuj-audit` would report a violation on the
user's own uncommitted work on every run. A check that cries wolf gets muted, and a muted
check is a deleted one. Take a `--snapshot` at run start and pass it back with
`--baseline`; only the delta is the agent's.

**The baseline is content-addressed, not a path list**, and that distinction is the whole
design. In the scenario above the dirty files ARE the app files under audit, so ignoring
*paths* that were already dirty would blind the check exactly where it must see — an agent
could edit any of them undetected. Digesting content fixes the false positive without
trading away the invariant: a pre-existing edit is forgiven only while its bytes are
unchanged, and the moment the agent touches that same file it is a violation again.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_PREFIX = ".ux/audits/"

# Sentinel for "this path was not in the baseline". Must never compare equal to a real
# digest — which rules out None and "", since "" is exactly what _digest() returns for a
# file that is absent.
_MISSING = object()

# Extra paths each profile permits ON TOP OF `prefix`. Keep `audit` empty: it is the
# baseline every auditor runs under, and an empty tuple is what makes this refactor a
# no-op for them.
EXTRA_BY_PROFILE: dict[str, tuple[str, ...]] = {
    "audit": (),
    "authoring": (".ux/cujs/", "SPEC.md"),
}


def _allowed(path: str, entries: tuple[str, ...]) -> bool:
    """True if `path` is permitted by any allowlist entry.

    A trailing slash means "directory prefix"; a bare entry means "this exact file".
    The distinction is load-bearing. A naive `startswith` would read `"SPEC.md"` as also
    permitting `SPEC.md.bak`, and `".ux/cujs"` as permitting `.ux/cujs-evil/` — an
    allowlist that silently spreads to neighbouring paths is worse than none at all.
    """
    for entry in entries:
        if entry.endswith("/"):
            if path.startswith(entry):
                return True
        elif path == entry:
            return True
    return False


def _dirty_paths(repo: Path) -> list[str]:
    """Every path currently differing from HEAD.

    Uses `git status --porcelain -uall` so untracked files are listed individually
    (a whole new `.ux/` dir would otherwise collapse to one summary line).
    """
    proc = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain", "-uall"],
        check=True, capture_output=True, text=True,
    )
    paths: list[str] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        # Porcelain v1: 2 status chars, a space, then the path (handle "R old -> new").
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path.strip().strip('"'))
    return paths


def _digest(repo: Path, path: str) -> str:
    """Content digest of a working-tree path; "" when it is absent.

    A deleted file digests to "" rather than raising, so that deleting a file that was
    merely *modified* at baseline still reads as a change — which it is.
    """
    try:
        return hashlib.sha256((repo / path).read_bytes()).hexdigest()
    except (FileNotFoundError, IsADirectoryError, OSError):
        return ""


def snapshot(repo: str | Path) -> dict[str, str]:
    """Digest every already-dirty path, for passing back as `baseline`.

    Take this at the START of a run. What it records is "the mess that was already here",
    which is the only way a later check can attribute the rest to the agent.
    """
    repo = Path(repo)
    return {path: _digest(repo, path) for path in _dirty_paths(repo)}


def changes_confined_to(repo: str | Path, prefix: str = DEFAULT_PREFIX, *,
                        allow: tuple[str, ...] = (),
                        baseline: dict[str, str] | None = None) -> list[str]:
    """Return host-repo paths changed OUTSIDE `prefix` (plus `allow`); [] = invariant holds.

    `allow` and `baseline` are keyword-only by design — see the module docstring. Callers
    that pass only `prefix` get exactly the behavior they had before either existed.

    `baseline` (from `snapshot()`) forgives dirt that was already present when the run
    started — but only while its content is byte-identical. Touch a pre-existing dirty
    file and it is a violation again. `baseline=None` assumes the repo started clean,
    which is the strict reading and stays the default.
    """
    repo = Path(repo)
    permitted = (prefix, *allow)
    violations: list[str] = []
    for path in _dirty_paths(repo):
        if _allowed(path, permitted):
            continue
        if baseline is not None and baseline.get(path, _MISSING) == _digest(repo, path):
            continue  # already dirty at run start, and untouched since
        violations.append(path)
    return violations


USAGE = """usage:
  audit_safety.py <host-repo-dir> --snapshot                  record pre-existing dirt
  audit_safety.py <host-repo-dir> [--profile audit|authoring] [--baseline <file>]

Profiles — paths the agent is permitted to have touched:
  audit      .ux/audits/                       every auditor (default)
  authoring  .ux/audits/, .ux/cujs/, SPEC.md   /ux-spec only

Baseline — who made the mess:
  Git says the tree differs from HEAD; it cannot say who made it differ. Without a
  baseline this assumes the repo started clean, so a dirty working tree reads as an
  agent violation. Take --snapshot at run START and pass it back with --baseline:

    audit_safety.py <repo> --snapshot > /tmp/base.json     # before the run
    audit_safety.py <repo> --baseline /tmp/base.json       # after the run

  Only the delta is the agent's. Pre-existing dirt is forgiven while its content is
  unchanged — touch one of those files and it is a violation again.

Exit 0 = confined (safe), 1 = a change escaped the profile, 2 = usage."""


def main(argv: list[str]) -> int:
    args = list(argv)
    if not args or args[0] in ("-h", "--help", "help"):
        # Without this, `--help` is passed to `git -C --help status` and the user gets a
        # raw CalledProcessError traceback from a script whose whole job is reassurance.
        # Explicit --help is a successful request for help (0); a bare
        # invocation is a usage error (2). They are not the same thing.
        print(USAGE, file=sys.stdout if args else sys.stderr)
        return 0 if args else 2

    profile = "audit"
    if "--profile" in args:
        i = args.index("--profile")
        if i + 1 >= len(args):
            print(USAGE, file=sys.stderr)
            return 2
        profile = args[i + 1]
        del args[i:i + 2]

    take_snapshot = "--snapshot" in args
    if take_snapshot:
        args.remove("--snapshot")

    baseline: dict[str, str] | None = None
    baseline_path: str | None = None
    if "--baseline" in args:
        i = args.index("--baseline")
        if i + 1 >= len(args):
            print(USAGE, file=sys.stderr)
            return 2
        baseline_path = args[i + 1]
        del args[i:i + 2]

    if take_snapshot and baseline_path is not None:
        print("--snapshot records a baseline; --baseline consumes one. Pick one.\n",
              file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 2

    if len(args) != 1 or profile not in EXTRA_BY_PROFILE:
        if profile not in EXTRA_BY_PROFILE:
            print(f"unknown profile {profile!r} — expected one of "
                  f"{sorted(EXTRA_BY_PROFILE)}\n", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 2

    repo = Path(args[0])
    if not (repo / ".git").exists():
        # Better than letting `git -C` fail with a raw traceback three frames deep.
        print(f"not a git repository: {repo}\n", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 2

    if take_snapshot:
        json.dump(snapshot(repo), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    if baseline_path is not None:
        try:
            baseline = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            # Never fall back to baseline=None here. That would silently re-enable the
            # strict check and blame the user's own dirt on the agent — the exact
            # false positive the baseline exists to remove, reappearing as a typo'd path.
            print(f"could not read baseline {baseline_path!r}: {exc}\n", file=sys.stderr)
            print(USAGE, file=sys.stderr)
            return 2

    allow = EXTRA_BY_PROFILE[profile]
    permitted = ", ".join((DEFAULT_PREFIX, *allow))
    scope = "since baseline" if baseline is not None else "vs HEAD, assuming a clean start"

    violations = changes_confined_to(args[0], allow=allow, baseline=baseline)
    if violations:
        print(f"SAFETY VIOLATION — changes outside {permitted} "
              f"(profile: {profile}; {scope}):", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        if baseline is None:
            print("\nIf the repo was already dirty before the run, this may be the "
                  "user's own work rather than the agent's — re-run with a --snapshot "
                  "taken at run start to tell them apart.", file=sys.stderr)
        return 1
    print(f"safe: all changes confined to {permitted} (profile: {profile}; {scope})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
