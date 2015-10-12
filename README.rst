pytest-sugar
================

|Build Status| |Version Status| |Downloads|

pytest-sugar is a plugin for `py.test <http://pytest.org>`_ that shows
failures and errors instantly and shows a progress bar.

|pytest-sugar|

.. |pytest-sugar| image:: http://pivotfinland.com/pytest-sugar/img/video.gif
   :alt: Screenshot
.. _pytest-sugar: http://pivotfinland.com/pytest-sugar/
.. |Build Status| image:: https://travis-ci.org/Frozenball/pytest-sugar.png?branch=master
   :target: https://travis-ci.org/Frozenball/pytest-sugar
.. |Version Status| image:: https://img.shields.io/pypi/v/pytest-sugar.svg
   :target: https://crate.io/packages/pytest-sugar/
.. |Downloads| image:: https://img.shields.io/pypi/dw/pytest-sugar.svg
   :target: https://crate.io/packages/pytest-sugar/

Requirements
------------

You will need the following prerequisites in order to use pytest-sugar:

- Python 2.6, 2.7, 3.3 or 3.4
- pytest 2.6.4 or newer

Installation
------------

To install pytest-sugar::

    $ pip install pytest-sugar

Then run your tests with::

    $ py.test

If you would like more detailed output (one test per line), then you may use the verbose option::

    $ py.test --verbose

If you would like to run tests without pytest-sugar, use::

    $ py.test -p no:sugar
