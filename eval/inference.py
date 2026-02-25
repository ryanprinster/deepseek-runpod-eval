"""RunPod vLLM OpenAI-compatible inference client."""
from __future__ import annotations

from datetime import datetime, timezone

import openai

import config


def build_client() -> openai.OpenAI:
    if not config.RUNPOD_API_KEY:
        raise RuntimeError("RUNPOD_API_KEY is not set. Copy .env.example to .env and fill in values.")
    if not config.RUNPOD_ENDPOINT_ID:
        raise RuntimeError("RUNPOD_ENDPOINT_ID is not set. Copy .env.example to .env and fill in values.")
    return openai.OpenAI(api_key=config.RUNPOD_API_KEY, base_url=config.BASE_URL)


def run_inference(
    prompt: str,
    *,
    client: openai.OpenAI | None = None,
    temperature: float = config.TEMPERATURE,
    max_tokens: int = config.MAX_TOKENS,
    n: int = config.N_SAMPLES,
) -> list[str]:
    """Run inference for a single prompt and return list of raw outputs.

    Forces chain-of-thought by prefilling the assistant turn with '<think>\n'.
    No system prompt per DeepSeek-R1 recommendation.
    """
    if client is None:
        client = build_client()

    messages = [
        {"role": "user", "content": prompt},
        # Prefill assistant turn to force CoT
        {"role": "assistant", "content": "<think>\n"},
    ]

    response = client.chat.completions.create(
        model=config.MODEL_NAME,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        n=n,
    )

    outputs = []
    for choice in response.choices:
        # Prepend the prefill so downstream parsers see a complete <think> block
        content = choice.message.content or ""
        full = "<think>\n" + content
        outputs.append(full)

    return outputs


def sampled_at_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
