"""Google Maps scraper using Playwright — no API key required."""

import os
import random

from playwright.sync_api import Error as PlaywrightError, sync_playwright

import config

def _accept_cookies(page):
    """Try to dismiss the Google consent/cookie banner if present."""
    try:
        # Try multiple consent button patterns
        for selector in [
            "button:has-text('Accept all')",
            "button:has-text('I agree')",
            "button:has-text('Reject all')",
            "button:has-text('Accept')",
            '[aria-label="Accept all"]',
            'form[action*="consent"] button',
        ]:
            btn = page.locator(selector)
            if btn.count() > 0 and btn.first.is_visible():
                btn.first.click()
                page.wait_for_timeout(2000)
                return
    except Exception:
        pass

def _collect_listing_urls(page, max_results, progress_callback=None):
    """
    Scroll the results panel and collect each listing's place URL.

    We deliberately collect URLs first (instead of clicking each card in
    place) because Google Maps' results list is virtualized: clicking a
    card and pressing "Back" resets the panel's scroll position, which
    detaches any cards loaded by earlier scrolling. Collecting URLs up
    front and then visiting each one directly with page.goto() sidesteps
    that entirely.
    """
    feed = page.locator('div[role="feed"]')
    if feed.count() == 0:
        return []

    seen = set()
    ordered_urls = []

    def _collect_current():
        links = page.locator('div[role="feed"] a[href*="/maps/place/"]')
        count = links.count()
        for i in range(count):
            href = links.nth(i).get_attribute("href")
            if href and href not in seen:
                seen.add(href)
                ordered_urls.append(href)

    _collect_current()

    last_height = 0
    retries = 0
    max_stall_retries = config.SCROLL_MAX_STALL_RETRIES

    while retries < max_stall_retries and len(ordered_urls) < max_results:
        feed.evaluate("el => el.scrollTo(0, el.scrollHeight)")
        page.wait_for_timeout(int(config.SCROLL_PAUSE_TIME * 1000))
        _collect_current()

        if progress_callback:
            progress_callback(
                0, max_results, f"Found {len(ordered_urls)} listings so far..."
            )

        # Google shows a "You've reached the end of the list" marker when
        # there are truly no more results to load.
        end_marker = page.locator("text=You've reached the end of the list")
        if end_marker.count() > 0:
            break

        new_height = feed.evaluate("el => el.scrollHeight")
        if new_height == last_height:
            retries += 1
        else:
            retries = 0
        last_height = new_height

    return ordered_urls[:max_results]

def _extract_detail(page):
    """Extract business details from the detail panel."""
    info = {}

    # Name (primary selector, with a fallback to any visible h1 in the panel
    # since Google periodically changes its hashed CSS class names)
    name_el = page.locator("h1.DUwDvf")
    if name_el.count() == 0:
        name_el = page.locator('div[role="main"] h1')
    info["name"] = name_el.first.inner_text().strip() if name_el.count() > 0 else "Unknown"

    # Rating
    rating_el = page.locator("div.F7nice span[aria-hidden='true']")
    info["rating"] = rating_el.first.inner_text().strip() if rating_el.count() > 0 else "N/A"

    # Review count - direct int return karo
    reviews_el = page.locator("div.F7nice span span")
    if reviews_el.count() > 0:
        text = reviews_el.first.inner_text().strip().replace("(", "").replace(")", "").replace(",", "")
        try:
            info["reviews"] = int(text) if text else 0
        except:
            info["reviews"] = 0
    else:
        info["reviews"] = 0

    # Category / type
    cat_el = page.locator("button.DkEaL")
    info["category"] = cat_el.inner_text().strip() if cat_el.count() > 0 else "N/A"

    # Address
    addr_el = page.locator('button[data-item-id="address"] div.Io6YTe')
    info["address"] = addr_el.inner_text().strip() if addr_el.count() > 0 else "N/A"

    # Phone
    phone_el = page.locator('button[data-item-id^="phone:"] div.Io6YTe')
    info["phone"] = phone_el.inner_text().strip() if phone_el.count() > 0 else "N/A"

    # Website
    website_el = page.locator('a[data-item-id="authority"] div.Io6YTe')
    info["website"] = website_el.inner_text().strip() if website_el.count() > 0 else None

    # Google Maps URL
    info["maps_url"] = page.url

    return info

def _should_force_headless():
    """
    Decide whether we must run headless regardless of config.HEADLESS.

    Any cloud host (Streamlit Cloud, HuggingFace Spaces, Vercel, etc.) is a
    Linux server with no real screen — trying to launch a headed browser
    there fails with "Missing X server or $DISPLAY". We only want headed
    mode on a real local desktop (e.g. your Windows laptop), so: force
    headless whenever we're on Linux and there's no DISPLAY set. Windows
    never sets $DISPLAY either, but os.name is "nt" there, so this check
    correctly leaves local Windows runs alone.
    """
    if os.environ.get("VERCEL") or os.environ.get("SPACE_ID") or os.environ.get("STREAMLIT_RUNTIME_ENV"):
        return True
    if os.name != "nt" and not os.environ.get("DISPLAY"):
        return True
    return False

