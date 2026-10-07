import io
import re

import pytest
from _pytest.reports import BaseReport, CollectReport, TestReport

import pytest_sugar
from pytest_sugar import SugarTerminalReporter, strip_colors

pytest_plugins = "pytester"


def get_counts(stdout):
    output = strip_colors(stdout)

    def _get(x):
        m = re.search(r"(\d+) %s" % x, output)
        if m:
            return m.group(1)
        return "n/a"

    return {
        x: _get(x)
        for x in (
            "passed",
            "xpassed",
            "failed",
            "xfailed",
            "deselected",
            "error",
            "rerun",
            "skipped",
        )
    }


def assert_count(testdir, *args):
    """Assert that n passed, n failed, ... matches"""
    without_plugin = testdir.runpytest("-p", "no:sugar", *args).stdout.str()
    with_plugin = testdir.runpytest("--force-sugar", *args).stdout.str()

    count_without = get_counts(without_plugin)
    count_with = get_counts(with_plugin)

    assert count_without == count_with, (
        "When running test with and without plugin, "
        "the resulting output differs.\n\n"
        "Without plugin: %s\n"
        "With plugin: %s\n"
        % (
            ", ".join(f"{v} {k}" for k, v in count_without.items()),
            ", ".join(f"{v} {k}" for k, v in count_with.items()),
        )
    )


