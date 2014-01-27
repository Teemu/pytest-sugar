# -*- coding: utf-8 -*-
"""
pytest_instafail
~~~~~~~~~~~~~~~~

py.test plugin to show failures instantly.

:copyright: see LICENSE for details
:license: BSD, see LICENSE for more details.
"""
import pytest
import pytest, py
import sys
import random
import os
import json
import time
import re
from _pytest.terminal import TerminalReporter


class TerminalColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    GRAY = '\033[1;30m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''
        self.GRAY = ''


bcolors = TerminalColors()

class EtaLogger:
    def __init__(self):
        self.settings_path = os.path.expanduser("~/.pytest-sugar.json")
        try:
            self.collected = json.loads(
                open(self.settings_path).read()
            )
        except IOError:
            self.collected = {}
        #print "-----------------"
        #print self.collected

    def collect(self, time, filename=None, hash=None):
        self.collected[filename] = time
        self.save()

    def estimate(self, paths):
        estimated_time = 0
        for path in paths:
            if path in self.collected:
                estimated_time += self.collected[path]
        return estimated_time

    def save_session(
        self,
        tests_duration,
        session_duration
    ):
        tests_sum = 0
        for path, time in tests_duration.items():
            self.collect(
                filename=path,
                time=time
            )
            tests_sum += time

        extra_time = session_duration - tests_sum
        self.collect(
            filename=os.getcwd(),
            time=extra_time
        )
        self.save()


    def save(self):
        #print "WRITING TO ",self.settings_path
        fp = open(self.settings_path, 'w')
        fp.write(json.dumps(self.collected))
        fp.close()


def flatten(l):
    for x in l:
        if isinstance(x, (list, tuple)):
            for y in flatten(x):
                yield y
        else:
            yield x


def pytest_collection_modifyitems(session, config, items):
    config.pluginmanager.getplugin('terminalreporter').tests_count += len(items)

def pytest_deselected(items):
    """ Update tests_count to not include deselected tests """
    if len(items) > 0:
        items[0].config.pluginmanager.getplugin('terminalreporter').tests_count -= len(items)

def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting", "reporting", after="general")
    group._addoption(
        '--nosugar', action="store_false", dest="sugar", default=True,
        help=(
            "disable pytest-sugar"
        )
    )


def real_string_length(string):
    for color in [
        bcolors.HEADER,
        bcolors.OKBLUE,
        bcolors.OKGREEN,
        bcolors.GRAY,
        bcolors.WARNING,
        bcolors.FAIL,
        bcolors.ENDC
    ]:
        string = string.replace(color, '')
    return len(string)

@pytest.mark.trylast
def pytest_configure(config):
    if config.option.sugar:
        # Get the standard terminal reporter plugin and replace it with our
        standard_reporter = config.pluginmanager.getplugin('terminalreporter')
        sugar_reporter = InstafailingTerminalReporter(standard_reporter)
        config.pluginmanager.unregister(standard_reporter)
        config.pluginmanager.register(sugar_reporter, 'terminalreporter')


def pytest_report_teststatus(report):
    if report.passed:
        letter = bcolors.OKGREEN+u'✓'+bcolors.ENDC
    elif report.skipped:
        letter = bcolors.OKBLUE+u's'+bcolors.ENDC
    elif report.failed:
        letter = bcolors.FAIL+u'⨯'+bcolors.ENDC
        if report.when != "call":
            letter = bcolors.FAIL+u'ₓ'+bcolors.ENDC
    return report.outcome, letter, report.outcome.upper()

class InstafailingTerminalReporter(TerminalReporter):
    def __init__(self, reporter):
        #pytest_collectreport = self.pytest_collectreport
        TerminalReporter.__init__(self, reporter.config)
        self.writer = self._tw
        self.eta_logger = EtaLogger()
        self.paths_left = []
        self.tests_count = 0
        self.tests_taken = 0
        self.current_line = u''
        self.currentfspath2 = ''
        self.time_taken = {}
        self.reports = []
        self.unreported_errors = []

    def get_estimate(self):
        session_duration = py.std.time.time() - self._sessionstarttime

        estimate = 0
        estimate += self.eta_logger.estimate(self.paths_left)
        estimate += self.eta_logger.estimate([os.getcwd()])
        estimate -= session_duration
        return estimate

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
        self.write_line("Test session starts (%s, %s)" % (sys.platform, verinfo), bold=True)
        lines = self.config.hook.pytest_report_header(config=self.config)
        lines.reverse()
        for line in flatten(lines):
            self.write_line(line)

    def write_fspath_result(self, fspath, res):
        return

    def insert_progress(self):
        def get_estimate():
            #return str(round(self.get_estimate(),2))
            seconds = int(round(self.get_estimate()))
            minutes = seconds/60
            seconds = seconds%60
            return "%im %is" % (minutes, seconds)

        def get_progress_bar():
            blocks = [
                u'█',
                u'▉',
                u'▉',
                u'▊',
                u'▊',
                u'▋',
                u'▋',
                u'▌',
                u'▌',
                u'▍',
                u'▍',
                u'▎',
                u'▎',
                u'▏',
                u'▏'
            ]
            length = 10
            p = float(self.tests_taken) / self.tests_count
            floored = int(round(p * length))
            progressbar = u''
            progressbar += "%i%% " % round(p*100)
            progressbar += bcolors.OKGREEN
            progressbar += blocks[0] * floored
            progressbar += bcolors.ENDC
            progressbar += bcolors.GRAY + blocks[0] * (length - floored) + bcolors.ENDC
            return progressbar

        append_string = get_progress_bar()
        return self.append_string(append_string)

    def append_string(self, append_string=''):
        console_width = self._tw.fullwidth
        full_line = self.current_line + " " * (console_width  - real_string_length(self.current_line))
        full_line = full_line[0:-(len(append_string)-15)] + append_string
        return full_line  

    def overwrite(self, line):
        sys.stdout.write("\r" + self.append_string(line).encode('utf-8'))
        sys.stdout.flush()

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
        if report.when == 'call':
            if report.fspath != self.currentfspath2:
                self.currentfspath2 = report.fspath
                basename = os.path.basename(report.fspath)
                self.current_line = (
                    u"   " +
                    bcolors.GRAY +
                    report.fspath[0:-len(basename)] +
                    bcolors.ENDC +
                    report.fspath[-len(basename):] +
                    u" "
                )
                print("")

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
                        markup = {'green':True}
                    elif rep.failed:
                        markup = {'red':True}
                    elif rep.skipped:
                        markup = {'yellow':True}
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

        self.eta_logger.save_session(self.time_taken, session_duration)

        print("\nResults (%.2fs):" % round(session_duration,2))
        if self.count('passed') > 0:
            self.write_line(
                "   %d passed" % self.count('passed') + 
                bcolors.ENDC
            )

        if self.count('failed') > 0:
            self.write_line(
                bcolors.FAIL+
                "   %d failed" % self.count('failed') + 
                bcolors.ENDC
            )
            for report in self.reports:
                if report.outcome == 'failed':
                    print("      - %s" % (
                        self._getcrashline(report)
                    ))

        if self.count('skipped') > 0:
            self.write_line(
                bcolors.GRAY+
                "   %d skipped" % self.count('skipped') + 
                bcolors.ENDC
            )

        if self.count('deselected') > 0:
            self.write_line(
                bcolors.GRAY+
                "   %d deselected" % self.count('deselected') + 
                bcolors.ENDC
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
                self.write_sep(u"―", msg)
                self._outrep_summary(report)
