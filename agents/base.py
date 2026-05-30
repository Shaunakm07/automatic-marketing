"""Shared base for all agents — wraps the Anthropic messages API."""

import anthropic
from config.settings import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def run_agent(
    system_prompt: str,
    user_message:  str,
    max_tokens:    int = 4096,
    temperature:   float = 1.0,
) -> str:
    """Single-turn agent call. Returns the text of the first content block."""
    response = _get_client().messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        temperature=temperature,
    )
    return response.content[0].text


def run_agent_with_history(
    system_prompt: str,
    messages:      list[dict],
    max_tokens:    int = 4096,
) -> str:
    """Multi-turn agent call."""
    response = _get_client().messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text
