import pytest


@pytest.yield_fixture
def fixt():
    yield
    raise Exception


def test_foo(fixt):
    pass
