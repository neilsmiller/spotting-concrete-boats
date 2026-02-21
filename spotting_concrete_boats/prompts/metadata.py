"""Solicitation metadata extraction.

Extracts structured factual metadata from a solicitation: contract type,
performance period, and evaluation criteria. These are objective fields that
can be extracted in a single prompt since they don't require subjective analysis.

Usage:
    from spotting_concrete_boats.prompts.metadata import USER_PROMPT, RESULT_SCHEMA
"""

from pydantic import BaseModel


class SolicitationMetadata(BaseModel):
    """Structured metadata extracted from the solicitation."""

    contract_type: str | None
    performance_period: str | None
    evaluation_criteria: list[str]


RESULT_SCHEMA = SolicitationMetadata

USER_PROMPT = """\
Extract the following metadata from the solicitation:

1. **Contract type**: The contract type (e.g., FFP, T&M, CPFF, IDIQ, BPA, etc.). \
If the solicitation does not clearly state a contract type, return null.

2. **Performance period**: The period of performance as stated in the solicitation \
(e.g., "1 base year + 4 option years", "12 months"). If not clearly stated, return null.

3. **Evaluation criteria**: The evaluation factors or criteria listed in the \
solicitation, in the order of importance as presented. Quote the factor names \
directly from the source text. If no evaluation criteria are stated, return an \
empty list.
"""
