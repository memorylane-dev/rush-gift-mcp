# Deployment

## Target

PlayMCP needs a public HTTP/HTTPS MCP endpoint.

```text
https://<deployed-host>/mcp
```

This project serves MCP over Streamable HTTP at `/mcp` and exposes `/health` for
platform health checks.

## Local HTTP Run

```bash
uv sync
MCP_TRANSPORT=streamable-http FASTMCP_HOST=127.0.0.1 PORT=8000 uv run python main.py
```

Check:

```bash
curl http://127.0.0.1:8000/health
```

## Docker Run

```bash
docker build -t rush-gift-mcp .
docker run --rm -p 8000:8000 rush-gift-mcp
```

Check:

```bash
curl http://127.0.0.1:8000/health
```

## Runtime Environment

For cloud deployment, set:

```text
MCP_TRANSPORT=streamable-http
FASTMCP_HOST=0.0.0.0
PORT=<platform provided port>
MCP_HTTP_PATH=/mcp
```

If the platform does not provide `PORT`, the server defaults to `8000`.

## PlayMCP Form

After deployment, paste the public MCP endpoint:

```text
https://<deployed-host>/mcp
```

Do not use `localhost` in PlayMCP. PlayMCP must reach the server from the public
internet or from the contest-provided cloud network.
