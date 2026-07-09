FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

ENV MCP_TRANSPORT=streamable-http \
    FASTMCP_HOST=0.0.0.0 \
    MCP_HTTP_PATH=/mcp \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY data ./data
COPY rush_gift ./rush_gift
COPY main.py ./

EXPOSE 8000

CMD ["uv", "run", "--frozen", "--no-dev", "python", "main.py"]