def _launch_browser(pw):
    """Launch Chromium and provide a useful setup error if browsers are missing."""
    launch_args = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-setuid-sandbox",
    ]
    headless = True if _should_force_headless() else config.HEADLESS
    try:
        return pw.chromium.launch(
            headless=headless,
            args=launch_args,
        )
    except PlaywrightError as exc:
        message = str(exc)
        if "Executable doesn't exist" in message:
            raise RuntimeError(
                "Playwright Chromium is not installed. Run: python -m playwright install chromium"
            ) from exc
        raise

def scrape_google_maps(query, max_results=None, progress_callback=None):
    """
    Scrape Google Maps for business listings.

    Args:
        query: Search query, e.g. "restaurants in New York"
        max_results: Maximum number of results to return
        progress_callback: Optional callable(current, total, message)

    Returns:
        List of dicts with business info.
    """
    if max_results is None:
        max_results = config.MAX_RESULTS_PER_SEARCH

    results = []

    if progress_callback:
        progress_callback(0, max_results, "Starting browser...")

    with sync_playwright() as pw:
        browser = _launch_browser(pw)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/146.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        try:
            # Navigate to Google Maps
            page.goto("https://www.google.com/maps", wait_until="load", timeout=60000)
            page.wait_for_timeout(3000)

            if config.DEBUG_SCREENSHOTS:
                page.screenshot(path="debug_page.png")

            _accept_cookies(page)
            page.wait_for_timeout(2000)

            # After consent, we may need to navigate again
            if "consent" in page.url.lower() or "sorry" in page.url.lower():
                page.goto("https://www.google.com/maps", wait_until="load", timeout=60000)
                page.wait_for_timeout(3000)

            if config.DEBUG_SCREENSHOTS:
                page.screenshot(path="debug_after_consent.png")

            # Type search query
            if progress_callback:
                progress_callback(0, max_results, f"Searching: {query}")

            # Wait for search box with longer timeout — try multiple selectors
            search_box = page.locator("#searchboxinput")
            if search_box.count() == 0 or not search_box.is_visible():
                search_box = page.locator('input[name="q"]')
            if search_box.count() == 0 or not search_box.is_visible():
                search_box = page.get_by_placeholder("Search Google Maps")
            search_box.wait_for(state="visible", timeout=30000)
            search_box.fill(query)
            page.keyboard.press("Enter")
            page.wait_for_timeout(3000)

            # Give the results panel a bit more time and retry the search
            # once if it never shows up — this usually means Google served
            # a CAPTCHA / "unusual traffic" page instead of real results
            # (commonly triggered after a burst of rapid automated requests).
            feed = page.locator('div[role="feed"]')
            if feed.count() == 0:
                page.wait_for_timeout(3000)
                feed = page.locator('div[role="feed"]')

            if feed.count() == 0:
                if config.DEBUG_SCREENSHOTS:
                    page.screenshot(path=os.path.join(config.SCREENSHOT_DIR, "no_results_panel.png"))
                if progress_callback:
                    progress_callback(
                        0, max_results,
                        "No results panel found (Google may be rate-limiting) — retrying once...",
                    )
                page.goto("https://www.google.com/maps", wait_until="load", timeout=60000)
                page.wait_for_timeout(3000)
                search_box = page.locator("#searchboxinput")
                search_box.wait_for(state="visible", timeout=30000)
                search_box.fill(query)
                page.keyboard.press("Enter")
                page.wait_for_timeout(4000)
                feed = page.locator('div[role="feed"]')
                if feed.count() == 0:
                    if config.DEBUG_SCREENSHOTS:
                        page.screenshot(path=os.path.join(config.SCREENSHOT_DIR, "no_results_panel_retry.png"))
                    raise RuntimeError(
                        "Google did not return a normal results list after retrying. "
                        "This usually means Google is temporarily rate-limiting this "
                        "connection — wait a few minutes and try again."
                    )

            # Scroll to load & collect every listing's URL
            if progress_callback:
                progress_callback(0, max_results, "Loading results...")

            listing_urls = _collect_listing_urls(page, max_results, progress_callback)
            total = len(listing_urls)

            if progress_callback:
                progress_callback(0, total, f"Found {total} listings. Extracting details...")

            # Visit each listing directly by URL — no click+back navigation,
            # so nothing depends on the results panel's scroll state.
            for idx, url in enumerate(listing_urls):
                try:
                    page.goto(url, wait_until="load", timeout=30000)
                    page.wait_for_timeout(1500 + random.randint(0, 800))

                    info = _extract_detail(page)

                    # If the name didn't come through, the page probably
                    # hadn't finished rendering yet — give it one more
                    # chance before accepting an incomplete record.
                    if info.get("name") in (None, "Unknown"):
                        page.wait_for_timeout(1500)
                        info = _extract_detail(page)

                    info["search_query"] = query
                    results.append(info)

                    if progress_callback:
                        progress_callback(
                            idx + 1, total, f"Extracted: {info.get('name', '?')}"
                        )

                except Exception as exc:
                    if progress_callback:
                        progress_callback(idx + 1, total, f"Skipped item {idx + 1}: {exc}")
                    continue

        except Exception as exc:
            if progress_callback:
                progress_callback(0, 0, f"Error: {exc}")
            raise
        finally:
            browser.close()

    return results
