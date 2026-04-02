from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


ProjectStatus = Literal["draft", "in_progress", "completed", "archived"]


class KeywordConfig(BaseModel):
    main_keywords: list[str] = Field(default_factory=list)
    exclusion_keywords: list[str] = Field(default_factory=list)
    mesh_terms: list[str] = Field(default_factory=list)


class StudySummary(BaseModel):
    population_setting: Optional[str] = None
    sample_size: Optional[str] = None
    study_design: Optional[str] = None
    interventions: list[str] = Field(default_factory=list)
    comparators: list[str] = Field(default_factory=list)
    outcomes: list[str] = Field(default_factory=list)
    effect_sizes: list[str] = Field(default_factory=list)
    conclusions: Optional[str] = None


class Paper(BaseModel):
    id: Optional[str] = None
    title: str
    authors: list[str] = Field(default_factory=list)
    year: Optional[int] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    abstract: Optional[str] = None
    selected: bool = False
    classification: Optional[Literal["supporting", "contradicting", "background"]] = None
    database_source: Optional[str] = None


class Manuscript(BaseModel):
    title: Optional[str] = None
    abstract: Optional[str] = None
    introduction: Optional[str] = None
    methods: Optional[str] = None
    results: Optional[str] = None
    evidence_comparison: Optional[str] = None
    discussion: Optional[str] = None
    conclusion: Optional[str] = None
    references: list[dict] = Field(default_factory=list)
    citation_style: str = "vancouver"


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = None
    status: ProjectStatus = "draft"


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=300)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    keyword_config: Optional[KeywordConfig] = None


class ProjectOut(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    status: ProjectStatus
    study_summary: StudySummary = Field(default_factory=StudySummary)
    papers: list[Paper] = Field(default_factory=list)
    manuscript: Manuscript = Field(default_factory=Manuscript)
    keyword_config: KeywordConfig = Field(default_factory=KeywordConfig)
    created_at: str
    updated_at: str

