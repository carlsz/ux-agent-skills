#!/usr/bin/env python3
"""Render a `.ux/audits` report (Markdown) into a self-contained HTML companion.

The Markdown report is the source of truth; this is a **derived view** — the report
contract, `validate_report.py`, `index.md`, and the roll-up are unaffected. Output is a
single `<stem>.html` written beside the `<stem>.md`, with **everything inlined**: CSS, and
every `./assets/*` image base64-embedded as a `data:` URI, so the file opens offline from
disk with no network access.

Design notes:
- Parsing helpers are **reused** from `validate_report.py` (one source of truth for the
  frontmatter split and the finding/​walkthrough/​image shapes).
- Output is **deterministic**: identical input (report + assets) yields byte-identical HTML,
  so re-rendering an unchanged report produces no diff churn. No timestamps, no randomness.

Usage:
    python3 scripts/render_report_html.py <report.md> [<report.md> ...]

Exit code 0 = all rendered; 1 = at least one failed (message on stderr).

Scope: Phase 0 — frontmatter header, severity bar, generic section rendering, and findings
as severity-badged cards with inline Evidence images. The `## Walkthrough` flipbook, the
cuj verified-pass banner, the roll-up dashboard, and `--index` land in later phases.
"""
from __future__ import annotations

import base64
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_report import (  # noqa: E402
    _split_frontmatter, is_rollup, PRIORITY_KEYS, derive_verdict,
)

# --- priority vocabulary (mirrors the report contract §4) --------------------------------

PRI_LABELS = {0: "Blocking", 1: "Major", 2: "Minor", 3: "Polish"}
PRI_ACTIONS = {0: "Fix immediately", 1: "Fix before release",
               2: "Fix in the next pass", 3: "Fix if time allows"}
PRI_ORDER = [0, 1, 2, 3]

# --- inline markdown ---------------------------------------------------------------------

IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")

IMAGE_MIME = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml",
}

# The five labelled fields of a finding block (report contract §5). `Severity` is the
# schema-2 spelling of the field schema 3 renamed to `Priority`: it stays in the pattern
# because reports are append-only history, and it must stay in BOTH alternations — a name
# missing from the lookahead does not merely go unrendered, it gets swallowed into the
# preceding field's value, which is how `Priority` silently vanished from every card.
#
# The leading `- ` is OPTIONAL, and that is not politeness. Contract §5 introduces the five
# fields as a markdown bullet list, which reads equally as "these are the fields" and as
# "this is the markup", so auditors split on it: of three real reports written against §5,
# the cuj one bulleted its fields and the usability and accessibility ones wrote bare bold
# paragraphs. The validator checks field presence with a substring test, so a bare-bold
# report is *contract-valid* — and with a mandatory `- ` here it rendered as a finding card
# with a completely empty body: no prose, no apparatus rail, no evidence, no fix. Silent
# total loss on a valid document. Read both forms; §5 now states the canonical one.
_FIELD_NAMES = (r"Issue Description|Framework Violation|Priority|Severity|Evidence|"
                r"Recommended Fix")
FINDING_FIELD_RE = re.compile(
    rf"^[ \t]*(?:[-*+][ \t]+)?\*\*({_FIELD_NAMES}):\*\*"
    rf"\s*(.*?)(?=\n[ \t]*(?:[-*+][ \t]+)?\*\*(?:{_FIELD_NAMES}):\*\*|\Z)",
    re.DOTALL | re.MULTILINE,
)


