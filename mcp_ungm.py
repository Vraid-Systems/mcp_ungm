import os
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("UNGM Notice Search")

# Constants for UNGM API configuration
# Modify these base URLs if the official UNGM Developer portal uses different paths
UNGM_API_BASE_URL = os.environ.get("UNGM_API_BASE_URL", "https://www.ungm.org/Public/Notice/Search")
UNGM_AUTH_URL = os.environ.get("UNGM_AUTH_URL", "https://www.ungm.org/STS/connect/token")


class UNGMClient:
    def __init__(self):
        # We support direct Bearer token passing, which is ideal for MCP
        # Or standard Client Credentials / Authorization Code Grant if implemented.
        self.client_id = os.environ.get("UNGM_CLIENT_ID")
        self.client_secret = os.environ.get("UNGM_CLIENT_SECRET")
        self.bearer_token = os.environ.get("UNGM_BEARER_TOKEN")
        self.token = None

    async def _get_access_token(self) -> str:
        """
        Retrieves a Bearer token.
        If a static UNGM_BEARER_TOKEN is provided, uses that.
        Otherwise, attempts to fetch one using UNGM_CLIENT_ID and UNGM_CLIENT_SECRET.
        """
        if self.bearer_token:
            return self.bearer_token

        if self.token:
            return self.token

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Authentication credentials missing. Provide UNGM_BEARER_TOKEN or UNGM_CLIENT_ID + UNGM_CLIENT_SECRET.")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                UNGM_AUTH_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    # We default to client credentials as it is headless/machine-to-machine.
                    # Standard user-facing AuthorizationCodeGrant is not headless friendly for MCP unless pre-authenticated
                    "grant_type": "client_credentials",
                    "scope": "ungm_api"
                }
            )
            response.raise_for_status()
            data = response.json()
            self.token = data.get("access_token")
            return self.token

    async def search_notices(
            self,
            keywords: Optional[str] = None,
            regions: Optional[str] = None,
            date_from: Optional[str] = None,
            date_to: Optional[str] = None
    ) -> str:
        """Searches UNGM notices using provided filters."""
        token = await self._get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        # Structure the query parameters for UNGM SearchNotices Request
        # Parameters align with standard UNGM Search filters
        params = {}
        if keywords:
            params["title"] = keywords
        if regions:
            params["regions"] = regions
        if date_from:
            params["publishedFrom"] = date_from
        if date_to:
            params["publishedTo"] = date_to

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    # Adjust this to the official developer.ungm.org REST API path
                    f"{UNGM_API_BASE_URL}",
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                return str(response.json())
            except Exception as e:
                return f"UNGM API Request Failed: {str(e)} - Attempted to call {response.url if 'response' in locals() else 'API'}"


ungm_client = None


@mcp.tool()
async def search_ungm_notices(
        keywords: str = "",
        regions: str = "",
        date_from: str = "",
        date_to: str = ""
) -> str:
    """
    Search for United Nations Global Marketplace (UNGM) notices based on keywords, regions, and dates.

    Args:
        keywords: Search term or keyword within the notice title or description (e.g., 'vehicles', 'IT services')
        regions: Region filter to restrict notices geographically (e.g., 'Africa', 'Europe')
        date_from: Start date for publication range (YYYY-MM-DD or ISO 8601)
        date_to: End date for publication range (YYYY-MM-DD or ISO 8601)
    """
    global ungm_client
    if not ungm_client:
        ungm_client = UNGMClient()

    try:
        results = await ungm_client.search_notices(
            keywords=keywords if keywords else None,
            regions=regions if regions else None,
            date_from=date_from if date_from else None,
            date_to=date_to if date_to else None
        )
        return results
    except Exception as e:
        return f"Error executing UNGM Notice Search: {str(e)}"


if __name__ == "__main__":
    mcp.run()
