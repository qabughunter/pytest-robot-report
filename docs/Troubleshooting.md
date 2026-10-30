# Troubleshooting

### `pytest: error: unrecognized arguments: --robot-report`

The plugin isn't loaded. Either add `pytest_plugins = ["pytest_robot_report"]` to the **top-level**
`conftest.py`, or run `pytest -p pytest_robot_report --robot-report`.

### `ModuleNotFoundError: No module named 'pytest_robot_report'`

pytest can't import the file. Put `pytest_robot_report.py` in the project root and add
`pythonpath = .` under `[pytest]` in `pytest.ini`, or run from the folder that contains the file.

### `ImportError: pytest_robot_report needs Robot Framework: pip install robotframework`

Robot Framework isn't installed in the environment pytest is using. Activate your virtual environment
and run `pip install robotframework`. Check with `python -m pip show robotframework`.

### Tests run but no `robot-results/` folder appears

- You forgot `--robot-report`. Without it, the plugin does nothing.
- You used `-n` (pytest-xdist). The plugin warns
  `pytest_robot_report does not support pytest-xdist (-n); no Robot report written.` Run without `-n`.
- You passed `--robot-output-dir`. The files are in that folder, relative to where you ran `pytest`.
  The paths are printed at the end of the run under **Robot Framework report**.

### The terminal shows `WARNING: rebot failed with return code N`

`output.xml` was written but Robot couldn't turn it into HTML. Run
`rebot --outputdir robot-results robot-results/output.xml` yourself to see Robot's error message, and
make sure `robotframework` is 7.0 or newer.

### My `logging` messages are missing from `log.html`

- They're below `--robot-log-level` (default `INFO`). Run with `--robot-log-level DEBUG`.
- They're `DEBUG` and the log is showing `INFO`. Change the **Log level** drop-down at the top of `log.html`.
- The logger has `propagate = False`, so it never reaches the root logger the plugin listens on.
  Set `propagate = True`, or use `robot_log()`.
- They were logged outside a test (for example at import time or in `pytest_sessionstart`). Only
  messages logged during setup, call or teardown are captured.

### `print()` output isn't inside my step

That's expected: pytest captures stdout for a whole phase, so it shows up once as "Captured stdout call".
Use `logging` or `robot_log()` for messages that should appear inside a step.

### No screenshot on failure

- The test doesn't use the `page` fixture (for example it creates its own page). Call
  `robot_screenshot(my_page, "...")` in your test or in a `try/except` block.
- `--robot-no-screenshot` is set.
- The failure happened in setup or teardown; the automatic screenshot is only taken for call-phase failures.

### Trace or screenshot links in `log.html` are broken

They're relative links to `test-results/`. Keep `robot-results/` and `test-results/` in the same relative
position (CI artifact: upload both). The links only appear when pytest-playwright actually saved files,
for example with `--screenshot only-on-failure --tracing retain-on-failure`.

### `PytestUnknownMarkWarning: Unknown pytest.mark.req`

Register your markers in `pytest.ini`:

```ini
markers =
    req(id): requirement ID for traceability
    smoke: quick checks
```

(`robot_tag` is registered by the plugin.)

### `log.html` is very large

Every failure screenshot is embedded as base64. Use `--robot-no-screenshot` and rely on the linked
Playwright screenshot, or reduce `robot_screenshot()` calls.

Next: [Limitations](Limitations.md)
