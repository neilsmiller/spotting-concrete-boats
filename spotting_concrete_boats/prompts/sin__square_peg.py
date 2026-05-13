"""Sin #6: Square Peg.

A square peg occurs when a solicitation adopts a contract pricing structure
that doesn't make sense for the requirement. Using firm fixed pricing (FFP)
when  the scope of a project is uncertain, or time and materials (T&M) pricing
when the cost and schedule can be reasonably predicted, can make it hard for
the government to effectively manage the contract's performance. This may lead
to projects taking much longer, requiring more contract adjustments, or
costing more than necessary.

Usage:
    from spotting_concrete_boats.prompts.sin__square_peg import USER_PROMPT, RESULT_SCHEMA
"""

from typing import Literal

from pydantic import BaseModel, computed_field

from spotting_concrete_boats.prompts.common import SEVERITY_LABELS, SinEvidence


class SquarePegResult(BaseModel):
    """Sin #6: Using the wrong contract pricing scheme for the requirements."""

    sufficient_content: bool
    severity: Literal[1, 2, 3]
    evidence: list[SinEvidence]
    reasoning: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def severity_label(self) -> str:
        """Human-readable severity label."""
        return SEVERITY_LABELS[self.severity]


RESULT_SCHEMA = SquarePegResult

USER_PROMPT = r"""\
Analyze the solicitation for **Square Peg** (Sin #6).

## Definition

A square peg occurs when a solicitation adopts a contract pricing structure \
that doesn't make sense for the requirement. Using fixed price contracts like \
firm fixed pricing (FFP) make sense when the scope of a project is uncertain, or  \
time and materials (T&M) pricing when the cost and schedule can be reasonably \
predicted, can make it hard for the government to effectively manage the contract's \
performance. This may lead to projects taking much longer, requiring more contract \
adjustments, or costing more than necessary. \

The core test: **Does this solicitation use contract pricing that is misaligned \
with the requirements or with the context provided in the solicitation?** \
If the government has no way to control labor costs or timeline even when price and \
schedule should be predictable (because the contract is T&M instead of fixed), this can
be a square peg. Alternatively, when the government uses a fixed-price contract or imposes \
a rigid schedule despite the scope of work being uncertain, this is a square peg: the work \
cannot be estimated accurately, so expensive contract modifications may be needed to \
stop the project from failing.

## Contract Type Basics

- In a **Fixed Price** contract, the agreed payment amount will not subsequently be \
adjusted to reflect the resources used, costs incurred, or time expended by the vendor. \
The Federal Acquisition Regulation (FAR) defines several types of fixed-price contracts, \
including firm-fixed-price (FFP); fixed-price contracts with an economic price adjustment; \
fixed-price incentive contracts; fixed-ceiling-price contracts with retroactive price \
redetermination; Firm-fixed-price, level-of-effort term contracts.
- The risk in a fixed price contract is intended to fall mostly on the vendor. The vendor \
is incentivized to perform the requirements as efficiently as possible. The FAR says: \
"A firm-fixed-price contract, which best utilizes the basic profit motive of business \
enterprise, shall be used when the risk involved is minimal or can be predicted with \
an acceptable degree of certainty." \
- A fixed-price contract makes sense when requirements are well-defined and unlikely to \
change; risk can be reasonable estimated; multiple vendors can bid, so competition will \
keep prices honest; performance criteria are measurable and objective (e.g. deliver product) \
X by Y date); or you're buying commercial products or routine services.
- A **cost-reimbursement** contract provides for payment of allowable incurred costs. Each \
contract of this type will describe the extent to which costs may be reimbursed. Different \
types of cost-reimbursement contracts include cost contract; cost-sharing contracts; \
cost-plus-incentive-fee contracts; cost-plus-award-fee contracts; cost-plus-fixed-fee; \
- According to the FAR: cost-reimbursement contracts should only be used when: \
"(1) Circumstances do not allow the agency to define its requirements sufficiently \
 to allow for a fixed-price type contract; or (2) Uncertainties involved in contract \
 performance do not permit costs to be estimated with sufficient accuracy to use any \
type of fixed-price contract." \
- **Time-and-materials** contracts and **labor-hour contracts** are not fixed-price contacts. \
- A time-and-materials (T&M) contract provides for acquiring supplies or services on the basis of \
(1) Direct labor hours at specified fixed hourly rates that include wages, overhead, general \
and administrative expenses, and profit; and (2) Actual cost for materials. \
- A T&M contract may only be used when it is not possible to accurately estimate the extent or \
duration of the work or anticipate costs accurately. Government surveillance of the vendor is \
required to make sure they are working efficiently and controlling costs. \
- A labor-hour contract is the same as T&M, except materials are not supplied \
by the contractor. \
- A T&M or labor hours contract should specify fixed hourly rates for each \
labor category (LCAT). \
- T&M makes sense when the work is unpredictable; requirements will evolve over the \
course of the project; \ the government is looking to purchase expertise instead of \
a particular output; and speed is more important that cost certainty. \
- T&M contracts are typically used for system maintenance and repair, research with \
undefined paths, IT services where the requirements depend on user need, and \
emergency response work. \
- Cost-reimbursement contracts make sense for large, complex, technically \
uncertain programs. T&M is better for discrete, labor-intensive tasks where \
the work type is known but the quantity cannot be predicted.

## What Constitutes Square Pegs

- **Mismatch between pricing type and context**: To establish if a solicitation is a square \
peg, you need to (1) see what the contract type is, (2) have enough context or information \
about the requirements to evaluate what type of contract is best, and (3) see that these \
two don't match.

Example of Square Peg (FFP contract was used when T&M would have been better): the \
Department of Defense has a solicitation for administrative services, including updating \
acquisition and budget trackers, monitoring email inboxes, and analyzing cyber-security trends. \
This contract was FFP. It should have been T&M, because there is no well-defined deliverable \
and the amount of work may vary. With FFP, the government cannot effectively control costs. \

Example of Square Peg (T&M where FFP would have been better): The Department of \
Homeland Security awarded a sole-source follow-on contract to a vendor that has \
worked on a particular project for 10+ years. DHS has a goal of decommissioning one \
legacy system and bringing the replacement online by September 2026. The justification \
says that the contractor's experience is essential to completing the project "on schedule \
and within budget." This is a clear use case for fixed-price: there is a clear goal and \
timeline, and it should be possible to estimate cost because the incumbent vendor is already \
working on this project. Since the contract is T&M however, the vendor has no incentive \
to meet the deadline. A T&M contract does not give the government leverage to keep \
deadlines.

Example of Square Peg (T&M contract was used when CR would have been better): NASA \
is writing a solicitation for long-term R&D on a complex spacecraft component.  The \
SOW describes multi-year research phases with technical milestones, meaning NASA cares \
about what is produced more than just hours worked. This contract uses T&M, which \
incentivizes the vendor to overbill without sufficient incentives for the output \
it delivers.

Example of Square Peg (CR contract when FFP would have been better): a data-heavy \
agency issues a solicitation to migrate a legacy database into the cloud. The SOW \
specifies a defined target architecture, a list of data tables to migrate, and a \
concrete completion deadline. This contract uses Cost-Plus-Fixed-Fee. A FFP contract \
would be better because timeline and schedule is predictable. Under CR, the vendor \
has no incentive to work efficiently. This may be severity 2 instead of 3, as the agency \
can argue that there unexpected challenges may arise which make FFP risky.

Example of Square Peg

## What is NOT Square Peg

- **Appropriate Firm-Fixed Price**: A fixed-price contract makes sense if requirements \
can be predicted in advance (like a construction contract) or a good is offered commercially \
(like standard software licenses).
- **Appropriate Cost-Reimbursement or T&M Project**: If you need expert advice (like \
consulting from an IT system architect) without a specific deliverable, or you need someone \
to maintain or repair a complex system, a T&M contract is appropriate.

## How Projects Can Fail Depends on Contract Type

- Failed projects can occur with any contract type. But the government needs to \
think through how each contract type can blow up. T&M will turn into a boondoggle \
when contracted employees aren’t using their time well — you pay a lot for people \
doing the wrong jobs. FFP contracts sink when you ask for the wrong deliverables —  \
like buying meetings and emails instead of an answer to your problem — or you \
misestimate how much it will cost to get there.

## Severity Rubric

**1 — Minimal**: The solicitation uses a contract type that is appropriate \
for the requirements. For example, it uses a fixed-price contract for \
straightforward requirements; or T&M for a labor-intensive project with \
unpredictable schedules or quantity of labor required; or cost-reimbursement \
for long-term, complex tasks like basic research grants.

**2 — Moderate**: Based on the information provided, there is good reason to \
think that a different contract type might have been preferable. The choice of \
contract type is defensible, or the solicitation has a justification \
of why the particular contract type is used, so you don't consider this a severe \
example of "square peg". There may also be modifications that mitigate the issues, \
like T&M contracts with incentives for meeting deadlines.

**3 — Severe**: Most contracting experts looking at this solicitation would \
agree that the government should have chosen a different contract type. \
The chosen contract type is a poor fit given the context provided in \
the solicitation, meaning there is a high risk that the project will \
go wrong (e.g. a fixed-price contract will need expensive modifications \
or a T&M project will allow inflated billing amounts.)

## Suggested Decision Sequence

- First identify the contract type stated in the solicitation. You can infer \
based on context, if it is not stated explicitly but implied.
- Next characterise the requirements: are they well-defined? Is the scope \
stable? Is the quantity of labor predictable?
- Identify the contract type that best fits those requirements.
- If steps 1 and 3 diverge, assess severity based on how badly mismatched \
they are and whether the solicitation offers any justification or mitigation.

## Evidence Guidelines

- Quote  the specific contract type from the contract.
- For severity 2 or 3, identify specific requirements or context that \
are in conflict with the contract type. Explain why each requirement \
or piece of context conflicts with the contract type.
- If a solicitation uses different contract types for different CLINs, \
assess each component separately and flag mismatches at the CLIN level.
- For severity 2, explain why the chosen contract type might be justifiable, \
or cite the justification given in the solicitation. If the chosen contract \
type is not reasonably justifiable, the severity should be 3 — Severe.
- Provide 2-5 evidence items for severity 2-3. For severity 1, evidence may be empty \
or contain 1 minor observation.
- Use `reasoning` for your overall judgment: synthesize the evidence, weigh \
mitigating factors, and explain why you assigned the severity you did. Individual \
`evidence` items should each stand alone — a specific quote and why it matters.

## Insufficient Content

Set `sufficient_content` to false if the solicitation text lacks enough detail \
to meaningfully assess this sin — e.g., the posting is a brief notice, \
amendment, sources sought, or pre-solicitation without an attached SOW/PWS; \
or there is zero information about the contract type or context for requirements. \
If you can infer contract type from context (e.g. LCATs with hourly rates imply \
a T&M contract), you can use that and you do not need to set `sufficient_content` \
to false. \
When false, set severity to 1, evidence to an empty list, and use reasoning \
to explain what was missing.
"""
