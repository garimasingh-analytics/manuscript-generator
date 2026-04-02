from fastapi import APIRouter

from app.api.auth.routes import router as auth_router
from app.api.projects.routes import router as projects_router
from app.api.agents.routes import router as agents_router
from app.api.export.routes import router as export_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(agents_router, prefix="/agents", tags=["agents"])
api_router.include_router(export_router, prefix="/export", tags=["export"])

