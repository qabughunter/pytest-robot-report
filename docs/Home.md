# pytest-robot-report wiki

Write tests in Python with pytest and Playwright, and read the results in Robot Framework's
`report.html` and `log.html`.

## Pages

1. [Installation](Installation.md): requirements and setup
2. [Usage](Usage.md): steps, logging, screenshots, the `step` fixture, tags and traceability
3. [Configuration](Configuration.md): every command-line option, and how to enable the plugin
4. [How It Works](How-It-Works.md): how pytest results map to Robot's model, and `output.xml` → `rebot`
5. [Using With Allure and ReportPortal](Using-With-Allure-and-ReportPortal.md): running all three reports at once
6. [CI: GitHub Actions](CI-GitHub-Actions.md): a workflow that runs tests and uploads the report
7. [Troubleshooting](Troubleshooting.md): common problems and fixes
8. [Limitations](Limitations.md): what isn't supported yet

## In 30 seconds

```bash
pip install robotframework pytest pytest-playwright
playwright install chromium
# copy pytest_robot_report.py next to conftest.py, then in conftest.py:
#   pytest_plugins = ["pytest_robot_report"]
pytest --robot-report
xdg-open robot-results/log.html     # macOS: open, Windows: start
```

## About these pages

This `docs/` folder is the project's wiki. GitHub's Wiki tab can't be written through the API, so the
pages live in the repository instead. To use the Wiki tab, create a wiki page for each file here with
the same name (without `.md`); `Home.md` becomes the wiki home page. Inside the Wiki tab, links work
without the `.md` extension, for example `[Usage](Usage)`.