class TestTerminalReporter:
    @pytest.mark.parametrize(
        "attributes, expected",
        [
            ({"outcome": "passed", "when": "setup"}, ("", "", "")),
            ({"outcome": "passed", "when": "teardown"}, ("", "", "")),
            ({"outcome": "passed", "when": "call"}, ("passed", "✓", "PASSED")),
            ({"outcome": "passed"}, ("passed", "✓", "PASSED")),
            ({"outcome": "passed", "when": "collect"}, ("passed", "✓", "PASSED")),
            (
                {"outcome": "passed", "when": "setup", "wasxfail": "reason"},
                ("xpassed", "X", "XPASS"),
            ),
            (
                {"outcome": "passed", "when": "teardown", "wasxfail": "reason"},
                ("xpassed", "X", "XPASS"),
            ),
            (
                {"outcome": "skipped", "when": "setup", "wasxfail": "reason"},
                ("xfailed", "x", "xfail"),
            ),
            ({"outcome": "failed", "when": "setup"}, ("failed", "ₓ", "FAILED")),
            ({"outcome": "failed", "when": "teardown"}, ("failed", "ₓ", "FAILED")),
            ({"outcome": "skipped", "when": "teardown"}, ("skipped", "s", "SKIPPED")),
            ({"outcome": "rerun", "when": "teardown"}, ("rerun", "R", "RERUN")),
            ({"outcome": "unknown", "when": "setup"}, ("unknown", "?", "UNKNOWN")),
        ],
    )
    def test_report_status(self, monkeypatch, attributes, expected):
        monkeypatch.setattr(pytest_sugar, "IS_SUGAR_ENABLED", True)
        monkeypatch.setattr(pytest_sugar, "THEME", pytest_sugar.Theme())
        report = BaseReport(**attributes)
        result = pytest_sugar.pytest_report_teststatus(report)
        assert tuple(strip_colors(value) for value in result) == expected

    @pytest.mark.parametrize("phase", ["setup", "teardown"])
    def test_disabled_fixture_report_status(self, monkeypatch, phase):
        report = BaseReport(outcome="passed", when=phase)
        with monkeypatch.context() as patch:
            patch.setattr(pytest_sugar, "IS_SUGAR_ENABLED", False)
            assert pytest_sugar.pytest_report_teststatus(report) is None

    def test_passed_collection_report_status(self, monkeypatch):
        monkeypatch.setattr(pytest_sugar, "IS_SUGAR_ENABLED", True)
        report = CollectReport("test_sample.py", "passed", None, [])
        category, _, word = pytest_sugar.pytest_report_teststatus(report)
        assert (category, word) == ("passed", "PASSED")

    def test_successful_fixture_reports_are_retained(self, monkeypatch, pytestconfig):
        monkeypatch.setattr(pytest_sugar, "IS_SUGAR_ENABLED", True)
        output = io.StringIO()
        reporter = SugarTerminalReporter(pytestconfig, file=output)
        reporter.tests_count = 1
        reports = [
            TestReport(
                "test_sample.py::test_sample",
                ("test_sample.py", 0, "test_sample"),
                {},
                "passed",
                None,
                phase,
            )
            for phase in ("setup", "call", "teardown")
        ]
        for report in reports:
            reporter.pytest_runtest_logreport(report)
        assert reporter.stats[""] == [reports[0], reports[2]]
        assert reporter.stats["passed"] == [reports[1]]
        assert reporter.reports == reports
        assert reporter.tests_taken == 1
        assert "100%" in strip_colors(output.getvalue())

    @pytest.mark.parametrize("reportchars", ["-rP", "-rpP"])
    @pytest.mark.parametrize("distributed", [False, True])
    def test_passes_summary_retains_fixture_output(
        self, testdir, reportchars, distributed
    ):
        testdir.makepyfile(
            """
            import pytest

            @pytest.fixture(autouse=True)
            def fixture(request):
                print(f"setup: {request.node.name}")
                yield
                print(f"teardown: {request.node.name}")

            def test_pass():
                print("call: test_pass")

            def test_fail():
                print("call: test_fail")
                assert False
            """
        )
        args = ["--force-sugar", reportchars, "--tb=short", "--color=no"]
        if distributed:
            pytest.importorskip("xdist")
            args.extend(["-n2", "-v"])
        result = testdir.runpytest(*args)
        assert result.ret == 1
        output = result.stdout.str()
        passes = output.split(" PASSES ", 1)[1]
        for phase in ("setup", "call", "teardown"):
            assert passes.count(f"{phase}: test_pass") == 1
            assert f"{phase}: test_fail" not in passes
        assert get_counts(output)["passed"] == "1"
        assert get_counts(output)["failed"] == "1"
        assert "100%" in output
        if reportchars == "-rpP":
            passed = [
                line for line in output.splitlines() if line.startswith("PASSED ")
            ]
            assert len(passed) == 1
            assert passed[0].endswith("::test_pass")

    def test_sugar_terminal_reporter_init_signature(self, pytestconfig):
        terminal_reporter = pytestconfig.pluginmanager.getplugin("terminalreporter")
        sugar_reporter = SugarTerminalReporter(terminal_reporter.config)
        assert sugar_reporter.config is terminal_reporter.config

        file_obj = io.StringIO()
        sugar_reporter = SugarTerminalReporter(terminal_reporter.config, file=file_obj)
        assert sugar_reporter.config is terminal_reporter.config
        assert sugar_reporter._tw._file is file_obj

    def test_new_summary(self, testdir):
        testdir.makepyfile(
            """
            import pytest

            def test_sample():
                assert False
            """
        )
        output = testdir.runpytest("--force-sugar").stdout.str()
        assert "test_new_summary.py:3 test_sample" in strip_colors(output)

    def test_old_summary(self, testdir):
        testdir.makepyfile(
            """
            import pytest

            def test_sample():
                assert False
            """
        )
        output = testdir.runpytest("--force-sugar", "--old-summary").stdout.str()
        assert "test_old_summary.py:4: assert False" in strip_colors(output)

    @pytest.mark.parametrize(
        "phase, action",
        [
            (None, "fail"),
            ("call", "fail"),
            ("setup", "fail"),
            ("teardown", "fail"),
            ("call", "skip"),
            ("setup", "skip"),
            ("teardown", "skip"),
        ],
    )
    @pytest.mark.parametrize("old_summary", [False, True])
    @pytest.mark.parametrize("distributed", [False, True])
    def test_passed_short_summary(
        self, testdir, phase, action, old_summary, distributed
    ):
        testdir.makepyfile(
            f"""
            import pytest

            @pytest.fixture(autouse=True)
            def fixture():
                if {phase == 'setup'}:
                    pytest.{action}("setup")
                yield
                if {phase == 'teardown'}:
                    pytest.{action}("teardown")

            def test_sample():
                if {phase == 'call'}:
                    pytest.{action}("call")
            """
        )
        args = ["-rp"]
        if distributed:
            pytest.importorskip("xdist")
            args.append("-n2")

        without_plugin = testdir.runpytest("-p", "no:sugar", *args)
        if old_summary:
            args.append("--old-summary")
        with_plugin = testdir.runpytest("--force-sugar", *args)

        expected_exit = 1 if phase is not None and action == "fail" else 0
        assert with_plugin.ret == without_plugin.ret == expected_exit
        assert get_counts(with_plugin.stdout.str()) == get_counts(
            without_plugin.stdout.str()
        )
        passed_without = [
            line
            for line in strip_colors(without_plugin.stdout.str()).splitlines()
            if line.startswith("PASSED ")
        ]
        passed_with = [
            line
            for line in strip_colors(with_plugin.stdout.str()).splitlines()
            if line.startswith("PASSED ")
        ]
        assert len(passed_without) == (phase in (None, "teardown"))
        assert passed_with == passed_without
        assert "100%" in strip_colors(with_plugin.stdout.str())

    def test_xfail_true(self, testdir):
        testdir.makepyfile(
            """
            import pytest

            @pytest.mark.xfail
            def test_sample():
                assert True
            """
        )
        assert_count(testdir)

    def test_xfail_false(self, testdir):
        testdir.makepyfile(
            """
            import pytest

            @pytest.mark.xfail
            def test_sample():
                assert False
            """
        )
        assert_count(testdir)

    def test_report_header(self, testdir):
        testdir.makeconftest(
            """
            def pytest_report_header(start_path):
                pass
            """
        )
        testdir.makepyfile(
            """
            def test():
                pass
            """
        )
        result = testdir.runpytest("--force-sugar")
        assert result.ret == 0, result.stderr.str()

    def test_xfail_strict_true(self, testdir):
        testdir.makepyfile(
            """
            import pytest

            @pytest.mark.xfail(strict=True)
            def test_sample():
                assert True
            """
        )
        assert_count(testdir)

    def test_xfail_strict_false(self, testdir):
        testdir.makepyfile(
            """
            import pytest

            @pytest.mark.xfail(strict=True)
            def test_sample():
                assert False
            """
        )
        assert_count(testdir)

    def test_xpass_true(self, testdir):
        testdir.makepyfile(
            """
            import pytest

            @pytest.mark.xpass
            def test_sample():
                assert True
            """
        )
        assert_count(testdir)

    def test_xpass_false(self, testdir):
        testdir.makepyfile(
            """
            import pytest

            @pytest.mark.xpass
            def test_sample():
                assert False
            """
        )
        assert_count(testdir)

    def test_flaky_test(self, testdir):
        pytest.importorskip("pytest_rerunfailures")
        testdir.makepyfile(
            """
            import pytest

            COUNT = 0

            @pytest.mark.flaky(reruns=10)
            def test_flaky_test():
                global COUNT
                COUNT += 1
                assert COUNT >= 7
            """
        )
        assert_count(testdir)

    def test_xpass_strict(self, testdir):
        testdir.makepyfile(
            """
            import pytest

            @pytest.mark.xfail(strict=True)
            def test_xpass():
                assert True
            """
        )
        result = testdir.runpytest("--force-sugar")
        result.stdout.fnmatch_lines(
            [
                "*test_xpass*",
                "*XPASS(strict)*",
                "*1 failed*",
            ]
        )

    def test_teardown_errors(self, testdir):
        testdir.makepyfile(
            """
            import pytest
            @pytest.yield_fixture
            def fixt():
                yield
                raise Exception

            def test_foo(fixt):
                pass
            """
        )
        assert_count(testdir)

        result = testdir.runpytest("--force-sugar")
        result.stdout.fnmatch_lines(
            ["*ERROR at teardown of test_foo*", "*1 passed*", "*1 error*"]
        )

    def test_skipping_tests(self, testdir):
        testdir.makepyfile(
            """
            import pytest
            @pytest.mark.skipif(True, reason='This must be skipped.')
            def test_skip_this_if():
                assert True
            """
        )
        assert_count(testdir)

    def test_deselecting_tests(self, testdir):
        testdir.makepyfile(
            """
            import pytest
            @pytest.mark.example
            def test_func():
                assert True

            def test_should_be():
                assert False
            """
        )
        assert_count(testdir)

    def test_item_count_after_pytest_collection_modifyitems(self, testdir):
        testdir.makeconftest(
            """
            import pytest

            @pytest.hookimpl(hookwrapper=True, tryfirst=True)
            def pytest_collection_modifyitems(config, items):
                yield
                items[:] = [x for x in items if x.name == 'test_one']
            """
        )
        testdir.makepyfile(
            """
            def test_one():
                print('test_one_passed')

            def test_ignored():
                assert 0
            """
        )
        result = testdir.runpytest("-s")
        result.stdout.fnmatch_lines(
            [
                "*test_one_passed*",
                "*100%*",
            ]
        )
        assert result.ret == 0

    def test_fail(self, testdir):
        testdir.makepyfile(
            """
            import pytest
            def test_func():
                assert 0
            """
        )
        result = testdir.runpytest("--force-sugar")
        result.stdout.fnmatch_lines(
            [
                "* test_func *",
                "    def test_func():",
                ">       assert 0",
                "E       assert 0",
            ]
        )

    def test_fail_unicode_crashline(self, testdir):
        testdir.makepyfile(
            """
            # -*- coding: utf-8 -*-
            import pytest
            def test_func():
                assert b'hello' == b'Bj\\xc3\\xb6rk Gu\\xc3\\xb0mundsd'
            """
        )
        result = testdir.runpytest("--force-sugar")
        result.stdout.fnmatch_lines(
            [
                "* test_func *",
                "    def test_func():",
                ">       assert * == *",
                "E       AssertionError: assert * == *",
            ]
        )

    def test_fail_in_fixture_and_test(self, testdir):
        testdir.makepyfile(
            """
            import pytest
            def test_func():
                assert False

            def test_func2():
                assert False

            @pytest.fixture
            def failure():
                return 3/0

            def test_lol(failure):
                assert True
            """
        )
        assert_count(testdir)
        output = strip_colors(testdir.runpytest("--force-sugar").stdout.str())
        assert output.count("         -") == 2

    def test_fail_fail(self, testdir):
        testdir.makepyfile(
            """
            import pytest
            def test_func():
                assert 0
            def test_func2():
                assert 0
            """
        )
        assert_count(testdir)
        result = testdir.runpytest("--force-sugar")
        result.stdout.fnmatch_lines(
            [
                "* test_func *",
                "    def test_func():",
                ">       assert 0",
                "E       assert 0",
                "* test_func2 *",
                "    def test_func2():",
                ">       assert 0",
                "E       assert 0",
            ]
        )

    def test_error_in_setup_then_pass(self, testdir):
        testdir.makepyfile(
            """
            def setup_function(function):
                print ("setup func")
                if function is test_nada:
                    assert 0
            def test_nada():
                pass
            def test_zip():
                pass
            """
        )
        assert_count(testdir)
        result = testdir.runpytest("--force-sugar")

        result.stdout.fnmatch_lines(
            [
                "*ERROR at setup of test_nada*",
                "",
                "function = <function test_nada at *",
                "",
                "*setup_function(function):*",
                "*setup func*",
                "*if function is test_nada:*",
                "*assert 0*",
                "test_error_in_setup_then_pass.py:4: AssertionError",
                "*Captured stdout setup*",
                "*setup func*",
                "*1 passed*",
            ]
        )
        assert result.ret != 0

    def test_error_in_teardown_then_pass(self, testdir):
        testdir.makepyfile(
            """
            def teardown_function(function):
                print ("teardown func")
                if function is test_nada:
                    assert 0
            def test_nada():
                pass
            def test_zip():
                pass
            """
        )
        assert_count(testdir)
        result = testdir.runpytest("--force-sugar")

        result.stdout.fnmatch_lines(
            [
                "*ERROR at teardown of test_nada*",
                "",
                "function = <function test_nada at*",
                "",
                "*def teardown_function(function):*",
                "*teardown func*",
                "*if function is test_nada*",
                ">*assert 0*",
                "E*assert 0*",
                "test_error_in_teardown_then_pass.py:4: AssertionError",
                "*Captured stdout teardown*",
                "teardown func",
                "*2 passed*",
            ]
        )
        assert result.ret != 0

    def test_collect_error(self, testdir):
        testdir.makepyfile("""raise ValueError(0)""")
        assert_count(testdir)
        result = testdir.runpytest("--force-sugar")
        result.stdout.fnmatch_lines(
            [
                "*ERROR collecting test_collect_error.py*",
                "test_collect_error.py:1: in <module>",
                "    raise ValueError(0)",
                "E   ValueError: 0",
            ]
        )

    def test_verbose(self, testdir):
        testdir.makepyfile(
            """
            import pytest

            def test_true():
                assert True

            def test_true2():
                assert True

            def test_false():
                assert False

            @pytest.mark.skip
            def test_skip():
                assert False

            @pytest.mark.xpass
            def test_xpass():
                assert True

            @pytest.mark.xfail
            def test_xfail():
                assert True
            """
        )
        assert_count(testdir, "--verbose")

    def test_verbose_has_double_colon(self, testdir):
        testdir.makepyfile(
            """
            def test_true():
                assert True
            """
        )
        output = testdir.runpytest("--force-sugar", "--verbose").stdout.str()
        assert "test_verbose_has_double_colon.py::test_true" in strip_colors(output)

    # def test_verbose_has_double_colon_with_class(self, testdir):
    #     testdir.makepyfile(
    #         """
    #         class TestTrue:

    #             def test_true(self):
    #                 assert True
    #         """
    #     )
    #     output = testdir.runpytest(
    #         '--force-sugar', '--verbose'
    #     ).stdout.str()

    #     test_name = (
    #         'test_verbose_has_double_colon_with_class.py::TestTrue::test_true')
    #     assert test_name in strip_colors(output)

    # def test_not_verbose_no_double_colon_filename(self, testdir):
    #     testdir.makepyfile(
    #         """
    #         class TestTrue:

    #             def test_true(self):
    #                 assert True
    #         """
    #     )
    #     output = testdir.runpytest(
    #         '--force-sugar'
    #     ).stdout.str()

    #     test_name = 'test_not_verbose_no_double_colon_filename.py'
    #     assert test_name in strip_colors(output)

    def test_xdist(self, testdir):
        pytest.importorskip("xdist")
        testdir.makepyfile(
            """
            def test_nada():
                pass
            def test_zip():
                pass
            """
        )
        result = testdir.runpytest("--force-sugar", "-n2")

        assert result.ret == 0, result.stderr.str()

    def test_xdist_verbose(self, testdir):
        pytest.importorskip("xdist")
        testdir.makepyfile(
            """
            def test_nada():
                pass
            def test_zip():
                pass
            """
        )
        result = testdir.runpytest("--force-sugar", "-n2", "-v")

        assert result.ret == 0, result.stderr.str()

    def test_doctest(self, testdir):
        """Test doctest-modules"""

        testdir.makepyfile(
            """
            class ToTest():
                @property
                def doctest(self):
                    \"\"\"
                        >>> Invalid doctest
                    \"\"\"
            """
        )
        result = testdir.runpytest("--force-sugar", "--doctest-modules")

        assert result.ret == 1, result.stderr.str()

    def test_doctest_lineno(self, testdir):
        """Test location reported for doctest-modules"""

        testdir.makepyfile(
            """
            def foobar():
                '''
                >>> foobar()
                '''
                raise NotImplementedError
            """
        )
        result = testdir.runpytest("--force-sugar", "--doctest-modules")

        assert result.ret == 1, result.stderr.str()
        result.stdout.fnmatch_lines(
            [
                "UNEXPECTED EXCEPTION: NotImplementedError()",
                "*test_doctest_lineno.py:3: UnexpectedException",
                "Results*:",
                "*-*test_doctest_lineno.py*:3*",
            ]
        )

    def test_flaky_rerun(self, testdir):
        pytest.importorskip("flaky")
        testdir.makepyfile(
            """
            import pytest
            from flaky import flaky

            @pytest.mark.parametrize("x", range(200))
            def test_lots1(x):
                assert True

            @flaky
            def test_flaky():
                assert False

            @pytest.mark.parametrize("x", range(80))
            def test_lots2(x):
                assert True
            """
        )
        result = testdir.runpytest("--force-sugar", "--no-flaky-report")

        assert result.ret == 1, result.stderr.str()
        test_counts = get_counts(result.stdout.str())
        assert test_counts["passed"] == "280"
        assert test_counts["failed"] == "1"
