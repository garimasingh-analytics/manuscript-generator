from __future__ import annotations

from pydantic import ValidationError

from app.models.projects import StudySummary
from app.services.llm import llm_json


SYSTEM = """You are a clinical/HEOR research assistant.
Extract a structured study summary from the provided report text.

Return JSON ONLY with exactly these keys:
- population_setting (string or null)
- sample_size (string or null)
- study_design (string or null)
- interventions (array of strings)
- comparators (array of strings)
- outcomes (array of strings)
- effect_sizes (array of strings)
- conclusions (string or null)

Do not include any additional keys."""


async def parse_study_summary(report_text: str) -> StudySummary:
    user = f"""Report text:
---
{report_text[:120_000]}
---

Extract PICO elements plus study design, sample size, effect sizes, and conclusions."""

    data = await llm_json(SYSTEM, user, max_tokens=1400)
    try:
        return StudySummary.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Invalid study_summary JSON: {e}") from e

