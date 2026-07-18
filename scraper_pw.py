"""Google Maps scraper using Playwright — no API key required."""

import os
import random
import re
from playwright.sync_api import Error as PlaywrightError, sync_playwright
import config

def _accept_cookies(page):
    """Try to dismiss the Google consent/cookie banner if present."""
    try:
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
            progress_callback(0, max_results, f"Found {len(ordered_urls)} listings so far...")
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
    name_el = page.locator("h1.DUwDvf")
    if name_el.count() == 0:
        name_el = page.locator('div[role="main"] h1')
    info["name"] = name_el.first.inner_text().strip() if name_el.count() > 0 else "Unknown"

    rating = "N/A"
    reviews = 0
    rating_selectors = [
        'div.F7nice span[aria-hidden="true"]',
        'span[aria-label*="stars"]',
        'div[jsaction*="pane.rating"] span:first-child'
    ]
    for sel in rating_selectors:
        rating_el = page.locator(sel)
        if rating_el.count() > 0:
            rating_text = rating_el.first.inner_text().strip()
            if rating_text and rating_text != "":
                rating = rating_text
                break
    
    reviews_selectors = [
        'div.F7nice span[aria-label*="reviews"]',
        'div.F7nice span span',
        'button[jsaction*="pane.rating"] span'
    ]
    for sel in reviews_selectors:
        reviews_el = page.locator(sel)
        if reviews_el.count() > 0:
            for i in range(reviews_el.count()):
                text = reviews_el.nth(i).inner_text().strip()
                num_match = re.search(r'(\d[\d,]*)', text)
                if num_match:
                    try:
                        reviews = int(num_match.group(1).replace(",", ""))
                        break
                    except:
                        continue
            if reviews > 0:
                break
    
    info["rating"] = rating
    info["reviews"] = reviews
    cat_el = page.locator("button.DkEaL")
    info["category"] = cat_el.inner_text().strip() if cat_el.count() > 0 else "N/A"
    addr_el = page.locator('button[data-item-id="address"] div.Io6YTe')
    info["address"] = addr_el.inner_text().strip() if addr_el.count() > 0 else "N/A"
    phone_el = page.locator('button[data-item-id^="phone:"] div.Io6YTe')
    info["phone"] = phone_el.inner_text().strip() if phone_el.count() > 0 else "N/A"
    website_el = page.locator('a[data-item-id="authority"] div.Io6YTe')
    info["website"] = website_el.inner_text().strip() if website_el.count() > 0 else None
    info["maps_url"] = page.url
    return info

def _should_force_headless():
    if os.environ.get("VERCEL") or os.environ.get("SPACE_ID") or os.environ.get("STREAMLIT_RUNTIME_ENV"):
        return True
    if os.name != "nt" and not os.environ.get("DISPLAY"):
        return True
    return False

def _launch_browser(pw):
    """Upgraded - Single and stable version for Streamlit Cloud"""
    launch_args = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-setuid-sandbox",
        "--disable-gpu",
    ]
    headless = True if _should_force_headless() else getattr(config, 'HEADLESS', True)
    try:
        return pw.chromium.launch(headless=headless, args=launch_args)
    except PlaywrightError as exc:
        message = str(exc)
        if "Executable doesn't exist" in message:
            raise RuntimeError(
                "Playwright Chromium is not installed. Run: python -m playwright install chromium"
            ) from exc
        raise

def scrape_google_maps(query, max_results=None, progress_callback=None):
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
            page.goto("https://www.google.com/maps", wait_until="load", timeout=60000)
            page.wait_for_timeout(3000)
            _accept_cookies(page)
            page.wait_for_timeout(2000)
            if "consent" in page.url.lower() or "sorry" in page.url.lower():
                page.goto("https://www.google.com/maps", wait_until="load", timeout=60000)
                page.wait_for_timeout(3000)
            if progress_callback:
                progress_callback(0, max_results, f"Searching: {query}")
            search_box = page.locator("#searchboxinput")
            if search_box.count() == 0 or not search_box.is_visible():
                search_box = page.locator('input[name="q"]')
            if search_box.count() == 0 or not search_box.is_visible():
                search_box = page.get_by_placeholder("Search Google Maps")
            search_box.wait_for(state="visible", timeout=30000)
            search_box.fill(query)
            page.keyboard.press("Enter")
            page.wait_for_timeout(3000)
            feed = page.locator('div[role="feed"]')
            if feed.count() == 0:
                page.wait_for_timeout(3000)
                feed = page.locator('div[role="feed"]')
            if feed.count() == 0:
                if progress_callback:
                    progress_callback(0, max_results, "No results panel found - retrying once...")
                page.goto("https://www.google.com/maps", wait_until="load", timeout=60000)
                page.wait_for_timeout(3000)
                search_box = page.locator("#searchboxinput")
                search_box.wait_for(state="visible", timeout=30000)
                search_box.fill(query)
                page.keyboard.press("Enter")
                page.wait_for_timeout(4000)
                feed = page.locator('div[role="feed"]')
                if feed.count() == 0:
                    raise RuntimeError("Google is rate-limiting - wait a few minutes and try again.")
            if progress_callback:
                progress_callback(0, max_results, "Loading results...")
            listing_urls = _collect_listing_urls(page, max_results, progress_callback)
            total = len(listing_urls)
            if progress_callback:
                progress_callback(0, total, f"Found {total} listings. Extracting details...")
            for idx, url in enumerate(listing_urls):
                try:
                    page.goto(url, wait_until="load", timeout=30000)
                    page.wait_for_timeout(1500 + random.randint(0, 800))
                    info = _extract_detail(page)
                    if info.get("name") in (None, "Unknown"):
                        page.wait_for_timeout(1500)
                        info = _extract_detail(page)
                    info["search_query"] = query
                    results.append(info)
                    if progress_callback:
                        progress_callback(idx + 1, total, f"Extracted: {info.get('name', '?')}")
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
