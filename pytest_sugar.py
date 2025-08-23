"""
pytest_sugar
~~~~~~~~~~~~

pytest-sugar is a plugin for pytest that changes the default look
and feel of pytest (e.g. progressbar, show tests that fail instantly).

:copyright: see LICENSE for details
:license: BSD, see LICENSE for more details.
"""

import dataclasses
import locale
import os
import re
import sys
import time
from configparser import ConfigParser  # type: ignore
from typing import Any, Dict, Generator, List, Optional, Sequence, TextIO, Tuple, Union

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.main import Session
from _pytest.nodes import Item
from _pytest.reports import BaseReport, CollectReport, TestReport
from _pytest.terminal import TerminalReporter, format_session_duration
from termcolor import colored

__version__ = "1.1.1"

LEN_RIGHT_MARGIN = 0
LEN_PROGRESS_PERCENTAGE = 5
LEN_PROGRESS_BAR_SETTING = "10"
LEN_PROGRESS_BAR: Optional[int] = None


@dataclasses.dataclass
class Theme:
    header: Optional[str] = "magenta"
    skipped: Optional[str] = "blue"
    success: Optional[str] = "green"
    warning: Optional[str] = "yellow"
    fail: Optional[str] = "red"
    error: Optional[str] = "red"
    xfailed: Optional[str] = "green"
    xpassed: Optional[str] = "red"
    progressbar: Optional[str] = "green"
    progressbar_fail: Optional[str] = "red"
    progressbar_background: Optional[str] = "grey"
    path: Optional[str] = "cyan"
    name = None
    symbol_passed: str = "✓"
    symbol_skipped: str = "s"
    symbol_failed: str = "⨯"
    symbol_failed_not_call: str = "ₓ"
    symbol_xfailed_skipped: str = "x"
    symbol_xfailed_failed: str = "X"
    symbol_unknown: str = "?"
    unknown: Optional[str] = "blue"
    symbol_rerun: Optional[str] = "R"
    rerun: Optional[str] = "blue"

    def __getitem__(self, x):
        return getattr(self, x)


THEME: Theme = Theme()
PROGRESS_BAR_BLOCKS: List[str] = [
    " ",
    "▏",
    "▎",
    "▎",
    "▍",
    "▍",
    "▌",
    "▌",
    "▋",
    "▋",
    "▊",
    "▊",
    "▉",
    "▉",
    "█",
]


def flatten(seq) -> Generator[Any, None, None]:
    for x in seq:
        if isinstance(x, (list, tuple)):
            yield from flatten(x)
        else:
            yield x


def pytest_collection_finish(session: Session) -> None:
    reporter = session.config.pluginmanager.getplugin("terminalreporter")
    if reporter:
        reporter.tests_count = len(session.items)


class DeferredXdistPlugin:
    def pytest_xdist_node_collection_finished(self, node, ids) -> None:
        terminal_reporter = node.config.pluginmanager.getplugin("terminalreporter")
        if terminal_reporter:
            terminal_reporter.tests_count = len(ids)


def pytest_deselected(items: Sequence[Item]) -> None:
    """Update tests_count to not include deselected tests"""
    if len(items) > 0:
        pluginmanager = items[0].config.pluginmanager
        terminal_reporter = pluginmanager.getplugin("terminalreporter")
        if (
            hasattr(terminal_reporter, "tests_count")
            and terminal_reporter.tests_count > 0
        ):
            terminal_reporter.tests_count -= len(items)


def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup("terminal reporting", "reporting", after="general")
    group._addoption(
        "--old-summary",
        action="store_true",
        dest="tb_summary",
        default=False,
        help=("Show tests that failed instead of one-line tracebacks"),
    )
    group._addoption(
        "--force-sugar",
        action="store_true",
        dest="force_sugar",
        default=False,
        help=("Force pytest-sugar output even when not in real terminal"),
    )
    group._addoption(
        "--sugar-trace-dir",
        action="store",
        dest="sugar_trace_dir",
        default="test-results",
        help=("Directory name for Playwright trace files (default: test-results)"),
    )
    group._addoption(
        "--sugar-no-trace",
        action="store_true",
        dest="sugar_no_trace",
        default=False,
        help=("Disable Playwright trace file detection and display"),
    )


