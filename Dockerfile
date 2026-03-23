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

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=3001
ENV HOST=0.0.0.0

# Expose port 3001 for HTTP/SSE
EXPOSE 3001

# Run FastMCP in HTTP/SSE mode (Streamable HTTP compatible)
CMD ["python", "-m", "surfa_mcp.server"]
