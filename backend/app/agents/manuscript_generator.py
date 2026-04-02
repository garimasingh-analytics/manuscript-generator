from __future__ import annotations

from typing import Any, Dict, List

from pydantic import ValidationError

from app.models.projects import Manuscript, StudySummary
from app.services.llm import llm_json


SYSTEM = """You are an expert medical writer for clinical/HEOR manuscripts.
Write a publication-ready IMRaD-style manuscript using the provided study summary and selected literature.

Return JSON ONLY with exactly these keys:
- title
- abstract
- introduction
- methods
- results
- evidence_comparison
- discussion
- conclusion
- references (array of objects; each must contain at least: title, doi (nullable), pmid (nullable), year (nullable), journal (nullable))
- citation_style (string; default 'vancouver')

Do not include any additional keys."""


def _paper_ref(p: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": p.get("title"),
        "doi": p.get("doi"),
        "pmid": p.get("pmid"),
        "year": p.get("year"),
        "journal": p.get("journal"),
        "authors": p.get("authors") or [],
    }


async def generate_manuscript(
    *, study_summary: StudySummary, selected_papers: List[Dict[str, Any]]
) -> Manuscript:
    refs = [_paper_ref(p) for p in selected_papers]
    user = {
        "study_summary": study_summary.model_dump(),
        "selected_papers": refs,
        "instructions": {
            "tone": "scientific, concise, journal-ready",
            "cite_in_text": "Use Vancouver-style numeric citations like [1], [2]",
        },
    }
    data = await llm_json(SYSTEM, str(user), max_tokens=2400)
    try:
        return Manuscript.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Invalid manuscript JSON: {e}") from e

