# Using with Allure and ReportPortal

This plugin doesn't replace other reporters. It only adds its own hooks and writes its own folder, so
Allure, ReportPortal, `pytest-html` and JUnit XML can all run in the same `pytest` command.

```bash
pytest --robot-report --alluredir allure-results --reportportal --junitxml junit.xml
```

Checked: a run with `allure-pytest` and `pytest-reportportal` installed alongside this plugin produced
both `allure-results/` and the Robot report.

## Allure

```bash
pip install allure-pytest
pytest --robot-report --alluredir allure-results
allure serve allure-results          # needs the Allure command-line tool
```

Allure steps and Robot steps are separate APIs. To get the same step in both reports, nest them, or wrap
them in one helper used by your page objects:

```python
import contextlib
import allure
from pytest_robot_report import robot_step

@contextlib.contextmanager
def step(name, *args):
    title = name if not args else f"{name}: {', '.join(map(str, args))}"
    with allure.step(title), robot_step(name, *args):
        yield
```

Python `logging` messages show up in both: Allure attaches pytest's captured log, and this plugin places
each record inside the running Robot step.

## ReportPortal

```bash
pip install pytest-reportportal
pytest --robot-report --reportportal
```

Configure `rp_endpoint`, `rp_project`, `rp_launch` and the API key the way you normally do
(see https://github.com/reportportal/agent-python-pytest). Keep the API key in an environment variable
or a secret store, never in the repository.

ReportPortal is a shared, long-term dashboard. The Robot report is a self-contained pair of HTML files
for one run, easy to attach to a CI build or send to someone.

## Which one when

| Need | Use |
|---|---|
| One file you can email or attach to a build, with steps, logs and screenshots | Robot `log.html` / `report.html` |
| Trends over time, categories, rich attachments | Allure (with history) |
| Team dashboard, failure triage across many runs | ReportPortal |
| CI test counts (GitHub, Jenkins, GitLab) | `--junitxml` |

## Things to keep apart

- Use different output folders: `robot-results/`, `allure-results/`, `test-results/` (Playwright).
- Don't use `pytest -n` if you want the Robot report; it's not supported (see [Limitations](Limitations.md)).

Next: [CI: GitHub Actions](CI-GitHub-Actions.md)
