import asyncio
import json
import random
from typing import AsyncGenerator, List, Optional
from puzzler import GeminiClient, Puzzler

from playwright.async_api import async_playwright, Browser, BrowserContext, Page


async def extract_image_urls_from_js(page: Page, max_results: Optional[int] = None) -> List[dict]:
    """Extract image URLs directly from the JavaScript data on the page."""
    # Execute JavaScript to extract the image data from the page
    result_data = await page.evaluate("""() => {
        // Try to find the JavaScript data structure with image information
        // This targets Google's specific data structure format
        const results = [];

        // Look for script tags or JavaScript variables that might contain image data
        try {
            // This is a bit of a hack, but we're looking for specific patterns in the JS data
            const scripts = Array.from(document.scripts);

            for (const script of scripts) {
                const text = script.text || '';

                // Look for patterns that indicate image data
                if (text.includes('https://') && text.includes('.jpg') || text.includes('.png') || text.includes('.jpeg')) {
                    // Extract URLs using regex
                    const matches = text.match(/(https:\\/\\/[^\\s"']+\\.(jpg|jpeg|png|gif)(\\?[^\\s"']+)?)/g);

                    if (matches) {
                        for (const url of matches) {
                            // Skip Google's thumbnail URLs
                            if (url.includes('encrypted-tbn0.gstatic.com')) continue;

                            // Try to find associated metadata
                            const metaIndex = text.indexOf(url);
                            const beforeUrl = text.substring(Math.max(0, metaIndex - 200), metaIndex);
                            const afterUrl = text.substring(metaIndex, Math.min(text.length, metaIndex + 200));

                            // Try to extract dimensions if available
                            let dimensions = null;
                            const dimensionsMatch = afterUrl.match(/(\\d+)\\s*[xX]\\s*(\\d+)/);
                            if (dimensionsMatch) {
                                dimensions = {
                                    width: parseInt(dimensionsMatch[2]),
                                    height: parseInt(dimensionsMatch[1])
                                };
                            }

                            // Try to extract source URL
                            let sourceUrl = null;
                            const sourceMatch = beforeUrl.match(/(https:\\/\\/[^\\s"']+)/g);
                            if (sourceMatch && sourceMatch.length > 0) {
                                const potentialSource = sourceMatch[sourceMatch.length - 1];
                                if (potentialSource.includes('http') && !potentialSource.includes('.jpg') &&
                                    !potentialSource.includes('.png') && !potentialSource.includes('.gif')) {
                                    sourceUrl = potentialSource;
                                }
                            }

                            results.push(url);
                        }
                    }
                }
            }
        } catch (e) {
            console.error('Error parsing JS data:', e);
        }

        // Remove duplicates
        const seen = new Set();
        return results.filter(item => {
            if (seen.has(item)) {
                return false;
            }
            seen.add(item);
            return true;
        });
    }""")

    if max_results:
        result_data = result_data[:max_results]

    return result_data