def _embed_asset(report_dir: Path, path: str) -> str | None:
    """Return a `data:` URI for a local image under the report dir, else None.

    Only local relative image files are inlined. External URLs, `data:` URIs, non-image
    extensions (e.g. a trace `.json`), and missing files all return None so the caller can
    degrade gracefully instead of emitting an external reference.
    """
    path = path.strip()
    if path.startswith(("http://", "https://", "data:", "//")):
        return None
    resolved = (report_dir / path).resolve()
    mime = IMAGE_MIME.get(resolved.suffix.lower())
    if mime is None or not resolved.is_file():
        return None
    b64 = base64.b64encode(resolved.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _img_html(alt: str, path: str, report_dir: Path) -> str:
    uri = _embed_asset(report_dir, path)
    if uri is not None:
        cap = html.escape(alt) if alt else ""
        figcap = f"<figcaption>{cap}</figcaption>" if cap else ""
        return f'<figure class="shot"><img alt="{html.escape(alt)}" src="{uri}">{figcap}</figure>'
    label = html.escape(alt or path)
    return f'<span class="missing" title="{html.escape(path)}">🖼 {label} — not embedded</span>'


def _inline(text: str, report_dir: Path) -> str:
    """Render inline Markdown (images, code, links, bold) to safe HTML.

    Images / code / links are rendered first and stashed behind sentinels so their content
    is not re-escaped; the remaining text is HTML-escaped; bold is applied last.
    """
    tokens: list[str] = []

    def stash(rendered: str) -> str:
        tokens.append(rendered)
        return f"\x00{len(tokens) - 1}\x00"

    text = IMG_RE.sub(lambda m: stash(_img_html(m.group(1), m.group(2), report_dir)), text)
    text = CODE_RE.sub(lambda m: stash(f"<code>{html.escape(m.group(1))}</code>"), text)
    text = LINK_RE.sub(
        lambda m: stash(
            f'<a href="{html.escape(m.group(2).strip())}">{html.escape(m.group(1))}</a>'
        ),
        text,
    )
    text = html.escape(text)
    text = BOLD_RE.sub(lambda m: f"<strong>{m.group(1)}</strong>", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: tokens[int(m.group(1))], text)
    return text


# --- block markdown ----------------------------------------------------------------------

SECTION_RE = re.compile(r"^##\s+(.*)$", re.MULTILINE)
ORDERED_RE = re.compile(r"^\d+\.\s")


def _render_table(rows: list[str], report_dir: Path) -> str:
    def cells(row: str) -> list[str]:
        return [c.strip() for c in row.strip().strip("|").split("|")]

    header: list[str] | None = None
    body: list[list[str]] = []
    for row in rows:
        parsed = cells(row)
        if parsed and all(set(c) <= set("-: ") for c in parsed):
            continue  # separator
        if header is None:
            header = parsed
        else:
            body.append(parsed)

    out = ['<table>']
    if header:
        out.append("<thead><tr>" + "".join(
            f"<th>{_inline(c, report_dir)}</th>" for c in header) + "</tr></thead>")
    out.append("<tbody>")
    for row in body:
        out.append("<tr>" + "".join(f"<td>{_inline(c, report_dir)}</td>" for c in row) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


# A line that continues the list item above it rather than starting anything of its own.
_BLOCK_START = ("|", "#", ">", "- ", "* ")


def _list_items(lines: list[str], i: int, starts, strip_marker) -> tuple[list[str], int]:
    """Collect a run of list items, folding hard-wrapped continuation lines into their item.

    These reports are wrapped at ~95 columns, so most list items span two or three source
    lines. Treating every line as its own item split one list into several, each restarting
    at `1.`, with the wrapped remainder stranded as a paragraph between them — a rendering
    that contradicted the document it came from.
    """
    items: list[str] = []
    while i < len(lines):
        stripped = lines[i].strip()
        if starts(stripped):
            items.append(strip_marker(stripped)); i += 1
            continue
        # A continuation: indented or not, it belongs to the item above.
        if items and stripped and not stripped.startswith(_BLOCK_START) \
                and not ORDERED_RE.match(stripped):
            items[-1] += " " + stripped; i += 1
            continue
        break
    return items, i


def _render_blocks(text: str, report_dir: Path) -> str:
    """Render a chunk of Markdown (paragraphs, lists, tables, quotes, sub-headings)."""
    lines = text.splitlines()
    out: list[str] = []
    para: list[str] = []
    i = 0

    def flush() -> None:
        if para:
            out.append(f"<p>{_inline(' '.join(para).strip(), report_dir)}</p>")
            para.clear()

    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            flush(); i += 1; continue
        if stripped.startswith("|"):
            flush()
            table: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table.append(lines[i]); i += 1
            out.append(_render_table(table, report_dir)); continue
        if stripped.startswith("#### "):
            flush(); out.append(f"<h4>{_inline(stripped[5:], report_dir)}</h4>"); i += 1; continue
        if stripped.startswith("### "):
            flush(); out.append(f"<h3>{_inline(stripped[4:], report_dir)}</h3>"); i += 1; continue
        if stripped.startswith(">"):
            flush()
            quote: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip()); i += 1
            out.append(f"<blockquote>{_inline(' '.join(quote), report_dir)}</blockquote>"); continue
        if stripped.startswith(("- ", "* ")):
            flush()
            items, i = _list_items(lines, i, lambda s: s.startswith(("- ", "* ")),
                                   lambda s: s[2:])
            out.append("<ul>" + "".join(
                f"<li>{_inline(it, report_dir)}</li>" for it in items) + "</ul>"); continue
        if ORDERED_RE.match(stripped):
            flush()
            items, i = _list_items(lines, i, lambda s: bool(ORDERED_RE.match(s)),
                                   lambda s: ORDERED_RE.sub("", s))
            out.append("<ol>" + "".join(
                f"<li>{_inline(it, report_dir)}</li>" for it in items) + "</ol>"); continue
        para.append(stripped); i += 1

    flush()
    return "\n".join(out)


# --- findings ----------------------------------------------------------------------------

# `validate_report.FINDING_RE` is schema-3 only, by design: a freshly written report must
# use `[PN]`. The RENDERER has to be read-tolerant in the same way it is for the `Severity`
# field name, because every report written before schema 3 tags its findings `[sev4]`..
# `[sev1]` — and a renderer that cannot see them publishes those reports with their
# findings section reading "No findings", which is the worst thing this file could say.
ANY_FINDING_RE = re.compile(r"^###\s+\[(?:P([0-3])|sev([1-4]))\]", re.MULTILINE | re.IGNORECASE)
ANY_TAG_RE = re.compile(r"^###\s+\[(?:P[0-3]|sev[1-4])\]\s*", re.MULTILINE | re.IGNORECASE)
# sev4 -> P0, sev3 -> P1, sev2 -> P2, sev1 -> P3 (contract §4's migration map).
SEV_TO_PRI = {4: 0, 3: 1, 2: 2, 1: 3}


def _parse_findings(body: str) -> list[dict]:
    matches = list(ANY_FINDING_RE.finditer(body))
    findings: list[dict] = []
    for idx, m in enumerate(matches):
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        block = body[start:end]
        newline = block.find("\n")
        heading = block[:newline] if newline != -1 else block
        title = ANY_TAG_RE.sub("", heading).strip()
        fields = {name: val.strip() for name, val in FINDING_FIELD_RE.findall(block)}
        p = int(m.group(1)) if m.group(1) is not None else SEV_TO_PRI[int(m.group(2))]
        findings.append({"p": p, "title": title, "fields": fields})
    return findings


def _split_media(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Separate inline images from the prose around them.

    `Evidence` routinely holds both halves of the apparatus in one blob: a screenshot embed
    and a `file:line` citation. The citation belongs in the rail and the screenshot does
    not — at 204px it would be a thumbnail of nothing — so they are split and placed
    separately. Punctuation left stranded by the removed embed is tidied up.
    """
    media = [(m.group(1), m.group(2).strip()) for m in IMG_RE.finditer(text)]
    rest = IMG_RE.sub("", text)
    rest = re.sub(r"[ \t]+", " ", rest)
    rest = re.sub(r"\s+([;,.])", r"\1", rest)
    rest = re.sub(r"([;,])\s*(?=[;,.])", "", rest)
    rest = rest.strip().strip(";,").strip()
    return rest, media


CODE_SPAN_RE = re.compile(r"(<code>)(.*?)(</code>)", re.DOTALL)


def _wbr_paths(markup: str) -> str:
    """Give `file:line` citations somewhere sensible to break inside the 204px rail.

    A path is one unbreakable token, so the rail either overflows or breaks it mid-word
    (`PlaceOrderB / utton.tsx:42`). `<wbr>` offers the separators as break opportunities,
    which the browser takes only when it has to — so a citation that fits stays on one line
    and one that does not breaks at a `/` instead of mid-identifier.
    """
    return CODE_SPAN_RE.sub(
        lambda m: m.group(1) + m.group(2).replace("/", "/<wbr>").replace("_", "_<wbr>")
        + m.group(3), markup)


RAIL_FIELDS = (
    # (source field names, rail label) — the apparatus, in the order it is read: what rule
    # was broken, where to look, why it was graded the way it was.
    (("Framework Violation",), "Framework"),
    (("Evidence",), "Source"),
    (("Priority", "Severity"), "Why this grade"),
)


def _render_findings(body: str, report_dir: Path) -> str:
    """Findings as cards, each with a permanent apparatus rail beside its prose.

    The rail is the design's one structural commitment: the framework citation, the source
    location and the grading rationale occupy their own column on every card, so the expert
    apparatus is prominent by *position* rather than by colour or weight. That is what lets
    it stay at full strength — a reader skimming the prose cannot miss it, and a reader
    checking the work does not have to hunt for it.
    """
    findings = _parse_findings(body)
    if not findings:
        return '<p class="none">No findings.</p>'
    cards: list[str] = []
    for f in findings:
        n, fields = f["p"], f["fields"]
        media: list[tuple[str, str]] = []

        rail: list[str] = []
        for keys, label in RAIL_FIELDS:
            key = next((k for k in keys if k in fields), None)
            if key is None:
                continue
            text, imgs = _split_media(fields[key])
            media += imgs
            if not text:
                continue
            rail.append(f"<div><dt>{label}</dt>"
                        f"<dd>{_wbr_paths(_render_blocks(text, report_dir))}</dd></div>")

        prose: list[str] = []
        issue, issue_imgs = _split_media(fields.get("Issue Description", ""))
        media += issue_imgs
        if issue:
            prose.append(_render_blocks(issue, report_dir))
        fix, fix_imgs = _split_media(fields.get("Recommended Fix", ""))
        media += fix_imgs
        if fix:
            prose.append(f'<div class="fix"><span class="k">Recommended fix &middot; '
                         f"{PRI_ACTIONS[n]}</span>{_render_blocks(fix, report_dir)}</div>")
        for alt, path in media:
            prose.append(_img_html(alt, path, report_dir))
        # A legacy card missing both prose fields still shows its apparatus rather than an
        # empty column: the rail becomes the card.
        if not prose and rail:
            body_html = f'<div class="find-body norail"><dl class="rail flat">{"".join(rail)}</dl></div>'
        else:
            rail_html = f'<dl class="rail">{"".join(rail)}</dl>' if rail else ""
            cls = "find-body" if rail else "find-body norail"
            body_html = (f'<div class="{cls}">{rail_html}'
                         f'<div class="prose">{"".join(prose)}</div></div>')

        cards.append(
            f'<article class="finding p{n}">'
            f'<div class="find-head"><span class="chip p{n}">P{n} {PRI_LABELS[n]}</span>'
            f"<h3>{_inline(f['title'], report_dir)}</h3></div>"
            f"{body_html}</article>")
    return "\n".join(cards)


# --- walkthrough flipbook ----------------------------------------------------------------

FRAME_RE = re.compile(r"^###\s+(.*)$", re.MULTILINE)
CUJ_PREFIX_RE = re.compile(r"^(CUJ-\d+)\s*[·:—\-]*\s*", re.IGNORECASE)


def _embed_img_tag(alt: str, path: str, report_dir: Path) -> str:
    uri = _embed_asset(report_dir, path)
    if uri is not None:
        return f'<img alt="{html.escape(alt)}" src="{uri}">'
    return f'<div class="missing">🖼 {html.escape(alt or path)} — not embedded</div>'


def _parse_walkthrough(content: str) -> tuple[str, list[dict]]:
    """Split a `## Walkthrough` body into an intro + ordered frames.

    Each `### <heading>` is a frame: its heading (the caption title), the first inline
    image, and any `>` blockquote (the expected-vs-observed line). A `CUJ-00x` prefix on the
    heading groups the frame under that journey; headings without one form a single group.
    """
    matches = list(FRAME_RE.finditer(content))
    intro = (content[:matches[0].start()] if matches else content).strip()
    frames: list[dict] = []
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        block = content[start:end]
        img = IMG_RE.search(block)
        alt, path = (img.group(1), img.group(2).strip()) if img else ("", "")
        caption = " ".join(
            ln.strip().lstrip(">").strip()
            for ln in block.splitlines() if ln.strip().startswith(">")
        )
        gm = CUJ_PREFIX_RE.match(title)
        gkey = gm.group(1).upper() if gm else None
        ftitle = CUJ_PREFIX_RE.sub("", title).strip() if gm else title
        frames.append({"gkey": gkey, "title": ftitle, "alt": alt, "path": path,
                       "caption": caption})
    return intro, frames


def _render_flipbook(label: str | None, frames: list[dict], report_dir: Path) -> str:
    slides = []
    for idx, f in enumerate(frames):
        active = " is-active" if idx == 0 else ""
        cap_title = f"<b>{html.escape(f['title'])}</b>" if f["title"] else ""
        cap_body = f" {_inline(f['caption'], report_dir)}" if f["caption"] else ""
        slides.append(
            f'<figure class="frame{active}">{_embed_img_tag(f["alt"], f["path"], report_dir)}'
            f"<figcaption>{cap_title}{cap_body}</figcaption></figure>"
        )
    label_html = (
        f'<div class="flip-label">{html.escape(label)}</div>' if label else ""
    )
    controls = ""
    if len(frames) > 1:
        dots = "".join(
            f'<button class="dot{" is-active" if i == 0 else ""}" data-i="{i}" '
            f'aria-label="Go to frame {i + 1}"></button>'
            for i in range(len(frames))
        )
        controls = (
            '<div class="flip-nav">'
            '<button class="prev" aria-label="Previous frame">&lsaquo;</button>'
            f'<span class="counter">1 / {len(frames)}</span>'
            '<button class="next" aria-label="Next frame">&rsaquo;</button></div>'
            f'<div class="dots">{dots}</div>'
        )
    return (
        f'<div class="flip" tabindex="0">{label_html}'
        f'<div class="frames">{"".join(slides)}</div>{controls}</div>'
    )


def _render_walkthrough(content: str, report_dir: Path) -> str:
    intro, frames = _parse_walkthrough(content)
    if not frames:
        return _render_blocks(content, report_dir)
    groups: list[tuple[str | None, list[dict]]] = []
    for f in frames:
        if groups and groups[-1][0] == f["gkey"]:
            groups[-1][1].append(f)
        else:
            groups.append((f["gkey"], [f]))
    parts: list[str] = []
    if intro:
        parts.append(_render_blocks(intro, report_dir))
    for label, gframes in groups:
        parts.append(_render_flipbook(label, gframes, report_dir))
    return "\n".join(parts)


# --- the brief (verdict / worst priority, health ring, counts, lead) --------------------

# `sev4: n` -> `p0: n`, and so on. Every report written before schema 3 counts on the old
# scale, and the brief is built entirely out of these counts — without the translation a
# historical report renders with no lockup, no chips and no total, which reads as "nothing
# found" rather than "written under the previous contract".
LEGACY_COUNT_KEYS = {"sev4": "p0", "sev3": "p1", "sev2": "p2", "sev1": "p3"}


def _summary_of(fm: dict) -> dict:
    """The per-priority counts, read tolerantly: both spellings of the key and the scale.

    §9 specifies `summary:`. Roll-ups written before it also used `totals:`. Reports older
    than schema 3 count in `sevN`. All of them are read here so a historical report renders
    its real numbers instead of a row of zeros — the same read-tolerant/write-strict split
    the validator keeps on the other side (it rejects every one of these on write).
    """
    for key in ("summary", "totals"):
        value = fm.get(key)
        if not isinstance(value, dict) or not value:
            continue
        if any(k in value for k in PRIORITY_KEYS):
            return value
        mapped = {LEGACY_COUNT_KEYS[k]: v for k, v in value.items()
                  if k in LEGACY_COUNT_KEYS and isinstance(v, int)}
        if mapped:
            total = value.get("total")
            return {**mapped, "total": total if isinstance(total, int) else sum(mapped.values())}
        return value
    return {}


def _has_counts(summary: dict) -> bool:
    return any(k in summary for k in PRIORITY_KEYS)


def _total_of(summary: dict) -> int:
    """`total` as written, or derived from the per-priority counts when absent.

    Never defaults to 0: a zero is not a neutral placeholder here, it asserts "nothing
    found" over a document that may list five issues.
    """
    total = summary.get("total")
    if isinstance(total, int):
        return total
    return sum(v for k in PRIORITY_KEYS if isinstance(v := summary.get(k), int))


def _live_counts(summary: dict) -> list[tuple[int, int]]:
    """The non-zero priority counts, worst first. Zeros are suppressed, not dimmed.

    Four cells reading `0` crowd out the one reading `2` and leave the eye to find the
    signal; the brief shows only what was actually found.
    """
    return [(n, c) for n in PRI_ORDER if isinstance(c := summary.get(f"p{n}"), int) and c]


def _worst(summary: dict) -> int | None:
    live = _live_counts(summary)
    return live[0][0] if live else None


def _cuj_verified(fm: dict) -> bool:
    """Whether a `cuj` report's `total: 0` is a verified pass or a run that proved nothing.

    `total: 0` is this auditor's success state and is byte-identical to an all-skipped run.
    The frameworks are the discriminator: `task-completion` + `success-criteria` mean
    journeys were completed and graded; `cuj-contract` alone means nothing was verified.
    """
    return bool({"task-completion", "success-criteria"} & set(fm.get("frameworks") or []))


def _ring(pct: int, band: str, size: int = 78) -> str:
    """The health score as a dial. Deterministic — fixed geometry, no randomness."""
    r = (size - 9) / 2
    circ = 2 * 3.141592653589793 * r
    on = circ * max(0, min(100, pct)) / 100
    mid = size / 2
    label = f"Health score {pct} out of 100, {band}" if band else f"Health score {pct} out of 100"
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" role="img" '
            f'aria-label="{html.escape(label)}">'
            f'<circle cx="{mid}" cy="{mid}" r="{r}" fill="none" stroke="var(--line)" '
            f'stroke-width="7"/>'
            f'<circle cx="{mid}" cy="{mid}" r="{r}" fill="none" stroke="var(--teal)" '
            f'stroke-width="7" stroke-linecap="round" stroke-dasharray="{on:.1f} {circ:.1f}" '
            f'transform="rotate(-90 {mid} {mid})"/>'
            f'<text x="50%" y="50%" text-anchor="middle" dy=".35em" font-size="21" '
            f'font-weight="600" fill="currentColor" '
            f'font-family="Optima,Candara,system-ui">{pct}</text></svg>')


def _trend_svg(vals: list[int], w: int = 108, h: int = 26) -> str:
    """A sparkline of prior runs. Only the roll-up carries `trend`, and it may be empty."""
    if len(vals) < 2:
        return ""
    lo, hi = min(vals) - 4, max(vals) + 4
    span = (hi - lo) or 1
    step = w / (len(vals) - 1)
    pts = " ".join(f"{i * step:.1f},{h - (v - lo) / span * h:.1f}" for i, v in enumerate(vals))
    joined = ", ".join(str(v) for v in vals)
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="Health over the previous {len(vals)} runs: {joined}">'
            f'<polyline points="{pts}" fill="none" stroke="var(--teal)" stroke-width="1.6" '
            f'opacity=".8"/></svg>')


def _health_dial(fm: dict) -> str:
    """The ring + band + trend cluster, or nothing when there is no scorecard to show."""
    health = fm.get("health") or {}
    pct, band = health.get("pct"), str(health.get("band", ""))
    if pct is None:
        if not band:
            return ""
        # A run with nothing gradable states that instead of drawing a dial at 0 or 100.
        return (f'<div class="ring"><div><div class="b">{html.escape(band)}</div>'
                f'<div class="t">no gradable item was reached</div></div></div>')
    trend = [v for v in (health.get("trend") or []) if isinstance(v, int)]
    trend_html = (f'{_trend_svg(trend)}<div class="t">previous {len(trend)} runs</div>'
                  if len(trend) >= 2 else "")
    return (f'<div class="ring">{_ring(int(pct), band)}'
            f'<div><div class="b">{html.escape(band)}</div>'
            f'<div class="t">health score</div>{trend_html}</div></div>')


def _brief(*, kind: str, token: str, token_label: str, eyebrow: str, title: str,
           lead_html: str, dial: str, summary: dict, foot_extra: str = "",
           claims_clean: bool = True) -> str:
    """The brief — one shareable screen that stands on its own.

    It is deliberately the *only* place the counts, the score and the headline appear. The
    executive summary and the `## Design health` body section are both skipped in the body
    for this reason: the same numbers printed two and three times down one page was the
    thing that made these reports hard to read, not a shortage of emphasis.
    """
    chips = "".join(
        f'<span class="chip p{n}">{c} &times; P{n} {PRI_LABELS[n]}</span>'
        for n, c in _live_counts(summary))
    if chips:
        total = _total_of(summary)
        plural = "finding" if total == 1 else "findings"
        worst = _worst(summary)
        foot = (f'<span class="chip total">{total} {plural}</span>{chips}'
                f'<span class="note">{PRI_ACTIONS[worst]} first.</span>')
    elif _has_counts(summary) and claims_clean:
        foot = '<span class="note">No findings recorded — nothing met the bar for a tag.</span>'
    else:
        # A run that verified nothing also has no findings. Saying "nothing met the bar"
        # over it would turn an empty run into a clean bill of health, which is the exact
        # confusion the `cuj` banner exists to prevent.
        foot = ""
    foot_html = (f'<div class="brief-foot">{foot}{foot_extra}</div>'
                 if (foot or foot_extra) else "")
    lead = f"{lead_html}" if lead_html else ""
    return (f'<section class="brief {kind}">'
            f'<div class="brief-top">'
            f'<div class="lock{" long" if len(token) > 5 else ""}">'
            f"<b>{html.escape(token)}</b>"
            f"<span>{html.escape(token_label)}</span></div>{dial}</div>"
            f'<div class="brief-why"><div class="eyebrow">{html.escape(eyebrow)}</div>'
            f"<h1>{html.escape(title)}</h1>{lead}</div>{foot_html}</section>")


def _report_lockup(fm: dict, summary: dict) -> tuple[str, str, str]:
    """(class, token, label) for an auditor report, whose scale has no go/no-go verdict.

    The gate in the contract is the *suite's*, derived across auditors — a single auditor
    report must not appear to issue one. What it can state is the worst thing it found and
    what the scale says to do about it, which is the whole point of P0-P3 over 0-4.
    """
    worst = _worst(summary)
    if worst is not None:
        return (f"lp{worst}", f"P{worst}", PRI_ACTIONS[worst].lower())
    if fm.get("auditor") == "cuj" and not _cuj_verified(fm):
        # `total: 0` without the verifying frameworks is not a pass; see _pass_banner.
        return ("warn", "UNVERIFIED", "no journey was observed")
    if _has_counts(summary):
        return ("go", "CLEAN", "no findings")
    return ("", "", "")


def _facts(pairs: list[tuple[str, str]]) -> str:
    cells = "".join(f"<span>{html.escape(k)} <b>{v}</b></span>" for k, v in pairs if v)
    return f'<p class="facts">{cells}</p>' if cells else ""


def _report_facts(fm: dict) -> str:
    frameworks = ", ".join(str(f) for f in (fm.get("frameworks") or []))
    target = str(fm.get("target", ""))
    return _facts([
        ("Target", f"<code>{html.escape(target)}</code>" if target else ""),
        ("Mode", html.escape(str(fm.get("mode", "")))),
        ("Run", html.escape(str(fm.get("date", ""))[:10])),
        ("Frameworks", html.escape(frameworks)),
    ])


# --- the health scorecard ----------------------------------------------------------------

def _scorecard(fm: dict) -> str:
    """Render the `health` scorecard (contract §4.1) from FRONTMATTER.

    The Markdown also carries a `## Design health` section for its own readers, and
    `render()` skips that section deliberately: printing the same numbers twice in one view
    is the "says everything three times" problem the contract rules out. Frontmatter is the
    source here because it is the validated form — the body table is prose.

    Each item declares its own denominator through `of`, so one block serves four auditors:
    Nielsen grades 0-4, a WCAG criterion 0-1, a journey step 0-1. Rows at or below half
    their denominator are tinted and carry the note the contract requires of them.
    """
    health = fm.get("health") or {}
    items = health.get("items")
    if not isinstance(items, list) or not items:
        return ""

    rows = []
    for it in items:
        if not isinstance(it, dict):
            continue
        score, of = it.get("score"), it.get("of", 4)
        if not isinstance(of, int) or of < 1:
            of = 4
        weak = isinstance(score, int) and score * 2 <= of
        if score is None:
            meter = "<em>not applicable</em>"
        elif of == 1:
            # A WCAG criterion and a journey step are pass/fail, not a grade. One dot out of
            # one is a weak way to say that, and it leaves the state encoded in colour alone.
            meter = ('<b class="yes">pass</b>' if score else '<b class="no">fail</b>')
        elif of <= 8:
            meter = "".join(
                f'<i class="{"warn" if weak and j < score else ("on" if j < score else "")}"></i>'
                for j in range(of))
        else:
            meter = f"<b>{score}/{of}</b>"
        note = str(it.get("note", "") or "")
        rows.append(
            f'<div class="r{" weak" if weak else ""}">'
            f'<div class="nm">{html.escape(str(it.get("item", "")))}'
            f'{f"<em>{html.escape(note)}</em>" if note else ""}</div>'
            f'<div class="dots">{meter}</div></div>')

    intro = ""
    if health.get("pct") is None:
        intro = ('<p class="unscored">This run reached nothing it could grade, so it reports '
                 "no percentage rather than one it did not earn — <b>0%</b> would read as a "
                 "catastrophe and <b>100%</b> as a clean pass, and both would be false.</p>")
    rubric = str(health.get("rubric", ""))
    caption = _facts([("Rubric", f"<code>{html.escape(rubric)}</code>" if rubric else ""),
                      ("Score", html.escape(f'{health.get("score")} of {health.get("max")}')
                       if health.get("max") else "")])
    return ('<section class="md"><h2>Design health</h2>' + intro + caption +
            f'<div class="rub">{"".join(rows)}</div></section>')


# --- banners (cuj verified-pass, provenance) ---------------------------------------------

def _banner(kind: str, icon: str, body_html: str) -> str:
    return f'<div class="banner {kind}"><span class="b-ico">{icon}</span><div>{body_html}</div></div>'


def _pass_banner(fm: dict, body: str) -> str:
    """For a cuj report, render the verified-pass (or verified-nothing) banner.

    `total: 0` is the cuj success state — but it is byte-identical to a run that verified
    nothing. The discriminator is the frameworks: `task-completion` + `success-criteria`
    mean journeys were actually completed and checked; `cuj-contract` alone means a static
    or all-skipped run that proved nothing. This makes that distinction loud.
    """
    if fm.get("auditor") != "cuj" or (fm.get("summary") or {}).get("total", 0) != 0:
        return ""
    verified = {"task-completion", "success-criteria"} & set(fm.get("frameworks") or [])
    jm = re.search(r"(\d+)\s*/\s*(\d+)\s+journeys passed", body)
    sm = re.search(r"(\d+)\s+of\s+(\d+)\s+steps verified", body)
    if verified:
        detail = ""
        if jm:
            detail += f" — {jm.group(1)}/{jm.group(2)} journeys passed"
        if sm:
            detail += f", {sm.group(1)}/{sm.group(2)} steps verified"
        return _banner("pass", "✓", f"<b>Verified pass</b>{detail}. Every journey completed "
                       "live and persisted a reload.")
    return _banner("warn", "⚠", "<b>Nothing verified</b> — <code>total: 0</code> here is a "
                   "static or all-skipped run (frameworks: <code>cuj-contract</code> only), "
                   "<b>not</b> a pass.")


def _provenance_banner(fm: dict, body: str) -> str:
    """Disclaim the two cases that most mislead: dev-lab web-perf, and static-mode runs."""
    low = body.lower()
    if fm.get("auditor") == "web-performance" and (
        "dev-mode" in low or "dev mode" in low or "not production" in low
    ):
        return _banner("info", "🔬", "<b>Dev-mode lab metrics</b> — indicative timings from "
                       "<code>next dev</code>, <b>not</b> production Core Web Vitals. Findings "
                       "are structural/potential, not measured regressions.")
    if fm.get("mode") == "static":
        return _banner("info", "📄", "<b>Static mode</b> — traced from source, not observed on "
                       "a running app; runtime-perception findings are <em>potential</em>.")
    return ""


# --- evidence fallback gallery (for reports with no walkthrough) --------------------------

EVIDENCE_IMG_RE = re.compile(
    r"\.?/?(assets/[\w./-]+\.(?:png|jpe?g|gif|webp|svg))", re.IGNORECASE
)


def _collect_evidence_images(body: str, report_dir: Path) -> list[tuple[str, str]]:
    """Find every embeddable `assets/*` image path in the body (embed *or* bare path).

    Older reports cite Evidence screenshots as bare `(./assets/x.png)` parentheticals rather
    than `![](...)` embeds, so a `## Walkthrough`-less report would otherwise show no images.
    This harvests both forms, dedupes by resolved path, and keeps first-seen order.
    """
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for m in EVIDENCE_IMG_RE.finditer(body):
        path = "./" + m.group(1)
        if path in seen:
            continue
        uri = _embed_asset(report_dir, path)
        if uri is not None:
            seen.add(path)
            out.append((path, uri))
    return out


def _gallery_section(imgs: list[tuple[str, str]]) -> str:
    tiles = "".join(
        f'<figure class="tile"><img alt="{html.escape(Path(p).stem)}" src="{uri}">'
        f"<figcaption>{html.escape(Path(p).name)}</figcaption></figure>"
        for p, uri in imgs
    )
    return ('<section class="md"><h2>Evidence gallery</h2>'
            f'<div class="gallery">{tiles}</div></section>')


# --- page shell --------------------------------------------------------------------------

STYLE = """
/* The report is one shareable screen followed by a calm document. Two rules carry the
   whole design:

   1. The brief at the top is complete on its own — verdict or worst priority, the health
      score, the counts and the lead paragraph — so a screenshot of it is a defensible
      summary and nobody has to scroll to know where things stand.
   2. The expert apparatus (framework citation, source location, grading rationale) gets a
      permanent column beside every finding. It is prominent by POSITION, not by styling,
      which is how it stays at full strength without shouting over the prose.

   Colour is institutional teal throughout; the verdict green/red and the priority ramp are
   the only other colours, so neither competes. Fonts are system stacks only — the file has
   to open offline from disk. */
:root{color-scheme:light dark;
--paper:#F7F7F5;--card:#FFFFFF;--ink:#1A1A1A;--ink2:#565A61;--line:#E3E2DD;--tint:#F0F3F2;
--teal:#0F5A52;--go:#1D6A3A;--nogo:#A61B1B;
/* Priority ramp. These carry WHITE text, so each is dark enough to clear 4.5:1 — the old
   ramp failed at 3.76:1 (sev4) and 2.80:1 (sev3), on an accessibility auditing tool. */
--p0:#A61B1B;--p1:#B5541C;--p2:#8A6D1F;--p3:#5A6472;
--chip-ink:#fff;
--shadow:0 1px 2px rgba(18,18,28,.03);}
@media(prefers-color-scheme:dark){:root{
--paper:#15181A;--card:#1C2022;--ink:#EDEDEA;--ink2:#A7ADB1;--line:#2C3134;--tint:#1F2628;
--teal:#6FB3A8;--go:#5FB07A;--nogo:#E06A6A;
/* Inverted: the badges lighten and take dark text, which clears 4.5:1 the other way. */
--p0:#E06A6A;--p1:#E0944E;--p2:#D7BA5C;--p3:#949DA9;
--chip-ink:#15181A;
--shadow:0 1px 2px rgba(0,0,0,.25);}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);
font:16px/1.62 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
-webkit-font-smoothing:antialiased}
.wrap{max-width:860px;margin:0 auto;padding:0 1.3rem 5rem}
.disp{font-family:Optima,Candara,"Gill Sans MT","Gill Sans","Trebuchet MS",system-ui,sans-serif}
.k{font:700 10.5px/1.4 system-ui,sans-serif;letter-spacing:.14em;text-transform:uppercase;
color:var(--ink2)}
a{color:var(--teal)}
a:focus-visible,[tabindex]:focus-visible,button:focus-visible{outline:2px solid var(--teal);
outline-offset:2px}
code{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:.85em;
background:var(--tint);color:var(--teal);padding:.08em .35em;border-radius:3px}
strong{font-weight:600}

/* --- the brief: the signature element, and the only thing above the fold ------------- */
.brief{background:var(--card);border:1px solid var(--line);border-radius:4px;
margin:1.8rem 0 2.2rem;overflow:hidden;box-shadow:var(--shadow)}
.brief-top{display:flex;align-items:center;gap:1.7rem;padding:1.6rem 1.7rem;flex-wrap:wrap}
.lock{display:flex;align-items:baseline;gap:.6rem}
.lock b{font:600 3.4rem/.95 Optima,Candara,"Gill Sans MT","Trebuchet MS",system-ui,sans-serif;
letter-spacing:-.015em;color:var(--ink)}
.lock.long b{font-size:2rem;letter-spacing:-.01em}
.lock span{font:700 10.5px/1.4 system-ui,sans-serif;letter-spacing:.14em;text-transform:uppercase;
color:var(--ink2);max-width:9rem}
.brief.go .lock b{color:var(--go)}
.brief.nogo .lock b,.brief.warn .lock b{color:var(--nogo)}
.brief.lp0 .lock b{color:var(--p0)}.brief.lp1 .lock b{color:var(--p1)}
.brief.lp2 .lock b{color:var(--p2)}.brief.lp3 .lock b{color:var(--p3)}
.ring{flex:0 0 auto;display:flex;align-items:center;gap:.85rem}
.ring svg{display:block}
.ring .b{font:700 10.5px/1.5 system-ui,sans-serif;letter-spacing:.12em;text-transform:uppercase;
color:var(--teal)}
.ring .t{color:var(--ink2);font-size:12px;margin-top:.1rem}
.brief-why{padding:0 1.7rem 1.4rem;max-width:66ch}
.brief-why h1{font:500 1.45rem/1.3 Optima,Candara,"Gill Sans MT","Trebuchet MS",system-ui,sans-serif;
margin:0 0 .4rem;letter-spacing:-.005em}
.brief-why .eyebrow{font:700 10.5px/1.4 system-ui,sans-serif;letter-spacing:.14em;
text-transform:uppercase;color:var(--ink2);margin-bottom:.5rem}
.brief-why p{margin:.4rem 0;color:var(--ink2);font-size:.95rem;line-height:1.6}
.brief-foot{display:flex;gap:.55rem;flex-wrap:wrap;align-items:center;
padding:.85rem 1.7rem;border-top:1px solid var(--line);background:var(--tint)}
.chip{font:600 11.5px/1.7 system-ui,sans-serif;border-radius:999px;padding:.05rem .65rem;
color:var(--chip-ink);letter-spacing:.02em;white-space:nowrap}
.chip.p0{background:var(--p0)}.chip.p1{background:var(--p1)}
.chip.p2{background:var(--p2)}.chip.p3{background:var(--p3)}
.chip.total{background:transparent;color:var(--ink);border:1px solid var(--line);font-weight:700}
.brief-foot .note{color:var(--ink2);font-size:12.5px}
.facts{display:flex;flex-wrap:wrap;gap:.35rem 2.2rem;color:var(--ink2);font-size:13px;
margin:-.9rem 0 0}
section.md .facts{margin:-.4rem 0 .8rem}
.facts b{color:var(--ink);font-weight:500}
.facts code{background:transparent;padding:0;color:var(--ink)}

h2{font:500 1.3rem/1.3 Optima,Candara,"Gill Sans MT","Trebuchet MS",system-ui,sans-serif;
margin:2.8rem 0 1rem;letter-spacing:-.005em}
h3{font-size:1rem;margin:1.2rem 0 .5rem}
h4{font:700 10.5px/1.4 system-ui,sans-serif;letter-spacing:.12em;text-transform:uppercase;
color:var(--ink2);margin:1.3rem 0 .4rem}
p{margin:.55rem 0}
ul,ol{margin:.5rem 0;padding-left:1.3rem}li{margin:.3rem 0}
blockquote{margin:.6rem 0;padding:.1rem 0 .1rem .9rem;border-left:3px solid var(--line);
color:var(--ink2)}
section.md{margin:0}

/* --- the health scorecard ------------------------------------------------------------- */
.rub{background:var(--card);border:1px solid var(--line);border-radius:4px;overflow:hidden}
.rub .r{display:grid;grid-template-columns:1fr 112px;gap:1rem;align-items:center;
padding:.62rem 1.1rem;border-bottom:1px solid var(--line)}
.rub .r:last-child{border-bottom:0}
.rub .r.weak{background:var(--tint)}
.rub .nm{font-size:14.5px}
.rub .nm em{display:block;font-style:normal;color:var(--ink2);font-size:12.5px;margin-top:.1rem}
.dots{display:flex;gap:4px;justify-content:flex-end;align-items:center}
.dots i{width:9px;height:9px;border-radius:50%;background:var(--line)}
.dots i.on{background:var(--teal)}
.dots i.warn{background:var(--p2)}
.dots em,.dots b{font:inherit;font-style:normal;font-weight:600;color:var(--ink2);font-size:12px;
letter-spacing:.04em}
.dots b.yes{color:var(--teal)}
.dots b.no{color:var(--p0);text-transform:uppercase;letter-spacing:.08em;font-size:11px}
.unscored{color:var(--ink2);font-size:.92rem;margin:.1rem 0 .9rem;max-width:66ch}

/* --- findings: C's card, A's permanent apparatus rail --------------------------------- */
.finding{background:var(--card);border:1px solid var(--line);border-radius:4px;margin:1rem 0;
box-shadow:var(--shadow)}
.find-head{padding:1.15rem 1.4rem .2rem}
.find-head h3{font:500 1.12rem/1.35 Optima,Candara,"Gill Sans MT","Trebuchet MS",
system-ui,sans-serif;margin:.5rem 0 0}
.find-body{display:grid;grid-template-columns:204px 1fr;gap:0 1.6rem;padding:.9rem 1.4rem 1.3rem}
.rail{border-right:1px solid var(--line);padding-right:1.5rem;margin:0}
.rail>*+*{margin-top:.95rem}
.rail dt{font:700 10px/1.4 system-ui,sans-serif;letter-spacing:.12em;text-transform:uppercase;
color:var(--ink2);margin-bottom:.18rem}
.rail dd{margin:0;font-size:12.8px;line-height:1.5}
.rail dd p{margin:0}
.rail dd p+p{margin-top:.4rem}
/* A `file:line` citation is one long token. It wraps anywhere rather than overflowing the
   rail, but never mid-word in the prose around it. */
.rail dd code{font-size:.9em;overflow-wrap:break-word;word-break:normal;hyphens:none;
display:inline-block;max-width:100%}
.find-body.norail{grid-template-columns:1fr}
.rail.flat{border-right:0;padding-right:0;display:grid;
grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:1rem}
.rail.flat>*+*{margin-top:0}
.prose>*:first-child{margin-top:0}
.prose .fix{margin-top:1rem;padding-top:.85rem;border-top:1px solid var(--line)}
.prose .fix .k{color:var(--teal);display:block;margin-bottom:.3rem}
.none{color:var(--ink2)}

figure{margin:1.05rem 0 0}
figure img{display:block;width:100%;border:1px solid var(--line);border-radius:3px}
figcaption{margin-top:.35rem;color:var(--ink2);font-size:12.5px}
.shot{margin:1.05rem 0 0}
.missing{display:inline-block;font-size:.78rem;color:var(--ink2);background:var(--tint);
border:1px dashed var(--line);border-radius:3px;padding:.15rem .5rem}

/* --- tables (per-auditor results, the index run log, any body table) ------------------ */
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);
border-radius:4px;font-size:14px;margin:.9rem 0;display:block;overflow-x:auto}
th{text-align:left;color:var(--ink2);font:700 10.5px/1.6 system-ui,sans-serif;
letter-spacing:.12em;text-transform:uppercase;padding:.7rem .9rem;
border-bottom:1px solid var(--line);background:var(--tint);white-space:nowrap}
td{padding:.7rem .9rem;border-bottom:1px solid var(--line);vertical-align:top}
td.zero{color:var(--ink2);opacity:.45}
tr:last-child td{border-bottom:0}

