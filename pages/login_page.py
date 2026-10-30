import logging

from playwright.sync_api import Page, expect

from pytest_robot_report import robot_step

log = logging.getLogger(__name__)


class LoginPage:
    """Page object for https://www.saucedemo.com login screen."""

    def __init__(self, page: Page):
        self.page = page
        self.username = page.get_by_placeholder("Username")
        self.password = page.get_by_placeholder("Password")
        self.login_button = page.get_by_role("button", name="Login")
        self.error = page.locator("[data-test='error']")

    def open(self):
        with robot_step("Open login page", "/"):
            self.page.goto("/")
            log.info("Opened %s", self.page.url)

    def login(self, user: str, password: str):
        with robot_step("Log in", user):
            self.username.fill(user)
            self.password.fill(password)
            log.info("Submitting login form for user %s", user)
            self.login_button.click()

    def expect_error(self, text: str):
        with robot_step("Error message should contain", text):
            expect(self.error).to_contain_text(text)
