"""pytest plugin: write pytest results as Robot Framework output.xml, report.html and log.html.

Enable with:  pytest -p pytest_robot_report --robot-report
or put  ``pytest_plugins = ["pytest_robot_report"]``  in your top-level conftest.py
and run  ``pytest --robot-report``.

In tests:
    from pytest_robot_report import robot_step, robot_log, robot_screenshot

    def test_login(page):
        with robot_step("Open login page", "https://www.saucedemo.com"):
            page.goto("https://www.saucedemo.com")
        robot_log("Some useful info")

Built on Robot Framework's public result model (robot.result.*) and robot.rebot.
Tested with Robot Framework 7.5, pytest 9.2, pytest-playwright 0.10.
"""
from __future__ import annotations

import base64
import contextlib
import inspect
import io
import logging
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

import pytest

try:
    from robot.result import Keyword, Result, TestSuite
    from robot import rebot
except ImportError as exc:  # pragma: no cover
    raise ImportError("pytest_robot_report needs Robot Framework: pip install robotframework") from exc

# Markers that are pytest machinery, not useful as Robot tags.
_IGNORED_MARKS = {"parametrize", "usefixtures", "filterwarnings", "skipif", "skip", "xfail",
                  "browser_context_args", "only_browser", "skip_browser"}

_LEVELS = [(logging.ERROR, "ERROR"), (logging.WARNING, "WARN"), (logging.INFO, "INFO"),
           (logging.DEBUG, "DEBUG"), (0, "TRACE")]


def _robot_level(levelno: int) -> str:
    for threshold, name in _LEVELS:
        if levelno >= threshold:
            return name
    return "TRACE"


def _ts(epoch: float | None = None) -> datetime:
    return datetime.fromtimestamp(epoch) if epoch else datetime.now()


class _State:
    """Holds the run being recorded. One per pytest session."""

    def __init__(self) -> None:
        self.enabled = False
        self.root: TestSuite | None = None
        self.suites: dict[tuple, TestSuite] = {}
        self.current: "_TestRecord | None" = None
        # Stack of containers that new steps/messages go into: TestCase or Keyword.
        self.stack: list[Any] = []

    def target(self):
        return self.stack[-1] if self.stack else None


_STATE = _State()


class _TestRecord:
    def __init__(self, test) -> None:
        self.test = test
        self.setup_kw = Keyword(name="pytest fixture setup", owner="pytest", type=Keyword.SETUP, status="PASS")
        self.teardown_kw = Keyword(name="pytest fixture teardown", owner="pytest", type=Keyword.TEARDOWN, status="PASS")
        self.phase_status: dict[str, str] = {}
        self.messages: dict[str, str] = {}


# ----------------------------------------------------------------------------- public API

def robot_log(message: str, level: str = "INFO", html: bool = False) -> None:
    """Add a message to the current step (or test) in log.html. No-op if the plugin is off."""
    target = _STATE.target()
    if target is not None:
        target.body.create_message(str(message), level=level, html=html, timestamp=datetime.now())


@contextlib.contextmanager
def robot_step(name: str, *args: Any, doc: str = "") -> Iterator[None]:
    """Context manager that shows up as a keyword (step) in log.html. Steps can be nested."""
    target = _STATE.target()
    if target is None:  # plugin disabled or used outside a test
        yield
        return
    kw = target.body.create_keyword(name=name, owner="Step", args=[str(a) for a in args], doc=doc,
                                    status="PASS", start_time=datetime.now())
    _STATE.stack.append(kw)
    try:
        yield
    except pytest.skip.Exception as exc:
        kw.status, kw.message = "SKIP", str(exc)
        raise
    except BaseException as exc:
        kw.status = "FAIL"
        kw.message = f"{type(exc).__name__}: {exc}".strip()
        kw.body.create_message(kw.message, level="FAIL", timestamp=datetime.now())
        raise
    finally:
        kw.end_time = datetime.now()
        if _STATE.stack and _STATE.stack[-1] is kw:
            _STATE.stack.pop()


