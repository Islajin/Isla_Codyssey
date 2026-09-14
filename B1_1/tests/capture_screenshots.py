import os
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = ROOT / "docs" / "screenshots"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)
BASE_URL = os.getenv("PORTFOLIO_URL", "http://127.0.0.1:8080")


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    page.on("console", lambda message: errors.append(f"console {message.type}: {message.text}") if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"pageerror: {error}"))

    page.goto(BASE_URL, wait_until="networkidle", timeout=30_000)
    page.evaluate("document.querySelectorAll('.reveal').forEach((element) => element.classList.add('visible'))")
    page.wait_for_timeout(700)
    page.screenshot(path=SCREENSHOTS / "desktop.png", full_page=True)

    page.evaluate("localStorage.setItem('theme', 'dark')")
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(700)
    page.screenshot(path=SCREENSHOTS / "dark.png")

    mobile = browser.new_page(viewport={"width": 390, "height": 844})
    mobile.goto(BASE_URL, wait_until="networkidle", timeout=30_000)
    mobile.click("#menu-toggle")
    mobile.wait_for_timeout(250)
    mobile.screenshot(path=SCREENSHOTS / "mobile-menu.png")
    mobile.click("#menu-toggle")
    mobile.wait_for_timeout(250)
    mobile.screenshot(path=SCREENSHOTS / "mobile.png")

    print(f"TITLE={page.title()}")
    print(f"PROJECT_CARDS={page.locator('.project-card').count()}")
    print(f"FILTERS={page.locator('.filter-button').count()}")
    print(f"MOBILE_MENU_CLASS={mobile.locator('#nav-menu').get_attribute('class')}")
    print(f"BROWSER_ERRORS={errors}")
    browser.close()
