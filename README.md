# Project Management API

A FastAPI-based project management dashboard API with PostgreSQL, SQLAlchemy, and AWS S3 integration.

## Features

- 🔐 JWT-based authentication
- 📁 Project CRUD operations
- 📄 Document management (upload, download, delete)
- 🖼️ Logo management with automatic resizing
- 👥 Project sharing and access control
- 🐳 Docker support
- 🧪 Comprehensive test suite
- 🔄 CI/CD with GitHub Actions

## Tech Stack

- **Python 3.14+**
- **FastAPI** - Modern web framework
- **SQLAlchemy 2.0** - Async ORM
- **PostgreSQL** - Database
- **Alembic** - Database migrations
- **AWS S3** - File storage
- **Docker** - Containerization
- **Pytest** - Testing

## Project Structure

```
.
├── app/
│   ├── api/
│   │   ├── deps.py           # Dependency injection
│   │   └── v1/
│   │       ├── endpoints/    # API route handlers
│   │       └── router.py     # API router
│   ├── core/
│   │   ├── config.py         # Settings management
│   │   ├── security.py       # JWT & password hashing
│   │   └── exceptions.py     # Custom exceptions
│   ├── db/
│   │   ├── base.py           # SQLAlchemy base
│   │   └── session.py        # Database session
│   ├── models/               # SQLAlchemy models
│   ├── repositories/         # Data access layer
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic
│   └── main.py               # Application entry point
├── alembic/                  # Database migrations
├── tests/                    # Test suite
├── docker/                   # Docker configurations
├── .github/workflows/        # CI/CD pipelines
└── pyproject.toml            # Project configuration
```

## Quick Start

### Prerequisites

- Python 3.14+
- UV (Python package manager)
- PostgreSQL 14+
- Docker & Docker Compose (optional)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd x_project
   ```

2. **Install UV** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install dependencies**
   ```bash
   uv sync --dev
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations**
   ```bash
   uv run alembic upgrade head
   ```

6. **Start the development server**
   ```bash
   uv run uvicorn app.main:app --reload
   ```

### Using Docker (Development)

```bash
# Start all services
docker-compose up -d

# Rebuild containers after Dockerfile changes
docker-compose up --build -d

# Run migrations
docker-compose exec api alembic upgrade head

# View logs
docker-compose logs -f api
```

### Production Deployment

```bash
# 1. Create production env file from template
cp .env.production.example .env.production
# Edit .env.production with real credentials

# 2. Start services
docker-compose -f docker-compose.prod.yml up -d

# 3. Run migrations (one-time)
docker-compose -f docker-compose.prod.yml --profile migration up migrate

# 4. View logs
docker-compose -f docker-compose.prod.yml logs -f api
```

Key differences from development:
- No hardcoded secrets — all credentials loaded from `.env.production`
- PostgreSQL requires password for all connections (custom `pg_hba.conf`)
- DB port not exposed to host — only reachable via internal Docker network
- No source code volume mounts — uses the built image
- No LocalStack — uses real AWS S3

## API Documentation

Once running, access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Create new user
- `POST /api/v1/auth/login` - Login and get JWT token

### Projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects` - List accessible projects
- `GET /api/v1/projects/{id}/info` - Get project details
- `PUT /api/v1/projects/{id}/info` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project (owner only)

### Documents
- `GET /api/v1/projects/{id}/documents` - List project documents
- `POST /api/v1/projects/{id}/documents` - Upload documents
- `GET /api/v1/documents/{id}` - Download document
- `PUT /api/v1/documents/{id}` - Update document
- `DELETE /api/v1/documents/{id}` - Delete document

### Logo
- `GET /api/v1/projects/{id}/logo` - Get project logo
- `PUT /api/v1/projects/{id}/logo` - Upload/update logo
- `DELETE /api/v1/projects/{id}/logo` - Delete logo

### Access Control
- `POST /api/v1/projects/{id}/invite` - Invite user to project

## Testing

This project includes both **unit tests** and **integration tests** for comprehensive coverage.

### Test Types

| Type | Location | Description |
|------|----------|-------------|
| **Unit Tests** | `tests/unit/` | Fast, isolated tests with mocked dependencies |
| **Integration Tests** | `tests/integration/` | Full API flow tests with real database |

### Prerequisites for Integration Tests

> **Note:** Integration tests require only the **database** service to be running (the API is loaded in-process by pytest). Start the database first:
> ```bash
> docker-compose up -d db
> ```

Before running integration tests, ensure the test database exists:

```bash
# If using Docker (recommended)
docker-compose exec db psql -U postgres -c "CREATE DATABASE test_project_management;"

# If using local PostgreSQL
psql -U postgres -c "CREATE DATABASE test_project_management;"
```

### Running Tests

```bash
# Run all tests (unit + integration)
uv run pytest

# Run only unit tests (fast, no database required)
uv run pytest tests/unit/ -v

# Run only integration tests (requires database)
uv run pytest tests/api/ -v

# Run with coverage report
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/api/test_projects.py -v

# Run specific test class
uv run pytest tests/api/test_auth.py::TestRegister -v

# Stop on first failure
uv run pytest -x
```

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures for integration tests
├── integration/                # Integration tests (API endpoints)
│   ├── test_auth.py         # Authentication endpoint tests
│   └── test_projects.py     # Project endpoint tests
└── unit/               # Unit tests (isolated, mocked)
    ├── test_security.py     # Password hashing & JWT token tests
    ├── test_schemas.py      # Pydantic schema validation tests
    └── test_auth_service.py # AuthService business logic tests
```

### Test Fixtures (Integration Tests)

| Fixture | Description |
|---------|-------------|
| `db_session` | Fresh database session per test (tables created/dropped) |
| `client` | Async HTTP client for API requests |
| `test_user` | Pre-created user for authenticated tests |
| `auth_headers` | JWT authorization headers |
| `test_project` | Pre-created project with owner access |
| `another_user` | Secondary user for access control tests |

> **Note:** Each integration test runs with a clean database state — tables are created before and dropped after each test function.
> **Unit tests** run without any external dependencies (database, S3, etc.) and use mocks for all external services.

## Pre-commit hooks
Install pre-commit hooks to use linter, formatter, and type checker automatically
```bash
pre-commit install
```

## Linting & Formatting

```bash
# Run linter
ruff check .

# Fix linting issues
ruff check . --fix

# Type checking
mypy app
```

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "<description>"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `JWT_SECRET_KEY` | Secret key for JWT signing | Required |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | 60 |
| `S3_BUCKET_NAME` | AWS S3 bucket name | Required |
| `AWS_ACCESS_KEY_ID` | AWS access key | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Required |

See `.env.example` for all available options.

## License

MIT License
