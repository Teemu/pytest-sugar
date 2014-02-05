from setuptools import setup
from pytest_sugar import __version__

setup(
    name='pytest-sugar',
    description=(
        'py.test is a plugin for py.test that changes the default look'
        ' and feel of py.test (e.g. progressbar, show tests that fail'
        ' instantly).'
    ),
    long_description=open("README.rst").read(),
    version=__version__,
    url='http://pivotfinland.com/pytest-sugar/',
    license='BSD',
    author='Teemu, Janne Vanhala and others',
    author_email='orkkiolento@gmail.com, janne.vanhala@gmail.com',
    py_modules=['pytest_sugar'],
    entry_points={'pytest11': ['sugar = pytest_sugar']},
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=['pytest>=2.3'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: PyPy',
    ]
)
