# Deployment

## Target

PlayMCP needs a public HTTP/HTTPS MCP endpoint.

```text
https://<deployed-host>/mcp
```

This project serves MCP over Streamable HTTP at `/mcp` and exposes `/health` for
platform health checks.

## Vercel

Vercel can be used as the public PlayMCP endpoint. This repository exposes a
top-level ASGI app as `main:app`, and `pyproject.toml` sets the Vercel entrypoint.

Expected endpoint after deployment:

```text
https://<project-name>.vercel.app/mcp
```

Health check:

```text
https://<project-name>.vercel.app/health
```

Deploy from the repository root:

```bash
npx vercel
```

Then use the production URL returned by Vercel in the PlayMCP Endpoint field:

```text
https://<production-domain>/mcp
```

Notes:

- Do not use `localhost` in PlayMCP.
- Vercel uses the Python ASGI runtime path here, not the Dockerfile.
- `vercel.json` sets `MCP_TRANSPORT=streamable-http`, `MCP_HTTP_PATH=/mcp`,
  and `MCP_STATELESS_HTTP=true` for Vercel.
- If PlayMCP cannot load tools from the Vercel URL, use a container/always-on
  host such as Cloud Run, Fly.io, Render, or Railway with the Dockerfile.

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

For Docker-based cloud deployment, set:

```text
MCP_TRANSPORT=streamable-http
FASTMCP_HOST=0.0.0.0
PORT=<platform provided port>
MCP_HTTP_PATH=/mcp
MCP_STATELESS_HTTP=true
```

If the platform does not provide `PORT`, the server defaults to `8000`.

## PlayMCP Form

After deployment, paste the public MCP endpoint:

```text
https://<deployed-host>/mcp
```

Do not use `localhost` in PlayMCP. PlayMCP must reach the server from the public
internet or from the contest-provided cloud network.
