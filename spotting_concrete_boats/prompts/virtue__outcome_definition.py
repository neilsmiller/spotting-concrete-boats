"""Virtue #1: Outcome Definition.

Does the solicitation define what success looks like? Performance standards,
SLAs, acceptance criteria, and measurable outcomes that hold the vendor
accountable for results — not just activities.

Usage:
    from spotting_concrete_boats.prompts.virtue__outcome_definition import (
        USER_PROMPT, RESULT_SCHEMA,
    )
"""

from typing import Literal

from pydantic import BaseModel, computed_field

from spotting_concrete_boats.prompts.common import STRENGTH_LABELS, VirtueEvidence


class OutcomeDefinitionResult(BaseModel):
    """Virtue #1: Solicitation defines measurable success criteria and outcomes."""

    sufficient_content: bool
    strength: Literal[1, 2, 3]
    evidence: list[VirtueEvidence]
    reasoning: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def strength_label(self) -> str:
        """Human-readable strength label."""
        return STRENGTH_LABELS[self.strength]


RESULT_SCHEMA = OutcomeDefinitionResult

USER_PROMPT = """\
Analyze the solicitation for **Outcome Definition** (Virtue #1).

## Definition

Outcome definition measures whether a solicitation articulates what success \
looks like — not just what work must be performed, but what results that work \
must achieve. Strong outcome definition includes performance standards, SLAs, \
acceptance criteria, measurable targets, and accountability mechanisms tied to \
results rather than activities.

The core test: **Could you objectively determine whether this contract \
succeeded?** When a solicitation defines clear, measurable outcomes — uptime \
targets, response times, quality thresholds, mission metrics — an independent \
observer could evaluate vendor performance against those standards. When it \
only describes tasks and activities, success is subjective.

## What to Look For

- **Performance standards and SLAs**: "System availability shall be 99.9%" or \
"Tier 1 tickets resolved within 4 business hours." Concrete, measurable targets \
tied to contract deliverables.
- **Acceptance criteria for deliverables**: Clear conditions under which the \
government will accept or reject work products — not just "deliverable shall be \
submitted" but "deliverable shall demonstrate X capability."
- **Outcome-based evaluation factors**: Award criteria or QASP metrics that \
evaluate results (user satisfaction, system performance, mission achievement) \
rather than process compliance.
- **Measurable objectives**: Quantified goals the work is expected to achieve — \
reduction targets, throughput improvements, quality benchmarks.
- **Accountability tied to results**: Incentive/disincentive structures, \
performance-based payments, or cure/termination triggers linked to outcome \
metrics rather than activity completion.

## What is NOT Outcome Definition

- **Absence of compliance theater**: A solicitation that avoids excessive \
reporting requirements is NOT the same as one that defines outcomes. Avoiding \
a sin is not the same as achieving this virtue.
- **Vague aspirational language**: "The contractor shall provide excellent \
service" or "ensure mission success" without measurable criteria is not \
outcome definition — it's unenforceable language.
- **Activity-based deliverables**: "Submit monthly reports" or "conduct weekly \
meetings" describe activities, not outcomes. They are not evidence of this \
virtue unless paired with what those reports must demonstrate.
- **Compliance requirements**: FISMA, Section 508, or regulatory mandates are \
constraints, not outcomes defined by the solicitation.

## Relationship to Sins

This virtue is NOT the inverse of the "Compliance Over Outcomes" sin. A \
solicitation can avoid compliance theater entirely and still fail to define \
what success looks like. The sin asks "does accountability measure process \
instead of results?" This virtue asks "does the solicitation affirmatively \
define what good results are?" These are independent dimensions — a \
solicitation can score well on one and poorly on the other.

## Strength Rubric

**1 — Weak**: No meaningful success metrics. The solicitation describes tasks \
and activities without defining what results those tasks should achieve. An \
evaluator could not objectively determine whether the contract succeeded. \
Deliverables are defined by submission, not quality.

**2 — Moderate**: Some outcome measures exist but gaps remain. The solicitation \
may define SLAs for some areas but leave others purely activity-based, or it \
may include general performance expectations without specific measurable \
targets. Success is partially defined.

**3 — Strong**: Clear, measurable criteria are central to the solicitation's \
accountability structure. Performance standards, acceptance criteria, and \
outcome metrics are specific, quantified, and tied to contract administration. \
An independent observer could evaluate whether the vendor succeeded.

## Evidence Guidelines

- Quote the specific language that demonstrates outcome definition — SLAs, \
acceptance criteria, performance targets, measurable objectives.
- For each quote, explain WHY it constitutes meaningful outcome definition — \
what makes it measurable and enforceable.
- Provide 2-5 evidence items for strength 2-3. For strength 1, evidence may \
be empty or contain 1 example of where outcomes should have been defined.
- Look especially in Quality Assurance Surveillance Plans, performance \
requirements sections, evaluation criteria, and deliverable descriptions.
- Use `reasoning` for your overall judgment: synthesize the evidence, weigh \
gaps, and explain why you assigned the strength you did. Individual `evidence` \
items should each stand alone — a specific quote and why it matters.

## Insufficient Content

Set `sufficient_content` to false if the solicitation text lacks enough detail \
to meaningfully assess this virtue — e.g., the posting is a brief notice, \
amendment, sources sought, or pre-solicitation without an attached SOW/PWS. \
When false, set strength to 1, evidence to an empty list, and use reasoning \
to explain what was missing.
"""
