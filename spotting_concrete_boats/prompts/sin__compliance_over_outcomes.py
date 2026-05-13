"""Sin #2: Compliance Over Outcomes.

Compliance over outcomes occurs when a solicitation's quality assurance and
evaluation processes measure adherence to prescribed processes rather than
actual performance or results. The government monitors whether the vendor
followed the rules, not whether the work product achieved its purpose.

Usage:
    from spotting_concrete_boats.prompts.sin__compliance_over_outcomes import (
        USER_PROMPT, RESULT_SCHEMA,
    )
"""

from typing import Literal

from pydantic import BaseModel, computed_field

from spotting_concrete_boats.prompts.common import SEVERITY_LABELS, SinEvidence


class ComplianceOverOutcomesResult(BaseModel):
    """Sin #2: QA processes that measure process compliance, not actual performance."""

    sufficient_content: bool
    severity: Literal[1, 2, 3]
    evidence: list[SinEvidence]
    reasoning: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def severity_label(self) -> str:
        """Human-readable severity label."""
        return SEVERITY_LABELS[self.severity]


RESULT_SCHEMA = ComplianceOverOutcomesResult

USER_PROMPT = """\
Analyze the solicitation for **Compliance Over Outcomes** (Sin #2).

## Definition

Compliance over outcomes occurs when a solicitation's quality assurance and \
accountability mechanisms measure whether the vendor followed prescribed processes \
rather than whether the work achieved its purpose. The government monitors adherence \
to the plan — not whether the plan produced results.

The core test: **Does this solicitation define success as "completed documentation"\
or "did a good job"?** When reporting requirements focus on activities performed, \
schedule adherence, and process documentation — with no performance targets, user \
satisfaction metrics, or outcome measures — the QA process assures compliance, not \
quality.

## What Constitutes Compliance Over Outcomes

- **Reporting burden without outcome metrics**: Weekly, monthly, AND quarterly \
reports required — each with prescribed sections covering activities, personnel, \
schedule status, and plans — but no performance targets or success criteria.
- **Overlapping reporting cadences**: Multiple report types covering the same \
ground at different intervals, generating paperwork without new insight.
- **Status reports focused on plan adherence**: Reports required to track progress \
against a pre-established schedule or plan (e.g., "deviations from the CPMP") \
rather than measuring whether deliverables meet user needs.
- **Prescribed report formats and sections**: Mandating specific report structures \
(e.g., "The WSR shall contain: development in process, FIAR activities, cyber \
activities, releases, maintenance planned, personnel leave") rather than letting \
the vendor communicate what matters.
- **Excessive meeting frequency**: Required meetings "no less than weekly" or \
multiple times daily, especially when combined with written reports covering the \
same content.
- **QA surveillance that checks process, not product**: Quality assurance plans \
that verify the vendor followed procedures rather than evaluating deliverable \
quality or user outcomes.

Example of compliance over outcomes: A solicitation requires weekly status reports \
covering development, audit readiness, cyber activities, releases, maintenance, and \
personnel leave — PLUS monthly progress reports in Microsoft Word and Project \
formats tracking deviations from the project plan — PLUS weekly-to-twice-daily \
teleconferences. The entire accountability structure monitors whether the vendor \
is following the plan, with no mention of system performance, user satisfaction, \
or mission outcomes.

## What is NOT Compliance Over Outcomes

- **Quarterly review meetings**: A periodic meeting to "communicate program \
successes, identify problems, and develop follow-up actions" is reasonable \
management oversight — as long as it's not one of many overlapping reporting \
requirements.
- **Performance metrics and SLAs**: "System shall maintain 99.9% uptime" or \
"Resolve tickets within 4 hours" are outcome-focused accountability. This is \
the opposite of this sin.
- **Deliverable acceptance testing**: Reviewing whether a deliverable meets \
specifications is outcome evaluation, not compliance theater.
- **Regulatory audits**: FISMA compliance checks, financial audits, or security \
assessments serve legitimate oversight purposes.
- **A single reasonable status report**: One monthly progress report is normal \
contract management. The sin emerges when reporting becomes the primary \
accountability mechanism.

The key distinction: accountability structures that ask "is the work good?" are \
outcome-focused. Structures that ask "did you follow the process?" are \
compliance-focused. The sin is when the latter crowds out the former entirely.

## Relationship to Waterfall Thinking

This sin is rooted in waterfall-era project management, where all tasks are specified \
in advance and each phase proceeds sequentially. In that model, tracking schedule \
adherence and plan deviations made sense. Modern work — especially IT services — \
requires responding to change, and "deviating from the plan" is often the right move. \
When a solicitation mandates waterfall-style reporting for work that demands \
flexibility, the QA process actively undermines good performance.

## Severity Rubric

**1 — Minimal**: Reporting requirements are light and reasonable. The solicitation \
may include standard progress reporting but also defines outcome metrics, performance \
standards, or SLAs. Accountability is balanced between process and results.

**2 — Moderate**: Noticeable reporting burden — multiple report types or prescribed \
formats — but the solicitation also includes some outcome-oriented accountability \
(performance metrics, acceptance criteria, user satisfaction measures). Compliance \
mechanisms exist but don't completely displace outcome focus.

**3 — Severe**: Reporting and process compliance dominate the accountability \
structure. Multiple overlapping cadences, detailed format requirements, plan-adherence \
tracking — with no meaningful performance targets or outcome metrics. The QA process \
is the primary way the government evaluates the vendor, and it measures process, \
not results.

## Evidence Guidelines

- Quote the specific reporting requirements, meeting mandates, or QA surveillance \
language that demonstrates compliance focus.
- For each quote, explain WHY it measures compliance rather than outcomes — \
specifically, what outcome metric or performance target is absent.
- Provide 2-5 evidence items for severity 2-3. For severity 1, evidence may be \
empty or contain 1 minor example.
- Look especially in QA Surveillance Plans, reporting sections, and deliverables \
lists — this sin is often concentrated in those areas rather than spread throughout.
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