def pytest_sessionstart(session: Session) -> None:
    global THEME, LEN_PROGRESS_BAR_SETTING
    config = ConfigParser()
    config.read(["pytest-sugar.conf", os.path.expanduser("~/.pytest-sugar.conf")])

    theme_attributes: Dict[str, Optional[str]] = {}
    fields: Tuple[dataclasses.Field, ...] = dataclasses.fields(Theme)

    for field in fields:
        key = field.name
        if not config.has_option("theme", key):
            continue

        value_str: str = config.get("theme", key).lower()
        value: Optional[str] = value_str
        if value in ("", "none"):
            value = None

        theme_attributes[key] = value

    if config.has_option("sugar", "progressbar_length"):
        LEN_PROGRESS_BAR_SETTING = config.get("sugar", "progressbar_length")

    THEME = Theme(**theme_attributes)  # type: ignore


def strip_colors(text: str) -> str:
    ansi_escape = re.compile(r"\x1b[^m]*m")
    stripped = ansi_escape.sub("", text)
    return stripped


def real_string_length(string: str) -> int:
    return len(strip_colors(string))


IS_SUGAR_ENABLED = False


@pytest.hookimpl(trylast=True)
def pytest_configure(config) -> None:
    global IS_SUGAR_ENABLED

    if sys.stdout.isatty() or config.getvalue("force_sugar"):
        IS_SUGAR_ENABLED = True

    if config.pluginmanager.hasplugin("xdist"):
        try:
            import xdist  # type: ignore # noqa: F401
        except ImportError:
            pass
        else:
            config.pluginmanager.register(DeferredXdistPlugin())

    if IS_SUGAR_ENABLED and not getattr(config, "slaveinput", None):
        # Get the standard terminal reporter plugin and replace it with our
        standard_reporter = config.pluginmanager.getplugin("terminalreporter")
        sugar_reporter = SugarTerminalReporter(standard_reporter.config)
        config.pluginmanager.unregister(standard_reporter)
        config.pluginmanager.register(sugar_reporter, "terminalreporter")


def pytest_report_teststatus(report: BaseReport) -> Optional[Tuple[str, str, str]]:
    if not IS_SUGAR_ENABLED:
        return None

    if report.passed:
        letter = colored(THEME.symbol_passed, THEME.success)
    elif report.skipped:
        letter = colored(THEME.symbol_skipped, THEME.skipped)
    elif report.failed:
        letter = colored(THEME.symbol_failed, THEME.fail)
        if report.when != "call":
            letter = colored(THEME.symbol_failed_not_call, THEME.fail)
    elif report.outcome == "rerun":
        letter = colored(THEME.symbol_rerun, THEME.rerun)
    else:
        letter = colored(THEME.symbol_unknown, THEME.unknown)

    if hasattr(report, "wasxfail"):
        if report.skipped:
            return (
                "xfailed",
                colored(THEME.symbol_xfailed_skipped, THEME.xfailed),
                "xfail",
            )
        if report.passed:
            return (
                "xpassed",
                colored(THEME.symbol_xfailed_failed, THEME.xpassed),
                "XPASS",
            )

    return report.outcome, letter, report.outcome.upper()


