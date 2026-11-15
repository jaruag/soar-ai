"""End-to-end tests for the SOAR-AI web UI, using Playwright.

These drive a real browser against a running server, so the server
must be up at http://127.0.0.1:8000 when these run.
"""

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:8000"


def test_page_loads(page: Page):
    """The main page loads and shows the app title."""
    page.goto(BASE_URL)
    expect(page.locator(".logo-text")).to_contain_text("SOAR")


def test_scan_form_is_visible(page: Page):
    """The scan form and its fields are present."""
    page.goto(BASE_URL)
    expect(page.locator("#package")).to_be_visible()
    expect(page.locator("#version")).to_be_visible()
    expect(page.locator("#scanBtn")).to_be_visible()


def test_tab_navigation(page: Page):
    """Clicking the About tab shows the about content."""
    page.goto(BASE_URL)

    # About section starts hidden
    expect(page.locator("#about")).not_to_be_visible()

    # Click the About nav item
    page.locator('.nav-item[data-tab="about"]').click()

    # Now it should be visible
    expect(page.locator("#about")).to_be_visible()


@pytest.mark.slow
def test_scan_shows_results(page: Page):
    """Running a real scan shows finding cards. This is slow (live scan + LLM)."""
    page.goto(BASE_URL)

    page.locator("#package").fill("requests")
    page.locator("#version").fill("2.19.0")
    page.locator("#scanBtn").click()

    # Wait for at least one finding card to appear (up to 60s for scan + LLM)
    expect(page.locator(".finding").first).to_be_visible(timeout=60000)

def test_history_tab_loads(page: Page):
    """Clicking History shows the history heading."""
    page.goto(BASE_URL)
    page.locator('.nav-item[data-tab="history"]').click()
    expect(page.locator("#history h1")).to_contain_text("history", ignore_case=True)


def test_wrong_ecosystem_shows_toast(page: Page):
    """Scanning a Python package while npm is selected should show a toast,
    not run a scan."""
    page.goto(BASE_URL)

    # Select npm, but type a Python package
    page.locator("#ecosystem").select_option("npm")
    page.locator("#package").fill("django")
    page.locator("#version").fill("2.2.0")
    page.locator("#scanBtn").click()

    # The toast should appear
    expect(page.locator("#toast")).to_be_visible()
    expect(page.locator("#toast")).to_contain_text("Python")


def test_ecosystem_selector_has_options(page: Page):
    """The ecosystem selector offers both pip and npm."""
    page.goto(BASE_URL)
    options = page.locator("#ecosystem option")
    expect(options).to_have_count(2)