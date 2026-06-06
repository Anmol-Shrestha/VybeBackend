FROM python:3.11-slim
WORKDIR /app

# Pull uv natively from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the system PATH for our virtual environment binaries
ENV PATH="/app/.venv/bin:$PATH"

# Copy lockfiles and source code (needed for editable install)
COPY pyproject.toml ./
COPY src ./src

# Sync dependencies (MCP is pure Python, no compilation needed)
RUN uv sync

EXPOSE 5000
CMD ["uv", "run", "python", "-m", "vybesix_mcp.server"]
