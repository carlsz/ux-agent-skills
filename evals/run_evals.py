#!/usr/bin/env python3
"""Eval runner for the ux-agent-skills auditor suite.

Two tiers, modelled on addyosmani/agent-skills:

  Tier 2 — Trigger & Routing (deterministic, CI):
      python3 evals/run_evals.py
    Validates each case's schema + minimums, then approximates routing with a stemmed
    TF-IDF over skill descriptions: every positive prompt must rank its skill within
    top_k, every negative prompt must NOT rank the skill first (its declared owner should
    outrank it), and our skill descriptions must not collide.

  Tier 3 — Behavioral (token-consuming, on demand):
      python3 evals/run_evals.py --behavioral usability-audit
    Prints the behavioral target (Sprout) setup and each eval's prompt + expectations, for
    a Claude session to run. Then grade the produced reports:
      python3 evals/run_evals.py --grade usability-audit --repo <sprout-dir> \
          <sprout-dir>/.ux/audits/usability-*.md
    validates each report against the contract, runs the safety check on the host repo,
    checks the mechanical expectations, and writes evals/results/<skill>-grading.json.

Stdlib only. The routing model is a lexical approximation, not the real router — it
catches missing vocabulary and over-broad descriptions, the same failure modes agent-
skills' Tier 2 targets.
"""
from __future__ import annotations

import glob
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = ROOT / "evals" / "cases"
RESULTS_DIR = ROOT / "evals" / "results"
sys.path.insert(0, str(ROOT / "scripts"))

COLLISION_ERROR = 0.75
COLLISION_WARN = 0.50
MIN_POSITIVE, MIN_NEGATIVE, MIN_BEHAVIORAL = 3, 2, 1

STOPWORDS = {
    "a", "an", "the", "of", "for", "and", "or", "to", "my", "this", "that", "is", "are",
    "with", "in", "on", "it", "its", "me", "i", "you", "your", "app", "site", "page",
    "screen", "before", "against", "all", "run", "do", "give", "using", "use",
}


# --------------------------------------------------------------------------- lexical
def stem(word: str) -> str:
    for suf in ("ization", "izations", "ations", "ation", "ing", "ers", "er", "ed",
                "ies", "es", "s", "ly"):
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            return word[: -len(suf)]
    return word


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [stem(w) for w in words if w not in STOPWORDS and len(w) > 1]


def build_idf(docs: dict[str, list[str]]) -> dict[str, float]:
    n = len(docs)
    df: Counter = Counter()
    for tokens in docs.values():
        for t in set(tokens):
            df[t] += 1
    return {t: math.log((n + 1) / (c + 1)) + 1 for t, c in df.items()}


