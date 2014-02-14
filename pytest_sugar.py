# -*- coding: utf-8 -*-
"""
pytest_sugar
~~~~~~~~~~~~

py.test is a plugin for py.test that changes the default look
and feel of py.test (e.g. progressbar, show tests that fail instantly).

:copyright: see LICENSE for details
:license: BSD, see LICENSE for more details.
"""
from __future__ import unicode_literals
import os
import sys
import time

import py
import pytest
from _pytest.terminal import TerminalReporter


__version__ = '0.3.3'

LEN_RIGHT_MARGIN = 5
LEN_PROGRESS_BAR = 10
LEN_SPACE_BETWEEN_PERCENT_AND_PROGRESS_BAR = 1
LEN_PERCENT = 3
LEN_SPACE_BETWEEN_TEST_STATUS_AND_PERCENT = 4
TERMINAL_COLORS = {
    'header': '\033[95m',
    'okblue': '\033[94m',
    'okgreen': '\033[92m',
    'gray': '\033[1;30m',
    'gray_bg': '\033[100m',
    'warning': '\033[93m',
    'fail': '\033[91m',
    'endc': '\033[0m'
}
PROGRESS_BAR_BLOCKS = [
    '█', '▉', '▉', '▊', '▊', '▋', '▋', '▌',
    '▌', '▍', '▍', '▎', '▎', '▏', '▏'
]


def flatten(l):
    for x in l:
        if isinstance(x, (list, tuple)):
            for y in flatten(x):
                yield y
        else:
            yield x


def pytest_collection_modifyitems(session, config, items):
    if config.option.sugar:
        terminal_reporter = config.pluginmanager.getplugin('terminalreporter')
        terminal_reporter.tests_count += len(items)


def pytest_deselected(items):
    """ Update tests_count to not include deselected tests """
    if len(items) > 0:
        pluginmanager = items[0].config.pluginmanager
        terminal_reporter = pluginmanager.getplugin('terminalreporter')
        terminal_reporter.tests_count -= len(items)


def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting", "reporting", after="general")
    group._addoption(
        '--nosugar', action="store_false", dest="sugar", default=True,
        help=(
            "disable pytest-sugar"
        )
    )


def real_string_length(string):
    for color_name, color_string in TERMINAL_COLORS.items():
        string = string.replace(color_string, '')
    return len(string)


@pytest.mark.trylast
def pytest_configure(config):
    global pytest_report_teststatus

    if config.option.sugar:
        # Get the standard terminal reporter plugin and replace it with our
        standard_reporter = config.pluginmanager.getplugin('terminalreporter')
        sugar_reporter = SugarTerminalReporter(standard_reporter)
        config.pluginmanager.unregister(standard_reporter)
        config.pluginmanager.register(sugar_reporter, 'terminalreporter')
        pytest_report_teststatus = _pytest_report_teststatus


def _pytest_report_teststatus(report):
    if report.passed:
        letter = TERMINAL_COLORS['okgreen']+'✓'+TERMINAL_COLORS['endc']
    elif report.skipped:
        letter = TERMINAL_COLORS['okblue']+'s'+TERMINAL_COLORS['endc']
    elif report.failed:
        letter = TERMINAL_COLORS['fail']+'⨯'+TERMINAL_COLORS['endc']
        if report.when != "call":
            letter = TERMINAL_COLORS['fail']+'ₓ'+TERMINAL_COLORS['endc']
    return report.outcome, letter, report.outcome.upper()


