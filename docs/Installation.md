# Installation

## Requirements

| Package | Tested version | Why |
|---|---|---|
| Python | 3.13 locally, 3.12 in CI | 3.12 or newer recommended |
| `robotframework` | 7.5 (`>=7.0` required) | Builds the result model, writes `output.xml`, runs `rebot` |
| `pytest` | 9.2 (`>=8.0`) | Test runner |
| `pytest-playwright` | 0.10 (`>=0.5`) | Optional, but needed for failure screenshots and artifact links |
| Playwright | 1.64 | Browser automation |

The plugin itself only needs `pytest` and `robotframework`. If Robot Framework is missing, importing the
plugin fails with: `pytest_robot_report needs Robot Framework: pip install robotframework`.

Linking Playwright artifacts uses `python-slugify`, which `pytest-playwright` already installs.

## Try the sample project

```bash
git clone https://github.com/qabughunter/pytest-robot-report.git
cd pytest-robot-report
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium          # on Linux CI: playwright install --with-deps chromium
pytest --robot-report
```

Expected result: 2 passed, 1 failed. The failure is intentional
(`test_inventory_has_ten_items_intentional_failure` expects 10 products, the shop has 6).
The terminal ends with:

```
---------------------------- Robot Framework report ----------------------------
Robot output: .../robot-results/output.xml
Robot report: .../robot-results/report.html
Robot log:    .../robot-results/log.html
```

## Add it to your own project

1. Copy `pytest_robot_report.py` into your project's root folder, the same folder as your top-level
   `conftest.py` (or `pytest.ini`), so it can be imported.
2. Install Robot Framework into the same virtual environment: `pip install robotframework`
3. Enable the plugin in one way only. Either add this to the top of `conftest.py`:
   ```python
   pytest_plugins = ["pytest_robot_report"]
   ```
   or leave `conftest.py` alone and run `pytest -p pytest_robot_report --robot-report`.
4. Run `pytest --robot-report` and open `robot-results/log.html`.

If `pytest_robot_report` can't be imported, add `pythonpath = .` under `[pytest]` in `pytest.ini`
(this repo does that).

Next: [Usage](Usage.md)
