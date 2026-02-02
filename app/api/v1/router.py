"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, documents, projects

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["Projects"],
)

api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["Documents"],
)
