import pytest


@pytest.yield_fixture
def fixt():
    raise Exception
    yield


def test_foo(fixt):
    pass
