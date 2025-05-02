import asyncio
import datetime
import json
import os
import random
import re
from typing import AsyncGenerator, Any
import typer
from playwright.async_api import async_playwright, Page
from puzzler import GeminiClient, Puzzler


async def take_screenshot(page: Page, basepath: str, step_name: str) -> None:
    if not basepath:
        return
    os.makedirs(basepath, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{step_name}_{timestamp}.png"
    filepath = os.path.join(basepath, filename)
    await page.screenshot(path=filepath)
    print(f"Screenshot saved: {filepath}")


async def extract_image_urls_from_js(
    page: Page, max_results: int | None = None
) -> list[str]:
    """Extract image URLs directly from the JavaScript data on the page."""
    # Execute JavaScript to extract the image data from the page
    urls = await page.evaluate(
        """() => {
        const results = [];
        try {
            const scripts = Array.from(document.scripts);
            for (const script of scripts) {
                const text = script.text || '';
                const matches = text.match(/(https?:\\/\\/[^\\s"']+\\.(jpg|jpeg|png|webp)(\\?[^\\s"']+)?)/g);
                if (!matches) continue;
                for (const url of matches) {
                    // Skip Google's thumbnail URLs
                    if (url.includes('encrypted-tbn0.gstatic.com')) continue;
                    results.push(url);
                }
            }
        } catch (e) {
            console.error('Error parsing JS data:', e);
        }
        return results;
    }"""
    )
    urls = list(set(urls))
    urls = urls[:max_results]
    return urls


class GoogleImageSearch:
    def __init__(
        self,
        headless: bool = True,
        navigation_timeout: int = 30000,
        scroll_delay: float = 1.0,
        wait_after_click: float = 2.0,
        safe_search: bool = True,
        user_agent: str | None = None,
        solver: Puzzler | None = None,
        cookies_file: str | None = None,
        debug_basepath: str | None = None,
        preferences_url: str | None = None,
    ):
        """
        Initialize the Google Image Search class.

        Args:
            headless: Whether to run the browser in headless mode
            navigation_timeout: Maximum time to wait for page navigation in milliseconds
            scroll_delay: Time to wait between scrolls in seconds
            wait_after_click: Time to wait after clicking buttons in seconds
            safe_search: SafeSearch setting: "on" (filtering), "off" (no filtering), or "images" (blur explicit)
            user_agent: Custom user agent string to use
            solver: Puzzler instance for solving captchas
            cookies_file: Path to file for saving/loading cookies
            debug_basepath: Base path for debug screenshots, if None no screenshots are taken
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
        self.debug_basepath = debug_basepath
        self.preferences_url = preferences_url or "https://www.google.com/safesearch"
        self.browser = None
        self.context = None
        self.settings_page = None

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
            print(f"Creating browser: headless={self.headless}")
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=["--disable-gpu", "--no-sandbox"],
            )
            self.context = await self.browser.new_context(
                user_agent=self.user_agent,
                viewport={"width": 1920, "height": 1080},
                ignore_https_errors=True,
            )
            if self.cookies_file:
                try:
                    with open(self.cookies_file, "rt") as f:
                        cookies = json.load(f)
                        await self.context.add_cookies(cookies)
                        print(f"Cookies loaded from {self.cookies_file}")
                except (FileNotFoundError, json.JSONDecodeError):
                    print(f"No valid cookies file found at {self.cookies_file}")
            self.context.set_default_navigation_timeout(self.navigation_timeout)
            self.settings_page = await self.context.new_page()
            await self._configure_safe_search(self.settings_page)

    async def _close_browser(self) -> None:
        """Close the browser if initialized."""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None

    async def _configure_safe_search(self, page: Page) -> None:
        # Navigate to Google preferences
        print(f"Configuring safe search to: {self.safe_search}")
        await page.goto(self.preferences_url)
        await take_screenshot(page, self.debug_basepath, "safe_search_start")
        # Click on the correct radio button
        # 0 = Filter
        # 1 = Blur
        # 2 = Off
        data_index = 0 if self.safe_search else 2
        selector = (
            f'g-radio-button-group div[jsname="GCYh9b"][data-index="{data_index}"]'
        )
        await page.wait_for_selector(
            selector, state="visible", timeout=self.navigation_timeout
        )
        await page.click(selector)
        await asyncio.sleep(self.wait_after_click)
        await take_screenshot(page, self.debug_basepath, "safe_search_configured")

    async def _scroll_to_load_more(
        self, page: Page, max_results: int, max_scrolls: int = 10
    ) -> set[str]:
        """Scroll down to load more images."""
        ret = set()
        prev_height = await page.evaluate("document.body.scrollHeight")

        for i in range(max_scrolls):
            got = await extract_image_urls_from_js(page, max_results)
            ret.update(got)

            # Scroll down
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(self.scroll_delay * random.uniform(0.8, 1.2))

            # Try to click "Show more results" button if it exists
            try:
                show_more_selector = "input[type='button'][value='Show more results']"
                if await page.is_visible(show_more_selector):
                    await take_screenshot(page, self.debug_basepath, "before_show_more")
                    await page.click(show_more_selector)
                    await asyncio.sleep(self.wait_after_click)
                    await take_screenshot(page, self.debug_basepath, "after_show_more")
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

        await take_screenshot(page, self.debug_basepath, "after_scrolling")

        return ret

    async def search_by_query(
        self, query: str, max_results: int | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Search for images using a text query.

        Args:
            query: The search query
            max_results: Maximum number of results to return (None for all available)

        Yields:
            URLs of images found on the search page
        """
        await self._initialize_browser()
        page = await self.context.new_page()

        try:
            # Navigate to Google Images
            await page.goto("https://www.google.com/imghp")
            await take_screenshot(page, self.debug_basepath, "navigated_to_google")

            # Solve any challenges if needed
            if self.solver:
                challenge_results = await self.solver.solve(page)
                if not challenge_results.solved:
                    print("Failed to solve challenge")
                    await take_screenshot(page, self.debug_basepath, "failed_puzzle")
                    return
                elif challenge_results.puzzles:
                    await self._save_cookies()

            # Enter search query
            await take_screenshot(page, self.debug_basepath, "before_enter_query")
            await page.fill("textarea[name='q']", query)
            await page.press("textarea[name='q']", "Enter")
            await page.wait_for_load_state("networkidle")
            await take_screenshot(page, self.debug_basepath, "after_enter_query")

            # Solve any challenges if needed
            if self.solver:
                challenge_results = await self.solver.solve(page)
                if not challenge_results.solved:
                    print("Failed to solve challenge")
                    await take_screenshot(page, self.debug_basepath, "failed_puzzle_b")
                    return
                elif challenge_results.puzzles:
                    await self._save_cookies()

            # Scroll to load all images, extract URLs
            image_urls = await self._scroll_to_load_more(page, max_results)
            await take_screenshot(page, self.debug_basepath, "all_results")

            print(f"Found {len(image_urls)} URLs")

            # Yield each URL
            for url in image_urls:
                yield url

        except Exception as e:
            print(f"search_by_query: error: {type(e)} {e}")

        finally:
            await page.close()

    async def search_by_image(
        self, image_path_or_url: str, max_results: int | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Search for similar images using an existing image.

        Args:
            image_path_or_url: Path to local image file or URL of an image
            max_results: Maximum number of results to return (None for all available)

        Yields:
            URLs of similar images found on the search page
        """
        await self._initialize_browser()
        page = await self.context.new_page()

        try:
            await page.goto("https://www.google.com/imghp")
            await take_screenshot(page, self.debug_basepath, "navigated_to_google")

            lens_button_selector = 'div[aria-label="Search by image"]'
            await page.wait_for_selector(
                lens_button_selector, state="visible", timeout=self.navigation_timeout
            )
            await page.click(lens_button_selector)

            paste_link_selector = 'input[placeholder="Paste image link"]'
            upload_button_selector = 'button:has-text("Upload an image")'
            await page.wait_for_selector(
                f"{paste_link_selector}, {upload_button_selector}",
                state="visible",
                timeout=self.navigation_timeout,
            )
            await take_screenshot(page, self.debug_basepath, "after_click_camera_icon")

            async with page.expect_file_chooser(
                timeout=self.navigation_timeout
            ) as fc_info:
                await page.get_by_role("button", name="upload a file").click()

            # Set the file in the file chooser
            file_chooser = await fc_info.value
            await file_chooser.set_files(image_path_or_url)
            await take_screenshot(page, self.debug_basepath, "after_file_set")

            # Wait until we either see results or challenge
            challenge_iframe_selector = (
                'iframe[title="reCAPTCHA"], div.recaptcha-checkbox-border'
            )
            results_url_pattern = re.compile(r"/search\?.*(udm=26|vsrid=|vsint=)")
            results_container_selector = "#rso"
            wait_for_challenge_task = asyncio.create_task(
                page.wait_for_selector(
                    challenge_iframe_selector,
                    state="visible",
                    timeout=self.navigation_timeout,
                )
            )
            wait_for_results_task = asyncio.create_task(
                page.wait_for_url(results_url_pattern, timeout=self.navigation_timeout)
            )
            done, pending = await asyncio.wait(
                [wait_for_challenge_task, wait_for_results_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()  # avoid resource leaks
            await take_screenshot(
                page, self.debug_basepath, "after_wait_challenge_or_results"
            )

            # Solve challenge if needed
            if (
                self.solver
                and wait_for_challenge_task in done
                and not wait_for_challenge_task.cancelled()
            ):
                await wait_for_challenge_task  # check for exceptions
                challenge_results = await self.solver.solve(page)
                if not challenge_results.solved:
                    print("Failed to solve challenge")
                    await take_screenshot(page, self.debug_basepath, "failed_puzzle")
                    return
                elif challenge_results.puzzles:
                    await self._save_cookies()
                    await take_screenshot(page, self.debug_basepath, "solved_puzzle")

            # Wait for search results to appear
            await page.wait_for_selector(
                results_container_selector,
                state="visible",
                timeout=self.navigation_timeout,
            )
            await page.wait_for_load_state(
                "networkidle", timeout=self.navigation_timeout
            )
            await take_screenshot(page, self.debug_basepath, "search_results_visible")

            # Scroll to load all images, extract URLs
            image_urls = await self._scroll_to_load_more(page, max_results)
            await take_screenshot(page, self.debug_basepath, "all_results")

            # Yield each URL
            for url in image_urls:
                yield url

        finally:
            await page.close()


async def create_solver() -> Puzzler:
    print("Creating solver")
    gemini_key = os.environ["GEMINI_API_KEY"]
    model = GeminiClient(
        api_key=gemini_key,
        max_retries=3,
        base_delay=0.5,
        max_total_time=15,
    )
    return Puzzler(
        model,
        rounds=40,
        sequences=12,
        screenshot_basepath=None,
        grid_4_score_3_threshold=5,
    )


async def save_results(results: dict[str, Any], output_file: str | None) -> None:
    """Save results to a JSON file if output file is specified."""
    if output_file:
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {output_file}")


app = typer.Typer(help="Google Image Search Tool")


@app.command()
def search(
    query: list[str] = typer.Option(None, "--queries", "-q"),
    image: list[str] = typer.Option(None, "--images", "-i"),
    cookies_file: str | None = typer.Option(None, "--cookies", "-c"),
    headless: bool = typer.Option(False, "--headless"),
    max_results: int | None = typer.Option(None, "--max-results", "-m"),
    scroll_delay: float = typer.Option(1.5, "--scroll-delay", "-s"),
    wait_click: float = typer.Option(2.0, "--wait-click", "-w"),
    safe_search: str = typer.Option("on", "--safe-search"),
    output_file: str | None = typer.Option(None, "--output", "-o"),
    debug_basepath: str | None = typer.Option(None, "--debug-basepath", "-d"),
):
    """
    Search for images using text queries and/or similar image search.

    Search by text:
        python -m similar_images.google_playwright -q "cute cats" -q "big dogs" -d /tmp/debug

    Search by image:
        python -m similar_images.google_playwright -i $PWD/tests/integration/data/dog.jpg -d /tmp/debug
    """
    asyncio.run(
        do_search(
            query,
            image,
            cookies_file,
            headless,
            max_results,
            scroll_delay,
            wait_click,
            safe_search,
            output_file,
            debug_basepath,
        )
    )


async def do_search(
    query,
    image,
    cookies_file,
    headless,
    max_results,
    scroll_delay,
    wait_click,
    safe_search,
    output_file,
    debug_basepath,
):
    if not query and not image:
        print("Error: At least one query or image must be provided")
        raise typer.Exit(code=1)

    if debug_basepath:
        print(f"Debug mode enabled, screenshots will be saved to: {debug_basepath}")
        os.makedirs(debug_basepath, exist_ok=True)

    solver = await create_solver()

    results = {"text_queries": {}, "image_queries": {}}

    # Initialize the search engine
    async with GoogleImageSearch(
        headless=headless,
        scroll_delay=scroll_delay,
        wait_after_click=wait_click,
        safe_search=safe_search,
        solver=solver,
        cookies_file=cookies_file,
        debug_basepath=debug_basepath,
    ) as search:
        # Process text queries
        if query:
            print("=== Processing Text Queries ===")
            for q in query:
                try:
                    print(f"Searching for: {q}")
                    results["text_queries"][q] = []
                    count = 0
                    async for url in search.search_by_query(q, max_results=max_results):
                        print(f"Found image: {url}")
                        results["text_queries"][q].append(url)
                        count += 1
                    print(f"Total results for '{q}': {count}")
                except Exception as e:
                    print(f"Error querying {img_path}: {type(e)} {e}")

        # Process image queries
        if image:
            print("=== Processing Image Queries ===")
            for img_path in image:
                try:
                    print(f"Searching for similar images to: {img_path}")
                    results["image_queries"][img_path] = []
                    count = 0
                    async for url in search.search_by_image(
                        img_path, max_results=max_results
                    ):
                        print(f"Found similar image: {url}")
                        results["image_queries"][img_path].append(url)
                        count += 1
                    print(f"Total results for image '{img_path}': {count}")
                except Exception as e:
                    print(f"Error searching similar to {img_path}: {type(e)} {e}")

    # Save results
    await save_results(results, output_file)


if __name__ == "__main__":
    app()
