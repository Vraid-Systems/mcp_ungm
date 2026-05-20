from typing import List, Optional

from mcp.server.fastmcp import FastMCP

from client_ungm import UNGMClient

mcp = FastMCP("UNGM Notice Search")


@mcp.tool()
def search_ungm_notices(
        title: Optional[str] = None,
        countries: Optional[List[str]] = None,
        deadline_from: Optional[str] = None,
        deadline_to: Optional[str] = None,
        opportunity_types: Optional[List[str]] = None
) -> str:
    """
    Search the United Nations Global Marketplace (UNGM) for procurement notices.

    Args:
        title: Keyword to search in the notice title.
        countries: List of country names to filter by (e.g. ["Yemen", "Ukraine"]).
        deadline_from: Start date for the deadline filter (format DD-MMM-YYYY, e.g. "19-May-2026").
        deadline_to: End date for the deadline filter (format DD-MMM-YYYY).
        opportunity_types: List of types (e.g. ["Request for quotation", "Invitation to bid", "Request for proposal"]).
    """
    client = UNGMClient(headless=True)

    try:
        results = client.search_and_filter(
            title=title,
            countries=countries,
            deadline_from=deadline_from,
            deadline_to=deadline_to,
            opportunity_types=opportunity_types
        )

        if not results:
            return "No procurement notices found matching those criteria."

        output = [f"Found {len(results)} notices:"]
        for idx, row in enumerate(results, 1):
            output.append(f"{idx}. {' | '.join(row)}")

        return "\n".join(output)

    except Exception as e:
        return f"An error occurred while scraping: {str(e)}"


if __name__ == "__main__":
    mcp.run()
