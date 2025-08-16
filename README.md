# pytest-sugar ✨

[![Build Status](https://img.shields.io/github/actions/workflow/status/Teemu/pytest-sugar/build-and-test.yaml?branch=main)](https://github.com/Teemu/pytest-sugar/actions)
[![PyPI Version](https://img.shields.io/pypi/v/pytest-sugar.svg)](https://pypi.org/project/pytest-sugar/)
[![Downloads](https://img.shields.io/pypi/dm/pytest-sugar)](https://pypi.org/project/pytest-sugar/)
![License](https://img.shields.io/pypi/l/pytest-sugar?color=blue)

This plugin extends [pytest](http://pytest.org) by showing failures and errors instantly, adding a progress bar, improving the test results, and making the output look better.

![render1667890332624-min](https://user-images.githubusercontent.com/53298/200600769-7b871b26-a36a-4ae6-ae24-945ee83fb74a.gif)

## Installation

To install pytest-sugar:

    python -m pip install pytest-sugar

Once installed, the plugin is activated automatically. Run your tests normally:

    pytest

If you would like more detailed output (one test per line), then you may use the verbose option:

    pytest --verbose

If you would like to run tests without pytest-sugar, use:

    pytest -p no:sugar

## Usage
pytest-sugar provides several command-line options to customize its output and behavior. These options enhance test reporting and Playwright trace integration:


Show detailed test failures instead of one-line tracebacks.
Use this if you want to see the full failure information instantly.

    --old-summary

Force pytest-sugar output even if pytest doesn’t detect a real terminal.
Useful when running tests in CI systems or other non-interactive environments.

    --force-sugar


Specify the directory where Playwright trace files are stored.
Defaults to Playwright default: "test-results"

    --sugar-trace-dir <directory>

Disable Playwright trace file detection and output display.
Use this if you want to turn off trace collection or display entirely.

    --sugar-no-trace


## How to contribute 👷‍♂️

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=master&repo=10950375)

Make sure to read our [Code of Conduct](https://github.com/Teemu/pytest-sugar/blob/master/.github/CODE_OF_CONDUCT.md). You can get started modifying the codebase with the following commands. Alternatively, you can try Github Codespaces (click the badge above). Push the changes to your repository & create a pull request.

````
git clone git@github.com:Teemu/pytest-sugar.git
cd pytest-sugar
python -m venv .venv
source .venv/bin/activate
echo ".venv" >> .git/info/exclude
pip install -e ".[dev]"
pre-commit install
````

There are two ways of running tests. We have our proper tests:

````
pytest .
````

There are also fake tests that can be used to visualise the output:

````
pytest faketests
````

When submitting a pull request, please add a `RELEASE.md` file in the root of the project that contains the release type (major, minor, patch) and a summary of the changes that will be used as the release changelog entry. For example:

```markdown
Release type: patch

For long-running tests, display minutes and not only seconds.
```

## Requirements

You will need the following prerequisites in order to use pytest-sugar:

- Python 3.8 or newer
- pytest 6.2 or newer

## Running on Windows

If you are seeing gibberish, you might want to try changing charset and fonts. See [this comment]( https://github.com/Teemu/pytest-sugar/pull/49#issuecomment-146567670) for more details.

## Similar projects

- [pytest-rich](https://github.com/nicoddemus/pytest-rich)
- [pytest-pretty](https://github.com/samuelcolvin/pytest-pretty)
