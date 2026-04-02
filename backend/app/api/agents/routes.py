from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pymongo import ReturnDocument

from app.agents.report_parser import parse_study_summary
from app.agents.literature_search import build_query, run_literature_search
from app.agents.manuscript_generator import generate_manuscript
from app.api.auth.deps import get_current_user
from app.db.mongo import jobs_col, projects_col
from app.models.jobs import GenerationStatusResponse, StartGenerationResponse
from app.models.literature import LiteratureSearchRequest, LiteratureSearchResponse
from app.utils.extract_text import extract_text_from_upload
from app.utils.dedupe import dedupe_papers, make_dedupe_key
from app.utils.ids import oid, str_id

router = APIRouter()


@router.post("/parse-report/{project_id}")
async def parse_report(
    project_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    project = await projects_col().find_one({"_id": oid(project_id), "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    raw = await file.read()
    try:
        text = extract_text_from_upload(file.filename or "", file.content_type, raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not text or len(text) < 100:
        raise HTTPException(status_code=400, detail="Could not extract enough text from file")

    try:
        summary = await parse_study_summary(text)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))

    now = datetime.now(tz=timezone.utc).isoformat()
    updated = await projects_col().find_one_and_update(
        {"_id": oid(project_id), "user_id": current_user["id"]},
        {"$set": {"study_summary": summary.model_dump(), "updated_at": now}},
        return_document=ReturnDocument.AFTER,
    )

    return str_id(updated)


@router.post("/search-literature/{project_id}", response_model=LiteratureSearchResponse)
async def search_literature(
    project_id: str,
    payload: LiteratureSearchRequest,
    current_user: dict = Depends(get_current_user),
):
    project = await projects_col().find_one({"_id": oid(project_id), "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    query = build_query(payload.main_keywords, payload.exclusion_keywords, payload.mesh_terms)
    raw_results, by_db, errors = await run_literature_search(
        databases=payload.databases, query=query, max_results_per_db=payload.max_results_per_db
    )

    # Merge any existing user selections/classification into the new results (by DOI/PMID/title).
    existing_papers = project.get("papers") or []
    existing_map = {}
    for ep in existing_papers:
        k = make_dedupe_key(ep)
        if k[1]:
            existing_map[k] = ep
    for p in raw_results:
        k = make_dedupe_key(p)
        old = existing_map.get(k)
        if old:
            if old.get("selected"):
                p["selected"] = True
            if old.get("classification"):
                p["classification"] = old.get("classification")

    total_found = len(raw_results)
    deduped = dedupe_papers(raw_results)

    # best-effort filters
    yr_start = payload.year_range.start
    yr_end = payload.year_range.end
    allowed_types = [t.strip().lower() for t in (payload.article_types or []) if t.strip()]
    filtered = []
    for p in deduped:
        y = p.get("year")
        if yr_start and y and y < yr_start:
            continue
        if yr_end and y and y > yr_end:
            continue
        if payload.open_access_only:
            # best-effort: DOAJ is OA; PMC is OA; Europe PMC may expose isOpenAccess/openAccess flags.
            if p.get("database_source") in ("doaj", "pmc"):
                pass
            elif p.get("open_access") is True:
                pass
            else:
                continue
        if allowed_types:
            ptype = (p.get("article_type") or p.get("type") or "").strip().lower()
            if ptype and not any(t in ptype for t in allowed_types):
                continue
        filtered.append(p)

    now = datetime.now(tz=timezone.utc).isoformat()
    await projects_col().update_one(
        {"_id": oid(project_id), "user_id": current_user["id"]},
        {
            "$set": {
                "papers": filtered,
                "keyword_config": {
                    "main_keywords": payload.main_keywords,
                    "exclusion_keywords": payload.exclusion_keywords,
                    "mesh_terms": payload.mesh_terms,
                },
                "updated_at": now,
            }
        },
    )

    return LiteratureSearchResponse(
        total_found=total_found,
        total_after_dedupe=len(filtered),
        by_database=by_db,
        papers=filtered,
        errors=errors,
    )


async def _run_generation_job(job_id: str):
    now = datetime.now(tz=timezone.utc).isoformat()
    job = await jobs_col().find_one_and_update(
        {"_id": oid(job_id)},
        {"$set": {"status": "running"}},
        return_document=ReturnDocument.AFTER,
    )
    if not job:
        return

    try:
        project = await projects_col().find_one({"_id": oid(job["project_id"]), "user_id": job["user_id"]})
        if not project:
            raise ValueError("Project not found")

        selected = [p for p in (project.get("papers") or []) if p.get("selected")]
        if not selected:
            raise ValueError("No selected papers")

        from app.models.projects import StudySummary  # local import to avoid cycles

        ss = StudySummary.model_validate(project.get("study_summary") or {})
        manuscript = await generate_manuscript(study_summary=ss, selected_papers=selected)

        completed_at = datetime.now(tz=timezone.utc).isoformat()
        await projects_col().update_one(
            {"_id": oid(job["project_id"]), "user_id": job["user_id"]},
            {"$set": {"manuscript": manuscript.model_dump(), "updated_at": completed_at}},
        )

        await jobs_col().update_one(
            {"_id": oid(job_id)},
            {
                "$set": {
                    "status": "completed",
                    "result": manuscript.model_dump(),
                    "error": None,
                    "completed_at": completed_at,
                }
            },
        )
    except Exception as e:
        completed_at = datetime.now(tz=timezone.utc).isoformat()
        await jobs_col().update_one(
            {"_id": oid(job_id)},
            {"$set": {"status": "failed", "error": str(e), "completed_at": completed_at}},
        )


@router.post("/generate-manuscript/{project_id}", response_model=StartGenerationResponse)
async def start_generation(project_id: str, current_user: dict = Depends(get_current_user)):
    project = await projects_col().find_one({"_id": oid(project_id), "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    selected = [p for p in (project.get("papers") or []) if p.get("selected")]
    if not selected:
        raise HTTPException(status_code=400, detail="Select at least one paper before generating")

    now = datetime.now(tz=timezone.utc).isoformat()
    doc = {
        "project_id": project_id,
        "user_id": current_user["id"],
        "status": "queued",
        "result": None,
        "error": None,
        "created_at": now,
        "completed_at": None,
    }
    res = await jobs_col().insert_one(doc)
    job_id = str(res.inserted_id)

    # Fire-and-forget async background task for LLM generation.
    asyncio.create_task(_run_generation_job(job_id))

    return StartGenerationResponse(job_id=job_id, status="queued")


@router.get("/generation-status/{job_id}", response_model=GenerationStatusResponse)
async def generation_status(job_id: str, current_user: dict = Depends(get_current_user)):
    job = await jobs_col().find_one({"_id": oid(job_id), "user_id": current_user["id"]})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return GenerationStatusResponse(**str_id(job))

