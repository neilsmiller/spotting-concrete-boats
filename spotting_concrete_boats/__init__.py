"""Spotting Concrete Boats — utilities for SAM.gov solicitation analysis."""

from spotting_concrete_boats.analyzer import (
    SolicitationAnalyzer,
    evidence_to_dataframe,
    results_to_dataframe,
)
from spotting_concrete_boats.documents import (
    build_attachment_blocks,
    build_document_blocks,
    build_document_content_block,
    can_process,
    encode_file_as_base64,
    extract_text,
)
from spotting_concrete_boats.sam import SAMClient

__all__ = [
    "SAMClient",
    "SolicitationAnalyzer",
    "build_attachment_blocks",
    "build_document_blocks",
    "build_document_content_block",
    "can_process",
    "encode_file_as_base64",
    "extract_text",
    "evidence_to_dataframe",
    "results_to_dataframe",
]
