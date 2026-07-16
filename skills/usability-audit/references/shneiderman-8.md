# Shneiderman's 8 Golden Rules of Interface Design

Ben Shneiderman's rules for predictable, efficient interaction — strongest for
data-dense, multi-step, and expert/enterprise interfaces. Cite as
"Shneiderman #N — <rule>". Many overlap Nielsen's heuristics; when a finding is
covered by both, attribute it to its **primary** framework and note the corroborating
one rather than filing it twice.

| # | Rule | Evaluation lens — look for |
|---|------|----------------------------|
| 1 | **Strive for consistency** | Identical actions, terms, layout, and color in identical situations; consistent prompts, menus, and help. Watch for the same concept named or styled two ways. |
| 2 | **Seek universal usability** | Does the design serve the range from novice to expert, and diverse abilities/devices? Look for explanations for novices and shortcuts for experts; accommodation of accessibility needs. |
| 3 | **Offer informative feedback** | Every user action gets a system response, proportionate to the action (modest for frequent/minor, substantial for infrequent/major). |
| 4 | **Design dialogs to yield closure** | Multi-step sequences have a clear beginning, middle, and end, with a completion signal that tells the user they're done (e.g. a confirmation after checkout). |
| 5 | **Prevent errors** | The design makes errors hard to commit — constrained inputs, sensible defaults, disabled invalid actions — and recovers gracefully when they happen. |
| 6 | **Permit easy reversal of actions** | Undo/redo for units of action; users can explore without fear because mistakes are reversible. |
| 7 | **Keep users in control (internal locus of control)** | Users are the initiators, not the responders; the system is predictable and doesn't surprise, block, or force. |
| 8 | **Reduce short-term memory load** | Displays are simple; information needed across steps is carried forward, not memorized. Recognition over recall (cf. Nielsen #6). |

## Distinctive contribution vs. Nielsen

Shneiderman adds emphasis Nielsen's 10 underweight:
- **#2 Universal usability** — explicitly designing for the novice↔expert spectrum and
  diverse abilities at once.
- **#4 Closure** — the *completion* signal at the end of a task sequence.
- **#7 Locus of control** — the user as the initiating agent throughout.

Weight these when auditing complex or expert workflows; for general feedback,
consistency, error prevention, and reversal, prefer the Nielsen citation and note
Shneiderman as corroborating.
