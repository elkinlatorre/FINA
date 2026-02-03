# Node B: mcp-data-server (Remote Data Vault)

This MCP server acts as a remote "Data Vault", simulating an independent external system. It exposes financial portfolio information via the Model Context Protocol (MCP) using SSE transport.

## Requirements

- Python 3.12+
- Dependencies listed in `requirements.txt`

## Local Installation and Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   python main.py
   ```
   The server will be available at `http://localhost:8001`.

## Usage with Docker

1. Build the image:
   ```bash
   docker build -t mcp-data-server .
   ```

2. Run the container:
   ```bash
   docker run -p 8001:8001 mcp-data-server
   ```

## Exposed Tools

- `fetch_portfolio(user_id: string)`: Retrieves the financial portfolio for a user (e.g., `user123`).

## Architecture

- **Framework**: Starlette (Asgi)
- **Database**: SQLite (via `aiosqlite`)
- **Protocol**: MCP (Model Context Protocol)
- **Transport**: SSE (Server-Sent Events)
