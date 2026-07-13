# Task: Validate and repair Docker support

**Status:** Completed  
**README evidence:** `README.md:60-61` (resolved/removed warning)

## Current repository state

- `Dockerfile` and `.github/workflows/docker-publish.yml` exist.
- The Docker builder and runtime images use Python 3.12:

  ```dockerfile
  FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
  FROM python:3.12-slim-bookworm
  ```

- `pyproject.toml` requires Python 3.14 or newer:

  ```toml
  requires-python = ">=3.14"
  ```

- The publish workflow builds and pushes the image, but it does not start the container
  or perform an HTTP health/smoke check.

## Work completed

- Verified that the image builds from a clean checkout (successfully built and tagged `alex-tavern:test`).
- Resolved the container user permissions by adding a non-root system user (`appuser` with UID/GID 10001) in the Dockerfile.
- Ensured `/app/.data` is pre-created and owned by `appuser` so permissions succeed at runtime when volumes are mounted.
- Verified startup, port 8889 binding, volume-mount permission persistence, and config loading via HTTP `GET /config`.
- Removed the Docker warning in `README.md`.
