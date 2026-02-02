# Single stage build - simpler and more reliable
FROM python:3.14-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libpq5 \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash appuser

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Create venv and install dependencies
ENV VIRTUAL_ENV="/app/venv"
ENV PATH="/app/venv/bin:$PATH"
ENV UV_LINK_MODE=copy
RUN uv venv /app/venv && uv sync --frozen --no-install-project --no-dev

# Copy application code
COPY --chown=appuser:appuser . .

# Fix venv ownership for appuser
RUN chown -R appuser:appuser /app/venv

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application - use python directly from PATH (venv is in PATH)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
