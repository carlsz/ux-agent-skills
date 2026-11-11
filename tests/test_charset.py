#!/usr/bin/env python3
"""Charset guard: no foreign-script letters, no invisible characters, anywhere.

This suite's product is prose. The personas' instructions ARE the auditor's behavior,
so a stray character in `agents/*.md` ships as a defect in the thing we sell, and the
other tests cannot see it: they assert that phrases they were TOLD about are present
(`test_components.py`) or that links resolve (`test_docs.py`). Neither can notice a
character nobody meant to type. Two classes are checkable mechanically:

* **Foreign-script letters** — a word from another writing system, or a
  homoglyph: a Cyrillic lookalike standing in for a Latin `a`. These come from
  generation slips and from paste, and review cannot see a lookalike at all.
* **Invisible and format characters** — zero-width spaces, non-breaking spaces, a BOM
  mid-file, and the bidirectional overrides of Trojan Source (CVE-2021-42574), which can
  make source read one way and execute another. No review catches these by eye; only a
  scan does.

The rule is **category-based, not an enumerated allowlist**: flag Unicode letters
(`L*`) and invisible/format characters (`Cf`/`Zs`/`Cc`), and leave every visible symbol
alone. The repo's prose legitimately uses 40 distinct non-ASCII glyphs — em dashes, box
drawing, `§`, `≥`, arrows, emoji — and an enumeration would need editing every time
prose grew a new one, which is how a guard becomes a nuisance and then gets deleted.
Variation selectors (`Mn`, e.g. U+FE0F after an emoji) are deliberately out of scope:
they are invisible but meaningless alone, and only appear paired with a visible glyph.

**This globs `git ls-files`.** Unlike `DOC_FILES` in `test_docs.py`, a hardcoded list
would defeat the point — the whole value here is covering the file nobody thought to
list, including one a future component adds.

Run: `python3 tests/test_charset.py` (exit 0 = pass, 1 = fail).
"""
from __future__ import annotations

import subprocess
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Suffixes whose bytes are not text. `UnicodeDecodeError` is the real backstop; this
# just avoids reading megabytes of PNG to discover that.
BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf",
    ".woff", ".woff2", ".ttf", ".otf", ".zip", ".gz",
}

# Invisible characters that are deliberate, as `U+XXXX: reason` — empty on purpose, and
# kept present for the same reason `EXTRA_BY_PROFILE["audit"]` stays `()` in
# `audit_safety.py`: the empty collection documents that the exception was considered.
# Adding one is a conscious act with a reason attached, not a quiet widening.
ALLOWED_INVISIBLE: dict[str, str] = {}

# Foreign-script letters that are deliberate (an i18n fixture, say). Also empty, also
# on purpose: today every component is English, and that is worth asserting.
ALLOWED_LETTERS: dict[str, str] = {}

# Tab, newline, carriage return and the plain space are ASCII and never flagged.
_ASCII_WHITESPACE = "\t\n\r "


def _describe(ch: str) -> str:
    return f"U+{ord(ch):04X} {unicodedata.name(ch, 'unnamed')}"


def scan_text(label: str, text: str) -> list[str]:
    """Return one finding per offending character, with file:line:col and its name."""
    findings: list[str] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for col, ch in enumerate(line, 1):
            if ord(ch) < 128:
                continue
            category = unicodedata.category(ch)
            if category.startswith("L"):
                if ch in ALLOWED_LETTERS:
                    continue
                findings.append(
                    f"{label}:{lineno}:{col} foreign-script letter {_describe(ch)} "
                    f"— a slip or a homoglyph; use the ASCII letter"
                )
            elif category in ("Cf", "Zs", "Cc") and ch not in _ASCII_WHITESPACE:
                if ch in ALLOWED_INVISIBLE:
                    continue
                findings.append(
                    f"{label}:{lineno}:{col} invisible character {_describe(ch)} "
                    f"— renders as nothing; delete it"
                )
    return findings


def tracked_text_files() -> list[Path]:
    """Every tracked file whose bytes decode as UTF-8 text."""
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        capture_output=True, text=True, check=True,
    ).stdout
    paths = []
    for name in out.split("\0"):
        if not name:
            continue
        path = ROOT / name
        if path.suffix.lower() in BINARY_SUFFIXES or not path.is_file():
            continue
        paths.append(path)
    return paths


def _self_check() -> list[str]:
    """Prove the scanner fires, so a green run means "clean", not "never looked".

    Same discipline as `test_safety.py` asserting through `audit_safety.main()`: a guard
    whose own firing is untested can rot into a no-op while the suite stays green.

    The offending characters are built with `chr()` from code points — not as literals,
    and not as `\\u` escapes either. This file is itself scanned once tracked, so a
    literal character here would make the guard fail on its own source; and an escape
    sequence is no safer, because it has a literal form to collapse into. That is exactly
    what happened when this file was first written: the escapes were emitted as the
    characters they denote, the self-check still passed (same runtime string), and only
    scanning this file revealed it. `chr(0x434)` has no literal form. Do not "simplify".
    """
    failures: list[str] = []
    cyrillic = "".join(chr(c) for c in (0x434, 0x43E, 0x43B, 0x436, 0x435, 0x43D))
    zero_width = "finding" + chr(0x200B) + "walkthrough"
    nbsp = "P0" + chr(0x00A0) + "blocks"
    bidi_override = "amount = 100" + chr(0x202E)  # Trojan Source: right-to-left override
    homoglyph = "us" + chr(0x430) + "bility"      # Cyrillic a, visually identical

    for name, sample, want in (
        ("a foreign-script word", cyrillic, 6),
        ("a homoglyph in an English word", homoglyph, 1),
        ("a zero-width space", zero_width, 1),
        ("a non-breaking space", nbsp, 1),
        ("a bidi override", bidi_override, 1),
    ):
        got = len(scan_text("<self-check>", sample))
        if got != want:
            failures.append(
                f"self-check: {name} should yield {want} finding(s), got {got} — "
                f"the scanner is not catching what this guard exists to catch"
            )

    # The other half: the deliberate glyphs this repo's prose uses must stay unflagged,
    # or the guard becomes a nuisance and gets deleted.
    deliberate = "An em dash, a section sign, an inequality and a tick: "
    deliberate += chr(0x2014) + chr(0x00A7) + chr(0x2265) + chr(0x2705) + chr(0x2502)
    noisy = scan_text("<self-check>", deliberate)
    if noisy:
        failures.append(f"self-check: deliberate visible punctuation was flagged: {noisy}")
    return failures


def main() -> int:
    failures = _self_check()

    files = tracked_text_files()
    if not files:
        failures.append("no tracked text files found — the glob is broken, not the repo clean")

    scanned = 0
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # genuinely binary despite its suffix
        scanned += 1
        failures += scan_text(str(path.relative_to(ROOT)), text)

    if failures:
        print("FAIL — charset:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"PASS — charset ({scanned} tracked text files, no foreign letters or invisibles)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
