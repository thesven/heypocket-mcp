# heypocket-mcp

Python MCP server for the HeyPocket public API.

## Scope

This server wraps the currently documented HeyPocket public API:

- Search recordings
- List recordings
- Get a recording by ID
- Get a recording audio URL
- Create a recording upload URL
- List tags

It supports both local `stdio` mode and hosted Streamable HTTP mode.

## Installation

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

## Configuration

Required environment variables:

- `HEYPOCKET_API_KEY`

Optional environment variables:

- `HEYPOCKET_BASE_URL` default `https://public.heypocketai.com`
- `HEYPOCKET_TIMEOUT_SECONDS` default `30`
- `HEYPOCKET_LOG_LEVEL` default `INFO`
- `HEYPOCKET_USER_AGENT_SUFFIX`

## Usage

### stdio

```bash
HEYPOCKET_API_KEY=your-key heypocket-mcp stdio
```

### HTTP

```bash
HEYPOCKET_API_KEY=your-key heypocket-mcp http --host 127.0.0.1 --port 8000 --path /mcp
```

## Tools

- `heypocket_search_recordings`
- `heypocket_list_recordings`
- `heypocket_get_recording`
- `heypocket_get_recording_audio_url`
- `heypocket_create_recording_upload_url`
- `heypocket_list_tags`

Each tool returns a structured object:

```json
{
  "ok": true,
  "data": {},
  "error": null
}
```

## Example MCP client config

### Local stdio

```json
{
  "mcpServers": {
    "heypocket": {
      "command": "heypocket-mcp",
      "args": ["stdio"],
      "env": {
        "HEYPOCKET_API_KEY": "your-key"
      }
    }
  }
}
```

### Hosted HTTP

```json
{
  "mcpServers": {
    "heypocket": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

## Development

```bash
pytest
ruff check .
mypy
```

## Limitations

- API key authentication only
- No webhook receiver in v1
- Only documented public API endpoints are wrapped
