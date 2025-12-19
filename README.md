# Retell MCP Server

A lightweight [FastMCP](https://github.com/modelcontextprotocol/fastmcp) server that exposes common Retell SDK operations (voice management, Hungarian salon agent provisioning, phone number lifecycle, batch calls, transcript retrieval/export) over an MCP-compatible HTTP interface. The server is stateless for HTTP clients and supports streaming responses where available.

## Features
- **Voice listing:** enumerate available voices from the Retell SDK.
- **Hungarian salon agent creation:** validate Hungarian prompts, create the agent through the SDK, and persist metadata in SQLite.
- **Phone number lifecycle:** create or import numbers, then bind them to agents.
- **Batch call launch:** trigger outbound campaigns against multiple targets.
- **Transcript handling:** retrieve transcripts, store them locally, and export them to external destinations.

## Getting Started

### Prerequisites
- Python 3.11+
- A Retell API key with permissions for voice, agent, phone number, batch call, and transcript APIs.
- Optional: [ngrok](https://ngrok.com/) if you need to expose the MCP server publicly.

### Installation
1. Clone this repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration
Set environment variables with the `RETELL_` prefix (or place them in a local `.env` file):

- `RETELL_API_KEY` (required): Retell API key.
- `RETELL_BASE_URL` (optional): Override the default Retell API endpoint.
- `RETELL_DATABASE_PATH` (optional): SQLite file path (defaults to `retell_mcp.sqlite3`).

### Running the Server Locally
Start the FastMCP server (stateless HTTP with streaming enabled):

```bash
python server.py
```

By default FastMCP binds to `http://127.0.0.1:8000`. Consult FastMCP logs for the final URL if you override host/port via environment variables that FastMCP respects.

### Exposing the Server Publicly (ngrok)
If your MCP client needs to reach the server from outside your machine:

1. Start the server locally (as above).
2. In another terminal, run ngrok to forward the FastMCP port (default `8000`):
   ```bash
   ngrok http 8000
   ```
3. Use the generated HTTPS forwarding URL as the endpoint for your MCP connector.

### MCP Connector URL
FastMCP exposes an `.well-known/ai-plugin.json`-style descriptor that MCP clients can consume. Point your MCP-compatible tool to the public or local base URL (e.g., `http://127.0.0.1:8000/` or the ngrok HTTPS URL) to register the connector. The server is stateless for HTTP clients and supports HTTP streaming responses where supported by FastMCP.

### Data Persistence
Agent and transcript metadata are stored in SQLite under the configured database path. Agent records keep the validated Hungarian prompt, voice selection, and optional bound phone number. Transcript records capture the transcript text and collection timestamp.

### Security Notes
- Keep your `RETELL_API_KEY` secret; never commit it to source control.
- Prefer HTTPS (via ngrok or another tunnel) when exposing the server publicly.
- SQLite files contain prompts and transcripts; secure them with filesystem permissions and avoid exposing them over shared volumes.
- Review FastMCP access controls before exposing the server broadly. Consider IP allowlists or reverse proxies when deploying outside a trusted network.

## Project Structure
- `server.py` – FastMCP entrypoint with tools for voice, agent, number, batch call, and transcript actions.
- `retell_client.py` – Retell SDK wrapper with retry logic.
- `schemas.py` – Pydantic request/response models with validation (including Hungarian prompt checks).
- `storage.py` – SQLite schema helpers for agents and transcripts.
- `config.py` – Environment-driven settings loader.
- `requirements.txt` – Python dependencies.

## Development Notes
- The MCP server is stateless for HTTP clients; all durable data is in SQLite.
- Tools may raise SDK exceptions surfaced through tenacity retries. Check server logs for details if a request fails.
- Extend `schemas.py` and `storage.py` if you need additional Retell capabilities or richer persistence.
