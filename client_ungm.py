from playwright.sync_api import sync_playwright


class UNGMClient:
    def __init__(self, headless=True):
        self.base_url = "https://www.ungm.org/Public/Notice"
        self.headless = headless

    def search_and_filter(self, title=None, countries=None, deadline_from=None, deadline_to=None,
                          opportunity_types=None):
        scraped_notices = []

        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()

            print(f"Navigating to {self.base_url}...")
            page.goto(self.base_url)

            # Wait for the network/page to fully load
            page.wait_for_load_state("networkidle")

            # 1. TITLE FILTER
            if title:
                print(f"Setting Title to: {title}")
                page.locator("input[id*='Title'], input[placeholder='Title']").first.fill(title)

            # 2. MULTIPLE COUNTRIES FILTER
            if countries:
                # Normalize string to a list if the user accidentally passes a single string
                if isinstance(countries, str):
                    countries = [countries]

                print(f"Setting Countries to: {', '.join(countries)}")
                for country in countries:
                    # Click the dropdown box to activate it for each country
                    page.locator("text='Beneficiary country or territory'").locator("..").locator(
                        "input, .select2-search__field").first.click()
                    # Type the country name to filter the list
                    page.keyboard.type(country, delay=100)
                    page.keyboard.press("Enter")
                    # Give it a tiny fraction of a second to register the tag before doing the next one
                    page.wait_for_timeout(200)

            # 3. DEADLINE BETWEEN / AND (DATES)
            # Dates should ideally be passed in as standard strings (e.g., '2026-06-01' or '01-Jun-2026')
            if deadline_from or deadline_to:
                print("Setting Deadline dates...")
                # The UNGM site has two adjacent date inputs for the deadline
                deadline_container = page.locator("text='Deadline between'").locator("..")
                date_inputs = deadline_container.locator("input[type='text'], input[type='date']").all()

                if deadline_from and len(date_inputs) >= 1:
                    date_inputs[0].fill(deadline_from)
                    date_inputs[0].press("Enter")

                if deadline_to and len(date_inputs) >= 2:
                    date_inputs[1].fill(deadline_to)
                    date_inputs[1].press("Enter")

            # 4. MULTIPLE OPPORTUNITY TYPES FILTER
            if opportunity_types:
                # Normalize string to a list if the user accidentally passes a single string
                if isinstance(opportunity_types, str):
                    opportunity_types = [opportunity_types]

                print(f"Setting Types of Opportunity to: {', '.join(opportunity_types)}")
                for opp_type in opportunity_types:
                    page.locator("text='Type of opportunity'").locator("..").locator(
                        "input, .select2-search__field").first.click()
                    page.keyboard.type(opp_type, delay=100)
                    page.keyboard.press("Enter")
                    # Brief pause to allow the UI to register the tag
                    page.wait_for_timeout(200)

            # CLICK SEARCH
            print("Applying filters and waiting for results...")
            page.locator("button:has-text('Search'), input[type='button'][value='Search']").first.click()

            # Wait for the UNGM "processing request" loader to appear, then disappear
            try:
                page.wait_for_selector("text=We are processing your request", state="visible", timeout=3000)
                page.wait_for_selector("text=We are processing your request", state="hidden", timeout=15000)
            except Exception:
                # If the loader is too fast or doesn't appear, fallback to a manual wait
                page.wait_for_timeout(3000)

            print("Extracting results...")

            # The result set usually sits in a specific CSS grid or table row format
            rows = page.locator(".table-row, table tbody tr").all()

            for row in rows:
                text_content = row.inner_text().strip()
                if text_content:
                    # Clean up the row text and split into usable columns
                    columns = [col.strip() for col in text_content.split('\n') if col.strip()]
                    scraped_notices.append(columns)

            browser.close()

        return scraped_notices
