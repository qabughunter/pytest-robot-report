"""Browser-free edge cases used to check the plugin itself (setup/teardown errors, skips, xfail)."""
import logging

import pytest

from pytest_robot_report import robot_log, robot_step


@pytest.fixture
def broken_setup():
    raise RuntimeError("database not reachable")


@pytest.fixture
def broken_teardown():
    with robot_step("Create temp data"):
        robot_log("created")
    yield
    with robot_step("Clean temp data"):
        raise RuntimeError("cleanup failed")


def test_setup_error(broken_setup):
    pass


def test_teardown_error(broken_teardown):
    with robot_step("Do work"):
        logging.getLogger("app").info("working")


@pytest.mark.skip(reason="not ready")
def test_skipped():
    pass


@pytest.mark.xfail(reason="known bug #12")
def test_known_bug():
    assert 1 == 2


@pytest.mark.parametrize("n", [1, 2])
class TestNumbers:
    """Class becomes a sub-suite; parametrize ids stay in test names."""

    def test_positive(self, n):
        with robot_step("Check positive", n):
            print(f"n={n}")
            assert n > 0