def tfidf_vec(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    tf = Counter(tokens)
    return {t: (c / len(tokens)) * idf.get(t, math.log(2) + 1)
            for t, c in tf.items()} if tokens else {}


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


# ------------------------------------------------------------------------- loading
def _frontmatter_description(md_path: Path) -> str:
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return ""
    fm = text.split("---", 2)[1]
    m = re.search(r"^description:\s*(.+)$", fm, re.MULTILINE)
    return m.group(1).strip() if m else ""


def load_routing_corpus() -> dict[str, str]:
    """name -> description, for our skills plus the declared competitors."""
    corpus: dict[str, str] = {}
    for skill_md in sorted(ROOT.glob("skills/*/SKILL.md")):
        name = skill_md.parent.name
        corpus[name] = _frontmatter_description(skill_md)
    competitors = json.loads((CASES_DIR / "competitors.json").read_text())["competitors"]
    corpus.update(competitors)
    return corpus


def load_cases() -> list[dict]:
    cases = []
    for path in sorted(CASES_DIR.glob("*.json")):
        if path.name == "competitors.json":
            continue
        cases.append(json.loads(path.read_text(encoding="utf-8")))
    return cases


# ------------------------------------------------------------------------- checks
def validate_schema(case: dict) -> list[str]:
    errs: list[str] = []
    name = case.get("skill_name", "<unknown>")
    if not case.get("skill_name"):
        errs.append("case missing 'skill_name'")
    trig = case.get("trigger", {})
    pos, neg = trig.get("positive", []), trig.get("negative", [])
    if len(pos) < MIN_POSITIVE:
        errs.append(f"{name}: needs >= {MIN_POSITIVE} positive triggers, has {len(pos)}")
    if len(neg) < MIN_NEGATIVE:
        errs.append(f"{name}: needs >= {MIN_NEGATIVE} negative triggers, has {len(neg)}")
    for p in pos:
        if "prompt" not in p:
            errs.append(f"{name}: a positive trigger has no 'prompt'")
    for ncase in neg:
        if "prompt" not in ncase or "owner" not in ncase:
            errs.append(f"{name}: a negative trigger needs 'prompt' and 'owner'")
    evals = case.get("evals", [])
    if len(evals) < MIN_BEHAVIORAL:
        errs.append(f"{name}: needs >= {MIN_BEHAVIORAL} behavioral eval, has {len(evals)}")
    for ev in evals:
        for key in ("id", "prompt", "expected_output", "expectations"):
            if key not in ev:
                errs.append(f"{name}: eval {ev.get('id', '?')} missing {key!r}")
    return errs


def check_routing(case: dict, corpus: dict[str, str], idf, vecs) -> tuple[list[str], int, int]:
    """Return (errors, rank1_hits, positive_count)."""
    errs: list[str] = []
    name = case["skill_name"]
    if name not in vecs:
        return [f"{name}: no description found for routing"], 0, 0

    def rank(prompt: str) -> list[tuple[str, float]]:
        q = tfidf_vec(tokenize(prompt), idf)
        scored = [(n, cosine(q, v)) for n, v in vecs.items()]
        return sorted(scored, key=lambda x: x[1], reverse=True)

    rank1 = 0
    positives = case["trigger"]["positive"]
    for p in positives:
        ranking = rank(p["prompt"])
        top_k = p.get("top_k", 3)
        names_in_k = [n for n, _ in ranking[:top_k]]
        if ranking and ranking[0][0] == name:
            rank1 += 1
        if name not in names_in_k:
            errs.append(f"{name}: positive {p['prompt']!r} did not rank the skill in "
                        f"top-{top_k} (got {names_in_k})")
    for ncase in case["trigger"]["negative"]:
        ranking = rank(ncase["prompt"])
        if ranking and ranking[0][0] == name:
            errs.append(f"{name}: negative {ncase['prompt']!r} wrongly ranked the skill "
                        f"first (owner should be {ncase['owner']!r})")
    return errs, rank1, len(positives)


def check_collisions(vecs: dict[str, dict], our_skills: list[str]) -> list[str]:
    errs: list[str] = []
    for i, a in enumerate(our_skills):
        for b in our_skills[i + 1:]:
            sim = cosine(vecs[a], vecs[b])
            if sim >= COLLISION_ERROR:
                errs.append(f"description collision: {a!r} vs {b!r} similarity {sim:.2f} "
                            f">= {COLLISION_ERROR}")
            elif sim >= COLLISION_WARN:
                print(f"  warn: {a!r} vs {b!r} similarity {sim:.2f} >= {COLLISION_WARN}")
    return errs


# ------------------------------------------------------------------- tier 2 entry
def run_tier2() -> int:
    corpus = load_routing_corpus()
    idf = build_idf({n: tokenize(d) for n, d in corpus.items()})
    vecs = {n: tfidf_vec(tokenize(d), idf) for n, d in corpus.items()}
    cases = load_cases()
    our_skills = [c["skill_name"] for c in cases]

    failures: list[str] = []
    rank1_total = pos_total = 0
    for case in cases:
        failures += validate_schema(case)
        errs, r1, pc = check_routing(case, corpus, idf, vecs)
        failures += errs
        rank1_total += r1
        pos_total += pc
    failures += check_collisions(vecs, our_skills)

    print(f"Tier 2 — {len(cases)} skills, "
          f"trigger rank-1 rate {rank1_total}/{pos_total}")
    if failures:
        print("FAIL — evals (Tier 2):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS — evals (Tier 2: schema, minimums, routing, collisions)")
    return 0


# ------------------------------------------------------------- tier 3 (on demand)
def run_behavioral(skill: str) -> int:
    case_path = CASES_DIR / f"{skill}.json"
    if not case_path.exists():
        print(f"no case file for {skill!r}", file=sys.stderr)
        return 2
    case = json.loads(case_path.read_text())
    tgt = case.get("behavioral_target", {})
    print(f"# Behavioral evals — {skill}\n")
    print(f"Target: {tgt.get('name')} ({tgt.get('repo')})")
    print(f"Run:    {tgt.get('run')}\n")
    for ev in case["evals"]:
        print(f"## eval {ev['id']} [{ev.get('trust_level', 'provisional')}]")
        print(f"Prompt: {ev['prompt']}")
        print(f"Expected: {ev['expected_output']}")
        print("Expectations (graded against the produced reports):")
        for e in ev["expectations"]:
            print(f"  - {e}")
        print()
    print("Run the prompt in a Claude session with both plugins loaded, then grade with:")
    print(f"  python3 evals/run_evals.py --grade {skill} --repo <target-dir> "
          f"<target-dir>/.ux/audits/*.md")
    return 0


def run_grade(skill: str, repo: str | None, report_paths: list[str]) -> int:
    from validate_report import validate  # scripts/validate_report.py
    try:
        from audit_safety import changes_confined_to
    except Exception:  # pragma: no cover
        changes_confined_to = None

    case = json.loads((CASES_DIR / f"{skill}.json").read_text())
    expectations = case["evals"][0]["expectations"]

    reports = []
    for pat in report_paths:
        reports.extend(sorted(glob.glob(pat)))
    result = {"skill": skill, "reports": [], "safety": None, "expectations": []}

    for r in reports:
        errs = validate(r)
        text = Path(r).read_text(encoding="utf-8").lower()
        result["reports"].append({
            "path": r,
            "contract_valid": not errs,
            "errors": errs,
            "cites_framework": any(k in text for k in
                                   ("nielsen", "shneiderman", "npcis", "wcag",
                                    "core web vital")),
        })

    if repo and changes_confined_to:
        violations = changes_confined_to(repo, ".ux/audits/")
        result["safety"] = {"confined": not violations, "violations": violations}

    # Mechanical expectation coverage; semantic ones are flagged for LLM/human grading.
    for e in expectations:
        low = e.lower()
        auto = None
        if "validate" in low or "contract" in low:
            auto = all(rr["contract_valid"] for rr in result["reports"]) \
                if result["reports"] else False
        elif "cite" in low or "framework" in low or "nielsen" in low:
            auto = all(rr["cites_framework"] for rr in result["reports"]) \
                if result["reports"] else False
        elif "confined" in low or "not edit" in low or "outside" in low:
            auto = result["safety"]["confined"] if result.get("safety") else None
        result["expectations"].append({"text": e, "auto_pass": auto})

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"{skill}-grading.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    auto_checked = [x for x in result["expectations"] if x["auto_pass"] is not None]
    passed = [x for x in auto_checked if x["auto_pass"]]
    print(f"graded {len(reports)} report(s); wrote {out.relative_to(ROOT)}")
    print(f"auto-checked expectations: {len(passed)}/{len(auto_checked)} pass "
          f"({len(result['expectations']) - len(auto_checked)} need LLM/human grading)")
    ok = (all(rr["contract_valid"] for rr in result["reports"]) and result["reports"]
          and (result["safety"] is None or result["safety"]["confined"]))
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if not argv:
        return run_tier2()
    if argv[0] == "--behavioral" and len(argv) >= 2:
        return run_behavioral(argv[1])
    if argv[0] == "--grade" and len(argv) >= 2:
        skill = argv[1]
        repo = None
        rest = argv[2:]
        if "--repo" in rest:
            i = rest.index("--repo")
            repo = rest[i + 1]
            rest = rest[:i] + rest[i + 2:]
        return run_grade(skill, repo, rest)
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
