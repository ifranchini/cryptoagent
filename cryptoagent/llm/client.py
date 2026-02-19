"""Thin LiteLLM wrapper for model-agnostic LLM calls."""

from __future__ import annotations

import json
import logging

import litellm

logger = logging.getLogger(__name__)

# Suppress noisy LiteLLM logs
litellm.suppress_debug_info = True


def call_llm(
    model: str,
    system: str,
    user: str,
    *,
    temperature: float = 0.3,
    response_format: dict | None = None,
    max_tokens: int = 4096,
) -> str:
    """Universal LLM call via LiteLLM. Works with any provider.

    Args:
        model: LiteLLM model string (e.g. "openai/gpt-4o-mini", "anthropic/claude-sonnet-4-20250514")
        system: System prompt
        user: User prompt
        temperature: Sampling temperature
        response_format: Optional JSON mode ({"type": "json_object"})
        max_tokens: Maximum response tokens

    Returns:
        The model's response text.
    """
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    kwargs: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format is not None:
        kwargs["response_format"] = response_format

    logger.info("Calling LLM: model=%s tokens=%d", model, max_tokens)

    response = litellm.completion(**kwargs)
    content = response.choices[0].message.content or ""

    logger.info(
        "LLM response: model=%s usage=%s",
        model,
        response.usage,
    )
    return content


def call_llm_json(
    model: str,
    system: str,
    user: str,
    *,
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> dict:
    """Call LLM and parse response as JSON.

    Falls back to extracting JSON from markdown code blocks if JSON mode
    isn't supported by the provider.
    """
    raw = call_llm(
        model=model,
        system=system + "\n\nYou MUST respond with valid JSON only. No markdown, no explanation.",
        user=user,
        temperature=temperature,
        response_format={"type": "json_object"},
        max_tokens=max_tokens,
    )

    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try extracting from code block
    if "```" in raw:
        start = raw.find("```")
        # Skip optional language tag
        start = raw.find("\n", start) + 1
        end = raw.find("```", start)
        if end > start:
            try:
                return json.loads(raw[start:end].strip())
            except json.JSONDecodeError:
                pass

    # Last resort: find first { ... } block
    brace_start = raw.find("{")
    brace_end = raw.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        try:
            return json.loads(raw[brace_start : brace_end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from LLM response:\n{raw[:500]}")
