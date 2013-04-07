from setuptools import setup

setup(
    name='pytest-instafail',
    description='py.test plugin to show failures instantly',
    long_description=open("README.rst").read(),
    version='0.1.0',
    url='https://github.com/jpvanhal/pytest-instafail',
    license='BSD',
    author='Janne Vanhala',
    author_email='janne.vanhala@gmail.com',
    py_modules=['pytest_instafail'],
    entry_points={'pytest11': ['instafail = pytest_instafail']},
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=['pytest>=2.3'],
)
