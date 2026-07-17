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
accident — only by someone typing `allow=` on purpose.

    python3 scripts/audit_safety.py <host-repo-dir> [--profile audit|authoring]

Exit 0 = confined (safe); 1 = a change escaped the profile; 2 = usage/other error.

Note: this measures the *agent's* footprint. If live mode required a user-authorized
setup step (e.g. `npm install`, which can touch a lockfile), commit or revert that before
checking, or the setup side-effect will show up here — it is not an audit write.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

DEFAULT_PREFIX = ".ux/audits/"

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


def changes_confined_to(repo: str | Path, prefix: str = DEFAULT_PREFIX, *,
                        allow: tuple[str, ...] = ()) -> list[str]:
    """Return host-repo paths changed OUTSIDE `prefix` (plus `allow`); [] = invariant holds.

    `allow` is keyword-only by design — see the module docstring. Callers that pass only
    `prefix` get exactly the behavior they had before profiles existed.

    Uses `git status --porcelain -uall` so untracked files are listed individually
    (a whole new `.ux/` dir would otherwise collapse to one summary line).
    """
    repo = Path(repo)
    proc = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain", "-uall"],
        check=True, capture_output=True, text=True,
    )
    permitted = (prefix, *allow)
    violations: list[str] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        # Porcelain v1: 2 status chars, a space, then the path (handle "R old -> new").
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = path.strip().strip('"')
        if not _allowed(path, permitted):
            violations.append(path)
    return violations


USAGE = """usage:
  audit_safety.py <host-repo-dir> [--profile audit|authoring]

Profiles — paths the agent is permitted to have touched:
  audit      .ux/audits/                       every auditor (default)
  authoring  .ux/audits/, .ux/cujs/, SPEC.md   /ux-spec only

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

    allow = EXTRA_BY_PROFILE[profile]
    permitted = ", ".join((DEFAULT_PREFIX, *allow))

    violations = changes_confined_to(args[0], allow=allow)
    if violations:
        print(f"SAFETY VIOLATION — changes outside {permitted} (profile: {profile}):",
              file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return 1
    print(f"safe: all changes confined to {permitted} (profile: {profile})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
