from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


DatabaseSource = Literal[
    "pubmed",
    "pmc",
    "europe_pmc",
    "semantic_scholar",
    "crossref",
    "doaj",
    "biorxiv",
    "medrxiv",
]


class YearRange(BaseModel):
    start: Optional[int] = None
    end: Optional[int] = None


class LiteratureSearchRequest(BaseModel):
    databases: List[DatabaseSource] = Field(default_factory=lambda: ["pubmed", "europe_pmc", "crossref", "doaj"])
    max_results_per_db: int = 25

    main_keywords: List[str] = Field(default_factory=list)
    exclusion_keywords: List[str] = Field(default_factory=list)
    mesh_terms: List[str] = Field(default_factory=list)

    year_range: YearRange = Field(default_factory=YearRange)
    open_access_only: bool = False
    article_types: List[str] = Field(default_factory=list)  # best-effort across sources


class LiteratureSearchResponse(BaseModel):
    total_found: int
    total_after_dedupe: int
    by_database: dict
    papers: list[dict]
    errors: dict