class GoogleImageSearch:
    def __init__(
        self,
        headless: bool = True,
        navigation_timeout: int = 30000,
        scroll_delay: float = 1.0,
        wait_after_click: float = 2.0,
        safe_search: bool = True,
        user_agent: Optional[str] = None,
        solver: Puzzler | None = None,
        cookies_file: str | None = None,
    ):
        """
        Initialize the Google Image Search class.

        Args:
            headless: Whether to run the browser in headless mode
            navigation_timeout: Maximum time to wait for page navigation in milliseconds
            scroll_delay: Time to wait between scrolls in seconds
            wait_after_click: Time to wait after clicking buttons in seconds
            safe_search: Whether to enable safe search
            user_agent: Custom user agent string to use
        """
        self.headless = headless
        self.navigation_timeout = navigation_timeout
        self.scroll_delay = scroll_delay
        self.wait_after_click = wait_after_click
        self.safe_search = safe_search
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        self.solver = solver
        self.cookies_file = cookies_file
        self.browser = None
        self.context = None

    async def __aenter__(self):
        """Initialize the browser when entering context."""
        await self._initialize_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the browser when exiting context."""
        await self._close_browser()

    async def _save_cookies(self) -> None:
        if not self.cookies_file:
            return
        cookies = await self.context.cookies()
        with open(self.cookies_file, "wt") as f:
            json.dump(cookies, f, indent=2)
        print(f"Cookies saved to {self.cookies_file}")

    async def _initialize_browser(self) -> None:
        """Initialize the browser if not already initialized."""
        if self.browser is None:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=self.headless, args=["--disable-gpu", "--no-sandbox"]
            )
            self.context = await self.browser.new_context(
                user_agent=self.user_agent,
                viewport={"width": 1920, "height": 1080},
            )
            if self.cookies_file:
                with open(self.cookies_file, "rt") as f:
                    cookies = json.load(f)
                    await self.context.add_cookies(cookies)
                    print(f"Cookies loaded from {self.cookies_file}")

            # Set navigation timeout
            self.context.set_default_navigation_timeout(self.navigation_timeout)

    async def _close_browser(self) -> None:
        """Close the browser if initialized."""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None

    async def _add_human_behavior(self, page: Page) -> None:
        """Add human-like behavior to avoid detection."""
        # Random mouse movements
        for _ in range(random.randint(2, 5)):
            await page.mouse.move(random.randint(100, 1000), random.randint(100, 500))
            await asyncio.sleep(random.uniform(0.1, 0.3))

        # Random pauses
        await asyncio.sleep(random.uniform(0.5, 1.5))

    async def _configure_safe_search(self, page: Page) -> None:
        """Configure safe search settings."""
        if not self.safe_search:
            await page.goto("https://www.google.com/preferences")
            await self._add_human_behavior(page)

            # Find and click the safe search option
            await page.click("div[data-name='SafeSearch'] > div > div")
            await asyncio.sleep(0.5)

            # Select "Don't filter explicit results"
            await page.click("div[data-value='0'] > div")
            await page.click("form[action='/save'] input[type='submit']")
            await page.wait_for_load_state("networkidle")

    async def _scroll_to_load_more(self, page: Page, max_scrolls: int = 10) -> None:
        """Scroll down to load more images."""
        prev_height = await page.evaluate("document.body.scrollHeight")

        for _ in range(max_scrolls):
            # Scroll down with human-like behavior
            await page.evaluate(f"window.scrollBy(0, {random.randint(500, 800)})")
            await asyncio.sleep(self.scroll_delay * random.uniform(0.8, 1.2))

            # Try to click "Show more results" button if it exists
            try:
                show_more_selector = "input[type='button'][value='Show more results']"
                if await page.is_visible(show_more_selector):
                    await page.click(show_more_selector)
                    await asyncio.sleep(self.wait_after_click)
            except Exception:
                pass

            # Check if we've reached the bottom
            curr_height = await page.evaluate("document.body.scrollHeight")
            if curr_height == prev_height:
                # Try once more after a pause
                await asyncio.sleep(1.0)
                curr_height = await page.evaluate("document.body.scrollHeight")
                if curr_height == prev_height:
                    break
            prev_height = curr_height

    async def search_by_query(
        self, query: str, max_results: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        Search for images using a text query.

        Args:
            query: The search query
            max_results: Maximum number of results to return (None for all available)

        Yields:
            URLs of images found on the search page
        """
        page = await self.context.new_page()

        try:
            # Configure safe search if needed
            await self._configure_safe_search(page)

            # Navigate to Google Images
            await page.goto("https://www.google.com/imghp")

            # Solve any challenges if needed
            challenge_results = await self.solver.solve(page)
            if not challenge_results.solved:
                print("Failed to solve challenge")
                return
            elif challenge_results.puzzles:
                await self._save_cookies()

            await self._add_human_behavior(page)

            # Enter search query
            await page.fill("textarea[name='q']", query)
            await page.press("textarea[name='q']", "Enter")
            await page.wait_for_load_state("networkidle")

            # Solve any challenges if needed
            challenge_results = await self.solver.solve(page)
            if not challenge_results.solved:
                print("Failed to solve challenge")
                return
            elif challenge_results.puzzles:
                await self._save_cookies()

            # Scroll to load more images
            await self._scroll_to_load_more(page)

            # Extract image URLs
            image_urls = await extract_image_urls_from_js(page, max_results)

            # Yield each URL
            for url in image_urls:
                yield url

        finally:
            await page.close()

    async def search_by_image(
        self, image_path_or_url: str, max_results: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        Search for similar images using an existing image.

        Args:
            image_path_or_url: Path to local image file or URL of an image
            max_results: Maximum number of results to return (None for all available)

        Yields:
            URLs of similar images found on the search page
        """
        page = await self.context.new_page()

        try:
            # Configure safe search if needed
            await self._configure_safe_search(page)

            # Navigate to Google Images
            await page.goto("https://www.google.com/imghp")
            await self._add_human_behavior(page)

            # Click on the camera icon
            await page.click("a[aria-label='Search by image']")
            await asyncio.sleep(self.wait_after_click)

            # Determine if we're uploading a local file or using a URL
            if image_path_or_url.startswith(("http://", "https://")):
                # Use URL
                await page.fill("input[name='image_url']", image_path_or_url)
                await page.click(
                    "form[action='/searchbyimage/upload'] button[type='submit']"
                )
            else:
                # Use local file
                input_file = await page.query_selector("input[type='file']")
                await input_file.set_input_files(image_path_or_url)
                await page.click(
                    "form[action='/searchbyimage/upload'] button[type='submit']"
                )

            await page.wait_for_load_state("networkidle")

            # Try to click on "Find visually similar images" if it exists
            try:
                similar_link = page.locator(
                    "a:has-text('Find visually similar images')"
                )
                if await similar_link.is_visible():
                    await similar_link.click()
                    await page.wait_for_load_state("networkidle")
            except Exception:
                pass

            # Scroll to load more images
            await self._scroll_to_load_more(page)

            # Extract image URLs
            image_urls = await self._extract_image_urls(page, max_results)

            # Yield each URL
            for url in image_urls:
                yield url

        finally:
            await page.close()


# Example usage
async def main():
    model = GeminiClient(
        max_retries=3,
        base_delay=0.5,
        max_total_time=15,
    )
    solver = Puzzler(
        model,
        rounds=40,
        sequences=12,
        screenshot_basepath=None,
        grid_4_score_3_threshold=5,
    )
    cookies_file = ".data/profiles/nicotrack-profiles/teen_mobile/cookies.json"
    # Use with context manager
    async with GoogleImageSearch(
        headless=False,
        scroll_delay=1.5,
        wait_after_click=2.0,
        safe_search=True,
        solver=solver,
        cookies_file=cookies_file,
    ) as search:
        print("Searching for 'cute cats'...")
        count = 0
        for query in ["cute cats", "big cats"]:
            async for url in search.search_by_query(query, max_results=5):
                print(f"Found image: {url}")
                count += 1
        print(f"Total results: {count}")

        # Search by image example
        image_path = "path/to/your/image.jpg"  # Replace with actual path
        # Uncomment to test:
        # print(f"Searching for similar images to {image_path}...")
        # count = 0
        # async for url in search.search_by_image(image_path, max_results=5):
        #     print(f"Found similar image: {url}")
        #     count += 1
        # print(f"Total results: {count}")


if __name__ == "__main__":
    asyncio.run(main())
