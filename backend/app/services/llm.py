from __future__ import annotations

import json
from typing import Any, Dict, Optional

from litellm import acompletion

from app.core.settings import settings


async def llm_json(system: str, user: str, *, max_tokens: int = 1200) -> Dict[str, Any]:
    """
    Calls LiteLLM and returns parsed JSON.

    We instruct the model to output JSON only; we still defensively parse
    and raise a ValueError if it's not valid JSON.
    """
    if not settings.litellm_api_key:
        raise ValueError("LITELLM_API_KEY not configured")

    resp = await acompletion(
        model=settings.litellm_model,
        api_key=settings.litellm_api_key,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )

    content: Optional[str] = None
    try:
        content = resp["choices"][0]["message"]["content"]
    except Exception:
        content = None

    if not content:
        raise ValueError("Empty LLM response")

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON: {e}") from e

