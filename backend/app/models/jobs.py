from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel


JobStatus = Literal["queued", "running", "completed", "failed"]


class StartGenerationResponse(BaseModel):
    job_id: str
    status: JobStatus


class GenerationStatusResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    status: JobStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