class SugarTerminalReporter(TerminalReporter):
    def __init__(self, reporter):
        TerminalReporter.__init__(self, reporter.config)
        self.writer = self._tw
        self.paths_left = []
        self.tests_count = 0
        self.tests_taken = 0
        self.current_line = ''
        self.currentfspath2 = ''
        self.time_taken = {}
        self.reports = []
        self.unreported_errors = []

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
        self._sessionstarttime = py.std.time.time()
        verinfo = ".".join(map(str, sys.version_info[:3]))
        self.write_line(
            "Test session starts "
            "(platform: %s, Python %s, pytest %s, pytest-sugar %s)" % (
                sys.platform, verinfo, pytest.__version__, __version__,
            ), bold=True
        )
        lines = self.config.hook.pytest_report_header(config=self.config)
        lines.reverse()
        for line in flatten(lines):
            self.write_line(line)

    def write_fspath_result(self, fspath, res):
        return

    def insert_progress(self):
        def get_progress_bar():
            length = LEN_PROGRESS_BAR
            p = float(self.tests_taken) / self.tests_count
            floored = int(p * length)
            rem = int(round((p * length - floored) * 13))
            progressbar = ''
            progressbar += "%i%% " % round(p*100)
            progressbar += TERMINAL_COLORS['okgreen']
            progressbar += TERMINAL_COLORS['gray_bg']
            progressbar += PROGRESS_BAR_BLOCKS[1] * floored
            if p == 1.0:
                progressbar += PROGRESS_BAR_BLOCKS[1]
            else:
                progressbar += PROGRESS_BAR_BLOCKS[14 - rem]
            progressbar += TERMINAL_COLORS['endc']
            progressbar += TERMINAL_COLORS['gray'] + TERMINAL_COLORS['gray_bg']
            progressbar += PROGRESS_BAR_BLOCKS[1] * (length - floored)
            progressbar += TERMINAL_COLORS['endc']
            return progressbar

        append_string = get_progress_bar()
        return self.append_string(append_string)

    def append_string(self, append_string=''):
        console_width = self._tw.fullwidth
        num_spaces = console_width - real_string_length(self.current_line)
        full_line = self.current_line + " " * num_spaces
        full_line = full_line[0:-(len(append_string) - 28)] + append_string
        return full_line

    def overwrite(self, line):
        self.writer.write("\r" + self.append_string(line))

    def begin_new_line(self, report, print_filename):
        basename = os.path.basename(report.fspath)
        if print_filename:
            self.current_line = (
                "   " +
                TERMINAL_COLORS['gray'] +
                report.fspath[0:-len(basename)] +
                TERMINAL_COLORS['endc'] +
                report.fspath[-len(basename):] +
                " "
            )
        else:
            self.current_line = " " * (4 + len(report.fspath))
        print("")

    def reached_last_column_for_test_status(self):
        max_column_for_test_status = (
            self._tw.fullwidth
            - LEN_RIGHT_MARGIN
            - LEN_PROGRESS_BAR
            - LEN_SPACE_BETWEEN_PERCENT_AND_PROGRESS_BAR
            - LEN_PERCENT
            - LEN_SPACE_BETWEEN_TEST_STATUS_AND_PERCENT
        )
        len_line = real_string_length(self.current_line)
        return len_line == max_column_for_test_status

    def pytest_runtest_logreport(self, report):
        self.reports.append(report)
        if report.outcome == 'failed':
            print("")
            self.print_failure(report)
            # Ignore other reports or it will cause duplicated letters
        if report.when == 'setup':
            self.setup_timer = time.time()
        if report.when == 'teardown':
            self.tests_taken += 1
            self.overwrite(self.insert_progress())
            path = os.path.join(os.getcwd(), report.location[0])
            time_taken = time.time() - self.setup_timer
            if not path in self.time_taken:
                self.time_taken[path] = 0
            self.time_taken[path] += time_taken
            if self.reached_last_column_for_test_status():
                self.begin_new_line(report, print_filename=False)
        if report.when == 'call':
            if report.fspath != self.currentfspath2:
                self.currentfspath2 = report.fspath
                self.begin_new_line(report, print_filename=True)

            rep = report
            res = pytest_report_teststatus(report=report)
            cat, letter, word = res
            self.current_line = self.current_line + letter

            self.stats.setdefault(cat, []).append(rep)
            if not letter and not word:
                return
            if self.verbosity > 0:
                if isinstance(word, tuple):
                    word, markup = word
                else:
                    if rep.passed:
                        markup = {'green': True}
                    elif rep.failed:
                        markup = {'red': True}
                    elif rep.skipped:
                        markup = {'yellow': True}
                line = self._locationline(str(rep.fspath), *rep.location)
                if not hasattr(rep, 'node'):
                    self.write_ensure_prefix(line, word, **markup)
                else:
                    self.ensure_newline()
                    if hasattr(rep, 'node'):
                        self._tw.write("[%s] " % rep.node.gateway.id)
                    self._tw.write(word, **markup)
                    self._tw.write(" " + line)
                    self.currentfspath = -2

    def count(self, key):
        if self.stats.get(key):
            return len(self.stats.get(key))
        else:
            return 0

    def summary_stats(self):
        session_duration = py.std.time.time() - self._sessionstarttime

        print("\nResults (%.2fs):" % round(session_duration, 2))
        if self.count('passed') > 0:
            self.write_line(
                "   %d passed" % self.count('passed') +
                TERMINAL_COLORS['endc']
            )

        if self.count('failed') > 0:
            self.write_line(
                TERMINAL_COLORS['fail'] +
                "   %d failed" % self.count('failed') +
                TERMINAL_COLORS['endc']
            )
            for report in self.reports:
                if report.outcome == 'failed':
                    print("      - %s" % (
                        self._getcrashline(report)
                    ))

        if self.count('skipped') > 0:
            self.write_line(
                TERMINAL_COLORS['fail'] +
                "   %d skipped" % self.count('skipped') +
                TERMINAL_COLORS['endc']
            )

        if self.count('deselected') > 0:
            self.write_line(
                TERMINAL_COLORS['fail'] +
                "   %d deselected" % self.count('deselected') +
                TERMINAL_COLORS['endc']
            )

    def summary_failures(self):
        # Prevent failure summary from being shown since we already
        # show the failure instantly after failure has occured.
        pass

    def summary_errors(self):
        # Prevent error summary from being shown since we already
        # show the error instantly after error has occured.
        pass

    def print_failure(self, report):
        if self.config.option.tbstyle != "no":
            if self.config.option.tbstyle == "line":
                line = self._getcrashline(report)
                self.write_line(line)
            else:
                msg = self._getfailureheadline(report)
                if not hasattr(report, 'when'):
                    msg = "ERROR collecting " + msg
                elif report.when == "setup":
                    msg = "ERROR at setup of " + msg
                elif report.when == "teardown":
                    msg = "ERROR at teardown of " + msg
                self.write_line('')
                self.write_sep("―", msg)
                self._outrep_summary(report)
