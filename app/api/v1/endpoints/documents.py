"""Document endpoints."""

from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Response, UploadFile, status

from app.api.deps import CurrentUser, DocumentServiceDep
from app.core.exceptions import AppException, AuthorizationError, NotFoundError
from app.schemas.document import DocumentResponse

router = APIRouter()


@router.get(
    "/{document_id}",
    summary="Download document",
    responses={
        200: {"description": "Document file", "content": {"application/octet-stream": {}}},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied"},
        404: {"description": "Document not found"},
    },
)
async def download_document(
    document_id: int,
    current_user: CurrentUser,
    document_service: DocumentServiceDep,
) -> Response:
    """
    Download a document.

    Requires the user to have access to the project containing the document.
    """
    try:
        content, content_type, filename = await document_service.get_document(
            document_id, current_user.id
        )
        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(content)),
            },
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e


@router.put(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Update document",
    responses={
        200: {"description": "Document updated"},
        400: {"description": "Invalid file"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied"},
        404: {"description": "Document not found"},
    },
)
async def update_document(
    document_id: int,
    current_user: CurrentUser,
    document_service: DocumentServiceDep,
    file: Annotated[UploadFile, File(description="New document file")],
) -> DocumentResponse:
    """
    Replace a document with a new file.

    Allowed file types: PDF, DOCX
    Maximum file size: 50MB

    Requires the user to have access to the project containing the document.
    """
    try:
        return await document_service.update_document(document_id, current_user.id, file)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
    responses={
        204: {"description": "Document deleted"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access denied"},
        404: {"description": "Document not found"},
    },
)
async def delete_document(
    document_id: int,
    current_user: CurrentUser,
    document_service: DocumentServiceDep,
) -> None:
    """
    Delete a document.

    Requires the user to have access to the project containing the document.
    """
    try:
        await document_service.delete_document(document_id, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e
