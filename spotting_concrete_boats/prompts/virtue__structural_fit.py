"""Virtue #3: Structural Fit.

Is the contract vehicle appropriate for the work? Contract type matched to
risk profile, realistic period of performance, aligned evaluation criteria,
and an overall structure that supports good outcomes rather than working
against them.

Usage:
    from spotting_concrete_boats.prompts.virtue__structural_fit import USER_PROMPT, RESULT_SCHEMA
"""

from typing import Literal

from pydantic import BaseModel, computed_field

from spotting_concrete_boats.prompts.common import STRENGTH_LABELS, VirtueEvidence


class StructuralFitResult(BaseModel):
    """Virtue #3: Contract vehicle and structure are appropriate for the work."""

    sufficient_content: bool
    strength: Literal[1, 2, 3]
    evidence: list[VirtueEvidence]
    reasoning: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def strength_label(self) -> str:
        """Human-readable strength label."""
        return STRENGTH_LABELS[self.strength]


RESULT_SCHEMA = StructuralFitResult

USER_PROMPT = """\
Analyze the solicitation for **Structural Fit** (Virtue #3).

## Definition

Structural fit measures whether the contract vehicle, period of performance, \
evaluation criteria, and overall acquisition structure are appropriate for the \
nature of the work being procured. Good structural fit means the government \
chose a contract type that allocates risk appropriately, set a realistic \
timeline, and designed evaluation criteria that select for the right things.

The core test: **Does the contract structure support good outcomes?** When \
the contract type matches the work's risk profile, the period of performance \
is realistic, and evaluation criteria align with what actually matters for \
success, the structure enables rather than undermines good performance. When \
there's a mismatch — a firm-fixed-price contract for undefined R&D, a \
12-month PoP for a multi-year transformation, or evaluation criteria that \
ignore technical quality — the structure works against the mission.

## What to Look For

- **Contract type matched to risk**: Firm-fixed-price for well-defined, \
repeatable work. Cost-plus or T&M for uncertain or evolving scope. The type \
should reflect who can best manage the risk — not just the government's \
preference for administrative simplicity.
- **Realistic period of performance**: The PoP allows enough time for the \
work described, including ramp-up, transition, and any phased delivery. \
Option periods structured logically (not reflexive one-year options for \
work that doesn't align to annual cycles).
- **Aligned evaluation criteria**: What the government says it values in \
proposals matches what the contract actually requires. If the work is \
technically complex, technical approach should outweigh price. If it's \
commoditized, LPTA may be appropriate.
- **Appropriate contract scope**: The work fits naturally into a single \
contract rather than being artificially bundled or split. Related work \
is kept together; unrelated work isn't forced into the same vehicle.
- **CLIN structure that supports management**: Contract Line Item Numbers \
organized to enable meaningful financial tracking and performance measurement, \
not just administrative convenience.

## What is NOT Structural Fit

- **Preference for a specific contract type**: There is no universally "right" \
contract type. FFP, T&M, cost-plus, IDIQ — each is appropriate in different \
contexts. The question is whether the choice fits THIS work.
- **Maximum flexibility**: Indefinite-delivery/indefinite-quantity vehicles \
provide flexibility, but flexibility without defined scope can also be a \
structural problem. More flexibility is not always better fit.
- **Longest possible PoP**: A longer period of performance is not inherently \
better. The question is whether the PoP matches the work's natural cadence \
and allows for realistic delivery.
- **Lowest price**: LPTA evaluation is appropriate for commoditized work. The \
issue arises when LPTA is used for complex work where quality differentiation \
matters.

## Relationship to Sins

This virtue has no direct sin counterpart. None of the existing sins evaluate \
whether the contract structure itself is appropriate. Structural fit is a \
purely positive assessment — it identifies when the government made good \
acquisition design choices that set the contract up for success.

## Strength Rubric

**1 — Weak**: Clear structural mismatch. The contract type doesn't fit the \
work's risk profile (e.g., FFP for undefined scope, T&M for well-defined \
deliverables), the PoP is unrealistic, evaluation criteria don't align with \
what matters, or the scope is awkwardly bundled. The structure works against \
good outcomes.

**2 — Moderate**: Structure is defensible but not optimal. The contract type \
is reasonable even if not ideal, the PoP is workable, and evaluation criteria \
are adequate. No major mismatches, but the structure doesn't actively support \
the best outcomes either. A competent but uninspired acquisition design.

**3 — Strong**: Structure supports good outcomes. Contract type matches the \
work's risk profile, PoP is realistic and well-phased, evaluation criteria \
prioritize what matters most for success, and the overall design reflects \
thoughtful acquisition planning. The structure enables rather than constrains \
good performance.

## Evidence Guidelines

- Quote specific structural elements — contract type designations, PoP \
provisions, evaluation factor weightings, CLIN structures, scope definitions.
- For each quote, explain WHY it demonstrates good (or poor) structural fit — \
what about the work makes this structural choice appropriate or inappropriate.
- Provide 2-5 evidence items for strength 2-3. For strength 1, evidence may \
be empty or contain 1 example of the most significant structural mismatch.
- Look especially in Sections B (supplies/services), F (deliveries/performance), \
L (instructions), and M (evaluation factors).
- Use `reasoning` for your overall judgment: synthesize the evidence, weigh \
structural strengths against weaknesses, and explain why you assigned the \
strength you did. Individual `evidence` items should each stand alone — a \
specific quote and why it matters.

## Insufficient Content

Set `sufficient_content` to false if the solicitation text lacks enough detail \
to meaningfully assess this virtue — e.g., the posting is a brief notice, \
amendment, sources sought, or pre-solicitation without an attached SOW/PWS. \
When false, set strength to 1, evidence to an empty list, and use reasoning \
to explain what was missing.
"""
