"""Sin #4: Insider Rewards Program.

Insider rewards occur when a solicitation's experience requirements, evaluation
criteria, or knowledge expectations effectively exclude any vendor that has not
previously held the contract. The solicitation rewards incumbency rather than
capability, reducing competition and locking in existing vendors.

Usage:
    from spotting_concrete_boats.prompts.sin__insider_rewards import USER_PROMPT, RESULT_SCHEMA
"""

from typing import Literal

from pydantic import BaseModel, computed_field

from spotting_concrete_boats.prompts.common import SEVERITY_LABELS, SinEvidence


class InsiderRewardsResult(BaseModel):
    """Sin #4: Experience requirements that effectively exclude non-incumbent vendors."""

    sufficient_content: bool
    severity: Literal[1, 2, 3]
    evidence: list[SinEvidence]
    reasoning: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def severity_label(self) -> str:
        """Human-readable severity label."""
        return SEVERITY_LABELS[self.severity]


RESULT_SCHEMA = InsiderRewardsResult

USER_PROMPT = """\
Analyze the solicitation for **Insider Rewards Program** (Sin #4).

## Definition

Insider rewards occur when a solicitation's experience requirements, evaluation \
criteria, or knowledge expectations effectively exclude any vendor that has not \
previously held the contract — or a very similar one. Instead of evaluating \
capability, the solicitation rewards incumbency, reducing competition and locking \
in existing vendors.

The core test: **Could a qualified vendor who has never worked this specific \
contract realistically compete?** When experience requirements demand prior federal \
contracts of a specific dollar size, in a narrow domain, within a short lookback \
window — the answer is usually no. The solicitation isn't selecting for capability; \
it's selecting for incumbency.

## What Constitutes Insider Rewards

- **Narrow prior-contract requirements**: Requiring multiple completed contracts of \
a specific dollar threshold (e.g., "$500K+" or "$25M+") in a narrow domain within \
a short time window (e.g., 2—3 years). The combination of size, specificity, and \
recency drastically shrinks the eligible pool.
- **Federal-specific experience mandates**: Requiring years of experience managing \
specifically "Federal Government programs/contracts" when the underlying skills \
are not unique to federal work. A vendor with 15 years of excellent commercial IT \
management experience would be disqualified.
- **Evaluation bonus points for incumbency proxies**: Awarding extra evaluation \
points for prior contracts of a specific type or size. This doesn't just set a \
floor — it actively advantages the incumbent in scoring.
- **Institutional knowledge as a requirement**: Requiring familiarity with the \
agency's specific systems, processes, or organizational structure that could only \
come from having held the contract before.
- **Transition plan scored against insider knowledge**: Evaluation criteria that \
score the transition plan in ways that reward detailed knowledge of the current \
operating environment — knowledge only the incumbent possesses.
- **Stacked requirements**: Combining multiple insider-favoring criteria (specific \
dollar thresholds + federal experience + domain narrowness + short lookback windows) \
that individually might be defensible but collectively exclude all but a handful of \
vendors.

Example of insider rewards: A $3 billion cell phone contract awards bonus evaluation \
points for demonstrating three previous $25 million cell phone contracts won within \
three years. The number of vendors who have won three $25M+ cell phone contracts in \
a three-year window is vanishingly small — likely only the incumbent and one or two \
others. The requirement doesn't test capability to deliver; it tests whether the \
vendor has already been winning these exact contracts.

## What is NOT Insider Rewards

- **Reasonable experience requirements**: "Demonstrate experience delivering IT \
services to organizations of comparable size and complexity" is legitimate — it tests \
capability without requiring specific contract types or dollar thresholds.
- **Security clearance requirements**: Requiring personnel with active clearances \
reflects genuine access constraints, not incumbency bias — even though it does limit \
the vendor pool.
- **Domain expertise without contract specificity**: "Team must include personnel \
with experience in healthcare IT systems" is a capability requirement. It becomes \
insider rewards when each key personnel "must have completed three federal \
healthcare IT contracts exceeding $2M each."
- **Past performance evaluation**: Evaluating the quality of a vendor's prior work \
is standard and appropriate. The sin is when the evaluation requires specific \
quantities of prior contracts at specific dollar levels in specific timeframes.
- **Transition planning as an evaluation factor**: Asking vendors to describe their \
transition approach is reasonable. It becomes insider rewards when the scoring rubric \
effectively requires insider knowledge to score well.

The key distinction: legitimate requirements test whether the vendor CAN do the work. \
Insider rewards test whether the vendor HAS done this specific work before, for the \
federal government, at a specific scale, recently enough.

## Vendor Capture and Its Consequences

This sin often reflects vendor capture — a state where the agency has become \
functionally dependent on the incumbent contractor. The agency's institutional \
knowledge lives in the vendor's staff, not in the agency's own workforce. When \
critical systems are held together by accumulated tribal knowledge, the agency \
cannot articulate requirements in vendor-neutral terms because they genuinely don't \
know how their own systems work without the incumbent.

The consequence is a self-reinforcing cycle: insider requirements → incumbent wins → \
agency becomes more dependent → next solicitation has even narrower requirements. \
Competition atrophies, costs rise, and the government loses bargaining power.

## Severity Rubric

**1 — Minimal**: Experience requirements are reasonable and capability-focused. The \
solicitation may reference prior experience but does not impose narrow dollar \
thresholds, federal-specific mandates, or short lookback windows that would exclude \
qualified newcomers. A competent vendor new to this specific contract could \
realistically compete.

**2 — Moderate**: Some experience requirements favor incumbents — specific dollar \
thresholds, federal experience mandates, or narrow domain requirements — but the \
solicitation also includes evaluation criteria that allow non-incumbents to compete \
on capability, technical approach, or price. The playing field is tilted but not \
closed.

**3 — Severe**: Experience requirements effectively function as an incumbent filter. \
Multiple criteria stack to exclude non-incumbents: specific contract dollar thresholds \
within short timeframes, federal-specific experience mandates, evaluation bonus points \
for prior similar contracts, and/or institutional knowledge requirements. A qualified \
vendor without this specific contract history would be unable to compete meaningfully.

## Evidence Guidelines

- Quote the specific experience requirements, evaluation criteria, or knowledge \
expectations that favor incumbents.
- For each quote, explain WHY it functions as an insider reward — specifically, \
what combination of specificity, dollar threshold, recency, and domain narrowness \
makes it exclusionary.
- Consider the cumulative effect: individual requirements may seem reasonable, \
but their combination may be exclusionary. Note when requirements stack.
- Provide 2-5 evidence items for severity 2-3. For severity 1, evidence may be \
empty or contain 1 minor observation.
- Look especially in evaluation criteria sections, personnel qualifications, and \
past performance requirements — insider rewards are most often embedded there.
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
