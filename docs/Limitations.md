# Limitations

Known limits of the current `pytest_robot_report.py`:

| Limitation | Details | Workaround |
|---|---|---|
| **No pytest-xdist (`-n`)** | With `-n`, the plugin warns `pytest_robot_report does not support pytest-xdist (-n); no Robot report written.` and writes nothing. Workers don't record either. | Run without `-n`, or split the suite across CI jobs that each write their own folder (`--robot-output-dir`) and combine them with `rebot --merge` or `rebot --output combined.xml ...` (not built in). |
| **`print()` is per phase, not per step** | pytest captures stdout for a whole phase, so `print()` output appears once as "Captured stdout setup/call/teardown" at the end of that phase. Stderr is shown as WARN. | Use `logging` or `robot_log()` for messages that should sit inside a step. |
| **Root logger only** | The handler is attached to the root logger. Loggers with `propagate = False` aren't captured. Messages logged outside setup/call/teardown are ignored. | Keep `propagate = True`, or call `robot_log()`. |
| **Screenshots are base64** | Screenshots from `robot_screenshot()` and the automatic failure screenshot are embedded in `log.html`. That keeps the log one shareable file, but it grows with every screenshot. | `--robot-no-screenshot`, fewer `robot_screenshot()` calls. |
| **Failure screenshot needs the `page` fixture** | The automatic screenshot uses the test's `page` fixture, and only for call-phase failures. | Call `robot_screenshot(your_page)` yourself. |
| **Relative artifact links** | Links to Playwright traces, videos and saved screenshots are relative paths from `--robot-output-dir` to pytest-playwright's `--output` folder (`test-results/`). | Move or upload both folders together. |
| **pytest-rerunfailures untested** | Not tested with `--reruns`. Retries would likely end up in one Robot test with every attempt's steps mixed together. | Avoid reruns with this report, or treat the result with care. |
| **Steps aren't real keywords** | Steps are Python context managers, so Robot's keyword statistics and libdoc links don't apply. | None needed for reading the log. |
| **Session-scoped fixtures** | Work done by a session- or module-scoped fixture is recorded in the setup (or teardown) of whichever test triggered it. | Expected behaviour; name steps clearly. |

Found something else? Open an issue with the pytest command, versions (`pip show pytest robotframework pytest-playwright`)
and the relevant part of `output.xml`.

Back to [Home](Home.md)
