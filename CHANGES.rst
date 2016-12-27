Changelog
---------

A list of changes between each release.

0.8.0 (2016-x-x)
^^^^^^^^^^^^^^^^^^^

- Release as an universal wheel
- Pytest3 compatibility
- Treat setup/teardown failures as errors
- Fix path issue in --new-summary
- Disable sugar output when not in terminal, should help with testing other pytest plugins
- Add double colons when in verbose mode
- Make --new-summary default

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
