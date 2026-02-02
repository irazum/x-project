"""Tests for project endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, ProjectAccess, User
from app.models.project_access import AccessRole


class TestCreateProject:
    """Tests for project creation."""

    @pytest.mark.asyncio
    async def test_create_project_success(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        """Test successful project creation."""
        response = await client.post(
            "/api/v1/projects",
            json={
                "name": "My New Project",
                "description": "A great project",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My New Project"
        assert data["description"] == "A great project"
        assert data["user_role"] == "owner"
        assert data["has_logo"] is False

    @pytest.mark.asyncio
    async def test_create_project_without_description(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        """Test project creation without description."""
        response = await client.post(
            "/api/v1/projects",
            json={"name": "Minimal Project"},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Project"
        assert data["description"] is None

    @pytest.mark.asyncio
    async def test_create_project_unauthorized(self, client: AsyncClient) -> None:
        """Test project creation without authentication."""
        response = await client.post(
            "/api/v1/projects",
            json={"name": "Test Project"},
        )

        assert response.status_code == 401


class TestGetProjects:
    """Tests for listing projects."""

    @pytest.mark.asyncio
    async def test_get_projects_empty(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        """Test getting projects when user has none."""
        response = await client.get("/api/v1/projects", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["projects"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_projects_with_access(
        self, client: AsyncClient, auth_headers: dict, test_project: Project
    ) -> None:
        """Test getting projects when user has access."""
        response = await client.get("/api/v1/projects", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["projects"]) == 1
        assert data["projects"][0]["name"] == "Test Project"


class TestGetProjectInfo:
    """Tests for getting project details."""

    @pytest.mark.asyncio
    async def test_get_project_info_success(
        self, client: AsyncClient, auth_headers: dict, test_project: Project
    ) -> None:
        """Test getting project info with access."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/info",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_project.id
        assert data["name"] == "Test Project"
        assert data["user_role"] == "owner"

    @pytest.mark.asyncio
    async def test_get_project_info_not_found(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        """Test getting non-existent project."""
        response = await client.get(
            "/api/v1/projects/99999/info",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_project_info_no_access(
        self,
        client: AsyncClient,
        test_project: Project,
        another_user: User,
    ) -> None:
        """Test getting project without access."""
        from app.core.security import create_access_token

        token = create_access_token(subject=another_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(
            f"/api/v1/projects/{test_project.id}/info",
            headers=headers,
        )

        assert response.status_code == 403


class TestUpdateProject:
    """Tests for updating projects."""

    @pytest.mark.asyncio
    async def test_update_project_success(
        self, client: AsyncClient, auth_headers: dict, test_project: Project
    ) -> None:
        """Test updating project with access."""
        response = await client.put(
            f"/api/v1/projects/{test_project.id}/info",
            json={
                "name": "Updated Project Name",
                "description": "Updated description",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Project Name"
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_project_partial(
        self, client: AsyncClient, auth_headers: dict, test_project: Project
    ) -> None:
        """Test partial project update."""
        response = await client.put(
            f"/api/v1/projects/{test_project.id}/info",
            json={"name": "New Name Only"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name Only"
        # Description should remain unchanged
        assert data["description"] == "A test project description"


class TestDeleteProject:
    """Tests for deleting projects."""

    @pytest.mark.asyncio
    async def test_delete_project_as_owner(
        self, client: AsyncClient, auth_headers: dict, test_project: Project
    ) -> None:
        """Test deleting project as owner."""
        response = await client.delete(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_project_as_participant(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_project: Project,
        another_user: User,
    ) -> None:
        """Test that participant cannot delete project."""
        # Add another_user as participant
        access = ProjectAccess(
            user_id=another_user.id,
            project_id=test_project.id,
            role=AccessRole.PARTICIPANT.value,
        )
        db_session.add(access)
        await db_session.commit()

        from app.core.security import create_access_token

        token = create_access_token(subject=another_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete(
            f"/api/v1/projects/{test_project.id}",
            headers=headers,
        )

        assert response.status_code == 403


class TestInviteUser:
    """Tests for inviting users to projects."""

    @pytest.mark.asyncio
    async def test_invite_user_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        another_user: User,
    ) -> None:
        """Test inviting user as owner."""
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/invite",
            params={"user": another_user.login},
            headers=auth_headers,
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_invite_nonexistent_user(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
    ) -> None:
        """Test inviting non-existent user."""
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/invite",
            params={"user": "nonexistent"},
            headers=auth_headers,
        )

        assert response.status_code == 404
