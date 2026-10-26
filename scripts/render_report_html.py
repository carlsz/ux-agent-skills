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
    _split_frontmatter, FINDING_RE, is_rollup, PRIORITY_KEYS, derive_verdict,
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
FINDING_FIELD_RE = re.compile(
    r"-\s+\*\*(Issue Description|Framework Violation|Priority|Severity|Evidence|"
    r"Recommended Fix):\*\*"
    r"\s*(.*?)(?=\n-\s+\*\*(?:Issue Description|Framework Violation|Priority|Severity|"
    r"Evidence|Recommended Fix):\*\*|\Z)",
    re.DOTALL,
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
            items: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(("- ", "* ")):
                items.append(lines[i].strip()[2:]); i += 1
            out.append("<ul>" + "".join(
                f"<li>{_inline(it, report_dir)}</li>" for it in items) + "</ul>"); continue
        if ORDERED_RE.match(stripped):
            flush()
            items = []
            while i < len(lines) and ORDERED_RE.match(lines[i].strip()):
                items.append(ORDERED_RE.sub("", lines[i].strip())); i += 1
            out.append("<ol>" + "".join(
                f"<li>{_inline(it, report_dir)}</li>" for it in items) + "</ol>"); continue
        para.append(stripped); i += 1

    flush()
    return "\n".join(out)


# --- findings ----------------------------------------------------------------------------

def _parse_findings(body: str) -> list[dict]:
    matches = list(FINDING_RE.finditer(body))
    findings: list[dict] = []
    for idx, m in enumerate(matches):
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        block = body[start:end]
        newline = block.find("\n")
        heading = block[:newline] if newline != -1 else block
        title = re.sub(r"^###\s+\[P[0-3]\]\s*", "", heading).strip()
        fields = {name: val.strip() for name, val in FINDING_FIELD_RE.findall(block)}
        findings.append({"p": int(m.group(1)), "title": title, "fields": fields})
    return findings


def _render_findings(body: str, report_dir: Path) -> str:
    findings = _parse_findings(body)
    if not findings:
        return '<p class="none">No findings.</p>'
    cards: list[str] = []
    for f in findings:
        n = f["p"]
        rows = []
        for keys, dt in (
            (("Issue Description",), "Issue"),
            (("Framework Violation",), "Violation"),
            (("Priority", "Severity"), "Priority"),
            (("Evidence",), "Evidence"),
            (("Recommended Fix",), "Fix"),
        ):
            # A schema-2 report labels this field `Severity`; the row is titled by what the
            # scale is now, not by what the source document happened to call it.
            key = next((k for k in keys if k in f["fields"]), None)
            if key:
                rows.append(
                    f"<dt>{dt}</dt><dd>{_render_blocks(f['fields'][key], report_dir)}</dd>")
        cards.append(
            f'<article class="finding p{n}">'
            f'<header><span class="badge p{n}">P{n} {PRI_LABELS[n]}</span>'
            f"<h3>{_inline(f['title'], report_dir)}</h3></header>"
            f"<dl>{''.join(rows)}</dl></article>"
        )
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


# --- header + severity bar ---------------------------------------------------------------

def _chip(text: str) -> str:
    return f'<span class="chip">{html.escape(str(text))}</span>'


def _render_header(fm: dict) -> str:
    auditor = fm.get("auditor", "report")
    scope = fm.get("scope", "")
    meta = []
    if fm.get("mode"):
        meta.append(_chip(f"mode: {fm['mode']}"))
    if fm.get("date"):
        meta.append(_chip(str(fm["date"])))
    for fw in fm.get("frameworks", []) or []:
        meta.append(_chip(fw))
    target = fm.get("target", "")
    target_html = f'<div class="target"><code>{html.escape(str(target))}</code></div>' if target else ""
    return (
        f'<header class="report-head">'
        f'<div class="eyebrow">{html.escape(str(auditor))} audit</div>'
        f"<h1>{html.escape(str(scope)) or html.escape(str(auditor))}</h1>"
        f"{target_html}"
        f'<div class="chips">{"".join(meta)}</div>'
        f"</header>"
    )


def _summary_of(fm: dict) -> dict:
    """The per-severity counts, reading the contract key and the one legacy spelling.

    §9 specifies `summary:`. Roll-ups written before it also used `totals:`; both are read
    here so a historical roll-up renders its real numbers instead of a row of zeros.
    """
    for key in ("summary", "totals"):
        value = fm.get(key)
        if isinstance(value, dict) and value:
            return value
    return {}


def _severity_bar(fm: dict) -> str:
    """Inline priority summary — `N findings · P0 0 · P1 1 …`.

    Priority is the only colour on the page: the count numbers carry the ramp, dimmed when
    zero. The badges on the cards do the heavy visual lifting.
    """
    summary = _summary_of(fm)
    # No counts at all → no bar. A roll-up written before §9 may carry none, and a row of
    # zeros is not a neutral default: it asserts "nothing found" over a document listing
    # five issues. Silence is the honest render; the body still carries the numbers.
    if not any(k in summary for k in PRIORITY_KEYS):
        return ""
    # Derive `total` when absent rather than defaulting to 0, for the same reason.
    total = summary.get("total")
    if not isinstance(total, int):
        total = sum(v for k in PRIORITY_KEYS if isinstance(v := summary.get(k), int))
    cells = [f'<div class="scell total"><b>{total}</b><span>findings</span></div>']
    for n in PRI_ORDER:
        count = summary.get(f"p{n}", 0)
        off = "" if count else " off"
        cells.append(
            f'<div class="scell p{n}{off}"><b>{count}</b>'
            f"<span>P{n} · {PRI_LABELS[n]}</span></div>"
        )
    return f'<section class="sevrow">{"".join(cells)}</section>'


def _health_section(fm: dict) -> str:
    """Render the `health` scorecard (contract §4.1) from FRONTMATTER.

    The Markdown also carries a `## Design health` section for its own readers, and
    `render()` skips that section deliberately: printing the same numbers twice in one view
    is the "says everything three times" problem the contract now rules out. Frontmatter is
    the source here because it is the validated form — the body table is prose.
    """
    health = fm.get("health") or {}
    items = health.get("items")
    if not isinstance(items, list) or not items:
        return ""

    pct, band = health.get("pct"), health.get("band", "")
    if pct is None:
        headline = (f'<div class="hband"><b>Unscored</b>'
                    f"<span>nothing gradable was reached &mdash; this run reports no "
                    f"percentage rather than one it did not earn</span></div>")
    else:
        headline = (f'<div class="hband"><b>{pct}<small>%</small></b>'
                    f'<span>{html.escape(str(band))} &middot; '
                    f'{health.get("score")} of {health.get("max")} '
                    f'&middot; {html.escape(str(health.get("rubric", "")))}</span></div>')

    rows = []
    for it in items:
        if not isinstance(it, dict):
            continue
        score, of = it.get("score"), it.get("of", 4)
        if score is None:
            meter, cls = '<em class="na">n/a</em>', " na"
        else:
            cls = " weak" if isinstance(score, int) and score * 2 <= of else ""
            meter = "".join(
                f'<i class="{"on" if j < score else ""}"></i>' for j in range(of)
            ) if of <= 8 else f"<em>{score}/{of}</em>"
            meter = f'<span class="pips">{meter}</span>'
        rows.append(
            f'<tr class="hrow{cls}"><td>{html.escape(str(it.get("item", "")))}</td>'
            f"<td>{meter}</td>"
            f'<td class="hnote">{html.escape(str(it.get("note", "") or ""))}</td></tr>')

    return ('<section class="md"><h2>Design health</h2>' + headline +
            f'<table class="health">{"".join(rows)}</table></section>')


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
:root{color-scheme:light dark;
--bg:#fbfbfc;--fg:#16161a;--mut:#6b7076;--card:#ffffff;--line:#e8e8ec;--link:#2563eb;
--shadow:0 1px 2px rgba(18,18,28,.04),0 2px 6px rgba(18,18,28,.06);
/* Badge backgrounds carry WHITE text, so each is dark enough to clear 4.5:1 — the old
   ramp failed at 3.76:1 (sev4) and 2.80:1 (sev3), on an accessibility auditing tool. */
--b0:#A61B1B;--b1:#B5541C;--b2:#8A6D1F;--b3:#5A6472;
--c0:#A61B1B;--c1:#B5541C;--c2:#8A6D1F;--c3:#5A6472;}
@media(prefers-color-scheme:dark){:root{
--bg:#0f0f12;--fg:#e9e9ec;--mut:#9a9aa2;--card:#17181c;--line:#2a2b31;--link:#7aa2f7;
--shadow:0 1px 2px rgba(0,0,0,.3),0 2px 8px rgba(0,0,0,.35);
--c0:#f87171;--c1:#fb923c;--c2:#d7ba5c;--c3:#94a3b8;}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.62 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:800px;margin:0 auto;padding:2.8rem 1.2rem 5rem}
.report-head{margin-bottom:.4rem}
.eyebrow{text-transform:uppercase;letter-spacing:.1em;font-size:.7rem;font-weight:800;color:var(--fg)}
h1{font-size:1.65rem;line-height:1.22;margin:.4rem 0 .6rem;letter-spacing:-.015em}
.target code{background:transparent;border:0;color:var(--mut);font-size:.84rem;padding:0}
.chips{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.75rem}
.chip{font-size:.73rem;background:var(--card);border:1px solid var(--line);
border-radius:999px;padding:.16rem .65rem;color:var(--mut);box-shadow:var(--shadow)}
/* severity summary — larger boxed cells, bold ramp: colour number + top accent */
.sevrow{display:flex;flex-wrap:wrap;gap:.65rem;margin:1.6rem 0 2.6rem}
.scell{flex:1 1 0;min-width:100px;background:var(--card);border:1px solid var(--line);
border-top:3px solid var(--line);border-radius:13px;padding:.8rem .9rem;box-shadow:var(--shadow);
display:flex;flex-direction:column;gap:.25rem}
.scell b{font-size:1.85rem;line-height:1;font-weight:800;font-variant-numeric:tabular-nums}
.scell span{font-size:.65rem;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);font-weight:700}
.scell.off{opacity:.5}.scell.total{border-top-color:var(--fg)}
.scell.p0{border-top-color:var(--b0)}.scell.p0 b{color:var(--c0)}
.scell.p1{border-top-color:var(--b1)}.scell.p1 b{color:var(--c1)}
.scell.p2{border-top-color:var(--b2)}.scell.p2 b{color:var(--c2)}
.scell.p3{border-top-color:var(--b3)}.scell.p3 b{color:var(--c3)}
section.md{margin:0 0 1.6rem}
h2{font-size:1.2rem;font-weight:750;margin:2.5rem 0 .9rem;letter-spacing:-.01em}
h3{font-size:1rem;margin:1.2rem 0 .5rem}h4{font-size:.9rem;margin:1rem 0 .4rem;color:var(--mut)}
p{margin:.55rem 0}a{color:var(--link)}
code{background:var(--card);border:1px solid var(--line);border-radius:5px;
padding:.05rem .35rem;font-size:.85em}
blockquote{margin:.5rem 0;padding:.3rem 0 .3rem .9rem;border-left:3px solid var(--line);color:var(--mut)}
ul,ol{margin:.5rem 0;padding-left:1.3rem}li{margin:.25rem 0}
table{border-collapse:separate;border-spacing:0;width:100%;margin:.9rem 0;font-size:.9rem;
display:block;overflow-x:auto;border:1px solid var(--line);border-radius:10px;box-shadow:var(--shadow)}
th,td{border-bottom:1px solid var(--line);padding:.5rem .7rem;text-align:left;vertical-align:top}
tr:last-child td{border-bottom:0}th{background:var(--card);font-size:.78rem;text-transform:uppercase;
letter-spacing:.03em;color:var(--mut)}
/* finding cards — soft-shadowed, no stripe; the bold badge carries the severity colour */
.finding{background:var(--card);border:1px solid var(--line);border-radius:14px;
padding:1.1rem 1.3rem;margin:1rem 0;box-shadow:var(--shadow)}
.finding header{display:flex;flex-wrap:wrap;align-items:center;gap:.6rem}
.finding h3{margin:0;font-size:1.02rem;font-weight:680}
.badge{font-size:.7rem;font-weight:800;letter-spacing:.02em;color:#fff;border-radius:6px;
padding:.16rem .5rem;white-space:nowrap;text-transform:uppercase}
.badge.p0{background:var(--b0)}.badge.p1{background:var(--b1)}
.badge.p2{background:var(--b2)}.badge.p3{background:var(--b3)}
.finding dl{margin:.85rem 0 0;display:grid;grid-template-columns:5.5rem 1fr;gap:.4rem .9rem}
.finding dt{font-size:.68rem;text-transform:uppercase;letter-spacing:.04em;color:var(--mut);
font-weight:700;padding-top:.15rem}
.finding dd{margin:0}.finding dd p:first-child{margin-top:0}
.shot{margin:.8rem 0;text-align:center}
.shot img{max-width:100%;max-height:540px;height:auto;border:1px solid var(--line);
border-radius:10px;box-shadow:var(--shadow);display:inline-block}
.shot figcaption{font-size:.74rem;color:var(--mut);margin-top:.4rem}
.missing{display:inline-block;font-size:.78rem;color:var(--mut);background:var(--card);
border:1px dashed var(--line);border-radius:6px;padding:.15rem .5rem}
.none{color:var(--mut)}
/* design health scorecard */
.hband{display:flex;align-items:baseline;gap:.7rem;flex-wrap:wrap;margin:.2rem 0 .9rem}
.hband b{font-size:1.9rem;font-weight:800;line-height:1;letter-spacing:-.02em}
.hband b small{font-size:.95rem;font-weight:600;color:var(--mut);margin-left:.1rem}
.hband span{color:var(--mut);font-size:.86rem}
table.health{font-size:.88rem}
table.health td{border-bottom:1px solid var(--line);padding:.42rem .7rem;vertical-align:middle}
table.health tr:last-child td{border-bottom:0}
.hrow.weak td:first-child{font-weight:650}
.hrow.na td{color:var(--mut)}
.hnote{color:var(--mut);font-size:.84rem}
.pips{display:inline-flex;gap:3px}
.pips i{width:15px;height:8px;border-radius:2px;background:var(--line)}
.pips i.on{background:var(--link)}
.hrow.weak .pips i.on{background:var(--b2)}
.pips em{font-style:normal;color:var(--mut);font-size:.84rem}
em.na{font-style:normal;color:var(--mut);font-size:.82rem}
/* walkthrough flipbook */
.flip{background:var(--card);border:1px solid var(--line);border-radius:14px;
box-shadow:var(--shadow);padding:.85rem;margin:1.1rem 0}
.flip:focus-visible{outline:2px solid var(--link);outline-offset:2px}
.flip-label{font-size:.7rem;font-weight:800;text-transform:uppercase;letter-spacing:.06em;
color:var(--mut);margin:.15rem .2rem .65rem}
.frames{position:relative}
.frame{display:none;margin:0}.frame.is-active{display:block}
.frame img{width:100%;max-height:560px;height:auto;object-fit:contain;background:var(--bg);
border:1px solid var(--line);border-radius:10px;display:block}
.frame figcaption{font-size:.84rem;color:var(--fg);margin-top:.65rem;line-height:1.5}
.frame figcaption b{font-weight:700}
.flip-nav{display:flex;align-items:center;justify-content:center;gap:1rem;margin-top:.7rem}
.flip-nav button{background:var(--card);border:1px solid var(--line);border-radius:9px;
width:2.1rem;height:2.1rem;font-size:1.2rem;line-height:1;cursor:pointer;color:var(--fg)}
.flip-nav button:hover{border-color:var(--link);color:var(--link)}
.counter{font-size:.8rem;color:var(--mut);font-variant-numeric:tabular-nums;
min-width:3.6rem;text-align:center}
.dots{display:flex;flex-wrap:wrap;gap:.4rem;justify-content:center;margin-top:.55rem}
.dot{width:.5rem;height:.5rem;border-radius:50%;border:0;padding:0;cursor:pointer;
background:var(--line)}.dot.is-active{background:var(--fg)}
/* banners: cuj pass, provenance */
.banner{display:flex;gap:.6rem;align-items:baseline;border:1px solid var(--line);
border-left-width:4px;border-radius:12px;padding:.75rem 1rem;margin:.2rem 0 1.5rem;
font-size:.9rem;box-shadow:var(--shadow)}
.banner .b-ico{font-size:1rem;line-height:1.4}
.banner b{font-weight:750}
.banner.pass{background:rgba(34,197,94,.10);border-color:rgba(34,197,94,.35);border-left-color:#22c55e}
.banner.warn{background:rgba(234,179,8,.12);border-color:rgba(234,179,8,.4);border-left-color:#eab308}
.banner.info{background:rgba(148,163,184,.13);border-color:rgba(148,163,184,.4);border-left-color:#94a3b8}
.banner.go{background:rgba(34,197,94,.10);border-color:rgba(34,197,94,.4);border-left-color:#22c55e}
.banner.nogo{background:rgba(239,68,68,.10);border-color:rgba(239,68,68,.4);border-left-color:#ef4444}
.banner.verdict{font-size:1rem;padding:.9rem 1.1rem}
.banner.verdict b{font-size:1.15rem;text-transform:uppercase;letter-spacing:.03em}
/* evidence fallback gallery */
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:.8rem}
.tile{margin:0;background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:.5rem;box-shadow:var(--shadow)}
.tile img{width:100%;max-height:220px;height:auto;object-fit:contain;background:var(--bg);
border:1px solid var(--line);border-radius:7px;display:block}
.tile figcaption{font-size:.72rem;color:var(--mut);margin-top:.35rem;word-break:break-all}
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

    The roll-up has its own frontmatter (`rollup`, `verdict`, `auditors_run`) rather than the
    per-report `auditor`/`summary`, so it renders through a dedicated path: a prominent
    go/no-go verdict, then the roll-up's sections (auditor table, per-auditor severity matrix,
    merged issues) generically — with report links repointed to their `.html` views.
    """
    verdict, reason = _verdict_parts(fm)
    # A roll-up written before the gate was mechanical can state a verdict its own counts
    # do not support — a `GO` over a sev3. The renderer does not overrule the document (it
    # is an append-only record of what that run concluded), but it must not present the
    # claim as settled either: a contested verdict renders amber, never green, so a glance
    # cannot mislead. Fresh roll-ups cannot reach this state — validate_rollup rejects them.
    summary = _summary_of(fm)
    derived = derive_verdict(summary) if any(k in summary for k in PRIORITY_KEYS) else verdict
    contested = derived != verdict
    kind = "warn" if contested else ("go" if verdict == "GO" else "nogo")
    icon = "⚠" if contested else ("✅" if verdict == "GO" else "🔴")
    date, target = fm.get("date", ""), fm.get("target", "")
    runs = fm.get("auditors_run") or []
    chip_vals = ([str(date)] if date else []) + ([f"{len(runs)} auditors"] if runs else [])
    target_html = (f'<div class="target"><code>{html.escape(str(target))}</code></div>'
                   if target else "")
    header = (f'<header class="report-head"><div class="eyebrow">UX audit roll-up</div>'
              f'<h1>{html.escape(str(fm.get("scope", "")))}</h1>{target_html}'
              f'<div class="chips">{"".join(_chip(v) for v in chip_vals)}</div></header>')
    detail = html.escape(reason) if reason else "suite verdict; detail below."
    if contested:
        counts = ", ".join(f"{k.upper()} {summary.get(k, 0)}" for k in PRIORITY_KEYS
                           if summary.get(k))
        detail += (f' <em>Contested: the merged counts ({counts}) derive '
                   f'<code>{derived}</code>. This roll-up states its verdict in prose '
                   f'rather than deriving it, so treat it as unverified.</em>')
    verdict_banner = _banner(
        f"verdict {kind}", icon, f"<b>{html.escape(verdict)}</b> — {detail}")

    body = _link_md_to_html(body)
    matches = list(SECTION_RE.finditer(body))
    pre = body[:matches[0].start()] if matches else body
    pre = re.sub(r"^\s*#\s+.*\n", "", pre, count=1)  # drop the redundant H1 title line
    parts = [header, verdict_banner, _severity_bar(fm)]
    if pre.strip():
        parts.append(f'<section class="md">{_render_blocks(pre, report_dir)}</section>')
    for idx, m in enumerate(matches):
        name = m.group(1).strip()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        parts.append(f'<section class="md"><h2>{_inline(name, report_dir)}</h2>'
                     f'{_render_blocks(body[start:end], report_dir)}</section>')
    return "\n".join(parts)


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
    for idx, m in enumerate(matches):
        name = m.group(1).strip()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        content = body[start:end]
        if name.lower() == "design health":
            # Rendered from frontmatter instead; see _health_section.
            continue
        if name.lower() == "findings":
            inner = _render_findings(content, report_dir)
        elif name.lower() == "walkthrough":
            has_walkthrough = True
            inner = _render_walkthrough(content, report_dir)
        else:
            inner = _render_blocks(content, report_dir)
        sections.append((name.lower(),
                         f'<section class="md"><h2>{_inline(name, report_dir)}</h2>{inner}</section>'))

    # A report with no walkthrough surfaces its Evidence screenshots as a fallback gallery.
    gallery = ""
    if not has_walkthrough:
        imgs = _collect_evidence_images(body, report_dir)
        if imgs:
            gallery = _gallery_section(imgs)

    parts: list[str] = [_render_header(fm), _pass_banner(fm, body),
                        _provenance_banner(fm, body), _severity_bar(fm)]
    health_html = _health_section(fm)
    injected = False
    scored = False
    for nlow, shtml in sections:
        if nlow == "appendix" and gallery and not injected:
            parts.append(gallery)
            injected = True
        parts.append(shtml)
        # The scorecard follows the executive summary, where the body section used to sit.
        if nlow == "executive summary" and health_html and not scored:
            parts.append(health_html)
            scored = True
    if health_html and not scored:
        parts.append(health_html)
    if gallery and not injected:
        parts.append(gallery)

    auditor = fm.get("auditor", "report")
    scope = fm.get("scope", "")
    title = f"{auditor} audit — {scope}".strip(" —")
    return _page(title, "\n".join(parts))


def render_to_file(md_path: str | Path) -> Path:
    md_path = Path(md_path)
    out = md_path.with_suffix(".html")
    out.write_text(render(md_path), encoding="utf-8")
    return out


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
    head = (f'<header class="report-head"><div class="eyebrow">UX audits</div>'
            f"<h1>{html.escape(title)}</h1></header>")
    return _page(title, head + _render_blocks("\n".join(kept), md_path.parent))


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
