from playwright.async_api import async_playwright


class UNGMClient:
    def __init__(self, headless=True):
        self.base_url = "https://www.ungm.org/Public/Notice"
        self.headless = headless

    async def search_and_filter(self, title=None, countries=None, deadline_from=None, deadline_to=None,
                                opportunity_types=None):
        scraped_notices = []

        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()

            print(f"Navigating to {self.base_url}...")
            await page.goto(self.base_url)

            # Wait for the network/page to fully load
            await page.wait_for_load_state("networkidle")

            # 1. TITLE FILTER
            if title:
                print(f"Setting Title to: {title}")
                await page.locator("input[id*='Title'], input[placeholder='Title']").first.fill(title)

            # 2. MULTIPLE COUNTRIES FILTER
            if countries:
                # Normalize string to a list if the user accidentally passes a single string
                if isinstance(countries, str):
                    countries = [countries]

                print(f"Setting Countries to: {', '.join(countries)}")
                for country in countries:
                    # Click the dropdown box to activate it for each country
                    await page.locator("text='Beneficiary country or territory'").locator("..").locator(
                        "input, .select2-search__field").first.click()
                    # Type the country name to filter the list
                    await page.keyboard.type(country, delay=100)
                    await page.keyboard.press("Enter")
                    # Give it a tiny fraction of a second to register the tag before doing the next one
                    await page.wait_for_timeout(200)

            # 3. DEADLINE BETWEEN / AND (DATES)
            if deadline_from or deadline_to:
                print("Setting Deadline dates...")
                # The UNGM site has two adjacent date inputs for the deadline
                deadline_container = page.locator("text='Deadline between'").locator("..")
                date_inputs = await deadline_container.locator("input[type='text'], input[type='date']").all()

                if deadline_from and len(date_inputs) >= 1:
                    await date_inputs[0].fill(deadline_from)
                    await date_inputs[0].press("Enter")

                if deadline_to and len(date_inputs) >= 2:
                    await date_inputs[1].fill(deadline_to)
                    await date_inputs[1].press("Enter")

            # 4. MULTIPLE OPPORTUNITY TYPES FILTER
            if opportunity_types:
                # Normalize string to a list if the user accidentally passes a single string
                if isinstance(opportunity_types, str):
                    opportunity_types = [opportunity_types]

                print(f"Setting Types of Opportunity to: {', '.join(opportunity_types)}")
                for opp_type in opportunity_types:
                    await page.locator("text='Type of opportunity'").locator("..").locator(
                        "input, .select2-search__field").first.click()
                    await page.keyboard.type(opp_type, delay=100)
                    await page.keyboard.press("Enter")
                    # Brief pause to allow the UI to register the tag
                    await page.wait_for_timeout(200)

            # CLICK SEARCH
            print("Applying filters and waiting for results...")
            await page.locator("button:has-text('Search'), input[type='button'][value='Search']").first.click()

            # Wait for the UNGM "processing request" loader to appear, then disappear
            try:
                await page.wait_for_selector("text=We are processing your request", state="visible", timeout=3000)
                await page.wait_for_selector("text=We are processing your request", state="hidden", timeout=15000)
            except Exception:
                # If the loader is too fast or doesn't appear, fallback to a manual wait
                await page.wait_for_timeout(3000)

            # 1. ADD A HARD WAIT FOR RENDERING
            print("Waiting for DOM to paint results...")
            await page.wait_for_timeout(2000)

            print("Extracting results...")

            # 1. Target the specific camelCase classes used for the result rows
            rows = await page.locator(".tableRow.dataRow").all()

            for row in rows:
                text_content = await row.inner_text()
                text_content = text_content.strip()

                if text_content:
                    # 2. SAFEGUARD: If the entire row is just numbers (like a calendar week), skip it
                    if text_content.replace('\n', '').replace(' ', '').isdigit():
                        continue

                    # Clean up the row text and split into usable columns
                    columns = [col.strip() for col in text_content.split('\n') if col.strip()]

                    if len(columns) > 1:
                        scraped_notices.append(columns)

            await browser.close()

        return scraped_notices
