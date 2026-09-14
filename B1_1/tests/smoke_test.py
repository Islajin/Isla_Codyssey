import os

from playwright.sync_api import sync_playwright


BASE_URL = os.getenv("PORTFOLIO_URL", "http://127.0.0.1:8080")


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    errors = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(BASE_URL, wait_until="networkidle", timeout=30_000)

    assert page.title() == "YeonJin — Web Developer"
    assert page.locator("main section").count() == 5
    assert page.locator(".project-card").count() > 0
    assert page.locator(".filter-button").count() > 1

    initial_theme = page.locator("html").get_attribute("data-theme")
    page.click("#theme-toggle")
    changed_theme = page.locator("html").get_attribute("data-theme")
    assert changed_theme != initial_theme
    assert page.evaluate("localStorage.getItem('theme')") == changed_theme
    page.reload(wait_until="networkidle")
    assert page.locator("html").get_attribute("data-theme") == changed_theme

    page.evaluate("document.documentElement.style.scrollBehavior = 'auto'; window.scrollTo(0, 400)")
    page.wait_for_function("document.querySelector('#scroll-top').classList.contains('visible')")
    assert "scrolled" in (page.locator("#site-header").get_attribute("class") or "")
    assert "visible" in (page.locator("#scroll-top").get_attribute("class") or "")

    page.click('a[href="#contact"]')
    page.wait_for_timeout(500)
    page.click('#contact-form button[type="submit"]')
    assert page.locator("#name-error").text_content()
    assert page.locator("#email-error").text_content()
    assert page.locator("#message-error").text_content()
    assert page.locator("#form-status").text_content()

    mobile = browser.new_page(viewport={"width": 390, "height": 844})
    mobile.goto(BASE_URL, wait_until="networkidle", timeout=30_000)
    mobile.click("#menu-toggle")
    assert "active" in (mobile.locator("#nav-menu").get_attribute("class") or "")
    assert mobile.locator("#menu-toggle").get_attribute("aria-expanded") == "true"

    assert not errors, f"Browser errors: {errors}"
    print("SMOKE_TEST_OK")
    browser.close()
