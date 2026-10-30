# CI: GitHub Actions

This repository ships a working workflow at
[`.github/workflows/tests.yml`](../.github/workflows/tests.yml). It runs on every push to `main`,
on pull requests, and on demand (**Actions → tests → Run workflow**).

```yaml
name: tests

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          playwright install --with-deps chromium

      - name: Run tests
        run: >
          pytest --robot-report
          --deselect tests/test_login.py::test_inventory_has_ten_items_intentional_failure

      - name: Upload Robot Framework report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: robot-results
          path: |
            robot-results/
            test-results/
          if-no-files-found: warn
```

## About the intentionally failing test

`tests/test_login.py::test_inventory_has_ten_items_intentional_failure` fails on purpose so you can see
a failure, its traceback and screenshot in `log.html` when you run the sample locally.

CI **deselects** that one test instead of hiding failures with `continue-on-error`. That way:

- the build is green when everything real passes, and
- a red build always means a real failure, not the demo.

The deselected test doesn't appear in the CI report. To see the failure demo, run `pytest --robot-report`
locally, or run the workflow on a branch where you remove the `--deselect` line.

In your own project, drop the `--deselect` line and run your whole suite.

## Getting the report

1. Open the workflow run in the **Actions** tab.
2. Under **Artifacts**, download `robot-results`.
3. Unzip it and open `robot-results/log.html` or `robot-results/report.html`.

The artifact includes `test-results/` too, because `log.html` links Playwright screenshots and traces by
relative path (`../test-results/...`). Keep both folders together after unzipping.
The upload step uses `if: always()`, so the report is uploaded even when tests fail.

## Variations

- **Run the plugin's own checks:** `pytest selftest --robot-report --robot-output-dir robot-selftest`.
  That suite contains deliberate setup and teardown errors, so it exits non-zero by design; use it for
  checking the report by eye, not as a CI gate.
- **Different browser:** `playwright install --with-deps firefox` and `pytest --browser firefox --robot-report`.
- **Report name per build:** `pytest --robot-report --robot-name "Build ${{ github.run_number }}"`.
- **Secrets:** pass credentials through `env:` from repository secrets
  (`${{ secrets.APP_PASSWORD }}`), never commit a `.env` file.

Next: [Troubleshooting](Troubleshooting.md)
