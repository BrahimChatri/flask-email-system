FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_CACHE_DIR=/home/appuser/.cache/uv

# Create and set the working directory
WORKDIR /app

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (Python package/dependency manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv \
    && mv /root/.local/bin/uvx /usr/local/bin/uvx

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install Python dependencies
RUN uv sync && uv pip install gunicorn

# Make sure venv executables are on PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy the backend application code
COPY . .

# Copy entrypoint script and make it executable
COPY ./entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create necessary directories and fix permissions
RUN mkdir -p /app/staticfiles /app/media /home/appuser/.cache/uv \
    && chown -R appuser:appuser /app /home/appuser

# Switch to non-root user
USER appuser

# Expose the port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
