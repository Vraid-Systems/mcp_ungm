from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from client_ungm import UNGMClient


# --- Custom Mock to Handle Playwright's Chained API ---
class MockLocator(MagicMock):
    """Mimics Playwright's locator chaining synchronously, while keeping actions async."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Actions must be AsyncMocks because we 'await' them in the client
        self.fill = AsyncMock()
        self.click = AsyncMock()
        self.inner_text = AsyncMock()
        self.press = AsyncMock()

        # .first needs to expose the same async actions
        self.first = MagicMock()
        self.first.fill = AsyncMock()
        self.first.click = AsyncMock()

        self.mock_elements = []

    def locator(self, *args, **kwargs):
        # Synchronously return self to support chaining: page.locator().locator()
        return self

    async def all(self):
        return self.mock_elements


@pytest.fixture
def mock_playwright_context():
    """Fixture to mock the async_playwright context manager and browser."""
    mock_cm = AsyncMock()
    mock_p = AsyncMock()
    mock_browser = AsyncMock()
    mock_page = AsyncMock()

    # CRITICAL FIX: Playwright's page.locator() is a synchronous method!
    # We must override it with a MagicMock so it returns our MockLocator 
    # instantly, rather than returning an awaitable coroutine.
    mock_page.locator = MagicMock()

    mock_cm.__aenter__.return_value = mock_p
    mock_p.chromium.launch.return_value = mock_browser
    mock_browser.new_page.return_value = mock_page

    return mock_cm, mock_page


@pytest.mark.asyncio
async def test_search_and_filter_all_populated_branches(mock_playwright_context):
    """Tests the primary branches: lists converted from strings, lists iterating, valid rows."""
    mock_cm, mock_page = mock_playwright_context

    def page_locator_side_effect(selector):
        loc = MockLocator()
        if "Deadline between" in selector:
            # Mock the two date inputs
            loc.mock_elements = [MockLocator(), MockLocator()]
        elif selector == ".tableRow.dataRow":
            # Mock row conditions: Valid, Empty, Digits-only, Single-column
            row1, row2, row3, row4 = MockLocator(), MockLocator(), MockLocator(), MockLocator()
            row1.inner_text.return_value = "Solar Panel \n 19-May"
            row2.inner_text.return_value = "   "  # Empty content branch
            row3.inner_text.return_value = "12 \n 34 \n 56"  # isdigit() branch
            row4.inner_text.return_value = "OnlyOneColumn"  # len <= 1 branch
            loc.mock_elements = [row1, row2, row3, row4]
        return loc

    mock_page.locator.side_effect = page_locator_side_effect

    # Force the exception branch when waiting for the loader to disappear
    mock_page.wait_for_selector.side_effect = Exception("Timeout exception")

    with patch('client_ungm.async_playwright', return_value=mock_cm):
        client = UNGMClient(headless=True)
        results = await client.search_and_filter(
            title="Solar",
            countries="Yemen",  # Test string -> list conversion branch
            deadline_from="19-May-2026",
            deadline_to="20-May-2026",
            opportunity_types=["Request for quotation", "Invitation to bid"]  # Test list loop branch
        )

        # Only row1 should make it through our strict validation filters
        assert len(results) == 1
        assert results[0] == ["Solar Panel", "19-May"]


@pytest.mark.asyncio
async def test_search_and_filter_alternate_branches(mock_playwright_context):
    """Tests alternate branches: lists for countries, string for opportunity types, partial dates."""
    mock_cm, mock_page = mock_playwright_context

    def page_locator_side_effect(selector):
        loc = MockLocator()
        if "Deadline between" in selector:
            # Simulate a scenario where only 1 date input is found in the DOM
            loc.mock_elements = [MockLocator()]
        elif selector == ".tableRow.dataRow":
            loc.mock_elements = []  # No rows found
        return loc

    mock_page.locator.side_effect = page_locator_side_effect

    # Test the SUCCESSFUL try/except branch for the loader (no exception raised)
    mock_page.wait_for_selector.return_value = None

    with patch('client_ungm.async_playwright', return_value=mock_cm):
        client = UNGMClient()
        results = await client.search_and_filter(
            countries=["Yemen", "Ukraine"],  # Test list loop branch
            deadline_from="19-May-2026",  # Only 'from', and only 1 input mocked
            opportunity_types="Request for quotation"  # Test string -> list conversion
        )

        assert results == []


@pytest.mark.asyncio
async def test_search_and_filter_empty_parameters(mock_playwright_context):
    """Tests that the script safely bypasses all parameter branches if None are provided."""
    mock_cm, mock_page = mock_playwright_context

    # FIX: Ensure page.locator defaults to our custom MockLocator
    # so that .first.click() is an awaitable AsyncMock!
    mock_page.locator.return_value = MockLocator()

    # Safely bypass the loader check
    mock_page.wait_for_selector.return_value = None

    with patch('client_ungm.async_playwright', return_value=mock_cm):
        client = UNGMClient(headless=True)
        results = await client.search_and_filter()  # No kwargs

        assert results == []
