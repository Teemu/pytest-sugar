# -*- coding: utf-8 -*-
import pytest

pytest_plugins = "pytester"


class TestTerminalReporter(object):
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
        result = testdir.runpytest()
        result.stdout.fnmatch_lines([
          '*1 passed*',
          '*6 rerun*'
        ])

    def test_xpass_and_xfail(self, testdir):
        testdir.makepyfile(
            """
            import pytest

            @pytest.mark.xfail
            def test_xfail_true():
                assert True

            @pytest.mark.xfail
            def test_xfail_false():
                assert False

            @pytest.mark.xpass
            def test_xpass_true():
                assert True

            @pytest.mark.xpass
            def test_xpass_false():
                assert False
            """
        )
        result = testdir.runpytest()
        result.stdout.fnmatch_lines([
          '*test_xpass_false*',
          '*1 passed*',
          '*1 xpassed*',
          '*1 failed*',
          '*1 xfailed*'
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
        result = testdir.runpytest()
        result.stdout.fnmatch_lines([
          '*ERROR at teardown of test_foo*',
          '*1 passed*',
          '*1 failed*'
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
        result = testdir.runpytest()
        result.stdout.fnmatch_lines(['*1 skipped*'])

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
        result = testdir.runpytest('-m', 'example')
        result.stdout.fnmatch_lines(['*1 passed*', '*1 deselected*'])

    def test_fail(self, testdir):
        testdir.makepyfile(
            """
            import pytest
            def test_func():
                assert 0
            """
        )
        result = testdir.runpytest()
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
                assert b'hello' == b'Bj\\xc3\\xb6rk Gu\\xc3\\xb0mundsd\\xc3\\xb3ttir'
            """
        )
        result = testdir.runpytest()
        result.stdout.fnmatch_lines([
            "* test_func *",
            "    def test_func():",
            ">       assert * == *",
            "E       assert * == *",
        ])

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
        result = testdir.runpytest()
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
        result = testdir.runpytest()

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
        result = testdir.runpytest()

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
        result = testdir.runpytest()
        result.stdout.fnmatch_lines([
            "*ERROR collecting test_collect_error.py*",
            "test_collect_error.py:1: in <module>",
            "    raise ValueError(0)",
            "E   ValueError: 0",
        ])

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
        result = testdir.runpytest('-n2')

        assert result.ret == 0, result.stderr.str()
