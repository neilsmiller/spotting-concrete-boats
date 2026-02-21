"""Sin #1: Requirement Sprawl.

Requirement sprawl occurs when a solicitation dictates HOW work should be done
rather than WHAT outcome is needed. Instead of defining measurable results, the
solicitation prescribes specific processes, tools, staffing levels, and methods —
removing the vendor's ability to innovate or optimize delivery.

Usage:
    from spotting_concrete_boats.prompts.sin__requirement_sprawl import USER_PROMPT, RESULT_SCHEMA
"""

from typing import Literal

from pydantic import BaseModel, computed_field

from spotting_concrete_boats.prompts.common import SEVERITY_LABELS, SinEvidence


class RequirementSprawlResult(BaseModel):
    """Sin #1: Solicitation dictates HOW work should be done rather than WHAT outcome is needed."""

    sufficient_content: bool
    severity: Literal[1, 2, 3]
    evidence: list[SinEvidence]
    reasoning: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def severity_label(self) -> str:
        """Human-readable severity label."""
        return SEVERITY_LABELS[self.severity]


RESULT_SCHEMA = RequirementSprawlResult

USER_PROMPT = """\
Analyze the solicitation for **Requirement Sprawl** (Sin #1).

## Definition

Requirement sprawl occurs when a solicitation dictates HOW work should be done rather \
than WHAT outcome is needed. Instead of defining measurable results or desired end \
states, the solicitation prescribes specific processes, tools, staffing structures, \
and step-by-step methods — removing the vendor's ability to innovate, automate, or \
optimize delivery.

The core test: **Does this solicitation prejudge the solution?** Requirements that \
lock vendors into a single implementation approach are sprawl. Requirements that \
define outcomes, constraints, or standards leave room for vendors to propose their \
best approach.

## What Constitutes Requirement Sprawl

- Long bullet lists specifying exactly how tasks "shall" be performed step-by-step
- Dictating specific tools, platforms, or technologies when the mission need could \
be met by alternatives
- Prescribing exact staffing structures, roles, and headcounts instead of capability \
requirements
- Detailed workflow procedures that preclude automation or process improvement
- Requirements copied from an incumbent's current operations, effectively mandating \
"do it the same way"

Example of sprawl: A solicitation lists 11 bullets specifying that Application \
Liaisons "shall provide ongoing support" including "generate routine system reports," \
"notify the AM to monitor high priority Incidents," "review, research and ensure \
complex customer Incidents that require escalation meet the stated criteria," etc. \
Each bullet prescribes a specific action rather than defining a service level or \
outcome. A vendor cannot automate, reorganize, or improve — they can only staff \
it exactly as described.

## What is NOT Requirement Sprawl

Not all specificity is sprawl. These are legitimate requirements:

- **Legal mandates and regulatory compliance**: "Comply with Section 508 accessibility \
standards" or "Meet HIPAA data handling requirements." Legal obligations are constraints, \
not prescriptive process choices.
- **Safety and security baselines**: "Encrypt data at rest using FIPS 140-2 validated \
modules." Security standards protect government interests.
- **Measurable outcomes and SLAs**: "Achieve 99.9% system uptime" or "Resolve Tier 1 \
tickets within 4 hours." These define WHAT, not HOW.
- **Reasonable deliverables**: "Submit monthly progress reports in PDF format." A \
focused delivery specification is not sprawl.
- **Technical interoperability constraints**: Requirements to integrate with specific \
existing government systems the vendor must work with.

The key distinction: legitimate requirements constrain the problem space (what must be \
achieved, what standards must be met). Sprawl constrains the solution space (how the \
vendor must do the work).

## Root Cause Patterns

Watch for these organizational signals — they often generate sprawl:
- Copy-paste from the incumbent's current contract (the "how" of the last vendor \
becomes the requirement for the next)
- Consensus-driven drafting where every stakeholder added requirements without an \
owner pruning them
- Bundling unrelated work areas into a single contract, each with its own detailed \
process requirements
- Substituting detailed process mandates for outcome definition when the agency \
can't articulate what success looks like

## Severity Rubric

**1 — Minimal**: Requirements are mostly outcome-focused. A few prescriptive elements \
may exist but they don't dominate or significantly constrain vendor approaches. The \
solicitation is competently scoped.

**2 — Moderate**: Clear sections with prescriptive requirements that dictate processes \
or methods, alongside other sections that remain outcome-oriented. Sprawl is present \
but not pervasive. A vendor would feel constrained in some areas but could still \
propose meaningful alternatives elsewhere.

**3 — Severe**: Prescriptive requirements dominate. Multiple sections dictate \
step-by-step processes, specific staffing structures, and exact methods. The \
solicitation reads more like an operating manual than a statement of need. Vendors \
have little room to innovate — they can only comply with the prescribed approach.

## Evidence Guidelines

- Quote the specific language from the solicitation that demonstrates sprawl.
- For each quote, explain WHY it is prescriptive sprawl rather than a legitimate \
constraint (legal, safety, outcome-based, etc.).
- Provide 2-5 evidence items for severity 2-3. For severity 1, evidence may be \
empty or contain 1 minor example.
- Focus on the most impactful examples — passages where a vendor's approach is most \
constrained — rather than cataloging every prescriptive bullet.
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
