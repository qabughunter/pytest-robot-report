# How it works

`pytest_robot_report.py` never touches Robot's XML by hand. It builds a result tree with Robot
Framework's public result model (`robot.result.TestSuite`, `TestCase`, `Keyword`, messages), saves it
with `robot.result.Result(...).save()` as `output.xml`, then calls `robot.rebot()` to create
`report.html` and `log.html`. That's the same thing `robot` does at the end of a normal Robot run, so the
HTML is Robot's own.

## Lifecycle

```
pytest_configure        --robot-report given? create the top-level TestSuite (name = --robot-name or rootdir)
  for each test:
    pytest_runtest_protocol   create suites for folders/module/classes, create the TestCase
      setup phase             steps + logs  -> "pytest fixture setup" keyword
      call phase              steps + logs  -> the test body
      teardown phase          steps + logs  -> "pytest fixture teardown" keyword
      pytest_runtest_makereport  per phase: status, failure text, captured stdout/stderr, failure screenshot
    end of protocol           link Playwright artifacts, combine phase results into the test status
pytest_sessionfinish    fix suite times, save output.xml, run rebot -> report.html + log.html
pytest_terminal_summary print the three file paths
```

During each phase the plugin keeps a stack of "where new things go": the test (or setup/teardown keyword)
at the bottom, and every open `robot_step` on top. `robot_log()`, `logging` records and nested steps are
added to whatever is on top of the stack.

A logging handler is attached to the **root logger** only for the duration of each phase, so records
from your code and from libraries that propagate to the root logger are captured live, inside the right step.

## pytest → Robot mapping

| pytest | Robot Framework |
|---|---|
| rootdir | top-level suite (name from `--robot-name` or the folder name) |
| each folder in the test path | nested suite, title-cased (`ui_tests` → `Ui Tests`) |
| test module `test_login.py` | suite `Login` (`test_` prefix removed, `_` → space, title case); module docstring → suite documentation |
| test class | nested suite with the class name; class docstring → documentation |
| test function | test case; name keeps the parametrize id, e.g. `test_positive[1]` |
| test docstring | test documentation |
| test line number | test `lineno` |
| markers | tags (see [Usage](Usage.md#tags-and-traceability-with-markers)) |
| `robot_step(name, *args, doc=)` | keyword with owner `Step`, arguments, documentation, timing and status |
| `robot_log()` / `logging` | messages with the matching level (`[logger] message` for logging) |
| `print()` / stderr | one "Captured stdout/stderr &lt;phase&gt;" message at the end of that phase (stderr as WARN) |
| fixture setup work | test setup keyword `pytest fixture setup` (shown only if not empty or failed) |
| fixture teardown work | test teardown keyword `pytest fixture teardown` (shown only if not empty or failed) |
| failure | FAIL message with pytest's full failure text; test message = short crash message |
| setup error | test FAIL with `Setup failed:` + message |
| teardown error | test FAIL with `Teardown failed:` (or `Also teardown failed:` appended) |
| `pytest.skip` / `skip` marker | SKIP with the reason |
| `xfail` that fails | SKIP with message `XFAIL: <reason>` |
| `xfail` that passes (non-strict) | PASS with message `XPASS: <reason>` |
| pytest-playwright artifacts | keyword `Playwright artifacts` with links to screenshots, `trace.zip` and videos |

Status precedence for a test: a failed or skipped setup wins; otherwise the call result is used; a failed
teardown then turns the test into FAIL.

## output.xml → rebot

At session end the plugin:

1. sets every suite's start and end time from its children,
2. saves `output.xml` into `--robot-output-dir` with generator `pytest_robot_report`,
3. runs `rebot(output.xml, log="log.html", report="report.html", loglevel="TRACE:INFO")`. All messages
   are kept, and `log.html` shows INFO and above by default, with a drop-down to see more.

rebot's own console output is suppressed. If rebot fails badly (return code 250 or higher), a
`WARNING: rebot failed with return code N` line is printed in the terminal summary.

Because the result is a normal `output.xml`, every Robot tool works on it:

```bash
rebot --name "Nightly" robot-results/output.xml                     # regenerate report/log
rebot --merge run1/output.xml run2/output.xml                        # merge runs
rebot --include req:TR-01 robot-results/output.xml                   # report for one requirement
rebot --output combined.xml pytest-run/output.xml robot-run/output.xml   # combine with real Robot runs
```

Next: [Using With Allure and ReportPortal](Using-With-Allure-and-ReportPortal.md)
