# pytest-sugar

[![Build status](https://travis-ci.org/Teemu/pytest-sugar.svg?branch=master)](https://travis-ci.org/Teemu/pytest-sugar)
[![Pypi version](https://img.shields.io/pypi/v/pytest-sugar.svg)](https://pypi.org/project/pytest-sugar/)

pytest-sugar is a plugin for [pytest](http://pytest.org) that shows
failures and errors instantly and shows a progress bar.

![Demo](https://i.imgur.com/jER0Jxj.gif)

## Requirements

You will need the following prerequisites in order to use pytest-sugar:

- Python 2.7, 3.4 or newer
- pytest 2.9.0 or newer
- pytest-xdist 1.14 or above if you want the progress bar to work while running
  tests in parallel

## Installation

To install pytest-sugar:

    pip install pytest-sugar

Then run your tests with:

    $ pytest

If you would like more detailed output (one test per line), then you may use the verbose option:

    $ pytest --verbose

If you would like to run tests without pytest-sugar, use:

    $ pytest -p no:sugar

## Running on Windows

If you are seeing gibberish, you might want to try changing charset and fonts. See [this comment]( https://github.com/Teemu/pytest-sugar/pull/49#issuecomment-146567670) for more details.
