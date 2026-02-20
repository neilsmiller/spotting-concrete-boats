"""Async solicitation analyzer with dynamic prompt discovery.

Discovers prompt modules at runtime and runs all analyses concurrently using
asyncio. Uses client.messages.parse() for structured outputs via Pydantic schemas.

Usage:
    from spotting_concrete_boats import SolicitationAnalyzer

    analyzer = SolicitationAnalyzer()

    # Discover available prompts
    analyzer.available_prompts  # ["metadata", "sin__requirement_sprawl", ...]

    # Analyze from local files (recommended for notebooks)
    results = analyzer.analyze_from_files(["solicitation.pdf"], description="RFP for ...")

    # Or build blocks manually and analyze
    results = analyzer.analyze(document_blocks)
    # results: {"sin__requirement_sprawl": {...}, ...}

    single = analyzer.analyze_single(document_blocks, "metadata")
    # single: {"contract_type": "FFP", ...}
"""

import asyncio
import concurrent.futures
import warnings
from pathlib import Path
from typing import Any

import anthropic
import pandas as pd  # type: ignore[import-untyped]
from pydantic import BaseModel

from spotting_concrete_boats.documents import build_document_blocks, get_supported_extensions
from spotting_concrete_boats.prompts import (
    SEVERITY_LABELS,
    STRENGTH_LABELS,
    SYSTEM_PROMPT,
    PromptConfig,
    discover_prompts,
)

DEFAULT_MODEL = "claude-sonnet-4-6"


