"""Document processing utilities for preparing files for Claude API."""

import base64
import logging
from pathlib import Path
from typing import Any

import pandas as pd
import pdfplumber
from docx import Document as DocxDocument

logger = logging.getLogger(__name__)

# Maps file extensions to MIME types for the Claude API
IMAGE_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}

# Extensions that support text extraction and are sent as text blocks (not base64).
# MIME types are kept for reference but aren't used in the current text-extraction path.
DOCUMENT_MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}

# File types we know we can't send directly to Claude
UNSUPPORTED_EXTENSIONS = {".xls", ".xlsx", ".csv", ".doc"}


def get_supported_extensions() -> set[str]:
    """Return the set of file extensions supported for document processing."""
    return set(IMAGE_MEDIA_TYPES.keys()) | set(DOCUMENT_MEDIA_TYPES.keys())


def can_process(file_path: str | Path) -> bool:
    """Check whether a file can be processed based on its extension.

    Returns True for supported extensions, False for unsupported or unknown types.
    """
    ext = Path(file_path).suffix.lower()
    return ext in IMAGE_MEDIA_TYPES or ext in DOCUMENT_MEDIA_TYPES


def encode_file_as_base64(file_path: str | Path) -> str | None:
    """Read a file and return its contents as a base64-encoded string.

    Args:
        file_path: Path to the file to encode.

    Returns:
        Base64-encoded string, or None if the file can't be read.
    """
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except OSError as e:
        logger.warning("Error reading file %s: %s", file_path, e)
        return None


def extract_text_from_pdf(file_path: str | Path, max_pages: int = 200) -> str:
    """Extract text from a PDF file using pdfplumber.

    Extracts text page-by-page with page delimiters. Tables are extracted
    as pipe-delimited rows to preserve structure. Table regions are excluded
    from the body text extraction to avoid duplicating content.

    Args:
        file_path: Path to the PDF file.
        max_pages: Maximum number of pages to extract. Defaults to 200.

    Returns:
        Extracted text with page delimiters.
    """
    pages = []
    with pdfplumber.open(file_path) as pdf:
        if len(pdf.pages) > max_pages:
            logger.warning(
                "PDF %s has %d pages, truncating to %d",
                file_path,
                len(pdf.pages),
                max_pages,
            )

        for i, page in enumerate(pdf.pages[:max_pages], start=1):
            page_parts = [f"--- Page {i} ---"]

            # Extract tables and their bounding boxes
            table_bboxes = [table.bbox for table in page.find_tables()]
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        cells = [cell if cell else "" for cell in row]
                        page_parts.append(" | ".join(cells))
                    page_parts.append("")  # blank line between tables

            # Filter out table regions before extracting body text to avoid duplication
            if table_bboxes:
                filtered_page = page
                for bbox in table_bboxes:
                    filtered_page = filtered_page.outside_bbox(bbox)
                text = filtered_page.extract_text()
            else:
                text = page.extract_text()

            if text:
                page_parts.append(text)

            pages.append("\n".join(page_parts))

    return "\n\n".join(pages)


def extract_text_from_docx(file_path: str | Path) -> str:
    """Extract text from a .docx file using python-docx.

    Args:
        file_path: Path to the .docx file.

    Returns:
        Extracted paragraph text joined by newlines.
    """
    doc = DocxDocument(str(file_path))
    return "\n".join(para.text for para in doc.paragraphs)


def extract_text_from_txt(file_path: str | Path) -> str:
    """Read text from a plain text file.

    Uses errors="replace" so undecodable bytes become U+FFFD rather than raising.

    Args:
        file_path: Path to the text file.

    Returns:
        File contents as a string (may contain replacement characters for
        bytes that couldn't be decoded as UTF-8).
    """
    with open(file_path, errors="replace") as f:
        return f.read()


EXTRACTORS = {
    ".pdf": extract_text_from_pdf,
    ".docx": extract_text_from_docx,
    ".txt": extract_text_from_txt,
}


