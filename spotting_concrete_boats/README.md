# spotting_concrete_boats

Python package for analyzing US federal solicitations against common procurement anti-patterns ("sins") using Claude.

## How It Works

1. **File encoding** — Local solicitation files (PDF, DOCX, images) are base64-encoded into Claude API content blocks by `documents.py`.
2. **Prompt discovery** — At startup, the analyzer scans the `prompts/` directory and loads every module that exports a `USER_PROMPT` and `RESULT_SCHEMA`. No registration step needed.
3. **Concurrent analysis** — `analyzer.py` fires all prompts against the document concurrently via `asyncio`, with prompt caching so the system prompt and document bytes are sent to the API only once.
4. **Structured output** — Each API response is parsed into a Pydantic model (`client.messages.parse()`), so results are typed dicts, not free text.
5. **DataFrames** — Two helper functions flatten the results into pandas DataFrames for summary and evidence-level analysis.

## Quick Start

```python
from spotting_concrete_boats import (
    SolicitationAnalyzer,
    results_to_dataframe,
    evidence_to_dataframe,
)

analyzer = SolicitationAnalyzer()

# See what prompts are available
analyzer.describe_prompts()

# Analyze solicitation files (recommended entry point)
results = analyzer.analyze_from_files(
    ["solicitation.pdf", "attachment.docx"],
    description="RFP for IT modernization services",
)

# Summary: one row per prompt
summary_df = results_to_dataframe(results)

# Evidence: one row per quote
evidence_df = evidence_to_dataframe(results)
```

## Working with Results

`analyze_from_files()` returns a dict mapping prompt name to its parsed result:

```python
{
    "metadata": {"contract_type": "FFP", "performance_period": "1 base + 4 option", ...},
    "requirement_sprawl": {"severity": 2, "reasoning": "...", "evidence": [...]},
    ...
}
```

### `results_to_dataframe(results)`

One row per prompt. Columns:

| Column | Description |
|---|---|
| `prompt` | Prompt name (e.g. `"requirement_sprawl"`) |
| `severity` | 1–3 Likert score (None for non-sin prompts like metadata) |
| `severity_label` | `"Minimal"`, `"Moderate"`, or `"Severe"` |
| `reasoning` | LLM's overall reasoning |
| `evidence_count` | Number of evidence items found |

### `evidence_to_dataframe(results)`

One row per evidence item. Columns:

| Column | Description |
|---|---|
| `prompt` | Which prompt produced this evidence |
| `severity` | Severity of the parent prompt |
| `severity_label` | Human-readable severity |
| `quote` | Direct quote from the solicitation |
| `explanation` | Why this quote is relevant |

## Adding a New Prompt

1. Create a new `.py` file in `spotting_concrete_boats/prompts/` (e.g. `my_analysis.py`).
2. Export two names: `USER_PROMPT` (str) and `RESULT_SCHEMA` (a Pydantic `BaseModel` subclass).
3. Set the module docstring — its first line becomes the description shown by `describe_prompts()`.
4. That's it. The analyzer discovers it automatically at runtime.

### Template for a sin-type prompt

```python
"""Sin #N: Short title.

Longer description of what this sin means and why it matters.
"""

from typing import Literal

from pydantic import BaseModel, computed_field

from spotting_concrete_boats.prompts.common import SEVERITY_LABELS, SinEvidence


class MyResult(BaseModel):
    """One-line description of the result."""

    severity: Literal[1, 2, 3]
    evidence: list[SinEvidence]
    reasoning: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def severity_label(self) -> str:
        return SEVERITY_LABELS[self.severity]


RESULT_SCHEMA = MyResult

USER_PROMPT = """\
Analyze the solicitation for [sin name].

[Detailed instructions, examples, and grading rubric.]
"""
```

### Template for a non-sin prompt (no severity)

```python
"""Short description of what this extracts."""

from pydantic import BaseModel


class MyResult(BaseModel):
    """Fields to extract."""

    field_one: str | None
    field_two: list[str]


RESULT_SCHEMA = MyResult

USER_PROMPT = """\
Extract the following from the solicitation:
...
"""
```

## Package Architecture

| Module | Purpose |
|---|---|
| `analyzer.py` | `SolicitationAnalyzer` class — orchestrates concurrent prompt execution and result parsing |
| `documents.py` | File encoding utilities — base64 encodes files into Claude API content blocks |
| `sam.py` | `SAMClient` — searches SAM.gov, downloads attachments, enriches with descriptions |
| `prompts/__init__.py` | Prompt discovery — scans for prompt modules and builds `PromptConfig` objects |
| `prompts/common.py` | Shared types — `SinEvidence` model and `SEVERITY_LABELS` dict |
| `prompts/system.py` | System prompt shared across all analyses |
| `prompts/metadata.py` | Extracts contract type, performance period, evaluation criteria |
| `prompts/requirement_sprawl.py` | Sin #1 — prescriptive HOW vs. outcome-based WHAT |
| `prompts/compliance_over_outcomes.py` | Sin #2 — compliance burden over delivery |
| `prompts/rule_pools.py` | Sin #3 — restrictive eligibility rules |
| `prompts/insider_rewards.py` | Sin #4 — incumbent/insider advantages |

## Supported File Formats

| Extension | Type |
|---|---|
| `.pdf` | Document |
| `.doc`, `.docx` | Document |
| `.txt` | Document |
| `.jpg`, `.jpeg` | Image |
| `.png` | Image |
| `.gif` | Image |
| `.webp` | Image |

Unsupported formats (`.xls`, `.xlsx`, `.csv`) are skipped with a warning.
