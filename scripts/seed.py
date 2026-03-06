"""Seed script to populate the database with test data for all API capabilities.

Usage:
    uv run python -m scripts.seed          # seed data
    uv run python -m scripts.seed --clean   # remove seeded data
    uv run python -m scripts.seed --reset   # clean + seed
"""

import argparse
import asyncio

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.document import Document
from app.models.project import Project
from app.models.project_access import AccessRole, ProjectAccess
from app.models.user import User

# ── Test data ────────────────────────────────────────────────────────────────

USERS = [
    {
        "login": "alice",
        "email": "alice@example.com",
        "password": "Alice123!",
    },
    {
        "login": "bob",
        "email": "bob@example.com",
        "password": "Bob12345!",
    },
    {
        "login": "charlie",
        "email": "charlie@example.com",
        "password": "Charlie1!",
    },
    {
        "login": "inactive_user",
        "email": "inactive@example.com",
        "password": "Inactive1!",
        "is_active": False,
    },
]

PROJECTS = [
    {
        "name": "Website Redesign",
        "description": "Complete redesign of the company website with modern UI/UX.",
    },
    {
        "name": "Mobile App",
        "description": "Cross-platform mobile application for project management.",
    },
    {
        "name": "API Documentation",
        "description": "Comprehensive API docs with OpenAPI spec and examples.",
    },
    {
        "name": "Empty Project",
        "description": None,
    },
]

# (project_index, user_index, role)
ACCESS_MAP = [
    # Alice owns "Website Redesign" and "Empty Project"
    (0, 0, AccessRole.OWNER),
    (3, 0, AccessRole.OWNER),
    # Bob owns "Mobile App", participates in "Website Redesign"
    (1, 1, AccessRole.OWNER),
    (0, 1, AccessRole.PARTICIPANT),
    # Charlie owns "API Documentation", participates in "Mobile App"
    (2, 2, AccessRole.OWNER),
    (1, 2, AccessRole.PARTICIPANT),
]

# Fake documents (no actual S3 files — just DB records for testing queries)
DOCUMENTS = [
    # Website Redesign documents
    {
        "project_index": 0,
        "filename": "design_spec_v2.pdf",
        "original_filename": "design_spec_v2.pdf",
        "content_type": "application/pdf",
        "file_size": 2_500_000,
        "storage_key": "documents/1/abc12345_design_spec_v2.pdf",
    },
    {
        "project_index": 0,
        "filename": "wireframes.pdf",
        "original_filename": "wireframes.pdf",
        "content_type": "application/pdf",
        "file_size": 5_100_000,
        "storage_key": "documents/1/def67890_wireframes.pdf",
    },
    # Mobile App documents
    {
        "project_index": 1,
        "filename": "requirements.docx",
        "original_filename": "requirements.docx",
        "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "file_size": 180_000,
        "storage_key": "documents/2/ghi11111_requirements.docx",
    },
    # API Documentation documents
    {
        "project_index": 2,
        "filename": "openapi_spec.pdf",
        "original_filename": "openapi_spec.pdf",
        "content_type": "application/pdf",
        "file_size": 420_000,
        "storage_key": "documents/3/jkl22222_openapi_spec.pdf",
    },
]


# ── Seed logic ───────────────────────────────────────────────────────────────


async def seed(session: AsyncSession) -> None:
    """Insert all test data."""

    # 1. Create users
    users: list[User] = []
    for data in USERS:
        user = User(
            login=data["login"],
            email=data["email"],
            hashed_password=get_password_hash(data["password"]),
            is_active=data.get("is_active", True),
        )
        session.add(user)
        users.append(user)
    await session.flush()  # assigns IDs

    print(f"Created {len(users)} users:")
    for u in users:
        print(f"  - {u.login} (id={u.id}, active={u.is_active})")

    # 2. Create projects
    projects: list[Project] = []
    for data in PROJECTS:
        project = Project(name=data["name"], description=data["description"])
        session.add(project)
        projects.append(project)
    await session.flush()

    print(f"\nCreated {len(projects)} projects:")
    for p in projects:
        print(f"  - {p.name} (id={p.id})")

    # 3. Grant access
    for proj_idx, user_idx, role in ACCESS_MAP:
        access = ProjectAccess(
            user_id=users[user_idx].id,
            project_id=projects[proj_idx].id,
            role=role.value,
        )
        session.add(access)
    await session.flush()

    print(f"\nCreated {len(ACCESS_MAP)} access records:")
    for proj_idx, user_idx, role in ACCESS_MAP:
        print(f"  - {users[user_idx].login} -> {projects[proj_idx].name} ({role.value})")

    # 4. Create documents
    for data in DOCUMENTS:
        doc = Document(
            project_id=projects[data["project_index"]].id,
            filename=data["filename"],
            original_filename=data["original_filename"],
            content_type=data["content_type"],
            file_size=data["file_size"],
            storage_key=data["storage_key"],
        )
        session.add(doc)
    await session.flush()

    print(f"\nCreated {len(DOCUMENTS)} documents:")
    for d in DOCUMENTS:
        print(f"  - {d['original_filename']} -> {projects[d['project_index']].name}")

    await session.commit()
    print("\n✅ Seed complete!")


SEED_LOGINS = [u["login"] for u in USERS]


async def clean(session: AsyncSession) -> None:
    """Remove all seeded data (cascading deletes handle related records)."""
    result = await session.execute(delete(User).where(User.login.in_(SEED_LOGINS)))
    await session.commit()
    print(f"🗑️  Deleted {result.rowcount} seeded users (with cascading projects/documents).")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Database seed script")
    parser.add_argument("--clean", action="store_true", help="Remove seeded data")
    parser.add_argument("--reset", action="store_true", help="Clean and re-seed")
    args = parser.parse_args()

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        if args.clean:
            await clean(session)
        elif args.reset:
            await clean(session)
            await seed(session)
        else:
            await seed(session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
