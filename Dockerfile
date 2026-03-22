# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy dependency files and source code
COPY pyproject.toml ./
COPY src/ ./src/

# Install the package and dependencies
RUN uv pip install --system .

# Install system dependencies for fly
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install flyctl
RUN curl -L https://fly.io/install.sh | sh
ENV PATH="/root/.fly/bin:${PATH}"

# Expose port 8080 for Fly.io
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Use fly mcp wrap to convert stdio MCP to SSE
CMD ["fly", "mcp", "wrap", "--", "python", "-m", "surfa_mcp.server"]
