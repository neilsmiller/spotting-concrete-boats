"""Prompts package for solicitation sin analysis.

Each sin has its own prompt module containing a USER_PROMPT string, a Pydantic
RESULT_SCHEMA, and the schema class itself. The system prompt is shared across
all analyses.

The package discovers its own prompt modules at import time via
``discover_prompts()``, so adding a new prompt module is all that's needed to
extend the analysis pipeline.

Usage:
    from spotting_concrete_boats.prompts import discover_prompts, SYSTEM_PROMPT

    prompts = discover_prompts()
    # {"sin__requirement_sprawl": PromptConfig(...), "metadata": PromptConfig(...), ...}
"""

import importlib
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from spotting_concrete_boats.prompts.common import SEVERITY_LABELS, STRENGTH_LABELS
from spotting_concrete_boats.prompts.system import SYSTEM_PROMPT

_PROMPTS_DIR = Path(__file__).parent
_PROMPTS_PACKAGE = "spotting_concrete_boats.prompts"
_SKIP_MODULES = {"__init__", "system", "schemas", "common"}


@dataclass
class PromptConfig:
    """Configuration for a single analysis prompt."""

    name: str
    user_prompt: str
    result_schema: type[BaseModel]
    description: str = ""


def discover_prompts() -> dict[str, PromptConfig]:
    """Scan the prompts package and return all valid prompt configurations.

    Each prompt module must export both ``USER_PROMPT`` (str) and
    ``RESULT_SCHEMA`` (BaseModel subclass). Modules missing either attribute
    raise ``ValueError`` immediately so misconfiguration is caught at startup.

    Returns:
        Dict mapping module name to its PromptConfig.
    """
    prompts: dict[str, PromptConfig] = {}

    for path in sorted(_PROMPTS_DIR.glob("*.py")):
        module_name = path.stem
        if module_name in _SKIP_MODULES:
            continue

        full_name = f"{_PROMPTS_PACKAGE}.{module_name}"
        mod = importlib.import_module(full_name)

        if not hasattr(mod, "USER_PROMPT"):
            raise ValueError(f"Prompt module {full_name} is missing USER_PROMPT")
        if not hasattr(mod, "RESULT_SCHEMA"):
            raise ValueError(f"Prompt module {full_name} is missing RESULT_SCHEMA")

        description = ""
        if mod.__doc__:
            description = mod.__doc__.strip().split("\n")[0].strip()

        prompts[module_name] = PromptConfig(
            name=module_name,
            user_prompt=mod.USER_PROMPT,
            result_schema=mod.RESULT_SCHEMA,
            description=description,
        )

    return prompts


__all__ = [
    "SEVERITY_LABELS",
    "STRENGTH_LABELS",
    "SYSTEM_PROMPT",
    "PromptConfig",
    "discover_prompts",
]
