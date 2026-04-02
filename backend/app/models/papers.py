from __future__ import annotations

from typing import List

from pydantic import BaseModel

from app.models.projects import Paper


class PapersUpdateRequest(BaseModel):
    papers: List[Paper]