/* --- walkthrough flipbook ------------------------------------------------------------- */
.flip{background:var(--card);border:1px solid var(--line);border-radius:4px;padding:.9rem;
margin:1.1rem 0;box-shadow:var(--shadow)}
.flip-label{font:700 10.5px/1.4 system-ui,sans-serif;letter-spacing:.12em;text-transform:uppercase;
color:var(--ink2);margin:.15rem .2rem .7rem}
.frames{position:relative}
.frame{display:none;margin:0}.frame.is-active{display:block}
.frame img{width:100%;max-height:560px;height:auto;object-fit:contain;background:var(--paper);
border:1px solid var(--line);border-radius:3px;display:block}
.frame figcaption{font-size:.86rem;color:var(--ink);margin-top:.6rem;line-height:1.55}
.frame figcaption b{font-weight:600}
.flip-nav{display:flex;align-items:center;justify-content:center;gap:1rem;margin-top:.75rem}
.flip-nav button{background:var(--card);border:1px solid var(--line);border-radius:3px;
width:2.1rem;height:2.1rem;font-size:1.2rem;line-height:1;cursor:pointer;color:var(--ink)}
.flip-nav button:hover{border-color:var(--teal);color:var(--teal)}
.counter{font-size:.8rem;color:var(--ink2);font-variant-numeric:tabular-nums;min-width:3.6rem;
text-align:center}
.dots-nav{display:flex;flex-wrap:wrap;gap:.4rem;justify-content:center;margin-top:.55rem}
.dot{width:.5rem;height:.5rem;border-radius:50%;border:0;padding:0;cursor:pointer;
background:var(--line)}.dot.is-active{background:var(--teal)}

