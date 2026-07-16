# AI Design Heuristics (PAIR + Amershi's Guidelines for Human-AI Interaction)

Heuristics for **non-deterministic, AI-driven** features — generative outputs, ML
predictions, assistants, recommendations. Derived from Google PAIR's People + AI
Guidebook and Amershi et al., *Guidelines for Human-AI Interaction* (CHI 2019).

**Applicability gate:** these apply **only where the product has AI features.** If the
in-scope surface has no AI/ML behavior, record this lens as *not applicable* in the
appendix — do not invent AI findings. Cite as "AI-Heuristics — <theme>".

## The three core themes (the persona's primary lens)

### 1. Expectation setting — communicate what the AI can and can't do
- Does the UI make the system's capabilities and limits clear *before* use, so users form
  an accurate mental model?
- Are confidence, uncertainty, or "this may be wrong" signals shown where outputs are
  probabilistic?
- Look for over-promising copy, hidden limitations, and no signal that a result is
  AI-generated.

### 2. Explainability — give context and rationale for outputs
- Can the user tell *why* the AI produced a given output (sources, factors, "because…")?
- Is enough context shown to judge whether to trust or act on the result?
- Look for unexplained decisions the user must accept blindly.

### 3. Correction pathways — keep the user in control of non-deterministic output
- Can the user easily **edit, reject, regenerate, or undo** an AI output?
- Is there a graceful path when the AI is wrong (dismiss, give feedback, fall back to
  manual)?
- Look for dead-ends where a bad AI result can't be overridden.

## Supporting guidelines (Amershi et al., abbreviated)

- **Initially:** make clear what the system can do (G1) and how well (G2).
- **During interaction:** show contextually relevant information (G4); match social norms
  and mitigate bias (G5–G6).
- **When wrong:** support efficient invocation, dismissal, and correction (G7–G9);
  scope services when in doubt; explain why the system did what it did (G11).
- **Over time:** remember recent interactions, learn from behavior, update cautiously, and
  encourage granular feedback (G12–G18).

## Distinctive contribution

This lens barely overlaps Nielsen/Shneiderman — it targets failure modes unique to
probabilistic systems (unclear capability, unexplained output, no correction path). When
AI features are present, weight it heavily; it catches issues the classic heuristics
cannot express.
