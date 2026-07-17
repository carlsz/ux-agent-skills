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
from validate_report import _split_frontmatter, FINDING_RE  # noqa: E402

# --- severity vocabulary (mirrors the report contract §4) --------------------------------

SEV_LABELS = {4: "Catastrophe", 3: "Major", 2: "Minor", 1: "Cosmetic"}
SEV_ORDER = [4, 3, 2, 1]

# --- inline markdown ---------------------------------------------------------------------

IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")

IMAGE_MIME = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml",
}

# The five labelled fields of a finding block (report contract §5).
FINDING_FIELD_RE = re.compile(
    r"-\s+\*\*(Issue Description|Framework Violation|Severity|Evidence|Recommended Fix):\*\*"
    r"\s*(.*?)(?=\n-\s+\*\*(?:Issue Description|Framework Violation|Severity|Evidence|"
    r"Recommended Fix):\*\*|\Z)",
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
        title = re.sub(r"^###\s+\[sev[0-4]\]\s*", "", heading).strip()
        fields = {name: val.strip() for name, val in FINDING_FIELD_RE.findall(block)}
        findings.append({"sev": int(m.group(1)), "title": title, "fields": fields})
    return findings


def _render_findings(body: str, report_dir: Path) -> str:
    findings = _parse_findings(body)
    if not findings:
        return '<p class="none">No findings.</p>'
    cards: list[str] = []
    for f in findings:
        sev = f["sev"]
        rows = []
        for key, dt in (
            ("Issue Description", "Issue"),
            ("Framework Violation", "Violation"),
            ("Severity", "Severity"),
            ("Evidence", "Evidence"),
            ("Recommended Fix", "Fix"),
        ):
            if key in f["fields"]:
                rows.append(
                    f"<dt>{dt}</dt><dd>{_render_blocks(f['fields'][key], report_dir)}</dd>")
        cards.append(
            f'<article class="finding sev{sev}">'
            f'<header><span class="badge sev{sev}">sev{sev}</span>'
            f"<h3>{_inline(f['title'], report_dir)}</h3></header>"
            f"<dl>{''.join(rows)}</dl></article>"
        )
    return "\n".join(cards)


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


def _severity_bar(fm: dict) -> str:
    """Minimal inline severity summary — `sev4 0  sev3 1 …  N findings`.

    Severity is the only colour on the page: the count numbers carry the ramp, dimmed when
    zero. No cells, no bar — the badges on the cards do the heavy visual lifting.
    """
    summary = fm.get("summary") or {}
    total = summary.get("total", 0)
    cells = [f'<div class="scell total"><b>{total}</b><span>findings</span></div>']
    for n in SEV_ORDER:
        count = summary.get(f"sev{n}", 0)
        off = "" if count else " off"
        cells.append(
            f'<div class="scell sev{n}{off}"><b>{count}</b>'
            f"<span>sev{n} · {SEV_LABELS[n]}</span></div>"
        )
    return f'<section class="sevrow">{"".join(cells)}</section>'


# --- page shell --------------------------------------------------------------------------

STYLE = """
:root{color-scheme:light dark;
--bg:#fbfbfc;--fg:#16161a;--mut:#6b7076;--card:#ffffff;--line:#e8e8ec;--link:#2563eb;
--shadow:0 1px 2px rgba(18,18,28,.04),0 2px 6px rgba(18,18,28,.06);
--s4:#ef4444;--s3:#f97316;--s2:#eab308;--s2ink:#1a1a1a;--s1:#94a3b8;--s1ink:#1a1a1a;
--c4:#dc2626;--c3:#ea580c;--c2:#a16207;--c1:#64748b;}
@media(prefers-color-scheme:dark){:root{
--bg:#0f0f12;--fg:#e9e9ec;--mut:#9a9aa2;--card:#17181c;--line:#2a2b31;--link:#7aa2f7;
--shadow:0 1px 2px rgba(0,0,0,.3),0 2px 8px rgba(0,0,0,.35);
--c4:#f87171;--c3:#fb923c;--c2:#eab308;--c1:#94a3b8;}}
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
.scell.sev4{border-top-color:var(--s4)}.scell.sev4 b{color:var(--c4)}
.scell.sev3{border-top-color:var(--s3)}.scell.sev3 b{color:var(--c3)}
.scell.sev2{border-top-color:var(--s2)}.scell.sev2 b{color:var(--c2)}
.scell.sev1{border-top-color:var(--s1)}.scell.sev1 b{color:var(--c1)}
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
.badge.sev4{background:var(--s4)}.badge.sev3{background:var(--s3)}
.badge.sev2{background:var(--s2);color:var(--s2ink)}.badge.sev1{background:var(--s1);color:var(--s1ink)}
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
"""


def _page(title: str, inner: str) -> str:
    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title>"
        f"<style>{STYLE}</style></head><body>"
        f'<main class="wrap">{inner}</main></body></html>\n'
    )


def render(md_path: str | Path) -> str:
    """Return the self-contained HTML for the report at `md_path`."""
    md_path = Path(md_path)
    report_dir = md_path.parent
    text = md_path.read_text(encoding="utf-8")
    fm, body = _split_frontmatter(text)
    if fm is None:
        raise ValueError(f"{md_path.name}: {body}")

    matches = list(SECTION_RE.finditer(body))
    parts: list[str] = [_render_header(fm), _severity_bar(fm)]

    for idx, m in enumerate(matches):
        name = m.group(1).strip()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        content = body[start:end]
        parts.append(f"<section class=\"md\"><h2>{_inline(name, report_dir)}</h2>")
        if name.lower() == "findings":
            parts.append(_render_findings(content, report_dir))
        else:
            parts.append(_render_blocks(content, report_dir))
        parts.append("</section>")

    auditor = fm.get("auditor", "report")
    scope = fm.get("scope", "")
    title = f"{auditor} audit — {scope}".strip(" —")
    return _page(title, "\n".join(parts))


def render_to_file(md_path: str | Path) -> Path:
    md_path = Path(md_path)
    out = md_path.with_suffix(".html")
    out.write_text(render(md_path), encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: render_report_html.py <report.md> [<report.md> ...]", file=sys.stderr)
        return 2
    ok = True
    for arg in argv:
        try:
            out = render_to_file(arg)
            print(f"rendered: {out}")
        except Exception as exc:  # noqa: BLE001 — report path + reason, keep going
            ok = False
            print(f"FAILED: {arg}: {exc}", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