def extract_text(file_path: str | Path) -> str:
    """Extract text from a supported document file.

    Routes to the appropriate extractor based on file extension.
    Supports .pdf, .docx, and .txt files.

    Args:
        file_path: Path to the document.

    Returns:
        Extracted text content.

    Raises:
        ValueError: If the file extension is not supported.
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    extractor = EXTRACTORS.get(ext)
    if not extractor:
        raise ValueError(f"Unsupported file type for text extraction: {ext}")
    return extractor(path)


def build_document_content_block(file_path: str | Path) -> dict[str, Any] | None:
    """Build a Claude API content block for a file (image or document).

    Images are base64-encoded and sent as image blocks. Documents (.pdf, .docx,
    .txt) have their text extracted and are sent as text blocks, which is far
    more token-efficient for text-heavy content.

    Args:
        file_path: Path to the file.

    Returns:
        A dict suitable for use in a Claude API message content list,
        or None if the file type is unsupported or can't be read.
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext in UNSUPPORTED_EXTENSIONS:
        logger.info("Skipping unsupported file type: %s", path.name)
        return None

    # Images: base64 encode as before
    if ext in IMAGE_MEDIA_TYPES:
        file_data = encode_file_as_base64(path)
        if not file_data:
            return None
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": IMAGE_MEDIA_TYPES[ext],
                "data": file_data,
            },
        }

    # Documents: extract text and send as text block
    if ext in DOCUMENT_MEDIA_TYPES:
        try:
            text = extract_text(path)
        except Exception as e:
            logger.warning("Error extracting text from %s: %s", path.name, e)
            return None
        if not text.strip():
            logger.info("No text extracted from %s", path.name)
            return None
        return {
            "type": "text",
            "text": f"[Document: {path.name}]\n\n{text}",
        }

    logger.info("Skipping unknown file type: %s", path.name)
    return None


def build_attachment_blocks(
    file_paths: list[str | Path],
) -> list[dict[str, Any]]:
    """Build Claude API content blocks for multiple attachments.

    Convenience wrapper around build_document_content_block for processing
    a list of files. Skips any files that can't be processed.

    Args:
        file_paths: List of file paths to process.

    Returns:
        List of content block dicts ready for the Claude API.
    """
    blocks = []
    for path in file_paths:
        block = build_document_content_block(path)
        if block:
            blocks.append(block)
    return blocks


def _count_pdf_pages(file_paths: list[str | Path]) -> int:
    """Count total pages across all PDF files in a list of paths."""
    total = 0
    for p in file_paths:
        if Path(p).suffix.lower() == ".pdf":
            try:
                with pdfplumber.open(p) as pdf:
                    total += len(pdf.pages)
            except Exception:
                pass
    return total


