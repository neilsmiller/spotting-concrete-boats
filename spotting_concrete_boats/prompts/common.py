"""Shared base models for prompt schemas.

Sin severity scale (1-3):
    1 = Minimal
    2 = Moderate
    3 = Severe

Virtue strength scale (1-3):
    1 = Weak
    2 = Moderate
    3 = Strong
"""

from pydantic import BaseModel

SEVERITY_LABELS: dict[int, str] = {1: "Minimal", 2: "Moderate", 3: "Severe"}
STRENGTH_LABELS: dict[int, str] = {1: "Weak", 2: "Moderate", 3: "Strong"}


class SinEvidence(BaseModel):
    """A single piece of evidence from the solicitation supporting a finding."""

    quote: str
    explanation: str


VirtueEvidence = SinEvidence
