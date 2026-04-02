from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pymongo import ReturnDocument

from app.api.auth.deps import get_current_user
from app.db.mongo import projects_col
from app.models.papers import PapersUpdateRequest
from app.models.projects import ProjectCreate, ProjectOut, ProjectUpdate
from app.utils.ids import oid, str_id

router = APIRouter()


@router.get("", response_model=list[ProjectOut])
async def list_projects(current_user: dict = Depends(get_current_user)):
    cur = projects_col().find({"user_id": current_user["id"]}).sort("updated_at", -1)
    docs = [str_id(d) async for d in cur]
    return docs


@router.post("", response_model=ProjectOut)
async def create_project(payload: ProjectCreate, current_user: dict = Depends(get_current_user)):
    now = datetime.now(tz=timezone.utc).isoformat()
    doc = {
        "user_id": current_user["id"],
        "title": payload.title,
        "description": payload.description,
        "status": payload.status,
        "study_summary": {},
        "papers": [],
        "manuscript": {},
        "keyword_config": {"main_keywords": [], "exclusion_keywords": [], "mesh_terms": []},
        "created_at": now,
        "updated_at": now,
    }
    res = await projects_col().insert_one(doc)
    created = {"_id": res.inserted_id, **doc}
    return ProjectOut(**str_id(created))


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    doc = await projects_col().find_one({"_id": oid(project_id), "user_id": current_user["id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut(**str_id(doc))


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str, payload: ProjectUpdate, current_user: dict = Depends(get_current_user)
):
    update: dict = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    update["updated_at"] = datetime.now(tz=timezone.utc).isoformat()

    res = await projects_col().find_one_and_update(
        {"_id": oid(project_id), "user_id": current_user["id"]},
        {"$set": update},
        return_document=ReturnDocument.AFTER,
    )
    if not res:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut(**str_id(res))


@router.delete("/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    res = await projects_col().delete_one({"_id": oid(project_id), "user_id": current_user["id"]})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"ok": True}


@router.put("/{project_id}/papers", response_model=ProjectOut)
async def update_project_papers(
    project_id: str, payload: PapersUpdateRequest, current_user: dict = Depends(get_current_user)
):
    update = {
        "papers": [p.model_dump() for p in payload.papers],
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    res = await projects_col().find_one_and_update(
        {"_id": oid(project_id), "user_id": current_user["id"]},
        {"$set": update},
        return_document=ReturnDocument.AFTER,
    )
    if not res:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut(**str_id(res))

