# UNGM MCP Server
A local Python Model Context Protocol (MCP) server for querying the United Nations Global Marketplace (UNGM) Notice Search API.
This server enables LLMs (like Claude Desktop and Gemini CLI) to dynamically search for UNGM notices filtering by keywords, regions, and publication dates.

## Features
- **Notice Search Tool**: Allows LLMs to search UNGM parameters (`keywords`, `regions`, `date_from`, `date_to`).
- **Authorization Support**: Allows authenticating to the UNGM APIs leveraging environment variables (`UNGM_BEARER_TOKEN` or `UNGM_CLIENT_ID` / `UNGM_CLIENT_SECRET`).
- **Headless MCP Integration**: Provides a `mcp.server.fastmcp` implementation seamlessly connecting your workflow tools.

## Installation

### Prerequisites

- Python 3.10+
- The `uv` package manager (recommended) or standard `pip`.

### Setup

```bash
# Clone or download this project
git clone <repository_url>
cd mcp_ungm

# Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -Ur requirements.txt
```

## Configuration

The server supports the standard Authorization Code grant / Client Credentials approaches via environment variables.
The easiest way to get things working is extracting a valid Bearer token from the developer portal or providing your OAuth Client ID / Secret.

Set the following Environment variables depending on your authentication path:

**Option 1: Pre-Generated Bearer Token (Easiest)**
- `UNGM_BEARER_TOKEN` - The Authorization Bearer token to connect to UNGM.

**Option 2: OAuth Client Credentials**
- `UNGM_CLIENT_ID` - Application Client ID generated in Developer UNGM
- `UNGM_CLIENT_SECRET` - Application Client Secret generated in Developer UNGM

*(Optional Configs)*
- `UNGM_API_BASE_URL` - Overrides the API Base string. (Defaults to `https://www.ungm.org/Public/Notice/Search`)
- `UNGM_AUTH_URL` - Overrides Token endpoint string. (Defaults to `https://www.ungm.org/STS/connect/token`)

## Usage with MCP Clients

### 1. Claude Desktop

To use this with Claude Desktop, you must configure the `mcpServers` object in Claude's configuration file.

**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Append the following configuration (replace `/path/to/server` with the absolute path):

```json
{
  "mcpServers": {
    "mcp_ungm": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "mcp",
        "--with",
        "httpx",
        "mcp-run",
        "/path/to/this/repo/mcp_ungm.py"
      ],
      "env": {
        "UNGM_BEARER_TOKEN": "YOUR_BEARER_TOKEN"
      }
    }
  }
}
```
*Note: If you are not using `uv`, replace `"command": "uv"` with your absolute path to the `.venv/bin/python` executable and `"args": ["/path/to/this/repo/mcp_ungm.py"]`.*

### 2. Gemini CLI or Other Node.js MCP Clients

Any client that conforms to MCP can connect to this standard python streams implementation using the `npx @modelcontextprotocol/inspector` test interface, or native integrations.

Example with MCP Inspector:
```bash
# Ensure you are within the project directory
export UNGM_BEARER_TOKEN="your_token_here"
npx @modelcontextprotocol/inspector uv run mcp_ungm.py
```
