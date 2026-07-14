"""Google Maps scraper using Selenium — no API key required."""

import os
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)

import config


def create_driver():
    """Create and return a configured Chrome WebDriver."""
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--lang=en-US")
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    )
    # Suppress logging
    opts.add_argument("--log-level=3")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])

    service = Service(log_output=os.devnull)
    driver = webdriver.Chrome(service=service, options=opts)
    driver.implicitly_wait(5)
    return driver


def _accept_cookies(driver):
    """Try to dismiss the Google consent/cookie banner if present."""
    try:
        btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Accept all')]")
            )
        )
        btn.click()
        time.sleep(1)
    except TimeoutException:
        pass


def _scroll_results(driver, max_results):
    """Scroll the results panel to load more entries."""
    try:
        scrollable = driver.find_element(
            By.CSS_SELECTOR, 'div[role="feed"]'
        )
    except NoSuchElementException:
        return

    last_height = 0
    retries = 0
    while retries < 8:
        driver.execute_script(
            "arguments[0].scrollTo(0, arguments[0].scrollHeight);", scrollable
        )
        time.sleep(config.SCROLL_PAUSE_TIME)

        items = driver.find_elements(By.CSS_SELECTOR, 'div[role="feed"] > div > div > a')
        if len(items) >= max_results:
            break

        new_height = driver.execute_script(
            "return arguments[0].scrollHeight", scrollable
        )
        if new_height == last_height:
            retries += 1
        else:
            retries = 0
        last_height = new_height


def _extract_detail(driver):
    """Extract business details from the detail panel."""
    info = {}

    # Name
    try:
        info["name"] = driver.find_element(
            By.CSS_SELECTOR, "h1.DUwDvf"
        ).text.strip()
    except NoSuchElementException:
        info["name"] = "Unknown"

    # Rating
    try:
        rating_el = driver.find_element(By.CSS_SELECTOR, "div.F7nice span[aria-hidden='true']")
        info["rating"] = rating_el.text.strip()
    except NoSuchElementException:
        info["rating"] = "N/A"

    # Review count
    try:
        reviews_el = driver.find_element(By.CSS_SELECTOR, "div.F7nice span span")
        text = reviews_el.text.strip().replace("(", "").replace(")", "").replace(",", "")
        info["reviews"] = text
    except NoSuchElementException:
        info["reviews"] = "0"

    # Category / type
    try:
        info["category"] = driver.find_element(
            By.CSS_SELECTOR, "button.DkEaL"
        ).text.strip()
    except NoSuchElementException:
        info["category"] = "N/A"

    # Address
    try:
        addr_el = driver.find_element(
            By.CSS_SELECTOR, 'button[data-item-id="address"] div.Io6YTe'
        )
        info["address"] = addr_el.text.strip()
    except NoSuchElementException:
        info["address"] = "N/A"

    # Phone
    try:
        phone_btn = driver.find_element(
            By.CSS_SELECTOR,
            'button[data-item-id^="phone:"] div.Io6YTe',
        )
        info["phone"] = phone_btn.text.strip()
    except NoSuchElementException:
        info["phone"] = "N/A"

    # Website
    try:
        website_el = driver.find_element(
            By.CSS_SELECTOR, 'a[data-item-id="authority"] div.Io6YTe'
        )
        info["website"] = website_el.text.strip()
    except NoSuchElementException:
        info["website"] = None

    # Google Maps URL
    try:
        info["maps_url"] = driver.current_url
    except Exception:
        info["maps_url"] = "N/A"

    return info


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
    driver = None

    try:
        if progress_callback:
            progress_callback(0, max_results, "Starting browser...")

        driver = create_driver()

        # Navigate to Google Maps
        maps_url = "https://www.google.com/maps"
        driver.get(maps_url)
        time.sleep(2)

        _accept_cookies(driver)

        # Type search query
        if progress_callback:
            progress_callback(0, max_results, f"Searching: {query}")

        search_box = WebDriverWait(driver, config.BROWSER_TIMEOUT).until(
            EC.presence_of_element_located((By.ID, "searchboxinput"))
        )
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.ENTER)
        time.sleep(3)

        # Scroll to load results
        if progress_callback:
            progress_callback(0, max_results, "Loading results...")

        _scroll_results(driver, max_results)

        # Collect all listing links
        items = driver.find_elements(
            By.CSS_SELECTOR, 'div[role="feed"] > div > div > a'
        )
        total = min(len(items), max_results)

        if progress_callback:
            progress_callback(0, total, f"Found {total} listings. Extracting details...")

        # Click each listing and extract details
        for idx in range(total):
            try:
                # Re-fetch items to avoid stale refs after navigation
                items = driver.find_elements(
                    By.CSS_SELECTOR, 'div[role="feed"] > div > div > a'
                )
                if idx >= len(items):
                    break

                items[idx].click()
                time.sleep(2)

                info = _extract_detail(driver)
                info["search_query"] = query
                results.append(info)

                if progress_callback:
                    progress_callback(
                        idx + 1, total, f"Extracted: {info.get('name', '?')}"
                    )

                # Go back to results list
                try:
                    back_btn = driver.find_element(
                        By.CSS_SELECTOR, 'button[aria-label="Back"]'
                    )
                    back_btn.click()
                    time.sleep(1.5)
                except NoSuchElementException:
                    driver.back()
                    time.sleep(2)

            except (StaleElementReferenceException, TimeoutException) as exc:
                if progress_callback:
                    progress_callback(idx + 1, total, f"Skipped item {idx + 1}: {exc}")
                continue

    except Exception as exc:
        if progress_callback:
            progress_callback(0, 0, f"Error: {exc}")
        raise
    finally:
        if driver:
            driver.quit()

    return results
