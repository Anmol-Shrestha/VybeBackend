FROM python:3.11-slim
WORKDIR /app

# Pull uv natively from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the system PATH for our virtual environment binaries
ENV PATH="/app/.venv/bin:$PATH"

# Copy lockfiles
COPY pyproject.toml uv.lock ./

# ⚡ Force uv to use pre-compiled wheels and skip raw C-compilation
RUN uv sync --frozen --no-build

# Copy clean architecture layers
COPY . .

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
