import codecs

from setuptools import setup


# Copied from (and hacked):
# https://github.com/pypa/virtualenv/blob/develop/setup.py#L42
def get_version(filename):
    import os
    import re

    here = os.path.dirname(os.path.abspath(__file__))
    f = codecs.open(os.path.join(here, filename), encoding="utf-8")
    version_file = f.read()
    f.close()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name="pytest-sugar",
    description=(
        "pytest-sugar is a plugin for pytest that changes the default"
        " look and feel of pytest (e.g. progressbar, show tests that"
        " fail instantly)."
    ),
    long_description=codecs.open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    version=get_version("pytest_sugar.py"),
    url="https://github.com/Teemu/pytest-sugar",
    project_urls={
        "Issue Tracker": "https://github.com/Teemu/pytest-sugar/issues",
    },
    license="BSD",
    author="Teemu, Janne Vanhala and others",
    author_email="orkkiolento@gmail.com, janne.vanhala@gmail.com",
    py_modules=["pytest_sugar"],
    entry_points={"pytest11": ["sugar = pytest_sugar"]},
    zip_safe=False,
    include_package_data=True,
    platforms="any",
    install_requires=["pytest>=6.2.0", "termcolor>=2.1.0"],
    extras_require={
        "dev": [
            "black",
            "flake8",
            "pre-commit",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
)
