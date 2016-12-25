# pytest-sugar

[![](https://travis-ci.org/Frozenball/pytest-sugar.png?branch=master)](https://travis-ci.org/Frozenball/pytest-sugar) ![](https://img.shields.io/pypi/v/pytest-sugar.svg)

pytest-sugar is a plugin for `py.test <http://pytest.org>`_ that shows
failures and errors instantly and shows a progress bar.

![](http://pivotfinland.com/pytest-sugar/img/video.gif)

## Requirements

You will need the following prerequisites in order to use pytest-sugar:

- Python 2.7, 3.4 or 3.5
- pytest 2.9.0 or newer
- pytest-xdist 1.14 or above if you want the progress bar to work while running
  tests in parallel

## Installation

To install pytest-sugar:

    $ pip install pytest-sugar

Then run your tests with:

    $ py.test

If you would like more detailed output (one test per line), then you may use the verbose option:

    $ py.test --verbose

If you would like to run tests without pytest-sugar, use:

    $ py.test -p no:sugar

## Running on Windows

If you are seeing gibberish, you might want to try changing charset and fonts. See [this comment]( https://github.com/Frozenball/pytest-sugar/pull/49#issuecomment-146567670) for more details.
