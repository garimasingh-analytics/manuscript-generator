from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.api.auth.deps import get_current_user
from app.db.mongo import projects_col
from app.services.exporter import (
    manuscript_to_docx,
    manuscript_to_markdown,
    manuscript_to_pdf,
    references_to_csv,
    references_to_json,
)
from app.utils.ids import oid

router = APIRouter()


@router.get("/{format}/{project_id}")
async def export_project(format: str, project_id: str, current_user: dict = Depends(get_current_user)):
    project = await projects_col().find_one({"_id": oid(project_id), "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    manuscript = project.get("manuscript") or {}
    title = (project.get("title") or "manuscript").strip().replace("/", "-")
    fmt = (format or "").lower()

    if fmt == "pdf":
        data = manuscript_to_pdf(manuscript)
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{title}.pdf"'},
        )

    if fmt == "docx":
        data = manuscript_to_docx(manuscript)
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{title}.docx"'},
        )

    if fmt == "markdown":
        md = manuscript_to_markdown(manuscript).encode("utf-8")
        return Response(
            content=md,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{title}.md"'},
        )

    if fmt == "references-json":
        data = references_to_json(manuscript)
        return Response(
            content=data,
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{title}-references.json"'},
        )

    if fmt == "references-csv":
        data = references_to_csv(manuscript)
        return Response(
            content=data,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{title}-references.csv"'},
        )

    raise HTTPException(
        status_code=400,
        detail="Unsupported format. Use: pdf, docx, markdown, references-json, references-csv",
    )

