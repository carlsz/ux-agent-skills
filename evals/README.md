# Evals

How we verify the auditor suite triggers correctly and behaves correctly. Modelled on
[addyosmani/agent-skills' evals](https://github.com/addyosmani/agent-skills/blob/main/evals/README.md),
adapted to this plugin's Python tooling and using [Sprout](https://github.com/carlsz/sprout)
as the behavioral target (no synthetic fixtures — a real app exercises the auditors).

## Layout

```
evals/
├── README.md                    # this file
├── run_evals.py                 # the runner (stdlib Python)
├── cases/
│   ├── usability-audit.json     # trigger + behavioral cases per skill
│   ├── ux-audit.json
│   └── competitors.json         # descriptions of external owners, for routing
└── results/                     # gitignored grading output
```

## Case format

Each `cases/<skill>.json` follows the agent-skills schema, plus a `behavioral_target`:

```json
{
  "skill_name": "usability-audit",
  "trigger": {
    "positive": [ { "prompt": "…", "top_k": 1 } ],
    "negative": [ { "prompt": "…", "owner": "web-quality-skills:accessibility" } ]
  },
  "behavioral_target": { "name": "sprout", "repo": "…", "run": "npm install && npm run dev" },
  "evals": [
    { "id": 1, "prompt": "…", "expected_output": "…",
      "expectations": ["verifiable statement", "…"], "trust_level": "provisional" }
  ]
}
```

- **`trigger.positive`** — realistic prompts that should rank the skill within `top_k`
  (default 3; use 1 for signature requests).
- **`trigger.negative`** — prompts owned by a *different* skill; ours must not rank first.
  `owner` names the competitor (its description lives in `competitors.json`).
- **`evals[]`** — behavioral cases: `expectations` are verifiable statements a grader
  checks against the produced reports (behaviors, not phrasings).
- **`trust_level`** — `provisional` for behavioral evals whose grading isn't yet fully
  automated.

**Minimums per skill:** ≥3 positive triggers, ≥2 negative triggers, ≥1 behavioral eval.

## Tier 2 — Trigger & routing (deterministic, CI)

```
python3 evals/run_evals.py
```

Validates every case's schema + minimums, then approximates routing with a **stemmed
TF-IDF** over skill descriptions (ours from each `SKILL.md`, competitors from
`competitors.json`): each positive prompt must rank its skill within `top_k`, each
negative must **not** rank the skill first, and our descriptions must not collide
(error ≥ 0.75 similarity, warn ≥ 0.50). It reports the trigger **rank-1 rate**. This is a
lexical approximation of the real router — it catches missing vocabulary and over-broad
descriptions. Guarded in CI by [`tests/test_evals.py`](../tests/test_evals.py).

## Tier 3 — Behavioral (token-consuming, on demand)

Behavioral evals run the auditors against **Sprout** and grade the output. Print a
skill's behavioral evals:

```
python3 evals/run_evals.py --behavioral usability-audit
```

Then run the prompt in a **fresh Claude session** with both plugins loaded — this plugin
(for the commands) and [`web-quality-skills`](https://github.com/addyosmani/web-quality-skills)
(the wrapped accessibility / web-performance auditors):

```
claude --plugin-dir /path/to/ux-agent-skills-v2
```

Paste the eval prompt (or, for the full suite roll-up, this):

```
Clone https://github.com/carlsz/sprout into a temp dir, npm install, and start the dev
server. Then run /ux-agent-skills:ux-audit http://localhost:<port> against it. Fan out to
usability (native) + accessibility + web performance (wrapping web-quality-skills);
normalize each into a .ux/audits contract report; skip+disclose any auditor whose skill
isn't installed; write a rollup with a go/no-go verdict. Findings only — do not edit
Sprout's code. Note: `npm install` may touch package-lock.json (a setup side-effect, not
an audit write) — revert it before the safety check.
```

Finally, grade the produced reports:

```
python3 evals/run_evals.py --grade usability-audit --repo <sprout-dir> \
    <sprout-dir>/.ux/audits/usability-*.md
```

The grader validates each report against the shared contract
([`scripts/validate_report.py`](../scripts/validate_report.py)), runs the safety-invariant
check ([`scripts/audit_safety.py`](../scripts/audit_safety.py)), auto-checks the mechanical
expectations (contract validity, framework citations, writes confined to `.ux/audits/`),
and writes `results/<skill>-grading.json`. Semantic expectations that can't be checked
mechanically are flagged for LLM/human grading — that's what `trust_level: provisional`
tracks.