def robot_screenshot(page: Any, title: str = "Screenshot", width: int = 800) -> None:
    """Embed a Playwright page screenshot (base64) in the current step."""
    if _STATE.target() is None:
        return
    try:
        png = page.screenshot(full_page=False)
    except Exception as exc:  # page closed etc.
        robot_log(f"Could not take screenshot: {exc}", level="WARN")
        return
    _embed_png(png, title, width)


def _embed_png(png: bytes, title: str, width: int = 800) -> None:
    data = base64.b64encode(png).decode("ascii")
    robot_log(f'<b>{title}</b><br><img src="data:image/png;base64,{data}" width="{width}">', html=True)


@pytest.fixture
def step():
    """Fixture form of robot_step:  ``with step("Click login"): ...``"""
    return robot_step


# ----------------------------------------------------------------------------- logging capture

class _RobotLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        target = _STATE.target()
        if target is None:
            return
        try:
            msg = self.format(record)
        except Exception:
            msg = record.getMessage()
        target.body.create_message(f"[{record.name}] {msg}", level=_robot_level(record.levelno),
                                   timestamp=_ts(record.created))


_HANDLER = _RobotLogHandler(level=logging.DEBUG)
_HANDLER.setFormatter(logging.Formatter("%(message)s"))


# ----------------------------------------------------------------------------- pytest hooks

def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("robot-report", "Robot Framework report")
    group.addoption("--robot-report", action="store_true", default=False,
                    help="Write Robot Framework output.xml, report.html and log.html.")
    group.addoption("--robot-output-dir", default="robot-results",
                    help="Directory for output.xml/report.html/log.html (default: robot-results).")
    group.addoption("--robot-name", default=None, help="Top-level suite name (default: rootdir name).")
    group.addoption("--robot-log-level", default="INFO",
                    help="Lowest Python logging level captured into log.html (default: INFO).")
    group.addoption("--robot-no-screenshot", action="store_true", default=False,
                    help="Do not embed a screenshot of the Playwright 'page' when a test fails.")


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "robot_tag(name): extra Robot Framework tag (any marker becomes a tag)")
    if not config.getoption("--robot-report"):
        return
    if hasattr(config, "workerinput"):  # pytest-xdist worker: not supported, master writes nothing either
        return
    if getattr(config.option, "numprocesses", None):
        import warnings
        warnings.warn(pytest.PytestWarning("pytest_robot_report does not support pytest-xdist (-n); no Robot report written."))
        return
    _STATE.enabled = True
    name = config.getoption("--robot-name") or Path(str(config.rootpath)).name
    _STATE.root = TestSuite(name=name, source=str(config.rootpath), start_time=datetime.now())
    _HANDLER.setLevel(getattr(logging, str(config.getoption("--robot-log-level")).upper(), logging.INFO))


def _suite_for(item: pytest.Item) -> TestSuite:
    """Directories -> module -> classes become nested suites."""
    root = _STATE.root
    rel = Path(item.nodeid.split("::")[0])
    parts: list[tuple[str, str, Any]] = [(p, "dir", None) for p in rel.parts[:-1]]
    parts.append((rel.name, "module", item.module if hasattr(item, "module") else None))
    for node in item.listchain():
        if isinstance(node, pytest.Class):
            parts.append((node.name, "class", node.obj))
    key: tuple = ()
    parent = root
    for name, kind, obj in parts:
        key += (name,)
        suite = _STATE.suites.get(key)
        if suite is None:
            display = name
            if kind == "module":
                display = Path(name).stem
                for prefix in ("test_",):
                    if display.startswith(prefix):
                        display = display[len(prefix):]
                display = display.replace("_", " ").title()
            elif kind == "dir":
                display = name.replace("_", " ").title()
            doc = inspect.getdoc(obj) or "" if obj is not None else ""
            source = str(Path(str(item.config.rootpath)) / Path(*key)) if kind != "class" else None
            suite = parent.suites.create(name=display, doc=doc, source=source)
            _STATE.suites[key] = suite
        parent = suite
    return parent


