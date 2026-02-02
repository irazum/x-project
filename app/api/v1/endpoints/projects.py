"""Project endpoints."""

from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile, status

from app.api.deps import (
    CurrentUser,
    DocumentServiceDep,
    LogoServiceDep,
    ProjectServiceDep,
)
from app.core.exceptions import (
    AppException,
    AuthorizationError,
    NotFoundError,
    OwnerRequiredError,
)
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.schemas.project import (
    ProjectCreate,
    ProjectInfoResponse,
    ProjectListResponse,
    ProjectUpdate,
)

router = APIRouter()


@router.post(
    "",
    response_model=ProjectInfoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    responses={
        201: {"description": "Project created successfully"},
        401: {"description": "Not authenticated"},
    },
)
async def create_project(
    data: ProjectCreate,
    current_user: CurrentUser,
    project_service: ProjectServiceDep,
) -> ProjectInfoResponse:
    """
    Create a new project.

    The authenticated user becomes the owner of the project.

    - **name**: Project name
    - **description**: Optional project description
    """
    return await project_service.create_project(data, current_user.id)


@router.get(
    "",
    response_model=ProjectListResponse,
    summary="Get all accessible projects",
    responses={
        200: {"description": "List of projects"},
        401: {"description": "Not authenticated"},
    },
)
async def get_projects(
    current_user: CurrentUser,
    project_service: ProjectServiceDep,
) -> ProjectListResponse:
    """
    Get all projects accessible by the current user.

    Returns projects where the user is either an owner or participant,
    including all documents for each project.
    """
    return await project_service.get_projects(current_user.id)


@router.get(
    "/{project_id}/info",
    response_model=ProjectInfoResponse,
    summary="Get project details",
    responses={
        200: {"description": "Project info"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied"},
        404: {"description": "Project not found"},
    },
)
async def get_project_info(
    project_id: int,
    current_user: CurrentUser,
    project_service: ProjectServiceDep,
) -> ProjectInfoResponse:
    """
    Get project details.

    Requires the user to have access to the project (owner or participant).
    """
    try:
        return await project_service.get_project_info(project_id, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e


@router.put(
    "/{project_id}/info",
    response_model=ProjectInfoResponse,
    summary="Update project details",
    responses={
        200: {"description": "Project updated"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied"},
        404: {"description": "Project not found"},
    },
)
async def update_project_info(
    project_id: int,
    data: ProjectUpdate,
    current_user: CurrentUser,
    project_service: ProjectServiceDep,
) -> ProjectInfoResponse:
    """
    Update project details.

    Requires the user to have access to the project.

    - **name**: New project name (optional)
    - **description**: New project description (optional)
    """
    try:
        return await project_service.update_project_info(project_id, data, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    responses={
        204: {"description": "Project deleted"},
        401: {"description": "Not authenticated"},
        403: {"description": "Owner access required"},
        404: {"description": "Project not found"},
    },
)
async def delete_project(
    project_id: int,
    current_user: CurrentUser,
    project_service: ProjectServiceDep,
) -> None:
    """
    Delete a project and all its documents and logo.

    Only the project owner can delete a project.
    """
    try:
        await project_service.delete_project(project_id, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except OwnerRequiredError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e


# Document endpoints under project
@router.get(
    "/{project_id}/documents",
    response_model=list[DocumentResponse],
    summary="Get project documents",
    responses={
        200: {"description": "List of documents"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied"},
        404: {"description": "Project not found"},
    },
)
async def get_project_documents(
    project_id: int,
    current_user: CurrentUser,
    document_service: DocumentServiceDep,
) -> list[DocumentResponse]:
    """
    Get all documents for a project.

    Requires the user to have access to the project.
    """
    try:
        return await document_service.get_project_documents(project_id, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e


@router.post(
    "/{project_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload documents to project",
    responses={
        201: {"description": "Documents uploaded"},
        400: {"description": "Invalid file"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied"},
        404: {"description": "Project not found"},
    },
)
async def upload_documents(
    project_id: int,
    current_user: CurrentUser,
    document_service: DocumentServiceDep,
    files: Annotated[list[UploadFile], File(description="Document files to upload")],
) -> DocumentUploadResponse:
    """
    Upload one or more documents to a project.

    Allowed file types: PDF, DOCX
    Maximum file size: 50MB per file

    Requires the user to have access to the project.
    """
    try:
        return await document_service.upload_documents(project_id, current_user.id, files)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


# Logo endpoints
@router.get(
    "/{project_id}/logo",
    summary="Get project logo",
    responses={
        200: {"description": "Logo image", "content": {"image/jpeg": {}}},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied"},
        404: {"description": "Project or logo not found"},
    },
)
async def get_logo(
    project_id: int,
    current_user: CurrentUser,
    logo_service: LogoServiceDep,
    thumbnail: Annotated[bool, Query(description="Return thumbnail instead of full logo")] = False,
) -> Response:
    """
    Get project logo image.

    Use `thumbnail=true` to get a smaller version.

    Requires the user to have access to the project.
    """
    try:
        content, content_type = await logo_service.get_logo(
            project_id, current_user.id, thumbnail=thumbnail
        )
        return Response(content=content, media_type=content_type)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e


@router.put(
    "/{project_id}/logo",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Upload or update project logo",
    responses={
        204: {"description": "Logo updated"},
        400: {"description": "Invalid file"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied"},
        404: {"description": "Project not found"},
    },
)
async def upsert_logo(
    project_id: int,
    current_user: CurrentUser,
    logo_service: LogoServiceDep,
    file: Annotated[UploadFile, File(description="Logo image file")],
) -> None:
    """
    Upload or replace project logo.

    The logo will be automatically resized and a thumbnail will be created.

    Allowed file types: JPEG, PNG, GIF, WebP
    Maximum dimensions: 800x800 (will be resized if larger)

    Requires the user to have access to the project.
    """
    try:
        await logo_service.upsert_logo(project_id, current_user.id, file)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.delete(
    "/{project_id}/logo",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project logo",
    responses={
        204: {"description": "Logo deleted"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied"},
        404: {"description": "Project not found"},
    },
)
async def delete_logo(
    project_id: int,
    current_user: CurrentUser,
    logo_service: LogoServiceDep,
) -> None:
    """
    Delete project logo.

    Requires the user to have access to the project.
    """
    try:
        await logo_service.delete_logo(project_id, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e


# Invite endpoint
@router.post(
    "/{project_id}/invite",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Invite user to project",
    responses={
        204: {"description": "User invited"},
        401: {"description": "Not authenticated"},
        403: {"description": "Owner access required"},
        404: {"description": "Project or user not found"},
        409: {"description": "User already has access"},
    },
)
async def invite_user(
    project_id: int,
    current_user: CurrentUser,
    project_service: ProjectServiceDep,
    user: Annotated[str, Query(description="Login of the user to invite")],
) -> None:
    """
    Invite a user to the project.

    The invited user will be granted participant permissions.

    Only the project owner can invite users.

    - **user**: Login of the user to invite
    """
    try:
        await project_service.invite_user(project_id, current_user.id, user)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except OwnerRequiredError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message) from e
