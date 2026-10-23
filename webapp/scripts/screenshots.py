"""Capture screenshots of every page of a running CodeSniff site (needs Chrome + the `playwright` Python package).

    make dev &      # backend :8000, frontend :5173
    python webapp/scripts/screenshots.py http://localhost:5173 "https://github.com/google/gson/pull/3141"
"""
import os
import sys

from playwright.sync_api import sync_playwright

SITE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5173"
TARGET = sys.argv[2] if len(sys.argv) > 2 else "https://github.com/google/gson/pull/3141"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "screenshots")
os.makedirs(OUT, exist_ok=True)


def shot(page, name, full=True):
    page.wait_for_timeout(600)
    page.screenshot(path=os.path.join(OUT, f"{name}.png"), full_page=full)
    print("saved", name)


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1366, "height": 900}, device_scale_factor=2)
    page.goto(SITE)
    page.get_by_role("heading", name="How smelly is this commit?").wait_for()
    page.wait_for_selector("text=borderline")
    shot(page, "1_home")
    page.get_by_label("GitHub repository, commit or pull-request URL").fill(TARGET)
    page.get_by_role("button", name="Analyze").click()
    page.get_by_test_id("progress").wait_for(timeout=30_000)
    shot(page, "2_progress", full=False)
    page.get_by_test_id("risk-score").wait_for(timeout=180_000)
    shot(page, "3_results")
    page.get_by_text("How this score is calculated").click()
    page.get_by_test_id("methods-table").locator("tbody tr").first.click()
    page.get_by_test_id("method-drawer").wait_for()
    shot(page, "4_results_method_drawer", full=False)
    page.keyboard.press("Escape")
    page.get_by_role("link", name="History").click()
    page.wait_for_selector("table")
    shot(page, "5_history")
    page.get_by_role("link", name="Research findings").click()
    page.wait_for_selector("text=Long runs of identical answers")
    page.wait_for_selector(".recharts-scatter-symbol")
    page.wait_for_timeout(3000)
    shot(page, "6_research_findings")
    page.get_by_role("link", name="About").click()
    page.wait_for_selector("text=What it does not claim")
    shot(page, "7_about")
    page.set_viewport_size({"width": 390, "height": 844})
    page.get_by_role("link", name="Analyze").click()
    page.get_by_role("heading", name="How smelly is this commit?").wait_for()
    shot(page, "8_home_mobile")
    browser.close()
