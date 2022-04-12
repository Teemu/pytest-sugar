# -*- coding: utf-8 -*-
"""
pytest_sugar
~~~~~~~~~~~~

pytest-sugar is a plugin for pytest that changes the default look
and feel of pytest (e.g. progressbar, show tests that fail instantly).

:copyright: see LICENSE for details
:license: BSD, see LICENSE for more details.
"""
from __future__ import unicode_literals
import locale
import os
import re
import sys
from packaging.version import parse

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser

from termcolor import colored

import py
import pytest
from _pytest.terminal import TerminalReporter


__version__ = '0.9.5'

LEN_RIGHT_MARGIN = 0
LEN_PROGRESS_PERCENTAGE = 5
LEN_PROGRESS_BAR_SETTING = '10'
LEN_PROGRESS_BAR = None
THEME = {
    'header': 'magenta',
    'skipped': 'blue',
    'success': 'green',
    'warning': 'yellow',
    'fail': 'red',
    'error': 'red',
    'xfailed': 'green',
    'xpassed': 'red',
    'progressbar': 'green',
    'progressbar_fail': 'red',
    'progressbar_background': 'grey',
    'path': 'cyan',
    'name': None,
    'symbol_passed': '✓',
    'symbol_skipped': 's',
    'symbol_failed': '⨯',
    'symbol_failed_not_call': 'ₓ',
    'symbol_xfailed_skipped': 'x',
    'symbol_xfailed_failed': 'X',
    'symbol_unknown': '?',
    'unknown': 'blue',
    'symbol_rerun': 'R',
    'rerun': 'blue',
}
PROGRESS_BAR_BLOCKS = [
    ' ', '▏', '▎', '▎', '▍', '▍', '▌', '▌', '▋', '▋', '▊', '▊', '▉', '▉', '█',
]


def flatten(seq):
    for x in seq:
        if isinstance(x, (list, tuple)):
            for y in flatten(x):
                yield y
        else:
            yield x


def pytest_runtestloop(session):
    reporter = session.config.pluginmanager.getplugin('terminalreporter')
    if reporter:
        reporter.tests_count = len(session.items)


class DeferredXdistPlugin(object):
    def pytest_xdist_node_collection_finished(self, node, ids):
        terminal_reporter = node.config.pluginmanager.getplugin(
            'terminalreporter'
        )
        if terminal_reporter:
            terminal_reporter.tests_count = len(ids)


def pytest_deselected(items):
    """ Update tests_count to not include deselected tests """
    if len(items) > 0:
        pluginmanager = items[0].config.pluginmanager
        terminal_reporter = pluginmanager.getplugin('terminalreporter')
        if (hasattr(terminal_reporter, 'tests_count')
                and terminal_reporter.tests_count > 0):
            terminal_reporter.tests_count -= len(items)


def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting", "reporting", after="general")
    group._addoption(
        '--old-summary', action="store_true",
        dest="tb_summary", default=False,
        help=(
            "Show tests that failed instead of one-line tracebacks"
        )
    )
    group._addoption(
        '--force-sugar', action="store_true",
        dest="force_sugar", default=False,
        help=(
            "Force pytest-sugar output even when not in real terminal"
        )
    )


def pytest_sessionstart(session):
    global LEN_PROGRESS_BAR_SETTING
    config = ConfigParser()
    config.read([
        'pytest-sugar.conf',
        os.path.expanduser('~/.pytest-sugar.conf')
    ])

    for key in THEME:
        if not config.has_option('theme', key):
            continue

        value = config.get("theme", key)
        value = value.lower()
        if value in ('', 'none'):
            value = None

        THEME[key] = value

    if config.has_option('sugar', 'progressbar_length'):
        LEN_PROGRESS_BAR_SETTING = config.get('sugar', 'progressbar_length')


def strip_colors(text):
    ansi_escape = re.compile(r'\x1b[^m]*m')
    stripped = ansi_escape.sub('', text)
    return stripped


def real_string_length(string):
    return len(strip_colors(string))


IS_SUGAR_ENABLED = False


@pytest.mark.trylast
def pytest_configure(config):
    global IS_SUGAR_ENABLED

    if sys.stdout.isatty() or config.getvalue('force_sugar'):
        IS_SUGAR_ENABLED = True

    if config.pluginmanager.hasplugin('xdist'):
        try:
            import xdist
        except ImportError:
            pass
        else:
            from packaging import version
            xdist_version = version.Version(xdist.__version__)
            if xdist_version >= version.Version('1.14'):
                config.pluginmanager.register(DeferredXdistPlugin())

    if IS_SUGAR_ENABLED and not getattr(config, 'slaveinput', None):
        # Get the standard terminal reporter plugin and replace it with our
        standard_reporter = config.pluginmanager.getplugin('terminalreporter')
        sugar_reporter = SugarTerminalReporter(standard_reporter)
        config.pluginmanager.unregister(standard_reporter)
        config.pluginmanager.register(sugar_reporter, 'terminalreporter')


