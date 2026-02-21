"""Sin #3: Rule Pools.

Rule pools occur when a solicitation cites overwhelming lists of regulations,
standards, and compliance frameworks without providing context for how they apply
to the specific work being solicited. The effect is to create a compliance burden
that favors incumbents who already know which rules actually matter.

Usage:
    from spotting_concrete_boats.prompts.sin__rule_pools import USER_PROMPT, RESULT_SCHEMA
"""

from typing import Literal

from pydantic import BaseModel, computed_field

from spotting_concrete_boats.prompts.common import SEVERITY_LABELS, SinEvidence


class RulePoolsResult(BaseModel):
    """Sin #3: Overwhelming lists of regulations cited without context or relevance."""

    sufficient_content: bool
    severity: Literal[1, 2, 3]
    evidence: list[SinEvidence]
    reasoning: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def severity_label(self) -> str:
        """Human-readable severity label."""
        return SEVERITY_LABELS[self.severity]


RESULT_SCHEMA = RulePoolsResult

USER_PROMPT = """\
Analyze the solicitation for **Rule Pools** (Sin #3).

## Definition

Rule pools occur when a solicitation cites overwhelming lists of regulations, \
standards, policies, and compliance frameworks without providing context for how \
each one applies to the specific work being solicited. Instead of curating a \
focused set of genuinely applicable requirements, the solicitation dumps a bulk \
list of "Applicable Documents" that vendors must parse, interpret, and comply with \
— many of which have questionable or no relevance to the actual work.

The core test: **Does this solicitation distinguish between regulations that \
genuinely govern this work and regulations that are simply on a master list?** \
When a solicitation cites dozens of policies without explaining their applicability, \
vendors cannot tell which rules actually matter — and the agency may not know either.

## What Constitutes Rule Pools

- **Bulk "Applicable Documents" lists**: Long lists (typically 20+) of regulations, \
directives, executive orders, and agency policies cited without explanation of how \
each applies to the specific scope of work.
- **Irrelevant or tangential regulations**: Policies that have no logical connection \
to the work being solicited — e.g., an executive order on energy-efficient standby \
power devices cited in a software services contract, or ID badge policies cited in \
a text-messaging RFP.
- **Contradictory compliance requirements**: Regulations in the list that contradict \
the solicitation's own purpose — e.g., a policy prohibiting SMS communications cited \
in a solicitation for an SMS platform. This forces vendors into absurd workaround \
engineering to "comply" with contradictory mandates.
- **Undifferentiated compliance burden**: All cited regulations presented at the same \
level of importance with no prioritization, categorization, or guidance on which \
ones carry operational weight versus which are boilerplate carryovers.
- **Copy-forward accumulation**: Applicable documents lists that have clearly grown \
over successive contract iterations, with older policies never reviewed for continued \
relevance. The list only grows; nothing is ever removed.

Example of rule pools: A VA solicitation for a text-messaging software system cites \
88 "Applicable Documents" including the Privacy Act (legitimate), six separate policy \
documents about ID badges (irrelevant to software), a 2001 executive order on \
energy-efficient standby power devices (unrelated), and — most absurdly — a VA \
policy explicitly stating "VA personnel should not use SMS to conduct communications." \
The agency is soliciting bids for the very capability one of its own cited policies \
prohibits.

## What is NOT Rule Pools

- **Focused regulatory citations with context**: A solicitation that cites 5-10 \
regulations and explains how each applies to the work ("Section 508 compliance is \
required because the system will be used by veterans with disabilities") is \
curating, not pooling.
- **Genuinely applicable compliance frameworks**: FISMA, FedRAMP, HIPAA, Section 508, \
and similar frameworks often legitimately apply to federal IT work. Citing them is \
appropriate when the work genuinely falls under their scope.
- **Standard FAR/DFARS clauses**: Contracts incorporate standard Federal Acquisition \
Regulation clauses by reference. These are a normal part of federal contracting, \
not rule pools — unless the solicitation adds dozens of agency-specific policies on \
top of them without context.
- **Security and privacy requirements for sensitive work**: A solicitation handling \
PII, health records, or classified information appropriately cites data protection \
regulations. The volume of security requirements for sensitive work may be high but \
justified.

The key distinction: a curated compliance section says "here are the regulations that \
govern this work and why." A rule pool says "here are all the regulations we could \
find — good luck figuring out which ones matter."

## Passive Management and Rule Cascading

Rule pools are a symptom of passive management. Instead of actively reviewing which \
regulations apply and providing interpretive guidance, agency leadership dumps the \
full list onto vendors and contractors. Rules then cascade restrictively downward \
through organizational hierarchies: each level of implementation interprets ambiguous \
guidance conservatively, adding layers of caution that compound until the original \
regulatory intent is buried under defensive compliance.

Good management means getting clarity about ambiguous rules and pushing back when \
compliance requirements don't serve the mission. Rule pools represent the abdication \
of that responsibility.

## Impact on Competition

Rule pools discourage qualified vendors from bidding. When a solicitation presents \
an impenetrably complex wall of regulations, vendors who could deliver excellent work \
face an unknown compliance burden they cannot accurately price or plan for. Many will \
decline to bid. Incumbents — who already know which of the 88 "applicable documents" \
actually get enforced — have a structural advantage. This makes rule pools a close \
cousin of Sin #4 (Insider Rewards): both reduce competition, but through different \
mechanisms.

## Severity Rubric

**1 — Minimal**: The solicitation cites a focused, reasonable set of regulations \
that are clearly relevant to the work. Standard FAR/DFARS clauses are incorporated \
by reference without excessive agency-specific additions. A vendor can readily \
understand the compliance landscape.

**2 — Moderate**: The solicitation includes a noticeable volume of regulatory \
citations — more than seems necessary for the scope — but many are at least \
plausibly relevant. Some appear to be boilerplate carryovers. The compliance burden \
is elevated but not impenetrable, and there are no glaring contradictions or absurd \
inclusions.

**3 — Severe**: The solicitation cites a large, undifferentiated list of regulations \
with little or no context for applicability. Clearly irrelevant or contradictory \
policies are included. The list appears to have accumulated over time without review. \
A vendor new to this agency would face a substantial compliance interpretation burden \
before even beginning to propose a technical solution.

## Evidence Guidelines

- Quote or reference the specific "Applicable Documents," "Referenced Standards," or \
compliance sections that demonstrate bulk, uncurated regulatory citation.
- For severity 2-3, identify specific regulations that appear irrelevant to the scope \
of work and explain WHY they are irrelevant — what is the disconnect between the \
cited policy and the actual work being solicited.
- Note any contradictions between cited regulations and the solicitation's stated \
purpose — these are the strongest evidence of uncurated rule pools.
- If the solicitation provides context or explanations for its regulatory citations, \
note that as a mitigating factor.
- Provide 2-5 evidence items for severity 2-3. For severity 1, evidence may be empty \
or contain 1 minor observation.
- Look especially in "Applicable Documents," "Referenced Standards," "Compliance \
Requirements," and attachment lists — rule pools are almost always concentrated in \
dedicated regulatory sections rather than scattered throughout the SOW.
- Use `reasoning` for your overall judgment: synthesize the evidence, weigh \
mitigating factors, and explain why you assigned the severity you did. Individual \
`evidence` items should each stand alone — a specific quote and why it matters.

## Insufficient Content

Set `sufficient_content` to false if the solicitation text lacks enough detail \
to meaningfully assess this sin — e.g., the posting is a brief notice, \
amendment, sources sought, or pre-solicitation without an attached SOW/PWS. \
When false, set severity to 1, evidence to an empty list, and use reasoning \
to explain what was missing.
"""