class SugarTerminalReporter(TerminalReporter):
    def __init__(self, config: Config, file: Union[TextIO, None] = None) -> None:
        TerminalReporter.__init__(self, config, file)
        self.paths_left = []
        self.tests_count = 0
        self.tests_taken = 0
        self.reports = []
        self.unreported_errors = []
        self.progress_blocks = []
        self.reset_tracked_lines()

    def reset_tracked_lines(self) -> None:
        self.current_lines = {}
        self.current_line_nums = {}
        self.current_line_num = 0

    def pytest_collectreport(self, report: CollectReport) -> None:
        TerminalReporter.pytest_collectreport(self, report)
        if report.location[0]:
            self.paths_left.append(os.path.join(os.getcwd(), report.location[0]))
        if report.failed:
            self.rewrite("")
            self.print_failure(report)

    def pytest_sessionstart(self, session: Session) -> None:
        self._session = session
        self._sessionstarttime = time.time()
        if self.no_header:
            return
        verinfo = ".".join(map(str, sys.version_info[:3]))
        self.write_line(
            "Test session starts "
            "(platform: %s, Python %s, pytest %s, pytest-sugar %s)"
            % (
                sys.platform,
                verinfo,
                pytest.__version__,
                __version__,
            ),
            bold=True,
        )
        if int(pytest.__version__.split(".")[0]) <= 6:
            hook_call_kwargs = {"startdir": self.startpath}
        else:
            hook_call_kwargs = {"start_path": self.startpath}
        lines = self.config.hook.pytest_report_header(
            config=self.config, **hook_call_kwargs
        )
        lines.reverse()
        for line in flatten(lines):
            self.write_line(line)

    def write_fspath_result(self, nodeid: str, res, **markup: bool) -> None:
        return

    def insert_progress(self, report: Union[CollectReport, TestReport]) -> None:
        def get_progress_bar() -> str:
            length = LEN_PROGRESS_BAR
            if not length:
                return ""

            p = float(self.tests_taken) / self.tests_count if self.tests_count else 0
            floored = int(p * length)
            rem = int(round((p * length - floored) * (len(PROGRESS_BAR_BLOCKS) - 1)))
            progressbar = "%i%% " % round(p * 100)
            # make sure we only report 100% at the last test
            if progressbar == "100% " and self.tests_taken < self.tests_count:
                progressbar = "99% "

            # if at least one block indicates failure,
            # then the percentage should reflect that
            if [1 for block, success in self.progress_blocks if not success]:
                progressbar = colored(progressbar, THEME.fail)
            else:
                progressbar = colored(progressbar, THEME.success)

            bar = PROGRESS_BAR_BLOCKS[-1] * floored
            if rem > 0:
                bar += PROGRESS_BAR_BLOCKS[rem]
            bar += " " * (LEN_PROGRESS_BAR - len(bar))

            last = 0
            last_theme = None

            progressbar_background = THEME.progressbar_background
            if progressbar_background is None:
                on_color = None
            else:
                on_color = "on_" + progressbar_background

            for block, success in self.progress_blocks:
                if success:
                    theme = THEME.progressbar
                else:
                    theme = THEME.progressbar_fail

                if last < block:
                    progressbar += colored(bar[last:block], last_theme, on_color)

                progressbar += colored(bar[block], theme, on_color)
                last = block + 1
                last_theme = theme

            if last < len(bar):
                progressbar += colored(bar[last : len(bar)], last_theme, on_color)

            return progressbar

        append_string = get_progress_bar()

        path = self.report_key(report)
        current_line = self.current_lines.get(path, "")
        line_num = self.current_line_nums.get(path, self.current_line_num)

        console_width = self._tw.fullwidth
        num_spaces = (
            console_width
            - real_string_length(current_line)
            - real_string_length(append_string)
            - LEN_RIGHT_MARGIN
        )
        full_line = current_line + " " * num_spaces
        full_line += append_string

        self.overwrite(full_line, self.current_line_num - line_num)

    def overwrite(self, line: str, rel_line_num: int) -> None:
        # Move cursor up rel_line_num lines
        if rel_line_num > 0:
            self.write("\033[%dA" % rel_line_num)

        # Overwrite the line
        self.write(f"\r{line}")

        # Return cursor to original line
        if rel_line_num > 0:
            self.write("\033[%dB" % rel_line_num)

    def get_max_column_for_test_status(self) -> int:
        assert LEN_PROGRESS_BAR

        return (
            self._tw.fullwidth
            - LEN_PROGRESS_PERCENTAGE
            - LEN_PROGRESS_BAR
            - LEN_RIGHT_MARGIN
        )

    def begin_new_line(
        self, report: Union[CollectReport, TestReport], print_filename: bool
    ) -> None:
        path = self.report_key(report)
        self.current_line_num += 1
        if len(report.fspath) > self.get_max_column_for_test_status() - 5:
            fspath = (
                "..."
                + report.fspath[-(self.get_max_column_for_test_status() - 5 - 5) :]
            )
        else:
            fspath = report.fspath
        basename = os.path.basename(fspath)
        if print_filename:
            if self.showlongtestinfo:
                test_location = report.location[0]
                test_name = report.location[2]
            else:
                test_location = fspath[0 : -len(basename)]
                test_name = fspath[-len(basename) :]
            if test_location:
                pass
                # only replace if test_location is not empty, if it is,
                # test_name contains the filename
                # FIXME: This doesn't work.
                # test_name = test_name.replace('.', '::')
            self.current_lines[path] = (
                " "
                + colored(test_location, THEME.path)
                + ("::" if self.verbosity > 0 else "")
                + colored(test_name, THEME.name)
                + " "
            )
        else:
            self.current_lines[path] = " " * (2 + len(fspath))
        self.current_line_nums[path] = self.current_line_num
        self.write("\r\n")

    def reached_last_column_for_test_status(
        self, report: Union[CollectReport, TestReport]
    ) -> bool:
        len_line = real_string_length(self.current_lines[self.report_key(report)])
        return len_line >= self.get_max_column_for_test_status()

    def pytest_runtest_logstart(self, nodeid, location) -> None:
        # Prevent locationline from being printed since we already
        # show the module_name & in verbose mode the test name.
        pass

    def pytest_runtest_logfinish(self, nodeid: str) -> None:
        # prevent the default implementation to try to show
        # pytest's default progress
        pass

    def report_key(self, report: Union[CollectReport, TestReport]) -> Any:
        """Returns a key to identify which line the report should write to."""
        return (
            (report.location or "") if self.showlongtestinfo else (report.fspath or "")
        )

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        global LEN_PROGRESS_BAR_SETTING, LEN_PROGRESS_BAR

        res = pytest_report_teststatus(report=report)
        assert res
        cat, letter, word = res
        self.stats.setdefault(cat, []).append(report)

        if not LEN_PROGRESS_BAR:
            if LEN_PROGRESS_BAR_SETTING.endswith("%"):
                LEN_PROGRESS_BAR = (
                    self._tw.fullwidth * int(LEN_PROGRESS_BAR_SETTING[:-1]) // 100
                )
            else:
                LEN_PROGRESS_BAR = int(LEN_PROGRESS_BAR_SETTING)

        self.reports.append(report)
        if report.outcome == "failed":
            print("")
            self.print_failure(report)
            # Ignore other reports or it will cause duplicated letters
        if report.when == "teardown":
            self.tests_taken += 1
            self.insert_progress(report)
            path = os.path.join(os.getcwd(), report.location[0])

        if report.when == "call" or report.skipped:
            path = self.report_key(report)
            if path not in self.current_line_nums:
                self.begin_new_line(report, print_filename=True)
            elif self.reached_last_column_for_test_status(report):
                # Print filename if another line was inserted in-between
                print_filename = (
                    self.current_line_nums[self.report_key(report)]
                    != self.current_line_num
                )
                self.begin_new_line(report, print_filename)

            self.current_lines[path] = self.current_lines[path] + letter

            block = int(
                float(self.tests_taken) * LEN_PROGRESS_BAR / self.tests_count
                if self.tests_count
                else 0
            )
            if report.failed:
                if not self.progress_blocks or self.progress_blocks[-1][0] != block:
                    self.progress_blocks.append([block, False])
                elif self.progress_blocks and self.progress_blocks[-1][0] == block:
                    self.progress_blocks[-1][1] = False
            else:
                if not self.progress_blocks or self.progress_blocks[-1][0] != block:
                    self.progress_blocks.append([block, True])

            if not letter and not word:
                return
            if self.verbosity > 0:
                markup = {"red": True}
                if isinstance(word, tuple):
                    word, markup = word
                else:
                    if report.passed:
                        markup = {"green": True}
                    elif report.skipped:
                        markup = {"yellow": True}
                    elif hasattr(report, "rerun") and isinstance(report.rerun, int):
                        markup = {"blue": True}
                line = self._locationline(str(report.fspath), *report.location)
                if hasattr(report, "node"):
                    self._tw.write("\r\n")
                    self.current_line_num += 1
                    if hasattr(report, "node"):
                        self._tw.write(f"[{report.node.gateway.id}] ")
                    self._tw.write(word, **markup)
                    self._tw.write(" " + line)
                    self.currentfspath = -2

    def count(self, key: str, when: tuple = ("call",)) -> int:
        value = self.stats.get(key)
        if value:
            return len([x for x in value if not hasattr(x, "when") or x.when in when])
        return 0

    def summary_stats(self) -> None:
        session_duration = time.time() - self._sessionstarttime
        print(f"\nResults ({format_session_duration(session_duration)}):")

        if self.count("passed") > 0:
            self.write_line(
                colored("   % 5d passed" % self.count("passed"), THEME.success)
            )

        if self.count("xpassed") > 0:
            self.write_line(
                colored("   % 5d xpassed" % self.count("xpassed"), THEME.xpassed)
            )

        if self.count("failed", when=("call",)) > 0:
            self.write_line(
                colored(
                    "   % 5d failed" % self.count("failed", when=("call",)),
                    THEME.fail,
                )
            )
            for i, report in enumerate(self.stats["failed"]):
                if report.when != "call":
                    continue

                if self.config.option.tb_summary:
                    crashline = self._get_decoded_crashline(report)
                else:
                    path = os.path.dirname(report.location[0])
                    name = os.path.basename(report.location[0])
                    lineno = self._get_lineno_from_report(report)
                    crashline = "{}{}{}:{} {}".format(
                        colored(path, THEME.path),
                        "/" if path else "",
                        colored(name, THEME.name),
                        lineno if lineno else "?",
                        colored(report.location[2], THEME.fail),
                    )

                # Add trace.zip path if it exists
                trace_path = self._find_playwright_trace(report)
                if trace_path:
                    crashline += f"\n           - 🎭 {trace_path}"
                self.write_line(f"         - {crashline}")

        if self.count("failed", when=("setup", "teardown")) > 0:
            self.write_line(
                colored(
                    "   % 5d error"
                    % (self.count("failed", when=("setup", "teardown"))),
                    THEME.error,
                )
            )

        if self.count("xfailed") > 0:
            self.write_line(
                colored("   % 5d xfailed" % self.count("xfailed"), THEME.xfailed)
            )

        if self.count("skipped", when=("call", "setup", "teardown")) > 0:
            self.write_line(
                colored(
                    "   % 5d skipped"
                    % (self.count("skipped", when=("call", "setup", "teardown"))),
                    THEME.skipped,
                )
            )

        if self.count("rerun") > 0:
            self.write_line(colored("   % 5d rerun" % self.count("rerun"), THEME.rerun))

        if self.count("deselected") > 0:
            self.write_line(
                colored("   % 5d deselected" % self.count("deselected"), THEME.warning)
            )

    def _find_playwright_trace(self, report: TestReport) -> Optional[str]:
        """
        Finds the Playwright trace file associated with a specific test report.

        Identifies the location of the trace file by using the test report's node ID
        and configuration options.
        It allows users to locate and optionally view the Playwright trace
        for failed tests.
        If Playwright trace finding is specifically disabled, or the trace file
        does not exist for the given test, no output is returned.

        Parameters:
        report (TestReport):
        The test report containing details about the test execution, including
        the node ID.

        Returns:
        Optional[str]: A string containing command to view the Playwright trace
        or
        None if trace is not enabled, the file does not exist, or an exception occurs.
        """
        # Check if trace finding is disabled
        if self.config.option.sugar_no_trace:
            return None

        try:
            # Extract test information from the report
            nodeid = report.nodeid

            # Handle Node ID conversion to trace name format
            trace_dir_name = self._convert_node_to_trace_name(nodeid)

            # Construct the expected trace directory path
            cwd = os.getcwd()
            trace_dir_name_from_config = self.config.option.sugar_trace_dir
            test_results_dir = os.path.join(cwd, trace_dir_name_from_config)
            trace_dir = os.path.join(test_results_dir, trace_dir_name)
            trace_file = os.path.join(trace_dir, "trace.zip")

            # Check if the trace file exists
            if os.path.exists(trace_file):
                # Provide the relative path and a command to view the trace
                trace_file_relative = os.path.relpath(trace_file, cwd).replace(
                    "\\", "/"
                )

                # Create a command to open the trace with Playwright for Python
                view_command = f"playwright show-trace {trace_file_relative}"

                # Display unzip command
                command_display = colored(view_command, THEME.warning)
                return command_display
            return None

        except (OSError, AttributeError):
            return None

    @staticmethod
    def _convert_node_to_trace_name(nodeid: str) -> str:
        # Convert the nodeid to the expected trace directory name
        trace_dir_name = (
            nodeid.replace("/", "-")
            .replace("\\", "-")
            .replace("::", "-")
            .replace("[", "-")
            .replace("]", "")
            .replace("_", "-")
            .replace(".", "-")
        )
        return trace_dir_name.lower()

    def _get_decoded_crashline(self, report: CollectReport) -> str:
        crashline = self._getcrashline(report)

        if hasattr(crashline, "decode"):
            encoding = locale.getpreferredencoding()
            try:
                crashline = crashline.decode(encoding)
            except UnicodeDecodeError:
                encoding = "utf-8"
                crashline = crashline.decode(encoding, errors="replace")

        return crashline

    def _get_lineno_from_report(self, report: CollectReport) -> int:
        # Doctest failures in pytest>3.10 are stored in
        # reprlocation_lines, a list of (ReprFileLocation, lines)
        try:
            location, lines = report.longrepr.reprlocation_lines[0]  # type: ignore
            return location.lineno
        except AttributeError:
            pass
        # Doctest failure reports have lineno=None at least up to
        # pytest==3.0.7, but it is available via longrepr object.
        try:
            return report.longrepr.reprlocation.lineno  # type: ignore
        except AttributeError:
            lineno = report.location[1]
            if lineno is not None:
                lineno += 1
            return lineno

    def summary_failures(self) -> None:
        # Prevent failure summary from being shown since we already
        # show the failure instantly after failure has occurred.
        pass

    def summary_errors(self) -> None:
        # Prevent error summary from being shown since we already
        # show the error instantly after error has occurred.
        pass

    def print_failure(self, report: Union[CollectReport, TestReport]) -> None:
        # https://github.com/Frozenball/pytest-sugar/issues/34
        if hasattr(report, "wasxfail"):
            return

        if self.config.option.tbstyle != "no":
            if self.config.option.tbstyle == "line":
                line = self._getcrashline(report)
                self.write_line(line)
            else:
                msg = self._getfailureheadline(report)
                # "when" was unset before pytest 4.2 for collection errors.
                when = getattr(report, "when", "collect")
                if when == "collect":
                    msg = "ERROR collecting " + msg
                elif when == "setup":
                    msg = "ERROR at setup of " + msg
                elif when == "teardown":
                    msg = "ERROR at teardown of " + msg
                self.write_line("")
                self.write_sep("―", msg)
                self._outrep_summary(report)
        self.reset_tracked_lines()