def pytest_report_teststatus(report):
    if not IS_SUGAR_ENABLED:
        return

    if report.passed:
        letter = colored(THEME['symbol_passed'], THEME['success'])
    elif report.skipped:
        letter = colored(THEME['symbol_skipped'], THEME['skipped'])
    elif report.failed:
        letter = colored(THEME['symbol_failed'], THEME['fail'])
        if report.when != "call":
            letter = colored(THEME['symbol_failed_not_call'], THEME['fail'])
    elif report.outcome == 'rerun':
        letter = colored(THEME['symbol_rerun'], THEME['rerun'])
    else:
        letter = colored(THEME['symbol_unknown'], THEME['unknown'])

    if hasattr(report, "wasxfail"):
        if report.skipped:
            return "xfailed", colored(
                THEME['symbol_xfailed_skipped'], THEME['xfailed']
            ), "xfail"
        elif report.passed:
            return "xpassed", colored(
                THEME['symbol_xfailed_failed'], THEME['xpassed']
            ), "XPASS"

    return report.outcome, letter, report.outcome.upper()


class SugarTerminalReporter(TerminalReporter):
    def __init__(self, reporter):
        TerminalReporter.__init__(self, reporter.config)
        self.paths_left = []
        self.tests_count = 0
        self.tests_taken = 0
        self.reports = []
        self.unreported_errors = []
        self.progress_blocks = []
        self.reset_tracked_lines()

    def reset_tracked_lines(self):
        self.current_lines = {}
        self.current_line_nums = {}
        self.current_line_num = 0

    def report_collect(self, final=False):
        pass

    def pytest_collectreport(self, report):
        TerminalReporter.pytest_collectreport(self, report)
        if report.location[0]:
            self.paths_left.append(
                os.path.join(os.getcwd(), report.location[0])
            )
        if report.failed:
            self.rewrite("")
            self.print_failure(report)

    def pytest_sessionstart(self, session):
        self._session = session
        self._sessionstarttime = py.std.time.time()
        verinfo = ".".join(map(str, sys.version_info[:3]))
        self.write_line(
            "Test session starts "
            "(platform: %s, Python %s, pytest %s, pytest-sugar %s)" % (
                sys.platform, verinfo, pytest.__version__, __version__,
            ), bold=True
        )
        lines = self.config.hook.pytest_report_header(
            config=self.config, startdir=self.startdir)
        lines.reverse()
        for line in flatten(lines):
            self.write_line(line)

    def write_fspath_result(self, fspath, res):
        return

    def insert_progress(self, report):
        def get_progress_bar():
            length = LEN_PROGRESS_BAR
            if not length:
                return ''

            p = (
                float(self.tests_taken) / self.tests_count
                if self.tests_count else 0
            )
            floored = int(p * length)
            rem = int(round(
                (p * length - floored) * (len(PROGRESS_BAR_BLOCKS) - 1)
            ))
            progressbar = "%i%% " % round(p * 100)
            # make sure we only report 100% at the last test
            if progressbar == "100% " and self.tests_taken < self.tests_count:
                progressbar = "99% "

            # if at least one block indicates failure,
            # then the percentage should reflect that
            if [1 for block, success in self.progress_blocks if not success]:
                progressbar = colored(progressbar, THEME['fail'])
            else:
                progressbar = colored(progressbar, THEME['success'])

            bar = PROGRESS_BAR_BLOCKS[-1] * floored
            if rem > 0:
                bar += PROGRESS_BAR_BLOCKS[rem]
            bar += ' ' * (LEN_PROGRESS_BAR - len(bar))

            last = 0
            last_theme = None

            progressbar_background = THEME['progressbar_background']
            if progressbar_background is None:
                on_color = None
            else:
                on_color = 'on_' + progressbar_background

            for block, success in self.progress_blocks:
                if success:
                    theme = THEME['progressbar']
                else:
                    theme = THEME['progressbar_fail']

                if last < block:
                    progressbar += colored(bar[last:block],
                                           last_theme,
                                           on_color)

                progressbar += colored(bar[block],
                                       theme,
                                       on_color)
                last = block + 1
                last_theme = theme

            if last < len(bar):
                progressbar += colored(bar[last:len(bar)],
                                       last_theme,
                                       on_color)

            return progressbar

        append_string = get_progress_bar()

        path = self.report_key(report)
        current_line = self.current_lines.get(path, "")
        line_num = self.current_line_nums.get(path, self.current_line_num)

        console_width = self._tw.fullwidth
        num_spaces = (
            console_width - real_string_length(current_line) -
            real_string_length(append_string) - LEN_RIGHT_MARGIN
        )
        full_line = current_line + " " * num_spaces
        full_line += append_string

        self.overwrite(full_line, self.current_line_num - line_num)

    def overwrite(self, line, rel_line_num):
        # Move cursor up rel_line_num lines
        if rel_line_num > 0:
            self.write("\033[%dA" % rel_line_num)

        # Overwrite the line
        self.write("\r%s" % line)

        # Return cursor to original line
        if rel_line_num > 0:
            self.write("\033[%dB" % rel_line_num)

    def get_max_column_for_test_status(self):
        return (
            self._tw.fullwidth
            - LEN_PROGRESS_PERCENTAGE
            - LEN_PROGRESS_BAR
            - LEN_RIGHT_MARGIN
        )

    def begin_new_line(self, report, print_filename):
        path = self.report_key(report)
        self.current_line_num += 1
        if len(report.fspath) > self.get_max_column_for_test_status() - 5:
            fspath = '...' + report.fspath[
                -(self.get_max_column_for_test_status() - 5 - 5):
            ]
        else:
            fspath = report.fspath
        basename = os.path.basename(fspath)
        if print_filename:
            if self.showlongtestinfo:
                test_location = report.location[0]
                test_name = report.location[2]
            else:
                test_location = fspath[0:-len(basename)]
                test_name = fspath[-len(basename):]
            if test_location:
                pass
                # only replace if test_location is not empty, if it is,
                # test_name contains the filename
                # FIXME: This doesn't work.
                # test_name = test_name.replace('.', '::')
            self.current_lines[path] = (
                " " +
                colored(test_location, THEME['path']) +
                ("::" if self.verbosity > 0 else "") +
                colored(test_name, THEME['name']) +
                " "
            )
        else:
            self.current_lines[path] = " " * (2 + len(fspath))
        self.current_line_nums[path] = self.current_line_num
        self.write("\r\n")

    def reached_last_column_for_test_status(self, report):
        len_line = real_string_length(
            self.current_lines[self.report_key(report)])
        return len_line >= self.get_max_column_for_test_status()

    def pytest_runtest_logstart(self, nodeid, location):
        # Prevent locationline from being printed since we already
        # show the module_name & in verbose mode the test name.
        pass

    def pytest_runtest_logfinish(self):
        # prevent the default implementation to try to show
        # pytest's default progress
        pass

    def report_key(self, report):
        """Returns a key to identify which line the report should write to."""
        return report.location if self.showlongtestinfo else report.fspath

    def pytest_runtest_logreport(self, report):
        global LEN_PROGRESS_BAR_SETTING, LEN_PROGRESS_BAR

        res = pytest_report_teststatus(report=report)
        cat, letter, word = res
        self.stats.setdefault(cat, []).append(report)

        if not LEN_PROGRESS_BAR:
            if LEN_PROGRESS_BAR_SETTING.endswith('%'):
                LEN_PROGRESS_BAR = (
                    self._tw.fullwidth *
                    int(LEN_PROGRESS_BAR_SETTING[:-1]) // 100
                )
            else:
                LEN_PROGRESS_BAR = int(LEN_PROGRESS_BAR_SETTING)

        self.reports.append(report)
        if report.outcome == 'failed':
            print("")
            self.print_failure(report)
            # Ignore other reports or it will cause duplicated letters
        if report.when == 'teardown':
            self.tests_taken += 1
            self.insert_progress(report)
            path = os.path.join(os.getcwd(), report.location[0])

        if report.when == 'call' or report.skipped:
            path = self.report_key(report)
            if path not in self.current_line_nums:
                self.begin_new_line(report, print_filename=True)
            elif self.reached_last_column_for_test_status(report):
                # Print filename if another line was inserted in-between
                print_filename = (
                    self.current_line_nums[self.report_key(report)] !=
                    self.current_line_num)
                self.begin_new_line(report, print_filename)

            self.current_lines[path] = self.current_lines[path] + letter

            block = int(
                float(self.tests_taken) * LEN_PROGRESS_BAR / self.tests_count
                if self.tests_count else 0
            )
            if report.failed:
                if (
                    not self.progress_blocks or
                    self.progress_blocks[-1][0] != block
                ):
                    self.progress_blocks.append([block, False])
                elif (
                    self.progress_blocks and
                    self.progress_blocks[-1][0] == block
                ):
                    self.progress_blocks[-1][1] = False
            else:
                if (
                    not self.progress_blocks or
                    self.progress_blocks[-1][0] != block
                ):
                    self.progress_blocks.append([block, True])

            if not letter and not word:
                return
            if self.verbosity > 0:
                markup = {'red': True}
                if isinstance(word, tuple):
                    word, markup = word
                else:
                    if report.passed:
                        markup = {'green': True}
                    elif report.skipped:
                        markup = {'yellow': True}
                line = self._locationline(str(report.fspath), *report.location)
                if hasattr(report, 'node'):
                    self._tw.write("\r\n")
                    self.current_line_num += 1
                    if hasattr(report, 'node'):
                        self._tw.write("[%s] " % report.node.gateway.id)
                    self._tw.write(word, **markup)
                    self._tw.write(" " + line)
                    self.currentfspath = -2

    def count(self, key, when=('call',)):
        if self.stats.get(key):
            return len([
                x for x in self.stats.get(key)
                if not hasattr(x, 'when') or x.when in when
            ])
        else:
            return 0

    def summary_stats(self):
        session_duration = py.std.time.time() - self._sessionstarttime

        print("\nResults (%.2fs):" % round(session_duration, 2))
        if self.count('passed') > 0:
            self.write_line(colored(
                "   % 5d passed" % self.count('passed'),
                THEME['success']
            ))

        if self.count('xpassed') > 0:
            self.write_line(colored(
                "   % 5d xpassed" % self.count('xpassed'),
                THEME['xpassed']
            ))

        if self.count('failed', when=['call']) > 0:
            self.write_line(colored(
                "   % 5d failed" % self.count('failed', when=['call']),
                THEME['fail']
            ))
            for report in self.stats['failed']:
                if report.when != 'call':
                    continue
                if self.config.option.tb_summary:
                    crashline = self._get_decoded_crashline(report)
                else:
                    path = os.path.dirname(report.location[0])
                    name = os.path.basename(report.location[0])
                    lineno = self._get_lineno_from_report(report)
                    crashline = '%s%s%s:%s %s' % (
                        colored(path, THEME['path']),
                        '/' if path else '',
                        colored(name, THEME['name']),
                        lineno if lineno else '?',
                        colored(report.location[2], THEME['fail'])
                    )
                self.write_line("         - %s" % crashline)

        if self.count('failed', when=['setup', 'teardown']) > 0:
            self.write_line(colored(
                "   % 5d error" % (
                    self.count('failed', when=['setup', 'teardown'])
                ),
                THEME['error']
            ))

        if self.count('xfailed') > 0:
            self.write_line(colored(
                "   % 5d xfailed" % self.count('xfailed'),
                THEME['xfailed']
            ))

        if self.count('skipped', when=['call', 'setup', 'teardown']) > 0:
            self.write_line(colored(
                "   % 5d skipped" % (
                    self.count('skipped', when=['call', 'setup', 'teardown'])
                ),
                THEME['skipped']
            ))

        if self.count('rerun') > 0:
            self.write_line(colored(
                "   % 5d rerun" % self.count('rerun'),
                THEME['rerun']
            ))

        if self.count('deselected') > 0:
            self.write_line(colored(
                "   % 5d deselected" % self.count('deselected'),
                THEME['warning']
            ))

    def _get_decoded_crashline(self, report):
        crashline = self._getcrashline(report)

        if hasattr(crashline, 'decode'):
            encoding = locale.getpreferredencoding()
            try:
                crashline = crashline.decode(encoding)
            except UnicodeDecodeError:
                encoding = 'utf-8'
                crashline = crashline.decode(encoding, errors='replace')

        return crashline

    def _get_lineno_from_report(self, report):
        # Doctest failures in pytest>3.10 are stored in
        # reprlocation_lines, a list of (ReprFileLocation, lines)
        try:
            location, lines = report.longrepr.reprlocation_lines[0]
            return location.lineno
        except AttributeError:
            pass
        # Doctest failure reports have lineno=None at least up to
        # pytest==3.0.7, but it is available via longrepr object.
        try:
            return report.longrepr.reprlocation.lineno
        except AttributeError:
            lineno = report.location[1]
            if lineno is not None:
                lineno += 1
            return lineno

    def summary_failures(self):
        # Prevent failure summary from being shown since we already
        # show the failure instantly after failure has occurred.
        pass

    def summary_errors(self):
        # Prevent error summary from being shown since we already
        # show the error instantly after error has occurred.
        pass

    def print_failure(self, report):
        # https://github.com/Frozenball/pytest-sugar/issues/34
        if hasattr(report, 'wasxfail'):
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
                self.write_line('')
                self.write_sep("―", msg)
                self._outrep_summary(report)
        self.reset_tracked_lines()


# On older version of Pytest, allow default progress
if parse(pytest.__version__) <= parse('3.4'):  # pragma: no cover
    del SugarTerminalReporter.pytest_runtest_logfinish
