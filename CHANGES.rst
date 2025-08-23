Changelog
---------

1.1.1 - 2025-08-23
^^^^^^^^^^^^^^^^^^

Adjust signature of SugarTerminalReporter to avoid conflicts with other pytest plugins

Contributed by [Daniil](https://github.com/TolstochenkoDaniil) via [PR #297](https://github.com/Teemu/pytest-sugar/pull/297/)


1.1.0 - 2025-08-16
^^^^^^^^^^^^^^^^^^

Add Playwright trace file detection and display support for failed tests. This enhancement automatically detects and displays Playwright trace.zip files with viewing commands when tests fail, making debugging easier for Playwright users.
![Playwright trace.zip](docs/images/playwright-trace-example.png)

New command-line options:
- `--sugar-trace-dir`: Configure the directory name for Playwright trace files (default: test-results)
- `--sugar-no-trace`: Disable Playwright trace file detection and display

Contributed by [kie](https://github.com/kiebak3r) via [PR #296](https://github.com/Teemu/pytest-sugar/pull/296/)


1.0.0 - 2024-02-01
^^^^^^^^^^^^^^^^^^

* Add support for pytest 8.x
* Drop support for Python 3.7

Contributed by [Justin Mayer](https://github.com/justinmayer) via [PR #281](https://github.com/Teemu/pytest-sugar/pull/281/)


0.9.7 - 2023-04-10
^^^^^^^^^^^^^^^^^^

- For long-running tests, display minutes and not only seconds (thanks @last-partizan)
- Add support for Pytest’s ``--header`` option (thanks @wiresv)

0.9.6 (2022-11-5)
^^^^^^^^^^^^^^^^^^^

- Remove py.std calls (thanks @alexcjohnson)

0.9.5 (2022-07-10)
^^^^^^^^^^^^^^^^^^^

- Fix distutils deprecation warning (thanks @tgagor)
- Fix incompatibility with pytest-timeout (thanks @graingert)
- Update pytest naming convention in documentation (thanks @avallbona)

0.9.4 (2020-07-06)
^^^^^^^^^^^^^^^^^^^

- Fix pytest-sugar 0.9.3 incompatible with pytest 5.4 (thanks @nicoddemus)
- Fix Tests fail with pytest 3.5.0 DOCTESTS (^)
- Fix Tests fail with pytest 5.x (^)

0.9.3 (2020-04-26)
^^^^^^^^^^^^^^^^^^^

- Fix incompatibility with pytest 5.4.0 (thanks @GuillaumeFavelier)

0.9.2 (2018-11-8)
^^^^^^^^^^^^^^^^^^^

- Fix incompatibility with pytest 3.10 (thanks @Natim)
- Double colons for verbose output (thanks @albertodonato)
- Fix "Wrong count with items modified in pytest_collection_modifyitems" (thanks @blueyed)
- Defer registration of xdist hook (thanks @blueyed)

0.9.1 (2017-8-4)
^^^^^^^^^^^^^^^^^^^

- Fix incompatibility with pytest 3.4 (thanks @nicoddemus)

0.9.0 (2017-8-4)
^^^^^^^^^^^^^^^^^^^

- Print correct location for doctest failures
- Write xdist output on correct lines

0.8.0 (2016-12-28)
^^^^^^^^^^^^^^^^^^^

- Release as an universal wheel
- Pytest3 compatibility
- Treat setup/teardown failures as errors
- Fix path issue in --new-summary
- Disable sugar output when not in terminal, should help with testing other pytest plugins
- Add double colons when in verbose mode
- Make --new-summary default, replaced flag with --old-summary

0.7.1 (2016-4-1)
^^^^^^^^^^^^^^^^^^^

- Fix issue with deselected tests

0.7.0 (2016-3-29)
^^^^^^^^^^^^^^^^^^^

- Show skipped tests
- Changed failed test summary (try `--new-summary` option to test it out)
- Show teardown errors
- Add support for pytest-rerunfailedtests
- Make test symbols customizable
- Remove deprecated `--nosugar`.

0.6.0 (2016-3-18)
^^^^^^^^^^^^^^^^^^^

- pytest-xdist support
- Turn off progress meter when progressbar_length=0

0.5.1 (2015-10-12)
^^^^^^^^^^^^^^^^^^^

- Fix Python 3 support

0.5.0 (2015-10-12)
^^^^^^^^^^^^^^^^^^^

- Colour progressbar correctly for low number of tests
- Fix error case when deactivating pytest-sugar using --lf together with --nosugar
- --nosugar deprecated, use -p no:sugar

0.4.0 (2015-03-25)
^^^^^^^^^^^^^^^^^^^

Thanks to or:

- Configurable colors
- Handling of long file paths
- Red progressbar in case of failures
- Using termcolor for much easier coloration and configuration
- Simplify the progressbar maths code
- Change the 's' for skipped tests to a circle
- Simplify the space filling logic of full_line
- Reduce the right margin to 0, so the blinking cursor is hidden

0.3.6 (2014-12-12)
^^^^^^^^^^^^^^^^^^^

- Crashline with non-ASCII, #42
- Restore Python 2.6 / 3.3 support
- Fix unit tests
- Fix UnicodeDecodeError during install, #43

0.3.5 (2014-11-26)
^^^^^^^^^^^^^^^^^^^

- Fix codec error during pip install

0.3.4 (2014-04-02)
^^^^^^^^^^^^^^^^^^^

- Using pytest.mark.xfails throws an error #34

0.3.3 (2014-02-14)
^^^^^^^^^^^^^^^^^^^

- Fix problem with PyPi package.

0.3.2 (2014-02-06)
^^^^^^^^^^^^^^^^^^^

- Fix issue with PyPI package.
- Code refactoring

0.3.1 (2014-02-06)
^^^^^^^^^^^^^^^^^^^

- Fix incorrect wrapping that fine-grained progress introduced

0.3.0 (2014-6-05)
^^^^^^^^^^^^^^^^^^^

- Fine-grained progressbar using more Unicode block chars
- Display version of pytest and pytest-sugar
- Python 3 support
- Fix GH-3: Wrap tests when they extend past line
