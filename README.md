# pytest-robot-report

[![tests](https://github.com/qabughunter/pytest-robot-report/actions/workflows/tests.yml/badge.svg)](https://github.com/qabughunter/pytest-robot-report/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Write your tests in **Python + pytest + Playwright** and read the results in Robot Framework's
**`report.html`** and **`log.html`**: pass/fail statistics, tags, nested steps, log messages,
tracebacks, and a screenshot of the page when a test fails.

`pytest_robot_report.py` is a single-file pytest plugin. It builds a Robot Framework result model
with Robot's public API (`robot.result.TestSuite`, `TestCase`, `Keyword`), saves it as `output.xml`,
then runs Robot's `rebot` to produce the HTML report and log. You keep writing pytest; you just get
Robot's report on top.

## Preview

![Robot Framework log.html generated from a pytest + Playwright run](log_preview.png)

*`log.html` from the sample suite: a passing test with its steps and logs, and the intentionally
failing test with its error, traceback and embedded screenshot.*

## Quick start

```bash
git clone https://github.com/qabughunter/pytest-robot-report.git
cd pytest-robot-report
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt                        # robotframework, pytest, pytest-playwright
playwright install chromium
```

## Run

```bash
pytest --robot-report
```

Then open `robot-results/report.html` (summary) or `robot-results/log.html` (steps and logs) in a browser.

> The sample suite includes one test that **fails on purpose**
> (`test_inventory_has_ten_items_intentional_failure`) so you can see how a failure looks in the log.

## Use it in your own project

1. Copy `pytest_robot_report.py` next to your top-level `conftest.py`.
2. `pip install robotframework`
3. Enable the plugin in **one** of these ways (not both):
   - add `pytest_plugins = ["pytest_robot_report"]` to the top of `conftest.py`, then run `pytest --robot-report`
   - or run `pytest -p pytest_robot_report --robot-report`

Without `--robot-report` the plugin stays loaded but does nothing.

## Example with `robot_step`

```python
from pytest_robot_report import robot_step, robot_log, robot_screenshot

def test_login(page):
    with robot_step("Open login page", "https://www.saucedemo.com"):   # a step (keyword) in log.html
        page.goto("https://www.saucedemo.com")
    with robot_step("Log in", "standard_user"):
        with robot_step("Type username"):                            # steps can be nested
            page.get_by_placeholder("Username").fill("standard_user")
        page.get_by_placeholder("Password").fill("secret_sauce")
        page.get_by_role("button", name="Login").click()
    robot_log("Logged in")                                           # INFO message in the current step
    robot_screenshot(page, "After login")                            # embeds a screenshot right here
```

The best place for steps is inside your **page object** methods (see [`pages/`](pages)), so every
test gets readable steps for free.

## Options

| Option | Default | What it does |
|---|---|---|
| `--robot-report` | off | Turns the plugin on. Without it, nothing is recorded or written. |
| `--robot-output-dir DIR` | `robot-results` | Folder for `output.xml`, `report.html` and `log.html` |
| `--robot-name NAME` | project folder name | Name of the top-level suite |
| `--robot-log-level LEVEL` | `INFO` | Lowest Python `logging` level copied into `log.html` |
| `--robot-no-screenshot` | off | Don't embed a screenshot of the `page` fixture when a test fails |

Recommended with pytest-playwright: `--screenshot only-on-failure --tracing retain-on-failure`
(already set in this repo's `pytest.ini`). The log then links the saved screenshot and `trace.zip`
under a **Playwright artifacts** step.

## Documentation (wiki)

The full guide lives in [`docs/`](docs/Home.md):

| Page | What's in it |
|---|---|
| [Home](docs/Home.md) | Index |
| [Installation](docs/Installation.md) | Requirements and setup |
| [Usage](docs/Usage.md) | Steps, logging, screenshots, the `step` fixture, tags and traceability |
| [Configuration](docs/Configuration.md) | Every CLI option and how to enable the plugin |
| [How It Works](docs/How-It-Works.md) | How pytest maps to the Robot model, and `output.xml` → `rebot` |
| [Using With Allure and ReportPortal](docs/Using-With-Allure-and-ReportPortal.md) | Running all three reports at once |
| [CI: GitHub Actions](docs/CI-GitHub-Actions.md) | Workflow that publishes the report as an artifact |
| [Troubleshooting](docs/Troubleshooting.md) | Common problems and fixes |
| [Limitations](docs/Limitations.md) | What isn't supported yet |

The `docs/` folder is this project's wiki. GitHub's Wiki tab can't be filled through the API, so if you
prefer the Wiki tab, copy each `docs/*.md` page into a wiki page with the same name (`Home.md` becomes
the wiki home page).

## Repository layout

| Path | What it is |
|---|---|
| `pytest_robot_report.py` | The plugin (single file) |
| `conftest.py` | Enables the plugin via `pytest_plugins` |
| `pytest.ini` | Base URL, Playwright artifact options, `smoke` and `req` markers |
| `pages/` | Page objects for https://www.saucedemo.com with steps inside |
| `tests/test_login.py` | Sample tests (2 pass, 1 fails on purpose) |
| `selftest/` | Browser-free edge cases for the plugin itself (setup/teardown errors, skip, xfail, classes, params) |
| `make_preview.py` | Renders `robot-results/log.html` into `log_preview.png` |
| `.github/workflows/tests.yml` | CI that runs the suite and uploads the report |

Tested locally with Python 3.13, Robot Framework 7.5, pytest 9.2, pytest-playwright 0.10, Playwright 1.64. CI runs on Python 3.12.

## License

[MIT](LICENSE)
