"""Virtue #2: Competition Accessibility.

Can qualified non-incumbents realistically compete? Clear self-contained scope,
sufficient background information, capability-based qualifications, and
transparent evaluation criteria that don't assume insider knowledge.

Usage:
    from spotting_concrete_boats.prompts.virtue__competition_accessibility import (
        USER_PROMPT, RESULT_SCHEMA,
    )
"""

from typing import Literal

from pydantic import BaseModel, computed_field

from spotting_concrete_boats.prompts.common import STRENGTH_LABELS, VirtueEvidence


class CompetitionAccessibilityResult(BaseModel):
    """Virtue #2: Solicitation enables qualified non-incumbents to compete."""

    sufficient_content: bool
    strength: Literal[1, 2, 3]
    evidence: list[VirtueEvidence]
    reasoning: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def strength_label(self) -> str:
        """Human-readable strength label."""
        return STRENGTH_LABELS[self.strength]


RESULT_SCHEMA = CompetitionAccessibilityResult

USER_PROMPT = """\
Analyze the solicitation for **Competition Accessibility** (Virtue #2).

## Definition

Competition accessibility measures whether a qualified vendor who has never \
worked on this contract could realistically submit a competitive proposal \
based solely on the solicitation materials. Strong accessibility means the \
solicitation is self-contained, clearly scoped, and evaluates capability \
rather than familiarity.

The core test: **Could a qualified newcomer compete on equal footing?** When \
a solicitation provides sufficient background, clearly defines scope and \
expectations, and evaluates demonstrated capability rather than incumbent \
knowledge, it enables genuine competition. When it assumes familiarity with \
current operations, references undisclosed systems, or structures evaluation \
to favor insiders, it restricts the competitive field.

## What to Look For

- **Self-contained scope description**: The solicitation explains the mission \
context, current environment, systems involved, and operational background — \
a newcomer can understand what they're bidding on without prior involvement.
- **Clear background and context**: Government-furnished information about \
existing systems, infrastructure, data volumes, user populations, and \
operational tempo that a newcomer would need to estimate effort.
- **Capability-based qualifications**: Evaluation criteria that assess relevant \
experience, technical approach, and demonstrated ability — not specific \
knowledge of this particular contract or agency.
- **Transparent evaluation criteria**: Clearly stated factors, subfactors, \
and their relative importance. Offerors understand how proposals will be \
scored and what matters most.
- **Transition planning**: Explicit recognition that a new vendor may win, \
with provisions for knowledge transfer, transition periods, and access to \
incumbent documentation.

## What is NOT Competition Accessibility

- **Absence of insider bias**: A solicitation that avoids explicit incumbent \
favoritism is NOT the same as one that actively enables competition. Avoiding \
the "Insider Rewards" sin is not the same as achieving this virtue.
- **Open procurement type**: Being a full-and-open competition doesn't mean \
the solicitation is actually accessible. The procurement mechanism matters \
less than the content.
- **Low barrier to entry**: This virtue is not about making it easy for \
unqualified vendors. It's about ensuring qualified vendors can compete \
regardless of whether they held the prior contract.
- **Maximum competition**: Some legitimate requirements naturally limit the \
competitive field (security clearances, specialized certifications). These \
constraints don't reduce accessibility — they define the qualified pool.

## Relationship to Sins

This virtue is NOT the inverse of the "Insider Rewards" sin. A solicitation \
can avoid explicit incumbent favoritism and still be opaque to newcomers. The \
sin asks "does the solicitation structurally advantage the incumbent?" This \
virtue asks "does the solicitation give newcomers what they need to compete?" \
These are independent dimensions — a solicitation can avoid bias while still \
being inaccessible.

## Strength Rubric

**1 — Weak**: The solicitation assumes insider knowledge. Key context is \
missing — references to undisclosed systems, undefined acronyms, scope that \
requires familiarity with current operations to understand. A qualified \
newcomer would struggle to write a competitive proposal without informal \
knowledge of the current contract.

**2 — Moderate**: Mostly accessible with some barriers. The solicitation \
provides reasonable background and clear scope in most areas, but gaps remain — \
some systems or processes referenced without explanation, evaluation criteria \
that could subtly favor incumbent knowledge, or missing operational data \
needed for realistic estimation.

**3 — Strong**: Fully competitive from the solicitation alone. Comprehensive \
background, self-contained scope, capability-based evaluation criteria, and \
explicit transition provisions. A qualified newcomer has everything needed to \
submit a competitive, well-informed proposal.

## Evidence Guidelines

- Quote specific language that demonstrates accessibility — background \
sections, government-furnished information, capability-based evaluation \
criteria, transition provisions.
- For each quote, explain WHY it enables competition — what information it \
provides and how a newcomer would use it.
- Provide 2-5 evidence items for strength 2-3. For strength 1, evidence may \
be empty or contain 1 example of where accessibility is notably lacking.
- Look especially in background sections, evaluation criteria, Section L/M, \
GFI/GFP listings, and transition requirements.
- Use `reasoning` for your overall judgment: synthesize the evidence, weigh \
barriers, and explain why you assigned the strength you did. Individual \
`evidence` items should each stand alone — a specific quote and why it matters.

## Insufficient Content

Set `sufficient_content` to false if the solicitation text lacks enough detail \
to meaningfully assess this virtue — e.g., the posting is a brief notice, \
amendment, sources sought, or pre-solicitation without an attached SOW/PWS. \
When false, set strength to 1, evidence to an empty list, and use reasoning \
to explain what was missing.
"""
