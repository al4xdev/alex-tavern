FROM ghcr.io/astral-sh/uv:python3.14-alpine AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

# Copy dependency files first to leverage Docker layer caching
COPY uv.lock pyproject.toml /app/

# Install dependencies without installing the project itself
RUN uv sync --frozen --no-install-project --no-dev

# Copy the rest of the application code
COPY . /app

# Sync the project
RUN uv sync --frozen --no-dev

# Use an ultra-small Python 3.14 Alpine runner image
FROM python:3.14-alpine
WORKDIR /app
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"

# Expose the API port
EXPOSE 8889

# Create data directory volume
VOLUME [ "/app/.data" ]

# Command to run uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8889"]
