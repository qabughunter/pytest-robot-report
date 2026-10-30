# Usage

Everything below comes from `pytest_robot_report.py`. Import what you need:

```python
from pytest_robot_report import robot_step, robot_log, robot_screenshot
```

When the plugin is off (no `--robot-report`), all three do nothing, so the same tests run normally
with plain `pytest`.

## Steps: `robot_step`

```python
robot_step(name, *args, doc="")
```

A context manager. Each `with robot_step(...)` block becomes a keyword (step) in `log.html`, with its
arguments, start and end time, and status.

```python
def test_checkout(page):
    with robot_step("Open login page", "https://www.saucedemo.com"):
        page.goto("https://www.saucedemo.com")
    with robot_step("Log in", "standard_user", doc="Logs in through the form"):
        with robot_step("Type username"):            # steps can be nested as deep as you like
            page.get_by_placeholder("Username").fill("standard_user")
        with robot_step("Type password"):
            page.get_by_placeholder("Password").fill("secret_sauce")
        page.get_by_role("button", name="Login").click()
```

- `args` are converted with `str()` and shown as the keyword's arguments.
- If the block raises, the step is marked **FAIL**, the error (`ExceptionType: message`) is logged inside
  it, and the exception carries on so pytest still fails the test. Every enclosing step is marked FAIL too.
- If the block calls `pytest.skip()`, the step is marked **SKIP**.
- Steps used inside fixtures land in the test's **setup** or **teardown** keyword (see below).

### Put steps in page objects

The cleanest pattern is to put steps inside page object methods, as in [`pages/login_page.py`](../pages/login_page.py):

```python
class LoginPage:
    def __init__(self, page):
        self.page = page
        self.username = page.get_by_placeholder("Username")
        self.password = page.get_by_placeholder("Password")
        self.login_button = page.get_by_role("button", name="Login")

    def login(self, user, password):
        with robot_step("Log in", user):
            self.username.fill(user)
            self.password.fill(password)
            self.login_button.click()
```

Then every test that calls `login.login(...)` gets a readable "Log in | standard_user" step.

## The `step` fixture

If you'd rather not import anything, request the `step` fixture. It is `robot_step` itself:

```python
def test_cart(page, step):
    with step("Add backpack to cart"):
        page.get_by_role("button", name="Add to cart").first.click()
```

## Messages: `robot_log` and `logging`

```python
robot_log(message, level="INFO", html=False)
```

Adds a message to the step that is currently running (or to the test, if no step is open).

```python
robot_log("Cart has 1 item")
robot_log("Price looks wrong", level="WARN")
robot_log("<b>Order id:</b> 1234", html=True)
```

`level` is a Robot Framework log level: `TRACE`, `DEBUG`, `INFO`, `WARN` or `ERROR`.

Standard Python `logging` works too, and is usually better because it also works without the plugin:

```python
import logging
log = logging.getLogger(__name__)

log.info("Opened %s", page.url)        # INFO message inside the current step
log.warning("Slow response")           # WARN
```

Each record appears as `[logger.name] message` in the step that was running when it was logged.
Python levels map to Robot levels: `ERROR`/`CRITICAL` → `ERROR`, `WARNING` → `WARN`, `INFO` → `INFO`,
`DEBUG` → `DEBUG`, anything lower → `TRACE`. Records below `--robot-log-level` (default `INFO`) are not
captured; see [Configuration](Configuration.md).

`log.html` keeps every captured level but shows `INFO` and above by default. Use the
**Log level** drop-down at the top of `log.html` to reveal `DEBUG` and `TRACE` messages.

`print()` output is also captured, but as one "Captured stdout call" message per phase, not inside the
step that printed it. See [Limitations](Limitations.md).

## Screenshots: `robot_screenshot`

```python
robot_screenshot(page, title="Screenshot", width=800)
```

Takes a viewport screenshot of a Playwright `page` and embeds it (as base64) in the current step, with
`title` in bold above it and the image shown `width` pixels wide.

```python
with robot_step("Checkout overview"):
    page.get_by_role("button", name="Checkout").click()
    robot_screenshot(page, "Checkout page")
```

If the screenshot can't be taken (for example the page is closed), a `WARN` message is logged instead.

### Automatic screenshot on failure

When a test fails in its call phase and it uses the `page` fixture, the plugin embeds a
"Screenshot at failure" in the test automatically. Turn this off with `--robot-no-screenshot`.

## Fixtures: setup and teardown

Work done in fixtures is recorded under two keywords on each test:

- **pytest fixture setup**: steps, logs and errors from the setup phase
- **pytest fixture teardown**: steps, logs and errors from the teardown phase

They only appear in the log when they contain something or failed. If setup fails, the test is FAIL
with `Setup failed: ...`. If teardown fails, the test is FAIL with `Teardown failed: ...` (or
`Also teardown failed: ...` is added to an existing failure).

```python
@pytest.fixture
def logged_in(page):
    with robot_step("Log in as standard_user"):
        LoginPage(page).open()
        LoginPage(page).login("standard_user", "secret_sauce")
    yield page
    with robot_step("Log out"):
        ...
```

## Tags and traceability with markers

Every pytest marker on a test becomes a Robot Framework **tag**, so you can filter by it in
`report.html` and get a statistics row per tag.

| Marker | Robot tag |
|---|---|
| `@pytest.mark.smoke` | `smoke` |
| `@pytest.mark.req("TR-01")` | `req:TR-01` |
| `@pytest.mark.req("TR-01", "TR-07")` | `req:TR-01`, `req:TR-07` |
| `@pytest.mark.robot_tag("checkout")` | `checkout` (no prefix) |
| marker with only keyword arguments | the marker name |

Rules, from the plugin's `_tags()` function:

- A marker with string or number arguments gives one `name:value` tag per argument. `robot_tag` gives the bare value.
- A marker without simple arguments gives a tag with just its name.
- pytest machinery markers are ignored: `parametrize`, `usefixtures`, `filterwarnings`, `skipif`, `skip`,
  `xfail`, `browser_context_args`, `only_browser`, `skip_browser`.
- Markers on classes and modules (`pytestmark`) are inherited, because the plugin reads all markers on the item.
- Tags are de-duplicated and sorted.

### A requirement traceability matrix

Register a `req` marker in `pytest.ini` (this repo does), then tag each test with the requirement it covers:

```ini
[pytest]
markers =
    smoke: quick checks
    req(id): requirement ID for traceability
```

```python
@pytest.mark.smoke
@pytest.mark.req("TR-01")
def test_valid_login_shows_products(page):
    """A standard user can log in and sees the product list."""
    ...
```

In `report.html`, **Statistics by Tag** then shows a row per requirement (`req:TR-01`, `req:TR-02`, ...)
with its pass and fail counts. Click a tag to list its tests. That table is your traceability matrix.
`robot_tag` is registered by the plugin; register your own markers such as `req` and `smoke` to avoid
`PytestUnknownMarkWarning`.

## Documentation

- A test function's docstring becomes the Robot test documentation.
- A test module's (or class's) docstring becomes the suite documentation.

Next: [Configuration](Configuration.md)