/* --- banners: the verdict reason, and the two disclaimers that matter ----------------- */
.banner{display:flex;gap:.6rem;align-items:baseline;font-size:.9rem;line-height:1.55}
.banner .b-ico{font-size:.95rem;line-height:1.5}
.banner b{font-weight:600}
.banner.verdict{padding:.8rem 1.7rem;border-top:1px solid var(--line);color:var(--ink2);
background:var(--card)}
.banner.verdict.warn{background:var(--tint)}
.banner.pass,.banner.warn,.banner.info,.banner.nogo,.banner.go{background:var(--card);
border:1px solid var(--line);border-left:3px solid var(--line);border-radius:0 3px 3px 0;
padding:.75rem 1rem;margin:0 0 1.2rem}
.banner.pass{border-left-color:var(--go)}
.banner.warn{border-left-color:var(--p2)}
.banner.info{border-left-color:var(--ink2)}
.banner.verdict.go,.banner.verdict.nogo,.banner.verdict.warn{border-left:0;border-radius:0;
margin:0}

/* --- evidence fallback gallery -------------------------------------------------------- */
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:1.1rem}
.tile{margin:0}
.tile img{width:100%;max-height:220px;height:auto;object-fit:contain;background:var(--paper);
border:1px solid var(--line);border-radius:3px;display:block}
.tile figcaption{font-size:.72rem;color:var(--ink2);margin-top:.35rem;word-break:break-all}

