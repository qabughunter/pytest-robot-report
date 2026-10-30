"""Render robot-results/log.html (failed test expanded) to log_preview.png."""
from pathlib import Path
from playwright.sync_api import sync_playwright

log = Path("robot-results/log.html").absolute()
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1400, "height": 1000})
    page.goto(log.as_uri())
    page.wait_for_selector("#s1-s1-s1-t3")

    def expand(element_id):
        # Robot's log.html toggles on header click; only click when collapsed.
        children = page.locator(f"#{element_id} > .children").first
        if not children.is_visible():
            page.locator(f"#{element_id} > .element-header").first.click()
            page.wait_for_timeout(300)

    expand("s1-s1-s1-t1")                      # passing test: steps + logs
    for kw in page.locator("#s1-s1-s1-t1 > .children > .keyword").all():
        if not kw.locator("> .children").first.is_visible():
            kw.locator("> .element-header").first.click()
    expand("s1-s1-s1-t3")                      # failing test: error, traceback, screenshot
    page.wait_for_timeout(800)
    page.screenshot(path="log_preview.png", full_page=True)
    b.close()
print("wrote log_preview.png")
