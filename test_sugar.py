# -*- coding: utf-8 -*-
import pytest
import re
from pytest_sugar import strip_colors

pytest_plugins = "pytester"


def get_counts(stdout):
    output = strip_colors(stdout)

    def _get(x):
        m = re.search('\d %s' % x, output)
        if m:
            return m.group()[0]
        else:
            return 'n/a'

    return {
        x: _get(x)
        for x in (
            'passed',
            'xpassed',
            'failed',
            'xfailed',
            'deselected',
            'error',
            'rerun',
            'skipped'
        )
    }


def assert_count(testdir, *args):
    """Assert that n passed, n failed, ... matches"""
    without_plugin = testdir.runpytest('-p', 'no:sugar', *args).stdout.str()
    with_plugin = testdir.runpytest('--force-sugar', *args).stdout.str()

    count_without = get_counts(without_plugin)
    count_with = get_counts(with_plugin)

    assert count_without == count_with, (
        "When running test with and without plugin, "
        "the resulting output differs.\n\n"
        "Without plugin: %s\n"
        "With plugin: %s\n" % (
            ", ".join('%s %s' % (v, k) for k, v in count_without.items()),
            ", ".join('%s %s' % (v, k) for k, v in count_with.items()),
        )
    )


class TestTerminalReporter(object):
    def test_new_summary(self, testdir):
        testdir.makepyfile(
            """
            import pytest

            def test_sample():
                assert False
            """
        )
        output = testdir.runpytest(
            '--force-sugar'
        ).stdout.str()
        assert 'test_new_summary.py:3 test_sample' in strip_colors(output)

    def test_old_summary(self, testdir):
        testdir.makepyfile(
            """
            import pytest

            def test_sample():
                assert False
            """
        )
        output = testdir.runpytest(
            '--force-sugar', '--old-summary'
        ).stdout.str()
        assert 'test_old_summary.py:4: assert False' in strip_colors(output)

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
            def pytest_report_header(startdir):
                pass
            """
        )
        testdir.makepyfile(
            """
            def test():
                pass
            """
        )
        result = testdir.runpytest('--force-sugar')
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
        pytest.importorskip('pytest_rerunfailures')
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
        result = testdir.runpytest('--force-sugar')
        result.stdout.fnmatch_lines([
            '*test_xpass*',
            '*XPASS(strict)*',
            '*1 failed*',
        ])

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

        result = testdir.runpytest('--force-sugar')
        result.stdout.fnmatch_lines([
            '*ERROR at teardown of test_foo*',
            '*1 passed*',
            '*1 error*'
        ])

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

    def test_fail(self, testdir):
        testdir.makepyfile(
            """
            import pytest
            def test_func():
                assert 0
            """
        )
        result = testdir.runpytest('--force-sugar')
        result.stdout.fnmatch_lines([
            "* test_func *",
            "    def test_func():",
            ">       assert 0",
            "E       assert 0",
        ])

    def test_fail_unicode_crashline(self, testdir):
        testdir.makepyfile(
            """
            # -*- coding: utf-8 -*-
            import pytest
            def test_func():
                assert b'hello' == b'Bj\\xc3\\xb6rk Gu\\xc3\\xb0mundsd'
            """
        )
        result = testdir.runpytest('--force-sugar')
        result.stdout.fnmatch_lines([
            "* test_func *",
            "    def test_func():",
            ">       assert * == *",
            "E       assert * == *",
        ])

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
        output = strip_colors(testdir.runpytest('--force-sugar').stdout.str())
        assert output.count('         -') == 2

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
        result = testdir.runpytest('--force-sugar')
        result.stdout.fnmatch_lines([
            "* test_func *",
            "    def test_func():",
            ">       assert 0",
            "E       assert 0",
            "* test_func2 *",
            "    def test_func2():",
            ">       assert 0",
            "E       assert 0",
        ])

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
        result = testdir.runpytest('--force-sugar')

        result.stdout.fnmatch_lines([
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
        ])
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
        result = testdir.runpytest('--force-sugar')

        result.stdout.fnmatch_lines([
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
        ])
        assert result.ret != 0

    def test_collect_error(self, testdir):
        testdir.makepyfile("""raise ValueError(0)""")
        assert_count(testdir)
        result = testdir.runpytest('--force-sugar')
        result.stdout.fnmatch_lines([
            "*ERROR collecting test_collect_error.py*",
            "test_collect_error.py:1: in <module>",
            "    raise ValueError(0)",
            "E   ValueError: 0",
        ])

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
        assert_count(testdir, '--verbose')

    def test_verbose_has_double_colon(self, testdir):
        testdir.makepyfile(
            """
            import pytest

            def test_true():
                assert True
            """
        )
        output = testdir.runpytest(
            '--force-sugar', '--verbose'
        ).stdout.str()
        assert 'test_verbose_has_double_colon.py::test_true' in strip_colors(
            output
        )

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
        result = testdir.runpytest('--force-sugar', '-n2')

        assert result.ret == 0, result.stderr.str()