def _tags(item: pytest.Item) -> list[str]:
    tags: list[str] = []
    for mark in item.iter_markers():
        if mark.name in _IGNORED_MARKS:
            continue
        simple = [a for a in mark.args if isinstance(a, (str, int, float))]
        if simple:
            tags.extend(f"{mark.name}:{a}" if mark.name != "robot_tag" else str(a) for a in simple)
        else:
            tags.append(mark.name)
    return sorted(set(tags))


def _start_test(item: pytest.Item) -> None:
    suite = _suite_for(item)
    doc = inspect.getdoc(getattr(item, "obj", None)) or "" if getattr(item, "obj", None) else ""
    test = suite.tests.create(name=item.name, doc=doc, tags=_tags(item), status="PASS",
                              lineno=(item.location[1] + 1) if item.location[1] is not None else None,
                              start_time=datetime.now())
    _STATE.current = _TestRecord(test)


def _phase_container(phase: str):
    rec = _STATE.current
    return {"setup": rec.setup_kw, "call": rec.test, "teardown": rec.teardown_kw}[phase]


@contextlib.contextmanager
def _phase(phase: str):
    if not _STATE.enabled or _STATE.current is None:
        yield
        return
    container = _phase_container(phase)
    if phase != "call":
        container.start_time = datetime.now()
    _STATE.stack = [container]
    root_logger = logging.getLogger()
    old_level = root_logger.level
    if root_logger.level > _HANDLER.level or root_logger.level == logging.NOTSET:
        root_logger.setLevel(_HANDLER.level)
    root_logger.addHandler(_HANDLER)
    try:
        yield
    finally:
        root_logger.removeHandler(_HANDLER)
        root_logger.setLevel(old_level)
        if phase != "call":
            container.end_time = datetime.now()


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_setup(item):
    with _phase("setup"):
        yield


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_call(item):
    with _phase("call"):
        yield


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_teardown(item, nextitem):
    with _phase("teardown"):
        yield


def _short_message(rep: pytest.TestReport) -> str:
    lr = rep.longrepr
    if rep.skipped and isinstance(lr, tuple) and len(lr) == 3:
        return str(lr[2]).removeprefix("Skipped: ")
    crash = getattr(lr, "reprcrash", None)
    if crash is not None and getattr(crash, "message", None):
        return crash.message
    text = str(lr or "").strip()
    return text.splitlines()[-1] if text else ""


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call):
    outcome = yield
    if not _STATE.enabled or _STATE.current is None:
        return
    rep: pytest.TestReport = outcome.get_result()
    rec = _STATE.current
    phase = rep.when
    container = _phase_container(phase)
    now = datetime.now()

    # Captured stdout / stderr (logging is captured live by our handler).
    for title, content in rep.sections:
        if not content.strip() or "log" in title.lower():
            continue
        if title.split()[-1] == phase:
            level = "WARN" if "stderr" in title else "INFO"
            container.body.create_message(f"{title}:\n{content.rstrip()}", level=level, timestamp=now)

    wasxfail = getattr(rep, "wasxfail", None)
    if rep.failed:
        status = "FAIL"
    elif rep.skipped:
        status = "SKIP"
    else:
        status = "PASS"
    message = _short_message(rep) if status != "PASS" else ""
    if wasxfail is not None:
        message = f"XFAIL: {wasxfail}" if rep.skipped else f"XPASS: {wasxfail}"

    if status == "FAIL":
        container.body.create_message(rep.longreprtext or message, level="FAIL", timestamp=now)
        if phase == "call" and not item.config.getoption("--robot-no-screenshot"):
            page = getattr(item, "funcargs", {}).get("page")
            if page is not None:
                _STATE.stack = [container]
                robot_screenshot(page, "Screenshot at failure")
    elif status == "SKIP" and message:
        container.body.create_message(message, level="SKIP", timestamp=now)

    if phase != "call":
        container.status = status
        container.message = message
    rec.phase_status[phase] = status
    rec.messages[phase] = message