@media(max-width:700px){
.brief-top{gap:1.1rem;padding:1.3rem 1.2rem}
.lock b{font-size:2.8rem}
.brief-why,.brief-foot,.banner.verdict{padding-left:1.2rem;padding-right:1.2rem}
.find-head{padding:1rem 1.1rem .2rem}
.find-body{grid-template-columns:1fr;gap:1.1rem;padding:.9rem 1.1rem 1.2rem}
.rail{border-right:0;border-bottom:1px solid var(--line);padding-right:0;padding-bottom:1rem;
display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.9rem}
.rail>*+*{margin-top:0}
.rub .r{grid-template-columns:1fr 92px;gap:.7rem}
}
"""

SCRIPT = """
document.querySelectorAll('.flip').forEach(function(flip){
  var frames=flip.querySelectorAll('.frame'),dots=flip.querySelectorAll('.dot'),
      counter=flip.querySelector('.counter'),n=frames.length,cur=0;
  if(n<2)return;
  function show(i){cur=(i%n+n)%n;
    frames.forEach(function(f,j){f.classList.toggle('is-active',j===cur);});
    dots.forEach(function(d,j){d.classList.toggle('is-active',j===cur);});
    if(counter)counter.textContent=(cur+1)+' / '+n;}
  var p=flip.querySelector('.prev'),x=flip.querySelector('.next');
  if(p)p.addEventListener('click',function(){show(cur-1);});
  if(x)x.addEventListener('click',function(){show(cur+1);});
  dots.forEach(function(d){d.addEventListener('click',function(){show(+d.dataset.i);});});
  flip.addEventListener('keydown',function(e){
    if(e.key==='ArrowLeft'){show(cur-1);e.preventDefault();}
    else if(e.key==='ArrowRight'){show(cur+1);e.preventDefault();}});
});
"""


def _page(title: str, inner: str) -> str:
    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title>"
        f"<style>{STYLE}</style></head><body>"
        f'<main class="wrap">{inner}</main>'
        f"<script>{SCRIPT}</script></body></html>\n"
    )


# A link whose visible text IS the `.md` filename, e.g. `[usability-….md](usability-….md)`:
# strip `.md` from the text and point the href at `.html`.
FULL_MD_LINK_RE = re.compile(r"\[([\w./-]+)\.md\]\((?!https?:|#|/)\1\.md([)#])")
# Any remaining relative `](report.md)` / `](index.md)` — repoint the href only.
MD_LINK_RE = re.compile(r"\]\((?!https?:|#|/)([\w./-]+)\.md([)#])")


def _link_md_to_html(text: str) -> str:
    """Repoint relative `.md` report/index links to their `.html` companions.

    Where the link text is the filename itself, the trailing `.md` is dropped from the
    visible text too, so a repointed link never reads `…-204236.md` while linking to `.html`.
    """
    text = FULL_MD_LINK_RE.sub(r"[\1](\1.html\2", text)
    return MD_LINK_RE.sub(r"](\1.html\2", text)


# A roll-up's verdict should be the bare token `GO` / `NO-GO` (contract §9), but roll-ups
# written before §9 jam the token and its justification into one string — "GO — all three
# journeys pass". Those read as neither GO nor NO-GO to an equality test, which is why every
# such roll-up would have rendered as a red NO-GO. Split the leading token off instead.
VERDICT_RE = re.compile(r"^\s*(NO[-\s]?GO|GO)\b[\s—:.-]*(.*)$", re.IGNORECASE | re.DOTALL)


def _verdict_parts(fm: dict) -> tuple[str, str]:
    """Return (token, reason) for a roll-up, tolerating the legacy single-string form."""
    raw = str(fm.get("verdict", "")).strip()
    reason = str(fm.get("verdict_reason", "")).strip()
    m = VERDICT_RE.match(raw)
    if not m:
        # Unparseable verdict: the honest render is no-go, never a green pass by default.
        return ("NO-GO", reason or raw)
    token = "GO" if m.group(1).upper().startswith("GO") else "NO-GO"
    return (token, reason or m.group(2).strip())


def _render_rollup(fm: dict, body: str, report_dir: Path) -> str:
    """Render a `rollup-*.md` suite report as a verdict dashboard.

    The roll-up is the one document in the suite that carries a go/no-go, so the brief's
    lockup is the verdict itself. Its lead paragraph — everything between the H1 and the
    first `## ` — becomes the brief's prose rather than being dropped (the generic path
    emits only `## ` sections, which is how the dashboard's opening line went missing).
    """
    verdict, reason = _verdict_parts(fm)
    # A roll-up written before the gate was mechanical can state a verdict its own counts
    # do not support — a `GO` over a P1. The renderer does not overrule the document (it is
    # an append-only record of what that run concluded), but it must not present the claim
    # as settled either: a contested verdict renders amber, never green, so a glance cannot
    # mislead. Fresh roll-ups cannot reach this state — validate_rollup rejects them.
    summary = _summary_of(fm)
    derived = derive_verdict(summary) if _has_counts(summary) else verdict
    contested = derived != verdict
    kind = "warn" if contested else ("go" if verdict == "GO" else "nogo")
    icon = "⚠" if contested else ("✅" if verdict == "GO" else "🔴")

    detail = html.escape(reason) if reason else "suite verdict; detail below."
    if contested:
        counts = ", ".join(f"{k.upper()} {summary.get(k, 0)}" for k in PRIORITY_KEYS
                           if summary.get(k))
        detail += (f' <em>Contested: the merged counts ({counts}) derive '
                   f'<code>{derived}</code>. This roll-up states its verdict in prose '
                   f'rather than deriving it, so treat it as unverified.</em>')
    verdict_banner = _banner(f"verdict {kind}", icon, detail)

    body = _link_md_to_html(body)
    matches = list(SECTION_RE.finditer(body))
    pre = body[:matches[0].start()] if matches else body
    pre = re.sub(r"^\s*#\s+.*\n", "", pre, count=1)  # the H1 is the brief's title
    lead = _render_blocks(pre, report_dir) if pre.strip() else ""

    # The contract key is `auditors_ran`. The renderer read `auditors_run` — a spelling that
    # appears nowhere in the contract, the validator or any fixture — so the count it showed
    # was always zero, on the one line of the dashboard that says how much of the suite
    # actually ran. Both spellings are read now; only `auditors_ran` validates.
    runs = fm.get("auditors_ran") or fm.get("auditors_run") or []
    skipped = fm.get("auditors_skipped") or []
    parts = [
        _brief(kind=kind, token=verdict, token_label="verdict",
               eyebrow="UX audit roll-up", title=str(fm.get("scope", "")),
               lead_html=lead, dial=_health_dial(fm), summary=summary,
               foot_extra=verdict_banner),
        _facts([("Target", f'<code>{html.escape(str(fm.get("target", "")))}</code>'
                 if fm.get("target") else ""),
                ("Run", html.escape(str(fm.get("date", ""))[:10])),
                ("Auditors", f"{len(runs)} ran, {len(skipped)} skipped" if runs or skipped else ""),
                ("Gate", "NO-GO on any P0 or P1")]),
    ]
    for idx, m in enumerate(matches):
        name = m.group(1).strip()
        start_i = m.end()
        end_i = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        parts.append(f'<section class="md"><h2>{_inline(name, report_dir)}</h2>'
                     f'{_render_blocks(body[start_i:end_i], report_dir)}</section>')
    return "\n".join(parts)


TABLE_LINE_RE = re.compile(r"^\s*\|")


def _lead_prose(content: str, report_dir: Path) -> str:
    """The executive summary as the brief's prose, with its count table dropped.

    The brief's chips already carry the per-priority counts, so re-printing the table three
    inches below them is the duplication this design exists to remove.
    """
    kept = [ln for ln in content.splitlines() if not TABLE_LINE_RE.match(ln)]
    text = "\n".join(kept).strip()
    return _render_blocks(text, report_dir) if text else ""


# Sections the brief and the scorecard absorb. Leaving them in the body as well is how one
# report came to state its counts three times and its score twice on a single screen.
ABSORBED = {"executive summary", "design health"}


def render(md_path: str | Path) -> str:
    """Return the self-contained HTML for the report at `md_path`."""
    md_path = Path(md_path)
    report_dir = md_path.parent
    text = md_path.read_text(encoding="utf-8")
    fm, body = _split_frontmatter(text)
    if fm is None:
        raise ValueError(f"{md_path.name}: {body}")

    if is_rollup(fm):
        title = f"UX audit roll-up — {fm.get('scope', '')}".strip(" —")
        return _page(title, _render_rollup(fm, body, report_dir))

    matches = list(SECTION_RE.finditer(body))
    sections: list[tuple[str, str]] = []  # (lowercased name, section html)
    has_walkthrough = False
    lead = ""
    for idx, m in enumerate(matches):
        name = m.group(1).strip()
        nlow = name.lower()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        content = body[start:end]
        if nlow == "executive summary":
            lead = _lead_prose(content, report_dir)
            continue
        if nlow in ABSORBED:
            continue
        if nlow == "findings":
            inner = _render_findings(content, report_dir)
        elif nlow == "walkthrough":
            has_walkthrough = True
            inner = _render_walkthrough(content, report_dir)
        else:
            inner = _render_blocks(content, report_dir)
        sections.append(
            (nlow, f'<section class="md"><h2>{_inline(name, report_dir)}</h2>{inner}</section>'))

    # A report with no walkthrough surfaces its Evidence screenshots as a fallback gallery.
    gallery = ""
    if not has_walkthrough:
        imgs = _collect_evidence_images(body, report_dir)
        if imgs:
            gallery = _gallery_section(imgs)

    summary = _summary_of(fm)
    kind, token, token_label = _report_lockup(fm, summary)
    auditor = str(fm.get("auditor", "report"))
    scope = str(fm.get("scope", ""))
    parts: list[str] = [
        _brief(kind=kind, token=token, token_label=token_label,
               eyebrow=f"{auditor} audit", title=scope or auditor,
               lead_html=lead, dial=_health_dial(fm), summary=summary,
               claims_clean=kind != "warn"),
        _report_facts(fm),
        _pass_banner(fm, body),
        _provenance_banner(fm, body),
        _scorecard(fm),
    ]
    injected = False
    for nlow, shtml in sections:
        if nlow == "appendix" and gallery and not injected:
            parts.append(gallery)
            injected = True
        parts.append(shtml)
    if gallery and not injected:
        parts.append(gallery)

    title = f"{auditor} audit — {scope}".strip(" —")
    return _page(title, "\n".join(p for p in parts if p))


def render_to_file(md_path: str | Path) -> Path:
    md_path = Path(md_path)
    out = md_path.with_suffix(".html")
    out.write_text(render(md_path), encoding="utf-8")
    return out


ZERO_CELL_RE = re.compile(r"<td>0</td>")


def render_index(md_path: str | Path) -> str:
    """Render `.ux/audits/index.md` (a run log) into a stable `index.html` landing page."""
    md_path = Path(md_path)
    text = _link_md_to_html(md_path.read_text(encoding="utf-8"))
    title = "Audit index"
    kept: list[str] = []
    for line in text.splitlines():
        if not kept and line.startswith("# "):
            title = line[2:].strip()
            continue
        kept.append(line)
    # The brief suppresses zero counts; a run log cannot drop the column, so it dims the
    # cell instead. Same purpose: a row of zeros should not compete with the one count that
    # is not zero.
    head = ('<section class="brief"><div class="brief-why">'
            '<div class="eyebrow">UX audits</div>'
            f"<h1>{html.escape(title)}</h1>"
            "<p>One row per run, appended and never rewritten. Each row links to that "
            "run's report; <code>Health</code> is the scorecard percentage it recorded.</p>"
            "</div></section>")
    table = ZERO_CELL_RE.sub('<td class="zero">0</td>',
                            _render_blocks("\n".join(kept), md_path.parent))
    return _page(title, head + table)


def render_index_to_file(md_path: str | Path) -> Path:
    md_path = Path(md_path)
    out = md_path.with_suffix(".html")
    out.write_text(render_index(md_path), encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--index":
        rest = argv[1:] or ["index.md"]
        ok = True
        for arg in rest:
            try:
                print(f"rendered index: {render_index_to_file(arg)}")
            except Exception as exc:  # noqa: BLE001
                ok = False
                print(f"FAILED index: {arg}: {exc}", file=sys.stderr)
        return 0 if ok else 1
    if not argv:
        print("usage: render_report_html.py <report.md> [...]  |  --index [<index.md>]",
              file=sys.stderr)
        return 2
    ok = True
    for arg in argv:
        try:
            # `index.md` has no frontmatter — route it to the index renderer for convenience.
            out = (render_index_to_file(arg) if Path(arg).name == "index.md"
                   else render_to_file(arg))
            print(f"rendered: {out}")
        except Exception as exc:  # noqa: BLE001 — report path + reason, keep going
            ok = False
            print(f"FAILED: {arg}: {exc}", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
