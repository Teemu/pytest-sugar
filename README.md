# pytest-sugar ✨

[![Pypi version](https://img.shields.io/pypi/v/pytest-sugar.svg)](https://pypi.org/project/pytest-sugar/)

This plugin extends [pytest](http://pytest.org) by showing failures and errors instantly, adding a progress bar, improving the test results and making the output look better.

![render1667890332624-min](https://user-images.githubusercontent.com/53298/200600769-7b871b26-a36a-4ae6-ae24-945ee83fb74a.gif)

## Installation

To install pytest-sugar:

    pip install pytest-sugar

The plugin is activated by activated. Run your tests normally:

    $ pytest

If you would like more detailed output (one test per line), then you may use the verbose option:

    $ pytest --verbose

If you would like to run tests without pytest-sugar, use:

    $ pytest -p no:sugar

## Requirements

You will need the following prerequisites in order to use pytest-sugar:

- Python 2.7, 3.4 or newer
- pytest 2.9.0 or newer
- pytest-xdist 1.14 or above if you want the progress bar to work while running
  tests in parallel

## Running on Windows

If you are seeing gibberish, you might want to try changing charset and fonts. See [this comment]( https://github.com/Teemu/pytest-sugar/pull/49#issuecomment-146567670) for more details.

## Similar projects

- [pytest-rich](https://github.com/nicoddemus/pytest-rich)
- [pytest-pretty](https://github.com/samuelcolvin/pytest-pretty)