def _attach_playwright_artifacts(item: pytest.Item, rec: _TestRecord) -> None:
    """Link pytest-playwright artifacts (trace.zip, video, screenshots) saved under --output."""
    try:
        out = item.config.getoption("--output")
    except ValueError:
        return  # pytest-playwright not installed
    try:
        from slugify import slugify
    except ImportError:
        return
    folder = Path(out).absolute() / slugify(item.nodeid)
    if not folder.is_dir():
        return
    report_dir = Path(item.config.getoption("--robot-output-dir")).absolute()
    links = []
    for f in sorted(folder.iterdir()):
        rel = os.path.relpath(f, report_dir).replace(os.sep, "/")
        if f.suffix == ".png":
            links.append(f'<b>{f.name}</b><br><a href="{rel}"><img src="{rel}" width="400"></a>')
        elif f.suffix == ".zip":
            links.append(f'Playwright trace: <a href="{rel}">{f.name}</a> '
                         f'(open with <code>playwright show-trace {f}</code> or https://trace.playwright.dev)')
        else:
            links.append(f'<a href="{rel}">{f.name}</a>')
    if links:
        kw = rec.test.body.create_keyword(name="Playwright artifacts", owner="pytest-playwright",
                                          status="PASS", start_time=datetime.now(), end_time=datetime.now())
        for html in links:
            kw.body.create_message(html, html=True, timestamp=datetime.now())


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_protocol(item: pytest.Item, nextitem):
    if not _STATE.enabled:
        yield
        return
    _start_test(item)
    yield
    if _STATE.current is None:
        return
    rec = _STATE.current
    _attach_playwright_artifacts(item, rec)
    test = rec.test
    st, msg = rec.phase_status, rec.messages
    if st.get("setup") == "FAIL":
        test.status, test.message = "FAIL", f"Setup failed:\n{msg['setup']}"
    elif st.get("setup") == "SKIP":
        test.status, test.message = "SKIP", msg["setup"]
    else:
        test.status, test.message = st.get("call", "PASS"), msg.get("call", "")
    if st.get("teardown") == "FAIL":
        if test.status == "FAIL":
            test.message += f"\n\nAlso teardown failed:\n{msg['teardown']}"
        else:
            test.status, test.message = "FAIL", f"Teardown failed:\n{msg['teardown']}"
    if rec.setup_kw.body or rec.setup_kw.status != "PASS":
        test.setup = rec.setup_kw
    if rec.teardown_kw.body or rec.teardown_kw.status != "PASS":
        test.teardown = rec.teardown_kw
    test.end_time = datetime.now()
    _STATE.current = None
    _STATE.stack = []


def _fix_suite_times(suite: TestSuite) -> None:
    for child in suite.suites:
        _fix_suite_times(child)
    starts = [t.start_time for t in suite.tests if t.start_time] + [s.start_time for s in suite.suites if s.start_time]
    ends = [t.end_time for t in suite.tests if t.end_time] + [s.end_time for s in suite.suites if s.end_time]
    if starts and suite.start_time is None:
        suite.start_time = min(starts)
    if ends:
        suite.end_time = max(ends)


def pytest_sessionfinish(session: pytest.Session, exitstatus) -> None:
    if not _STATE.enabled or _STATE.root is None:
        return
    config = session.config
    out_dir = Path(config.getoption("--robot-output-dir")).absolute()
    out_dir.mkdir(parents=True, exist_ok=True)
    root = _STATE.root
    root.end_time = datetime.now()
    _fix_suite_times(root)
    output = out_dir / "output.xml"
    Result(suite=root, generator="pytest_robot_report").save(output)
    rc = rebot(str(output), outputdir=str(out_dir), log="log.html", report="report.html",
               loglevel="TRACE:INFO", stdout=io.StringIO(), stderr=io.StringIO())
    _STATE.summary = [f"Robot output: {output}", f"Robot report: {out_dir / 'report.html'}", f"Robot log:    {out_dir / 'log.html'}"]
    if rc >= 250:
        _STATE.summary.append(f"WARNING: rebot failed with return code {rc}")


def pytest_terminal_summary(terminalreporter) -> None:
    lines = getattr(_STATE, "summary", None)
    if lines:
        terminalreporter.write_sep("-", "Robot Framework report")
        for line in lines:
            terminalreporter.write_line(line)