def _run_async(coro):
    """Run an async coroutine, compatible with Jupyter notebooks.

    When called from inside a running event loop (e.g. Jupyter), executes the
    coroutine in a separate thread with its own event loop to avoid the
    'cannot enter context' errors from nest_asyncio + Python 3.12.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No running loop — safe to use asyncio.run() directly
        return asyncio.run(coro)

    # Inside an existing event loop (Jupyter) — run in a new thread
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


class SolicitationAnalyzer:
    """Analyzes solicitation documents against all discovered sin prompts.

    Public methods are synchronous. Async parallelism is an internal
    optimization — callers don't need to manage event loops.

    Args:
        client: An AsyncAnthropic client instance. Created automatically if not provided.
        api_key: Anthropic API key. Falls back to the ANTHROPIC_API_KEY env var if not set.
        model: Claude model identifier.
        max_tokens: Maximum tokens for each API response.
        max_retries: Number of retries on rate limit errors.
        retry_wait: Seconds to wait between rate limit retries.
    """

    def __init__(
        self,
        client: anthropic.AsyncAnthropic | None = None,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = 2048,
        max_retries: int = 3,
        retry_wait: int = 60,
    ):
        if client and api_key:
            raise ValueError("Pass either 'client' or 'api_key', not both.")
        self._client = client or anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.retry_wait = retry_wait
        self.prompts = discover_prompts()
        self.system_prompt = SYSTEM_PROMPT
        # Cached system prompt for reuse across concurrent calls
        self._cached_system = [
            {
                "type": "text",
                "text": self.system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]

    def __repr__(self) -> str:
        prompt_names = ", ".join(self.available_prompts)
        return f"SolicitationAnalyzer(model={self.model!r}, prompts=[{prompt_names}])"

    # --- Public API ---

    def analyze_from_files(
        self,
        file_paths: list[str | Path],
        description: str | None = None,
        prompts: list[str] | None = None,
    ) -> dict[str, dict]:
        """Build content blocks from local files and run all prompts.

        Recommended entry point for Jupyter notebooks. Handles file encoding
        and content block construction automatically.

        Args:
            file_paths: Paths to solicitation files (PDF, DOCX, images, etc.).
            description: Optional text description to prepend as context.
            prompts: Optional list of prompt names to run. If None, runs all prompts.

        Returns:
            Dict mapping prompt name to its parsed result as a plain dict.

        Raises:
            ValueError: If no processable content is produced (all files skipped
                and no description provided).
            KeyError: If any name in ``prompts`` is not a discovered prompt.
        """
        blocks = build_document_blocks(file_paths, description=description)
        if not blocks:
            supported = sorted(get_supported_extensions())
            raise ValueError(
                "No processable content: all files were skipped and no description provided. "
                f"Supported formats: {', '.join(supported)}"
            )
        return self.analyze(blocks, prompts=prompts)

    def analyze(
        self,
        document_blocks: list[dict[str, Any]],
        prompts: list[str] | None = None,
    ) -> dict[str, dict]:
        """Run all discovered prompts concurrently against a solicitation.

        Uses prompt caching: the system prompt and document blocks are marked
        with cache_control so they're reused across all concurrent API calls.

        Args:
            document_blocks: List of content blocks representing the solicitation
                (text blocks, document blocks from build_document_content_block, etc.).
            prompts: Optional list of prompt names to run. If None, runs all prompts.

        Returns:
            Dict mapping prompt name to its parsed result as a plain dict. Prompts
            that fail (after retries) are excluded from the result and logged.

        Raises:
            KeyError: If any name in ``prompts`` is not a discovered prompt.
        """
        self._validate_prompt_names(prompts)
        return _run_async(self._analyze_async(document_blocks, prompts=prompts))

    def analyze_single(self, document_blocks: list[dict[str, Any]], prompt_name: str) -> dict:
        """Run a single named prompt against a solicitation.

        No cache_control is applied — each call is standalone.

        Args:
            document_blocks: List of content blocks representing the solicitation.
            prompt_name: Key from discover_prompts() (e.g., "metadata", "sin__rule_pools").

        Returns:
            The parsed result as a plain dict for the specified prompt.

        Raises:
            KeyError: If prompt_name is not a discovered prompt.
        """
        return _run_async(self._analyze_single_async(document_blocks, prompt_name))

    # --- Prompt Discovery ---

    @property
    def available_prompts(self) -> list[str]:
        """Return the names of all discovered analysis prompts."""
        return list(self.prompts.keys())

    def describe_prompts(self) -> pd.DataFrame:
        """Return a DataFrame of available prompts and their descriptions."""
        rows = [
            {"name": config.name, "description": config.description}
            for config in self.prompts.values()
        ]
        return pd.DataFrame(rows)

    # --- Internal Implementation ---

    def _validate_prompt_names(self, prompts: list[str] | None) -> None:
        """Raise KeyError if any name in ``prompts`` is not a discovered prompt."""
        if prompts is None:
            return
        unknown = set(prompts) - set(self.prompts)
        if unknown:
            raise KeyError(
                f"Unknown prompt(s): {sorted(unknown)}. "
                f"Available prompts: {self.available_prompts}"
            )

    async def _analyze_async(
        self,
        document_blocks: list[dict[str, Any]],
        prompts: list[str] | None = None,
    ) -> dict[str, dict]:
        """Run all prompts concurrently with prompt caching."""
        # Document blocks with cache_control on the last block
        cached_doc_blocks = []
        for i, block in enumerate(document_blocks):
            b = dict(block)
            if i == len(document_blocks) - 1:
                b["cache_control"] = {"type": "ephemeral"}
            cached_doc_blocks.append(b)

        configs_to_run = (
            [self.prompts[name] for name in prompts]
            if prompts is not None
            else list(self.prompts.values())
        )

        tasks = [self._run_prompt(cached_doc_blocks, config) for config in configs_to_run]
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)

        results: dict[str, dict] = {}
        failures: list[str] = []
        for config, outcome in zip(configs_to_run, outcomes):
            if isinstance(outcome, Exception):
                error_type = type(outcome).__name__
                failures.append(f"{config.name} ({error_type})")
            else:
                results[config.name] = outcome.model_dump()  # type: ignore[union-attr]

        total = len(configs_to_run)
        succeeded = total - len(failures)
        print(f"Analysis complete: {succeeded}/{total} prompts succeeded.")
        if failures:
            failure_str = ", ".join(failures)
            warnings.warn(f"Failed: {failure_str}", stacklevel=2)

        return results

    async def _analyze_single_async(
        self, document_blocks: list[dict[str, Any]], prompt_name: str
    ) -> dict:
        """Run a single prompt without caching."""
        if prompt_name not in self.prompts:
            raise KeyError(
                f"Unknown prompt '{prompt_name}'. " f"Available prompts: {self.available_prompts}"
            )
        config = self.prompts[prompt_name]

        messages = [
            {
                "role": "user",
                "content": [
                    *document_blocks,
                    {"type": "text", "text": config.user_prompt},
                ],
            }
        ]

        result = await self._call_parse(messages, config.result_schema)
        return result.model_dump()

    async def _run_prompt(
        self,
        cached_doc_blocks: list[dict[str, Any]],
        config: PromptConfig,
    ) -> BaseModel:
        """Build messages for a single prompt and call the API."""
        messages = [
            {
                "role": "user",
                "content": [
                    *cached_doc_blocks,
                    {"type": "text", "text": config.user_prompt},
                ],
            }
        ]

        return await self._call_parse(messages, config.result_schema, use_cache=True)

    async def _call_parse(
        self,
        messages: list[dict[str, Any]],
        result_schema: type[BaseModel],
        use_cache: bool = False,
    ) -> BaseModel:
        """Call client.messages.parse() with retry logic for rate limits.

        Args:
            messages: The messages list for the API call.
            result_schema: Pydantic model class for structured output.
            use_cache: If True, use cached system prompt for prompt caching.

        Returns:
            Parsed Pydantic model instance.

        Raises:
            anthropic.RateLimitError: If rate limited after exhausting all retries.
            anthropic.APIStatusError: For non-rate-limit API errors (raised immediately).
        """
        system = self._cached_system if use_cache else self.system_prompt
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.messages.parse(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=system,
                    messages=messages,
                    output_format=result_schema,
                )
                return response.parsed_output
            except anthropic.RateLimitError:
                if attempt < self.max_retries:
                    print(
                        f"  Rate limit hit. Waiting {self.retry_wait}s "
                        f"(retry {attempt + 1}/{self.max_retries})..."
                    )
                    await asyncio.sleep(self.retry_wait)
                else:
                    raise


def _extract_score(
    data: dict[str, Any],
) -> tuple[str | None, int | None, str | None]:
    """Determine prompt type and extract the numeric score from a result dict.

    Sins have a ``severity`` field; virtues have a ``strength`` field.
    Prompts with neither (e.g. metadata) return all-None.

    Returns:
        (prompt_type, score, score_label) — e.g. ("sin", 3, "Severe") or
        ("virtue", 2, "Moderate").
    """
    severity = data.get("severity")
    if severity is not None:
        return "sin", severity, SEVERITY_LABELS.get(severity)

    strength = data.get("strength")
    if strength is not None:
        return "virtue", strength, STRENGTH_LABELS.get(strength)

    return None, None, None


def _format_metadata_as_reasoning(data: dict[str, Any]) -> str:
    """Format metadata fields into a readable string for the reasoning column."""
    parts = []
    if data.get("contract_type"):
        parts.append(f"Contract type: {data['contract_type']}")
    if data.get("performance_period"):
        parts.append(f"Performance period: {data['performance_period']}")
    criteria = data.get("evaluation_criteria", [])
    if criteria:
        parts.append(f"Evaluation criteria: {'; '.join(criteria)}")
    return " | ".join(parts) if parts else ""


def results_to_dataframe(results: dict[str, dict]) -> pd.DataFrame:
    """Convert analysis results to a summary DataFrame.

    Takes the dict returned by ``SolicitationAnalyzer.analyze()`` and returns a
    DataFrame with one row per prompt.

    Columns: prompt, prompt_type, sufficient_content, score, score_label,
    reasoning, evidence_count. Prompts without a severity/strength field
    (e.g. metadata) have their fields summarized in the reasoning column.

    Args:
        results: Dict mapping prompt name to its parsed result dict.

    Returns:
        pandas DataFrame with one row per prompt.
    """
    rows = []
    for prompt_name, data in results.items():
        prompt_type, score, score_label = _extract_score(data)
        reasoning = data.get("reasoning")
        if prompt_type is None and reasoning is None:
            reasoning = _format_metadata_as_reasoning(data)
        rows.append(
            {
                "prompt": prompt_name,
                "prompt_type": prompt_type,
                "sufficient_content": data.get("sufficient_content"),
                "score": score,
                "score_label": score_label,
                "reasoning": reasoning,
                "evidence_count": len(data["evidence"]) if "evidence" in data else None,
            }
        )
    return pd.DataFrame(rows)


def evidence_to_dataframe(results: dict[str, dict]) -> pd.DataFrame:
    """Convert analysis results to a DataFrame with one row per evidence item.

    Columns: prompt, prompt_type, sufficient_content, score, score_label,
    quote, explanation. Prompts without evidence are excluded.

    Args:
        results: Dict mapping prompt name to its parsed result dict.

    Returns:
        pandas DataFrame with one row per evidence item.
    """
    rows = []
    for prompt_name, data in results.items():
        prompt_type, score, score_label = _extract_score(data)
        for item in data.get("evidence", []):
            rows.append(
                {
                    "prompt": prompt_name,
                    "prompt_type": prompt_type,
                    "sufficient_content": data.get("sufficient_content"),
                    "score": score,
                    "score_label": score_label,
                    "quote": item.get("quote"),
                    "explanation": item.get("explanation"),
                }
            )
    return pd.DataFrame(rows)
