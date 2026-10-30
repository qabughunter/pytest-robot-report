from playwright.sync_api import Page, expect

from pytest_robot_report import robot_step


class InventoryPage:
    """Page object for the product list shown after login."""

    def __init__(self, page: Page):
        self.page = page
        self.title = page.locator("[data-test='title']")
        self.items = page.locator("[data-test='inventory-item']")

    def expect_loaded(self):
        with robot_step("Inventory page should be open"):
            expect(self.page).to_have_url("https://www.saucedemo.com/inventory.html")
            expect(self.title).to_have_text("Products")

    def expect_item_count(self, count: int):
        with robot_step("Inventory should list items", count):
            expect(self.items).to_have_count(count)
