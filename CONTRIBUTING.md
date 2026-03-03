# Contributing to Surfa MCP

Thanks for your interest in contributing! 🎉

## Development Setup

```bash
# Clone the repo
git clone https://github.com/gamladz/surfa-mcp.git
cd surfa-mcp

# Create virtual environment
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
uv pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Edit .env with your Surfa API key
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_tools.py::test_get_analytics_success -v

# Run with coverage
pytest tests/ --cov=surfa_mcp
```

## Code Style

We use:
- **Black** for formatting
- **Ruff** for linting

```bash
# Format code
black src/

# Lint code
ruff check src/
```

## Adding a New Tool

1. Create `src/surfa_mcp/tools/your_tool.py`
2. Implement the tool function and Tool definition
3. Add to `src/surfa_mcp/tools/__init__.py`
4. Register in `src/surfa_mcp/server.py`
5. Add tests in `tests/test_tools.py`
6. Update README with examples

## Submitting Changes

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Questions?

Open an issue or reach out to support@surfa.dev
