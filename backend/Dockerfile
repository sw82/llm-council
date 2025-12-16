FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock .python-version ./

# Install dependencies
RUN uv sync --frozen --no-install-project

# Copy application code
COPY backend ./backend

# Create data directory
RUN mkdir -p data/conversations

# Run the application
# We use --host 0.0.0.0 to allow external access (including from other containers/host)
CMD ["uv", "run", "python", "-m", "backend.main"]
