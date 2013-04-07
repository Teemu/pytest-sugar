# -*- coding: utf-8 -*-
"""
pytest_instafail
~~~~~~~~~~~~~~~~

py.test plugin to show failures instantly.

:copyright: (c) 2013 by Janne Vanhala.
:license: BSD, see LICENSE for more details.
"""
import pytest
from _pytest.terminal import TerminalReporter


def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting", "reporting", after="general")
    group._addoption(
        '--instafail', action="store_true", dest="instafail", default=False,
        help=(
            "show failures and errors instantly as they occur (disabled by "
            "default)."
        )
    )


@pytest.mark.trylast
def pytest_configure(config):
    if config.option.instafail:
        # Get the standard terminal reporter plugin...
        standard_reporter = config.pluginmanager.getplugin('terminalreporter')
        instafail_reporter = InstafailingTerminalReporter(standard_reporter)

        # ...and replace it with our own instafailing reporter.
        config.pluginmanager.unregister(standard_reporter)
        config.pluginmanager.register(instafail_reporter, 'terminalreporter')


class InstafailingTerminalReporter(TerminalReporter):
    def __init__(self, reporter):
        TerminalReporter.__init__(self, reporter.config)
        self._tw = reporter._tw

    def pytest_collectreport(self, report):
        # Show errors occurred during the collection instantly.
        TerminalReporter.pytest_collectreport(self, report)
        if report.failed:
            self.rewrite("")  # erase the "collecting" message
            self.print_failure(report)

    def pytest_runtest_logreport(self, report):
        # Show failures and errors occuring during running a test
        # instantly.
        TerminalReporter.pytest_runtest_logreport(self, report)
        if report.failed:
            if self.verbosity <= 0:
                self._tw.line()
            self.print_failure(report)

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
                self.write_sep("_", msg)
                self._outrep_summary(report)
