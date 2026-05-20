from unittest.mock import patch, AsyncMock

import pytest

from mcp_ungm import search_ungm_notices


@pytest.mark.asyncio
async def test_search_ungm_notices_success_with_results():
    """Tests formatting when the scraper returns valid data rows."""
    mock_data = [
        ["Title A", "19-May-2026", "Yemen"],
        ["Title B", "22-May-2026", "Ukraine"]
    ]

    with patch('mcp_ungm.UNGMClient') as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.search_and_filter = AsyncMock(return_value=mock_data)

        result = await search_ungm_notices(title="Test")

        # Verify the formatting string
        assert "Found 2 notices:" in result
        assert "1. Title A | 19-May-2026 | Yemen" in result
        assert "2. Title B | 22-May-2026 | Ukraine" in result


@pytest.mark.asyncio
async def test_search_ungm_notices_empty():
    """Tests the fallback message when no notices are found."""
    with patch('mcp_ungm.UNGMClient') as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.search_and_filter = AsyncMock(return_value=[])

        result = await search_ungm_notices(title="NonExistent")

        assert "No procurement notices found" in result


@pytest.mark.asyncio
async def test_search_ungm_notices_exception():
    """Tests that scraping exceptions are safely caught and returned as readable strings."""
    with patch('mcp_ungm.UNGMClient') as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.search_and_filter = AsyncMock(side_effect=Exception("Playwright timeout error"))

        result = await search_ungm_notices()

        assert "An error occurred while scraping: Playwright timeout error" in result
