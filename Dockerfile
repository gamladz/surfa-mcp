# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy dependency files and source code
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install the exact versions in uv.lock (never resolve fresh at build time:
# an unpinned build pulls new major versions of fastmcp/mcp), then the package
RUN uv export --frozen --no-dev --no-emit-project -o requirements.txt \
    && uv pip install --system -r requirements.txt \
    && uv pip install --system --no-deps .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=3001
ENV HOST=0.0.0.0

# Expose port 3001 for HTTP/SSE
EXPOSE 3001

# Run FastMCP in HTTP/SSE mode (Streamable HTTP compatible)
CMD ["python", "-m", "surfa_mcp.server"]
