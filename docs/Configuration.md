# Configuration

## Enabling the plugin

The plugin has to be loaded by pytest and then switched on with `--robot-report`.

**Load it in one way only:**

| Way | How |
|---|---|
| `conftest.py` (recommended) | Put `pytest_plugins = ["pytest_robot_report"]` at the top of your **top-level** `conftest.py`. Then run `pytest --robot-report`. |
| Command line | Leave `conftest.py` alone and run `pytest -p pytest_robot_report --robot-report`. |

Don't do both. Pick one place so it's clear where the plugin is loaded from. (`pytest_plugins` is
only allowed in the root `conftest.py`; newer pytest versions reject it in nested ones.)

Once loaded, the plugin does nothing until you pass `--robot-report`. Your normal `pytest` runs are unaffected.

To always produce the report, add the flag to `addopts` in `pytest.ini`:

```ini
[pytest]
addopts = --robot-report --screenshot only-on-failure --tracing retain-on-failure
```

## Command-line options

These are all the options the plugin registers (`pytest --help` lists them under **Robot Framework report**):

| Option | Default | What it does |
|---|---|---|
| `--robot-report` | off | Turns the plugin on. It records the run and writes `output.xml`, `report.html` and `log.html` at the end. |
| `--robot-output-dir DIR` | `robot-results` | Folder for the three files. A relative path is resolved against the folder you run `pytest` from. Created if missing. |
| `--robot-name NAME` | name of the pytest rootdir | Name of the top-level suite shown in the report and log. |
| `--robot-log-level LEVEL` | `INFO` | Lowest Python `logging` level copied into `log.html`: `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL`. An unknown value falls back to `INFO`. |
| `--robot-no-screenshot` | off | Don't embed a screenshot of the `page` fixture when a test fails. |

Examples:

```bash
pytest --robot-report
pytest --robot-report --robot-output-dir reports/robot --robot-name "Swag Labs UI"
pytest --robot-report --robot-log-level DEBUG
pytest --robot-report --robot-no-screenshot
pytest selftest --robot-report --robot-output-dir robot-selftest     # the plugin's own edge-case suite
```

`--robot-log-level` only affects Python `logging` records. Messages written with `robot_log()` are
always kept. While a test runs, the plugin lowers the root logger's level to this value if needed and
restores it afterwards.

## pytest-playwright options that work well with it

These belong to pytest-playwright, not to this plugin:

| Option | Effect in the Robot log |
|---|---|
| `--screenshot only-on-failure` | Saved screenshot is linked (and shown as a thumbnail) under a **Playwright artifacts** step |
| `--tracing retain-on-failure` | `trace.zip` is linked, with a hint to open it with `playwright show-trace` or https://trace.playwright.dev |
| `--video retain-on-failure` | Video file is linked |
| `--output DIR` | Where those artifacts go (default `test-results`). The plugin reads this to find them. |
| `--base-url URL` / `base_url` in `pytest.ini` | Lets page objects use `page.goto("/")` |

This repo's `pytest.ini`:

```ini
[pytest]
pythonpath = .
testpaths = tests
base_url = https://www.saucedemo.com
addopts = --screenshot only-on-failure --tracing retain-on-failure
markers =
    smoke: quick checks
    req(id): requirement ID for traceability
```

## Not supported

- `pytest -n` (pytest-xdist): the plugin warns `pytest_robot_report does not support pytest-xdist (-n); no Robot report written.`
  and writes nothing. See [Limitations](Limitations.md).

Next: [How It Works](How-It-Works.md)
