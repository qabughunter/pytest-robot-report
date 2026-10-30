"""Login feature of the Swag Labs demo shop (saucedemo.com)."""
import logging

import pytest

from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage
from pytest_robot_report import robot_log

log = logging.getLogger(__name__)


@pytest.mark.smoke
@pytest.mark.req("TR-01")
def test_valid_login_shows_products(page):
    """A standard user can log in and sees the product list."""
    login = LoginPage(page)
    login.open()
    login.login("standard_user", "secret_sauce")
    inventory = InventoryPage(page)
    inventory.expect_loaded()
    inventory.expect_item_count(6)
    print("Stdout is captured too: login worked")


@pytest.mark.req("TR-02")
def test_locked_out_user_sees_error(page):
    """A locked-out user gets a clear error message."""
    login = LoginPage(page)
    login.open()
    login.login("locked_out_user", "secret_sauce")
    login.expect_error("Sorry, this user has been locked out.")
    robot_log("Locked-out message verified")


@pytest.mark.req("TR-03")
def test_inventory_has_ten_items_intentional_failure(page):
    """INTENTIONAL FAILURE: the shop has 6 products, this test expects 10.

    Shows how a failure, its traceback and the screenshot look in log.html.
    """
    login = LoginPage(page)
    login.open()
    login.login("standard_user", "secret_sauce")
    log.warning("About to check a wrong item count on purpose")
    InventoryPage(page).expect_item_count(10)
