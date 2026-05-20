# UNGM MCP Server
A local Python Model Context Protocol (MCP) server for querying the United Nations Global Marketplace (UNGM) Notice Search via playwright.
This server enables LLMs (like Claude Desktop and Gemini CLI) to dynamically search for UNGM notices filtering by keywords, regions, and publication dates.

## Features
- **Notice Search Tool**: Allows LLMs to search UNGM parameters (`title`, `countries`, `deadline_from`, `deadline_to`, `opportunity_types`).
- **Headless MCP Integration**: Provides a `mcp.server.fastmcp` implementation seamlessly connecting your workflow tools.

## Installation

### Prerequisites
- Python 3.10+

### Setup

```bash
# Clone or download this project
git clone <repository_url>
cd mcp_ungm

# Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -Ur requirements.txt

playwright install chromium
```

## Usage with MCP Clients
```json
{
  "mcpServers": {
    "mcp_ungm": {
      "command": "/path/to/this/repo/.venv/bin/python",
      "args": [
        "/path/to/this/repo/mcp_ungm.py"
      ]
    }
  }
}
```