def compute_attachment_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Precompute attachment statistics columns on the DataFrame.

    Adds `total_pages` and `file_types` columns. Should be called once after
    resolving attachment paths to avoid repeated PDF opens during context building.

    Args:
        df: DataFrame with an `attachment_paths` column (list of file path strings).

    Returns:
        The same DataFrame with new columns added in-place.
    """
    total_pages = []
    file_types = []
    for paths in df["attachment_paths"]:
        if not isinstance(paths, list) or not paths:
            total_pages.append(0)
            file_types.append("")
            continue
        total_pages.append(_count_pdf_pages(paths))
        ext_counts: dict[str, int] = {}
        for p in paths:
            ext = Path(p).suffix.lower()
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
        file_types.append(", ".join(f"{c} {e.lstrip('.')}" for e, c in sorted(ext_counts.items())))
    df["total_pages"] = total_pages
    df["file_types"] = file_types
    return df


def build_solicitation_context(row: pd.Series) -> str:
    """Build a structured context string from an opportunity DataFrame row.

    Extracts key metadata fields and formats them as a readable text block
    that helps the LLM understand what it's analyzing before reading attachments.

    Args:
        row: A single row from the opportunities DataFrame.

    Returns:
        Formatted context string with solicitation metadata and description.
    """

    def _get(field: str) -> str | None:
        """Return a non-empty string value or None."""
        val = row.get(field)
        if pd.isna(val) if not isinstance(val, str) else not val.strip():
            return None
        return str(val).strip()

    lines = []

    if title := _get("title"):
        lines.append(f"Title: {title}")

    if sol_num := _get("solicitationNumber"):
        lines.append(f"Solicitation Number: {sol_num}")

    if opp_type := _get("type"):
        lines.append(f"Notice Type: {opp_type}")

    if agency := _get("office"):
        lines.append(f"Agency: {agency}")

    if naics := _get("naicsCode"):
        lines.append(f"NAICS Code: {naics}")

    if classification := _get("classificationCode"):
        lines.append(f"Classification Code: {classification}")

    if set_aside := _get("typeOfSetAsideDescription"):
        lines.append(f"Set-Aside: {set_aside}")

    # Dates and response window
    def _fmt_date(val: Any) -> str | None:
        """Format a date value as YYYY-MM-DD, or None if not a valid date."""
        try:
            dt = pd.to_datetime(val)
            if pd.isna(dt):
                return None
            return dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return None

    if posted_str := _fmt_date(row.get("postedDate")):
        lines.append(f"Posted: {posted_str}")
    if deadline_str := _fmt_date(row.get("responseDeadLine")):
        lines.append(f"Response Deadline: {deadline_str}")

    if pd.notna(row.get("postedDate")) and pd.notna(row.get("responseDeadLine")):
        try:
            posted_dt = pd.to_datetime(row["postedDate"])
            deadline_dt = pd.to_datetime(row["responseDeadLine"], utc=True)
            if posted_dt.tzinfo is None:
                posted_dt = posted_dt.tz_localize("UTC")
            days = (deadline_dt - posted_dt).days
            if days >= 0:
                lines.append(f"Response Window: {days} days")
        except (ValueError, TypeError):
            pass

    # Place of performance
    pop = row.get("placeOfPerformance")
    if isinstance(pop, dict):
        parts = []
        city = pop.get("city", {})
        if isinstance(city, dict) and city.get("name"):
            parts.append(city["name"])
        state = pop.get("state", {})
        if isinstance(state, dict) and state.get("name"):
            parts.append(state["name"])
        elif isinstance(state, dict) and state.get("code"):
            parts.append(state["code"])
        country = pop.get("country", {})
        if isinstance(country, dict) and country.get("name") and country["name"] != "UNITED STATES":
            parts.append(country["name"])
        if parts:
            lines.append(f"Place of Performance: {', '.join(parts)}")

    # Total attachment count from the API (resourceLinks), not limited by local downloads
    resource_links = row.get("resourceLinks")
    if isinstance(resource_links, list):
        n_attachments = len(resource_links)
    else:
        n_attachments = 0
    lines.append(f"Attachments: {n_attachments}")

    # Local file stats (may be fewer than total due to download cap)
    attachment_paths = row.get("attachment_paths")
    if isinstance(attachment_paths, list) and attachment_paths:
        # Page count — prefer precomputed column, fall back to counting
        total_pages = row.get("total_pages")
        if pd.isna(total_pages) or total_pages is None:
            total_pages = _count_pdf_pages(attachment_paths)
        if total_pages and int(total_pages) > 0:
            lines.append(f"Total Pages (PDFs): {int(total_pages)}")

    # Description (the original SAM.gov text)
    desc = _get("description")
    if desc and len(desc) > 20:
        lines.append(f"\nDescription:\n{desc}")

    return "\n".join(lines)


def build_document_blocks(
    file_paths: list[str | Path],
    description: str | None = None,
) -> list[dict]:
    """Build Claude API content blocks from files with an optional text description.

    Convenience entry point for notebook users. Prepends an optional text block
    describing the solicitation, then delegates to build_attachment_blocks() for
    file processing.

    Args:
        file_paths: List of file paths to process.
        description: Optional text description to prepend (e.g. solicitation title,
            context notes). Added as a text content block before file blocks.

    Returns:
        List of content block dicts ready for the Claude API.
    """
    blocks: list[dict] = []
    if description:
        blocks.append({"type": "text", "text": description})
    blocks.extend(build_attachment_blocks(file_paths))
    return blocks
